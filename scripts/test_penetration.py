#!/usr/bin/env python3
"""
Test Penetration Calculation
Verify that the new penetration calculation gives accurate results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from court.simplified_court import SimplifiedCourtDynamics
import numpy as np

def test_penetration():
    """Test penetration calculation with known points"""
    
    # Example court setup (you'll need to use your actual video's config)
    video_path = "../data/videos/jan2.mp4"
    
    try:
        court = SimplifiedCourtDynamics.load_from_config(video_path)
        
        print("\n" + "="*70)
        print("PENETRATION CALCULATION TEST")
        print("="*70)
        
        # Test points along the depth axis
        mid_center = court.mid_center
        end_center = (court.end_line[0] + court.end_line[1]) / 2
        
        print(f"\nMidline center: {mid_center}")
        print(f"End line center: {end_center}")
        print(f"Total depth (pixels): {court.depth_magnitude:.1f}px")
        print(f"Conversion ratio: 1px = {court.END_DISTANCE/court.depth_magnitude:.4f}m")
        
        # Test points at known positions
        test_points = [
            ("Midline center", tuple(mid_center.astype(int)), 0.0),
            ("25% depth", tuple((mid_center + 0.25 * court.depth_vector).astype(int)), 1.625),
            ("50% depth", tuple((mid_center + 0.50 * court.depth_vector).astype(int)), 3.25),
            ("Baulk line (~58%)", tuple(((court.baulk_line[0] + court.baulk_line[1]) / 2).astype(int)), 3.75),
            ("Bonus line (~73%)", tuple(((court.bonus_line[0] + court.bonus_line[1]) / 2).astype(int)), 4.75),
            ("75% depth", tuple((mid_center + 0.75 * court.depth_vector).astype(int)), 4.875),
            ("End line (100%)", tuple(end_center.astype(int)), 6.5),
        ]
        
        print("\n" + "-"*70)
        print(f"{'Point':<20} {'Position':<20} {'Expected':<12} {'Calculated':<12} {'Error'}")
        print("-"*70)
        
        for name, point, expected in test_points:
            calculated = court.get_penetration_depth(point)
            error = abs(calculated - expected)
            error_pct = (error / expected * 100) if expected > 0 else 0
            
            print(f"{name:<20} {str(point):<20} {expected:>6.2f}m     {calculated:>6.2f}m     {error_pct:>5.1f}%")
        
        print("-"*70)
        
        # Test line crossing detection
        print("\n" + "="*70)
        print("LINE CROSSING TESTS")
        print("="*70)
        
        baulk_center = tuple(((court.baulk_line[0] + court.baulk_line[1]) / 2).astype(int))
        bonus_center = tuple(((court.bonus_line[0] + court.bonus_line[1]) / 2).astype(int))
        
        print(f"\nBaulk line center: {baulk_center}")
        print(f"  Crossed baulk? {court.crossed_baulk_line(baulk_center)} (should be True)")
        print(f"  Penetration: {court.get_penetration_depth(baulk_center):.2f}m (should be ~3.75m)")
        
        print(f"\nBonus line center: {bonus_center}")
        print(f"  Crossed bonus? {court.crossed_bonus_line(bonus_center)} (should be True)")
        print(f"  Penetration: {court.get_penetration_depth(bonus_center):.2f}m (should be ~4.75m)")
        
        print("\n" + "="*70)
        print("✅ Test complete! Check if calculated values match expected.")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Run court setup: python court/setup_play_area.py data/videos/jan2.mp4")
        print("2. Config file exists: config/play_area.json")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    
    test_penetration()
