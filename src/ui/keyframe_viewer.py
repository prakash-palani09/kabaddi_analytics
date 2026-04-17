import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import os
import cv2
from PIL import Image, ImageTk

from theme import (
    apply_theme, flat_btn, divider,
    BG, CARD, BORDER, PRIMARY, SUCCESS, ACCENT, DANGER,
    TEXT, TEXT2, TEXT3, WHITE,
    F_H2, F_H3, F_BODY, F_SMALL, F_LABEL,
    PAD_SM, PAD_MD, PAD_LG, PAD_XL,
)

# ── Event badge colours ────────────────────────────────────────────────────
EVENT_COLORS = {
    'start': SUCCESS,   # green  — raid begins
    'baulk': PRIMARY,   # blue   — baulk line crossed
    'bonus': ACCENT,    # orange — bonus line crossed
    'end':   TEXT2,     # muted  — raid ends
}

EVENT_LABELS = {
    'start': 'Raid Start',
    'baulk': 'Baulk Line',
    'bonus': 'Bonus Line',
    'end':   'End / Return',
}

LINE_NAMES = {
    'start': 'MIDLINE (Raid Start)',
    'baulk': 'BAULK LINE',
    'bonus': 'BONUS LINE',
    'end':   'END LINE (Return to Midline)',
}


