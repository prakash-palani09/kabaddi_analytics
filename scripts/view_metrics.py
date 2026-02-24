"""
Raid Metrics Visualizer
Display and analyze extracted raid metrics
"""

import pandas as pd
import sys

def display_raid_summary(csv_path):
    """Display summary of extracted raid metrics"""
    df = pd.read_csv(csv_path)
    
    print("\n" + "="*70)
    print("🏏 RAID METRICS SUMMARY")
    print("="*70)
    
    print(f"\n📊 Total Raids: {len(df)}")
    
    print("\n⏱️  DURATION STATS:")
    print(f"  Average: {df['duration'].mean():.2f}s")
    print(f"  Min: {df['duration'].min():.2f}s")
    print(f"  Max: {df['duration'].max():.2f}s")
    
    print("\n📏 PENETRATION STATS:")
    print(f"  Average Max Depth: {df['max_penetration'].mean():.1f}px")
    print(f"  Deepest Raid: {df['max_penetration'].max():.1f}px")
    print(f"  Bonus Line Crossed: {df['crossed_bonus'].sum()} raids ({df['crossed_bonus'].mean()*100:.1f}%)")
    print(f"  Baulk Line Crossed: {df['crossed_baulk'].sum()} raids ({df['crossed_baulk'].mean()*100:.1f}%)")
    
    print("\n🤼 ENGAGEMENT STATS:")
    print(f"  Average Defenders Engaged: {df['defenders_engaged'].mean():.1f}")
    print(f"  Max Defenders Engaged: {df['defenders_engaged'].max()}")
    
    print("\n🏃 MOVEMENT STATS:")
    print(f"  Average Speed: {df['avg_speed'].mean():.1f} px/s")
    print(f"  Average Direction Changes: {df['direction_changes'].mean():.1f}")
    
    print("\n" + "="*70)
    print("\n📋 INDIVIDUAL RAIDS:")
    print("-"*70)
    
    for idx, row in df.iterrows():
        print(f"\nRaid #{idx+1} (Raider {row['raider_id']}):")
        print(f"  Duration: {row['duration']:.2f}s | Penetration: {row['max_penetration']:.1f}px")
        print(f"  Zone: {row['deepest_zone']} | Defenders: {row['defenders_engaged']}")
        print(f"  Bonus: {'✓' if row['crossed_bonus'] else '✗'} | Baulk: {'✓' if row['crossed_baulk'] else '✗'}")
        print(f"  Speed: {row['avg_speed']:.1f} px/s | Agility: {row['direction_changes']} changes")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_metrics.py <csv_path>")
        sys.exit(1)
    
    display_raid_summary(sys.argv[1])
