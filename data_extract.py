#!/usr/bin/env python3
"""
Minimal Data Extractor for Kabaddi Video Analytics
Extracts basic raid metrics from video for player ranking
"""

import cv2
import numpy as np
import csv
from ultralytics import YOLO
from court.midline_manager import load_midline, has_midline

class DataExtractor:
    def __init__(self, video_path):
        self.video_path = video_path
        self.model = YOLO("yolov8n.pt")
        
        # Load midline
        if not has_midline(video_path):
            raise ValueError("No midline found. Run setup first.")
        
        midline_data = load_midline(video_path)
        self.p1, self.p2 = midline_data["p1"], midline_data["p2"]
        
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
        self.max_missing = 30  # Allow 30 frames of missing raider
        self.last_raider_pos = None
    
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
        """Extract raid data from video"""
        frame_count = 0
        DISPLAY_SCALE = 0.6
        
        if display:
            cv2.namedWindow("Data Extraction", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Draw midline
            cv2.line(frame, self.p1, self.p2, (0, 255, 255), 2)
            
            # Track players
            results = self.model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
            
            if results and results[0].boxes.id is not None:
                raider_found = False
                
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    tid = int(box.id[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    side = self.point_side(cx, cy)
                    
                    # Draw player box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                    cv2.putText(frame, f"ID {tid}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                    
                    # Track baseline
                    if tid not in self.player_side:
                        self.player_side[tid] = side
                        self.side_count[tid] = 1
                    elif side == self.player_side[tid]:
                        self.side_count[tid] += 1
                    
                    # Raid start
                    if (not self.raid_active and 
                        self.side_count.get(tid, 0) >= 5 and 
                        side != self.player_side[tid]):
                        
                        self.raider_id = tid
                        self.raid_active = True
                        self.raid_start = frame_count
                        self.positions = [(cx, cy)]
                        self.missing_frames = 0
                        self.last_raider_pos = (cx, cy)
                        print(f"Raid start: Player {tid}")
                    
                    # Track raider
                    if self.raid_active and tid == self.raider_id:
                        raider_found = True
                        self.missing_frames = 0
                        self.last_raider_pos = (cx, cy)
                        
                        # Highlight raider
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        cv2.putText(frame, "RAIDER", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        self.positions.append((cx, cy))
                        
                        # Draw path
                        if len(self.positions) > 1:
                            for i in range(1, len(self.positions)):
                                cv2.line(frame, self.positions[i-1], self.positions[i], (255, 0, 0), 2)
                        
                        # Raid end
                        if side == self.player_side[tid]:
                            self.end_raid(frame_count)
                
                # Handle missing raider
                if self.raid_active and not raider_found:
                    self.missing_frames += 1
                    
                    # Try to find replacement raider
                    if self.missing_frames > 5:  # After 5 frames, try to switch
                        best_candidate = None
                        min_distance = float('inf')
                        
                        for box in results[0].boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            tid = int(box.id[0])
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            side = self.point_side(cx, cy)
                            
                            # Only consider players on opponent side
                            if side == self.player_side.get(self.raider_id, 0):
                                continue
                            
                            # Find closest to last known raider position
                            if self.last_raider_pos:
                                dist = np.sqrt((cx - self.last_raider_pos[0])**2 + (cy - self.last_raider_pos[1])**2)
                                if dist < min_distance and dist < 100:  # Within reasonable distance
                                    min_distance = dist
                                    best_candidate = tid
                        
                        if best_candidate:
                            print(f"Raider switched: {self.raider_id} -> {best_candidate}")
                            self.raider_id = best_candidate
                            self.missing_frames = 0
                    
                    # Show missing status
                    if self.last_raider_pos:
                        cv2.circle(frame, self.last_raider_pos, 20, (0, 165, 255), 2)
                        cv2.putText(frame, f"MISSING {self.missing_frames}", 
                                   (self.last_raider_pos[0]-30, self.last_raider_pos[1]-30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                    
                    # End raid if missing too long
                    if self.missing_frames > self.max_missing:
                        print(f"Raider lost, ending raid after {self.missing_frames} frames")
                        self.end_raid(frame_count, success=0)
            
            # Display status
            status = f"Raids: {len(self.raids)} | Frame: {frame_count}"
            if self.raid_active:
                status += f" | RAID ACTIVE - Player {self.raider_id}"
                if self.missing_frames > 0:
                    status += f" (Missing: {self.missing_frames})"
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
            'success': success
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
    
    def save_csv(self, filename="extracted_data.csv"):
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
    video_path = "data/videos/current_video.mp4"
    
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