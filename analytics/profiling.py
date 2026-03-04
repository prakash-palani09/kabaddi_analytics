def build_raider_profile(raids, all_raids=None):
    """Build profile from raids (for scoring) and all_raids (for display stats)"""
    total_raids = len(raids)
    
    successful_raids = sum(1 for r in raids if r["success"])
    total_penetration = sum(r["penetration"] for r in raids)
    total_duration = sum(r["duration"] for r in raids)
    total_points = sum(r.get("points", 0) for r in raids)
    
    profile = {
        "raids": total_raids,
        "success_rate": (successful_raids/total_raids * 100) if total_raids else 0,
        "avg_penetration": total_penetration/total_raids if total_raids else 0,
        "avg_duration": total_duration/total_raids if total_raids else 0,
        "avg_points": total_points/total_raids if total_raids else 0,
        "total_points": total_points
    }
    
    # Add all-time stats if provided
    if all_raids:
        all_total = len(all_raids)
        all_successful = sum(1 for r in all_raids if r["success"])
        all_points = sum(r.get("points", 0) for r in all_raids)
        all_penetration = sum(r["penetration"] for r in all_raids)
        all_duration = sum(r["duration"] for r in all_raids)
        
        profile.update({
            "all_raids": all_total,
            "all_success_rate": (all_successful/all_total * 100) if all_total else 0,
            "all_avg_penetration": all_penetration/all_total if all_total else 0,
            "all_avg_duration": all_duration/all_total if all_total else 0,
            "all_total_points": all_points,
            "all_avg_points": all_points/all_total if all_total else 0
        })
    
    return profile