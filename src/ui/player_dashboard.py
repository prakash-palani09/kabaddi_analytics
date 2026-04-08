"""
Player Dashboard UI
Shows detailed player profile with spider chart and statistics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import numpy as np

from theme import (
    apply_theme, flat_btn, card, divider,
    entry as make_entry, figure_bg,
    BG, CARD, BORDER, PRIMARY, SUCCESS, ACCENT, DANGER,
    TEXT, TEXT2, TEXT3, WHITE,
    F_H1, F_H2, F_H3, F_BODY, F_SMALL, F_LABEL, F_STAT,
    C_BLUE, C_GREEN, C_ORANGE, C_RED, C_GRID,
    PAD_SM, PAD_MD, PAD_LG, PAD_XL,
)

# ── Stat card accent colours (cycles through meaningful palette) ───────────
_STAT_COLORS = [PRIMARY, SUCCESS, ACCENT, C_RED, PRIMARY, SUCCESS, ACCENT, C_RED]


def radar_factory(num_vars, frame='circle'):
    """Create a radar chart projection with `num_vars` axes."""
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
            spine.set_transform(
                Affine2D().scale(.5).translate(.5, .5) + self.transAxes)
            return {'polar': spine}

    register_projection(RadarAxes)
    return theta


class PlayerDashboard:
    def __init__(self, parent, player_id, profile, stats, profile_manager):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Player Dashboard — {player_id}")
        self.window.geometry("1200x820")
        self.window.configure(bg=BG)

        self.player_id    = player_id
        self.profile      = profile
        self.stats        = stats
        self.profile_manager = profile_manager

        self.create_dashboard()

    # ──────────────────────────────────────────────────────────────────────
    #  MAIN LAYOUT
    # ──────────────────────────────────────────────────────────────────────

    def create_dashboard(self):
        # ── Top header bar ────────────────────────────────────────────────
        header = tk.Frame(self.window, bg=PRIMARY)
        header.pack(fill='x')

        hdr_inner = tk.Frame(header, bg=PRIMARY)
        hdr_inner.pack(fill='x', padx=PAD_XL, pady=PAD_MD)

        # Left: player identity
        id_col = tk.Frame(hdr_inner, bg=PRIMARY)
        id_col.pack(side='left', fill='y')

        tk.Label(id_col,
                 text=self.player_id,
                 font=('Segoe UI', 26, 'bold'), fg=WHITE, bg=PRIMARY).pack(anchor='w')
        tk.Label(id_col,
                 text=f"{self.profile.name}  ·  {self.profile.team}",
                 font=('Segoe UI', 13), fg='#bfdbfe', bg=PRIMARY).pack(anchor='w', pady=(2, 0))

        # Right: action button
        flat_btn(hdr_inner, "✎  Edit Profile",
                 command=self.edit_profile,
                 color=WHITE,
                 hover='#e2e8f0').pack(
            side='right',
            padx=(PAD_MD, 0))
        # Override fg for this button (white bg needs dark text)
        for widget in hdr_inner.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(fg=PRIMARY, activeforeground=PRIMARY)

        # Blue underline accent
        tk.Frame(header, bg=SUCCESS, height=3).pack(fill='x')

        # ── Body (two columns) ────────────────────────────────────────────
        body = tk.Frame(self.window, bg=BG)
        body.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD_LG)

        # Left column
        left = tk.Frame(body, bg=BG)
        left.pack(side='left', fill='both', expand=False,
                  padx=(0, PAD_MD))
        left.config(width=400)
        left.pack_propagate(False)

        # Right column
        right = tk.Frame(body, bg=BG)
        right.pack(side='left', fill='both', expand=True)

        self._build_left_panel(left)
        self._build_right_panel(right)

    # ──────────────────────────────────────────────────────────────────────
    #  LEFT PANEL  — Profile + Stats
    # ──────────────────────────────────────────────────────────────────────

    def _build_left_panel(self, parent):
        # ── Profile info card ──────────────────────────────────────────────
        info_card = card(parent, padx=PAD_LG, pady=PAD_MD)
        info_card.pack(fill='x', pady=(0, PAD_MD))

        _card_title(info_card, "Profile")

        grid = tk.Frame(info_card, bg=CARD)
        grid.pack(fill='x')
        grid.columnconfigure(1, weight=1)

        def _row(label, value, row_num):
            tk.Label(grid, text=label,
                     font=('Segoe UI', 11), fg=TEXT2, bg=CARD).grid(
                row=row_num, column=0, sticky='w', pady=6)
            tk.Label(grid, text=value,
                     font=('Segoe UI', 12, 'bold'), fg=TEXT, bg=CARD).grid(
                row=row_num, column=1, sticky='w', padx=(PAD_MD, 0), pady=6)

        _row("Player ID", self.player_id,   0)
        _row("Name",      self.profile.name, 1)
        _row("Team",      self.profile.team, 2)

        # ── KPI stat tiles ────────────────────────────────────────────────
        stats_card = card(parent, padx=PAD_MD, pady=PAD_MD)
        stats_card.pack(fill='both', expand=True)

        _card_title(stats_card, "Statistics")

        stats_data = [
            ("Total Raids",      self.stats.get('all_raids', 0)),
            ("Success Rate",     f"{self.stats.get('all_success_rate', 0):.1f}%"),
            ("Avg Penetration",  f"{self.stats.get('all_avg_penetration', 0):.2f} m"),
            ("Avg Duration",     f"{self.stats.get('all_avg_duration', 0):.1f} sec"),
            ("Total Points",     self.stats.get('total_points', 0)),
            ("Avg Points/Raid",  f"{self.stats.get('avg_points_per_raid', 0):.2f}"),
            ("Total Matches",    self.stats.get('total_matches', 0)),
            ("Rank Score",       f"{self.stats.get('score', 0):.3f}"),
        ]

        # 2-column tile grid
        tile_grid = tk.Frame(stats_card, bg=CARD)
        tile_grid.pack(fill='both', expand=True)
        tile_grid.columnconfigure(0, weight=1)
        tile_grid.columnconfigure(1, weight=1)

        for i, (label, value) in enumerate(stats_data):
            col_idx = i % 2
            row_idx = i // 2

            tile = tk.Frame(tile_grid, bg=BG,
                            highlightbackground=BORDER,
                            highlightthickness=1)
            tile.grid(row=row_idx, column=col_idx,
                      sticky='nsew', padx=3, pady=3)
            tile_grid.rowconfigure(row_idx, weight=1)

            color = _STAT_COLORS[i]
            tk.Frame(tile, bg=color, height=3).pack(fill='x')
            tk.Label(tile, text=str(value),
                     font=('Segoe UI', 16, 'bold'),
                     fg=color, bg=BG).pack(anchor='w',
                                           padx=PAD_SM, pady=(PAD_SM, 0))
            tk.Label(tile, text=label,
                     font=('Segoe UI', 11), fg=TEXT2, bg=BG).pack(
                anchor='w', padx=PAD_SM, pady=(0, PAD_SM))

    # ──────────────────────────────────────────────────────────────────────
    #  RIGHT PANEL  — Radar chart
    # ──────────────────────────────────────────────────────────────────────

    def _build_right_panel(self, parent):
        radar_card = card(parent, padx=0, pady=0)
        radar_card.pack(fill='both', expand=True)

        _card_title(radar_card, "Performance Radar", padx=PAD_MD)

        self.create_spider_chart(radar_card)

    # ──────────────────────────────────────────────────────────────────────
    #  SPIDER CHART  (logic unchanged, styling upgraded)
    # ──────────────────────────────────────────────────────────────────────

    def create_spider_chart(self, parent):
        """Create pentagon-shaped radar chart with quality-based metrics"""
        categories = ['Efficiency', 'Aggression', 'Impact', 'Control', 'Consistency']

        ELITE_PENETRATION    = 5.0
        ELITE_POINTS_PER_RAID = 3.0
        ELITE_RAIDS_PER_MATCH = 15

        efficiency = min(self.stats.get('all_success_rate', 0), 100)

        aggression = min(
            (self.stats.get('all_avg_penetration', 0) / ELITE_PENETRATION) * 100, 100)

        impact = min(
            (self.stats.get('avg_points_per_raid', 0) / ELITE_POINTS_PER_RAID) * 100, 100)

        success_rate = self.stats.get('all_success_rate', 0)
        avg_duration = self.stats.get('all_avg_duration', 0)
        if 5 <= avg_duration <= 20:
            duration_score = 100
        elif avg_duration < 5:
            duration_score = (avg_duration / 5) * 100
        else:
            duration_score = max(100 - ((avg_duration - 20) / 5) * 100, 0)
        control = min(max((success_rate / 100) * duration_score, 0), 100)

        total_raids   = self.stats.get('all_raids', 0)
        total_matches = self.stats.get('total_matches', 1)
        raids_per_match = total_raids / total_matches if total_matches > 0 else 0
        consistency = min((raids_per_match / ELITE_RAIDS_PER_MATCH) * 100, 100)

        values = [efficiency, aggression, impact, control, consistency]

        MAX_RADIUS = 100
        N = 5
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False) + np.pi / 2
        normalized = [v / 100 for v in values]

        # ── Figure ────────────────────────────────────────────────────────
        fig = plt.Figure(figsize=(7.0, 7.0), facecolor=CARD)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(CARD)

        # Grid rings
        grid_levels  = [0.2, 0.4, 0.6, 0.8, 1.0]
        grid_colours = ['#e2e8f0', '#e2e8f0', '#cbd5e1', '#cbd5e1', '#94a3b8']

        for level, gc in zip(grid_levels, grid_colours):
            r = level * MAX_RADIUS
            xs = [r * np.cos(a) for a in angles] + [r * np.cos(angles[0])]
            ys = [r * np.sin(a) for a in angles] + [r * np.sin(angles[0])]
            ax.plot(xs, ys, color=gc, linewidth=0.8, zorder=1)
            ax.text(1, r + 2, f'{int(level * 100)}',
                    ha='left', va='bottom', size=9,
                    color=TEXT3, zorder=2)

        # Spoke lines
        for angle in angles:
            ax.plot([0, MAX_RADIUS * np.cos(angle)],
                    [0, MAX_RADIUS * np.sin(angle)],
                    color=BORDER, linewidth=0.8, zorder=1)

        # Data polygon — primary colour fill
        x_data = [normalized[i] * MAX_RADIUS * np.cos(angles[i]) for i in range(N)] \
                 + [normalized[0] * MAX_RADIUS * np.cos(angles[0])]
        y_data = [normalized[i] * MAX_RADIUS * np.sin(angles[i]) for i in range(N)] \
                 + [normalized[0] * MAX_RADIUS * np.sin(angles[0])]

        ax.fill(x_data, y_data, alpha=0.20, color=PRIMARY, zorder=3)
        ax.plot(x_data, y_data,
                color=PRIMARY, linewidth=2.5, zorder=4)

        # Data point markers
        for i in range(N):
            px = normalized[i] * MAX_RADIUS * np.cos(angles[i])
            py = normalized[i] * MAX_RADIUS * np.sin(angles[i])
            ax.scatter(px, py,
                       s=60, color=PRIMARY,
                       zorder=5, edgecolors=WHITE, linewidths=1.5)

        # Category labels
        label_r = MAX_RADIUS * 1.22
        for i, (angle, cat) in enumerate(zip(angles, categories)):
            x = label_r * np.cos(angle)
            y = label_r * np.sin(angle)
            # Colour label by performance tier
            pct = values[i]
            if pct >= 70:
                lc = SUCCESS
            elif pct >= 40:
                lc = ACCENT
            else:
                lc = TEXT2
            ax.text(x, y, cat,
                    ha='center', va='center',
                    size=13, weight='bold', color=lc, zorder=6)

            # Small percentage underneath
            ax.text(x, y - MAX_RADIUS * 0.13,
                    f"{values[i]:.0f}%",
                    ha='center', va='center',
                    size=10.5, color=TEXT2, zorder=6)

        ax.set_xlim(-MAX_RADIUS * 1.4, MAX_RADIUS * 1.4)
        ax.set_ylim(-MAX_RADIUS * 1.4, MAX_RADIUS * 1.4)
        ax.set_aspect('equal')
        ax.axis('off')
        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True,
                                     padx=PAD_MD, pady=PAD_MD)

    # ──────────────────────────────────────────────────────────────────────
    #  EDIT PROFILE DIALOG
    # ──────────────────────────────────────────────────────────────────────

    def edit_profile(self):
        """Open dialog to edit player profile"""
        dlg = tk.Toplevel(self.window)
        dlg.title(f"Edit Profile — {self.player_id}")
        dlg.geometry("440x280")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)

        # Header strip
        hdr = tk.Frame(dlg, bg=PRIMARY)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Edit Player Profile",
                 font=F_H3, fg=WHITE, bg=PRIMARY).pack(
            padx=PAD_LG, pady=PAD_MD, anchor='w')
        tk.Frame(hdr, bg=SUCCESS, height=2).pack(fill='x')

        # Form card
        form = card(dlg, padx=PAD_XL, pady=PAD_LG)
        form.pack(fill='both', expand=True,
                  padx=PAD_LG, pady=PAD_LG)

        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Name",
                 font=F_LABEL, fg=TEXT2, bg=CARD).grid(
            row=0, column=0, sticky='w', pady=8)
        name_entry = make_entry(form, width=26)
        name_entry.insert(0, self.profile.name)
        name_entry.grid(row=0, column=1, sticky='ew', pady=8, padx=(PAD_MD, 0))

        tk.Label(form, text="Team",
                 font=F_LABEL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky='w', pady=8)
        team_entry = make_entry(form, width=26)
        team_entry.insert(0, self.profile.team)
        team_entry.grid(row=1, column=1, sticky='ew', pady=8, padx=(PAD_MD, 0))

        divider(form, bg=BORDER).grid(row=2, column=0, columnspan=2,
                                       sticky='ew', pady=(PAD_MD, 0))

        btn_row = tk.Frame(form, bg=CARD)
        btn_row.grid(row=3, column=0, columnspan=2,
                     sticky='e', pady=(PAD_MD, 0))

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
            dlg.destroy()
            self.window.destroy()

        flat_btn(btn_row, "Save Changes",
                 command=save_changes,
                 color=SUCCESS).pack(side='left', padx=(0, PAD_SM))
        flat_btn(btn_row, "Cancel",
                 command=dlg.destroy,
                 color='#64748b').pack(side='left')


# ── Shared card-title helper ───────────────────────────────────────────────

def _card_title(parent, text, padx=PAD_MD):
    row = tk.Frame(parent, bg=CARD)
    row.pack(fill='x', padx=padx, pady=(0, PAD_SM))
    tk.Frame(row, bg=PRIMARY, width=3, height=18).pack(
        side='left', padx=(0, PAD_SM))
    tk.Label(row, text=text, font=F_H3, fg=TEXT, bg=CARD).pack(side='left')
    divider(parent, bg=BORDER).pack(fill='x', pady=(0, PAD_MD))