#!/usr/bin/env python3
"""
Simplified Court Dynamics for Kabaddi
Uses 4 parallel lines for accurate penetration calculation
"""

import numpy as np
import json
import os


class SimplifiedCourtDynamics:
    # Official distances from midline (in meters)
    BAULK_DISTANCE = 3.75
    BONUS_DISTANCE = 4.75
    END_DISTANCE = 6.5
    
    def __init__(self, play_box, midline, baulk_line, bonus_line, end_line):
        self.play_box = np.array(play_box)
        self.midline = np.array(midline)
        self.baulk_line = np.array(baulk_line)
        self.bonus_line = np.array(bonus_line)
        self.end_line = np.array(end_line)
        
        # Calculate depth direction using all lines
        self._calculate_depth_direction()
    
    def _calculate_depth_direction(self):
        """Calculate the depth direction vector from midline to end line"""
        mid_center = (self.midline[0] + self.midline[1]) / 2
        end_center = (self.end_line[0] + self.end_line[1]) / 2
        
        # Depth vector (direction from midline to end line)
        self.depth_vector = end_center - mid_center
        self.depth_magnitude = np.linalg.norm(self.depth_vector)
        
        if self.depth_magnitude > 0:
            self.depth_direction = self.depth_vector / self.depth_magnitude
        else:
            self.depth_direction = np.array([0, 1])
        
        self.mid_center = mid_center
        
        print(f"✓ Depth direction calculated: {self.depth_magnitude:.1f} pixels = {self.END_DISTANCE}m")
    
    @classmethod
    def load_from_config(cls, video_path):
        """Load court configuration"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'play_area.json'
        )
        
        if not os.path.exists(config_file):
            raise ValueError(f"Config not found: {config_file}")
        
        with open(config_file, 'r') as f:
            all_configs = json.load(f)
        
        config = None
        if video_path in all_configs:
            config = all_configs[video_path]
        else:
            norm_path = os.path.normpath(video_path)
            for key in all_configs:
                if os.path.normpath(key) == norm_path:
                    config = all_configs[key]
                    break
            
            if config is None:
                basename = os.path.basename(video_path)
                for key in all_configs:
                    if os.path.basename(key) == basename:
                        config = all_configs[key]
                        break
        
        if config is None:
            raise ValueError(f"No config for: {video_path}")
        
        return cls(
            config['play_box'],
            config['midline'],
            config['baulk_line'],
            config['bonus_line'],
            config['end_line']
        )
    
    def is_inside_play_box(self, point):
        """Check if point inside play box"""
        x, y = point
        n = len(self.play_box)
        inside = False
        
        p1x, p1y = self.play_box[0]
        for i in range(1, n + 1):
            p2x, p2y = self.play_box[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def get_penetration_depth(self, point):
        """Calculate penetration in METERS using parallel line projection"""
        x, y = point[:2] if len(point) > 2 else point
        
        # Vector from midline center to point
        point_vector = np.array([float(x), float(y)]) - self.mid_center
        
        # Project onto depth direction
        projection = float(np.dot(point_vector, self.depth_direction))
        
        # Convert pixels to meters with higher precision
        # projection is in pixels, depth_magnitude is pixels for END_DISTANCE meters
        meters = (projection / float(self.depth_magnitude)) * self.END_DISTANCE
        
        return float(max(0.0, meters))
    
    def crossed_baulk_line(self, point):
        """Check if penetration >= 3.75m"""
        return self.get_penetration_depth(point) >= self.BAULK_DISTANCE
    
    def crossed_bonus_line(self, point):
        """Check if penetration >= 4.75m"""
        return self.get_penetration_depth(point) >= self.BONUS_DISTANCE
    
    def analyze_raid_path(self, positions):
        """Analyze raid path"""
        if not positions:
            return {'total_distance': 0, 'avg_speed': 0, 'direction_changes': 0}
        
        total_distance = 0
        for i in range(1, len(positions)):
            x1, y1 = positions[i-1][:2]
            x2, y2 = positions[i][:2]
            total_distance += np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        direction_changes = 0
        if len(positions) >= 3:
            for i in range(1, len(positions) - 1):
                x1, y1 = positions[i-1][:2]
                x2, y2 = positions[i][:2]
                x3, y3 = positions[i+1][:2]
                
                v1 = (x2 - x1, y2 - y1)
                v2 = (x3 - x2, y3 - y2)
                
                dot = v1[0] * v2[0] + v1[1] * v2[1]
                if dot < 0:
                    direction_changes += 1
        
        avg_speed = total_distance / len(positions) if len(positions) > 0 else 0
        
        return {
            'total_distance': total_distance,
            'avg_speed': avg_speed,
            'direction_changes': direction_changes
        }
