"""
Player Dashboard UI
Shows detailed player profile with spider chart and statistics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import numpy as np


def radar_factory(num_vars, frame='circle'):
    """Create a radar chart with `num_vars` axes."""
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
    
    class RadarAxes(PolarAxes):
        name = 'radar'
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')
        
        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)
        
        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)
        
        def _close_line(self, line):
            x, y = line.get_data()
            if x[0] != x[-1]:
                x = np.concatenate((x, [x[0]]))
                y = np.concatenate((y, [y[0]]))
                line.set_data(x, y)
        
        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)
        
        def _gen_axes_patch(self):
            return Circle((0.5, 0.5), 0.5)
        
        def _gen_axes_spines(self):
            spine = Spine(axes=self, spine_type='circle',
                         path=Path.unit_circle())
            spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                              + self.transAxes)
            return {'polar': spine}
    
    register_projection(RadarAxes)
    return theta


class PlayerDashboard:
    def __init__(self, parent, player_id, profile, stats, profile_manager):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Player Dashboard - {player_id}")
        self.window.geometry("1000x700")
        self.window.configure(bg='#ecf0f1')
        
        self.player_id = player_id
        self.profile = profile
        self.stats = stats
        self.profile_manager = profile_manager
        
        self.create_dashboard()
    
    def create_dashboard(self):
        # Header
        header_frame = tk.Frame(self.window, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"Player ID: {self.player_id}", 
                font=("Arial", 18, "bold"), fg='white', bg='#2c3e50').pack(side='left', padx=20, pady=10)
        
        # Edit button
        tk.Button(header_frame, text="Edit Profile", command=self.edit_profile,
                 bg='#3498db', fg='white', font=("Arial", 10)).pack(side='right', padx=20)
        
        # Main content
        content_frame = tk.Frame(self.window, bg='#ecf0f1')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Profile info
        left_frame = tk.LabelFrame(content_frame, text="Profile Information", 
                                   font=("Arial", 12, "bold"), bg='#ecf0f1', padx=10, pady=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Profile details
        tk.Label(left_frame, text="Name:", font=("Arial", 11, "bold"), bg='#ecf0f1').grid(row=0, column=0, sticky='w', pady=5)
        tk.Label(left_frame, text=self.profile.name, font=("Arial", 11), bg='#ecf0f1').grid(row=0, column=1, sticky='w', padx=10)
        
        tk.Label(left_frame, text="Team:", font=("Arial", 11, "bold"), bg='#ecf0f1').grid(row=1, column=0, sticky='w', pady=5)
        tk.Label(left_frame, text=self.profile.team, font=("Arial", 11), bg='#ecf0f1').grid(row=1, column=1, sticky='w', padx=10)
        
        # Statistics
        stats_frame = tk.LabelFrame(left_frame, text="Statistics", font=("Arial", 11, "bold"), bg='#ecf0f1')
        stats_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        stats_data = [
            ("Total Raids", self.stats.get('all_raids', 0)),
            ("Success Rate", f"{self.stats.get('all_success_rate', 0):.1f}%"),
            ("Avg Penetration", f"{self.stats.get('all_avg_penetration', 0):.2f} m"),
            ("Avg Duration", f"{self.stats.get('all_avg_duration', 0):.1f} sec"),
            ("Total Points", self.stats.get('total_points', 0)),
            ("Avg Points/Raid", f"{self.stats.get('avg_points_per_raid', 0):.2f}"),
            ("Total Matches", self.stats.get('total_matches', 0)),
            ("Rank Score", f"{self.stats.get('score', 0):.3f}")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            tk.Label(stats_frame, text=f"{label}:", font=("Arial", 10), bg='#ecf0f1').grid(row=i, column=0, sticky='w', padx=5, pady=3)
            tk.Label(stats_frame, text=str(value), font=("Arial", 10, "bold"), bg='#ecf0f1').grid(row=i, column=1, sticky='e', padx=5, pady=3)
        
        # Right side - Spider chart
        right_frame = tk.LabelFrame(content_frame, text="Performance Radar", 
                                    font=("Arial", 12, "bold"), bg='#ecf0f1')
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.create_spider_chart(right_frame)
    
    def create_spider_chart(self, parent):
        """Create pentagon-shaped radar chart with quality-based metrics"""
        categories = ['Efficiency', 'Aggression', 'Impact', 'Control', 'Consistency']
        
        # Elite performance thresholds
        ELITE_PENETRATION = 5.0  # meters
        ELITE_POINTS_PER_RAID = 3.0
        ELITE_RAIDS_PER_MATCH = 15
        
        # 1. Efficiency → Success Rate (%)
        efficiency = min(self.stats.get('all_success_rate', 0), 100)
        
        # 2. Aggression → Avg Max Penetration
        aggression = min((self.stats.get('all_avg_penetration', 0) / ELITE_PENETRATION) * 100, 100)
        
        # 3. Impact → Avg Points per Raid
        impact = min((self.stats.get('avg_points_per_raid', 0) / ELITE_POINTS_PER_RAID) * 100, 100)
        
        # 4. Control → Successful raids in optimal duration (5-20 sec)
        success_rate = self.stats.get('all_success_rate', 0)
        avg_duration = self.stats.get('all_avg_duration', 0)
        
        if 5 <= avg_duration <= 20:
            duration_score = 100
        elif avg_duration < 5:
            duration_score = (avg_duration / 5) * 100
        else:
            duration_score = max(100 - ((avg_duration - 20) / 5) * 100, 0)
        
        control = (success_rate / 100) * duration_score
        control = min(max(control, 0), 100)
        
        # 5. Consistency → Raid Activity (raids per match)
        total_raids = self.stats.get('all_raids', 0)
        total_matches = self.stats.get('total_matches', 1)
        raids_per_match = total_raids / total_matches if total_matches > 0 else 0
        consistency = min((raids_per_match / ELITE_RAIDS_PER_MATCH) * 100, 100)
        
        values = [efficiency, aggression, impact, control, consistency]
        
        # Radar geometry constants
        MAX_RADIUS = 100
        N = 5
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False) + np.pi / 2
        
        # Normalize values to 0-1 range
        normalized_values = [v / 100 for v in values]
        
        # Create figure
        fig = plt.Figure(figsize=(6, 6), facecolor='#ecf0f1')
        ax = fig.add_subplot(111)
        
        # Draw uniform radial grid levels
        for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
            radius = level * MAX_RADIUS
            x_grid = [radius * np.cos(angle) for angle in angles] + [radius * np.cos(angles[0])]
            y_grid = [radius * np.sin(angle) for angle in angles] + [radius * np.sin(angles[0])]
            ax.plot(x_grid, y_grid, 'k--', linewidth=0.5, alpha=0.3)
            ax.text(0, radius, f'{int(level * 100)}%', ha='center', va='bottom', size=8, color='gray')
        
        # Draw axes from center to vertices
        for angle in angles:
            ax.plot([0, MAX_RADIUS * np.cos(angle)], [0, MAX_RADIUS * np.sin(angle)], 'k-', linewidth=0.5, alpha=0.3)
        
        # Plot data pentagon
        x_data = [normalized_values[i] * MAX_RADIUS * np.cos(angles[i]) for i in range(N)] + [normalized_values[0] * MAX_RADIUS * np.cos(angles[0])]
        y_data = [normalized_values[i] * MAX_RADIUS * np.sin(angles[i]) for i in range(N)] + [normalized_values[0] * MAX_RADIUS * np.sin(angles[0])]
        
        ax.plot(x_data, y_data, 'o-', linewidth=3, color='#e74c3c', markersize=10)
        ax.fill(x_data, y_data, alpha=0.35, color='#e74c3c')
        
        # Add category labels
        label_distance = MAX_RADIUS * 1.15
        for i, (angle, category) in enumerate(zip(angles, categories)):
            x = label_distance * np.cos(angle)
            y = label_distance * np.sin(angle)
            ax.text(x, y, category, ha='center', va='center', size=11, weight='bold')
        
        # Configure axes
        ax.set_xlim(-MAX_RADIUS * 1.3, MAX_RADIUS * 1.3)
        ax.set_ylim(-MAX_RADIUS * 1.3, MAX_RADIUS * 1.3)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
    
    def edit_profile(self):
        """Open dialog to edit player profile"""
        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Edit Profile - {self.player_id}")
        edit_window.geometry("400x200")
        edit_window.configure(bg='#ecf0f1')
        
        tk.Label(edit_window, text="Name:", font=("Arial", 11), bg='#ecf0f1').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_entry = tk.Entry(edit_window, font=("Arial", 11), width=25)
        name_entry.insert(0, self.profile.name)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(edit_window, text="Team:", font=("Arial", 11), bg='#ecf0f1').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        team_entry = tk.Entry(edit_window, font=("Arial", 11), width=25)
        team_entry.insert(0, self.profile.team)
        team_entry.grid(row=1, column=1, padx=10, pady=10)
        
        def save_changes():
            new_name = name_entry.get().strip()
            new_team = team_entry.get().strip()
            
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty")
                return
            
            self.profile.name = new_name
            self.profile.team = new_team
            self.profile_manager.save_profiles()
            
            messagebox.showinfo("Success", "Profile updated successfully")
            edit_window.destroy()
            self.window.destroy()
        
        tk.Button(edit_window, text="Save", command=save_changes, bg='#27ae60', fg='white', 
                 font=("Arial", 11), width=10).grid(row=2, column=0, padx=10, pady=20)
        tk.Button(edit_window, text="Cancel", command=edit_window.destroy, bg='#95a5a6', fg='white',
                 font=("Arial", 11), width=10).grid(row=2, column=1, padx=10, pady=20)
