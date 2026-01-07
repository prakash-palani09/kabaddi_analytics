from analytics.profiling import build_raider_profile
from analytics.ranking import rank_players
from analytics.ranking import rank_players, assign_ranks


raider_A = [
    {"duration": 6, "penetration": 45, "success": True},
    {"duration": 7, "penetration": 40, "success": True},
    {"duration": 8, "penetration": 30, "success": False},
]

raider_B = [
    {"duration": 5, "penetration": 25, "success": True},
    {"duration": 6, "penetration": 20, "success": True},
]

profiles = {
    "Raider_A": build_raider_profile(raider_A),
    "Raider_B": build_raider_profile(raider_B),
}

ranking = rank_players(profiles)

print("Profiles:", profiles)
print("Ranking:", ranking)

#ranking of the players


final_ranking = assign_ranks(ranking)

for r in final_ranking:
    print(r)