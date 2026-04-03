"""Kabaddi Analytics — Central Design System"""
import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────
BG        = '#f8fafc'
CARD      = '#ffffff'
BORDER    = '#e2e8f0'
PRIMARY   = '#2563eb'
PRIMARY_H = '#1d4ed8'
SUCCESS   = '#22c55e'
SUCCESS_H = '#16a34a'
ACCENT    = '#f97316'
ACCENT_H  = '#ea6c00'
DANGER    = '#ef4444'
DANGER_H  = '#dc2626'
TEXT      = '#0f172a'
TEXT2     = '#64748b'
TEXT3     = '#94a3b8'
WHITE     = '#ffffff'
ROW_ODD   = '#f8fafc'
ROW_EVEN  = '#ffffff'
HEADER_BG = '#ffffff'
HEADER_BORDER = '#e2e8f0'

# ── Sidebar / Nav tones ────────────────────────────────────────────────────
NAV_BG      = '#0f172a'
NAV_ACTIVE  = '#2563eb'
NAV_TEXT    = '#cbd5e1'
NAV_TEXT_A  = '#ffffff'

# ── Spacing & sizing constants ─────────────────────────────────────────────
PAD_XS  = 4
PAD_SM  = 8
PAD_MD  = 14
PAD_LG  = 20
PAD_XL  = 28

# ── Typography ─────────────────────────────────────────────────────────────
F_H1    = ('Segoe UI', 22, 'bold')
F_H2    = ('Segoe UI', 13, 'bold')
F_H3    = ('Segoe UI', 11, 'bold')
F_BODY  = ('Segoe UI', 10)
F_SMALL = ('Segoe UI',  9)
F_MONO  = ('Consolas',  9)
F_STAT  = ('Segoe UI', 20, 'bold')   # large KPI value
F_LABEL = ('Segoe UI',  9)           # field labels / captions

# ── Chart colours ──────────────────────────────────────────────────────────
C_BLUE   = '#2563eb'
C_GREEN  = '#22c55e'
C_ORANGE = '#f97316'
C_RED    = '#ef4444'
C_GRID   = '#e2e8f0'
C_PURPLE = '#8b5cf6'
C_YELLOW = '#eab308'

# Ordered palette for multi-series charts
CHART_PALETTE = [C_BLUE, C_GREEN, C_ORANGE, C_RED, C_PURPLE, C_YELLOW]


# ══════════════════════════════════════════════════════════════════════════
#  THEME APPLICATION
# ══════════════════════════════════════════════════════════════════════════

