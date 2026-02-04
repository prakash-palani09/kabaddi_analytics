#!/usr/bin/env python3
"""
Enhanced Kabaddi Data Extractor with Stable Tracking and Pose Estimation
"""

import cv2
import numpy as np
import csv
import sys
import os
sys.path.append('..')
import mediapipe as mp
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline

class EnhancedDataExtractor:
    def __init__(self, video_path):
        self.video_path = video_path
        self.model = YOLO("../yolov8n.pt")
        
        # MediaPipe setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Load midline
        if not has_midline(video_path):
            raise ValueError("No midline found. Run setup first.")
        
        midline_data = load_midline(video_path)
        self.p1, self.p2 = midline_data["p1"], midline_data["p2"]
        
        # Video setup
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Enhanced tracking
        self.player_tracks = {}  # Store player history
        self.raids = []
        self.raid_active = False
        self.raider_id = None
        self.raid_start = None
        self.positions = []
        
        # Stability parameters
        self.min_baseline_frames = 10
        self.max_jump_distance = 150  # Max pixel jump between frames
        self.smoothing_window = 3
    
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
    
    def smooth_position(self, player_id, new_pos):
        """Apply position smoothing to reduce jitter"""
        if player_id not in self.player_tracks:
            self.player_tracks[player_id] = {'positions': [], 'sides': [], 'stable_side': None}
        
        track = self.player_tracks[player_id]
        
        # Check for unrealistic jumps
        if track['positions']:
            last_pos = track['positions'][-1]
            distance = np.sqrt((new_pos[0] - last_pos[0])**2 + (new_pos[1] - last_pos[1])**2)
            
            if distance > self.max_jump_distance:
                # Use predicted position instead
                if len(track['positions']) >= 2:
                    # Linear prediction
                    prev_pos = track['positions'][-2]
                    velocity = (last_pos[0] - prev_pos[0], last_pos[1] - prev_pos[1])
                    predicted_pos = (last_pos[0] + velocity[0], last_pos[1] + velocity[1])
                    new_pos = predicted_pos
        
        # Add to history
        track['positions'].append(new_pos)
        if len(track['positions']) > self.smoothing_window:
            track['positions'].pop(0)
        
        # Return smoothed position
        if len(track['positions']) >= self.smoothing_window:
            avg_x = sum(pos[0] for pos in track['positions']) / len(track['positions'])
            avg_y = sum(pos[1] for pos in track['positions']) / len(track['positions'])
            return (int(avg_x), int(avg_y))
        
        return new_pos
    
    def update_player_side(self, player_id, side):
        """Update player side with stability check"""
        if player_id not in self.player_tracks:
            self.player_tracks[player_id] = {'positions': [], 'sides': [], 'stable_side': None}
        
        track = self.player_tracks[player_id]
        track['sides'].append(side)
        
        # Keep only recent sides
        if len(track['sides']) > self.min_baseline_frames:
            track['sides'].pop(0)
        
        # Determine stable side
        if len(track['sides']) >= self.min_baseline_frames:
            side_counts = {}
            for s in track['sides']:
                side_counts[s] = side_counts.get(s, 0) + 1
            
            # Stable side is the most common
            most_common_side = max(side_counts, key=side_counts.get)
            if side_counts[most_common_side] >= self.min_baseline_frames * 0.7:
                track['stable_side'] = most_common_side
        
        return track['stable_side']
    
    def get_pose_features(self, frame, bbox):
        """Extract pose features using MediaPipe"""
        x1, y1, x2, y2 = bbox
        
        # Expand bbox slightly for better pose detection
        margin = 20
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(frame.shape[1], x2 + margin)
        y2 = min(frame.shape[0], y2 + margin)
        
        person_crop = frame[y1:y2, x1:x2]
        
        if person_crop.size == 0:
            return None
        
        # Convert to RGB for MediaPipe
        rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_crop)
        
        if results.pose_landmarks:
            # Extract key pose features
            landmarks = results.pose_landmarks.landmark
            
            # Body center (average of shoulders and hips)
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            body_center_x = (left_shoulder.x + right_shoulder.x + left_hip.x + right_hip.x) / 4
            body_center_y = (left_shoulder.y + right_shoulder.y + left_hip.y + right_hip.y) / 4
            
            # Convert back to frame coordinates
            global_x = x1 + body_center_x * (x2 - x1)
            global_y = y1 + body_center_y * (y2 - y1)
            
            return {
                'body_center': (int(global_x), int(global_y)),
                'pose_confidence': min([left_shoulder.visibility, right_shoulder.visibility, 
                                      left_hip.visibility, right_hip.visibility])
            }
        
        return None
    
    def extract_data(self, display=True):
        """Extract raid data with enhanced tracking"""
        frame_count = 0
        DISPLAY_SCALE = 0.6
        missing_frames = 0
        max_missing = 15  # Reduced from 30 for better recovery
        
        if display:
            cv2.namedWindow("Enhanced Data Extraction", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Draw midline
            cv2.line(frame, self.p1, self.p2, (0, 255, 255), 2)
            
            # Detect players
            results = self.model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
            
            raider_found = False
            
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    
                    # Get pose-based center if possible
                    pose_data = self.get_pose_features(frame, (x1, y1, x2, y2))
                    if pose_data and pose_data['pose_confidence'] > 0.5:
                        cx, cy = pose_data['body_center']
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), -1)  # Magenta dot for pose center
                    else:
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Apply position smoothing
                    smooth_pos = self.smooth_position(tid, (cx, cy))
                    cx, cy = smooth_pos
                    
                    # Update side tracking
                    current_side = self.point_side(cx, cy)
                    stable_side = self.update_player_side(tid, current_side)
                    
                    # Draw player
                    color = (0, 255, 0) if stable_side is None else (0, 200, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                    cv2.putText(frame, f"ID {tid}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    cv2.circle(frame, (cx, cy), 3, color, -1)
                    
                    # Raid detection
                    if stable_side is not None:
                        # Raid start
                        if (not self.raid_active and 
                            current_side != stable_side and
                            abs(current_side - stable_side) > 0.3):  # More lenient threshold
                            
                            self.raider_id = tid
                            self.raid_active = True
                            self.raid_start = frame_count
                            self.positions = [(cx, cy)]
                            missing_frames = 0
                            print(f"Raid start: Player {tid} (Side: {stable_side} -> {current_side})")
                        
                        # Track active raider
                        if self.raid_active and tid == self.raider_id:
                            raider_found = True
                            missing_frames = 0
                            
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.putText(frame, "RAIDER", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
                            self.positions.append((cx, cy))
                            
                            # Draw smooth path
                            if len(self.positions) > 1:
                                for i in range(1, len(self.positions)):
                                    cv2.line(frame, self.positions[i-1], self.positions[i], (255, 0, 0), 2)
                            
                            # Raid end - return to stable side
                            if abs(current_side - stable_side) < 0.4:  # More lenient return threshold
                                self.end_raid(frame_count)
                
                # Handle missing raider with aggressive recovery
                if self.raid_active and not raider_found:
                    missing_frames += 1
                    
                    # Try to find replacement raider immediately
                    if missing_frames > 2:  # Start looking after just 2 frames
                        best_candidate = None
                        min_distance = float('inf')
                        
                        # Get last known position
                        last_pos = self.positions[-1] if self.positions else None
                        
                        for box in results[0].boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            tid = int(box.id[0])
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            current_side = self.point_side(cx, cy)
                            
                            # Only consider players on opponent side
                            original_side = None
                            if self.raider_id in self.player_tracks:
                                original_side = self.player_tracks[self.raider_id].get('stable_side')
                            
                            if original_side is not None and abs(current_side - original_side) < 0.3:
                                continue  # Skip players on original side
                            
                            # Find closest to last known position
                            if last_pos:
                                dist = np.sqrt((cx - last_pos[0])**2 + (cy - last_pos[1])**2)
                                if dist < min_distance and dist < 200:  # Increased search radius
                                    min_distance = dist
                                    best_candidate = tid
                        
                        if best_candidate:
                            print(f"Raider switched: {self.raider_id} -> {best_candidate} (distance: {min_distance:.1f})")
                            self.raider_id = best_candidate
                            missing_frames = 0
                            raider_found = True
                    
                    # Show missing status
                    if last_pos and not raider_found:
                        cv2.circle(frame, last_pos, 25, (0, 165, 255), 3)
                        cv2.putText(frame, f"SEARCHING {missing_frames}", 
                                   (last_pos[0]-40, last_pos[1]-35), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    
                    # End raid if missing too long
                    if missing_frames > max_missing:
                        print(f"Raider lost permanently after {missing_frames} frames, ending raid")
                        self.end_raid(frame_count)
                        missing_frames = 0
            
            # Display status
            status = f"Raids: {len(self.raids)} | Frame: {frame_count}"
            if self.raid_active:
                status += f" | RAID ACTIVE - Player {self.raider_id}"
                if missing_frames > 0:
                    status += f" (Missing: {missing_frames})"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display
            if display:
                display_frame = cv2.resize(frame, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
                cv2.imshow("Enhanced Data Extraction", display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
        
        self.cap.release()
        if display:
            cv2.destroyAllWindows()
        return self.raids
    
    def end_raid(self, frame_count):
        """End raid and calculate metrics"""
        if not self.positions:
            return
        
        duration = (frame_count - self.raid_start) / self.fps
        
        # Calculate metrics
        penetration = max(self.distance_to_midline(pos[0], pos[1]) for pos in self.positions)
        
        # Smooth movement distance
        total_distance = 0
        for i in range(1, len(self.positions)):
            dx = self.positions[i][0] - self.positions[i-1][0]
            dy = self.positions[i][1] - self.positions[i-1][1]
            total_distance += np.sqrt(dx*dx + dy*dy)
        
        avg_speed = total_distance / len(self.positions) * self.fps if self.positions else 0
        
        # Direction changes (more stable calculation)
        direction_changes = 0
        if len(self.positions) > 4:  # Need more points for stable calculation
            for i in range(3, len(self.positions)-1):
                # Use 3-point windows for stability
                v1 = np.array(self.positions[i-1]) - np.array(self.positions[i-3])
                v2 = np.array(self.positions[i+1]) - np.array(self.positions[i-1])
                
                if np.linalg.norm(v1) > 10 and np.linalg.norm(v2) > 10:  # Minimum movement threshold
                    angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1))
                    if angle > np.pi/2:  # 90 degree threshold for significant direction change
                        direction_changes += 1
        
        # Save data
        raid_data = {
            'player_id': f'P{self.raider_id}',
            'duration_sec': round(duration, 2),
            'penetration_px': round(penetration, 1),
            'total_distance': round(total_distance, 1),
            'avg_speed': round(avg_speed, 1),
            'direction_changes': direction_changes,
            'success': 1
        }
        
        self.raids.append(raid_data)
        print(f"Raid end: {duration:.1f}s, {penetration:.0f}px, Distance: {total_distance:.0f}px")
        
        # Reset
        self.raid_active = False
        self.raider_id = None
        self.positions = []
    
    def save_csv(self, filename="enhanced_extracted_data.csv"):
        """Save data to CSV"""
        if not self.raids:
            print("No raids to save")
            return
        
        fieldnames = ['player_id', 'duration_sec', 'penetration_px', 'total_distance', 
                     'avg_speed', 'direction_changes', 'success']
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.raids)
        
        print(f"Saved {len(self.raids)} raids to {filename}")

def main():
    video_path = "../data/videos/current_video.mp4"
    
    try:
        extractor = EnhancedDataExtractor(video_path)
        print("Starting enhanced data extraction...")
        print("Features: Pose estimation, Position smoothing, Stable tracking")
        print("Press ESC to stop")
        
        raids = extractor.extract_data(display=True)
        extractor.save_csv()
        
        print(f"\nExtracted {len(raids)} raids")
        if raids:
            print("Sample:", raids[0])
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()