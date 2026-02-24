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

class KabaddiAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kabaddi Analytics System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Load synthetic data
        self.load_data()
        
        # Create main interface
        self.create_main_interface()
        
    def load_data(self):
        """Load extracted raid data and calculate rankings"""
        try:
            self.data = []
            # First try to load extracted data from real video processing
            extracted_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "extracted", "extracted_data.csv")
            
            if os.path.exists(extracted_path):
                print(f"Loading extracted data from: {extracted_path}")
                with open(extracted_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            # Check if it's the new format (from data_extract.py)
                            if 'raider_id' in row and 'duration' in row:
                                self.data.append({
                                    'match_id': 'Extracted',
                                    'player_id': str(row['raider_id']),
                                    'raid_duration_sec': float(row['duration']),
                                    'penetration_px': float(row['max_penetration']),
                                    'success': 1 if row.get('crossed_baulk', 'False') == 'True' else 0,
                                    'raid_points': 1 if row.get('crossed_baulk', 'False') == 'True' else 0
                                })
                            # Old format
                            elif 'player_id' in row and 'duration_sec' in row:
                                self.data.append({
                                    'match_id': 'Extracted',
                                    'player_id': row['player_id'],
                                    'raid_duration_sec': float(row['duration_sec']),
                                    'penetration_px': float(row['penetration_px']),
                                    'success': int(row['success']),
                                    'raid_points': 1 if int(row['success']) == 1 else 0
                                })
                        except (ValueError, KeyError) as e:
                            print(f"Skipping invalid row: {row} - Error: {e}")
                            continue
                
                if self.data:
                    print(f"Loaded {len(self.data)} raids from extracted data")
                    self.update_rankings()
                    return
            
            # Fallback to synthetic data
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "synthetic", "synthetic_data.csv")
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Handle empty or invalid values
                        raid_points = row.get('raid_points', '').strip()
                        if not raid_points or raid_points == '':
                            raid_points = 0
                        else:
                            raid_points = int(raid_points)
                        
                        self.data.append({
                            'match_id': row['match_id'],
                            'player_id': row['player_id'],
                            'raid_duration_sec': float(row['raid_duration_sec']),
                            'penetration_px': float(row['penetration_px']),
                            'success': int(row['success']),
                            'raid_points': raid_points
                        })
                    except (ValueError, KeyError) as e:
                        print(f"Skipping invalid row: {row} - Error: {e}")
                        continue
            
            if not self.data:
                print("No valid data found, creating sample data...")
                self.create_sample_data()
            else:
                self.update_rankings()
                
        except FileNotFoundError:
            print("synthetic_data.csv not found, creating sample data...")
            self.create_sample_data()
            
    def create_sample_data(self):
        """Create realistic synthetic data"""
        import random
        
        self.data = []
        
        # 20+ players with realistic names
        players = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10',
                  'R11', 'R12', 'R13', 'R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20',
                  'R21', 'R22', 'R23', 'R24', 'R25']
        
        # 8 matches
        matches = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8']
        
        for player in players:
            # Each player participates in 6-10 matches randomly
            player_matches = random.sample(matches, random.randint(6, 8))
            
            for match in player_matches:
                # Each player has 30-200 total raids across all matches
                raids_in_match = random.randint(4, 25)  # Distributed across matches
                
                for _ in range(raids_in_match):
                    # Realistic raid parameters
                    duration = round(random.uniform(2.0, 8.0), 1)  # 2-8 seconds
                    penetration = random.randint(100, 250)  # 100-250 pixels
                    success = random.choice([0, 1])  # Random success
                    
                    # Add raid points based on success
                    if success == 1:
                        raid_points = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 8, 2])[0]
                    else:
                        raid_points = 0
                    
                    self.data.append({
                        'match_id': match,
                        'player_id': player,
                        'raid_duration_sec': duration,
                        'penetration_px': penetration,
                        'success': success,
                        'raid_points': raid_points
                    })
        
        # Ensure each player has 30-200 total raids
        player_raid_counts = {}
        for row in self.data:
            player_id = row['player_id']
            player_raid_counts[player_id] = player_raid_counts.get(player_id, 0) + 1
        
        # Adjust raid counts to meet requirements
        for player in players:
            current_count = player_raid_counts.get(player, 0)
            target_count = random.randint(30, 200)
            
            if current_count < target_count:
                # Add more raids
                for _ in range(target_count - current_count):
                    match = random.choice(player_matches if player in [p for p in players if p in [row['player_id'] for row in self.data]] else matches[:6])
                    success = random.choice([0, 1])
                    raid_points = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 8, 2])[0] if success else 0
                    
                    self.data.append({
                        'match_id': match,
                        'player_id': player,
                        'raid_duration_sec': round(random.uniform(2.0, 8.0), 1),
                        'penetration_px': random.randint(100, 250),
                        'success': success,
                        'raid_points': raid_points
                    })
            elif current_count > target_count:
                # Remove excess raids
                player_data = [row for row in self.data if row['player_id'] == player]
                excess = current_count - target_count
                to_remove = random.sample(player_data, excess)
                for row in to_remove:
                    self.data.remove(row)
        
        self.save_data()
        self.update_rankings()
        
    def save_data(self):
        """Save data to CSV"""
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "synthetic", "synthetic_data.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['match_id', 'player_id', 'raid_duration_sec', 'penetration_px', 'success', 'raid_points'])
            writer.writeheader()
            writer.writerows(self.data)
        
    def update_rankings(self):
        """Calculate player rankings from data"""
        self.player_stats = {}
        
        # Group data by player and match
        player_data = {}
        for row in self.data:
            player_id = row['player_id']
            if player_id not in player_data:
                player_data[player_id] = []
            player_data[player_id].append(row)
        
        # Calculate stats for each player
        for player_id, raids_data in player_data.items():
            # Group by match to get match order
            matches = {}
            for row in raids_data:
                match_id = row['match_id']
                if match_id not in matches:
                    matches[match_id] = []
                matches[match_id].append(row)
            
            # Sort matches (assuming M1, M2, M3... format)
            sorted_matches = sorted(matches.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
            
            # Get last 15 matches for scoring
            recent_matches = sorted_matches[-15:] if len(sorted_matches) > 15 else sorted_matches
            
            # All raids for display stats
            all_raids = []
            for row in raids_data:
                all_raids.append({
                    'duration': row['raid_duration_sec'],
                    'penetration': row['penetration_px'],
                    'success': bool(row['success']),
                    'points': row.get('raid_points', 0)
                })
            
            # Recent raids for scoring
            recent_raids = []
            for match_id in recent_matches:
                for row in matches[match_id]:
                    recent_raids.append({
                        'duration': row['raid_duration_sec'],
                        'penetration': row['penetration_px'],
                        'success': bool(row['success']),
                        'points': row.get('raid_points', 0)
                    })
            
            # Build profile with recent raids for scoring, all raids for display
            self.player_stats[player_id] = build_raider_profile(recent_raids, all_raids)
        
        # Calculate rankings based on recent performance
        ranking = rank_players(self.player_stats)
        self.final_ranking = assign_ranks(ranking)
        
    def create_main_interface(self):
        # Title
        title = tk.Label(self.root, text="Kabaddi Analytics System", 
                        font=("Arial", 24, "bold"), fg='white', bg='#2c3e50')
        title.pack(pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Video Processing Tab
        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame, text="Video Processing")
        self.create_video_tab()
        
        # Player Rankings Tab
        self.ranking_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ranking_frame, text="Player Rankings")
        self.create_ranking_tab()
        
    def create_video_tab(self):
        # Video upload section
        upload_frame = tk.LabelFrame(self.video_frame, text="Video Upload & Processing", 
                                   font=("Arial", 14, "bold"), padx=10, pady=10)
        upload_frame.pack(fill='x', padx=10, pady=10)
        
        # File selection
        self.selected_file = tk.StringVar(value="No file selected")
        file_frame = tk.Frame(upload_frame)
        file_frame.pack(fill='x', pady=5)
        
        tk.Button(file_frame, text="Select Video File", command=self.select_video_file,
                 bg='#3498db', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        tk.Label(file_frame, textvariable=self.selected_file, 
                font=("Arial", 10)).pack(side='left', padx=10)
        
        # Processing buttons
        button_frame = tk.Frame(upload_frame)
        button_frame.pack(fill='x', pady=10)
        
        tk.Button(button_frame, text="Setup Midline", command=self.setup_midline,
                 bg='#e74c3c', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Setup Court Lines", command=self.setup_court_lines,
                 bg='#e67e22', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Process Video", command=self.process_video,
                 bg='#27ae60', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Full Pipeline", command=self.run_full_pipeline,
                 bg='#9b59b6', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="View Live Process", command=self.view_live_process,
                 bg='#f39c12', fg='white', font=("Arial", 12)).pack(side='left', padx=5)
        
        # Status display
        self.status_text = tk.Text(upload_frame, height=15, width=80)
        self.status_text.pack(fill='both', expand=True, pady=10)
        
    def create_ranking_tab(self):
        # Control panel
        control_frame = tk.LabelFrame(self.ranking_frame, text="Player Management", 
                                    font=("Arial", 14, "bold"), padx=10, pady=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Add new player section
        add_frame = tk.Frame(control_frame)
        add_frame.pack(fill='x', pady=5)
        
        tk.Label(add_frame, text="Add New Player Data:", font=("Arial", 12, "bold")).pack(anchor='w')
        
        # Input fields
        input_frame = tk.Frame(add_frame)
        input_frame.pack(fill='x', pady=5)
        
        tk.Label(input_frame, text="Match ID:").grid(row=0, column=0, padx=5, sticky='w')
        self.match_id_entry = tk.Entry(input_frame, width=10)
        self.match_id_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(input_frame, text="Player ID:").grid(row=0, column=2, padx=5, sticky='w')
        self.player_id_entry = tk.Entry(input_frame, width=10)
        self.player_id_entry.grid(row=0, column=3, padx=5)
        
        tk.Label(input_frame, text="Duration (sec):").grid(row=1, column=0, padx=5, sticky='w')
        self.duration_entry = tk.Entry(input_frame, width=10)
        self.duration_entry.grid(row=1, column=1, padx=5)
        
        tk.Label(input_frame, text="Penetration (px):").grid(row=1, column=2, padx=5, sticky='w')
        self.penetration_entry = tk.Entry(input_frame, width=10)
        self.penetration_entry.grid(row=1, column=3, padx=5)
        
        tk.Label(input_frame, text="Success (1/0):").grid(row=2, column=0, padx=5, sticky='w')
        self.success_entry = tk.Entry(input_frame, width=10)
        self.success_entry.grid(row=2, column=1, padx=5)
        
        tk.Label(input_frame, text="Raid Points (0-7):").grid(row=2, column=2, padx=5, sticky='w')
        self.points_entry = tk.Entry(input_frame, width=10)
        self.points_entry.grid(row=2, column=3, padx=5)
        
        tk.Button(input_frame, text="Add Data", command=self.add_player_data,
                 bg='#3498db', fg='white').grid(row=3, column=0, padx=10)
        
        # Delete player section
        delete_frame = tk.Frame(add_frame)
        delete_frame.pack(fill='x', pady=10)
        
        tk.Label(delete_frame, text="Delete Player:", font=("Arial", 12, "bold")).pack(anchor='w')
        
        delete_input_frame = tk.Frame(delete_frame)
        delete_input_frame.pack(fill='x', pady=5)
        
        tk.Label(delete_input_frame, text="Player ID to Delete:").grid(row=0, column=0, padx=5, sticky='w')
        self.delete_player_entry = tk.Entry(delete_input_frame, width=15)
        self.delete_player_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(delete_input_frame, text="Delete Player", command=self.delete_player_data,
                 bg='#e74c3c', fg='white').grid(row=0, column=2, padx=10)
        
        # Rankings display
        self.create_rankings_display()
        
    def create_rankings_display(self):
        # Rankings table and chart
        display_frame = tk.Frame(self.ranking_frame)
        display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Rankings table
        table_frame = tk.LabelFrame(display_frame, text="Player Rankings", 
                                  font=("Arial", 12, "bold"))
        table_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Treeview for rankings
        columns = ('Rank', 'Player', 'Score', 'Success Rate', 'Avg Penetration', 'Avg Duration', 'Total Points', 'Total Raids', 'Avg Points', 'Matches')
        self.ranking_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Store sort direction for each column
        self.sort_reverse = {col: False for col in columns}
        
        # Adjust column widths and add sorting
        for col in columns:
            self.ranking_tree.heading(col, text=col, command=lambda c=col: self.sort_table(c))
            if col in ['Success Rate', 'Avg Penetration', 'Avg Duration', 'Avg Points']:
                self.ranking_tree.column(col, width=100)
            else:
                self.ranking_tree.column(col, width=80)
        
        self.ranking_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Right side - Charts
        chart_frame = tk.LabelFrame(display_frame, text="Performance Charts", 
                                  font=("Arial", 12, "bold"))
        chart_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        # Create matplotlib figure
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        self.fig.patch.set_facecolor('white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initial display
        self.update_display()
        
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
        
        # Store the selected video path for later use
        self.current_video_path = self.video_path
        self.log_status("Setting up play area (court boundaries, midline, baulk, bonus)...")
        threading.Thread(target=self.run_setup_play_area, daemon=True).start()
    
    def setup_midline(self):
        # Redirect to play area setup
        self.setup_court_lines()
        
    def run_setup_play_area(self):
        try:
            self.log_status("=== PLAY AREA SETUP PROCESS ===")
            self.log_status("Step 1/2: Preparing video...")
            
            # Use the stored video path
            target_path = self.current_video_path
            self.log_status(f"Using video: {os.path.basename(target_path)}")
            
            self.log_status("Step 2/2: Interactive play area setup...")
            self.log_status(">>> INSTRUCTION: Click 11 points in order:")
            self.log_status("    1-5: Play box corners (pentagon, clockwise)")
            self.log_status("    6-7: Midline (2 points)")
            self.log_status("    8-9: Baulk line (2 points)")
            self.log_status("    10-11: Bonus line (2 points)")
            
            # Import and run setup_play_area
            import subprocess
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            setup_script = os.path.join(root_dir, "court", "setup_play_area.py")
            
            # Run the setup script with the video path
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
        
        # Store the selected video path for processing
        self.current_video_path = self.video_path
        self.log_status("Processing video for raid analysis...")
        threading.Thread(target=self.run_video_processing, daemon=True).start()
        
    def run_video_processing(self):
        try:
            self.log_status("=== VIDEO PROCESSING PIPELINE ===")
            
            # Use the stored video path
            VIDEO_PATH = self.current_video_path
            self.log_status(f"Processing: {os.path.basename(VIDEO_PATH)}")
            
            # Check if play area is configured
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(root_dir, "config", "play_area.json")
            
            if not os.path.exists(config_path):
                self.log_status("❌ No play area configuration found!")
                self.log_status("Please run 'Setup Court Lines' first.")
                return
            
            self.log_status("Step 1/3: Initializing data extraction system...")
            
            self.log_status("Step 2/3: Running raid extraction...")
            self.log_status(">>> Detecting players, tracking raids, extracting metrics <<<")
            
            # Import and run data extractor
            sys.path.append(os.path.join(root_dir, "scripts"))
            from scripts.data_extract import DataExtractor
            
            extractor = DataExtractor(VIDEO_PATH)
            raids = extractor.extract_data(display=False)
            
            self.log_status(f"Extraction complete! Total raids: {len(raids)}")
            
            self.log_status("Step 3/3: Saving results...")
            output_path = VIDEO_PATH.replace('.mp4', '_raid_metrics.csv')
            extractor.save_results(output_path)
            
            # Copy to extracted folder
            extracted_dir = os.path.join("data", "extracted")
            os.makedirs(extracted_dir, exist_ok=True)
            extracted_path = os.path.join(extracted_dir, "extracted_data.csv")
            shutil.copy2(output_path, extracted_path)
            
            self.log_status(f"Results saved to: {output_path}")
            self.log_status(f"Copied to: {extracted_path}")
            self.log_status("=== VIDEO PROCESSING COMPLETED SUCCESSFULLY ===")
            
            # Show extracted data and ask user for additional details
            self.show_extracted_data_dialog(raids, extracted_path)
                
        except Exception as e:
            self.log_status(f"Error in video processing: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def run_full_pipeline(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
        
        # Store the selected video path for full pipeline
        self.current_video_path = self.video_path
        self.log_status("=== FULL PIPELINE EXECUTION ===")
        self.log_status("This will run: Setup Midline → Process Video automatically")
        self.log_status("Phase 1: Setting up midline configuration...")
        threading.Thread(target=self.full_pipeline_thread, daemon=True).start()
        
    def full_pipeline_thread(self):
        # Phase 1: Setup
        self.run_setup_play_area()
        
        # Check if setup was successful
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
        dialog.geometry("900x700")
        dialog.configure(bg='#ecf0f1')
        
        # Title
        tk.Label(dialog, text="Raid Extraction Complete!", font=("Arial", 16, "bold"), bg='#ecf0f1').pack(pady=10)
        
        # Display extracted data
        data_frame = tk.LabelFrame(dialog, text="Extracted Raids", font=("Arial", 12, "bold"), padx=10, pady=10)
        data_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for raids
        columns = ('Raider ID', 'Duration', 'Max Penetration', 'Crossed Bonus', 'Crossed Baulk', 'Avg Speed')
        tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        for raid in raids:
            tree.insert('', 'end', values=(
                raid['raider_id'],
                f"{raid['duration']:.2f}s",
                f"{raid['max_penetration']:.1f}px",
                'Yes' if raid['crossed_bonus'] else 'No',
                'Yes' if raid['crossed_baulk'] else 'No',
                f"{raid['avg_speed']:.1f}px/s"
            ))
        
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Form for additional details (shown immediately)
        form_frame = tk.LabelFrame(dialog, text="Enter Details to Add to Rankings", font=("Arial", 12, "bold"), padx=20, pady=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Match ID
        tk.Label(form_frame, text="Match ID:", font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5, padx=5)
        match_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        match_entry.grid(row=0, column=1, pady=5, padx=5)
        match_entry.insert(0, "M_Video")
        
        # Player ID
        tk.Label(form_frame, text="Player ID:", font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5, padx=5)
        player_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        player_entry.grid(row=1, column=1, pady=5, padx=5)
        player_entry.insert(0, f"P{raids[0]['raider_id']}" if raids else "P1")
        
        # Raid Points
        tk.Label(form_frame, text="Raid Points (comma-separated):", font=("Arial", 10)).grid(row=2, column=0, sticky='w', pady=5, padx=5)
        points_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        points_entry.grid(row=2, column=1, pady=5, padx=5)
        points_entry.insert(0, ",".join(["1" if r['crossed_baulk'] else "0" for r in raids]))
        tk.Label(form_frame, text="(e.g., 1,2,0,3)", font=("Arial", 8), fg='gray').grid(row=2, column=2, sticky='w', padx=5)
        
        # Success
        tk.Label(form_frame, text="Success (comma-separated 1/0):", font=("Arial", 10)).grid(row=3, column=0, sticky='w', pady=5, padx=5)
        success_entry = tk.Entry(form_frame, width=25, font=("Arial", 10))
        success_entry.grid(row=3, column=1, pady=5, padx=5)
        success_entry.insert(0, ",".join(["1" if r['crossed_baulk'] else "0" for r in raids]))
        tk.Label(form_frame, text="(e.g., 1,1,0,1)", font=("Arial", 8), fg='gray').grid(row=3, column=2, sticky='w', padx=5)
        
        def add_to_rankings():
            try:
                match_id = match_entry.get().strip()
                player_id = player_entry.get().strip()
                points_str = points_entry.get().strip()
                success_str = success_entry.get().strip()
                
                if not match_id or not player_id:
                    messagebox.showerror("Error", "Match ID and Player ID are required!")
                    return
                
                # Parse points and success
                points_list = [int(p.strip()) for p in points_str.split(',')]
                success_list = [int(s.strip()) for s in success_str.split(',')]
                
                if len(points_list) != len(raids) or len(success_list) != len(raids):
                    messagebox.showerror("Error", f"Please provide exactly {len(raids)} values for points and success!")
                    return
                
                # Add raids to data
                for i, raid in enumerate(raids):
                    self.data.append({
                        'match_id': match_id,
                        'player_id': player_id,
                        'raid_duration_sec': raid['duration'],
                        'penetration_px': raid['max_penetration'],
                        'success': success_list[i],
                        'raid_points': points_list[i]
                    })
                
                self.save_data()
                self.update_rankings()
                self.update_display()
                
                dialog.destroy()
                self.log_status(f"Added {len(raids)} raids for player {player_id} to rankings!")
                messagebox.showinfo("Success", f"Successfully added {len(raids)} raids to rankings!")
                
            except ValueError:
                messagebox.showerror("Error", "Invalid input! Please enter valid numbers.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add data: {str(e)}")
        
        def skip():
            dialog.destroy()
            self.log_status("Extracted data not added to rankings")
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#ecf0f1')
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Add to Rankings", command=add_to_rankings,
                 bg='#27ae60', fg='white', font=("Arial", 11), padx=30).pack(side='left', padx=10)
        tk.Button(button_frame, text="Skip", command=skip,
                 bg='#e74c3c', fg='white', font=("Arial", 11), padx=30).pack(side='left', padx=10)
    def delete_player_data(self):
        try:
            player_id = self.delete_player_entry.get().strip()
            
            if not player_id:
                messagebox.showerror("Error", "Player ID cannot be empty!")
                return
            
            # Check if player exists
            player_exists = any(row['player_id'] == player_id for row in self.data)
            
            if not player_exists:
                messagebox.showerror("Error", f"Player {player_id} not found in database!")
                return
            
            # Count raids to be deleted
            raids_to_delete = len([row for row in self.data if row['player_id'] == player_id])
            
            # Confirm deletion
            result = messagebox.askyesno(
                "Confirm Deletion", 
                f"Are you sure you want to delete player {player_id}?\n\n"
                f"This will remove {raids_to_delete} raid records permanently."
            )
            
            if result:
                # Remove all data for this player
                self.data = [row for row in self.data if row['player_id'] != player_id]
                self.save_data()
                
                # Update rankings
                self.update_rankings()
                self.update_display()
                
                # Clear entry
                self.delete_player_entry.delete(0, tk.END)
                
                messagebox.showinfo("Success", f"Player {player_id} deleted successfully!\n{raids_to_delete} raid records removed.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete player: {str(e)}")
            
    def add_player_data(self):
        try:
            match_id = self.match_id_entry.get().strip()
            player_id = self.player_id_entry.get().strip()
            duration = float(self.duration_entry.get())
            penetration = float(self.penetration_entry.get())
            success = int(self.success_entry.get())
            raid_points = int(self.points_entry.get()) if self.points_entry.get().strip() else 0
            
            if not match_id:
                match_id = "Manual"
            if not player_id:
                messagebox.showerror("Error", "Player ID cannot be empty!")
                return
                
            # Add to data
            new_row = {
                'match_id': match_id,
                'player_id': player_id,
                'raid_duration_sec': duration,
                'penetration_px': penetration,
                'success': success,
                'raid_points': raid_points
            }
            
            self.data.append(new_row)
            self.save_data()
            
            # Update rankings
            self.update_rankings()
            self.update_display()
            
            # Clear entries
            self.match_id_entry.delete(0, tk.END)
            self.player_id_entry.delete(0, tk.END)
            self.duration_entry.delete(0, tk.END)
            self.penetration_entry.delete(0, tk.END)
            self.success_entry.delete(0, tk.END)
            self.points_entry.delete(0, tk.END)
            
            messagebox.showinfo("Success", f"Data added for player {player_id} in match {match_id}!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add data: {str(e)}")
            
    def update_display(self):
        # Clear existing items
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        
        # Populate rankings table
        for rank_data in self.final_ranking:
            player_id = rank_data['player_id']
            profile = self.player_stats[player_id]
            
            # Count unique matches for this player
            player_matches = set(row['match_id'] for row in self.data if row['player_id'] == player_id)
            
            # Calculate total points and avg points per raid
            total_points = sum(row.get('raid_points', 0) for row in self.data if row['player_id'] == player_id)
            total_raids = profile.get('all_raids', profile['raids'])
            avg_points_per_raid = total_points / total_raids if total_raids > 0 else 0
            
            self.ranking_tree.insert('', 'end', values=(
                rank_data['rank'],
                player_id,
                f"{rank_data['score']:.3f}",  # Recent score only
                f"{profile.get('all_success_rate', profile['success_rate']):.2f}",  # Overall SR
                f"{profile.get('all_avg_penetration', profile['avg_penetration']):.0f}",  # Overall penetration
                f"{profile.get('all_avg_duration', profile['avg_duration']):.1f}",  # Overall duration
                total_points,  # Total points
                total_raids,  # Total raids
                f"{avg_points_per_raid:.2f}",  # Avg points per raid
                len(player_matches)  # Total matches
            ))
        
        # Update charts
        self.update_charts()
        
    def update_charts(self):
        # Clear previous plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
        
        players = [r['player_id'] for r in self.final_ranking]
        scores = [r['score'] for r in self.final_ranking]
        
        # Chart 1: Overall Scores
        self.ax1.bar(players, scores, color='#3498db')
        self.ax1.set_title('Player Scores')
        self.ax1.set_ylabel('Score')
        
        # Chart 2: Success Rates (Overall)
        success_rates = [self.player_stats[p].get('all_success_rate', self.player_stats[p]['success_rate']) for p in players]
        self.ax2.bar(players, success_rates, color='#2ecc71')
        self.ax2.set_title('Success Rates (Overall)')
        self.ax2.set_ylabel('Success Rate')
        
        # Chart 3: Average Penetration (Overall)
        penetrations = [self.player_stats[p].get('all_avg_penetration', self.player_stats[p]['avg_penetration']) for p in players]
        self.ax3.bar(players, penetrations, color='#e74c3c')
        self.ax3.set_title('Average Penetration (Overall)')
        self.ax3.set_ylabel('Penetration (px)')
        
        # Chart 4: Total Points
        total_points = [sum(row.get('raid_points', 0) for row in self.data if row['player_id'] == p) for p in players]
        self.ax4.bar(players, total_points, color='#f39c12')
        self.ax4.set_title('Total Points')
        self.ax4.set_ylabel('Points')
        
        plt.tight_layout()
        self.canvas.draw()
        
    def view_live_process(self):
        """Open a window to view key frames from raid processing"""
        keyframes_dir = os.path.join("data", "keyframes")
        if not os.path.exists(keyframes_dir):
            messagebox.showinfo("Info", "No key frames found. Please run video processing first.")
            return
            
        # Create new window for live view
        live_window = tk.Toplevel(self.root)
        live_window.title("Raid Key Frames Viewer")
        live_window.geometry("900x700")
        
        # Title
        tk.Label(live_window, text="Raid Key Frames", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(live_window, text="Start → Bonus → Baulk → End", font=("Arial", 10)).pack()
        
        # Frame display
        frame_label = tk.Label(live_window)
        frame_label.pack(pady=10)
        
        # Controls
        control_frame = tk.Frame(live_window)
        control_frame.pack(pady=10)
        
        # Get available frames
        frame_files = [f for f in os.listdir(keyframes_dir) if f.endswith('.jpg')]
        frame_files.sort(key=lambda x: (int(x.split('_')[1]), x.split('_')[2], int(x.split('_')[-1].split('.')[0])))
        
        if not frame_files:
            tk.Label(live_window, text="No key frames available", font=("Arial", 14)).pack(pady=50)
            return
            
        current_frame = tk.IntVar(value=0)
        
        def update_frame():
            if frame_files:
                frame_path = os.path.join(keyframes_dir, frame_files[current_frame.get()])
                if os.path.exists(frame_path):
                    import cv2
                    from PIL import Image, ImageTk
                    
                    img = cv2.imread(frame_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (800, 600))
                    
                    photo = ImageTk.PhotoImage(Image.fromarray(img))
                    frame_label.configure(image=photo)
                    frame_label.image = photo
                    
                    # Parse filename for info
                    fname = frame_files[current_frame.get()]
                    parts = fname.replace('.jpg', '').split('_')
                    raid_num = parts[1]
                    event_type = parts[2]
                    frame_num = parts[-1]
                    
                    info_text = f"Raid #{raid_num} - {event_type.upper()} - Frame {frame_num} ({current_frame.get()+1}/{len(frame_files)})"
                    frame_info.set(info_text)
        
        frame_info = tk.StringVar()
        tk.Label(control_frame, textvariable=frame_info, font=("Arial", 12)).pack(pady=5)
        
        # Navigation buttons
        nav_frame = tk.Frame(control_frame)
        nav_frame.pack(pady=5)
        
        def prev_frame():
            if current_frame.get() > 0:
                current_frame.set(current_frame.get() - 1)
                update_frame()
                
        def next_frame():
            if current_frame.get() < len(frame_files) - 1:
                current_frame.set(current_frame.get() + 1)
                update_frame()
        
        tk.Button(nav_frame, text="◀ Previous", command=prev_frame).pack(side='left', padx=5)
        tk.Button(nav_frame, text="Next ▶", command=next_frame).pack(side='left', padx=5)
        
        # Frame slider
        frame_scale = tk.Scale(control_frame, from_=0, to=len(frame_files)-1, orient='horizontal',
                              variable=current_frame, command=lambda x: update_frame(), length=400)
        frame_scale.pack(pady=10)
        
        # Auto-play controls
        auto_frame = tk.Frame(control_frame)
        auto_frame.pack(pady=5)
        
        auto_playing = tk.BooleanVar()
        
        def auto_play():
            if auto_playing.get():
                if current_frame.get() < len(frame_files) - 1:
                    current_frame.set(current_frame.get() + 1)
                    update_frame()
                    live_window.after(500, auto_play)  # 500ms delay
                else:
                    auto_playing.set(False)
                    play_button.config(text="▶ Play")
        
        def toggle_play():
            if auto_playing.get():
                auto_playing.set(False)
                play_button.config(text="▶ Play")
            else:
                auto_playing.set(True)
                play_button.config(text="⏸ Pause")
                auto_play()
        
        play_button = tk.Button(auto_frame, text="▶ Play", command=toggle_play)
        play_button.pack(side='left', padx=5)
        
        tk.Button(auto_frame, text="⏹ Reset", command=lambda: [current_frame.set(0), update_frame(), auto_playing.set(False), play_button.config(text="▶ Play")]).pack(side='left', padx=5)
        
        # Initial frame load
        update_frame()
    
    def sort_table(self, col):
        """Sort table by column"""
        # Get all items
        items = [(self.ranking_tree.set(child, col), child) for child in self.ranking_tree.get_children('')]
        
        # Determine sort type and direction
        reverse = self.sort_reverse[col]
        
        # Sort based on column type
        if col in ['Rank', 'Total Points', 'Total Raids', 'Matches']:
            # Integer columns
            items.sort(key=lambda x: int(x[0]), reverse=reverse)
        elif col in ['Score', 'Success Rate', 'Avg Penetration', 'Avg Duration', 'Avg Points']:
            # Float columns
            items.sort(key=lambda x: float(x[0]), reverse=reverse)
        else:
            # String columns
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        # Rearrange items in sorted order
        for index, (val, child) in enumerate(items):
            self.ranking_tree.move(child, '', index)
        
        # Toggle sort direction for next click
        self.sort_reverse[col] = not reverse
        
        # Update column header to show sort direction
        direction = " ▼" if reverse else " ▲"
        for column in self.ranking_tree['columns']:
            if column == col:
                self.ranking_tree.heading(column, text=column + direction)
            else:
                self.ranking_tree.heading(column, text=column)
    
    def log_status(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = KabaddiAnalyticsApp(root)
    root.mainloop()