def apply_theme(root):
    """Apply the full Kabaddi Analytics design system to the root window."""
    root.configure(bg=BG)
    s = ttk.Style()
    s.theme_use('clam')

    # ── Notebook / Tabs ────────────────────────────────────────────────────
    s.configure('TNotebook',
                background=BG,
                borderwidth=0,
                tabmargins=[0, 0, 0, 0])
    s.configure('TNotebook.Tab',
                background='#f1f5f9',
                foreground=TEXT2,
                font=('Segoe UI', 10, 'bold'),
                padding=[28, 11],
                borderwidth=0)
    s.map('TNotebook.Tab',
          background=[('selected', CARD),      ('active', '#e8edf4')],
          foreground=[('selected', PRIMARY),    ('active', TEXT)],
          focuscolor=[('selected', CARD)])

    # ── Frames ─────────────────────────────────────────────────────────────
    s.configure('TFrame',       background=BG)
    s.configure('Card.TFrame',  background=CARD, relief='flat')
    s.configure('Nav.TFrame',   background=NAV_BG, relief='flat')
    s.configure('Header.TFrame',background=HEADER_BG, relief='flat')

    # ── LabelFrame ─────────────────────────────────────────────────────────
    s.configure('TLabelframe',
                background=CARD,
                bordercolor=BORDER,
                relief='flat',
                padding=[PAD_MD, PAD_SM])
    s.configure('TLabelframe.Label',
                background=CARD,
                foreground=TEXT2,
                font=F_H3)

    # ── Treeview (table) ───────────────────────────────────────────────────
    s.configure('Treeview',
                background=CARD,
                foreground=TEXT,
                fieldbackground=CARD,
                font=F_BODY,
                rowheight=38,
                borderwidth=0,
                relief='flat')
    s.configure('Treeview.Heading',
                background='#f1f5f9',
                foreground=TEXT2,
                font=('Segoe UI', 9, 'bold'),
                relief='flat',
                padding=[12, 9])
    s.map('Treeview',
          background=[('selected', PRIMARY)],
          foreground=[('selected', WHITE)])
    s.map('Treeview.Heading',
          background=[('active', BORDER)],
          relief=[('active', 'flat')])

    # ── Scrollbar ──────────────────────────────────────────────────────────
    s.configure('TScrollbar',
                background=BORDER,
                troughcolor=BG,
                bordercolor=BG,
                arrowcolor=TEXT3,
                relief='flat',
                width=7)
    s.map('TScrollbar',
          background=[('active', TEXT3), ('pressed', TEXT2)])

    # ── Entry / Combobox ───────────────────────────────────────────────────
    s.configure('TEntry',
                fieldbackground=CARD,
                foreground=TEXT,
                bordercolor=BORDER,
                selectbackground=PRIMARY,
                selectforeground=WHITE,
                font=F_BODY,
                padding=[8, 6])
    s.map('TEntry',
          bordercolor=[('focus', PRIMARY)])

    s.configure('TCombobox',
                fieldbackground=CARD,
                foreground=TEXT,
                selectbackground=PRIMARY,
                selectforeground=WHITE,
                font=F_BODY,
                padding=[6, 5])
    s.map('TCombobox',
          fieldbackground=[('readonly', CARD)],
          bordercolor=[('focus', PRIMARY)])

    # ── Progressbar ────────────────────────────────────────────────────────
    s.configure('TProgressbar',
                troughcolor=BORDER,
                background=PRIMARY,
                bordercolor=BG,
                darkcolor=PRIMARY,
                lightcolor=PRIMARY,
                thickness=6)
    s.configure('Success.TProgressbar',
                troughcolor=BORDER,
                background=SUCCESS,
                darkcolor=SUCCESS,
                lightcolor=SUCCESS,
                thickness=6)
    s.configure('Accent.TProgressbar',
                troughcolor=BORDER,
                background=ACCENT,
                darkcolor=ACCENT,
                lightcolor=ACCENT,
                thickness=6)

    # ── Separator ──────────────────────────────────────────────────────────
    s.configure('TSeparator', background=BORDER)

    # ── Checkbutton / Radiobutton ──────────────────────────────────────────
    s.configure('TCheckbutton',
                background=CARD,
                foreground=TEXT,
                font=F_BODY,
                focuscolor=CARD)
    s.configure('TRadiobutton',
                background=CARD,
                foreground=TEXT,
                font=F_BODY,
                focuscolor=CARD)

    # ── Scale (slider) ─────────────────────────────────────────────────────
    s.configure('TScale',
                background=BG,
                troughcolor=BORDER,
                sliderlength=18,
                sliderrelief='flat')


# ══════════════════════════════════════════════════════════════════════════
#  LAYOUT HELPERS
# ══════════════════════════════════════════════════════════════════════════

def card(parent, padx=PAD_MD, pady=PAD_SM, **kw):
    """White card with a subtle border — the primary container unit."""
    return tk.Frame(parent, bg=CARD,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                    padx=padx, pady=pady, **kw)


def accent_card(parent, color=PRIMARY, padx=PAD_MD, pady=PAD_SM, **kw):
    """Card with a 3-px coloured left-edge accent stripe (sports feel)."""
    wrapper = tk.Frame(parent, bg=color,
                       highlightbackground=BORDER,
                       highlightthickness=1, **kw)
    inner = tk.Frame(wrapper, bg=CARD, padx=padx, pady=pady)
    inner.pack(fill='both', expand=True, padx=(3, 0))
    return wrapper, inner


def divider(parent, bg=BORDER, height=1, padx=0):
    f = tk.Frame(parent, bg=bg, height=height)
    if padx:
        f.pack(fill='x', padx=padx)
    return f


def section_title(parent, text, bg=CARD):
    return tk.Label(parent, text=text, font=F_H3, fg=TEXT, bg=bg)


