import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import cv2
from PIL import Image, ImageTk

def open_keyframe_viewer(parent_root):
    """Open keyframe viewer window"""
    keyframes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "keyframes")
    if not os.path.exists(keyframes_dir):
        keyframes_dir = os.path.join("data", "keyframes")
    
    if not os.path.exists(keyframes_dir):
        messagebox.showinfo("Info", "No key frames found. Please run video processing first.")
        return
    
    frame_files = [f for f in os.listdir(keyframes_dir) if f.endswith('.jpg')]
    if not frame_files:
        messagebox.showinfo("Info", "No key frames available. Please run video processing first.")
        return
    
    # Organize frames by raid and event type
    raids_data = {}
    for fname in frame_files:
        parts = fname.replace('.jpg', '').split('_')
        if len(parts) >= 4:
            raid_num = int(parts[1])
            event_type = parts[2]
            
            if raid_num not in raids_data:
                raids_data[raid_num] = {'start': None, 'baulk': None, 'bonus': None, 'end': None, 'lost': None}
            
            if event_type in raids_data[raid_num] and raids_data[raid_num][event_type] is None:
                raids_data[raid_num][event_type] = fname
    
    if not raids_data:
        messagebox.showinfo("Info", "No valid raid key frames found.")
        return
    
    # Create viewer window
    live_window = tk.Toplevel(parent_root)
    live_window.title("Raid Key Frames Viewer")
    live_window.geometry("1000x800")
    live_window.configure(bg='#2c3e50')
    
    # Title
    tk.Label(live_window, text="Raid Key Frames Viewer", 
            font=("Arial", 18, "bold"), fg='white', bg='#2c3e50').pack(pady=10)
    tk.Label(live_window, text="Navigate through raid events: Start → Baulk → Bonus → End", 
            font=("Arial", 11), fg='#ecf0f1', bg='#2c3e50').pack()
    
    # Current state
    current_raid = tk.IntVar(value=min(raids_data.keys()))
    event_sequence = ['start', 'baulk', 'bonus', 'end']
    current_event_idx = tk.IntVar(value=0)
    
    # Info frame
    info_frame = tk.Frame(live_window, bg='#34495e', relief='raised', bd=2)
    info_frame.pack(fill='x', padx=20, pady=10)
    
    raid_info = tk.StringVar()
    event_info = tk.StringVar()
    
    tk.Label(info_frame, textvariable=raid_info, font=("Arial", 14, "bold"), 
            fg='#3498db', bg='#34495e').pack(pady=5)
    tk.Label(info_frame, textvariable=event_info, font=("Arial", 12), 
            fg='#2ecc71', bg='#34495e').pack(pady=5)
    
    # Image display frame
    image_frame = tk.Frame(live_window, bg='#2c3e50')
    image_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    frame_label = tk.Label(image_frame, bg='#34495e')
    frame_label.pack(fill='both', expand=True)
    
    # Message label for "not detected"
    message_label = tk.Label(image_frame, text="", font=("Arial", 16, "bold"), 
                            fg='#e74c3c', bg='#34495e')
    
    def update_display():
        raid_num = current_raid.get()
        event_idx = current_event_idx.get()
        event_type = event_sequence[event_idx]
        
        # Update info labels
        raid_info.set(f"Raid #{raid_num} ({list(raids_data.keys()).index(raid_num) + 1}/{len(raids_data)})")
        event_info.set(f"Event: {event_type.upper()} ({event_idx + 1}/4)")
        
        # Check if this event exists for current raid
        frame_file = raids_data[raid_num].get(event_type)
        
        if frame_file:
            # Show image
            message_label.pack_forget()
            frame_label.pack(fill='both', expand=True)
            
            frame_path = os.path.join(keyframes_dir, frame_file)
            if os.path.exists(frame_path):
                img = cv2.imread(frame_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (900, 550))
                
                photo = ImageTk.PhotoImage(Image.fromarray(img))
                frame_label.configure(image=photo)
                frame_label.image = photo
        else:
            # Show "not detected" message
            frame_label.pack_forget()
            message_label.pack(fill='both', expand=True, pady=100)
            
            line_name = {
                'start': 'MIDLINE (Raid Start)',
                'baulk': 'BAULK LINE',
                'bonus': 'BONUS LINE',
                'end': 'END LINE (Return to Midline)'
            }.get(event_type, event_type.upper())
            
            message_label.config(text=f"⚠ NOT DETECTED\n\nRaider did not cross {line_name}")
    
    # Control buttons
    control_frame = tk.Frame(live_window, bg='#2c3e50')
    control_frame.pack(fill='x', padx=20, pady=15)
    
    button_frame = tk.Frame(control_frame, bg='#2c3e50')
    button_frame.pack()
    
    def next_event():
        event_idx = current_event_idx.get()
        raid_num = current_raid.get()
        
        if event_idx < len(event_sequence) - 1:
            current_event_idx.set(event_idx + 1)
        else:
            raid_keys = sorted(raids_data.keys())
            current_raid_idx = raid_keys.index(raid_num)
            
            if current_raid_idx < len(raid_keys) - 1:
                current_raid.set(raid_keys[current_raid_idx + 1])
                current_event_idx.set(0)
            else:
                messagebox.showinfo("End", "Reached end of all raids!")
                return
        
        update_display()
    
    def prev_event():
        event_idx = current_event_idx.get()
        raid_num = current_raid.get()
        
        if event_idx > 0:
            current_event_idx.set(event_idx - 1)
        else:
            raid_keys = sorted(raids_data.keys())
            current_raid_idx = raid_keys.index(raid_num)
            
            if current_raid_idx > 0:
                current_raid.set(raid_keys[current_raid_idx - 1])
                current_event_idx.set(len(event_sequence) - 1)
            else:
                messagebox.showinfo("Start", "Already at the first event!")
                return
        
        update_display()
    
    def jump_to_raid():
        raid_keys = sorted(raids_data.keys())
        raid_num = simpledialog.askinteger("Jump to Raid", 
                                          f"Enter raid number ({min(raid_keys)}-{max(raid_keys)}):",
                                          minvalue=min(raid_keys), maxvalue=max(raid_keys))
        if raid_num and raid_num in raids_data:
            current_raid.set(raid_num)
            current_event_idx.set(0)
            update_display()
    
    # Navigation buttons
    tk.Button(button_frame, text="◀ Previous", command=prev_event, 
             bg='#95a5a6', fg='white', font=("Arial", 12, "bold"), 
             padx=20, pady=10, width=12).pack(side='left', padx=10)
    
    tk.Button(button_frame, text="Next ▶", command=next_event, 
             bg='#3498db', fg='white', font=("Arial", 12, "bold"), 
             padx=20, pady=10, width=12).pack(side='left', padx=10)
    
    tk.Button(button_frame, text="Jump to Raid", command=jump_to_raid, 
             bg='#e67e22', fg='white', font=("Arial", 12, "bold"), 
             padx=20, pady=10, width=12).pack(side='left', padx=10)
    
    # Initial display
    update_display()
