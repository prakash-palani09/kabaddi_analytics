#!/usr/bin/env python3
"""
Video Analytics Data Extractor for Kabaddi Player Ranking
Extracts performance metrics from match videos for player evaluation
"""

import cv2
import numpy as np
import csv
import os
from datetime import datetime
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline

class KabaddiVideoAnalytics:
    def __init__(self, video_path, model_path="yolov8n.pt"):
        self.video_path = video_path
        self.model_path = model_path
        self.model = YOLO(model_path)
        
        # Load midline configuration
        if not has_midline(video_path):
            raise ValueError("No midline configuration found. Run setup_midline.py first.")
        
        midline_data = load_midline(video_path)
        self.p1, self.p2 = midline_data["p1"], midline_data["p2"]
        
        # Analytics data storage
        self.raid_data = []
        self.current_raid = None
        
        # Tracking state
        self.player_baseline_side = {}
        self.baseline_counter = {}
        self.raider_track_id = None
        self.raid_active = False
        self.raid_start_frame = None
        
        # Video properties
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = 0
        
    def point_side(self, x, y):
        """Determine which side of midline a point is on"""
        return np.sign((self.p2[0] - self.p1[0]) * (y - self.p1[1]) - 
                      (self.p2[1] - self.p1[1]) * (x - self.p1[0]))
    
    def distance_to_midline(self, x, y):
        """Calculate perpendicular distance from point to midline"""
        A = self.p2[1] - self.p1[1]
        B = self.p1[0] - self.p2[0]
        C = self.p2[0] * self.p1[1] - self.p1[0] * self.p2[1]
        return abs(A * x + B * y + C) / np.sqrt(A * A + B * B)
    
    def calculate_movement_metrics(self, positions):
        """Calculate movement-based metrics from position history"""
        if len(positions) < 2:
            return {
                'total_distance': 0,
                'avg_speed': 0,
                'max_speed': 0,
                'direction_changes': 0,
                'acceleration_changes': 0
            }
        
        # Calculate distances and speeds
        distances = []
        speeds = []
        directions = []
        
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            
            # Distance between consecutive positions
            dist = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
            distances.append(dist)
            
            # Speed (distance per frame * fps = pixels per second)
            speed = dist * self.fps
            speeds.append(speed)
            
            # Direction (angle)
            if dist > 0:
                angle = np.arctan2(curr_pos[1] - prev_pos[1], curr_pos[0] - prev_pos[0])
                directions.append(angle)
        
        # Count direction changes (significant angle changes)
        direction_changes = 0
        for i in range(1, len(directions)):
            angle_diff = abs(directions[i] - directions[i-1])
            if angle_diff > np.pi/4:  # 45 degree threshold
                direction_changes += 1
        
        # Count acceleration changes
        acceleration_changes = 0
        for i in range(1, len(speeds)):
            if len(speeds) > 1:
                speed_diff = abs(speeds[i] - speeds[i-1])
                if speed_diff > 50:  # Significant speed change threshold
                    acceleration_changes += 1
        
        return {
            'total_distance': sum(distances),
            'avg_speed': np.mean(speeds) if speeds else 0,
            'max_speed': max(speeds) if speeds else 0,
            'direction_changes': direction_changes,
            'acceleration_changes': acceleration_changes
        }
    
    def extract_raid_metrics(self, raider_positions, raid_duration_frames):
        """Extract comprehensive raid metrics"""
        if not raider_positions:
            return None
        
        # Basic metrics
        duration_sec = raid_duration_frames / self.fps
        
        # Penetration depth (maximum distance from midline)
        max_penetration = 0
        for pos in raider_positions:
            penetration = self.distance_to_midline(pos[0], pos[1])
            max_penetration = max(max_penetration, penetration)
        
        # Movement metrics
        movement_metrics = self.calculate_movement_metrics(raider_positions)
        
        # Spatial metrics
        start_pos = raider_positions[0]
        end_pos = raider_positions[-1]
        
        # Court coverage (bounding box area)
        x_coords = [pos[0] for pos in raider_positions]
        y_coords = [pos[1] for pos in raider_positions]
        court_coverage = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        
        # Escape efficiency (straight line vs actual path)
        straight_distance = np.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
        escape_efficiency = straight_distance / movement_metrics['total_distance'] if movement_metrics['total_distance'] > 0 else 0
        
        return {
            'duration_sec': duration_sec,
            'penetration_px': max_penetration,
            'total_distance': movement_metrics['total_distance'],
            'avg_speed': movement_metrics['avg_speed'],
            'max_speed': movement_metrics['max_speed'],
            'direction_changes': movement_metrics['direction_changes'],
            'acceleration_changes': movement_metrics['acceleration_changes'],
            'court_coverage': court_coverage,
            'escape_efficiency': escape_efficiency,
            'start_side': self.point_side(start_pos[0], start_pos[1]),
            'end_side': self.point_side(end_pos[0], end_pos[1])
        }
    
    def process_video(self, output_csv="video_analytics_data.csv"):
        """Process entire video and extract analytics data"""
        print(f"🎬 Processing video: {self.video_path}")
        print(f"📊 Midline: {self.p1} to {self.p2}")
        
        raider_positions = []
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Run YOLO tracking
            results = self.model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
            
            if results and results[0].boxes.id is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    side = self.point_side(cx, cy)
                    
                    # Track player baseline
                    if tid not in self.player_baseline_side:
                        self.player_baseline_side[tid] = side
                        self.baseline_counter[tid] = 1
                    else:
                        if side == self.player_baseline_side[tid]:
                            self.baseline_counter[tid] += 1
                    
                    # Detect raid start
                    if (not self.raid_active and 
                        self.baseline_counter.get(tid, 0) >= 5 and 
                        side != self.player_baseline_side[tid]):
                        
                        self.raider_track_id = tid
                        self.raid_active = True
                        self.raid_start_frame = self.frame_count
                        raider_positions = [(cx, cy)]
                        
                        print(f"🏃 RAID START | Player {tid} | Frame {self.frame_count}")
                    
                    # Track active raider
                    if self.raid_active and tid == self.raider_track_id:
                        raider_positions.append((cx, cy))
                        
                        # Detect raid end
                        if side == self.player_baseline_side[tid]:
                            raid_duration = self.frame_count - self.raid_start_frame
                            
                            # Extract metrics
                            metrics = self.extract_raid_metrics(raider_positions, raid_duration)
                            
                            if metrics:
                                # Determine success (simplified: if raider returns to start side)
                                success = 1 if metrics['end_side'] == metrics['start_side'] else 0
                                
                                raid_record = {
                                    'match_id': f"V_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                    'player_id': f"P{tid}",
                                    'raid_duration_sec': round(metrics['duration_sec'], 2),
                                    'penetration_px': round(metrics['penetration_px'], 1),
                                    'success': success,
                                    'total_distance': round(metrics['total_distance'], 1),
                                    'avg_speed': round(metrics['avg_speed'], 1),
                                    'max_speed': round(metrics['max_speed'], 1),
                                    'direction_changes': metrics['direction_changes'],
                                    'acceleration_changes': metrics['acceleration_changes'],
                                    'court_coverage': round(metrics['court_coverage'], 1),
                                    'escape_efficiency': round(metrics['escape_efficiency'], 3),
                                    'frame_start': self.raid_start_frame,
                                    'frame_end': self.frame_count
                                }
                                
                                self.raid_data.append(raid_record)
                                print(f"✅ RAID END | Duration: {metrics['duration_sec']:.1f}s | Penetration: {metrics['penetration_px']:.0f}px")
                            
                            # Reset raid state
                            self.raid_active = False
                            self.raider_track_id = None
                            raider_positions = []
                            self.player_baseline_side.clear()
                            self.baseline_counter.clear()
            
            # Progress update
            if self.frame_count % 100 == 0:
                print(f"📈 Processed {self.frame_count} frames | Raids detected: {len(self.raid_data)}")
        
        self.cap.release()
        
        # Save data to CSV
        if self.raid_data:
            self.save_to_csv(output_csv)
            print(f"💾 Saved {len(self.raid_data)} raid records to {output_csv}")
        else:
            print("⚠️ No raids detected in video")
        
        return self.raid_data
    
    def save_to_csv(self, filename):
        """Save extracted data to CSV file"""
        fieldnames = [
            'match_id', 'player_id', 'raid_duration_sec', 'penetration_px', 'success',
            'total_distance', 'avg_speed', 'max_speed', 'direction_changes', 
            'acceleration_changes', 'court_coverage', 'escape_efficiency',
            'frame_start', 'frame_end'
        ]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.raid_data)

def main():
    """Main execution function"""
    video_path = "data/videos/current_video.mp4"
    
    if not os.path.exists(video_path):
        print("❌ Video file not found. Please place video at data/videos/current_video.mp4")
        return
    
    try:
        # Initialize analytics
        analytics = KabaddiVideoAnalytics(video_path)
        
        # Process video and extract data
        raid_data = analytics.process_video("extracted_video_data.csv")
        
        print(f"\n🎯 EXTRACTION COMPLETE!")
        print(f"📊 Total raids analyzed: {len(raid_data)}")
        print(f"📁 Data saved to: extracted_video_data.csv")
        
        # Display sample metrics
        if raid_data:
            print(f"\n📈 Sample Metrics:")
            sample = raid_data[0]
            print(f"   Duration: {sample['raid_duration_sec']}s")
            print(f"   Penetration: {sample['penetration_px']}px")
            print(f"   Speed: {sample['avg_speed']:.1f} px/s")
            print(f"   Direction Changes: {sample['direction_changes']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()