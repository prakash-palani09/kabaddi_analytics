import numpy as np

def raid_duration(start_frame, end_frame, fps):
    return (end_frame - start_frame) / fps


def penetration_depth(positions, midline_x):
    """
    positions: list of (x, y) positions of raider during raid
    midline_x: x coordinate of midline
    """
    distances = [abs(x - midline_x) for x, y in positions]
    return max(distances) if distances else 0


def defender_engagement(defender_positions, raider_positions, threshold=50):
    """
    Counts how many unique defenders came close to raider
    """
    engaged = set()
    for d_id, d_positions in defender_positions.items():
        for (dx, dy), (rx, ry) in zip(d_positions, raider_positions):
            if np.hypot(dx - rx, dy - ry) < threshold:
                engaged.add(d_id)
                break
    return len(engaged)


def reaction_time(raid_start_frame, first_engage_frame, fps):
    return (first_engage_frame - raid_start_frame) / fps

def success_rate(successful,total):
    if total ==0:
        return 0
    return successful / total

def normalize(value,min_val,max_val):
    if max_val - min_val ==0:
        return 0
    return (value-min_val)/(max_val-min_val)