#!/usr/bin/env python3
"""
Demo Data Extraction - Shows extracted raid metrics without requiring video processing
"""

import random
import csv
import os

def generate_demo_raid_data():
    """Generate realistic raid data for demonstration"""
    raids = []
    
    # Generate 50 sample raids with realistic metrics
    for i in range(50):
        # Realistic raid parameters
        duration = round(random.uniform(3.0, 12.0), 1)  # 3-12 seconds
        penetration = random.randint(80, 300)  # 80-300 pixels
        success = random.choice([0, 1])  # Binary success
        
        # Points based on success and penetration depth
        if success == 1:
            if penetration > 250:
                points = random.choices([3, 4, 5], weights=[50, 30, 20])[0]
            elif penetration > 180:
                points = random.choices([2, 3, 4], weights=[40, 40, 20])[0]
            else:
                points = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        else:
            points = 0
        
        raid = {
            'raid_id': f'R{i+1:03d}',
            'player_id': f'P{random.randint(1, 8)}',
            'duration_sec': duration,
            'penetration_px': penetration,
            'success': success,
            'raid_points': points,
            'total_distance': round(penetration * random.uniform(1.2, 2.5), 1),
            'avg_speed': round(random.uniform(15, 45), 1),
            'direction_changes': random.randint(0, 8)
        }
        
        raids.append(raid)
    
    return raids

def display_extracted_data(raids):
    """Display the extracted raid data in a formatted way"""
    print("=" * 80)
    print("🏏 KABADDI RAID DATA EXTRACTION RESULTS")
    print("=" * 80)
    print()
    
    # Summary statistics
    total_raids = len(raids)
    successful_raids = sum(1 for r in raids if r['success'] == 1)
    success_rate = (successful_raids / total_raids) * 100
    
    print(f"📊 EXTRACTION SUMMARY:")
    print(f"   Total Raids Extracted: {total_raids}")
    print(f"   Successful Raids: {successful_raids}")
    print(f"   Overall Success Rate: {success_rate:.1f}%")
    print()
    
    # Sample data display
    print(f"📋 SAMPLE EXTRACTED RAID DATA:")
    print("-" * 80)
    print(f"{'ID':<6} {'Player':<8} {'Duration':<10} {'Penetration':<12} {'Success':<8} {'Points':<8}")
    print("-" * 80)
    
    # Show first 15 raids
    for raid in raids[:15]:
        print(f"{raid['raid_id']:<6} {raid['player_id']:<8} {raid['duration_sec']:<10} "
              f"{raid['penetration_px']:<12} {raid['success']:<8} {raid['raid_points']:<8}")
    
    if len(raids) > 15:
        print(f"... and {len(raids) - 15} more raids")
    
    print("-" * 80)
    print()
    
    # Player-wise breakdown
    player_stats = {}
    for raid in raids:
        pid = raid['player_id']
        if pid not in player_stats:
            player_stats[pid] = {'raids': 0, 'successful': 0, 'total_points': 0, 'total_penetration': 0}
        
        player_stats[pid]['raids'] += 1
        player_stats[pid]['successful'] += raid['success']
        player_stats[pid]['total_points'] += raid['raid_points']
        player_stats[pid]['total_penetration'] += raid['penetration_px']
    
    print(f"👥 PLAYER PERFORMANCE BREAKDOWN:")
    print("-" * 70)
    print(f"{'Player':<8} {'Raids':<8} {'Success%':<10} {'Avg Pen.':<10} {'Total Pts':<10}")
    print("-" * 70)
    
    for player_id, stats in sorted(player_stats.items()):
        success_pct = (stats['successful'] / stats['raids']) * 100
        avg_penetration = stats['total_penetration'] / stats['raids']
        print(f"{player_id:<8} {stats['raids']:<8} {success_pct:<10.1f} "
              f"{avg_penetration:<10.0f} {stats['total_points']:<10}")
    
    print("-" * 70)
    print()
    
    # Metrics ranges
    durations = [r['duration_sec'] for r in raids]
    penetrations = [r['penetration_px'] for r in raids]
    points = [r['raid_points'] for r in raids if r['success'] == 1]
    
    print(f"📈 EXTRACTED METRICS RANGES:")
    print(f"   Duration: {min(durations):.1f}s - {max(durations):.1f}s (avg: {sum(durations)/len(durations):.1f}s)")
    print(f"   Penetration: {min(penetrations)}px - {max(penetrations)}px (avg: {sum(penetrations)/len(penetrations):.0f}px)")
    if points:
        print(f"   Points (successful raids): {min(points)} - {max(points)} (avg: {sum(points)/len(points):.1f})")
    print()
    
    return raids

def save_extracted_data(raids, filename="demo_extracted_data.csv"):
    """Save extracted data to CSV file"""
    fieldnames = ['raid_id', 'player_id', 'duration_sec', 'penetration_px', 'success', 
                 'raid_points', 'total_distance', 'avg_speed', 'direction_changes']
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raids)
    
    print(f"💾 DATA SAVED TO: {filename}")
    print(f"📁 Ready for analysis and player ranking!")
    print("=" * 80)

def main():
    print("🚀 Starting Demo Data Extraction...")
    print("⚡ Simulating video processing and raid detection...")
    print()
    
    # Generate demo data
    raids = generate_demo_raid_data()
    
    # Display results
    extracted_raids = display_extracted_data(raids)
    
    # Save to file
    save_extracted_data(extracted_raids)
    
    print()
    print("✅ Demo Data Extraction Completed!")
    print("This demonstrates the type of data extracted from kabaddi videos:")
    print("• Raid duration (seconds)")
    print("• Penetration depth (pixels)")
    print("• Success/failure (1/0)")
    print("• Points earned")
    print("• Additional movement metrics")

if __name__ == "__main__":
    main()