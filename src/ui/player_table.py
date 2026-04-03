import tkinter as tk
from tkinter import ttk

from theme import (
    BG, CARD, BORDER, PRIMARY, SUCCESS, ACCENT, DANGER,
    TEXT, TEXT2, TEXT3, WHITE,
    F_H3, F_BODY, F_SMALL, F_LABEL,
    ROW_ODD, ROW_EVEN,
    PAD_SM, PAD_MD,
)

# ── Per-column display config ──────────────────────────────────────────────
_COL_CONFIG = {
    'Rank':            dict(width=52,  anchor='center'),
    'Player':          dict(width=130, anchor='w'),
    'Score':           dict(width=80,  anchor='center'),
    'Success Rate':    dict(width=100, anchor='center'),
    'Avg Penetration': dict(width=115, anchor='center'),
    'Avg Duration':    dict(width=100, anchor='center'),
    'Total Points':    dict(width=95,  anchor='center'),
    'Total Raids':     dict(width=85,  anchor='center'),
    'Avg Points':      dict(width=90,  anchor='center'),
    'Matches':         dict(width=72,  anchor='center'),
}

# Top-3 rank highlight colours
_RANK_COLORS = {
    1: ('#fef9c3', '#854d0e'),   # gold tint
    2: ('#f1f5f9', '#475569'),   # silver tint
    3: ('#fff7ed', '#9a3412'),   # bronze tint
}


