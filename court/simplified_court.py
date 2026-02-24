"""
Simplified Court Dynamics for Kabaddi
Uses play box, midline, baulk line, and bonus line
"""

import numpy as np
import json
import os

class SimplifiedCourtDynamics:
    def __init__(self, play_box, midline, baulk_line, bonus_line):
        """
        Args:
            play_box: [p1, p2, p3, ...] - corners of play area (any polygon)
            midline: [p1, p2] - midline points
            baulk_line: [p1, p2] - baulk line points
            bonus_line: [p1, p2] - bonus line points
        """
        self.play_box = [np.array(p) for p in play_box]
        self.midline = [np.array(p) for p in midline]
        self.baulk_line = [np.array(p) for p in baulk_line]
        self.bonus_line = [np.array(p) for p in bonus_line]
    
    def is_inside_play_box(self, point):
        """Check if point is inside play box"""
        x, y = point
        # Simple polygon containment check
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
    
    def distance_to_line(self, point, line):
        """Calculate perpendicular distance from point to line"""
        p1, p2 = line
        x0, y0 = point
        x1, y1 = p1
        x2, y2 = p2
        
        num = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1)
        den = np.sqrt((y2-y1)**2 + (x2-x1)**2)
        
        return num / den if den > 0 else 0
    
    def get_penetration_depth(self, point):
        """Get penetration depth from midline"""
        return self.distance_to_line(point, self.midline)
    
    def crossed_line(self, point, line):
        """Check if point crossed a line (simple side check)"""
        # Check which side of line the point is on
        p1, p2 = line
        d = (point[0] - p1[0]) * (p2[1] - p1[1]) - (point[1] - p1[1]) * (p2[0] - p1[0])
        return d > 0  # Crossed if on positive side
    
    def crossed_bonus_line(self, point):
        """Check if crossed bonus line"""
        dist = self.distance_to_line(point, self.bonus_line)
        return dist > 10  # Small threshold
    
    def crossed_baulk_line(self, point):
        """Check if crossed baulk line"""
        dist = self.distance_to_line(point, self.baulk_line)
        return dist > 10
    
    def analyze_raid_path(self, positions):
        """
        Analyze raid path
        
        Returns:
            dict with penetration metrics
        """
        if not positions:
            return {
                'max_depth': 0,
                'avg_depth': 0,
                'crossed_bonus_line': False,
                'crossed_baulk_line': False,
                'deepest_zone': 'none'
            }
        
        depths = [self.get_penetration_depth(pos) for pos in positions]
        max_depth = max(depths)
        avg_depth = np.mean(depths)
        
        # Check line crossings
        crossed_bonus = any(self.crossed_bonus_line(pos) for pos in positions)
        crossed_baulk = any(self.crossed_baulk_line(pos) for pos in positions)
        
        # Determine deepest zone
        if crossed_baulk:
            deepest_zone = 'deep_zone'
        elif crossed_bonus:
            deepest_zone = 'mid_zone'
        else:
            deepest_zone = 'safe_zone'
        
        return {
            'max_depth': max_depth,
            'avg_depth': avg_depth,
            'crossed_bonus_line': crossed_bonus,
            'crossed_baulk_line': crossed_baulk,
            'deepest_zone': deepest_zone,
            'zones_visited': [],
            'lateral_movement': 0,
            'sectors_visited': []
        }
    
    @staticmethod
    def load_from_config(video_path):
        """Load court dynamics from saved config"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'play_area.json'
        )
        
        if not os.path.exists(config_file):
            raise ValueError("No play area configured. Run setup_play_area.py first.")
        
        with open(config_file, 'r') as f:
            all_configs = json.load(f)
        
        if video_path not in all_configs:
            raise ValueError(f"No play area configured for {video_path}")
        
        config = all_configs[video_path]
        
        return SimplifiedCourtDynamics(
            config['play_box'],
            config['midline'],
            config['baulk_line'],
            config['bonus_line']
        )
