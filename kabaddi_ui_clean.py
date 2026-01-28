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
        """Load synthetic data and calculate rankings"""
        try:
            self.data = []
            with open('synthetic_data.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'match_id': row['match_id'],
                        'player_id': row['player_id'],
                        'raid_duration_sec': float(row['raid_duration_sec']),
                        'penetration_px': float(row['penetration_px']),
                        'success': int(row['success']),
                        'raid_points': int(row.get('raid_points', 0))  # Handle missing points
                    })
            self.update_rankings()
        except FileNotFoundError:
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
                    
                    self.data.append({
                        'match_id': match,
                        'player_id': player,
                        'raid_duration_sec': duration,
                        'penetration_px': penetration,
                        'success': success
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
                    self.data.append({
                        'match_id': match,
                        'player_id': player,
                        'raid_duration_sec': round(random.uniform(2.0, 8.0), 1),
                        'penetration_px': random.randint(100, 250),
                        'success': random.choice([0, 1])
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
        with open('synthetic_data.csv', 'w', newline='') as f:
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
        columns = ('Rank', 'Player', 'Score', 'Recent SR', 'Recent Pen', 'Recent Dur', 'Recent Pts', 'Recent Raids', 'All Raids', 'All SR', 'All Pts', 'Matches')
        self.ranking_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Store sort direction for each column
        self.sort_reverse = {col: False for col in columns}
        
        # Adjust column widths and add sorting
        for col in columns:
            self.ranking_tree.heading(col, text=col, command=lambda c=col: self.sort_table(c))
            if col in ['Recent SR', 'Recent Pen', 'Recent Dur', 'Recent Pts', 'All SR', 'All Pts']:
                self.ranking_tree.column(col, width=80)
            else:
                self.ranking_tree.column(col, width=70)
        
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
            
    def setup_midline(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
            
        self.log_status("Setting up midline...")
        threading.Thread(target=self.run_setup_midline, daemon=True).start()
        
    def run_setup_midline(self):
        try:
            self.log_status("=== MIDLINE SETUP PROCESS ===")
            self.log_status("Step 1/3: Copying video to processing directory...")
            
            # Copy video to expected location
            target_path = "data/videos/current_video.mp4"
            os.makedirs("data/videos", exist_ok=True)
            shutil.copy2(self.video_path, target_path)
            self.log_status("Video copied successfully")
            
            self.log_status("Step 2/3: Loading video for midline selection...")
            
            # Run setup directly in this process
            import cv2
            from court.midline_manager import save_midline
            
            DISPLAY_SCALE = 0.6
            midline_points = []
            
            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN and len(midline_points) < 2:
                    midline_points.append((int(x / DISPLAY_SCALE), int(y / DISPLAY_SCALE)))
                    self.log_status(f"Midline point {len(midline_points)} selected: {midline_points[-1]}")
            
            cap = cv2.VideoCapture(target_path)
            ret, first_frame = cap.read()
            
            if not ret:
                self.log_status("Error: Cannot read video file")
                return
            
            self.log_status("Video loaded successfully")
            self.log_status("Step 3/3: Interactive midline selection...")
            self.log_status(">>> INSTRUCTION: Click 2 points on the court midline, then press ENTER <<<")
            
            cv2.namedWindow("Setup Midline", cv2.WINDOW_NORMAL)
            cv2.setMouseCallback("Setup Midline", mouse_callback)
            
            while True:
                temp = first_frame.copy()
                for p in midline_points:
                    cv2.circle(temp, p, 6, (0,255,255), -1)
                
                if len(midline_points) == 2:
                    cv2.line(temp, midline_points[0], midline_points[1], (0,255,255), 2)
                    cv2.putText(temp, "Press ENTER to save", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                else:
                    cv2.putText(temp, f"Click point {len(midline_points)+1}/2", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                
                display = cv2.resize(temp, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
                cv2.imshow("Setup Midline", display)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 13 and len(midline_points) == 2:
                    self.log_status("Midline points confirmed")
                    break
                elif key == 27:
                    self.log_status("Setup cancelled by user")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
            
            cap.release()
            cv2.destroyAllWindows()
            
            p1, p2 = midline_points
            save_midline(target_path, p1, p2)
            self.log_status(f"Midline coordinates saved: {p1} to {p2}")
            self.log_status("=== MIDLINE SETUP COMPLETED SUCCESSFULLY ===")
                
        except Exception as e:
            self.log_status(f"Error in midline setup: {str(e)}")
            
    def process_video(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
            
        self.log_status("Processing video for raid analysis...")
        threading.Thread(target=self.run_video_processing, daemon=True).start()
        
    def run_video_processing(self):
        try:
            self.log_status("=== VIDEO PROCESSING PIPELINE ===")
            self.log_status("Step 1/6: Initializing AI models...")
            
            # Run processing directly in this process
            import cv2
            import numpy as np
            from ultralytics import YOLO
            from court.midline_manager import load_midline, has_midline
            
            VIDEO_PATH = "data/videos/current_video.mp4"
            MODEL_PATH = "yolov8n.pt"
            
            self.log_status("Step 2/6: Loading saved midline configuration...")
            
            if not has_midline(VIDEO_PATH):
                self.log_status("No saved midline found! Please run Setup Midline first.")
                return
            
            midline_data = load_midline(VIDEO_PATH)
            p1, p2 = midline_data["p1"], midline_data["p2"]
            self.log_status(f"Midline loaded: {p1} to {p2}")
            
            self.log_status("Step 3/6: Loading YOLO model for player detection...")
            cap = cv2.VideoCapture(VIDEO_PATH)
            model = YOLO(MODEL_PATH)
            frame_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.log_status(f"Video loaded: {total_frames} frames to process")
            
            self.log_status("Step 4/6: Initializing tracking algorithms...")
            
            def point_side(p1, p2, x, y):
                return np.sign((p2[0] - p1[0]) * (y - p1[1]) - (p2[1] - p1[1]) * (x - p1[0]))
            
            player_baseline_side = {}
            baseline_counter = {}
            raider_track_id = None
            raider_start_side = None
            raid_active = False
            raid_count = 0
            
            # Create output directory
            os.makedirs("sample_output_frame", exist_ok=True)
            
            self.log_status("Step 5/6: Processing video frames...")
            self.log_status(">>> Detecting players, tracking movements, identifying raids <<<")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                progress = (frame_count / total_frames) * 100
                
                # Draw midline
                cv2.line(frame, p1, p2, (0,255,255), 2)
                
                # Run AI detection and tracking
                results = model.track(frame, persist=True, conf=0.4, classes=[0], tracker="bytetrack.yaml")
                
                if results and results[0].boxes.id is not None:
                    for box in results[0].boxes:
                        x1,y1,x2,y2 = map(int, box.xyxy[0])
                        tid = int(box.id[0])
                        cx = (x1 + x2)//2
                        cy = (y1 + y2)//2
                        side = point_side(p1, p2, cx, cy)
                        
                        # Draw player detection
                        cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),1)
                        cv2.putText(frame,f"ID {tid}",(x1,y1-5), cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
                        
                        # Track player baseline
                        if tid not in player_baseline_side:
                            player_baseline_side[tid] = side
                            baseline_counter[tid] = 1
                        else:
                            if side == player_baseline_side[tid]:
                                baseline_counter[tid] += 1
                        
                        # Detect raid start
                        if (not raid_active and baseline_counter.get(tid, 0) >= 5 and side != player_baseline_side[tid]):
                            raider_track_id = tid
                            raider_start_side = player_baseline_side[tid]
                            raid_active = True
                            raid_count += 1
                            self.log_status(f"RAID {raid_count} DETECTED | Raider ID: {tid} | Frame: {frame_count}")
                        
                        # Track active raider
                        if raid_active and tid == raider_track_id:
                            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),3)
                            cv2.putText(frame,"RAIDER",(x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                            
                            # Detect raid end
                            if side == raider_start_side:
                                self.log_status(f"RAID {raid_count} ENDED | Frame: {frame_count}")
                                raid_active = False
                                raider_track_id = None
                                raider_start_side = None
                                player_baseline_side.clear()
                                baseline_counter.clear()
                
                # Save progress frames
                if frame_count % 30 == 0:
                    cv2.imwrite(f"sample_output_frame/progress_frame_{frame_count}.jpg", frame)
                    self.log_status(f"Progress: {progress:.1f}% | Frame {frame_count}/{total_frames} | Raids detected: {raid_count}")
            
            cap.release()
            self.log_status("Step 6/6: Finalizing results...")
            self.log_status(f"Processing complete! Total raids detected: {raid_count}")
            self.log_status(f"Output frames saved: Check sample_output_frame/ directory")
            self.log_status("=== VIDEO PROCESSING COMPLETED SUCCESSFULLY ===")
                
        except Exception as e:
            self.log_status(f"Error in video processing: {str(e)}")
            
    def run_full_pipeline(self):
        if not hasattr(self, 'video_path'):
            messagebox.showerror("Error", "Please select a video file first!")
            return
            
        self.log_status("=== FULL PIPELINE EXECUTION ===")
        self.log_status("This will run: Setup Midline → Process Video automatically")
        self.log_status("Phase 1: Setting up midline configuration...")
        threading.Thread(target=self.full_pipeline_thread, daemon=True).start()
        
    def full_pipeline_thread(self):
        # Phase 1: Setup
        self.run_setup_midline()
        
        # Check if setup was successful
        if "SETUP COMPLETED SUCCESSFULLY" in self.status_text.get("1.0", tk.END):
            self.log_status("Phase 2: Starting video processing...")
            self.run_video_processing()
            
            if "PROCESSING COMPLETED SUCCESSFULLY" in self.status_text.get("1.0", tk.END):
                self.log_status("=== FULL PIPELINE COMPLETED SUCCESSFULLY ===")
                self.log_status("Midline configured and saved")
                self.log_status("Video processed and raids detected")
                self.log_status("Output frames generated")
            else:
                self.log_status("Pipeline failed at video processing stage")
        else:
            self.log_status("Pipeline failed at midline setup stage")
            
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
            
            self.ranking_tree.insert('', 'end', values=(
                rank_data['rank'],
                player_id,
                f"{rank_data['score']:.3f}",
                f"{profile['success_rate']:.2f}",  # Recent (scoring)
                f"{profile['avg_penetration']:.0f}",
                f"{profile['avg_duration']:.1f}",
                f"{profile.get('avg_points', 0):.2f}",
                profile['raids'],  # Recent raids count
                profile.get('all_raids', profile['raids']),  # All-time raids
                f"{profile.get('all_success_rate', profile['success_rate']):.2f}",  # All-time SR
                f"{profile.get('all_avg_points', profile.get('avg_points', 0)):.2f}",  # All-time points
                len(player_matches)
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
        
        # Chart 2: Success Rates
        success_rates = [self.player_stats[p]['success_rate'] for p in players]
        self.ax2.bar(players, success_rates, color='#2ecc71')
        self.ax2.set_title('Success Rates')
        self.ax2.set_ylabel('Success Rate')
        
        # Chart 3: Average Penetration
        penetrations = [self.player_stats[p]['avg_penetration'] for p in players]
        self.ax3.bar(players, penetrations, color='#e74c3c')
        self.ax3.set_title('Average Penetration')
        self.ax3.set_ylabel('Penetration (px)')
        
        # Chart 4: Average Duration
        durations = [self.player_stats[p]['avg_duration'] for p in players]
        self.ax4.bar(players, durations, color='#f39c12')
        self.ax4.set_title('Average Duration')
        self.ax4.set_ylabel('Duration (sec)')
        
        plt.tight_layout()
        self.canvas.draw()
        
    def view_live_process(self):
        """Open a window to view live processing frames"""
        if not os.path.exists("sample_output_frame"):
            messagebox.showinfo("Info", "No processing frames found. Please run video processing first.")
            return
            
        # Create new window for live view
        live_window = tk.Toplevel(self.root)
        live_window.title("Live Process Viewer")
        live_window.geometry("800x600")
        
        # Frame display
        frame_label = tk.Label(live_window)
        frame_label.pack(pady=10)
        
        # Controls
        control_frame = tk.Frame(live_window)
        control_frame.pack(pady=10)
        
        # Get available frames
        frame_files = [f for f in os.listdir("sample_output_frame") if f.endswith('.jpg')]
        frame_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        
        if not frame_files:
            tk.Label(live_window, text="No frames available", font=("Arial", 14)).pack(pady=50)
            return
            
        current_frame = tk.IntVar(value=0)
        
        def update_frame():
            if frame_files:
                frame_path = os.path.join("sample_output_frame", frame_files[current_frame.get()])
                if os.path.exists(frame_path):
                    import cv2
                    from PIL import Image, ImageTk
                    
                    img = cv2.imread(frame_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (640, 480))
                    
                    photo = ImageTk.PhotoImage(Image.fromarray(img))
                    frame_label.configure(image=photo)
                    frame_label.image = photo
                    
                    frame_info.set(f"Frame: {frame_files[current_frame.get()]} ({current_frame.get()+1}/{len(frame_files)})")
        
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
        if col in ['Rank', 'Recent Raids', 'All Raids', 'Matches']:
            # Integer columns
            items.sort(key=lambda x: int(x[0]), reverse=reverse)
        elif col in ['Score', 'Recent SR', 'Recent Pen', 'Recent Dur', 'Recent Pts', 'All SR', 'All Pts']:
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