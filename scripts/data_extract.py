#!/usr/bin/env python3
"""
Minimal Data Extractor for Kabaddi Video Analytics
Extracts basic raid metrics from video for player ranking
"""

import cv2
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ultralytics import YOLO
from court.simplified_court import SimplifiedCourtDynamics
from analytics.raid_extractor import RaidMetricsExtractor
import json

class DataExtractor:
    def __init__(self, video_path):
        self.video_path = video_path
        
        # Check if video exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "yolov8n-pose.pt")
        self.model = YOLO(model_path)
        
        # Load simplified court dynamics
        try:
            self.court_dynamics = SimplifiedCourtDynamics.load_from_config(video_path)
        except ValueError as e:
            raise ValueError(f"{e}\nRun: python court/setup_play_area.py")
        
        # Get midline from court dynamics
        self.p1, self.p2 = tuple(self.court_dynamics.midline[0]), tuple(self.court_dynamics.midline[1])
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"✓ Video loaded: {total_frames} frames @ {self.fps:.2f} FPS")
        
        self.metrics_extractor = RaidMetricsExtractor(self.court_dynamics, self.fps)
        
        self.raids = []
        self.current_raid = None
        self.raider_id = None
        self.raid_active = False
        self.missing_frames = 0
        self.max_missing = 60
        self.raider_locked = False
        
        # Key frames directory
        self.keyframes_dir = os.path.join("data", "keyframes")
        os.makedirs(self.keyframes_dir, exist_ok=True)
    
    def point_side(self, x, y):
        return np.sign((self.p2[0] - self.p1[0]) * (y - self.p1[1]) - 
                      (self.p2[1] - self.p1[1]) * (x - self.p1[0]))
    
    def extract_data(self, display=True):
        frame_count = 0
        all_players = {}
        DISPLAY_SCALE = 0.6
        
        print(f"Video FPS: {self.fps}")
        print(f"Midline: {self.p1} -> {self.p2}")
        print(f"Play box: {self.court_dynamics.play_box}")
        
        if display:
            cv2.namedWindow("Data Extraction", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Draw play area (works with any polygon)
            n = len(self.court_dynamics.play_box)
            for i in range(n):
                p1 = tuple(self.court_dynamics.play_box[i].astype(int))
                p2 = tuple(self.court_dynamics.play_box[(i+1)%n].astype(int))
                cv2.line(frame, p1, p2, (255, 255, 0), 2)
            
            # Draw midline
            cv2.line(frame, self.p1, self.p2, (0, 255, 255), 2)
            
            # Draw baulk line
            b1 = tuple(self.court_dynamics.baulk_line[0].astype(int))
            b2 = tuple(self.court_dynamics.baulk_line[1].astype(int))
            cv2.line(frame, b1, b2, (0, 0, 255), 2)
            
            # Draw bonus line
            bo1 = tuple(self.court_dynamics.bonus_line[0].astype(int))
            bo2 = tuple(self.court_dynamics.bonus_line[1].astype(int))
            cv2.line(frame, bo1, bo2, (0, 255, 0), 2)
            
            # Draw end line
            e1 = tuple(self.court_dynamics.end_line[0].astype(int))
            e2 = tuple(self.court_dynamics.end_line[1].astype(int))
            cv2.line(frame, e1, e2, (255, 0, 255), 2)
            cv2.putText(frame, "END", e1, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            
            # Enhanced tracking with multi-scale detection for far players
            results = self.model.track(
                frame, 
                persist=True, 
                conf=0.05,      # Very low confidence to detect far players
                iou=0.15,       # Lower IOU for better matching
                verbose=False,
                tracker="botsort.yaml",
                imgsz=1920,     # Larger image size for better far detection
                max_det=50      # Detect more players
            )
            
            current_frame_players = set()
            raider_detected_this_frame = False
            
            # Debug: Print detection info every 30 frames
            if frame_count % 30 == 0:
                print(f"Frame {frame_count}: Detected {len(results[0].boxes) if results and results[0].boxes.id is not None else 0} players, Tracking {len(all_players)} players")
            
            if results and results[0].boxes.id is not None:
                for i, box in enumerate(results[0].boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    conf = float(box.conf[0])
                    
                    # Get pose keypoints for better center calculation
                    keypoints = None
                    if results[0].keypoints is not None and i < len(results[0].keypoints):
                        kpts = results[0].keypoints[i].xy.cpu().numpy()[0]
                        if len(kpts) > 0:
                            keypoints = kpts
                            valid_kpts = kpts[kpts[:, 0] > 0]
                            if len(valid_kpts) >= 4:
                                # Prioritize torso keypoints for stability
                                torso_kpts = [kpts[5], kpts[6], kpts[11], kpts[12]]
                                valid_torso = [k for k in torso_kpts if k[0] > 0 and k[1] > 0]
                                if len(valid_torso) >= 2:
                                    cx = int(np.mean([k[0] for k in valid_torso]))
                                    cy = int(np.mean([k[1] for k in valid_torso]))
                                else:
                                    cx = int(np.mean(valid_kpts[:, 0]))
                                    cy = int(np.mean(valid_kpts[:, 1]))
                            else:
                                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    else:
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Calculate player size (for far player detection)
                    player_height = y2 - y1
                    player_width = x2 - x1
                    is_far_player = player_height < 80 or player_width < 40  # Small = far from camera
                    
                    # FILTER: Only track players inside play box
                    if not self.court_dynamics.is_inside_play_box((cx, cy)):
                        # Draw gray box for outside players
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (128, 128, 128), 1)
                        cv2.putText(frame, "OUT", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
                        continue  # Skip this player
                    
                    current_frame_players.add(tid)
                    side = self.point_side(cx, cy)
                    
                    # Initialize or update player tracking
                    if tid not in all_players:
                        all_players[tid] = {
                            'positions': [],
                            'keypoints': [],
                            'side_history': [],
                            'confidence': [],
                            'baseline_side': None,
                            'last_seen': frame_count
                        }
                    
                    # Update player data
                    all_players[tid]['last_seen'] = frame_count
                    all_players[tid]['confidence'].append(conf)
                    
                    # Position smoothing (less aggressive for far players)
                    if len(all_players[tid]['positions']) > 0:
                        last_pos = all_players[tid]['positions'][-1]
                        alpha = 0.5 if is_far_player else 0.7  # Less smoothing for far players
                        smooth_cx = int(alpha * cx + (1 - alpha) * last_pos[0])
                        smooth_cy = int(alpha * cy + (1 - alpha) * last_pos[1])
                        cx, cy = smooth_cx, smooth_cy
                    
                    # Use bottom center (feet) for penetration calculation
                    feet_x = (x1 + x2) // 2
                    feet_y = y2  # Bottom of bounding box
                    
                    # Track maximum penetration from ANY body part
                    max_penetration_point = (feet_x, feet_y)
                    max_penetration_depth = self.court_dynamics.get_penetration_depth((feet_x, feet_y))
                    
                    # Check all keypoints for maximum penetration
                    if keypoints is not None:
                        for kpt in keypoints:
                            if kpt[0] > 0 and kpt[1] > 0:
                                kpt_depth = self.court_dynamics.get_penetration_depth((int(kpt[0]), int(kpt[1])))
                                if kpt_depth > max_penetration_depth:
                                    max_penetration_depth = kpt_depth
                                    max_penetration_point = (int(kpt[0]), int(kpt[1]))
                    
                    # Also check bounding box corners for extended limbs
                    for corner in [(x1, y2), (x2, y2), (feet_x, y2)]:
                        corner_depth = self.court_dynamics.get_penetration_depth(corner)
                        if corner_depth > max_penetration_depth:
                            max_penetration_depth = corner_depth
                            max_penetration_point = corner
                    
                    all_players[tid]['positions'].append((max_penetration_point[0], max_penetration_point[1], frame_count))
                    all_players[tid]['keypoints'].append(keypoints)
                    all_players[tid]['side_history'].append(side)
                    
                    # Keep only recent history
                    if len(all_players[tid]['positions']) > 30:
                        all_players[tid]['positions'].pop(0)
                        all_players[tid]['keypoints'].pop(0)
                        all_players[tid]['side_history'].pop(0)
                        all_players[tid]['confidence'].pop(0)
                    
                    # Determine baseline side
                    if len(all_players[tid]['side_history']) >= 15 and all_players[tid]['baseline_side'] is None:
                        sides = all_players[tid]['side_history'][:15]
                        side_counts = {}
                        for s in sides:
                            side_counts[s] = side_counts.get(s, 0) + 1
                        most_common = max(side_counts, key=side_counts.get)
                        if side_counts[most_common] >= 11:
                            all_players[tid]['baseline_side'] = most_common
                            print(f"✓ Player {tid} baseline established: side={most_common}")
                    
                    # Raider locking - STRICT to prevent ID switching
                    is_raider = False
                    
                    if self.raid_active and self.raider_locked and tid == self.raider_id:
                        is_raider = True
                        raider_detected_this_frame = True
                    elif not self.raid_active:
                        if all_players[tid]['baseline_side'] is not None:
                            recent_sides = all_players[tid]['side_history'][-7:]
                            if len(recent_sides) >= 7:
                                opposite_count = sum(1 for s in recent_sides if s != all_players[tid]['baseline_side'])
                                if opposite_count >= 6:
                                    is_raider = True
                                    print(f"🎯 Raid detected! Player {tid} crossed midline (baseline={all_players[tid]['baseline_side']}, current_side={side})")
                    
                    # Draw player with keypoints for ALL players
                    if is_raider:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        cv2.putText(frame, f"RAIDER (ID:{tid}) LOCKED", 
                                  (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        if not self.raid_active:
                            self.start_raid(tid, frame_count, all_players)
                            raider_detected_this_frame = True
                            # Save key frame: Raid Start
                            cv2.imwrite(f"{self.keyframes_dir}/raid_{len(self.raids)+1}_start_frame_{frame_count}.jpg", frame)
                        elif self.raider_id == tid:
                            raider_detected_this_frame = True
                            
                            # Check and save bonus/baulk crossing
                            if self.current_raid and 'crossed_bonus' not in self.current_raid:
                                if self.court_dynamics.crossed_bonus_line((cx, cy)):
                                    self.current_raid['crossed_bonus'] = True
                                    cv2.imwrite(f"{self.keyframes_dir}/raid_{len(self.raids)+1}_bonus_frame_{frame_count}.jpg", frame)
                            
                            if self.current_raid and 'crossed_baulk' not in self.current_raid:
                                if self.court_dynamics.crossed_baulk_line((cx, cy)):
                                    self.current_raid['crossed_baulk'] = True
                                    cv2.imwrite(f"{self.keyframes_dir}/raid_{len(self.raids)+1}_baulk_frame_{frame_count}.jpg", frame)
                        
                        # Draw keypoints for raider
                        if keypoints is not None:
                            for kpt in keypoints:
                                if kpt[0] > 0 and kpt[1] > 0:
                                    cv2.circle(frame, (int(kpt[0]), int(kpt[1])), 3, (255, 0, 255), -1)
                    else:
                        # Draw all other players with keypoints
                        color_intensity = int(255 * min(conf * 2, 1.0))  # Boost visibility
                        thickness = 2 if is_far_player else 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (color_intensity, 0, 0), thickness)
                        cv2.putText(frame, f"ID:{tid} ({conf:.2f})", (x1, y1-5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (color_intensity, 0, 0), 1)
                        
                        # Draw keypoints for ALL players
                        if keypoints is not None:
                            for kpt in keypoints:
                                if kpt[0] > 0 and kpt[1] > 0:
                                    cv2.circle(frame, (int(kpt[0]), int(kpt[1])), 2, (0, 255, 255), -1)
            
            # Clean up lost players (longer timeout for far players)
            lost_players = [tid for tid, data in all_players.items() 
                          if frame_count - data['last_seen'] > 90]  # Increased from 60 to 90
            for tid in lost_players:
                del all_players[tid]
            
            # Check if raider returned to baseline (immediate raid end)
            if self.raid_active and self.raider_id in all_players:
                if all_players[self.raider_id]['baseline_side'] is not None:
                    recent_sides = all_players[self.raider_id]['side_history'][-5:]
                    if len(recent_sides) >= 5:
                        baseline_count = sum(1 for s in recent_sides if s == all_players[self.raider_id]['baseline_side'])
                        if baseline_count >= 4:
                            print(f"🔙 Raider returned to baseline, ending raid (SUCCESS)")
                            # Mark as successful return
                            self.current_raid['returned_to_baseline'] = True
                            # Save key frame: Raid End
                            cv2.imwrite(f"{self.keyframes_dir}/raid_{len(self.raids)+1}_end_frame_{frame_count}.jpg", frame)
                            self.end_raid(frame_count, all_players)
            
            # AGGRESSIVE RAIDER RECOVERY - Enhanced
            if self.raid_active and not raider_detected_this_frame:
                self.missing_frames += 1
                
                # Try to recover raider immediately
                if results and results[0].boxes.id is not None and self.raider_id in all_players:
                    if len(all_players[self.raider_id]['positions']) > 0:
                        last_raider_pos = all_players[self.raider_id]['positions'][-1]
                        best_candidate = None
                        min_distance = float('inf')
                        
                        for i, box in enumerate(results[0].boxes):
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            tid = int(box.id[0])
                            
                            # Get center with pose if available
                            if results[0].keypoints is not None and i < len(results[0].keypoints):
                                kpts = results[0].keypoints[i].xy.cpu().numpy()[0]
                                valid_kpts = kpts[kpts[:, 0] > 0]
                                if len(valid_kpts) >= 4:
                                    cx = int(np.mean(valid_kpts[:, 0]))
                                    cy = int(np.mean(valid_kpts[:, 1]))
                                else:
                                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            else:
                                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            
                            # Only consider players inside play box
                            if not self.court_dynamics.is_inside_play_box((cx, cy)):
                                continue
                            
                            side = self.point_side(cx, cy)
                            
                            # Check if on opposite side (potential raider)
                            if tid in all_players and all_players[tid]['baseline_side'] is not None:
                                if side != all_players[tid]['baseline_side']:
                                    dist = np.sqrt((cx - last_raider_pos[0])**2 + (cy - last_raider_pos[1])**2)
                                    if dist < 400 and dist < min_distance:  # Increased search radius
                                        min_distance = dist
                                        best_candidate = tid
                            # Also check unknown players (new detections)
                            elif tid not in all_players:
                                dist = np.sqrt((cx - last_raider_pos[0])**2 + (cy - last_raider_pos[1])**2)
                                if dist < 300 and dist < min_distance:
                                    min_distance = dist
                                    best_candidate = tid
                        
                        # Recover immediately if found
                        if best_candidate:
                            # STRICT: Only switch if very close or same ID reappeared
                            if min_distance < 200 or best_candidate == self.raider_id:
                                print(f"⚡ Raider recovered: {self.raider_id} -> {best_candidate} (dist: {min_distance:.0f}px)")
                                self.raider_id = best_candidate
                                self.missing_frames = 0
                                raider_detected_this_frame = True
                                self.raider_locked = True
                
                if self.missing_frames > 0 and self.raider_id in all_players:
                    if len(all_players[self.raider_id]['positions']) > 0:
                        last_pos = all_players[self.raider_id]['positions'][-1]
                        cv2.circle(frame, (last_pos[0], last_pos[1]), 30, (0, 165, 255), 3)
                        cv2.putText(frame, f"SEARCHING {self.missing_frames}", 
                                   (last_pos[0]-50, last_pos[1]-40), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                
                if self.missing_frames > 120:  # Increased from 60 to 120 frames (4 seconds)
                    print(f"❌ Raider lost, ending raid")
                    # Save key frame: Raid Lost
                    cv2.imwrite(f"{self.keyframes_dir}/raid_{len(self.raids)+1}_lost_frame_{frame_count}.jpg", frame)
                    self.end_raid(frame_count, all_players)
            
            # Display status
            status = f"Raids: {len(self.raids)} | Frame: {frame_count} | Players: {len(current_frame_players)}"
            if self.raid_active:
                raid_duration = (frame_count - self.current_raid['start_frame']) / self.fps
                status += f" | RAID - P{self.raider_id} ({raid_duration:.1f}s)"
                if self.missing_frames > 0:
                    status += f" [LOST:{self.missing_frames}]"
                if self.raider_locked:
                    status += " [LOCKED]"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if display:
                display_frame = cv2.resize(frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
                cv2.imshow("Data Extraction", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        if self.raid_active:
            self.end_raid(frame_count, all_players)
        
        self.cap.release()
        if display:
            cv2.destroyAllWindows()
        
        return self.raids
    
    def start_raid(self, raider_id, frame, all_players):
        self.raid_active = True
        self.raider_id = raider_id
        self.raider_locked = True
        self.missing_frames = 0
        
        self.current_raid = {
            'raider_id': raider_id,
            'start_frame': frame,
            'positions': [],
            'defenders': {}
        }
        
        print(f"🏃 Raid started - Raider {raider_id} LOCKED at frame {frame}")
    
    def end_raid(self, frame, all_players):
        if not self.current_raid:
            return
        
        self.current_raid['end_frame'] = frame
        
        if self.raider_id in all_players:
            self.current_raid['positions'] = all_players[self.raider_id]['positions'].copy()
        
        raider_side = all_players[self.raider_id]['baseline_side'] if self.raider_id in all_players else None
        for tid, data in all_players.items():
            if tid != self.raider_id and raider_side is not None and data['baseline_side'] is not None and data['baseline_side'] == -raider_side:
                self.current_raid['defenders'][tid] = data['positions'].copy()
        
        metrics = self.metrics_extractor.extract_raid_metrics(self.current_raid)
        self.raids.append(metrics)
        
        success_status = "SUCCESS" if metrics.get('success', 0) == 1 else "INCOMPLETE"
        print(f"✅ Raid ended ({success_status}) - Duration: {metrics['duration']:.2f}s, Max Penetration: {metrics['max_penetration']:.2f}m")
        
        self.raid_active = False
        self.raider_id = None
        self.raider_locked = False
        self.current_raid = None
        self.missing_frames = 0
    
    def save_results(self, output_path):
        self.metrics_extractor.export_to_csv(self.raids, output_path)


if __name__ == "__main__":
    video_path = "../data/videos/jan2.mp4"
    
    if len(sys.argv) >= 2:
        video_path = sys.argv[1]
    
    try:
        extractor = DataExtractor(video_path)
        print("🎬 Starting data extraction...")
        raids = extractor.extract_data(display=True)
        
        # Save to data/extracted directory
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "extracted")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{video_name}_raid_metrics.csv")
        
        extractor.save_results(output_path)
        
        print(f"\n📊 Extraction complete!")
        print(f"Total raids: {len(raids)}")
        print(f"Saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
