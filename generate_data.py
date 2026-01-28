import csv
import random

def generate_realistic_data():
    """Generate realistic kabaddi synthetic data"""
    
    data = []
    
    # 25 players
    players = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10',
              'R11', 'R12', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20',
              'R21', 'R22', 'R23', 'R24', 'R25']
    
    # 20 matches (to make last 15 matches meaningful)
    matches = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10',
              'M11', 'M12', 'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20']
    
    print("Generating realistic kabaddi data...")
    print(f"Players: {len(players)}")
    print(f"Matches: {len(matches)}")
    
    for player in players:
        # Each player participates in 10-18 matches
        num_matches = random.randint(10, 18)
        player_matches = random.sample(matches, num_matches)
        
        # Each player has 30-200 total raids
        total_raids = random.randint(30, 200)
        
        # Distribute raids across matches
        raids_per_match = []
        remaining_raids = total_raids
        
        for i in range(len(player_matches)):
            if i == len(player_matches) - 1:
                # Last match gets remaining raids
                raids_per_match.append(remaining_raids)
            else:
                # Random distribution
                max_raids = min(remaining_raids - (len(player_matches) - i - 1), remaining_raids // 2)
                raids = random.randint(1, max(1, max_raids))
                raids_per_match.append(raids)
                remaining_raids -= raids
        
        # Generate raids for each match
        for match, num_raids in zip(player_matches, raids_per_match):
            for _ in range(num_raids):
                # Realistic parameters
                duration = round(random.uniform(2.0, 8.0), 1)  # 2-8 seconds
                penetration = random.randint(100, 250)  # 100-250 pixels
                
                # Success rate varies by player skill (some players are better)
                player_skill = hash(player) % 100  # Consistent skill per player
                if player_skill > 70:  # Top players
                    success_prob = 0.7
                elif player_skill > 40:  # Average players
                    success_prob = 0.5
                else:  # Weaker players
                    success_prob = 0.3
                
                success = 1 if random.random() < success_prob else 0
                
                # Raid points system (realistic distribution)
                if success == 0:
                    raid_points = 0
                else:
                    # Realistic point distribution
                    point_rand = random.random()
                    if point_rand < 0.70:  # 70% get 1 point
                        raid_points = 1
                    elif point_rand < 0.85:  # 15% get 2 points
                        raid_points = 2
                    elif point_rand < 0.95:  # 10% get 3 points
                        raid_points = 3
                    elif point_rand < 0.98:  # 3% get 4 points
                        raid_points = 4
                    elif point_rand < 0.995:  # 1.5% get 5 points
                        raid_points = 5
                    elif point_rand < 0.999:  # 0.4% get 6 points
                        raid_points = 6
                    else:  # 0.1% get 7 points (super rare)
                        raid_points = 7
                
                data.append({
                    'match_id': match,
                    'player_id': player,
                    'raid_duration_sec': duration,
                    'penetration_px': penetration,
                    'success': success,
                    'raid_points': raid_points
                })
        
        print(f"Generated {total_raids} raids for {player} across {num_matches} matches")
    
    # Save to CSV
    with open('synthetic_data.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['match_id', 'player_id', 'raid_duration_sec', 'penetration_px', 'success', 'raid_points'])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n✅ Generated {len(data)} total raid records")
    print("✅ Data saved to synthetic_data.csv")
    
    # Statistics
    player_stats = {}
    for row in data:
        player_id = row['player_id']
        if player_id not in player_stats:
            player_stats[player_id] = {'raids': 0, 'matches': set(), 'successes': 0, 'total_points': 0}
        
        player_stats[player_id]['raids'] += 1
        player_stats[player_id]['matches'].add(row['match_id'])
        player_stats[player_id]['successes'] += row['success']
        player_stats[player_id]['total_points'] += row['raid_points']
    
    print("\n📊 Data Summary:")
    print(f"Total Players: {len(player_stats)}")
    print(f"Total Matches: {len(matches)}")
    print(f"Total Raids: {len(data)}")
    
    raid_counts = [stats['raids'] for stats in player_stats.values()]
    print(f"Raids per player: {min(raid_counts)} - {max(raid_counts)}")
    
    success_rates = [stats['successes']/stats['raids'] for stats in player_stats.values()]
    print(f"Success rates: {min(success_rates):.2f} - {max(success_rates):.2f}")
    
    avg_points = [stats['total_points']/stats['raids'] for stats in player_stats.values()]
    print(f"Average points per raid: {min(avg_points):.2f} - {max(avg_points):.2f}")

if __name__ == "__main__":
    generate_realistic_data()