def open_keyframe_viewer(parent_root):
    """Open keyframe viewer window"""
    keyframes_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "keyframes")
    if not os.path.exists(keyframes_dir):
        keyframes_dir = os.path.join("data", "keyframes")

    if not os.path.exists(keyframes_dir):
        messagebox.showinfo("Info",
            "No key frames found. Please run video processing first.")
        return

    frame_files = [f for f in os.listdir(keyframes_dir) if f.endswith('.jpg')]
    if not frame_files:
        messagebox.showinfo("Info",
            "No key frames available. Please run video processing first.")
        return

    # ── Organise frames by raid + event type ──────────────────────────────
    raids_data = {}
    for fname in frame_files:
        parts = fname.replace('.jpg', '').split('_')
        if len(parts) >= 4:
            raid_num   = int(parts[1])
            event_type = parts[2]
            raids_data.setdefault(
                raid_num,
                {'start': None, 'baulk': None, 'bonus': None,
                 'end': None, 'lost': None})
            if event_type in raids_data[raid_num] \
                    and raids_data[raid_num][event_type] is None:
                raids_data[raid_num][event_type] = fname

    if not raids_data:
        messagebox.showinfo("Info", "No valid raid key frames found.")
        return

    # ═══════════════════════════════════════════════════════════════════
    #  BUILD WINDOW
    # ═══════════════════════════════════════════════════════════════════
    win = tk.Toplevel(parent_root)
    win.title("Raid Key Frames Viewer")
    win.geometry("1160x900")
    win.configure(bg=BG)

    # ── Top header bar ────────────────────────────────────────────────
    header = tk.Frame(win, bg=PRIMARY)
    header.pack(fill='x')

    header_inner = tk.Frame(header, bg=PRIMARY)
    header_inner.pack(fill='x', padx=PAD_XL, pady=PAD_MD)

    tk.Label(header_inner,
             text="Raid Key Frames Viewer",
             font=('Segoe UI', 18, 'bold'), fg=WHITE, bg=PRIMARY).pack(anchor='w')
    tk.Label(header_inner,
             text="Navigate through raid events: Start → Baulk → Bonus → End",
             font=('Segoe UI', 12), fg='#bfdbfe', bg=PRIMARY).pack(anchor='w', pady=(2, 0))

    # Primary accent underline
    tk.Frame(header, bg=SUCCESS, height=3).pack(fill='x')

    # ── State ─────────────────────────────────────────────────────────
    event_sequence    = ['start', 'baulk', 'bonus', 'end']
    current_raid      = tk.IntVar(value=min(raids_data.keys()))
    current_event_idx = tk.IntVar(value=0)

    # ── Raid selector bar ────────────────────────────────────────────
    selector_bar = tk.Frame(win, bg=CARD,
                            highlightbackground=BORDER, highlightthickness=1)
    selector_bar.pack(fill='x', padx=PAD_LG, pady=(PAD_LG, 0))

    sel_inner = tk.Frame(selector_bar, bg=CARD)
    sel_inner.pack(fill='x', padx=PAD_LG, pady=PAD_SM)

    tk.Label(sel_inner, text="Select Raid:",
             font=('Segoe UI', 11, 'bold'), fg=TEXT, bg=CARD).pack(side='left')

    raid_keys = sorted(raids_data.keys())
    raid_combo_var = tk.StringVar(value=f"Raid #{raid_keys[0]}")
    raid_combo = ttk.Combobox(
        sel_inner,
        textvariable=raid_combo_var,
        values=[f"Raid #{r}" for r in raid_keys],
        state='readonly',
        width=14,
        font=('Segoe UI', 11)
    )
    raid_combo.pack(side='left', padx=(PAD_SM, PAD_LG))

    tk.Label(sel_inner,
             text=f"{len(raids_data)} raid(s) available",
             font=('Segoe UI', 10), fg=TEXT3, bg=CARD).pack(side='left')

    # ── Info strip ───────────────────────────────────────────────────
    info_strip = tk.Frame(win, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
    info_strip.pack(fill='x', padx=PAD_LG, pady=(PAD_SM, 0))

    info_inner = tk.Frame(info_strip, bg=CARD)
    info_inner.pack(fill='x', padx=PAD_LG, pady=PAD_SM)

    # Left: raid ID pill
    raid_pill_frame = tk.Frame(info_inner, bg=CARD)
    raid_pill_frame.pack(side='left')

    raid_num_lbl = tk.Label(raid_pill_frame,
                            text="Raid #–",
                            font=('Segoe UI', 22, 'bold'),
                            fg=PRIMARY, bg=CARD)
    raid_num_lbl.pack(side='left')

    raid_counter_lbl = tk.Label(raid_pill_frame,
                                text="",
                                font=('Segoe UI', 13), fg=TEXT2, bg=CARD)
    raid_counter_lbl.pack(side='left', padx=(PAD_SM, 0))

    # Right: event badge
    event_badge = tk.Label(info_inner,
                           text="  START  ",
                           font=('Segoe UI', 11, 'bold'),
                           fg=WHITE, bg=SUCCESS,
                           relief='flat', padx=6, pady=4)
    event_badge.pack(side='right')

    event_step_lbl = tk.Label(info_inner,
                              text="Step 1 / 4",
                              font=('Segoe UI', 11), fg=TEXT2, bg=CARD)
    event_step_lbl.pack(side='right', padx=(0, PAD_MD))

    divider(win, bg=BORDER).pack(fill='x', padx=PAD_LG)

    # ── Image area ────────────────────────────────────────────────────
    img_card = tk.Frame(win, bg='#0f172a',
                        highlightbackground=BORDER, highlightthickness=1)
    img_card.pack(fill='both', expand=True,
                  padx=PAD_LG, pady=PAD_MD)

    frame_label = tk.Label(img_card, bg='#0f172a')
    frame_label.pack(fill='both', expand=True)

    # "Not detected" overlay
    not_detected_frame = tk.Frame(img_card, bg='#0f172a')
    alert_icon = tk.Label(not_detected_frame,
                          text="⚠",
                          font=('Segoe UI', 44),
                          fg=ACCENT, bg='#0f172a')
    not_det_title = tk.Label(not_detected_frame,
                             text="Not Detected",
                             font=('Segoe UI', 22, 'bold'),
                             fg=WHITE, bg='#0f172a')
    not_det_sub = tk.Label(not_detected_frame,
                           text="",
                           font=('Segoe UI', 13), fg=TEXT3, bg='#0f172a')

    # ── Event timeline strip ─────────────────────────────────────────
    timeline_card = tk.Frame(win, bg=CARD,
                             highlightbackground=BORDER, highlightthickness=1)
    timeline_card.pack(fill='x', padx=PAD_LG, pady=(0, PAD_MD))

    timeline_inner = tk.Frame(timeline_card, bg=CARD)
    timeline_inner.pack(pady=PAD_SM)

    step_labels = []
    for i, ev in enumerate(event_sequence):
        col = EVENT_COLORS[ev]

        cell = tk.Frame(timeline_inner, bg=CARD)
        cell.pack(side='left', padx=PAD_LG)

        dot = tk.Frame(cell, bg=BORDER, width=10, height=10)
        dot.pack()

        lbl = tk.Label(cell,
                       text=EVENT_LABELS[ev],
                       font=('Segoe UI', 11), fg=TEXT3, bg=CARD)
        lbl.pack()

        if i < len(event_sequence) - 1:
            tk.Label(timeline_inner,
                     text="————",
                     font=F_SMALL, fg=BORDER, bg=CARD).pack(side='left')

        step_labels.append((dot, lbl, col))

    # ── Navigation controls ───────────────────────────────────────────
    nav_card = tk.Frame(win, bg=CARD,
                        highlightbackground=BORDER, highlightthickness=1)
    nav_card.pack(fill='x', padx=PAD_LG, pady=(0, PAD_LG))

    nav_inner = tk.Frame(nav_card, bg=CARD)
    nav_inner.pack(pady=PAD_MD)

    # ── UPDATE FUNCTION ───────────────────────────────────────────────
    def update_display():
        raid_num  = current_raid.get()
        event_idx = current_event_idx.get()
        event_type = event_sequence[event_idx]

        # Info strip
        raid_num_lbl.config(text=f"Raid #{raid_num}")
        pos = list(raids_data.keys()).index(raid_num) + 1
        raid_counter_lbl.config(text=f"({pos} of {len(raids_data)})")

        ev_color = EVENT_COLORS[event_type]
        event_badge.config(
            text=f"  {EVENT_LABELS[event_type].upper()}  ",
            bg=ev_color)
        event_step_lbl.config(text=f"Step {event_idx + 1} / {len(event_sequence)}")

        # Timeline dots
        for i, (dot, lbl, col) in enumerate(step_labels):
            if i < event_idx:
                dot.config(bg=TEXT3)
                lbl.config(fg=TEXT3)
            elif i == event_idx:
                dot.config(bg=col)
                lbl.config(fg=col, font=('Segoe UI', 11, 'bold'))
            else:
                dot.config(bg=BORDER)
                lbl.config(fg=TEXT3, font=('Segoe UI', 11))

        # Image or not-detected panel
        frame_file = raids_data[raid_num].get(event_type)

        if frame_file:
            not_detected_frame.pack_forget()
            frame_label.pack(fill='both', expand=True)

            frame_path = os.path.join(keyframes_dir, frame_file)
            if os.path.exists(frame_path):
                img = cv2.imread(frame_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (1040, 580))
                photo = ImageTk.PhotoImage(Image.fromarray(img))
                frame_label.configure(image=photo)
                frame_label.image = photo
        else:
            frame_label.pack_forget()
            not_detected_frame.pack(fill='both', expand=True)
            alert_icon.pack(pady=(PAD_XL, PAD_SM))
            not_det_title.pack()
            not_det_sub.config(
                text=f"Raider did not cross  {LINE_NAMES.get(event_type, event_type.upper())}")
            not_det_sub.pack(pady=(PAD_SM, 0))

    # ── Navigation callbacks ──────────────────────────────────────────
    def next_event():
        event_idx = current_event_idx.get()
        raid_num  = current_raid.get()

        if event_idx < len(event_sequence) - 1:
            current_event_idx.set(event_idx + 1)
        else:
            raid_keys = sorted(raids_data.keys())
            idx = raid_keys.index(raid_num)
            if idx < len(raid_keys) - 1:
                new_raid = raid_keys[idx + 1]
                current_raid.set(new_raid)
                current_event_idx.set(0)
                raid_combo_var.set(f"Raid #{new_raid}")
            else:
                messagebox.showinfo("End", "Reached the end of all raids!")
                return
        update_display()

    def prev_event():
        event_idx = current_event_idx.get()
        raid_num  = current_raid.get()

        if event_idx > 0:
            current_event_idx.set(event_idx - 1)
        else:
            raid_keys = sorted(raids_data.keys())
            idx = raid_keys.index(raid_num)
            if idx > 0:
                new_raid = raid_keys[idx - 1]
                current_raid.set(new_raid)
                current_event_idx.set(len(event_sequence) - 1)
                raid_combo_var.set(f"Raid #{new_raid}")
            else:
                messagebox.showinfo("Start", "Already at the first event!")
                return
        update_display()

    def on_raid_selected(event=None):
        val = raid_combo_var.get()  # e.g. "Raid #3"
        raid_num = int(val.split('#')[1])
        current_raid.set(raid_num)
        current_event_idx.set(0)
        update_display()

    raid_combo.bind('<<ComboboxSelected>>', on_raid_selected)

    def jump_to_raid():
        raid_keys = sorted(raids_data.keys())
        raid_num  = simpledialog.askinteger(
            "Jump to Raid",
            f"Enter raid number ({min(raid_keys)}–{max(raid_keys)}):",
            minvalue=min(raid_keys), maxvalue=max(raid_keys))
        if raid_num and raid_num in raids_data:
            current_raid.set(raid_num)
            current_event_idx.set(0)
            raid_combo_var.set(f"Raid #{raid_num}")
            update_display()

    # ── Nav buttons ───────────────────────────────────────────────────
    flat_btn(nav_inner, "◀  Previous",
             command=prev_event,
             color='#475569').pack(side='left', padx=PAD_SM)

    flat_btn(nav_inner, "Next  ▶",
             command=next_event,
             color=PRIMARY).pack(side='left', padx=PAD_SM)

    flat_btn(nav_inner, "Jump to Raid",
             command=jump_to_raid,
             color=ACCENT).pack(side='left', padx=PAD_SM)

    # Keyboard shortcuts
    win.bind('<Right>', lambda e: next_event())
    win.bind('<Left>',  lambda e: prev_event())

    # Shortcut hint
    tk.Label(nav_inner,
             text="  ← → arrow keys to navigate",
             font=('Segoe UI', 11), fg=TEXT3, bg=CARD).pack(side='right', padx=PAD_MD)

    # ── Initial display ───────────────────────────────────────────────
    update_display()