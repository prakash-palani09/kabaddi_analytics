"""
Half Kabaddi Court Dynamics
Defines court zones, boundaries, and spatial regions from midline
"""

import numpy as np
import json
import os

class HalfCourtDynamics:
    """
    Half Kabaddi Court Layout (from midline):
    
    |---------------|  Boundary Line (back)
    |               |
    |   Deep Zone   |  (High risk, high reward)
    |               |
    |---------------|  Baulk Line
    |               |
    | Mid Zone      |  (Moderate penetration)
    |               |
    |---------------|  Bonus Line
    |               |
    | Safe Zone     |  (Low penetration)
    |               |
    |===============|  MIDLINE (starting point)
    """
    
    def __init__(self, midline_p1, midline_p2):
        """
        Initialize court dynamics from midline
        
        Args:
            midline_p1: (x, y) first point of midline
            midline_p2: (x, y) second point of midline
        """
        self.midline_p1 = np.array(midline_p1)
        self.midline_p2 = np.array(midline_p2)
        
        # Calculate midline properties
        self.midline_vector = self.midline_p2 - self.midline_p1
        self.midline_length = np.linalg.norm(self.midline_vector)
        self.midline_normal = self.get_perpendicular_vector()
        
        # Define zone distances from midline (in pixels)
        # These will be calibrated based on actual court dimensions
        self.zones = {
            'safe_zone': (0, 80),      # 0-80px from midline
            'bonus_line': 80,           # Bonus line at 80px
            'mid_zone': (80, 160),      # 80-160px from midline
            'baulk_line': 160,          # Baulk line at 160px
            'deep_zone': (160, 240),    # 160-240px from midline
            'boundary': 240             # Back boundary at 240px
        }
        
        # Risk levels for each zone
        self.risk_levels = {
            'safe_zone': 1,
            'mid_zone': 2,
            'deep_zone': 3
        }
    
    def get_perpendicular_vector(self):
        """Get unit vector perpendicular to midline"""
        # Perpendicular vector (rotate 90 degrees)
        perp = np.array([-self.midline_vector[1], self.midline_vector[0]])
        return perp / np.linalg.norm(perp)
    
    def get_penetration_depth(self, point):
        """
        Calculate penetration depth from midline
        
        Args:
            point: (x, y) position
            
        Returns:
            float: Distance from midline (positive = penetrated)
        """
        point = np.array(point)
        # Project point onto perpendicular direction
        midline_center = (self.midline_p1 + self.midline_p2) / 2
        relative_pos = point - midline_center
        depth = np.dot(relative_pos, self.midline_normal)
        return abs(depth)
    
    def get_zone(self, point):
        """
        Determine which court zone a point is in
        
        Args:
            point: (x, y) position
            
        Returns:
            str: Zone name ('safe_zone', 'mid_zone', 'deep_zone', 'out_of_bounds')
        """
        depth = self.get_penetration_depth(point)
        
        if depth < self.zones['safe_zone'][1]:
            return 'safe_zone'
        elif depth < self.zones['mid_zone'][1]:
            return 'mid_zone'
        elif depth < self.zones['deep_zone'][1]:
            return 'deep_zone'
        else:
            return 'out_of_bounds'
    
    def get_risk_level(self, point):
        """
        Get risk level at a position (1=low, 2=medium, 3=high)
        
        Args:
            point: (x, y) position
            
        Returns:
            int: Risk level (1-3)
        """
        zone = self.get_zone(point)
        return self.risk_levels.get(zone, 0)
    
    def crossed_bonus_line(self, point):
        """Check if point crossed bonus line"""
        depth = self.get_penetration_depth(point)
        return depth >= self.zones['bonus_line']
    
    def crossed_baulk_line(self, point):
        """Check if point crossed baulk line"""
        depth = self.get_penetration_depth(point)
        return depth >= self.zones['baulk_line']
    
    def is_out_of_bounds(self, point):
        """Check if point is beyond court boundary"""
        depth = self.get_penetration_depth(point)
        return depth >= self.zones['boundary']
    
    def get_lateral_position(self, point):
        """
        Get lateral position along midline (left to right)
        
        Args:
            point: (x, y) position
            
        Returns:
            float: Position along midline (0=left, 1=right)
        """
        point = np.array(point)
        # Project onto midline direction
        relative_pos = point - self.midline_p1
        projection = np.dot(relative_pos, self.midline_vector / self.midline_length)
        return np.clip(projection / self.midline_length, 0, 1)
    
    def get_court_sector(self, point):
        """
        Divide court into sectors (left, center, right)
        
        Args:
            point: (x, y) position
            
        Returns:
            str: Sector name
        """
        lateral = self.get_lateral_position(point)
        
        if lateral < 0.33:
            return 'left'
        elif lateral < 0.67:
            return 'center'
        else:
            return 'right'
    
    def analyze_raid_path(self, positions):
        """
        Analyze a raid path through the court
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            dict: Raid path analysis
        """
        if not positions:
            return {}
        
        depths = [self.get_penetration_depth(pos) for pos in positions]
        zones = [self.get_zone(pos) for pos in positions]
        sectors = [self.get_court_sector(pos) for pos in positions]
        
        return {
            'max_depth': max(depths),
            'avg_depth': np.mean(depths),
            'deepest_zone': zones[np.argmax(depths)],
            'zones_visited': list(set(zones)),
            'crossed_bonus_line': any(self.crossed_bonus_line(pos) for pos in positions),
            'crossed_baulk_line': any(self.crossed_baulk_line(pos) for pos in positions),
            'sectors_visited': list(set(sectors)),
            'lateral_movement': max(self.get_lateral_position(pos) for pos in positions) - 
                               min(self.get_lateral_position(pos) for pos in positions)
        }
    
    def save_config(self, video_path):
        """Save court dynamics configuration"""
        config = {
            'midline_p1': self.midline_p1.tolist(),
            'midline_p2': self.midline_p2.tolist(),
            'zones': self.zones,
            'risk_levels': self.risk_levels
        }
        
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, 'court_dynamics.json')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Court dynamics saved to {config_file}")
    
    @staticmethod
    def load_from_midline(video_path):
        """Load court dynamics from saved midline"""
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from court.midline_manager import load_midline, has_midline
        
        if not has_midline(video_path):
            raise ValueError("No midline configured for this video")
        
        midline_data = load_midline(video_path)
        return HalfCourtDynamics(midline_data['p1'], midline_data['p2'])


