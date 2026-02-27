"""
Player Profile Management System
Stores and manages individual player profiles with detailed statistics
"""

import json
import os

class PlayerProfile:
    def __init__(self, player_id, name="", team=""):
        self.player_id = player_id
        self.name = name or f"Player {player_id}"
        self.team = team or "Unknown Team"
        self.stats = {}
    
    def update_stats(self, stats):
        """Update player statistics"""
        self.stats = stats
    
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'player_id': self.player_id,
            'name': self.name,
            'team': self.team,
            'stats': self.stats
        }
    
    @staticmethod
    def from_dict(data):
        """Create profile from dictionary"""
        profile = PlayerProfile(data['player_id'], data.get('name', ''), data.get('team', ''))
        profile.stats = data.get('stats', {})
        return profile


class PlayerProfileManager:
    def __init__(self, profiles_file='data/player_profiles.json'):
        self.profiles_file = profiles_file
        self.profiles = {}
        self.load_profiles()
    
    def load_profiles(self):
        """Load profiles from JSON file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    for player_id, profile_data in data.items():
                        self.profiles[player_id] = PlayerProfile.from_dict(profile_data)
            except Exception as e:
                print(f"Error loading profiles: {e}")
                self.profiles = {}
    
    def save_profiles(self):
        """Save profiles to JSON file"""
        os.makedirs(os.path.dirname(self.profiles_file), exist_ok=True)
        data = {pid: profile.to_dict() for pid, profile in self.profiles.items()}
        with open(self.profiles_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_profile(self, player_id):
        """Get or create player profile"""
        if player_id not in self.profiles:
            self.profiles[player_id] = PlayerProfile(player_id)
        return self.profiles[player_id]
    
    def update_profile(self, player_id, name=None, team=None, stats=None):
        """Update player profile"""
        profile = self.get_profile(player_id)
        if name:
            profile.name = name
        if team:
            profile.team = team
        if stats:
            profile.update_stats(stats)
        self.save_profiles()
    
    def delete_profile(self, player_id):
        """Delete player profile"""
        if player_id in self.profiles:
            del self.profiles[player_id]
            self.save_profiles()