def section_header(parent, text, subtitle='', bg=CARD):
    """Small in-card section heading with optional subtitle."""
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=text, font=F_H3, fg=TEXT, bg=bg).pack(anchor='w')
    if subtitle:
        tk.Label(f, text=subtitle, font=F_SMALL, fg=TEXT2, bg=bg).pack(anchor='w')
    divider(f, bg=BORDER).pack(fill='x', pady=(6, 0))
    return f


def page_header(parent, title, subtitle=''):
    """Full-width page header bar with title, subtitle, and primary accent underline."""
    bar = tk.Frame(parent, bg=HEADER_BG,
                   highlightbackground=HEADER_BORDER,
                   highlightthickness=1)
    bar.pack(fill='x', side='top')

    inner = tk.Frame(bar, bg=HEADER_BG)
    inner.pack(fill='x', padx=PAD_XL, pady=(PAD_MD, PAD_SM))

    # Title row: colour dot + text
    row = tk.Frame(inner, bg=HEADER_BG)
    row.pack(anchor='w')
    tk.Frame(row, bg=PRIMARY, width=4, height=28).pack(side='left', padx=(0, 10))
    tk.Label(row, text=title, font=F_H1, fg=TEXT, bg=HEADER_BG).pack(side='left')

    if subtitle:
        tk.Label(inner, text=subtitle,
                 font=F_BODY, fg=TEXT2,
                 bg=HEADER_BG).pack(anchor='w', pady=(2, 0))

    # Accent underline strip
    tk.Frame(bar, bg=PRIMARY, height=3).pack(fill='x')
    return bar


def scrollable_frame(parent, bg=BG):
    """Returns (outer_frame, inner_frame). Pack/grid outer_frame; place widgets in inner_frame."""
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
    vsb = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)

    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor='nw')

    def _on_configure(e):
        canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.itemconfig(win, width=canvas.winfo_width())

    inner.bind('<Configure>', _on_configure)
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
    canvas.bind_all('<MouseWheel>',
                    lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))
    return outer, inner


# ══════════════════════════════════════════════════════════════════════════
#  WIDGET FACTORIES
# ══════════════════════════════════════════════════════════════════════════

def flat_btn(parent, text, command, color=PRIMARY, hover=None, **kw):
    """Flat, coloured button with hover animation."""
    hov = hover or _darken(color)
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=WHITE, font=('Segoe UI', 10, 'bold'),
                  relief='flat', bd=0, cursor='hand2',
                  activebackground=hov, activeforeground=WHITE,
                  padx=20, pady=9, **kw)
    b.bind('<Enter>', lambda e: b.config(bg=hov))
    b.bind('<Leave>', lambda e: b.config(bg=color))
    return b


def icon_btn(parent, text, command, color=BG, fg=TEXT, hover=None, **kw):
    """Ghost-style secondary button (light background, dark text)."""
    hov = hover or BORDER
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=fg, font=F_BODY,
                  relief='flat', bd=0, cursor='hand2',
                  activebackground=hov, activeforeground=TEXT,
                  highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=7, **kw)
    b.bind('<Enter>', lambda e: b.config(bg=hov))
    b.bind('<Leave>', lambda e: b.config(bg=color))
    return b


def entry(parent, width=14, **kw):
    """Flat entry widget matching the design system."""
    return tk.Entry(parent, width=width, font=F_BODY, bg=CARD, fg=TEXT,
                    relief='flat',
                    highlightbackground=BORDER,
                    highlightcolor=PRIMARY,
                    highlightthickness=1,
                    insertbackground=TEXT, **kw)


def stat_card(parent, value, label_text, color=PRIMARY, width=None):
    """KPI stat tile: large coloured value + descriptive label + colour stripe."""
    kw = {'width': width} if width else {}
    f = card(parent, padx=PAD_LG, pady=PAD_MD, **kw)
    # Top colour stripe
    tk.Frame(f, bg=color, height=3, width=60).pack(anchor='w', pady=(0, PAD_SM))
    tk.Label(f, text=str(value),
             font=F_STAT, fg=color, bg=CARD).pack(anchor='w')
    tk.Label(f, text=label_text,
             font=F_LABEL, fg=TEXT2, bg=CARD).pack(anchor='w', pady=(2, 0))
    return f


