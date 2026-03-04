import tkinter as tk
from tkinter import ttk

class PlayerTable:
    """Reusable sortable player table component"""
    
    def __init__(self, parent, columns, profile_manager, player_stats, data, final_ranking, open_dashboard_callback):
        """
        Initialize player table
        
        Args:
            parent: Parent widget
            columns: Tuple of column names
            profile_manager: PlayerProfileManager instance
            player_stats: Dictionary of player statistics
            data: List of all raid data
            final_ranking: List of ranked players
            open_dashboard_callback: Function to open player dashboard
        """
        self.parent = parent
        self.columns = columns
        self.profile_manager = profile_manager
        self.player_stats = player_stats
        self.data = data
        self.final_ranking = final_ranking
        self.open_dashboard_callback = open_dashboard_callback
        
        # Sort direction tracking
        self.sort_reverse = {col: False for col in columns}
        
        # Create table
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_table(c))
            if col in ['Success Rate', 'Avg Penetration', 'Avg Duration', 'Avg Points']:
                self.tree.column(col, width=100)
            else:
                self.tree.column(col, width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind double-click
        self.tree.bind('<Double-Button-1>', self._on_double_click)
    
    def populate(self, player_filter=None):
        """
        Populate table with player data
        
        Args:
            player_filter: Optional function to filter players (returns True to include)
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter players if needed
        players_to_show = self.final_ranking
        if player_filter:
            players_to_show = [p for p in self.final_ranking if player_filter(p['player_id'])]
        
        # Populate table
        for rank_data in players_to_show:
            player_id = rank_data['player_id']
            profile = self.player_stats[player_id]
            
            # Calculate stats
            player_matches = set(row['match_id'] for row in self.data if row['player_id'] == player_id)
            total_points = sum(row.get('raid_points', 0) for row in self.data if row['player_id'] == player_id)
            total_raids = profile.get('all_raids', profile['raids'])
            avg_points_per_raid = total_points / total_raids if total_raids > 0 else 0
            
            # Build row values based on columns
            values = []
            for col in self.columns:
                if col == 'Rank':
                    values.append(rank_data['rank'])
                elif col == 'Player':
                    values.append(player_id)
                elif col == 'Score':
                    values.append(f"{rank_data['score']:.3f}")
                elif col == 'Success Rate':
                    values.append(f"{profile.get('all_success_rate', profile['success_rate']):.2f}")
                elif col == 'Avg Penetration':
                    values.append(f"{profile.get('all_avg_penetration', profile['avg_penetration']):.2f}")
                elif col == 'Avg Duration':
                    values.append(f"{profile.get('all_avg_duration', profile['avg_duration']):.1f}")
                elif col == 'Total Points':
                    values.append(total_points)
                elif col == 'Total Raids':
                    values.append(total_raids)
                elif col == 'Avg Points':
                    values.append(f"{avg_points_per_raid:.2f}")
                elif col == 'Matches':
                    values.append(len(player_matches))
            
            self.tree.insert('', 'end', values=tuple(values))
    
    def sort_table(self, col):
        """Sort table by column"""
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        reverse = self.sort_reverse[col]
        
        # Determine sort type
        if col in ['Rank', 'Total Points', 'Total Raids', 'Matches']:
            items.sort(key=lambda x: int(x[0]), reverse=reverse)
        elif col in ['Score', 'Success Rate', 'Avg Penetration', 'Avg Duration', 'Avg Points']:
            items.sort(key=lambda x: float(x[0]), reverse=reverse)
        else:
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        # Rearrange items
        for index, (val, child) in enumerate(items):
            self.tree.move(child, '', index)
        
        # Toggle sort direction
        self.sort_reverse[col] = not reverse
        
        # Update column headers
        direction = " ▼" if reverse else " ▲"
        for column in self.columns:
            if column == col:
                self.tree.heading(column, text=column + direction)
            else:
                self.tree.heading(column, text=column)
    
    def _on_double_click(self, event):
        """Handle double-click to open player dashboard"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        player_id = item['values'][self.columns.index('Player')]
        
        # Get player stats
        profile = self.profile_manager.get_profile(player_id)
        stats = self.player_stats.get(player_id, {})
        
        # Add additional stats
        player_matches = set(row['match_id'] for row in self.data if row['player_id'] == player_id)
        total_points = sum(row.get('raid_points', 0) for row in self.data if row['player_id'] == player_id)
        total_raids = stats.get('all_raids', stats.get('raids', 0))
        avg_points_per_raid = total_points / total_raids if total_raids > 0 else 0
        
        stats['total_points'] = total_points
        stats['avg_points_per_raid'] = avg_points_per_raid
        stats['total_matches'] = len(player_matches)
        
        # Find player's rank score
        for rank_data in self.final_ranking:
            if rank_data['player_id'] == player_id:
                stats['score'] = rank_data['score']
                break
        
        # Call dashboard callback
        self.open_dashboard_callback(player_id, profile, stats)