class PlayerTable:
    """Reusable sortable player table component"""

    def __init__(self, parent, columns, profile_manager,
                 player_stats, data, final_ranking, open_dashboard_callback):
        self.parent               = parent
        self.columns              = columns
        self.profile_manager      = profile_manager
        self.player_stats         = player_stats
        self.data                 = data
        self.final_ranking        = final_ranking
        self.open_dashboard_callback = open_dashboard_callback

        self.sort_reverse = {col: False for col in columns}

        self._build_toolbar()
        self._build_table()

    # ──────────────────────────────────────────────────────────────────────
    #  CONSTRUCTION
    # ──────────────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        """Slim toolbar above the table: column hint + row count badge."""
        toolbar = tk.Frame(self.parent, bg=CARD, pady=PAD_SM)
        toolbar.pack(fill='x', padx=PAD_MD)

        tk.Label(toolbar,
                 text="Double-click a row to open the Player Dashboard",
                 font=F_SMALL, fg=TEXT3, bg=CARD).pack(side='left')

        self._row_count_lbl = tk.Label(
            toolbar, text="",
            font=('Segoe UI', 8, 'bold'),
            bg=PRIMARY, fg=WHITE,
            relief='flat', padx=6, pady=2)
        self._row_count_lbl.pack(side='right')

        # Thin divider below toolbar
        tk.Frame(self.parent, bg=BORDER, height=1).pack(fill='x')

    def _build_table(self):
        """Build the Treeview with scrollbar inside a clean container."""
        container = tk.Frame(self.parent, bg=CARD)
        container.pack(fill='both', expand=True)

        # Vertical scrollbar
        vsb = ttk.Scrollbar(container, orient='vertical')
        vsb.pack(side='right', fill='y')

        # Horizontal scrollbar (useful when many columns)
        hsb = ttk.Scrollbar(container, orient='horizontal')
        hsb.pack(side='bottom', fill='x')

        self.tree = ttk.Treeview(
            container,
            columns=self.columns,
            show='headings',
            height=20,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.tree.pack(fill='both', expand=True)

        # ── Column headers ────────────────────────────────────────────────
        for col in self.columns:
            cfg   = _COL_CONFIG.get(col, {})
            width = cfg.get('width', 90)
            anch  = cfg.get('anchor', 'center')

            self.tree.heading(col, text=col,
                              command=lambda c=col: self.sort_table(c))
            self.tree.column(col, width=width, anchor=anch,
                             stretch=True, minwidth=50)

        # ── Alternating row tags ──────────────────────────────────────────
        self.tree.tag_configure('odd',  background=ROW_ODD,  foreground=TEXT)
        self.tree.tag_configure('even', background=ROW_EVEN, foreground=TEXT)

        # Top-3 highlight tags
        self.tree.tag_configure('rank1',
                                background=_RANK_COLORS[1][0],
                                foreground=_RANK_COLORS[1][1],
                                font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('rank2',
                                background=_RANK_COLORS[2][0],
                                foreground=_RANK_COLORS[2][1],
                                font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('rank3',
                                background=_RANK_COLORS[3][0],
                                foreground=_RANK_COLORS[3][1],
                                font=('Segoe UI', 10, 'bold'))

        # Hover highlight
        self.tree.tag_configure('hover',
                                background='#eff6ff',
                                foreground=PRIMARY)

        self.tree.bind('<Double-Button-1>', self._on_double_click)
        self.tree.bind('<Motion>',          self._on_hover)
        self._hovered_item = None

    # ──────────────────────────────────────────────────────────────────────
    #  POPULATE  (logic unchanged)
    # ──────────────────────────────────────────────────────────────────────

    def populate(self, player_filter=None):
        """Populate table with player data."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        players_to_show = self.final_ranking
        if player_filter:
            players_to_show = [p for p in self.final_ranking
                               if player_filter(p['player_id'])]

        for row_idx, rank_data in enumerate(players_to_show):
            player_id = rank_data['player_id']
            profile   = self.player_stats[player_id]

            player_matches     = set(row['match_id'] for row in self.data
                                     if row['player_id'] == player_id)
            total_points       = sum(row.get('raid_points', 0) for row in self.data
                                     if row['player_id'] == player_id)
            total_raids        = profile.get('all_raids', profile['raids'])
            avg_points_per_raid = total_points / total_raids if total_raids > 0 else 0

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

            # Choose row tag
            rank = rank_data['rank']
            if rank == 1:
                tag = 'rank1'
            elif rank == 2:
                tag = 'rank2'
            elif rank == 3:
                tag = 'rank3'
            elif row_idx % 2 == 0:
                tag = 'even'
            else:
                tag = 'odd'

            self.tree.insert('', 'end', values=tuple(values), tags=(tag,))

        # Update row count badge
        count = len(players_to_show)
        self.tree.update_idletasks()
        self._row_count_lbl.config(
            text=f"  {count} player{'s' if count != 1 else ''}  ")

    # ──────────────────────────────────────────────────────────────────────
    #  SORT  (logic unchanged, heading indicator updated)
    # ──────────────────────────────────────────────────────────────────────

    def sort_table(self, col):
        """Sort table by column."""
        items   = [(self.tree.set(child, col), child)
                   for child in self.tree.get_children('')]
        reverse = self.sort_reverse[col]

        if col in ('Rank', 'Total Points', 'Total Raids', 'Matches'):
            items.sort(key=lambda x: int(x[0]),   reverse=reverse)
        elif col in ('Score', 'Success Rate', 'Avg Penetration',
                     'Avg Duration', 'Avg Points'):
            items.sort(key=lambda x: float(x[0]), reverse=reverse)
        else:
            items.sort(key=lambda x: x[0],        reverse=reverse)

        for index, (_, child) in enumerate(items):
            self.tree.move(child, '', index)

        self.sort_reverse[col] = not reverse

        # Refresh heading labels — active column gets coloured arrow
        direction = " ▼" if reverse else " ▲"
        for column in self.columns:
            if column == col:
                self.tree.heading(column,
                                  text=column + direction)
            else:
                self.tree.heading(column, text=column)

    # ──────────────────────────────────────────────────────────────────────
    #  INTERACTION  (logic unchanged)
    # ──────────────────────────────────────────────────────────────────────

    def _on_hover(self, event):
        """Highlight row under cursor."""
        item = self.tree.identify_row(event.y)
        if item == self._hovered_item:
            return

        # Restore previous hovered item
        if self._hovered_item:
            prev_tags = list(self.tree.item(self._hovered_item, 'tags'))
            if 'hover' in prev_tags:
                prev_tags.remove('hover')
                self.tree.item(self._hovered_item, tags=prev_tags)

        # Apply hover to new item (only on non-top3 rows)
        if item:
            current_tags = list(self.tree.item(item, 'tags'))
            if not any(t in current_tags for t in ('rank1', 'rank2', 'rank3')):
                self.tree.item(item, tags=current_tags + ['hover'])

        self._hovered_item = item

    def _on_double_click(self, event):
        """Handle double-click to open player dashboard."""
        selection = self.tree.selection()
        if not selection:
            return

        item      = self.tree.item(selection[0])
        player_id = item['values'][self.columns.index('Player')]

        profile = self.profile_manager.get_profile(player_id)
        stats   = self.player_stats.get(player_id, {})

        player_matches      = set(row['match_id'] for row in self.data
                                   if row['player_id'] == player_id)
        total_points        = sum(row.get('raid_points', 0) for row in self.data
                                   if row['player_id'] == player_id)
        total_raids         = stats.get('all_raids', stats.get('raids', 0))
        avg_points_per_raid = total_points / total_raids if total_raids > 0 else 0

        stats['total_points']       = total_points
        stats['avg_points_per_raid'] = avg_points_per_raid
        stats['total_matches']      = len(player_matches)

        for rank_data in self.final_ranking:
            if rank_data['player_id'] == player_id:
                stats['score'] = rank_data['score']
                break

        self.open_dashboard_callback(player_id, profile, stats)