def progress_stat_card(parent, value, label_text, pct, color=PRIMARY):
    """Stat card with an embedded progress bar below the value."""
    f = card(parent, padx=PAD_LG, pady=PAD_MD)
    tk.Frame(f, bg=color, height=3, width=60).pack(anchor='w', pady=(0, PAD_SM))
    tk.Label(f, text=str(value), font=F_STAT, fg=color, bg=CARD).pack(anchor='w')
    tk.Label(f, text=label_text, font=F_LABEL, fg=TEXT2, bg=CARD).pack(anchor='w', pady=(2, 4))
    bar_bg = tk.Frame(f, bg=BORDER, height=5)
    bar_bg.pack(fill='x')
    fill_w = max(4, int(min(pct, 100)))
    bar_fill = tk.Frame(bar_bg, bg=color, height=5)
    bar_fill.place(relwidth=fill_w / 100, relheight=1)
    return f


def badge(parent, text, color=PRIMARY):
    """Small coloured pill badge."""
    return tk.Label(parent,
                    text=f'  {text}  ',
                    font=('Segoe UI', 8, 'bold'),
                    bg=color, fg=WHITE,
                    relief='flat', padx=2, pady=2)


def status_dot(parent, color=SUCCESS, label='', bg=CARD):
    """Coloured dot + optional label (e.g. 'Live', 'Active')."""
    f = tk.Frame(parent, bg=bg)
    tk.Frame(f, bg=color, width=8, height=8).pack(side='left', padx=(0, 5), pady=4)
    if label:
        tk.Label(f, text=label, font=F_SMALL, fg=TEXT2, bg=bg).pack(side='left')
    return f


def form_row(parent, label_text, row, col=0, bg=CARD):
    """Label + entry pair on a grid layout."""
    tk.Label(parent, text=label_text,
             font=F_LABEL, fg=TEXT2, bg=bg).grid(
        row=row, column=col, sticky='w', padx=(0, PAD_SM), pady=7)
    e = entry(parent)
    e.grid(row=row, column=col + 1, sticky='ew', pady=7)
    return e


def table_toolbar(parent, bg=CARD):
    """Slim toolbar above a table (for search/filter buttons)."""
    bar = tk.Frame(parent, bg=bg, pady=PAD_SM)
    bar.pack(fill='x', padx=PAD_MD)
    return bar


# ══════════════════════════════════════════════════════════════════════════
#  CHART STYLE
# ══════════════════════════════════════════════════════════════════════════

def apply_chart_style(ax, title='', ylabel='', xlabel='', facecolor=CARD):
    """Apply the Kabaddi Analytics chart theme to a matplotlib Axes."""
    ax.set_facecolor(facecolor)

    # Spines
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.spines['left'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)

    # Ticks
    ax.tick_params(colors=TEXT2, labelsize=8, length=3, width=0.8)
    ax.tick_params(axis='x', pad=4)

    # Grid — horizontal only
    ax.yaxis.grid(True, color=C_GRID, linewidth=0.8, linestyle='--', alpha=0.7)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Labels
    if title:
        ax.set_title(title,
                     fontsize=11, fontweight='bold',
                     color=TEXT, pad=14,
                     fontfamily='Segoe UI')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=TEXT2,
                      labelpad=8, fontfamily='Segoe UI')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=TEXT2,
                      labelpad=8, fontfamily='Segoe UI')


def style_bar_chart(ax, bars, color=C_BLUE, highlight_color=C_ORANGE,
                    highlight_idx=None):
    """Apply bar styling: uniform colour with optional single-bar highlight."""
    for i, bar in enumerate(bars):
        c = highlight_color if highlight_idx is not None and i == highlight_idx else color
        bar.set_color(c)
        bar.set_edgecolor('none')
        bar.set_linewidth(0)


def figure_bg(fig, color=BG):
    """Set figure background to match the app background."""
    fig.patch.set_facecolor(color)


# ══════════════════════════════════════════════════════════════════════════
#  INTERNAL UTILITIES
# ══════════════════════════════════════════════════════════════════════════

def _darken(hex_color, amount=28):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (f'#{max(0, r - amount):02x}'
            f'{max(0, g - amount):02x}'
            f'{max(0, b - amount):02x}')


def _lighten(hex_color, amount=30):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (f'#{min(255, r + amount):02x}'
            f'{min(255, g + amount):02x}'
            f'{min(255, b + amount):02x}')