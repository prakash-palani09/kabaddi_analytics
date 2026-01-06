from analytics.profiling import build_raider_profile
from analytics.ranking import rank_players

dummy_raids = [
    {"duration": 6, "penetration": 40, "success": True},
    {"duration": 8, "penetration": 30, "success": False},
    {"duration": 5, "penetration": 50, "success": True},
]

player_profiles = {
    "Raider_1": build_raider_profile(dummy_raids),
    "Raider_2": build_raider_profile(dummy_raids[:-1])
}

ranked = rank_players(player_profiles)
print(ranked)
