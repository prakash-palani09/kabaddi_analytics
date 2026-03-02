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
        
        print(f"✓ Court setup:")
        print(f"  Midline center: {mid_center}")
        print(f"  End line center: {end_center}")
        print(f"  Distance (pixels): {self.depth_magnitude:.1f}px = {self.END_DISTANCE}m")
        print(f"  Ratio: 1 pixel = {self.END_DISTANCE/self.depth_magnitude:.4f}m")
        
        # Calculate actual line depths
        baulk_center = (self.baulk_line[0] + self.baulk_line[1]) / 2
        baulk_vector = baulk_center - mid_center
        baulk_projection = np.dot(baulk_vector, self.depth_direction)
        baulk_depth = (baulk_projection / self.depth_magnitude) * self.END_DISTANCE
        
        bonus_center = (self.bonus_line[0] + self.bonus_line[1]) / 2
        bonus_vector = bonus_center - mid_center
        bonus_projection = np.dot(bonus_vector, self.depth_direction)
        bonus_depth = (bonus_projection / self.depth_magnitude) * self.END_DISTANCE
        
        print(f"  Baulk line at: {baulk_depth:.2f}m (marked as 3.75m)")
        print(f"  Bonus line at: {bonus_depth:.2f}m (marked as 4.75m)")
    
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
        """Calculate penetration in METERS using perpendicular distance to midline
        
        Uses true perpendicular distance formula:
        distance = |Ax + By + C| / sqrt(A² + B²)
        """
        x, y = point[:2] if len(point) > 2 else point
        
        # Midline coefficients: Ax + By + C = 0
        x1, y1 = float(self.midline[0][0]), float(self.midline[0][1])
        x2, y2 = float(self.midline[1][0]), float(self.midline[1][1])
        
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # Perpendicular distance from point to midline
        denominator = np.sqrt(A * A + B * B)
        if denominator == 0:
            return 0.0
        
        pixel_distance = abs(A * float(x) + B * float(y) + C) / denominator
        
        # Total perpendicular distance from midline to endline
        # Use endline center point
        ex, ey = float(self.end_line[0][0]), float(self.end_line[0][1])
        total_pixel_depth = abs(A * ex + B * ey + C) / denominator
        
        if total_pixel_depth == 0:
            return 0.0
        
        # Convert to meters
        meters = (pixel_distance / total_pixel_depth) * self.END_DISTANCE
        
        return float(max(0.0, meters))
    
    def crossed_baulk_line(self, point):
        """Check if point crossed the physical baulk line (treat as parallel)"""
        penetration = self.get_penetration_depth(point)
        # Get baulk line position in depth direction
        baulk_center = (self.baulk_line[0] + self.baulk_line[1]) / 2
        baulk_vector = baulk_center - self.mid_center
        baulk_projection = float(np.dot(baulk_vector, self.depth_direction))
        baulk_depth = (baulk_projection / float(self.depth_magnitude)) * self.END_DISTANCE
        
        # If raider penetration >= baulk line depth, they crossed it
        return penetration >= baulk_depth
    
    def crossed_bonus_line(self, point):
        """Check if point crossed the physical bonus line (treat as parallel)"""
        penetration = self.get_penetration_depth(point)
        # Get bonus line position in depth direction
        bonus_center = (self.bonus_line[0] + self.bonus_line[1]) / 2
        bonus_vector = bonus_center - self.mid_center
        bonus_projection = float(np.dot(bonus_vector, self.depth_direction))
        bonus_depth = (bonus_projection / float(self.depth_magnitude)) * self.END_DISTANCE
        
        # If raider penetration >= bonus line depth, they crossed it
        return penetration >= bonus_depth
    
    def get_line_depth(self, line_name):
        """Get the actual depth of a marked line in meters"""
        if line_name == 'baulk':
            line_center = (self.baulk_line[0] + self.baulk_line[1]) / 2
        elif line_name == 'bonus':
            line_center = (self.bonus_line[0] + self.bonus_line[1]) / 2
        else:
            return 0.0
        
        line_vector = line_center - self.mid_center
        line_projection = float(np.dot(line_vector, self.depth_direction))
        return (line_projection / float(self.depth_magnitude)) * self.END_DISTANCE
    
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