def visualize_court_zones(court_dynamics, frame_shape):
    """
    Create visualization overlay for court zones
    
    Args:
        court_dynamics: HalfCourtDynamics instance
        frame_shape: (height, width) of video frame
        
    Returns:
        numpy array: Overlay image with zones
    """
    import cv2
    
    overlay = np.zeros((frame_shape[0], frame_shape[1], 3), dtype=np.uint8)
    
    # Draw midline
    cv2.line(overlay, tuple(court_dynamics.midline_p1.astype(int)), 
             tuple(court_dynamics.midline_p2.astype(int)), (0, 255, 255), 3)
    
    # Draw zone boundaries (parallel lines to midline)
    for zone_name, distance in [('bonus_line', 80), ('baulk_line', 160), ('boundary', 240)]:
        # Calculate parallel line at distance
        offset = court_dynamics.midline_normal * distance
        p1_offset = court_dynamics.midline_p1 + offset
        p2_offset = court_dynamics.midline_p2 + offset
        
        color = (0, 255, 0) if zone_name == 'bonus_line' else (255, 165, 0) if zone_name == 'baulk_line' else (0, 0, 255)
        cv2.line(overlay, tuple(p1_offset.astype(int)), tuple(p2_offset.astype(int)), color, 2)
        
        # Add label
        label_pos = ((p1_offset + p2_offset) / 2).astype(int)
        cv2.putText(overlay, zone_name.upper(), tuple(label_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return overlay


if __name__ == "__main__":
    # Test with sample midline
    midline_p1 = (100, 500)
    midline_p2 = (900, 500)
    
    court = HalfCourtDynamics(midline_p1, midline_p2)
    
    # Test points
    test_points = [
        (500, 450),  # Safe zone
        (500, 400),  # Mid zone
        (500, 350),  # Deep zone
    ]
    
    print("🏏 Half Court Dynamics Test")
    print("=" * 50)
    for point in test_points:
        depth = court.get_penetration_depth(point)
        zone = court.get_zone(point)
        risk = court.get_risk_level(point)
        sector = court.get_court_sector(point)
        
        print(f"Point {point}:")
        print(f"  Depth: {depth:.1f}px")
        print(f"  Zone: {zone}")
        print(f"  Risk: {risk}/3")
        print(f"  Sector: {sector}")
        print()
