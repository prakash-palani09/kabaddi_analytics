import sys
import os
# Go up two levels: src/ui -> src -> root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import subprocess
import os
import threading
import shutil
import csv
from PIL import Image, ImageTk
from analytics.profiling import build_raider_profile
from analytics.ranking import rank_players, assign_ranks
from analytics.player_profile import PlayerProfileManager
from player_dashboard import PlayerDashboard
from keyframe_viewer import open_keyframe_viewer
from player_table import PlayerTable

from theme import (
    apply_theme, page_header, card, flat_btn,
    entry as make_entry,
    section_header, divider,
    apply_chart_style, figure_bg,
    BG, CARD, BORDER, PRIMARY, SUCCESS, ACCENT, DANGER,
    TEXT, TEXT2, TEXT3, WHITE,
    F_H2, F_H3, F_BODY, F_SMALL, F_LABEL, F_MONO,
    C_BLUE, C_GREEN, C_ORANGE, C_RED,
    PAD_SM, PAD_MD, PAD_LG, PAD_XL,
)


class KabaddiAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kabaddi Analytics System")
        self.root.geometry("1400x900")

        # Apply the unified design system
        apply_theme(root)

        # Initialize player profile manager
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        profiles_file = os.path.join(root_dir, 'data', 'player_profiles.json')
        self.profile_manager = PlayerProfileManager(profiles_file)

        # Load synthetic data
        self.load_data()

        # Create main interface
        self.create_main_interface()

    # ──────────────────────────────────────────────────────────────────────
    #  DATA LAYER  (backend — unchanged)
    # ──────────────────────────────────────────────────────────────────────

    def load_data(self):
        """Load extracted raid data and calculate rankings"""
        self.data = []
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        csv_path = os.path.join(root_dir, "data", "synthetic", "synthetic_data.csv")
        print(f"\n{'='*70}")
        print(f"LOADING DATA FROM: {csv_path}")
        print(f"File exists: {os.path.exists(csv_path)}")
        print(f"{'='*70}\n")

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        self.data.append({
                            'match_id': row['match_id'],
                            'player_id': row['player_id'],
                            'raid_duration_sec': float(row['raid_duration_sec']),
                            'penetration_px': float(row['penetration_px']),
                            'success': int(row['success']),
                            'raid_points': int(row.get('raid_points', 0) or 0)
                        })
                    except (ValueError, KeyError):
                        continue

            print(f"✓ Loaded {len(self.data)} raids")
            print(f"✓ Unique players: {len(set(row['player_id'] for row in self.data))}")
            self.update_rankings()

        except FileNotFoundError:
            print("ERROR: synthetic_data.csv not found!")
            self.create_sample_data()

    def create_sample_data(self):
        """Create realistic synthetic data: 28 players (7 per team, 4 teams), each played 3+ matches"""
        import random
        self.data = []
        teams = ['TeamA', 'TeamB', 'TeamC', 'TeamD']
        players = [f"{team}_P{i}" for team in teams for i in range(1, 8)]
        matches = [f'M{i}' for i in range(1, 13)]
        team_matches = {team: matches[i*3:(i+1)*3] for i, team in enumerate(teams)}

        for player in players:
            team = player.split('_')[0]
            for match in team_matches[team]:
                for _ in range(random.randint(8, 20)):
                    duration    = round(random.uniform(2.5, 7.5), 1)
                    penetration = round(random.uniform(1.0, 5.0), 2)
                    success     = random.choices([0, 1], weights=[40, 60])[0]
                    raid_points = random.choices([1, 2, 3], weights=[60, 30, 10])[0] if success else 0
                    self.data.append({
                        'match_id': match, 'player_id': player,
                        'raid_duration_sec': duration,
                        'penetration_px': penetration,
                        'success': success, 'raid_points': raid_points
                    })

        self.save_data()
        self.update_rankings()

    def save_data(self):
        """Save data to CSV"""
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "synthetic", "synthetic_data.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'match_id', 'player_id', 'raid_duration_sec',
                'penetration_px', 'success', 'raid_points'])
            writer.writeheader()
            writer.writerows(self.data)

    def update_rankings(self):
        """Calculate player rankings from data"""
        self.player_stats = {}
        player_data = {}
        for row in self.data:
            player_data.setdefault(row['player_id'], []).append(row)

        for player_id, raids_data in player_data.items():
            matches = {}
            for row in raids_data:
                matches.setdefault(row['match_id'], []).append(row)

            sorted_matches = sorted(
                matches.keys(),
                key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
            recent_matches = sorted_matches[-15:]

            all_raids = [{'duration': r['raid_duration_sec'],
                          'penetration': r['penetration_px'],
                          'success': bool(r['success']),
                          'points': r.get('raid_points', 0)} for r in raids_data]

            recent_raids = [{'duration': r['raid_duration_sec'],
                             'penetration': r['penetration_px'],
                             'success': bool(r['success']),
                             'points': r.get('raid_points', 0)}
                            for mid in recent_matches for r in matches[mid]]

            self.player_stats[player_id] = build_raider_profile(recent_raids, all_raids)

        ranking = rank_players(self.player_stats)
        self.final_ranking = assign_ranks(ranking)

        # Auto-populate team in profile from player_id prefix (e.g. TeamA_P1 → TeamA)
        for pid in self.player_stats:
            profile = self.profile_manager.get_profile(pid)
            if profile.team == 'Unknown Team' and '_' in pid:
                profile.team = pid.split('_')[0]
        self.profile_manager.save_profiles()

    # ──────────────────────────────────────────────────────────────────────
    #  MAIN INTERFACE
    # ──────────────────────────────────────────────────────────────────────

    def create_main_interface(self):
        # Full-width branded page header
        page_header(self.root,
                    "Kabaddi Analytics System",
                    "Performance Intelligence Platform")

        # Tab bar
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True,
                           padx=PAD_MD, pady=(PAD_SM, PAD_MD))

        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame,   text="  Video Processing  ")

        self.ranking_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ranking_frame, text="  Player Rankings  ")

        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="  Analytics  ")

        self.teams_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.teams_frame,   text="  Teams  ")

        self.create_video_tab()
        self.create_ranking_tab()
        self.create_analytics_tab()
        self.create_teams_tab()

    # ──────────────────────────────────────────────────────────────────────
    #  VIDEO TAB
    # ──────────────────────────────────────────────────────────────────────

    def create_video_tab(self):
        outer = tk.Frame(self.video_frame, bg=BG)
        outer.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD_LG)

        # ── Upload controls card ──────────────────────────────────────────
        upload_frame = card(outer, padx=PAD_LG, pady=PAD_MD)
        upload_frame.pack(fill='x', pady=(0, PAD_MD))

        _card_title(upload_frame, "Video Upload & Processing")

        # File selection row
        file_row = tk.Frame(upload_frame, bg=CARD)
        file_row.pack(fill='x', pady=(PAD_SM, 0))

        flat_btn(file_row, "Select Video File",
                 command=self.select_video_file,
                 color=PRIMARY).pack(side='left')

        self.selected_file = tk.StringVar(value="No file selected")
        tk.Label(file_row, textvariable=self.selected_file,
                 font=F_BODY, fg=TEXT2, bg=CARD).pack(side='left', padx=PAD_MD)

        # Action buttons row
        btn_row = tk.Frame(upload_frame, bg=CARD)
        btn_row.pack(fill='x', pady=(PAD_SM, 0))

        flat_btn(btn_row, "Setup Court Lines",
                 command=self.setup_court_lines,
                 color=ACCENT).pack(side='left', padx=(0, PAD_SM))
        flat_btn(btn_row, "Process Video",
                 command=self.process_video,
                 color=SUCCESS).pack(side='left', padx=(0, PAD_SM))
        flat_btn(btn_row, "View Live Process",
                 command=self.view_live_process,
                 color=PRIMARY).pack(side='left')

        # ── Console card ──────────────────────────────────────────────────
        console_card = card(outer, padx=0, pady=0)
        console_card.pack(fill='both', expand=True)

        # Dark console header bar
        console_bar = tk.Frame(console_card, bg='#1e293b', padx=PAD_MD, pady=6)
        console_bar.pack(fill='x')
        tk.Label(console_bar, text="Processing Log",
                 font=('Segoe UI', 9, 'bold'), fg='#94a3b8',
                 bg='#1e293b').pack(side='left')

        # Text area with scrollbar
        text_container = tk.Frame(console_card, bg='#0f172a')
        text_container.pack(fill='both', expand=True)

        vsb = ttk.Scrollbar(text_container, orient='vertical')
        vsb.pack(side='right', fill='y')

        self.status_text = tk.Text(
            text_container,
            font=F_MONO,
            bg='#0f172a', fg='#94a3b8',
            relief='flat', borderwidth=0,
            padx=PAD_MD, pady=PAD_SM,
            insertbackground=TEXT3,
            selectbackground='#334155',
            selectforeground=WHITE,
            yscrollcommand=vsb.set,
            wrap='word'
        )
        vsb.config(command=self.status_text.yview)
        self.status_text.pack(fill='both', expand=True)

    # ──────────────────────────────────────────────────────────────────────
    #  RANKING TAB
    # ──────────────────────────────────────────────────────────────────────

    def create_ranking_tab(self):
        outer = tk.Frame(self.ranking_frame, bg=BG)
        outer.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD_LG)

        # ── Player Management card ────────────────────────────────────────
        control_frame = card(outer, padx=PAD_LG, pady=PAD_MD)
        control_frame.pack(fill='x', pady=(0, PAD_MD))

        _card_title(control_frame, "Player Management")

        # Two-column layout: Add | vertical rule | Delete
        cols = tk.Frame(control_frame, bg=CARD)
        cols.pack(fill='x', pady=(PAD_SM, 0))

        # ── Add column ────────────────────────────────────────────────────
        add_frame = tk.Frame(cols, bg=CARD)
        add_frame.pack(side='left', fill='both', expand=True, padx=(0, PAD_LG))

        tk.Label(add_frame, text="Add New Player Data",
                 font=F_H3, fg=TEXT, bg=CARD).pack(anchor='w', pady=(0, PAD_SM))

        input_frame = tk.Frame(add_frame, bg=CARD)
        input_frame.pack(fill='x')
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)

        def _lbl(text, row, col):
            tk.Label(input_frame, text=text,
                     font=F_LABEL, fg=TEXT2, bg=CARD).grid(
                row=row, column=col, sticky='w',
                padx=(0, PAD_SM), pady=6)

        _lbl("Match ID",         0, 0)
        self.match_id_entry = make_entry(input_frame, width=13)
        self.match_id_entry.grid(row=0, column=1, sticky='ew',
                                  padx=(0, PAD_LG), pady=6)

        _lbl("Player ID",        0, 2)
        self.player_id_entry = make_entry(input_frame, width=13)
        self.player_id_entry.grid(row=0, column=3, sticky='ew', pady=6)

        _lbl("Team Name",        1, 0)
        self.team_name_entry = make_entry(input_frame, width=13)
        self.team_name_entry.grid(row=1, column=1, sticky='ew',
                                   padx=(0, PAD_LG), pady=6)

        _lbl("Duration (sec)",   1, 2)
        self.duration_entry = make_entry(input_frame, width=13)
        self.duration_entry.grid(row=1, column=3, sticky='ew', pady=6)

        _lbl("Penetration (m)",  2, 0)
        self.penetration_entry = make_entry(input_frame, width=13)
        self.penetration_entry.grid(row=2, column=1, sticky='ew',
                                     padx=(0, PAD_LG), pady=6)

        _lbl("Success (1/0)",    2, 2)
        self.success_entry = make_entry(input_frame, width=13)
        self.success_entry.grid(row=2, column=3, sticky='ew', pady=6)

        _lbl("Raid Points (0-7)", 3, 0)
        self.points_entry = make_entry(input_frame, width=13)
        self.points_entry.grid(row=3, column=1, sticky='ew',
                                padx=(0, PAD_LG), pady=6)

        flat_btn(input_frame, "+ Add Data",
                 command=self.add_player_data,
                 color=SUCCESS).grid(row=4, column=0, columnspan=2,
                                     sticky='w', pady=(PAD_MD, 0))

        # Vertical divider
        tk.Frame(cols, bg=BORDER, width=1).pack(side='left', fill='y',
                                                 padx=PAD_LG)

        # ── Delete column ─────────────────────────────────────────────────
        delete_frame = tk.Frame(cols, bg=CARD)
        delete_frame.pack(side='left', fill='y')

        tk.Label(delete_frame, text="Delete Player",
                 font=F_H3, fg=TEXT, bg=CARD).pack(anchor='w',
                                                     pady=(0, PAD_SM))

        tk.Label(delete_frame, text="Player ID",
                 font=F_LABEL, fg=TEXT2, bg=CARD).pack(anchor='w')

        del_row = tk.Frame(delete_frame, bg=CARD)
        del_row.pack(fill='x', pady=(PAD_SM, PAD_MD))

        self.delete_player_entry = make_entry(del_row, width=18)
        self.delete_player_entry.pack(side='left')

        flat_btn(delete_frame, "Delete Player",
                 command=self.delete_player_data,
                 color=DANGER).pack(anchor='w')

        # ── Rankings table card ───────────────────────────────────────────
        self.create_rankings_display(outer)

    def create_rankings_display(self, parent=None):
        if parent is None:
            parent = self.ranking_frame

        display_card = card(parent, padx=0, pady=0)
        display_card.pack(fill='both', expand=True)

        _card_title(display_card, "Player Rankings", padx=PAD_MD)

        table_frame = tk.Frame(display_card, bg=CARD)
        table_frame.pack(fill='both', expand=True)

        columns = ('Rank', 'Player', 'Score', 'Success Rate', 'Avg Penetration',
                   'Avg Duration', 'Total Points', 'Total Raids', 'Avg Points', 'Matches')
        self.ranking_table = PlayerTable(
            table_frame,
            columns,
            self.profile_manager,
            self.player_stats,
            self.data,
            self.final_ranking,
            self._open_dashboard
        )

        self.update_display()

    # ──────────────────────────────────────────────────────────────────────
    #  VIDEO — backend helpers (unchanged)
    # ──────────────────────────────────────────────────────────────────────

    def select_video_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Kabaddi Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if file_path:
            self.selected_file.set(os.path.basename(file_path))
            self.video_path = file_path
            self.log_status(f"Selected video: {file_path}")

    def setup_court_lines(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
        self.current_video_path = self.video_path
        self.log_status("Setting up play area (court boundaries, midline, baulk, bonus)...")
        threading.Thread(target=self.run_setup_play_area, daemon=True).start()

    def setup_midline(self):
        self.setup_court_lines()

    def run_setup_play_area(self):
        try:
            self.log_status("=== PLAY AREA SETUP PROCESS ===")
            self.log_status("Step 1/2: Preparing video...")

            target_path = self.current_video_path
            self.log_status(f"Using video: {os.path.basename(target_path)}")

            self.log_status("Step 2/2: Interactive play area setup...")
            self.log_status(">>> INSTRUCTION: Click 13 points in order:")
            self.log_status("    1-5: Play box corners (pentagon, clockwise)")
            self.log_status("    6-7: Midline (2 points) - 0m")
            self.log_status("    8-9: Baulk line (2 points) - 3.75m from midline")
            self.log_status("    10-11: Bonus line (2 points) - 4.75m from midline")
            self.log_status("    12-13: End line (2 points) - 6.5m from midline")

            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            setup_script = os.path.join(root_dir, "court", "setup_play_area.py")
            result = subprocess.run([sys.executable, setup_script, target_path],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                self.log_status("Configuration saved successfully")
                self.log_status("=== PLAY AREA SETUP COMPLETED SUCCESSFULLY ===")
            else:
                self.log_status("Setup cancelled or failed")
                if result.stderr:
                    self.log_status(f"Error: {result.stderr}")

        except Exception as e:
            self.log_status(f"Error in play area setup: {str(e)}")
            import traceback
            traceback.print_exc()

    def process_video(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
        self.current_video_path = self.video_path
        self.log_status("Processing video for raid analysis...")
        threading.Thread(target=self.run_video_processing, daemon=True).start()

    def run_video_processing(self):
        try:
            self.log_status("=== VIDEO PROCESSING PIPELINE ===")
            VIDEO_PATH = self.current_video_path
            self.log_status(f"Processing: {os.path.basename(VIDEO_PATH)}")

            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(root_dir, "config", "play_area.json")

            if not os.path.exists(config_path):
                self.log_status("No play area configuration found!")
                self.log_status("Please run 'Setup Court Lines' first.")
                return

            self.log_status("Step 1/3: Initializing data extraction system...")
            self.log_status("Step 2/3: Running raid extraction...")
            self.log_status(">>> Detecting players, tracking raids, extracting metrics <<<")

            sys.path.append(os.path.join(root_dir, "scripts"))
            from scripts.data_extract import DataExtractor

            extractor = DataExtractor(VIDEO_PATH)
            raids = extractor.extract_data(display=True)

            self.log_status(f"Extraction complete! Total raids: {len(raids)}")
            self.log_status("Step 3/3: Saving results...")

            output_path = VIDEO_PATH.replace('.mp4', '_raid_metrics.csv')
            extractor.save_results(output_path)

            extracted_dir = os.path.join("data", "extracted")
            os.makedirs(extracted_dir, exist_ok=True)
            extracted_path = os.path.join(extracted_dir, "extracted_data.csv")
            shutil.copy2(output_path, extracted_path)

            self.log_status(f"Results saved to: {output_path}")
            self.log_status(f"Copied to: {extracted_path}")
            self.log_status("=== VIDEO PROCESSING COMPLETED SUCCESSFULLY ===")

            self.show_extracted_data_dialog(raids, extracted_path)

        except Exception as e:
            self.log_status(f"Error in video processing: {str(e)}")
            import traceback
            traceback.print_exc()

    def run_full_pipeline(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
        self.current_video_path = self.video_path
        self.log_status("=== FULL PIPELINE EXECUTION ===")
        self.log_status("This will run: Setup Midline → Process Video automatically")
        self.log_status("Phase 1: Setting up midline configuration...")
        threading.Thread(target=self.full_pipeline_thread, daemon=True).start()

    def full_pipeline_thread(self):
        self.run_setup_play_area()
        if "SETUP COMPLETED SUCCESSFULLY" in self.status_text.get("1.0", tk.END):
            self.log_status("Phase 2: Starting video processing...")
            self.run_video_processing()
            if "PROCESSING COMPLETED SUCCESSFULLY" in self.status_text.get("1.0", tk.END):
                self.log_status("=== FULL PIPELINE COMPLETED SUCCESSFULLY ===")
                self.log_status("Play area configured and saved")
                self.log_status("Video processed and raid metrics extracted")
                self.log_status("Results saved to CSV")
            else:
                self.log_status("Pipeline failed at video processing stage")
        else:
            self.log_status("Pipeline failed at play area setup stage")

    def show_extracted_data_dialog(self, raids, csv_path):
        """Show extracted raid data and ask user if they want to add to rankings"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Extracted Raid Data")
        dialog.geometry("960x740")
        dialog.configure(bg=BG)

        # Branded header strip
        hdr = tk.Frame(dialog, bg=PRIMARY, pady=PAD_MD)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Raid Extraction Complete",
                 font=F_H3, fg=WHITE, bg=PRIMARY).pack(padx=PAD_LG, anchor='w')
        tk.Label(hdr, text=f"{len(raids)} raids extracted — review and add to rankings below",
                 font=F_SMALL, fg='#bfdbfe', bg=PRIMARY).pack(padx=PAD_LG, anchor='w')
        tk.Frame(hdr, bg=SUCCESS, height=2).pack(fill='x', pady=(PAD_SM, 0))

        body = tk.Frame(dialog, bg=BG)
        body.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD_LG)

        # ── Raids table card ──────────────────────────────────────────────
        data_card = card(body, padx=0, pady=0)
        data_card.pack(fill='both', expand=True, pady=(0, PAD_MD))

        tbl_hdr = tk.Frame(data_card, bg=CARD, padx=PAD_MD, pady=PAD_SM)
        tbl_hdr.pack(fill='x')
        tk.Label(tbl_hdr, text="Extracted Raids",
                 font=F_H3, fg=TEXT, bg=CARD).pack(anchor='w')
        divider(data_card, bg=BORDER).pack(fill='x')

        tbl_cols = ('Raider ID', 'Duration', 'Max Penetration (m)',
                    'Crossed Bonus', 'Crossed Baulk', 'Avg Speed (m/s)')
        tree = ttk.Treeview(data_card, columns=tbl_cols, show='headings', height=8)
        for col in tbl_cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor='center')
        from court.simplified_court import SimplifiedCourtDynamics
        for raid in raids:
            tree.insert('', 'end', values=(
                raid['raider_id'],
                f"{raid['duration']:.2f}s",
                f"{raid['max_penetration']:.2f}m",
                'Yes' if raid['crossed_bonus'] else 'No',
                'Yes' if raid['crossed_baulk'] else 'No',
                f"{raid['avg_speed']:.2f}m/s"
            ))
        tree_vsb = ttk.Scrollbar(data_card, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=tree_vsb.set)
        tree_vsb.pack(side='right', fill='y', padx=(0, PAD_SM))
        tree.pack(fill='both', expand=True, padx=PAD_MD, pady=PAD_SM)

        # ── Entry form card ───────────────────────────────────────────────
        form_card = card(body, padx=PAD_LG, pady=PAD_MD)
        form_card.pack(fill='x')
        _card_title(form_card, "Enter Details to Add to Rankings")

        form_grid = tk.Frame(form_card, bg=CARD)
        form_grid.pack(fill='x', pady=(PAD_SM, 0))
        form_grid.columnconfigure(1, weight=1)
        form_grid.columnconfigure(3, weight=1)

        def _fl(text, row, col):
            tk.Label(form_grid, text=text,
                     font=F_LABEL, fg=TEXT2, bg=CARD).grid(
                row=row, column=col, sticky='w',
                padx=(0, PAD_SM), pady=6)

        _fl("Match ID", 0, 0)
        match_entry = make_entry(form_grid, width=22)
        match_entry.grid(row=0, column=1, sticky='ew',
                         padx=(0, PAD_LG), pady=6)
        match_entry.insert(0, "M_Video")

        _fl("Player ID", 0, 2)
        existing_players = list(set([row['player_id'] for row in self.data]))
        player_var = tk.StringVar()
        player_combo = ttk.Combobox(form_grid, textvariable=player_var,
                                    width=20, font=F_BODY)
        player_combo['values'] = existing_players
        player_combo.grid(row=0, column=3, sticky='ew', pady=6)
        player_combo.set(f"P{raids[0]['raider_id']}" if raids else "P1")

        _fl("Team Name", 1, 0)
        team_entry = make_entry(form_grid, width=22)
        team_entry.grid(row=1, column=1, sticky='ew',
                        padx=(0, PAD_LG), pady=6)
        team_entry.insert(0, "Team_A")

        _fl("Raid Points (comma-separated)", 2, 0)
        points_entry = make_entry(form_grid, width=22)
        points_entry.grid(row=2, column=1, sticky='ew',
                          padx=(0, PAD_LG), pady=6)
        points_entry.insert(0, ",".join(["1" if r['crossed_baulk'] else "0" for r in raids]))
        tk.Label(form_grid, text="e.g. 1, 2, 0, 3",
                 font=F_SMALL, fg=TEXT3, bg=CARD).grid(row=2, column=2, sticky='w')

        _fl("Success (comma-separated 1/0)", 3, 0)
        success_entry = make_entry(form_grid, width=22)
        success_entry.grid(row=3, column=1, sticky='ew',
                           padx=(0, PAD_LG), pady=6)
        success_entry.insert(0, ",".join(["1" if r['crossed_baulk'] else "0" for r in raids]))
        tk.Label(form_grid, text="e.g. 1, 1, 0, 1",
                 font=F_SMALL, fg=TEXT3, bg=CARD).grid(row=3, column=2, sticky='w')

        def add_to_rankings():
            try:
                match_id   = match_entry.get().strip()
                player_id  = player_var.get().strip()
                team_name  = team_entry.get().strip()
                points_str = points_entry.get().strip()
                success_str = success_entry.get().strip()

                if not match_id or not player_id or not team_name:
                    messagebox.showerror("Error", "Match ID, Player ID, and Team Name are required!")
                    return

                points_list  = [int(p.strip()) for p in points_str.split(',')]
                success_list = [int(s.strip()) for s in success_str.split(',')]

                if len(points_list) != len(raids) or len(success_list) != len(raids):
                    messagebox.showerror("Error",
                        f"Please provide exactly {len(raids)} values for points and success!")
                    return

                for i, raid in enumerate(raids):
                    self.data.append({
                        'match_id': match_id,
                        'player_id': player_id,
                        'raid_duration_sec': raid['duration'],
                        'penetration_px': raid['max_penetration'],
                        'success': success_list[i],
                        'raid_points': points_list[i]
                    })

                # Save team name to profile so dashboard shows it correctly
                self.profile_manager.update_profile(
                    player_id, team=team_name)

                self.save_data()
                self.update_rankings()
                self.update_display()
                dialog.destroy()
                self.log_status(f"Added {len(raids)} raids for player {player_id} to rankings!")
                messagebox.showinfo("Success",
                    f"Successfully added {len(raids)} raids to rankings!")

            except ValueError:
                messagebox.showerror("Error", "Invalid input! Please enter valid numbers.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add data: {str(e)}")

        def skip():
            dialog.destroy()
            self.log_status("Extracted data not added to rankings")

        # Footer action row
        footer = tk.Frame(dialog, bg=BG)
        footer.pack(fill='x', padx=PAD_LG, pady=(0, PAD_LG))
        flat_btn(footer, "Add to Rankings",
                 command=add_to_rankings,
                 color=SUCCESS).pack(side='left', padx=(0, PAD_SM))
        flat_btn(footer, "Skip",
                 command=skip,
                 color=DANGER).pack(side='left')

    def delete_player_data(self):
        try:
            player_id = self.delete_player_entry.get().strip()
            if not player_id:
                messagebox.showerror("Error", "Player ID cannot be empty!")
                return

            player_exists = any(row['player_id'] == player_id for row in self.data)
            if not player_exists:
                messagebox.showerror("Error", f"Player {player_id} not found in database!")
                return

            raids_to_delete = len([row for row in self.data
                                    if row['player_id'] == player_id])

            if messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete player {player_id}?\n\n"
                f"This will remove {raids_to_delete} raid records permanently."
            ):
                self.data = [row for row in self.data if row['player_id'] != player_id]
                self.save_data()
                self.update_rankings()
                self.update_display()

                if hasattr(self, 'selected_team') and self.selected_team.get():
                    self.show_team_players(self.selected_team.get())

                self.delete_player_entry.delete(0, tk.END)
                messagebox.showinfo("Success",
                    f"Player {player_id} deleted successfully!\n"
                    f"{raids_to_delete} raid records removed.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete player: {str(e)}")

    def add_player_data(self):
        try:
            match_id    = self.match_id_entry.get().strip()
            player_id   = self.player_id_entry.get().strip()
            duration    = float(self.duration_entry.get())
            penetration = float(self.penetration_entry.get())
            success     = int(self.success_entry.get())
            raid_points = int(self.points_entry.get()) if self.points_entry.get().strip() else 0

            if not match_id:
                match_id = "Manual"
            if not player_id:
                messagebox.showerror("Error", "Player ID cannot be empty!")
                return

            team_name = self.team_name_entry.get().strip()
            self.data.append({
                'match_id': match_id, 'player_id': player_id,
                'raid_duration_sec': duration,
                'penetration_px': penetration,
                'success': success, 'raid_points': raid_points
            })
            if team_name:
                self.profile_manager.update_profile(player_id, team=team_name)
            self.save_data()
            self.update_rankings()
            self.update_display()

            for e in (self.match_id_entry, self.player_id_entry, self.team_name_entry,
                      self.duration_entry, self.penetration_entry,
                      self.success_entry, self.points_entry):
                e.delete(0, tk.END)

            messagebox.showinfo("Success",
                f"Data added for player {player_id} in match {match_id}!")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add data: {str(e)}")

    # ──────────────────────────────────────────────────────────────────────
    #  ANALYTICS TAB
    # ──────────────────────────────────────────────────────────────────────

    def create_analytics_tab(self):
        """Create analytics tab with themed charts"""
        outer = tk.Frame(self.analytics_frame, bg=BG)
        outer.pack(fill='both', expand=True)

        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(
            2, 2, figsize=(13, 8))
        figure_bg(self.fig, BG)
        self.fig.tight_layout(pad=3.5)

        self.canvas = FigureCanvasTkAgg(self.fig, outer)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True,
                                          padx=PAD_MD, pady=PAD_MD)
        self.update_charts()

    def update_display(self):
        self.ranking_table.data         = self.data
        self.ranking_table.player_stats = self.player_stats
        self.ranking_table.final_ranking = self.final_ranking

        if hasattr(self, 'team_table'):
            self.team_table.data         = self.data
            self.team_table.player_stats = self.player_stats
            self.team_table.final_ranking = self.final_ranking

        self.ranking_table.populate()
        self.update_charts()
        self._refresh_team_buttons()

    def update_charts(self):
        if not hasattr(self, 'ax1'):
            return

        for ax in (self.ax1, self.ax2, self.ax3, self.ax4):
            ax.clear()

        top_players = [r['player_id'] for r in self.final_ranking[:10]]
        # Wrap long IDs at underscore so they don't crowd the x-axis
        labels = [p.replace('_', '\n') for p in top_players]

        scores = [r['score'] for r in self.final_ranking[:10]]

        # ── Chart 1: Overall Scores ─────────────────────────────────────
        bars1 = self.ax1.bar(range(len(top_players)), scores,
                             color=C_BLUE, edgecolor='none', width=0.62)
        if scores:
            bars1[scores.index(max(scores))].set_color(ACCENT)
        apply_chart_style(self.ax1, title='Overall Scores — Top 10', ylabel='Score')
        self.ax1.set_xticks(range(len(top_players)))
        self.ax1.set_xticklabels(labels, rotation=35, ha='right', fontsize=7.5)

        # ── Chart 2: Success Rates ──────────────────────────────────────
        success_rates = [
            self.player_stats[p].get('all_success_rate',
                                      self.player_stats[p]['success_rate'])
            for p in top_players
        ]
        bars2 = self.ax2.bar(range(len(top_players)), success_rates,
                             color=C_GREEN, edgecolor='none', width=0.62)
        if success_rates:
            bars2[success_rates.index(max(success_rates))].set_color(ACCENT)
        apply_chart_style(self.ax2, title='Success Rates — Top 10', ylabel='Success Rate (%)')
        self.ax2.set_xticks(range(len(top_players)))
        self.ax2.set_xticklabels(labels, rotation=35, ha='right', fontsize=7.5)

        # ── Chart 3: Average Penetration ────────────────────────────────
        penetrations = [
            self.player_stats[p].get('all_avg_penetration',
                                      self.player_stats[p]['avg_penetration'])
            for p in top_players
        ]
        bars3 = self.ax3.bar(range(len(top_players)), penetrations,
                             color=C_RED, edgecolor='none', width=0.62)
        if penetrations:
            bars3[penetrations.index(max(penetrations))].set_color(ACCENT)
        apply_chart_style(self.ax3, title='Avg Penetration — Top 10', ylabel='Penetration (m)')
        self.ax3.set_xticks(range(len(top_players)))
        self.ax3.set_xticklabels(labels, rotation=35, ha='right', fontsize=7.5)

        # ── Chart 4: Total Points ───────────────────────────────────────
        total_points = [
            sum(row.get('raid_points', 0) for row in self.data
                if row['player_id'] == p)
            for p in top_players
        ]
        bars4 = self.ax4.bar(range(len(top_players)), total_points,
                             color=C_ORANGE, edgecolor='none', width=0.62)
        if total_points:
            bars4[total_points.index(max(total_points))].set_color(PRIMARY)
        apply_chart_style(self.ax4, title='Total Points — Top 10', ylabel='Points')
        self.ax4.set_xticks(range(len(top_players)))
        self.ax4.set_xticklabels(labels, rotation=35, ha='right', fontsize=7.5)

        self.fig.tight_layout(pad=2.8)
        self.canvas.draw()

    # ──────────────────────────────────────────────────────────────────────
    #  MISC CALLBACKS (unchanged)
    # ──────────────────────────────────────────────────────────────────────

    def view_live_process(self):
        """Open keyframe viewer window"""
        open_keyframe_viewer(self.root)

    def _open_dashboard(self, player_id, profile, stats):
        """Open player dashboard — callback for PlayerTable"""
        PlayerDashboard(self.root, player_id, profile, stats, self.profile_manager)

    def log_status(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()

    # ──────────────────────────────────────────────────────────────────────
    #  TEAMS TAB
    # ──────────────────────────────────────────────────────────────────────

    def _refresh_team_buttons(self):
        """Rebuild team buttons when new teams are added."""
        if not hasattr(self, '_team_btn_frame'):
            return
        for w in self._team_btn_frame.winfo_children():
            w.destroy()
        teams = set()
        for pid in set(row['player_id'] for row in self.data):
            profile = self.profile_manager.get_profile(pid)
            if profile.team and profile.team != 'Unknown Team':
                teams.add(profile.team)
            elif '_' in pid:
                teams.add(pid.split('_')[0])
        for team in sorted(teams):
            b = tk.Button(
                self._team_btn_frame, text=f"  {team}",
                command=lambda t=team: self.show_team_players(t),
                bg=CARD, fg=TEXT2, font=F_BODY, relief='flat', bd=0,
                cursor='hand2', anchor='w',
                activebackground='#f1f5f9', activeforeground=PRIMARY,
                padx=PAD_MD, pady=PAD_SM, width=14)
            b.bind('<Enter>', lambda e, w=b: w.config(bg='#f1f5f9', fg=PRIMARY))
            b.bind('<Leave>', lambda e, w=b: w.config(bg=CARD, fg=TEXT2))
            b.pack(fill='x', pady=2)

    def create_teams_tab(self):
        """Create teams tab with team list and player tables"""
        outer = tk.Frame(self.teams_frame, bg=BG)
        outer.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD_LG)

        # ── Left: Team selector panel ─────────────────────────────────────
        left_panel = card(outer, padx=PAD_MD, pady=PAD_MD)
        left_panel.pack(side='left', fill='y', padx=(0, PAD_MD))

        tk.Label(left_panel, text="Teams",
                 font=F_H3, fg=TEXT, bg=CARD).pack(anchor='w', pady=(0, PAD_SM))
        divider(left_panel, bg=BORDER).pack(fill='x', pady=(0, PAD_SM))

        teams = set()
        for player_id in set(row['player_id'] for row in self.data):
            # Check saved profile for team name first
            profile = self.profile_manager.get_profile(player_id)
            if profile.team and profile.team != 'Unknown Team':
                teams.add(profile.team)
            elif '_' in player_id:
                teams.add(player_id.split('_')[0])

        self.selected_team = tk.StringVar()

        self._team_btn_frame = tk.Frame(left_panel, bg=CARD)
        self._team_btn_frame.pack(fill='x')
        for team in sorted(teams):
            b = tk.Button(
                self._team_btn_frame, text=f"  {team}",
                command=lambda t=team: self.show_team_players(t),
                bg=CARD, fg=TEXT2,
                font=F_BODY, relief='flat', bd=0,
                cursor='hand2', anchor='w',
                activebackground='#f1f5f9',
                activeforeground=PRIMARY,
                padx=PAD_MD, pady=PAD_SM, width=14)
            b.bind('<Enter>', lambda e, w=b: w.config(bg='#f1f5f9', fg=PRIMARY))
            b.bind('<Leave>', lambda e, w=b: w.config(bg=CARD, fg=TEXT2))
            b.pack(fill='x', pady=2)

        # ── Right: Players panel ──────────────────────────────────────────
        right_panel = tk.Frame(outer, bg=BG)
        right_panel.pack(side='left', fill='both', expand=True)

        # Team name header card
        name_card = card(right_panel, padx=PAD_LG, pady=PAD_SM)
        name_card.pack(fill='x', pady=(0, PAD_MD))
        self.team_name_label = tk.Label(
            name_card,
            text="Select a team to view players",
            font=F_H2, fg=TEXT2, bg=CARD)
        self.team_name_label.pack(anchor='w')

        # Player table card
        table_card = card(right_panel, padx=0, pady=0)
        table_card.pack(fill='both', expand=True)

        columns = ('Rank', 'Player', 'Score', 'Success Rate', 'Avg Penetration',
                   'Total Points', 'Total Raids', 'Avg Points', 'Matches')
        self.team_table = PlayerTable(
            table_card,
            columns,
            self.profile_manager,
            self.player_stats,
            self.data,
            self.final_ranking,
            self._open_dashboard
        )

    def show_team_players(self, team_name):
        """Display players for selected team"""
        self.selected_team.set(team_name)
        self.team_name_label.config(
            text=f"  {team_name}  —  Player Rankings",
            fg=TEXT, font=F_H2)

        def _team_filter(pid):
            # Match by saved profile team name OR by ID prefix
            profile = self.profile_manager.get_profile(pid)
            if profile.team and profile.team != 'Unknown Team':
                return profile.team == team_name
            return pid.startswith(team_name + '_')

        self.team_table.populate(player_filter=_team_filter)


# ── Module-level UI helper (shared across methods) ─────────────────────────

def _card_title(parent, text, padx=PAD_MD):
    """Renders a left-accented section title + divider inside a card."""
    row = tk.Frame(parent, bg=CARD)
    row.pack(fill='x', padx=padx, pady=(0, PAD_SM))
    tk.Frame(row, bg=PRIMARY, width=3, height=18).pack(side='left',
                                                        padx=(0, PAD_SM))
    tk.Label(row, text=text, font=F_H3, fg=TEXT, bg=CARD).pack(side='left')
    divider(parent, bg=BORDER).pack(fill='x', pady=(0, PAD_MD))


if __name__ == "__main__":
    root = tk.Tk()
    app = KabaddiAnalyticsApp(root)
    root.mainloop()