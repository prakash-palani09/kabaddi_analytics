"""
Raid Metrics Extractor
Extracts penetration depth, duration, engagement, and other metrics from tracked raid data
"""

import numpy as np

class RaidMetricsExtractor:
    def __init__(self, court_dynamics, fps):
        self.court = court_dynamics
        self.fps = fps
    
    def extract_raid_metrics(self, raid_data):
        """
        Extract all metrics from a single raid
        
        Args:
            raid_data: {
                'raider_id': int,
                'start_frame': int,
                'end_frame': int,
                'positions': [(x, y, frame), ...],
                'defenders': {defender_id: [(x, y, frame), ...]},
                'keypoints': [keypoints_array, ...],  # Optional
                'returned_to_baseline': bool  # Success indicator
            }
        
        Returns:
            dict: Comprehensive raid metrics
        """
        positions = [(x, y) for x, y, _ in raid_data['positions']]
        
        # Basic metrics
        duration = self.raid_duration(raid_data['start_frame'], raid_data['end_frame'])
        max_depth = self.max_penetration_depth(positions)
        avg_depth = self.avg_penetration_depth(positions)
        
        # Success detection: raider returned to baseline (crossed midline again)
        success = raid_data.get('returned_to_baseline', False)
        
        # Court analysis
        path_analysis = self.court.analyze_raid_path(positions)
        
        # Defender engagement
        engagement = self.defender_engagement_count(raid_data['positions'], raid_data.get('defenders', {}))
        reaction_time = self.defender_reaction_time(raid_data['start_frame'], raid_data.get('defenders', {}))
        
        # Movement metrics
        speed = self.avg_speed(raid_data['positions'])
        agility = self.direction_changes(positions)
        
        return {
            'raider_id': raid_data['raider_id'],
            'duration': duration,
            'max_penetration': max_depth,  # In meters
            'avg_penetration': avg_depth,  # In meters
            'success': 1 if success else 0,  # 1 if returned to baseline, 0 otherwise
            'crossed_bonus': raid_data.get('crossed_bonus', False),
            'crossed_baulk': raid_data.get('crossed_baulk', False),
            'deepest_zone': path_analysis.get('deepest_zone', 'unknown'),
            'zones_visited': len(path_analysis.get('zones_visited', [])),
            'lateral_movement': path_analysis.get('lateral_movement', 0),
            'sectors_visited': len(path_analysis.get('sectors_visited', [])),
            'defenders_engaged': engagement,
            'reaction_time': reaction_time,
            'avg_speed': speed,
            'direction_changes': agility,
            'start_frame': raid_data['start_frame'],
            'end_frame': raid_data['end_frame']
        }
    
    def raid_duration(self, start_frame, end_frame):
        """Raid duration in seconds"""
        return (end_frame - start_frame) / self.fps
    
    def max_penetration_depth(self, positions):
        """Maximum penetration depth in METERS"""
        if not positions:
            return 0.0
        depths = [self.court.get_penetration_depth(pos) for pos in positions]
        return float(max(depths))
    
    def avg_penetration_depth(self, positions):
        """Average penetration depth"""
        if not positions:
            return 0
        depths = [self.court.get_penetration_depth(pos) for pos in positions]
        return np.mean(depths)
    
    def defender_engagement_count(self, raider_positions, defenders, threshold=80):
        """Count unique defenders engaged (within threshold distance)"""
        engaged = set()
        for def_id, def_positions in defenders.items():
            for rx, ry, rf in raider_positions:
                for dx, dy, df in def_positions:
                    if abs(rf - df) <= 2:  # Same time window
                        if np.hypot(rx - dx, ry - dy) < threshold:
                            engaged.add(def_id)
                            break
                if def_id in engaged:
                    break
        return len(engaged)
    
    def defender_reaction_time(self, raid_start, defenders):
        """Time until first defender engagement"""
        if not defenders:
            return None
        
        first_engage = float('inf')
        for def_positions in defenders.values():
            if def_positions:
                first_engage = min(first_engage, def_positions[0][2])
        
        if first_engage == float('inf'):
            return None
        
        return (first_engage - raid_start) / self.fps
    
    def avg_speed(self, positions):
        """Average movement speed in pixels/second"""
        if len(positions) < 2:
            return 0
        
        total_dist = 0
        for i in range(1, len(positions)):
            x1, y1, _ = positions[i-1]
            x2, y2, _ = positions[i]
            total_dist += np.hypot(x2 - x1, y2 - y1)
        
        duration = (positions[-1][2] - positions[0][2]) / self.fps
        return total_dist / duration if duration > 0 else 0
    
    def direction_changes(self, positions):
        """Count significant direction changes (agility indicator)"""
        if len(positions) < 3:
            return 0
        
        changes = 0
        threshold = 45  # degrees
        
        for i in range(1, len(positions) - 1):
            v1 = np.array(positions[i]) - np.array(positions[i-1])
            v2 = np.array(positions[i+1]) - np.array(positions[i])
            
            if np.linalg.norm(v1) > 5 and np.linalg.norm(v2) > 5:
                angle = np.arccos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1))
                if np.degrees(angle) > threshold:
                    changes += 1
        
        return changes
    
    def export_to_csv(self, raids_metrics, output_path):
        """Export raid metrics to CSV"""
        import csv
        
        if not raids_metrics:
            return
        
        fieldnames = raids_metrics[0].keys()
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(raids_metrics)
        
        print(f"✅ Exported {len(raids_metrics)} raids to {output_path}")
