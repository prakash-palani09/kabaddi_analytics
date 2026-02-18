#!/usr/bin/env python3
"""
Minimal Data Extractor for Kabaddi Video Analytics
Extracts basic raid metrics from video for player ranking
"""

import cv2
import numpy as np
import csv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline
from court.court_dynamics import HalfCourtDynamics
import json

class DataExtractor:
    def __init__(self, video_path):
        self.video_path = video_path
        # Use model from models folder
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "yolov8n-pose.pt")
        self.model = YOLO(model_path)
        
        # Load midline
        if not has_midline(video_path):
            raise ValueError("No midline found. Run setup first.")
        
        midline_data = load_midline(video_path)
        self.p1, self.p2 = midline_data["p1"], midline_data["p2"]
        
        # Load court lines (baulk and bonus)
        self.court_lines = self.load_court_lines(video_path)
        
        # Initialize court dynamics
        self.court_dynamics = HalfCourtDynamics(self.p1, self.p2)
        
        # Video setup
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Data storage
        self.raids = []
        
        # Tracking state
        self.player_side = {}
        self.side_count = {}
        self.raider_id = None
        self.raid_active = False
        self.raid_start = None
        self.positions = []
        
        # Recovery state
        self.missing_frames = 0
        self.max_missing = 60
        self.last_raider_pos = None
        self.raider_keypoints = None
    
    def load_court_lines(self, video_path):
        """Load baulk and bonus lines"""
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'court_lines.json')
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                all_configs = json.load(f)
                return all_configs.get(video_path, {})
        return {}  # Store raider's pose keypoints
    
    def point_side(self, x, y):
        """Which side of midline"""
        return np.sign((self.p2[0] - self.p1[0]) * (y - self.p1[1]) - 
                      (self.p2[1] - self.p1[1]) * (x - self.p1[0]))
    
    def distance_to_midline(self, x, y):
        """Distance from point to midline"""
        A = self.p2[1] - self.p1[1]
        B = self.p1[0] - self.p2[0]
        C = self.p2[0] * self.p1[1] - self.p1[0] * self.p2[1]
        return abs(A * x + B * y + C) / np.sqrt(A * A + B * B)
    
    def extract_data(self, display=True):
        """Extract raid data from video - Enhanced tracking for ALL players"""
        frame_count = 0
        DISPLAY_SCALE = 0.6
        
        # Enhanced tracking for ALL players
        all_players = {}  # {track_id: {'positions': [], 'keypoints': [], 'side_history': [], 'confidence': []}}
        
        if display:
            cv2.namedWindow("Data Extraction", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Draw midline
            cv2.line(frame, self.p1, self.p2, (0, 255, 255), 2)
            
            # Draw court lines if available
            if self.court_lines:
                if 'baulk_line' in self.court_lines and len(self.court_lines['baulk_line']) == 2:
                    cv2.line(frame, tuple(self.court_lines['baulk_line'][0]), 
                            tuple(self.court_lines['baulk_line'][1]), (0, 0, 255), 2)
                    cv2.putText(frame, "BAULK", tuple(self.court_lines['baulk_line'][0]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                if 'bonus_line' in self.court_lines and len(self.court_lines['bonus_line']) == 2:
                    cv2.line(frame, tuple(self.court_lines['bonus_line'][0]), 
                            tuple(self.court_lines['bonus_line'][1]), (0, 255, 0), 2)
                    cv2.putText(frame, "BONUS", tuple(self.court_lines['bonus_line'][0]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Enhanced tracking with aggressive detection for distant players
            results = self.model.track(
                frame, 
                persist=True, 
                conf=0.2,    # Even lower for distant players
                iou=0.4,     # Lower IoU for better separation
                verbose=False,
                tracker="bytetrack.yaml",
                imgsz=1280   # Higher resolution for better small object detection
            )
            
            current_frame_players = set()
            raider_detected_this_frame = False
            
            if results and results[0].boxes.id is not None:
                for i, box in enumerate(results[0].boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    conf = float(box.conf[0])
                    current_frame_players.add(tid)
                    
                    # Get pose keypoints with better center calculation
                    keypoints = None
                    if results[0].keypoints is not None and i < len(results[0].keypoints):
                        kpts = results[0].keypoints[i].xy.cpu().numpy()[0]
                        if len(kpts) > 0:
                            keypoints = kpts
                            # Use torso center (shoulders + hips) for more stable tracking
                            valid_kpts = kpts[kpts[:, 0] > 0]
                            if len(valid_kpts) >= 4:  # Need at least 4 keypoints
                                # Use shoulders (5,6) and hips (11,12) for body center
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
                    
                    # Update player data with smoothing
                    all_players[tid]['last_seen'] = frame_count
                    all_players[tid]['confidence'].append(conf)
                    
                    # Position smoothing (exponential moving average)
                    if len(all_players[tid]['positions']) > 0:
                        last_pos = all_players[tid]['positions'][-1]
                        alpha = 0.7  # Smoothing factor
                        smooth_cx = int(alpha * cx + (1 - alpha) * last_pos[0])
                        smooth_cy = int(alpha * cy + (1 - alpha) * last_pos[1])
                        cx, cy = smooth_cx, smooth_cy
                    
                    all_players[tid]['positions'].append((cx, cy, frame_count))
                    all_players[tid]['keypoints'].append(keypoints)
                    all_players[tid]['side_history'].append(side)
                    
                    # Keep only recent history (last 30 frames)
                    if len(all_players[tid]['positions']) > 30:
                        all_players[tid]['positions'].pop(0)
                        all_players[tid]['keypoints'].pop(0)
                        all_players[tid]['side_history'].pop(0)
                        all_players[tid]['confidence'].pop(0)
                    
                    # Determine baseline side with higher confidence
                    if len(all_players[tid]['side_history']) >= 15 and all_players[tid]['baseline_side'] is None:
                        sides = all_players[tid]['side_history'][:15]
                        # Use most common side with 70% threshold
                        side_counts = {}
                        for s in sides:
                            side_counts[s] = side_counts.get(s, 0) + 1
                        most_common = max(side_counts, key=side_counts.get)
                        if side_counts[most_common] >= 11:  # 70% of 15
                            all_players[tid]['baseline_side'] = most_common
                    
                    # Enhanced raider detection
                    is_raider = False
                    if all_players[tid]['baseline_side'] is not None:
                        # Check if player is consistently on opposite side
                        recent_sides = all_players[tid]['side_history'][-7:]  # Last 7 frames
                        if len(recent_sides) >= 7:
                            opposite_count = sum(1 for s in recent_sides if s != all_players[tid]['baseline_side'])
                            # Need 6 out of 7 frames on opposite side
                            if opposite_count >= 6:
                                is_raider = True
                    
                    # Draw player with confidence indicator
                    if is_raider:
                        # RAIDER - Red box, thick
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        cv2.putText(frame, f"RAIDER (ID:{tid})", (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Track raid if not already tracking
                        if not self.raid_active:
                            self.raider_id = tid
                            self.raid_active = True
                            self.raid_start = frame_count
                            self.positions = [(cx, cy)]
                            print(f"Raid start: Player {tid} at frame {frame_count}")
                        elif self.raider_id == tid:
                            self.positions.append((cx, cy))
                            
                            # Draw raid path with gradient
                            if len(self.positions) > 1:
                                for j in range(1, len(self.positions)):
                                    thickness = max(1, int(3 * j / len(self.positions)))
                                    cv2.line(frame, self.positions[j-1], self.positions[j], (255, 0, 0), thickness)
                    else:
                        # Regular player - Green box with confidence
                        color_intensity = int(255 * conf)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, color_intensity, 0), 1)
                        cv2.putText(frame, f"ID:{tid} ({conf:.2f})", (x1, y1-5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, color_intensity, 0), 1)
                    
                    # Draw keypoints for raider only
                    if keypoints is not None and is_raider:
                        for kpt in keypoints:
                            if kpt[0] > 0 and kpt[1] > 0:
                                cv2.circle(frame, (int(kpt[0]), int(kpt[1])), 2, (255, 0, 255), -1)
                    
                    # Check raid end
                    if self.raid_active and tid == self.raider_id and not is_raider:
                        # Raider returned to baseline side
                        if side == all_players[tid]['baseline_side']:
                            self.end_raid(frame_count)
                    
                    # Mark if raider was detected
                    if self.raid_active and tid == self.raider_id:
                        raider_detected_this_frame = True
            
            # Clean up lost players (not seen for 60 frames)
            lost_players = [tid for tid, data in all_players.items() 
                          if frame_count - data['last_seen'] > 60]
            for tid in lost_players:
                del all_players[tid]
            
            # AGGRESSIVE RAIDER RECOVERY
            if self.raid_active and not raider_detected_this_frame:
                self.missing_frames += 1
                
                if results and results[0].boxes.id is not None and len(self.positions) > 0:
                    last_raider_pos = self.positions[-1]
                    best_candidate = None
                    min_distance = float('inf')
                    
                    for i, box in enumerate(results[0].boxes):
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        tid = int(box.id[0])
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        side = self.point_side(cx, cy)
                        
                        if tid in all_players and all_players[tid]['baseline_side'] is not None:
                            if side != all_players[tid]['baseline_side']:
                                dist = np.sqrt((cx - last_raider_pos[0])**2 + (cy - last_raider_pos[1])**2)
                                if dist < 300 and dist < min_distance:
                                    min_distance = dist
                                    best_candidate = tid
                    
                    if best_candidate and self.missing_frames >= 3:
                        print(f"⚡ Raider recovered: {self.raider_id} -> {best_candidate}")
                        self.raider_id = best_candidate
                        self.missing_frames = 0
                
                if self.missing_frames > 0 and len(self.positions) > 0:
                    last_pos = self.positions[-1]
                    cv2.circle(frame, last_pos, 30, (0, 165, 255), 3)
                    cv2.putText(frame, f"SEARCHING {self.missing_frames}", 
                               (last_pos[0]-50, last_pos[1]-40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                
                if self.missing_frames > 90:
                    print(f"❌ Raider lost, ending raid")
                    self.end_raid(frame_count, success=0)
            else:
                self.missing_frames = 0
            
            # Display enhanced status
            status = f"Raids: {len(self.raids)} | Frame: {frame_count} | Players: {len(current_frame_players)}"
            if self.raid_active:
                raid_duration = (frame_count - self.raid_start) / self.fps
                status += f" | RAID - P{self.raider_id} ({raid_duration:.1f}s)"
                if self.missing_frames > 0:
                    status += f" [LOST:{self.missing_frames}]"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display video
            if display:
                display_frame = cv2.resize(frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
                cv2.imshow("Data Extraction", display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC to exit
                    break
        
        self.cap.release()
        if display:
            cv2.destroyAllWindows()
        return self.raids
    
    def end_raid(self, frame_count, success=1):
        """End current raid and calculate metrics"""
        duration = (frame_count - self.raid_start) / self.fps
        
        if not self.positions:
            return
        
        # Calculate metrics
        penetration = max(self.distance_to_midline(pos[0], pos[1]) for pos in self.positions)
        
        # Use court dynamics for zone analysis
        zone_analysis = self.court_dynamics.analyze_raid_path(self.positions)
        crossed_bonus = zone_analysis.get('crossed_bonus_line', False)
        crossed_baulk = zone_analysis.get('crossed_baulk_line', False)
        deepest_zone = zone_analysis.get('deepest_zone', 'unknown')
        
        # Movement distance
        total_distance = 0
        for i in range(1, len(self.positions)):
            dx = self.positions[i][0] - self.positions[i-1][0]
            dy = self.positions[i][1] - self.positions[i-1][1]
            total_distance += np.sqrt(dx*dx + dy*dy)
        
        # Speed
        avg_speed = total_distance / len(self.positions) * self.fps if self.positions else 0
        
        # Direction changes
        direction_changes = 0
        if len(self.positions) > 2:
            for i in range(2, len(self.positions)):
                v1 = np.array(self.positions[i-1]) - np.array(self.positions[i-2])
                v2 = np.array(self.positions[i]) - np.array(self.positions[i-1])
                if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                    angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1))
                    if angle > np.pi/3:  # 60 degree threshold
                        direction_changes += 1
        
        # Save raid data
        raid_data = {
            'player_id': f'P{self.raider_id}',
            'duration_sec': round(duration, 2),
            'penetration_px': round(penetration, 1),
            'total_distance': round(total_distance, 1),
            'avg_speed': round(avg_speed, 1),
            'direction_changes': direction_changes,
            'success': success,
            'crossed_bonus': crossed_bonus,
            'crossed_baulk': crossed_baulk,
            'deepest_zone': deepest_zone
        }
        
        self.raids.append(raid_data)
        print(f"Raid end: {duration:.1f}s, {penetration:.0f}px, Success: {success}")
        
        # Reset
        self.raid_active = False
        self.raider_id = None
        self.positions = []
        self.missing_frames = 0
        self.last_raider_pos = None
        self.player_side.clear()
        self.side_count.clear()
    
    def save_csv(self, filename=None):
        """Save data to CSV"""
        if not self.raids:
            print("No raids to save")
            return
        
        # Save to data/extracted folder
        if filename is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "extracted")
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, "extracted_data.csv")
        
        fieldnames = ['player_id', 'duration_sec', 'penetration_px', 'total_distance', 
                     'avg_speed', 'direction_changes', 'success', 'crossed_bonus', 'crossed_baulk', 'deepest_zone']
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.raids)
        
        print(f"Saved {len(self.raids)} raids to {filename}")
        
        # Display extracted metrics summary
        self.display_metrics_summary()
    
    def display_metrics_summary(self):
        """Display comprehensive metrics summary"""
        if not self.raids:
            return
            
        print("\n" + "="*60)
        print("📊 EXTRACTED DATA METRICS SUMMARY")
        print("="*60)
        
        # Overall statistics
        total_raids = len(self.raids)
        successful_raids = sum(1 for r in self.raids if r['success'] == 1)
        success_rate = (successful_raids / total_raids) * 100 if total_raids > 0 else 0
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Raids Detected: {total_raids}")
        print(f"   Successful Raids: {successful_raids}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print()
        
        # Player-wise breakdown
        player_stats = {}
        for raid in self.raids:
            pid = raid['player_id']
            if pid not in player_stats:
                player_stats[pid] = []
            player_stats[pid].append(raid)
        
        print(f"👥 PLAYER PERFORMANCE BREAKDOWN:")
        for player_id, raids in player_stats.items():
            player_success = sum(1 for r in raids if r['success'] == 1)
            player_success_rate = (player_success / len(raids)) * 100
            avg_duration = sum(r['duration_sec'] for r in raids) / len(raids)
            avg_penetration = sum(r['penetration_px'] for r in raids) / len(raids)
            avg_speed = sum(r['avg_speed'] for r in raids) / len(raids)
            
            print(f"   {player_id}:")
            print(f"     Raids: {len(raids)} | Success: {player_success_rate:.1f}%")
            print(f"     Avg Duration: {avg_duration:.1f}s | Avg Penetration: {avg_penetration:.0f}px")
            print(f"     Avg Speed: {avg_speed:.1f} px/s")
            print()
        
        # Top performers
        if len(player_stats) > 1:
            # Sort by success rate then by raid count
            sorted_players = sorted(player_stats.items(), 
                                  key=lambda x: (sum(1 for r in x[1] if r['success'] == 1) / len(x[1]), len(x[1])), 
                                  reverse=True)
            
            print(f"🏆 TOP PERFORMERS:")
            for i, (player_id, raids) in enumerate(sorted_players[:3]):
                success_rate = (sum(1 for r in raids if r['success'] == 1) / len(raids)) * 100
                print(f"   #{i+1} {player_id}: {success_rate:.1f}% success ({len(raids)} raids)")
            print()
        
        # Metrics ranges
        durations = [r['duration_sec'] for r in self.raids]
        penetrations = [r['penetration_px'] for r in self.raids]
        speeds = [r['avg_speed'] for r in self.raids]
        
        print(f"📊 METRICS RANGES:")
        print(f"   Duration: {min(durations):.1f}s - {max(durations):.1f}s (avg: {sum(durations)/len(durations):.1f}s)")
        print(f"   Penetration: {min(penetrations):.0f}px - {max(penetrations):.0f}px (avg: {sum(penetrations)/len(penetrations):.0f}px)")
        print(f"   Speed: {min(speeds):.1f} - {max(speeds):.1f} px/s (avg: {sum(speeds)/len(speeds):.1f} px/s)")
        print()
        
        print(f"💾 DATA SAVED TO: extracted_data.csv")
        print(f"📁 READY FOR PLAYER RANKING ANALYSIS")
        print("="*60)

def main():
    video_path = "data/videos/jan1.mp4"
    
    try:
        extractor = DataExtractor(video_path)
        print("Starting data extraction with video display...")
        print("Press ESC to stop early")
        
        raids = extractor.extract_data(display=True)
        extractor.save_csv()
        
        print(f"\nExtracted {len(raids)} raids")
        if raids:
            print("Sample:", raids[0])
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()