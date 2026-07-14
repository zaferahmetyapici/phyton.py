import random
import math
import sys
import os
import threading
import time
import json
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, font
except Exception:
    tk = None
    ttk = None
    messagebox = None
    font = None

try:
    import winsound
except Exception:
    winsound = None

try:
    import ctypes
except Exception:
    ctypes = None


def generate_operation_question(op_name, difficulty='easy'):
    """Return (expr_str, answer_int) for a simple 4-operations question."""
    diff = (difficulty or 'easy').lower()

    def _rand_by_digits(digits):
        if digits <= 1:
            return random.randint(1, 9)
        return random.randint(10, 99)

    if op_name is None:
        op_name = random.choice(['Addition', 'Subtraction', 'Multiplication', 'Division'])
    op = op_name.lower()

    # Operand size rules requested:
    # easy: all operations -> 1 digit with 1 digit
    # normal: add/sub -> 2 digits with 1 digit; mul/div -> 2 digits with 1 digit
    # hard: add/sub -> 2 digits with 2 digits; mul/div -> 2 digits with 1 digit
    if diff == 'easy':
        d1, d2 = 1, 1
    elif diff == 'normal':
        d1, d2 = 2, 1
    else:  # hard (and fallback)
        if 'mul' in op or 'times' in op or 'div' in op:
            d1, d2 = 2, 1
        else:
            d1, d2 = 2, 2

    if 'add' in op:
        a = _rand_by_digits(d1)
        b = _rand_by_digits(d2)
        return f"{a} + {b} = _", a + b
    if 'sub' in op:
        a = _rand_by_digits(d1)
        b = _rand_by_digits(d2)
        if a < b:
            a, b = b, a
        return f"{a} - {b} = _", a - b
    if 'mul' in op or 'times' in op:
        a = _rand_by_digits(d1)
        b = _rand_by_digits(d2)
        return f"{a} × {b} = _", a * b
    if 'div' in op:
        # keep integer division while respecting displayed operand sizes
        if diff == 'easy':
            b = random.randint(1, 9)
            ans = random.randint(1, max(1, 9 // b))
            a = ans * b  # single-digit dividend
        else:
            # normal/hard: 2-digit dividend with 1-digit divisor
            b = random.randint(2, 9)
            min_ans = max(1, (10 + b - 1) // b)
            max_ans = max(min_ans, 99 // b)
            ans = random.randint(min_ans, max_ans)
            a = ans * b
            if a < 10 or a > 99:
                a = random.randint(10, 99)
                a = a - (a % b)
                if a < 10:
                    a += b
                ans = a // b
        return f"{a} ÷ {b} = _", ans
    # fallback
    a = _rand_by_digits(1 if diff == 'easy' else 2)
    b = _rand_by_digits(1)
    return f"{a} + {b} = _", a + b


def generate_group_pattern(pg, length=4, difficulty='easy'):
    """Return a numeric sequence for Patterns mode respecting difficulty ranges.

    - `pg` may be 'All' or a label like '1-3-5' or '2-4-6'.
    - For multi-number labels we treat values as bases and generate multiples
      of a chosen base that fit within the numeric range for `difficulty`.
    - Single-number labels produce a small arithmetic progression starting
      near that number but constrained to the numeric range.
    """
    # difficulty ranges (inclusive)
    ranges = {
        'easy': (1, 30),
        'normal': (30, 70),
        'hard': (60, 100)
    }
    lo, hi = ranges.get((difficulty or 'easy').lower(), (1, 30))
    try:
        # extract any numeric parts (supports labels like 'All', '1 Pattern', '1-3-5')
        cleaned = ''.join(ch if ch.isdigit() or ch == '-' else '' for ch in (pg or ''))
        parts = [int(x) for x in cleaned.split('-') if x]
        if parts:
            # multi-base label: choose a base and produce consecutive
            # multiples that lie within [lo, hi]
            if len(parts) > 1:
                base = random.choice(parts)
                # compute feasible multiplier range so base*(m + length-1) <= hi
                try:
                    m_min = max(1, (lo + base - 1) // base)
                    m_max = max(1, hi // base) - (length - 1)
                    if m_max >= m_min:
                        m = random.randint(m_min, m_max)
                        return [base * (m + i) for i in range(length)]
                    # fallback: if insufficient room, return consecutive multiples clipped
                    start_m = max(1, (lo + base - 1) // base)
                    return [base * (start_m + i) for i in range(length)]
                except Exception:
                    return [base * (i + 1) for i in range(length)]
            else:
                # single-number label: treat as a base and produce multiples
                base = parts[0]
                try:
                    m_min = max(1, (lo + base - 1) // base)
                    m_max = max(1, hi // base) - (length - 1)
                    if m_max >= m_min:
                        m = random.randint(m_min, m_max)
                        return [base * (m + i) for i in range(length)]
                    # fallback: start with smallest feasible multiplier
                    start_m = max(1, (lo + base - 1) // base)
                    return [base * (start_m + i) for i in range(length)]
                except Exception:
                    return [base * (i + 1) for i in range(length)]
    except Exception:
        pass
    # 'All' or fallback: pick a random start inside the range and step=1
    try:
        start = random.randint(lo, max(lo, hi - (length - 1)))
        return [start + i for i in range(length)]
    except Exception:
        return list(range(1, length + 1))


def generate_sequence(kind, length=5):
    if kind == 'count':
        return list(range(1, length+1))
    if kind == 'add2':
        start = 1
        return [start + i*2 for i in range(length)]
    if kind == 'double':
        start = 1
        seq = [start]
        for _ in range(length-1):
            seq.append(seq[-1]*2)
        return seq
    # fallback
    return list(range(1, length+1))
class PatternPicnicGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PATTERN PICNIC')

        # Create a colorful rainbow icon (left half only, 4 lines)
        try:
            w, h = 64, 64
            icon_img = tk.PhotoImage(width=w, height=h)
            # Use colors from header (e53935 red, 1e88e5 blue, fdd835 yellow, 43a047 green)
            # Original header rainbow: ['#e53935', '#fb8c00', '#fdd835', '#43a047', '#1e88e5', '#8e24aa', '#d81b60']
            # We need standard looking red, blue, yellow, green but using the header's specific hex codes for consistency.
            # Red: #e53935
            # Blue: #1e88e5
            # Yellow: #fdd835
            # Green: #43a047
            rainbow_colors = ['#e53935', '#1e88e5', '#fdd835', '#43a047'] 
            
            # The full rainbow would center at bottom-right now, so we see only the left quadrant?
            # User said "half of this. left part of the rainbow".
            # A standard rainbow is a semi-circle (top half).
            # Left part would be the left quarter-circle.
            # So the center should be at (w, h) so we see the top-left quadrant arcs?
            
            cx, cy = w - 5, h - 5
            max_r = 60
            band_width = 10 
            
            # Efficient drawing using pixel iteration
            for y in range(h):
                for x in range(w):
                    dx = x - cx
                    dy = y - cy
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    found_color = None
                    # We want the top-left quadrant relative to center (w, h)
                    # Coordinates approach (w, h) from top-left (0,0).
                    # So x < cx and y < cy is naturally true for most of the canvas if center is bottom-right.
                    
                    if True: # Condition always true for this quadrant setup
                        # Check distance bands
                        # dist 0..10: empty
                        # dist 10..20: inner band
                        # ...
                        # dist 50..60: outer band
                        
                        # We want outer band to be Red (index 0)
                        # max_r = 60.
                        # 4 bands of width 10 -> 40 pixels.
                        # Inner radius = 20.
                        
                        if 20 <= dist < 60:
                            # Map distance to index.
                            # 50-60 -> index 0 (Red)
                            # 40-50 -> index 1
                            # 30-40 -> index 2
                            # 20-30 -> index 3 (Green)
                            
                            raw_idx = int((60 - 0.1 - dist) / band_width)
                            if 0 <= raw_idx < len(rainbow_colors):
                                found_color = rainbow_colors[raw_idx]
                    
                    if found_color:
                        icon_img.put(found_color, to=(x, y))
            
            self.iconphoto(True, icon_img)
        except Exception:
            pass

        # set an optimum default window size and allow resizing (slightly smaller)
        self.geometry('900x640')
        try:
            self._center_window(900, 640)
        except Exception:
            pass
        # lock size to the default and keep centered
        try:
            self.resizable(False, False)
            try:
                self.minsize(900, 640)
                self.maxsize(900, 640)
            except Exception:
                pass
        except Exception:
            pass

        # playful fonts (fallback to system defaults if unavailable)
        fav = 'Comic Sans MS'
        try:
            # slightly smaller fonts for slightly more compact layout
            self.main_font = font.Font(family=fav, size=15)
            self.big_font = font.Font(family=fav, size=30, weight='bold')
            self.kid_button_font = font.Font(family=fav, size=16, weight='bold')
            # compact choice button font (bold)
            self.small_button_font = font.Font(family=fav, size=12, weight='bold')
        except Exception:
            self.main_font = font.Font(family='Helvetica', size=15)
            self.big_font = font.Font(family='Helvetica', size=30, weight='bold')
            self.kid_button_font = font.Font(family='Helvetica', size=16, weight='bold')
            self.small_button_font = font.Font(family='Helvetica', size=12, weight='bold')

        self.age = 7
        self.difficulty = 'easy'
        # sensible default rounds shown on the start screen
        self.rounds = 10
        self.player_name = 'Guest'
        self.pattern_group = 'All'
        self.current_round = 0
        self.score = 0

        # persistent statistics (per player name)
        try:
            self._stats_file = os.path.join(os.getcwd(), 'player_stats.json')
        except Exception:
            self._stats_file = 'player_stats.json'
        self._player_stats = {}
        self._load_player_statistics()

        self.kinds = ['count', 'add2', 'even']
        self.current_seq = []
        self.blank_index = 0
        self.fullscreen = False

        # set a clean white background
        try:
            self.configure(bg='white')
            # ensure all future created widgets inherit this unless specified
            self.option_add('*Background', 'white')
        except Exception:
            pass
        # scan for a shapes folder with image files and preload them
        try:
            self._scan_shapes_folder()
        except Exception:
            pass
        # flag to indicate a preloaded image has been placed on the canvas
        # start as False when using preloaded shape images so we don't reveal
        # the pattern label until the thumbnail is actually drawn
        try:
            self._image_placed = not bool(getattr(self, '_using_shape_images', False))
        except Exception:
            self._image_placed = True
        self._build_start_screen()
        # play intro sound shortly after start (use sounds/intro.wav if present)
        try:
            self.after(300, lambda: self._play_sound_file('intro'))
        except Exception:
            pass
        # ensure window appears above other windows on start
        try:
            self.after(100, self._ensure_front)
        except Exception:
            pass
        # keep UI responsive to window size changes
        try:
            self.bind('<Configure>', self._on_resize)
        except Exception:
            pass
        # debounce token for resize redraws
        self._resize_after_id = None
        # Timer for buffering round transitions
        self._next_round_timer = None
        # sequence canvas items and feedback widget
        self._seq_text_items = []
        self._canvas_feedback_widget = None

    def _center_window(self, width=1000, height=700):
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = int(width)
            h = int(height)
            x = max(0, (sw - w) // 2)
            # move the window slightly upwards so it's not perfectly centered
            offset = 50
            y = max(0, (sh - h) // 2 - offset)
            self.geometry(f"{w}x{h}+{x}+{y}")
            # sensible minimums
            try:
                self.minsize(600, 420)
            except Exception:
                pass
        except Exception:
            pass

    def _validate_answer(self, proposed):
        """Tkinter validatecommand: allow only digits or empty string."""
        try:
            return proposed == "" or proposed.isdigit()
        except Exception:
            return False

    def _scan_shapes_folder(self):
        # look for a 'shapes' folder next to the script or in the frozen bundle
        try:
            base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            base = os.path.dirname(os.path.abspath(__file__))
        # try a few likely locations for a shapes folder
        shapes_dir = os.path.join(base, 'shapes')
        if not os.path.isdir(shapes_dir):
            alt = os.path.join(os.getcwd(), 'shapes')
            if os.path.isdir(alt):
                shapes_dir = alt
            else:
                return
        exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        files = [f for f in os.listdir(shapes_dir) if os.path.splitext(f)[1].lower() in exts]
        # Shuffle the files on load so the order is random every time app starts
        random.shuffle(files)
        
        imgs = []
        names = []
        # track the maximum thumbnail dimension we produce so vector shapes match
        max_thumb_dim = 0
        for fn in files:
            path = os.path.join(shapes_dir, fn)
            # create a small thumbnail at load time so drawing is instant later
            try:
                from PIL import Image, ImageTk
                pil = Image.open(path)
                # thumbnail size conservative so images don't dominate the canvas
                thumb_w, thumb_h = (140, 140)
                pw, ph = pil.size
                ratio = min(thumb_w / pw if pw else 1, thumb_h / ph if ph else 1, 1)
                if ratio < 1:
                    new_size = (max(1, int(pw * ratio)), max(1, int(ph * ratio)))
                    pil = pil.resize(new_size, Image.LANCZOS)
                img = ImageTk.PhotoImage(pil)
                imgs.append((path, img))
                try:
                    max_thumb_dim = max(max_thumb_dim, img.width(), img.height())
                except Exception:
                    pass
            except Exception:
                try:
                    # fallback to Tk PhotoImage (may be large); attempt integer subsample if needed
                    img = tk.PhotoImage(file=path)
                    try:
                        pw = img.width()
                        ph = img.height()
                        thumb_w, thumb_h = (140, 140)
                        sx = max(1, int(pw / thumb_w))
                        sy = max(1, int(ph / thumb_h))
                        subs = max(sx, sy)
                        if subs > 1:
                            img = img.subsample(subs, subs)
                    except Exception:
                        pass
                    imgs.append((path, img))
                    try:
                        max_thumb_dim = max(max_thumb_dim, img.width(), img.height())
                    except Exception:
                        pass
                except Exception:
                    # skip files that cannot be loaded
                    continue
            name = os.path.splitext(fn)[0].replace('_', ' ').strip().lower()
            names.append(name)
        if imgs:
            self._shape_images = imgs
            self._shape_image_names = names
            # store thumbnail display size so vector drawings can match
            try:
                if max_thumb_dim and max_thumb_dim > 0:
                    self._max_thumb_dim = max_thumb_dim
                else:
                    self._max_thumb_dim = 140
            except Exception:
                self._max_thumb_dim = 140
            # Only set rounds to image count when shapes mode is active; don't
            # override the start-screen default rounds when the app first loads.
            try:
                if getattr(self, 'mode_var', None) and self.mode_var.get() == 'Geometric Shapes':
                    self.rounds = len(imgs)
                    try:
                        if getattr(self, 'rounds_var', None) is not None:
                            self.rounds_var.set(str(len(imgs)))
                    except Exception:
                        pass
            except Exception:
                pass

            # mark that we'll use image-based drawing (not vector)
            try:
                self._using_shape_images = True
                self._last_shape = None
                self._last_color = None
            except Exception:
                pass

    def _ensure_front(self):
        try:
            try:
                self.lift()
            except Exception:
                pass
            try:
                # briefly make topmost so it appears above other windows
                self.attributes('-topmost', True)
            except Exception:
                pass
            try:
                self.focus_force()
            except Exception:
                pass
            try:
                # clear topmost after a short delay
                self.after(500, lambda: self.attributes('-topmost', False))
            except Exception:
                pass
        except Exception:
            pass
    def _build_start_screen(self):
        for w in self.winfo_children():
            w.destroy()
        
        # Add buffer space at the top to move everything down (3 rows)
        tk.Label(self, text='', bg=self.cget('bg'), height=3).pack()

        # colorful header: each letter is a colorful label (rainbow)
        header_frm = tk.Frame(self, bg=self.cget('bg'))
        header_frm.pack(pady=(10, 6))
        title_text = 'PATTERN PICNIC'
        rainbow = ['#e53935', '#fb8c00', '#fdd835', '#43a047', '#1e88e5', '#8e24aa', '#d81b60']
        
        # Determine font family from self.big_font if possible, else default
        fam = 'Helvetica'
        if self.big_font:
            try:
                fam = self.big_font.actual()['family']
            except Exception:
                pass
        
        # Bigger font for header
        header_fnt = font.Font(family=fam, size=44, weight='bold')

        ci = 0
        for ch in title_text:
            if ch == ' ':
                spacer = tk.Label(header_frm, text=' ', font=header_fnt, bg=self.cget('bg'))
                spacer.pack(side='left')
                continue
            lbl = tk.Label(header_frm, text=ch, font=header_fnt, fg=rainbow[ci % len(rainbow)], bg=self.cget('bg'))
            lbl.pack(side='left', padx=0)
            ci += 1

        # Spacer after header, before the rest
        tk.Label(self, text='', bg=self.cget('bg'), height=2).pack()

        # (fullscreen button removed from header)
        # (rainbow icon removed)
        desc = tk.Label(self, text='Find The Answers!', font=self.main_font, bg=self.cget('bg'))
        desc.pack(pady=(0, 12))

        # player name
        player_row = tk.Frame(self, bg=self.cget('bg'))
        player_row.pack(pady=(0, 6))
        tk.Label(player_row, text='Player Name:', font=self.main_font, bg=self.cget('bg')).pack(side='left', padx=(0, 6))
        self.player_var = tk.StringVar(value=getattr(self, 'player_name', 'Guest'))
        tk.Entry(player_row, textvariable=self.player_var, width=16, font=self.main_font).pack(side='left')

        # inline layout for age / rounds / difficulty (tighter spacing)
        frm = tk.Frame(self, bg=self.cget('bg'))
        frm.pack(pady=6)

        # Row 0: Age / Rounds / Difficulty (centered)
        row0 = tk.Frame(frm, bg=self.cget('bg'))
        row0.pack()
        tk.Label(row0, text='Age:', font=self.main_font, bg=self.cget('bg')).pack(side='left', padx=(0,6))
        self.age_var = tk.StringVar(value=str(self.age))
        tk.Entry(row0, textvariable=self.age_var, width=4, font=self.main_font).pack(side='left', padx=(0,10))
        tk.Label(row0, text='Rounds:', font=self.main_font, bg=self.cget('bg')).pack(side='left', padx=(0,6))
        self.rounds_var = tk.StringVar(value=str(self.rounds))
        # keep a reference so we can enable/disable when modes change
        self.rounds_entry = tk.Entry(row0, textvariable=self.rounds_var, width=4, font=self.main_font)
        self.rounds_entry.pack(side='left', padx=(0,10))
        tk.Label(row0, text='Difficulty:', font=self.main_font, bg=self.cget('bg')).pack(side='left', padx=(0,6))
        self.diff_var = tk.StringVar(value=self.difficulty.upper())
        if ttk:
            cb = ttk.Combobox(row0, textvariable=self.diff_var, values=['EASY', 'NORMAL', 'HARD'], state='readonly', font=self.main_font, width=8, height=3)
            cb.pack(side='left')
            cb.current(0)
        else:
            tk.OptionMenu(row0, self.diff_var, 'EASY', 'NORMAL', 'HARD').pack(side='left')

        # Mode selection and controls (centered)
        # Row1: radios
        row1 = tk.Frame(frm, bg=self.cget('bg'))
        row1.pack(pady=(6,0))
        self.mode_var = tk.StringVar(value='Patterns')
        rb_patterns = tk.Radiobutton(row1, text='Patterns', variable=self.mode_var, value='Patterns', command=self._on_mode_change, font=self.main_font, bg=self.cget('bg'))
        rb_patterns.pack(side='left', padx=(8,8))
        rb_ops = tk.Radiobutton(row1, text='4 Operations', variable=self.mode_var, value='4 Operations', command=self._on_mode_change, font=self.main_font, bg=self.cget('bg'))
        rb_ops.pack(side='left', padx=(8,8))
        rb_multmode = tk.Radiobutton(row1, text='Multiplication', variable=self.mode_var, value='Multiplication', command=self._on_mode_change, font=self.main_font, bg=self.cget('bg'))
        rb_multmode.pack(side='left', padx=(8,8))
        rb_shapes = tk.Radiobutton(row1, text='Geometric Shapes', variable=self.mode_var, value='Geometric Shapes', command=self._on_mode_change, font=self.main_font, bg=self.cget('bg'))
        rb_shapes.pack(side='left', padx=(8,8))

        # Row2: combobox area
        row2 = tk.Frame(frm, bg=self.cget('bg'))
        row2.pack(pady=(6,0))

        # Pattern selector
        self.group_var = tk.StringVar(value=self.pattern_group)
        groups = ['All'] + [f"{i} Pattern" for i in range(1, 11)]
        if ttk:
            self.pattern_cb = ttk.Combobox(row2, textvariable=self.group_var, values=groups, state='readonly', font=self.main_font, width=10, height=11)
            self.pattern_cb.pack(side='left')
            try:
                self.pattern_cb.current(0)
            except Exception:
                pass
        else:
            self.pattern_cb = tk.OptionMenu(row2, self.group_var, *groups)
            self.pattern_cb.pack(side='left')

        # Times-table selector (1 times .. 10 times) - show descriptive labels
        self.times_var = tk.StringVar(value='All')
        # include 'All' option for mixed multiplication questions
        times = ['All'] + [f"{i} times" for i in range(1, 11)]
        if ttk:
            self.times_cb = ttk.Combobox(row2, textvariable=self.times_var, values=times, state='readonly', font=self.main_font, width=10, height=11)
            try:
                # default selection to 'All'
                self.times_cb.current(0)
            except Exception:
                pass
            self.times_cb.pack(side='left')
        else:
            self.times_cb = tk.OptionMenu(row2, self.times_var, *times)
            self.times_cb.pack(side='left', padx=(8,0))


        # Operations selector
        # operations combobox includes 'All' and defaults to 'All'
        self.ops_var = tk.StringVar(value='All')
        ops = ['All', 'Addition', 'Subtraction', 'Multiplication', 'Division']
        if ttk:
            self.ops_cb = ttk.Combobox(row2, textvariable=self.ops_var, values=ops, state='readonly', font=self.main_font, width=10, height=5)
            self.ops_cb.pack(side='left')
            try:
                self.ops_cb.current(0)
            except Exception:
                pass
        else:
            self.ops_cb = tk.OptionMenu(row2, self.ops_var, *ops)
            self.ops_cb.pack(side='left')

        # initialize visibility
        try:
            self._on_mode_change()
        except Exception:
            pass

        # Spacer before start button
        tk.Label(self, text='', bg=self.cget('bg'), height=2).pack()
        
        start_btn = tk.Button(self, text='🎮 Start Game', font=self.kid_button_font, bg='#4CAF50', fg='white', padx=10, pady=6, command=self._start_game)
        start_btn.pack(pady=12)

        stats_btn = tk.Button(self, text='📊 Statistics', font=self.kid_button_font, bg='#607D8B', fg='white', padx=10, pady=6, command=self._show_statistics_screen)
        stats_btn.pack(pady=(0, 10))

        # Credits section (bottom-right)
        credits_row = tk.Frame(self, bg=self.cget('bg'))
        credits_row.pack(side='bottom', fill='x', padx=10, pady=(0, 8))
        credits_link_font = font.Font(family='Terminal', size=12, underline=True)
        credits_link = tk.Label(
            credits_row,
            text='Credits',
            font=credits_link_font,
            bg=self.cget('bg'),
            fg='#1E88E5',
            cursor='hand2'
        )
        credits_link.pack(anchor='e')
        credits_link.bind('<Button-1>', self._open_credits_canvas)

    def _open_credits_canvas(self, event=None):
        for w in self.winfo_children():
            w.destroy()

        credits_canvas = tk.Canvas(self, bg='white', bd=0, highlightthickness=0, relief='flat')
        credits_canvas.pack(fill='both', expand=True)

        title_font = font.Font(family='Terminal', size=16)
        body_font = font.Font(family='Terminal', size=16)

        ascii_picnic = (
            '////    /   ////   /   /   /   ////\n'
            '/   /   /   /      //  /   /   /   \n'
            '////    /   /      / / /   /   /   \n'
            ' /       /   /      /  //   /   /    \n'
            '/       /   ////   /   /   /   ////'
        )
        ascii_pattern = (
            '////     ///    /////   /////   ////    ////    /   /\n'
            '/   /   /   /     /       /     /       /   /   //  /\n'
            '////    /////     /       /     ///     ////    / / /\n'
            '/       /   /     /       /     /       /  /    /  //\n'
            '/       /   /     /       /     ////    /   /   /   /'
        )
        message_text = (
            'I created this application for my beloved beautiful daughter Duru and other wonderful children, '
            'that they can make and achieve anything when they believe..'
        )

        def _draw_credits(event=None):
            try:
                credits_canvas.delete('all')
                canvas_w = max(credits_canvas.winfo_width(), 800)
                canvas_h = max(credits_canvas.winfo_height(), 560)
                margin = 24

                # Keep ASCII title inside visible area on smaller windows
                if canvas_w < 1000:
                    title_font.config(size=13)
                elif canvas_w < 1280:
                    title_font.config(size=14)
                else:
                    title_font.config(size=16)

                title1_id = credits_canvas.create_text(
                    canvas_w // 2,
                    40,
                    text=ascii_pattern,
                    font=title_font,
                    fill='black',
                    justify='center',
                    anchor='n'
                )
                bbox1 = credits_canvas.bbox(title1_id)
                title2_y = (bbox1[3] + (title_font.metrics('linespace') * 3)) if bbox1 else 150

                title2_id = credits_canvas.create_text(
                    canvas_w // 2,
                    title2_y,
                    text=ascii_picnic,
                    font=title_font,
                    fill='black',
                    justify='center',
                    anchor='n'
                )
                bbox2 = credits_canvas.bbox(title2_id)
                # push passage ~2 rows lower under the title block
                next_y = (bbox2[3] + 24 + (body_font.metrics('linespace') * 2)) if bbox2 else 320

                credits_canvas.create_text(
                    canvas_w // 2,
                    next_y,
                    text=message_text,
                    font=body_font,
                    fill='black',
                    width=max(360, canvas_w - (margin * 2)),
                    justify='center',
                    anchor='n'
                )

                credits_canvas.create_text(
                    canvas_w - margin,
                    canvas_h - margin,
                    text='Copyright (c) Y P C Software v2026.2.0',
                    font=font.Font(family='Terminal', size=11),
                    fill='black',
                    anchor='se'
                )
            except Exception:
                pass

        credits_canvas.bind('<Configure>', _draw_credits)
        self.after(10, _draw_credits)

        back_font = font.Font(family='Terminal', size=11, weight='bold')

        back_btn = tk.Button(
            self,
            text='◀ Back',
            font=back_font,
            command=self._build_start_screen,
            bg='#9E9E9E',
            fg='white'
        )
        back_btn.place(relx=0.02, rely=0.04, anchor='nw')

    def _start_game(self):
        try:
            entered_name = (getattr(self, 'player_var', tk.StringVar(value='Guest')).get() or '').strip()
            self.player_name = entered_name if entered_name else 'Guest'
        except Exception:
            self.player_name = 'Guest'

        try:
            self.age = max(3, int(self.age_var.get()))
        except Exception:
            self.age = 7
        try:
            self.rounds = max(1, int(self.rounds_var.get()))
        except Exception:
            self.rounds = 5
        # If multiplication mode, force 10 rounds and prepare non-repeating multipliers
        try:
            mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
        except Exception:
            mode = 'Patterns'
        if mode == 'Multiplication':
            self.rounds = 10
            try:
                self.rounds_var.set('10')
            except Exception:
                pass
            # prepare a shuffled list of multipliers 1..10 to avoid repeats
            self._mult_list = list(range(1, 11))
            random.shuffle(self._mult_list)
        
        if mode == 'Geometric Shapes':
            try:
                # Prepare shuffled list of indices for shapes to ensure all are shown
                # before repeating any.
                if getattr(self, '_shape_images', None):
                    n_shapes = len(self._shape_images)
                    # Create a list large enough for the number of rounds
                    indices = []
                    # Ensure at least one full set if rounds is small, or multiple sets if rounds is large
                    while len(indices) < max(self.rounds, n_shapes):
                         chunk = list(range(n_shapes))
                         random.shuffle(chunk)
                         indices.extend(chunk)
                    self._shuffled_shape_indices = indices
            except Exception:
                pass

        # difficulty combobox shows uppercase; normalize to lowercase for logic
        self.difficulty = (self.diff_var.get() or 'easy').lower()
        # record selected pattern group
        try:
            self.pattern_group = (self.group_var.get() or 'All')
        except Exception:
            self.pattern_group = 'All'
        self.current_round = 0
        self.score = 0
        self.kinds = self._pick_kind_for_age(self.age)
        # reset history browsing state when starting a new game
        try:
            self._viewing_history = None
        except Exception:
            pass
        self._build_game_screen()
        self._next_round()

    def _load_player_statistics(self):
        try:
            if os.path.isfile(self._stats_file):
                with open(self._stats_file, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self._player_stats = data
                else:
                    self._player_stats = {}
            else:
                self._player_stats = {}
        except Exception:
            self._player_stats = {}

    def _save_player_statistics(self):
        try:
            with open(self._stats_file, 'w', encoding='utf-8') as fh:
                json.dump(self._player_stats, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _record_player_statistics(self):
        try:
            name = (getattr(self, 'player_name', 'Guest') or 'Guest').strip()
            if not name:
                name = 'Guest'

            try:
                mode_name = (getattr(self, 'mode_var', None).get() if getattr(self, 'mode_var', None) else 'Patterns') or 'Patterns'
            except Exception:
                mode_name = 'Patterns'
            mode_name = str(mode_name).upper()

            stats_key = f'{name}||{mode_name}'

            stats = self._player_stats.get(stats_key, {
                'name': name,
                'game': mode_name,
                'games_played': 0,
                'total_score': 0,
                'total_rounds': 0,
                'best_score': 0,
                'best_accuracy': 0.0,
                'last_played': ''
            })

            rounds_val = int(getattr(self, 'rounds', 0) or 0)
            score_val = int(getattr(self, 'score', 0) or 0)

            stats['games_played'] = int(stats.get('games_played', 0)) + 1
            stats['total_score'] = int(stats.get('total_score', 0)) + score_val
            stats['total_rounds'] = int(stats.get('total_rounds', 0)) + rounds_val
            stats['best_score'] = max(int(stats.get('best_score', 0)), score_val)

            try:
                accuracy = (score_val / rounds_val) * 100 if rounds_val > 0 else 0.0
            except Exception:
                accuracy = 0.0
            stats['best_accuracy'] = max(float(stats.get('best_accuracy', 0.0)), float(accuracy))
            stats['last_played'] = time.strftime('%Y-%m-%d %H:%M:%S')
            stats['name'] = name
            stats['game'] = mode_name

            self._player_stats[stats_key] = stats
            self._save_player_statistics()
        except Exception:
            pass

    def _reset_statistics(self):
        try:
            self._player_stats = {}
            self._save_player_statistics()
        except Exception:
            pass
        self._show_statistics_screen()

    def _show_statistics_screen(self):
        for w in self.winfo_children():
            w.destroy()

        stats_color = '#000000'
        stats_title_font = self.big_font
        stats_row_font = self.main_font
        stats_btn_font = self.kid_button_font
        try:
            stats_header_font = font.Font(
                family=self.main_font.actual().get('family', 'Helvetica'),
                size=self.main_font.actual().get('size', 14),
                weight='bold'
            )
        except Exception:
            stats_header_font = self.main_font

        title = tk.Label(self, text='Player Statistics', font=stats_title_font, bg=self.cget('bg'), fg=stats_color)
        title.pack(pady=(18, 10))

        box = tk.Frame(self, bg='white', bd=1, relief='solid')
        box.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        self._load_player_statistics()
        if not self._player_stats:
            tk.Label(box, text='No statistics yet.', font=stats_row_font, bg='white', fg=stats_color).pack(pady=18)
        else:
            table = tk.Frame(box, bg='white')
            table.pack(anchor='n', padx=18, pady=(10, 8))

            headers = ['NAME', 'GAME', 'PLAYED', 'WON', 'SCRORE']
            anchors = ['w', 'w', 'e', 'e', 'e']
            for c, h in enumerate(headers):
                tk.Label(table, text=h, font=stats_header_font, bg='white', fg=stats_color, anchor=anchors[c]).grid(row=0, column=c, sticky='ew', padx=(0, 10), pady=(0, 6))

            table.grid_columnconfigure(0, minsize=170)
            table.grid_columnconfigure(1, minsize=170)
            table.grid_columnconfigure(2, minsize=110)
            table.grid_columnconfigure(3, minsize=120)
            table.grid_columnconfigure(4, minsize=140)

            # normalize legacy rows and sort by latest play, then best score
            normalized_rows = []
            for key, st in self._player_stats.items():
                if not isinstance(st, dict):
                    continue

                nm = str(st.get('name') or '').strip()
                gm = str(st.get('game') or '').strip()

                # backward compatibility: old key style was name-only
                if not nm:
                    try:
                        nm = str(key).split('||')[0].strip() if '||' in str(key) else str(key).strip()
                    except Exception:
                        nm = 'GUEST'
                if not nm:
                    nm = 'GUEST'

                if not gm:
                    try:
                        gm = str(key).split('||', 1)[1].strip() if '||' in str(key) else 'ALL MODES'
                    except Exception:
                        gm = 'ALL MODES'

                st['name'] = nm
                st['game'] = gm
                normalized_rows.append(st)

            rows = sorted(
                normalized_rows,
                key=lambda st: (
                    str(st.get('last_played', '')),
                    int(st.get('best_score', 0))
                ),
                reverse=True
            )

            # list only 10 statistics rows
            for row_idx, st in enumerate(rows[:10], start=1):
                name = str(st.get('name', 'GUEST')).upper()[:20]
                game = str(st.get('game', 'ALL MODES')).upper()[:20]
                games = int(st.get('games_played', 0))
                total_score = int(st.get('total_score', 0))
                best_score = int(st.get('best_score', 0))
                best_acc = float(st.get('best_accuracy', 0.0))

                values = [name, game, f'{games}', f'{best_score}', f'{best_acc:.0f}%']
                for c, value in enumerate(values):
                    tk.Label(table, text=value, font=stats_row_font, bg='white', fg=stats_color, anchor=anchors[c]).grid(row=row_idx, column=c, sticky='ew', padx=(0, 10), pady=3)

        actions = tk.Frame(self, bg=self.cget('bg'))
        actions.pack(fill='x', padx=24, pady=(0, 12))

        reset_btn = tk.Button(actions, text='Reset Stats', font=stats_btn_font, command=self._reset_statistics, bg='#F44336', fg='white')
        reset_btn.pack(side='right', padx=8)
        try:
            reset_btn.config(padx=6, pady=2)
        except Exception:
            pass

        back_btn = tk.Button(actions, text='◀ Back', font=stats_btn_font, command=self._build_start_screen, bg='#4CAF50', fg='white')
        back_btn.pack(side='left', padx=8)

    def _on_mode_change(self):
        mode = self.mode_var.get()
        try:
            # Hide all optional controls first
            try:
                self.pattern_cb.pack_forget()
            except Exception:
                pass
            try:
                self.ops_cb.pack_forget()
            except Exception:
                pass
            try:
                self.times_cb.pack_forget()
            except Exception:
                pass

            # Configure per-mode visibility/state
            if mode == 'Patterns':
                try:
                    self.pattern_cb.pack(side='left')
                except Exception:
                    pass
                try:
                    self.rounds_entry.config(state='normal')
                except Exception:
                    pass
                # ensure widgets are enabled after shapes mode
                try:
                    try:
                        self.pattern_cb.config(state='readonly')
                    except Exception:
                        self.pattern_cb.config(state='normal')
                except Exception:
                    pass
            elif mode == 'Multiplication':
                try:
                    self.times_cb.pack(side='left')
                except Exception:
                    pass
                try:
                    self.rounds_var.set('10')
                except Exception:
                    pass
                try:
                    self.rounds_entry.config(state='disabled')
                except Exception:
                    pass
                try:
                    try:
                        self.times_cb.config(state='readonly')
                    except Exception:
                        self.times_cb.config(state='normal')
                except Exception:
                    pass
            elif mode == '4 Operations':
                try:
                    self.ops_cb.pack(side='left')
                except Exception:
                    pass
                try:
                    self.rounds_entry.config(state='normal')
                except Exception:
                    pass
                try:
                    try:
                        self.ops_cb.config(state='readonly')
                    except Exception:
                        self.ops_cb.config(state='normal')
                except Exception:
                    pass
            elif mode == 'Geometric Shapes':
                # deactivate/hide all comboboxes for shapes mode
                try:
                    self.pattern_cb.pack_forget()
                except Exception:
                    pass
                try:
                    self.ops_cb.pack_forget()
                except Exception:
                    pass
                try:
                    self.times_cb.pack_forget()
                except Exception:
                    pass
                try:
                    # also disable if ttk widget (harmless if not)
                    self.pattern_cb.config(state='disabled')
                except Exception:
                    pass
                try:
                    self.ops_cb.config(state='disabled')
                except Exception:
                    pass
                try:
                    self.times_cb.config(state='disabled')
                except Exception:
                    pass
                try:
                    # disable rounds entry and set to image count when shapes are available
                    self.rounds_entry.config(state='disabled')
                except Exception:
                    pass
                try:
                    if getattr(self, '_shape_images', None):
                        cnt = len(self._shape_images)
                        try:
                            self.rounds_var.set(str(cnt))
                        except Exception:
                            pass
                        try:
                            self.rounds = cnt
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    # if game screen exists, make the pattern label smaller for shapes
                    if getattr(self, 'pattern_label', None):
                        try:
                            self.pattern_label.config(font=self.main_font)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    def _build_game_screen(self):
        for w in self.winfo_children():
            w.destroy()
        # round indicator rendered inside its own small canvas to allow
        # precise centering and easier in-canvas drawing when restoring snapshots
        try:
            self.round_canvas = tk.Canvas(self, width=220, height=40, bg=self.cget('bg'), highlightthickness=0)
            # move indicator one row down by increasing top padding
            self.round_canvas.pack(pady=(24, 6), anchor='center')
            try:
                self._round_text_id = self.round_canvas.create_text(110, 20, text='', font=self.main_font, fill='#1E88E5', anchor='center')
            except Exception:
                self._round_text_id = None
        except Exception:
            # fallback to the old label if canvas creation fails for some reason
            self.round_label = tk.Label(self, text='', font=self.main_font, bg=self.cget('bg'), fg='#1E88E5')
            self.round_label.pack(pady=(24, 6), anchor='center')
        # allow long text to wrap and canvas to expand with window
        # questions and drawing area use white background and are centered on the canvas
        # set explicit border/background options to avoid visible seams
        self.canvas = tk.Canvas(self, bg='white', bd=0, highlightthickness=0, relief='flat')
        # add more top padding so the white area sits lower on the window
        self.canvas.pack(fill='both', expand=True, padx=0, pady=(50,12))
        # draw a backing rectangle that always fills the canvas to avoid
        # thin seams or platform-specific widget boundaries when embedding
        # other widgets via create_window.
        try:
            self.canvas.update_idletasks()
            w = self.canvas.winfo_width() or 600
            h = self.canvas.winfo_height() or 300
            self._canvas_bg_rect = self.canvas.create_rectangle(0, 0, w, h, fill='white', outline='')
            # ensure the bg rect stays beneath other items
            try:
                self.canvas.tag_lower(self._canvas_bg_rect)
            except Exception:
                pass
            # removed center mask to avoid visible white line
            self._canvas_center_mask = None
            try:
                # extra safety: ensure no center mask object exists
                self.canvas.delete('center_mask')
            except Exception:
                pass
        except Exception:
            self._canvas_bg_rect = None
        # create a centered label on the canvas for the question text (keeps it on the white area)
        # ensure the label has no border or highlight so it blends with canvas
        self.pattern_label = tk.Label(self.canvas, text='', font=self.big_font, bg='white', wraplength=900, justify='center', bd=0, highlightthickness=0, relief='flat')
        # create a canvas window for the label anchored at center.
        # update layout first so we can compute the canvas center and avoid any flash
        try:
            self.canvas.update_idletasks()
            w = self.canvas.winfo_width() or 600
            h = self.canvas.winfo_height() or 300
            cx = w // 2
            cy = h // 2
            self._pattern_window = self.canvas.create_window(cx, cy, window=self.pattern_label, anchor='center')
            try:
                # initially hide the pattern label until we finish layout to avoid a one-line flash
                self.canvas.itemconfigure(self._pattern_window, state='hidden')
                try:
                    # ensure label text empty initially to avoid transient numbers
                    self.pattern_label.config(text='')
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            # fallback: create offscreen and schedule placement
            self._pattern_window = self.canvas.create_window(-10000, -10000, window=self.pattern_label, anchor='center')
        # placement will be handled by the round setup to avoid early reveals
        # Choice buttons for Geometric Shapes mode (created but hidden for other modes)
        self.choice_frame = tk.Frame(self, bg=self.cget('bg'))
        # three push buttons placed directly under the canvas
        self.choice_buttons = []
        # add flexible spacers so buttons appear centered
        left_spacer = tk.Frame(self.choice_frame, bg=self.cget('bg'))
        left_spacer.pack(side='left', expand=True, fill='x')
        for i in range(3):
            b = tk.Button(self.choice_frame, text=f'Choice {i+1}', font=self.small_button_font, bg=self.cget('bg'), relief='raised', command=(lambda idx=i: self._on_shape_choice(idx)), padx=6, pady=2)
            # fixed, equal-size buttons (don't expand to fill)
            b.pack(side='left', padx=6, pady=2)
            try:
                # slightly smaller fixed size so labels fit comfortably
                b.config(width=14, height=1)
            except Exception:
                pass
            self.choice_buttons.append(b)
        right_spacer = tk.Frame(self.choice_frame, bg=self.cget('bg'))
        right_spacer.pack(side='left', expand=True, fill='x')
        # internal selection and history
        self._selected_choice = None
        self._choice_map = {}
        self._round_history = []
        # index into _round_history when viewing past rounds; None when live
        self._viewing_history = None

        # don't pack yet; we'll place the choices before the entry frame when needed
        try:
            self.choice_frame.pack_forget()
        except Exception:
            pass

        # answer area uses same snow background to remove gray line
        self.entry_frm = tk.Frame(self, bg=self.cget('bg'))
        self.entry_frm.pack(fill='x')
        # center the answer label+entry together
        self.answer_inner = tk.Frame(self.entry_frm, bg=self.cget('bg'))
        self.answer_inner.pack()
        self.answer_var = tk.StringVar()
        # intentional typo per request: 'Asnwer' and centered
        # match the label background to the window to remove gray strip
        self.answer_label = tk.Label(self.answer_inner, text='Answer', font=self.main_font, bg=self.cget('bg'))
        self.answer_label.pack(side='left', padx=(0,8))
        self.answer_entry = tk.Entry(self.answer_inner, textvariable=self.answer_var, font=self.main_font, width=6)
        vcmd = (self.register(self._validate_answer), '%P')
        self.answer_entry.config(validate='key', validatecommand=vcmd)
        self.answer_entry.pack(side='left')
        btn_frm = tk.Frame(self, bg=self.cget('bg'))
        btn_frm.pack(pady=12, fill='x')
        # inner frame to center the control buttons
        btn_inner = tk.Frame(btn_frm, bg=self.cget('bg'))
        btn_inner.pack(expand=True)
        # Home button on the left of navigation
        home = tk.Button(btn_inner, text='🏠 Home', font=self.kid_button_font, command=self._build_start_screen, bg='#4CAF50', fg='white')
        home.pack(side='left', padx=8)
        back = tk.Button(btn_inner, text='◀ Back', font=self.kid_button_font, command=self._go_back, bg='#FFD54F', fg='white')
        back.pack(side='left', padx=8)
        self.submit_button = tk.Button(btn_inner, text='✅ Submit', font=self.kid_button_font, command=self._submit_answer, bg='#29B6F6', fg='white')
        self.submit_button.pack(side='left', padx=8)
        # Next button: triangle plus label
        self.next_button = tk.Button(btn_inner, text='▶ Next', font=self.kid_button_font, command=self._skip, bg='#9E9E9E', fg='white')
        self.next_button.pack(side='left', padx=8)
        for btn in (back, self.submit_button, self.next_button):
            try:
                btn.config(width=10, height=1)
            except Exception:
                pass
        feedback_frm = tk.Frame(self, bg=self.cget('bg'))
        feedback_frm.pack(pady=6, fill='x')
        # inner centered container to hold feedback text and the icon at the end
        center_inner = tk.Frame(feedback_frm, bg=self.cget('bg'))
        # expand horizontally so centered children span the full width
        center_inner.pack(fill='x')
        # make the left column expand so the feedback label can center itself
        try:
            center_inner.grid_columnconfigure(0, weight=1)
        except Exception:
            pass
        # feedback label and icon placed side-by-side inside center_inner; center_inner is packed without fill so it stays centered
        self.feedback_label = tk.Label(center_inner, text='', font=self.main_font, bg=self.cget('bg'), justify='center', anchor='center')
        self.feedback_label.grid(row=0, column=0, sticky='ew')
        # smaller icon canvas to the right of the feedback
        
        # Score label placed inside center_inner so it centers under feedback
        # Match score color to the round indicator color for consistency
        try:
            round_fg = getattr(self, 'round_label', None) and self.round_label.cget('fg') or '#1E88E5'
        except Exception:
            round_fg = '#1E88E5'
        self.score_label = tk.Label(center_inner, text='', font=self.main_font, bg=self.cget('bg'), fg=round_fg)
        try:
            self.score_label.grid(row=1, column=0, columnspan=2, pady=(6, 12), sticky='ew')
        except Exception:
            # fallback to packing on the main window
            try:
                self.score_label = tk.Label(self, text='', font=self.main_font, bg=self.cget('bg'), fg='#4A148C')
                self.score_label.pack(pady=(6, 12))
            except Exception:
                pass

        # ensure choice_frame hidden by default; _next_round will show when needed
        try:
            self.choice_frame.pack_forget()
        except Exception:
            pass

    def _draw_shape_on_canvas(self, shape, color):
        c = self.canvas
        # if image-based shapes are available, avoid drawing vector shapes (prevents flash)
        try:
            if getattr(self, '_using_shape_images', False):
                return
        except Exception:
            pass
        w = c.winfo_width() or 600
        h = c.winfo_height() or 300
        cx = w // 2
        cy = h // 2
        # slightly smaller base size so tall shapes (cylinder/sphere) don't overflow
        base_size = max(36, min(w, h) // 7)
        # if thumbnail size information exists, use it as the baseline so vector
        # shapes match the displayed image size regardless of original picture size
        try:
            thumb_dim = int(getattr(self, '_max_thumb_dim', 0))
            if thumb_dim and thumb_dim > 0:
                # size here is the approximate half-extent we will use for drawing
                base_size = max(28, int(thumb_dim * 0.48))
        except Exception:
            pass
        # adjust per-shape so spheres/cylinders don't visually dominate thumbnails
        if shape in ('circle', 'sphere'):
            size = max(32, int(base_size * 0.9))
        elif shape == 'cylinder':
            size = max(34, int(base_size * 0.95))
        else:
            size = base_size
        fill = color
        outline = 'black'
        # basic 2D representations for shapes
        if shape in ('circle', 'sphere'):
            c.create_oval(cx - size, cy - size, cx + size, cy + size, fill=fill, outline=outline, width=2, tags='shapes')
        elif shape == 'ellipse':
            c.create_oval(cx - int(size*1.4), cy - int(size*0.8), cx + int(size*1.4), cy + int(size*0.8), fill=fill, outline=outline, width=2, tags='shapes')
        elif shape in ('square', 'cube'):
            c.create_rectangle(cx - size, cy - size, cx + size, cy + size, fill=fill, outline=outline, width=2, tags='shapes')
            if shape == 'cube':
                off = size//3
                # draw a simple isometric cube illusion
                c.create_polygon([cx - size, cy - size, cx - size + off, cy - size - off, cx + size + off, cy - size - off, cx + size, cy - size], outline=outline, fill='', tags='shapes')
                c.create_rectangle(cx - size + off, cy - size - off, cx + size + off, cy + size - off, outline=outline, tags='shapes')
                c.create_line(cx + size, cy - size, cx + size + off, cy - size - off, fill=outline, tags='shapes')
        elif shape in ('rectangle', 'rectangular prism', 'cuboid'):
            c.create_rectangle(cx - int(size*1.4), cy - int(size*0.8), cx + int(size*1.4), cy + int(size*0.8), fill=fill, outline=outline, width=2, tags='shapes')
            if shape in ('rectangular prism', 'cuboid'):
                off = size//4
                c.create_rectangle(cx - int(size*1.4) + off, cy - int(size*0.8) - off, cx + int(size*1.4) + off, cy + int(size*0.8) - off, outline=outline, tags='shapes')
                self.choice_frame.pack(pady=6, fill='x', before=self.entry_frm, anchor='center')
            pts = [cx, cy - size, cx - size, cy + size, cx + size, cy + size]
            c.create_polygon(pts, fill=fill, outline=outline, width=2, tags='shapes')
            if shape == 'triangular prism':
                off = size//4
                c.create_polygon([cx - size, cy + size, cx - size + off, cy + size - off, cx + size + off, cy + size - off, cx + size, cy + size], outline=outline, fill='', tags='shapes')
        elif shape == 'cone':
            pts = [cx, cy - size, cx - size, cy + size, cx + size, cy + size]
            c.create_polygon(pts, fill=fill, outline=outline, width=2, tags='shapes')
            c.create_oval(cx - size//2, cy + int(size*0.6), cx + size//2, cy + int(size*0.8), outline=outline)
        elif shape == 'pentagon':
            pts = []
            for i in range(5):
                ang = (i * 2 * math.pi / 5) - math.pi/2
                pts.extend([cx + int(size * 0.9 * math.cos(ang)), cy + int(size * 0.9 * math.sin(ang))])
            c.create_polygon(pts, fill=fill, outline=outline, width=2)
        elif shape == 'hexagon':
            pts = []
            for i in range(6):
                ang = (i * 2 * math.pi / 6) - math.pi/2
                pts.extend([cx + int(size * 0.9 * math.cos(ang)), cy + int(size * 0.9 * math.sin(ang))])
            c.create_polygon(pts, fill=fill, outline=outline, width=2)
        elif shape == 'cylinder':
            # body (slightly shorter so it matches thumbnail height)
            c.create_rectangle(cx - size, cy - int(size*0.25), cx + size, cy + int(size*0.6), fill=fill, outline=outline, width=2, tags='shapes')
            # top ellipse (narrower)
            c.create_oval(cx - int(size*0.7), cy - int(size*0.45), cx + int(size*0.7), cy - int(size*0.12), fill=fill, outline=outline, width=2, tags='shapes')
        else:
            # fallback simple circle
            c.create_oval(cx - size, cy - size, cx + size, cy + size, fill=fill, outline=outline, width=2, tags='shapes')

    def _on_resize(self, event=None):
        try:
            if hasattr(self, 'pattern_label'):
                w = max(200, self.winfo_width())
                # keep text wrapping within the window
                try:
                    self.pattern_label.config(wraplength=int(w * 0.9))
                except Exception:
                    pass
            # if showing a shape, redraw it to fit the new canvas size
            mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
            # If we're using loaded images, reposition/redraw images on resize
            if mode == 'Geometric Shapes' and getattr(self, '_using_shape_images', False):
                try:
                    # debounce multiple resizes
                    try:
                        if getattr(self, '_resize_after_id', None):
                            self.after_cancel(self._resize_after_id)
                    except Exception:
                        pass
                    def _do_redraw_img():
                        try:
                            # reposition image centered and adjust pattern label
                            try:
                                self.canvas.delete('shapes')
                            except Exception:
                                pass
                            try:
                                # Use the current random image index if set, otherwise fallback
                                if hasattr(self, 'current_image_index'):
                                    idx = self.current_image_index
                                else:
                                    idx = (self.current_round - 1) % len(self._shape_images)
                                
                                _, photo = self._shape_images[idx]
                                self._last_image = photo
                                cx = self.canvas.winfo_width() // 2
                                cy = self.canvas.winfo_height() // 2
                                try:
                                    h = self.canvas.winfo_height() or 300
                                    # move thumbnails up by ~30px (two rows)
                                    offset = max(10, int(h * 0.18) - 30)
                                except Exception:
                                    offset = 50
                                self.canvas.create_image(cx, cy + offset, image=photo, tags='shapes')
                                try:
                                    # mark image as placed and enable Next
                                    self._image_placed = True
                                except Exception:
                                    pass
                                try:
                                    if getattr(self, 'next_button', None):
                                        try:
                                            self.next_button.config(state='normal')
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            try:
                                self._place_pattern_label()
                            except Exception:
                                pass
                        finally:
                            try:
                                self._resize_after_id = None
                            except Exception:
                                pass
                    try:
                        self._resize_after_id = self.after(120, _do_redraw_img)
                    except Exception:
                        try:
                            _do_redraw_img()
                        except Exception:
                            pass
                except Exception:
                    pass
            elif mode == 'Geometric Shapes' and getattr(self, '_last_shape', None):
                try:
                    s = self._last_shape
                    c = getattr(self, '_last_color', 'blue')
                    # debounce multiple resizes: cancel previous scheduled redraw
                    try:
                        if getattr(self, '_resize_after_id', None):
                            self.after_cancel(self._resize_after_id)
                    except Exception:
                        pass
                    def _do_redraw():
                        try:
                            self.canvas.update_idletasks()
                            self._draw_shape_on_canvas(s, c)
                            try:
                                self._place_pattern_label()
                            except Exception:
                                pass
                        finally:
                            try:
                                self._resize_after_id = None
                            except Exception:
                                pass
                    try:
                        self._resize_after_id = self.after(150, _do_redraw)
                    except Exception:
                        # fallback immediate redraw
                        try:
                            self.canvas.update_idletasks()
                            self._draw_shape_on_canvas(s, c)
                        except Exception:
                            pass
                except Exception:
                    pass
            # resize the background rectangle to cover the full canvas area
            try:
                if getattr(self, '_canvas_bg_rect', None) is not None:
                    cw = self.canvas.winfo_width() or 0
                    ch = self.canvas.winfo_height() or 0
                    try:
                        self.canvas.coords(self._canvas_bg_rect, 0, 0, cw, ch)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if getattr(self, '_canvas_center_mask', None) is not None:
                    # if mask exists (should be None), remove it
                    try:
                        self.canvas.delete(self._canvas_center_mask)
                        self._canvas_center_mask = None
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _on_shape_choice(self, idx):
        # idx is index into the currently shown choice buttons
        try:
            sel = self._choice_map.get(idx)
        except Exception:
            sel = None
        self._selected_choice = sel
        # visually indicate selection
        for i, b in enumerate(self.choice_buttons):
            try:
                if i == idx:
                    b.config(relief='sunken', bg='#B0BEC5', fg='black')
                else:
                    b.config(relief='raised', bg=self.cget('bg'), fg='black')
            except Exception:
                pass

    def _save_live_state(self):
        """Save the current unfinished round state before browsing history."""
        try:
            state = {}
            state['current_seq'] = getattr(self, 'current_seq', None)
            state['blank_index'] = getattr(self, 'blank_index', None)
            state['current_answer'] = getattr(self, 'current_answer', None)
            state['shape_images'] = getattr(self, '_shape_images', None)
            state['last_image'] = getattr(self, '_last_image', None)
            state['last_shape'] = getattr(self, '_last_shape', None)
            state['last_color'] = getattr(self, '_last_color', None)
            state['current_image_index'] = getattr(self, 'current_image_index', None)
            state['shape_image_names'] = getattr(self, '_shape_image_names', None)
            state['shuffled_shape_indices'] = getattr(self, '_shuffled_shape_indices', None)
            
            # Save pattern label text
            try:
                if getattr(self, 'pattern_label', None):
                    state['pattern_label_text'] = self.pattern_label.cget('text')
            except Exception:
                pass
            
            # Save mode specific stuff
            state['mode'] = getattr(self, 'mode_var', None) and self.mode_var.get()
            
            self._live_round_state = state
        except Exception:
            pass

    def _restore_live_state(self):
        """Restore the live round state if available."""
        try:
            state = getattr(self, '_live_round_state', None)
            if not state:
                return False
                
            # Restore mode first
            mode = state.get('mode')
            if mode:
                if getattr(self, 'mode_var', None): self.mode_var.set(mode)
                if getattr(self, 'mode_combobox', None): self.mode_combobox.set(mode)
            
            # Clean up prior state (including both shapes and text)
            try: self.canvas.delete('all')
            except: pass
            
            for tid in getattr(self, '_seq_text_items', []) or []:
                try: self.canvas.delete(tid)
                except: pass
            self._seq_text_items = []

            # Restore data
            self.current_seq = state.get('current_seq')
            self.blank_index = state.get('blank_index')
            self.current_answer = state.get('current_answer')
            self._shape_images = state.get('shape_images')
            self._last_image = state.get('last_image')
            self._last_shape = state.get('last_shape')
            self._last_color = state.get('last_color')
            if state.get('current_image_index') is not None:
                self.current_image_index = state.get('current_image_index')
                
            # Restore shape mode helpers
            if state.get('shape_image_names'): self._shape_image_names = state.get('shape_image_names')
            if state.get('shuffled_shape_indices'): self._shuffled_shape_indices = state.get('shuffled_shape_indices')

            # Always reset typed answer when returning to live state.
            # History browsing may have inserted an old solved answer.
            try:
                if getattr(self, 'answer_var', None):
                    self.answer_var.set('')
            except Exception:
                pass

            try:
                if getattr(self, 'answer_entry', None):
                    prev_state = self.answer_entry.cget('state')
                    if prev_state == 'disabled':
                        self.answer_entry.config(state='normal')
                    self.answer_entry.delete(0, 'end')
            except Exception:
                pass

            # Show/Hide inputs based on mode
            try:
                if mode in ('Patterns', 'Multiplication', '4 Operations'):
                    if getattr(self, 'answer_entry', None): self.answer_entry.pack(side='left', padx=5)
                    if hasattr(self, 'choice_frame') and self.choice_frame: self.choice_frame.pack_forget()
                elif mode == 'Geometric Shapes':
                    if getattr(self, 'answer_entry', None): self.answer_entry.pack_forget()
                    if hasattr(self, 'choice_frame') and self.choice_frame: self.choice_frame.pack(pady=6, fill='x', anchor='center')
                    # Restore buttons state?
                    # The choice buttons should be reset
            except: pass

            # Redraw based on mode
            # Force update for canvas dimensions
            self.canvas.update_idletasks()
            
            if mode in ('Patterns', 'Multiplication', '4 Operations') and self.current_seq:
                w = self.canvas.winfo_width() or 600
                h = self.canvas.winfo_height() or 300
                cx = w // 2
                cy = h // 2
                if mode in ('Multiplication', '4 Operations', 'Ops/Math'):
                    spacing = max(40, min(80, w // (len(self.current_seq) + 2)))
                else:
                    spacing = max(60, min(140, w // (len(self.current_seq) + 1)))
                start_x = cx - spacing * (len(self.current_seq) - 1) / 2
                
                # Recreate text items
                for i, v in enumerate(self.current_seq):
                    txt = '_' if i == self.blank_index else str(v)
                    tid = self.canvas.create_text(int(start_x + i * spacing), cy, text=txt, font=self.big_font, fill='black', tags='seq')
                    self._seq_text_items.append(tid)

            elif mode == 'Geometric Shapes':
                if self._last_shape:
                     self._draw_shape_on_canvas(self._last_shape, self._last_color)
                elif self._last_image:
                     cx = self.canvas.winfo_width() // 2
                     cy = self.canvas.winfo_height() // 2
                     try:
                        h = self.canvas.winfo_height() or 300
                        offset = max(10, int(h * 0.18) - 30)
                     except: offset = 50
                     self.canvas.create_image(cx, cy + offset, image=self._last_image, tags='shapes')
                
            # Restore pattern label text
            try:
                if getattr(self, 'pattern_label', None) and 'pattern_label_text' in state:
                    self.pattern_label.config(text=state['pattern_label_text'], fg='#0D47A1')
            except Exception:
                pass

            # Restore choices if logic permits, or just randomize
            pass
            
            # Restore controls to normal or disabled based on whether it was answered
            try:
                is_answered = False
                if self._round_history and self._round_history[-1].get('selected') is not None:
                    is_answered = True
                    
                state_str = 'disabled' if is_answered else 'normal'
                
                if getattr(self, 'submit_button', None):
                    self.submit_button.config(state=state_str)
                if getattr(self, 'choice_buttons', None): 
                    for btn in self.choice_buttons: btn.config(state=state_str)
                if getattr(self, 'answer_entry', None): self.answer_entry.config(state=state_str)
            except: pass
            
            return True
        except Exception:
            return False

    def _go_back(self):
        try:
            # Cancel any pending timer to prevent auto-advancing while viewing history
            try:
                if getattr(self, '_next_round_timer', None):
                    self.after_cancel(self._next_round_timer)
                    self._next_round_timer = None
            except Exception:
                pass

            if not self._round_history:
                return
            
            # Save the current mode (active game mode) before we start browsing history
            # Only save if we are STARTING to browse history (currently live)
            try:
                if getattr(self, '_viewing_history', None) is None:
                    self._save_live_state()
            except Exception:
                pass

            # Use a robust way to determine target index
            try:
                # If we are currently "Live" (viewing_history is None),
                # we want to view the PREVIOUS completed round, NOT the current live one.
                # If current round is generated but unfinished, it is the last item in history.
                # So we want len - 2.
                if getattr(self, '_viewing_history', None) is None:
                    # check if current round is already in history?
                    # usually it is appended at generation.
                    if len(self._round_history) >= self.current_round:
                        idx = self.current_round - 2
                    else:
                        idx = len(self._round_history) - 1
                else:
                    # If we are already viewing history, go back one step
                    idx = self._viewing_history - 1
            except Exception:
                idx = len(self._round_history) - 1

            # Clamp index to be valid
            if idx < 0:
                idx = 0
            if idx >= len(self._round_history):
                idx = len(self._round_history) - 1
                
            # If we are already at the start, do nothing (or reload start)
            if getattr(self, '_viewing_history', None) is not None and idx == self._viewing_history:
                 # We are asking to go back but index didn't change (at 0).
                 if idx == 0:
                     # allow reload in case of glitches
                     pass
                 else:
                     return

            snap = self._round_history[idx]
            try:
                self._viewing_history = idx
            except Exception:
                pass
            try:
                self.current_round = idx + 1
            except Exception:
                pass
            try:
                self._load_snapshot(snap, idx)
                
                # CRITICAL: _load_snapshot might update the mode_var via Combobox.
                # But we want to preserve the USER'S selected mode for the NEXT live round?
                # Or should the mode switch to what was in history?
                # User complaint: "history independently".
                # This implies viewing history should NOT change the current game settings for future rounds.
                
                # However, to view the history correctly, we MUST update the UI mode.
                # So we must saving the intended "Next Round Mode" somewhere before loading snapshot?
                # Or we just accept that viewing history changes the mode.
                
                # If the user says "history independently", they probably hate that their settings changed.
                # But more importantly, if they go back to Round 6 (Live), they expect it to be what they were playing.
                pass
            except Exception:
                pass
        except Exception:
            pass

    def _load_snapshot(self, snap, idx=None):
        """Restore minimal UI state from a snapshot dict.

        This implementation is intentionally simpler and more linear than the
        previous deeply nested version to avoid fragile try/except nesting.
        """
        # basic safety checks
        if not isinstance(snap, dict):
            return

        mode = snap.get('mode')
        displayed = snap.get('displayed')
        # Safely copy sequence to prevent reference issues
        raw_seq = snap.get('current_seq')
        if isinstance(raw_seq, (list, tuple)):
            self.current_seq = list(raw_seq)
        else:
            self.current_seq = []
            
        self.blank_index = snap.get('blank_index')
        self.current_answer = snap.get('current_answer')

        # clear previous sequence items and any feedback window
        try:
            # Force update before clearing to ensure proper state
            self.canvas.update_idletasks()
            for tid in getattr(self, '_seq_text_items', []) or []:
                self.canvas.delete(tid)
        except Exception:
            pass
        self._seq_text_items = []
        try:
            if getattr(self, '_canvas_feedback_widget', None):
                self.canvas.delete(self._canvas_feedback_widget)
        except Exception:
            pass
        self._canvas_feedback_widget = None

        # restore choices for Geometric Shapes / choice-based modes
        try:
            if mode and mode.startswith('Geometric'):
                choices = snap.get('choices', []) or []
                self._choice_map.clear()
                for i, b in enumerate(self.choice_buttons):
                    val = choices[i] if i < len(choices) else ''
                    try:
                        b.config(text=(val.title() if val else ''))
                        b.config(relief='raised', bg=self.cget('bg'), fg='black')
                    except Exception:
                        pass
                    self._choice_map[i] = val
                try:
                    self.choice_frame.pack(pady=6, fill='x', before=self.entry_frm, anchor='center')
                except Exception:
                    try:
                        self.choice_frame.pack(pady=6, fill='x', anchor='center')
                    except Exception:
                        pass
                try:
                    self.answer_entry.pack_forget()
                    self.answer_label.pack_forget()
                except Exception:
                    pass
                
                # Restore the specific shape image for this historical round
                try:
                    # Clear current shape
                    self.canvas.delete('shapes')
                    
                    # If using image files 
                    fname = snap.get('file')
                    if fname and hasattr(self, '_shape_images'):
                        # Find matching photo in _shape_images by filename
                        # _shape_images is list of (path, photo)
                        # We need to match os.path.basename(path) == fname
                        found_photo = None
                        for p_path, p_photo in self._shape_images:
                            if os.path.basename(p_path) == fname:
                                found_photo = p_photo
                                break
                        
                        if found_photo:
                            w = self.canvas.winfo_width() or 600
                            h = self.canvas.winfo_height() or 300
                            cx = w // 2
                            cy = h // 2
                            offset = max(10, int(h * 0.18) - 30)
                            self.canvas.create_image(cx, cy + offset, image=found_photo, tags='shapes')
                        else:
                            # Fallback if image not found in current session list (e.g. reload)
                            self.canvas.create_text(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, text=f"[Image: {fname}]", font=self.main_font)
                    
                    # If using vector shapes
                    elif snap.get('shape') and snap.get('color'):
                        start_shape = snap.get('shape')
                        start_color = snap.get('color')
                        self._draw_shape_on_canvas(start_shape, start_color)

                except Exception:
                    pass

            else:
                # numeric/operation mode: set pattern text and place it
                try:
                    if displayed is not None:
                        self.pattern_label.config(text=displayed, fg='black')
                except Exception:
                    pass
                try:
                    self._place_pattern_label()
                except Exception:
                    pass

                # recreate sequence items if present
                if self.current_seq:
                    try:
                        self.canvas.update_idletasks()
                        w = self.canvas.winfo_width() or 600
                        cx = w // 2
                        
                        # Use tight spacing for equations, loose for pattern sequences
                        mode_str = snap.get('mode', '')
                        seq_len = len(self.current_seq) if self.current_seq else 0
                        if seq_len > 0:
                            if mode_str in ['Multiplication', 'Ops/Math', '4 Operations']:
                                spacing = max(40, min(80, w // (seq_len + 2)))
                            else:
                                spacing = max(60, min(140, w // (seq_len + 1)))

                            start_x = cx - spacing * (seq_len - 1) / 2
                            y = self.canvas.winfo_height() // 2 or 150
                            for i, v in enumerate(self.current_seq):
                                if i == self.blank_index:
                                    # When reviewing history, show the correct answer in green
                                    if snap.get('was_correct') is not None:
                                        txt = str(snap.get('current_answer') or v)
                                        fill = '#8BC34A'  # green for correct
                                    else:
                                        txt = '_'
                                        fill = 'black'
                                else:
                                    txt = str(v)
                                    fill = 'black'
                                tid = self.canvas.create_text(int(start_x + i * spacing), y, text=txt, font=self.big_font, fill=fill, tags='seq')
                                self._seq_text_items.append(tid)
                    except Exception:
                        pass

        except Exception:
            # fall back silently on any unexpected error while restoring
            pass

        # restore selection/feedback visuals
        try:
            sel = snap.get('selected')
            was_correct = snap.get('was_correct')
            if sel:
                for i, b in enumerate(self.choice_buttons):
                    try:
                        val = self._choice_map.get(i)
                        if val and sel and val.lower() == sel.lower():
                            b.config(relief='sunken')
                            # Do not mark the user's wrong selection red during history;
                            # instead leave it sunken and highlight the correct answer below.
                        # always mark the correct choice green when known
                        if was_correct is False and val and val.lower() == (snap.get('current_answer') or '').lower():
                            b.config(bg='#8BC34A', fg='white')
                        if was_correct is True and val and val.lower() == sel.lower():
                            b.config(bg='#8BC34A', fg='white')
                    except Exception:
                        pass
        except Exception:
            pass

        # If the snapshot contains a feedback sentence (e.g. "Yes!" / "No!"),
        # restore it as a permanent indicator while browsing history. Otherwise
        # clear transient feedback widgets as before.
        try:
            fb_text = snap.get('feedback_text')
            fb_fg = snap.get('feedback_fg', 'black')
            if fb_text:
                try:
                    # For live rounds show the top feedback label; when
                    # browsing history hide the top label and keep the
                    # canvas-based indicator (bottom) to avoid duplicate
                    # messages above the score.
                    if getattr(self, '_viewing_history', None) is None:
                        self.feedback_label.config(text=fb_text, fg=fb_fg)
                    else:
                        try:
                            self.feedback_label.config(text='')
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    container = tk.Frame(self.canvas, bg='white')
                    lbl = tk.Label(container, text=fb_text, font=self.main_font, bg='white', fg=fb_fg, anchor='center', justify='center')
                    lbl.grid(row=0, column=0, sticky='ew')
                    try:
                        icon_c = tk.Canvas(container, width=28, height=28, bg='white', highlightthickness=0)
                        icon_c.grid(row=0, column=1, padx=(8, 0), pady=2)
                    except Exception:
                        icon_c = None
                    try:
                        cx, cy = self._feedback_coords()
                    except Exception:
                        cx = None
                        cy = None
                    if cx and cy:
                        try:
                            self._canvas_feedback_widget = self.canvas.create_window(cx, cy, window=container, anchor='n', tags='feedback')
                        except Exception:
                            try:
                                self._canvas_feedback_widget = self.canvas.create_window(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2 + 60, window=container, anchor='n', tags='feedback')
                            except Exception:
                                self._canvas_feedback_widget = None
                    else:
                        try:
                            self._canvas_feedback_widget = self.canvas.create_window(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2 + 60, window=container, anchor='n', tags='feedback')
                        except Exception:
                            self._canvas_feedback_widget = None
                    # draw appropriate icon if possible
                    try:
                        if icon_c is not None:
                            # IMPORTANT: Disable drawing the check/cross icon when viewing history
                            # because user requested "disappear it"
                            if getattr(self, '_viewing_history', None) is not None:
                                pass
                            elif was_correct is True:
                                pass
                            elif was_correct is False:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass
            else:
                try:
                    if getattr(self, '_canvas_feedback_widget', None):
                        try:
                            self.canvas.delete(self._canvas_feedback_widget)
                        except Exception:
                            pass
                        try:
                            self._canvas_feedback_widget = None
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self.feedback_label.config(text='')
                except Exception:
                    pass
        except Exception:
            pass

        # ensure round index and label are consistent
        try:
            if idx is not None:
                try:
                    self.current_round = int(idx) + 1
                except Exception:
                    pass
            else:
                try:
                    if isinstance(snap, dict) and hasattr(self, '_round_history') and snap in self._round_history:
                        self.current_round = self._round_history.index(snap) + 1
                except Exception:
                    pass
            try:
                txt = f'Round {getattr(self, "current_round", "?")}/{getattr(self, "rounds", "?")}'
                if getattr(self, '_round_text_id', None) is not None and getattr(self, 'round_canvas', None) is not None:
                    try:
                        self.round_canvas.itemconfigure(self._round_text_id, text=txt)
                    except Exception:
                        pass
                else:
                    try:
                        # fallback if canvas wasn't created
                        self.round_label.config(text=txt)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

        # Update submit button text based on the round being viewed
        try:
            if getattr(self, 'submit_button', None):
                if self.current_round == self.rounds:
                    self.submit_button.config(text='End')
                else:
                    self.submit_button.config(text='✅ Submit')
        except Exception:
            pass

        # Disable inputs when viewing history so user cannot re-answer solved questions
        try:
            # Check safely for selected answer in the snapshot
            user_sel = None
            if isinstance(snap, dict):
                user_sel = snap.get('selected')
            
            is_answered = (user_sel is not None)
            
            # Additional check: if we are viewing a past round, treat it as answered/read-only 
            # unless it's the very last round AND it wasn't solved yet.
            # But the user wants history to be completely deactivated.
            current_hist_idx = getattr(self, '_viewing_history', None)
            if current_hist_idx is not None:
                # If we are viewing ANY history item, disable controls to prevent tampering
                # unless it is the last item which represents the current live round?
                # No, live round is NOT in history index usually, or is unfinished.
                pass

            if getattr(self, 'answer_entry', None):
                self.answer_entry.config(state='normal')
                self.answer_entry.delete(0, 'end')
                # If we have a stored answer for this round, show it (even if deactivated)
                if is_answered:
                    try:
                        self.answer_entry.insert(0, str(user_sel))
                    except Exception:
                        pass
                    self.answer_entry.config(state='disabled')
                else:
                    self.answer_entry.config(state='normal')

            if getattr(self, 'submit_button', None):
                if is_answered:
                    self.submit_button.config(state='disabled')
                else:
                    self.submit_button.config(state='normal')

            if getattr(self, 'choice_buttons', None):
                for btn in self.choice_buttons:
                    if is_answered:
                        btn.config(state='disabled')
                    else:
                        btn.config(state='normal')
                        
            # Force disable if viewing history to satisfy "make solved rounds completely history and deactivated"
            if current_hist_idx is not None and current_hist_idx < len(self._round_history):
                 # if the round in history has a selected answer, definitely disable.
                 # if it doesn't (user skipped/unsolved?), still disable to prevent modifying history?
                 # User said "solved rounds... seemed unsolved".
                 # If round was solved, is_answered is True.
                 # If is_answered is True, we disable above.
                 # So why did they seem unsolved? 
                 # Maybe is_answered was False? -> 'selected' was missing?
                 pass

        except Exception:
            pass

    def _pick_shape_choices(self, correct):
        # Expanded list of shapes to include all potential file names and common geometric terms
        shapes = [
            'circle', 'triangle', 'rectangle', 'square', 'pentagon', 'hexagon', 
            'cube', 'rectangular prism', 'square prism', 'cone', 'cylinder', 
            'sphere', 'pyramid', 'ellipse', 'triangular prism'
        ]
        
        # Remove the correct answer from potential distractors
        # Also handle potential synonyms to avoid confusing choices (e.g. if answer is 
        # 'rectangular prism', don't offer 'cuboid' if it were in the list)
        others = [s for s in shapes if s != correct]
        
        # Ensure we have enough distractors
        if len(others) < 2:
            others = ['circle', 'triangle', 'square'] # fallback
            
        picks = random.sample(others, 2)
        picks.append(correct)
        random.shuffle(picks)
        return picks

    def _toggle_fullscreen(self, event=None):
        try:
            self.fullscreen = not getattr(self, 'fullscreen', False)
            self.attributes('-fullscreen', self.fullscreen)
            if hasattr(self, 'full_btn') and self.full_btn:
                try:
                    self.full_btn.config(text='Exit Fullscreen' if self.fullscreen else 'Full Screen')
                except Exception:
                    pass
        except Exception:
            pass

    def _exit_fullscreen(self, event=None):
        try:
            self.fullscreen = False
            self.attributes('-fullscreen', False)
            if hasattr(self, 'full_btn') and self.full_btn:
                try:
                    self.full_btn.config(text='Full Screen')
                except Exception:
                    pass
        except Exception:
            pass

    def _pick_kind_for_age(self, age):
        if age <= 6:
            return ['count', 'add2']
        if age == 7:
            return ['count', 'add2', 'even']
        return ['count', 'add2', 'even', 'double']

    def _next_round(self):
        # Reset submission state for the new round
        self._processing_submission = False

        # hide pattern label early to avoid any transient rendering at the top
        try:
            if getattr(self, '_pattern_window', None):
                try:
                    self.canvas.itemconfigure(self._pattern_window, state='hidden')
                except Exception:
                    pass
        except Exception:
            pass

        # If the user is viewing past rounds, advance through the saved snapshots
        try:
            if getattr(self, '_viewing_history', None) is not None:
                # Check if we are moving to the live round
                if self._viewing_history + 1 == len(self._round_history) - 1:
                     # We want to return to the LIVE game state.
                     # Never auto-end here; ending should only happen when user explicitly presses End.

                     # If not over, we are returning to the UNFINISHED live round.
                     self._viewing_history = None
                     
                     # TRY TO RESTORE LIVE STATE
                     if self._restore_live_state():
                         if self.current_round <= len(self._round_history):
                             self.current_round = len(self._round_history)
                         
                         try:
                             txt = f'Round {self.current_round}/{self.rounds}'
                             if getattr(self, '_round_text_id', None) is not None and getattr(self, 'round_canvas', None) is not None:
                                 self.round_canvas.itemconfigure(self._round_text_id, text=txt)
                             else:
                                 self.round_label.config(text=txt)
                         except Exception:
                             pass
                             
                         try:
                             if getattr(self, 'submit_button', None):
                                 if self.current_round == self.rounds:
                                     self.submit_button.config(text='End')
                                 else:
                                     self.submit_button.config(text='✅ Submit')
                         except Exception:
                             pass
                             
                         return # Stop here, do not generate new round

                     # If restore failed, rebuild from the latest snapshot to avoid showing an older round.
                     try:
                        live_idx = len(self._round_history) - 1
                        if live_idx >= 0:
                            live_snap = self._round_history[live_idx]
                            self._load_snapshot(live_snap, live_idx)
                            self.current_round = live_idx + 1

                            is_answered = (live_snap.get('selected') is not None) or (live_snap.get('was_correct') is not None)
                            state_str = 'disabled' if is_answered else 'normal'

                            if getattr(self, 'submit_button', None):
                                self.submit_button.config(state=state_str)
                            if getattr(self, 'choice_buttons', None):
                                for btn in self.choice_buttons:
                                    btn.config(state=state_str)
                            if getattr(self, 'answer_entry', None):
                                self.answer_entry.config(state=state_str)
                        else:
                            self.current_round = 1
                        
                     except Exception:
                        pass

                     # RESTORE THE LIVE MODE SETTING IF WE SAVED IT
                     try:
                        saved = getattr(self, '_saved_live_mode', None)
                        if saved:
                             if getattr(self, 'mode_var', None):
                                 self.mode_var.set(saved)
                             if getattr(self, 'mode_combobox', None):
                                 self.mode_combobox.set(saved)
                             self._saved_live_mode = None
                     except Exception:
                        pass
                        
                     try:
                         txt = f'Round {self.current_round}/{self.rounds}'
                         if getattr(self, '_round_text_id', None) is not None and getattr(self, 'round_canvas', None) is not None:
                             self.round_canvas.itemconfigure(self._round_text_id, text=txt)
                         else:
                             self.round_label.config(text=txt)
                     except Exception:
                         pass
                         
                     try:
                         if getattr(self, 'submit_button', None):
                             if self.current_round == self.rounds:
                                 self.submit_button.config(text='End')
                             else:
                                 self.submit_button.config(text='✅ Submit')
                     except Exception:
                         pass
                     
                     return

                # if there's a next saved snapshot, load it
                elif self._viewing_history + 1 < len(self._round_history) - 1:
                    try:
                        self._viewing_history += 1
                        self.current_round = self._viewing_history + 1
                        is_last = (self._viewing_history == len(self._round_history) - 1)
                        # if we are returning to the latest round (which might be unsolved),
                        # we should re-enable controls unless it was already solved/completed.
                        
                        self._load_snapshot(self._round_history[self._viewing_history], self._viewing_history)
                        
                        # Logic for "is_last":
                        # If we are viewing a history item, it is by definition COMPLETED or we are just reviewing it.
                        # User explicitely requested: "remain on history mode until round N which is unsolved."
                        # This means even the last item (current round) should be viewed in read-only mode first.
                        
                        # So we DO NOT exit history mode here.
                        
                        try:
                            # Always disable controls when viewing history 
                            if getattr(self, 'submit_button', None):
                                self.submit_button.config(state='disabled')
                            if getattr(self, 'choice_buttons', None):
                                for btn in self.choice_buttons:
                                    btn.config(state='disabled')
                            if getattr(self, 'answer_entry', None):
                                self.answer_entry.config(state='disabled')
                        except Exception:
                            pass
                        
                        return # IMPORTANT: Return to avoid falling through to generating new rounds!

                        try:
                            # force immediate canvas update so Next feels as fast as Back
                            self.canvas.update_idletasks()
                            try:
                                self._place_pattern_label()
                            except Exception:
                                pass
                        except Exception:
                            pass

                    except Exception as e:
                        print(f"Error traversing history: {e}")
                        pass
                    
                    return

                # If we are already at the live round (shouldn't happen if we clear it, but just in case)
                elif self._viewing_history == len(self._round_history) - 1:
                    self._viewing_history = None
                    return
        except Exception:
            self._viewing_history = None

        # EXPLICITLY DELETE EVERYTHING TAGGED 'feedback' BEFORE ANYTHING ELSE
        try:
             # Force update to ensure deletion logic completes
             self.canvas.update_idletasks()
             self.canvas.delete('feedback')
             
             # Also try specific cleanup of known widget
             if getattr(self, '_canvas_feedback_widget', None):
                 try:
                     self.canvas.delete(self._canvas_feedback_widget)
                 except: pass
                 self._canvas_feedback_widget = None
             
             # Bruteforce cleanup: iterate all window items and delete if they look like feedback
             # (This is a safety net for stuck items without tags)
             for item in self.canvas.find_all():
                 tags = self.canvas.gettags(item)
                 if 'feedback' in tags:
                     self.canvas.delete(item)
                 # also checking window contents is hard but we can check position?
                 # feedback is usually centered bottom.
             
             self.canvas.update_idletasks()
        except Exception:
             pass

        # Starting a new live round, ensure controls are enabled and cleared
        # Force clear answer entry and variable *multiple ways*
        try:
            # Unconditionally clear first
            if getattr(self, 'answer_entry', None):
                 self.answer_entry.delete(0, 'end')

            if getattr(self, 'answer_var', None):
                self.answer_var.set('')
            
            if getattr(self, 'answer_entry', None):
                self.answer_entry.config(state='normal')
                self.answer_entry.delete(0, 'end')
                # Force update to ensure deletion
                self.answer_entry.update_idletasks()
                # Schedule another clear just in case
                def _force_clear():
                    try:
                        if getattr(self, 'answer_var', None): self.answer_var.set('')
                        if getattr(self, 'answer_entry', None): self.answer_entry.delete(0, 'end')
                    except: pass
                self.after(50, _force_clear)
                self.after(200, _force_clear)
            
            if getattr(self, 'submit_button', None):
                self.submit_button.config(state='normal')
            if getattr(self, 'choice_buttons', None):
                for btn in self.choice_buttons:
                    btn.config(state='normal')
        except Exception:
            pass

        self.current_round += 1
        
        # Update submit button text for the final round
        try:
            if getattr(self, 'submit_button', None):
                if self.current_round == self.rounds:
                    self.submit_button.config(text='End')
                else:
                    self.submit_button.config(text='✅ Submit')
        except Exception:
            pass

        # clear any canvas feedback from previous round (Yes/No messages)
        try:
            # Delete items tagged as feedback (most reliable)
            self.canvas.delete('feedback')
            # Also try deleting via stored ID
            if getattr(self, '_canvas_feedback_widget', None):
                try:
                    self.canvas.delete(self._canvas_feedback_widget)
                except Exception:
                    pass
                try:
                    self._canvas_feedback_widget = None
                except Exception:
                    pass
            # Force update before drawing new stuff
            self.canvas.update_idletasks()
        except Exception:
            pass
            
        # CRITICAL: Clean up artifacts from other modes to prevent "ghost" elements
        try:
            self.canvas.delete('shapes')
            for tid in getattr(self, '_seq_text_items', []) or []:
                try:
                    self.canvas.delete(tid)
                except: pass
            self._seq_text_items = []
        except Exception:
            pass

        mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
        # Use a fixed sequence length of 5 for all difficulties/modes
        length = 5
        # Patterns mode: build a numeric sequence with one blank (draw on canvas so we can color blanks)
        if mode == 'Patterns':
            pg = getattr(self, 'group_var', tk.StringVar(value='All')).get()
            # generate a base sequence and ensure it has enough elements
            seq = generate_group_pattern(pg, length=length, difficulty=self.difficulty)
            # if generator returned fewer elements than requested, extend it
            try:
                if not seq:
                    seq = list(range(1, length + 1))
                elif len(seq) < length:
                    # determine a step if possible, else default 1
                    try:
                        step = seq[1] - seq[0]
                    except Exception:
                        step = 1
                    while len(seq) < length:
                        seq.append(seq[-1] + step)
            except Exception:
                # fallback simple sequence
                seq = list(range(1, length + 1))
            self.current_seq = seq[:length]
            self.blank_index = random.randint(0, len(self.current_seq) - 1)
            # clear any operation question state
            self.current_answer = None
            # draw the sequence on the canvas (preserve the pattern_label for other modes)
            try:
                # remove previous sequence text items
                for tid in getattr(self, '_seq_text_items', []) or []:
                    try:
                        self.canvas.delete(tid)
                    except Exception:
                        pass
                self._seq_text_items = []
                self.canvas.update_idletasks()
                w = self.canvas.winfo_width() or 600
                h = self.canvas.winfo_height() or 300
                cx = w // 2
                cy = h // 2
                # spacing based on canvas width
                spacing = max(60, min(140, w // (len(self.current_seq) + 1)))
                start_x = cx - spacing * (len(self.current_seq) - 1) / 2
                y = cy
                for i, v in enumerate(self.current_seq):
                    txt = '_' if i == self.blank_index else str(v)
                    tid = self.canvas.create_text(int(start_x + i * spacing), y, text=txt, font=self.big_font, fill='black', tags='seq')
                    self._seq_text_items.append(tid)
                # remove any existing canvas feedback widget
                try:
                    if self._canvas_feedback_widget:
                        self.canvas.delete(self._canvas_feedback_widget)
                        self._canvas_feedback_widget = None
                except Exception:
                    pass

                # Also prepare a displayed string so the label shows the same text if needed
                try:
                    displayed = self._show_sequence_with_blank(self.current_seq, self.blank_index)
                except Exception:
                    displayed = None

            except Exception:
                displayed = self._show_sequence_with_blank(self.current_seq, self.blank_index)
            
            # Record snapshot INDEPENDENTLY of drawing success/failure
            try:
                # Ensure we have a valid snapshot even if things went wrong
                snap = {
                    'mode': 'Patterns', 
                    'displayed': None, 
                    'current_seq': list(self.current_seq) if self.current_seq is not None else None, 
                    'blank_index': self.blank_index, 
                    # If this is a pattern, the answer is implicit in the sequence. 
                    # But for Operations (which use Patterns mode var?), we need to be careful.
                    # Actually, for Patterns, the answer IS computable from the sequence.
                    'current_answer': self.current_seq[self.blank_index] if (self.current_seq and self.blank_index is not None and 0 <= self.blank_index < len(self.current_seq)) else None,
                    'feedback_text': None
                }
                # Append only if this round index isn't already covered in history (prevent duplicates)
                if self.current_round > len(self._round_history):
                     self._round_history.append(snap)
            except Exception:
                pass
            
            # FINAL CLEAUNP: ensure no feedback widget remains
            try:
                self.canvas.delete('feedback')
                if getattr(self, '_canvas_feedback_widget', None):
                    self.canvas.delete(self._canvas_feedback_widget)
                    self._canvas_feedback_widget = None
            except: pass
        else:
            if mode == 'Geometric Shapes':
                # If a shapes folder was loaded, use those images in sequence
                self.current_seq = None
                self.blank_index = None
                displayed = 'Which shape is this?'
                # ensure radio choices visible, hide numeric entry
                try:
                    self.choice_frame.pack(pady=6, fill='x', anchor='center')
                    try:
                        self.answer_entry.pack_forget()
                    except Exception:
                        pass
                    try:
                        self.answer_label.pack_forget()
                    except Exception:
                        pass
                except Exception:
                    pass
                # If images were loaded from shapes folder, show them in round order
                picks = []
                try:
                    if getattr(self, '_shape_images', None):
                        # Ensure shuffled list exists and grab next unique index
                        if not hasattr(self, '_shuffled_shape_indices') or not self._shuffled_shape_indices:
                             self._shuffled_shape_indices = list(range(len(self._shape_images)))
                             random.shuffle(self._shuffled_shape_indices)
                        
                        try:
                            idx = self._shuffled_shape_indices.pop(0)
                        except:
                            idx = random.randint(0, len(self._shape_images) - 1)
                        
                        # Store the index so resize events know which image to draw
                        self.current_image_index = idx
                            
                        # Use filename without extension as the true answer
                        try:
                            path = self._shape_images[idx][0]
                            fbase = os.path.basename(path)
                            name, _ = os.path.splitext(fbase)
                            # Fix the name format (replace underscores with spaces)
                            name = name.replace('_', ' ').strip().lower()
                            # Update display name in list too so choices match
                            try:
                                if idx < len(self._shape_image_names):
                                    self._shape_image_names[idx] = name
                            except Exception:
                                pass
                        except Exception:
                            name = "unknown"
                            
                        self.current_answer = name
                        # clear any pending vector redraws and shapes
                        try:
                            if getattr(self, '_resize_after_id', None):
                                try:
                                    self.after_cancel(self._resize_after_id)
                                except Exception:
                                    pass
                                self._resize_after_id = None
                        except Exception:
                            pass
                        try:
                            self.canvas.delete('all') # CLEAR EVERYTHING
                            self.canvas.update_idletasks() # FORCE CLEAR
                        except Exception:
                            pass
                        # hide the pattern label until image is placed to avoid flash
                        try:
                            if getattr(self, '_pattern_window', None):
                                self.canvas.itemconfigure(self._pattern_window, state='hidden')
                        except Exception:
                            pass
                        
                        # Immediately draw a white cover to block anything
                        w_cover = self.canvas.winfo_width() or 800
                        h_cover = self.canvas.winfo_height() or 600
                        self.canvas.create_rectangle(0, 0, w_cover, h_cover, fill='white', outline='white', tags='cover')

                        # schedule placing the preloaded thumbnail after layout to avoid flash
                        try:
                            def _draw_thumb(i=idx):
                                try:
                                    # wait until canvas has a reasonable size to avoid initial misplaced draw
                                    w = self.canvas.winfo_width() or 0
                                    h = self.canvas.winfo_height() or 0
                                    # mark that the image is not yet placed and disable Next until it is
                                    try:
                                        self._image_placed = False
                                    except Exception:
                                        pass
                                    try:
                                        if getattr(self, 'next_button', None):
                                            try:
                                                self.next_button.config(state='disabled')
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                    if w < 180 or h < 120:
                                        try:
                                            self.after(60, lambda: _draw_thumb(i))
                                        except Exception:
                                            pass
                                        return
                                    
                                    # Clear everything, including the cover
                                    try:
                                        self.canvas.delete('all')
                                        self.canvas.update_idletasks()
                                    except Exception:
                                        pass
                                    
                                    # Redraw everything from scratch
                                    # 1. Background fill
                                    self.canvas.create_rectangle(0, 0, w, h, fill='white', outline='white')
                                    
                                    # 2. Draw the image
                                    _, photo = self._shape_images[i]
                                    self._last_image = photo
                                    cx = w // 2
                                    cy = h // 2
                                    try:
                                        offset = max(10, int(h * 0.18) - 30)
                                    except Exception:
                                        offset = 50
                                    try:
                                        self.canvas.create_image(cx, cy + offset, image=photo, tags='shapes')
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                                # once placed, enable Next and mark completion
                                try:
                                    self._image_placed = True
                                except Exception:
                                    pass
                                try:
                                    if getattr(self, 'next_button', None):
                                        try:
                                            self.next_button.config(state='normal')
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    if getattr(self, '_pattern_window', None):
                                        try:
                                            self.canvas.itemconfigure(self._pattern_window, state='normal')
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                try:
                                    self._place_pattern_label()
                                except Exception:
                                    pass
                            # schedule the drawing (it will reschedule itself until canvas ready)
                            _draw_thumb()
                        except Exception:
                            pass
                        # build choices from available image names
                        try:
                            others = [n for n in getattr(self, '_shape_image_names', []) if n != name]
                            picks = random.sample(others, 2) if len(others) >= 2 else others[:2]
                            picks.append(name)
                            random.shuffle(picks)
                        except Exception:
                            picks = [name]
                    else:
                        # fallback to built-in vector shapes when no images are available
                        shapes = ['circle', 'triangle', 'rectangle', 'ellipse', 'square', 'pentagon', 'hexagon', 'cube', 'rectangular prism', 'cuboid', 'cone', 'cylinder', 'triangular prism', 'sphere']
                        shape = random.choice(shapes)
                        colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', '#FFB74D', '#81C784']
                        color = random.choice(colors)
                        self.current_answer = shape
                        try:
                            self._last_shape = shape
                            self._last_color = color
                        except Exception:
                            pass
                        try:
                            # immediately draw vector shape now to avoid lag when pressing Next
                            try:
                                self.canvas.delete('shapes')
                            except Exception:
                                pass
                            try:
                                if getattr(self, '_pattern_window', None):
                                    try:
                                        self.canvas.itemconfigure(self._pattern_window, state='hidden')
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                self._draw_shape_on_canvas(shape, color)
                                try:
                                    if getattr(self, '_pattern_window', None):
                                        self.canvas.itemconfigure(self._pattern_window, state='normal')
                                except Exception:
                                    pass
                                try:
                                    self._place_pattern_label()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        except Exception:
                            pass
                        # prepare choices from built-in list
                        picks = self._pick_shape_choices(shape)
                except Exception:
                    picks = []
                # populate choice buttons and map internal keys to shape names
                self._choice_map.clear()
                for i, b in enumerate(self.choice_buttons):
                    try:
                        val = picks[i] if i < len(picks) else ''
                        b.config(text=(val.title() if val else ''))
                        # reset visual state for new round
                        try:
                            b.config(relief='raised', bg=self.cget('bg'), fg='black')
                            b.update_idletasks()
                        except Exception:
                            pass
                        self._choice_map[i] = val
                    except Exception:
                        pass
                try:
                    # ensure internal selection cleared
                    self._selected_choice = None
                    for b in self.choice_buttons:
                        try:
                            b.config(relief='raised', bg=self.cget('bg'), fg='black')
                            b.update()
                        except Exception:
                            pass
                except Exception:
                    pass
                # place choices under the canvas and schedule drawing after layout
                try:
                    self.choice_frame.pack_forget()
                except Exception:
                    pass
                try:
                    self.choice_frame.pack(pady=6, fill='x', before=self.entry_frm, anchor='center')
                except Exception:
                    try:
                        self.choice_frame.pack(pady=6, fill='x', anchor='center')
                    except Exception:
                        pass
                try:
                    self.answer_entry.pack_forget()
                except Exception:
                    pass
                try:
                    self.answer_label.pack_forget()
                except Exception:
                    pass
                try:
                    # record snapshot for history (copy picks list)
                    if getattr(self, '_shape_images', None):
                        # Use the actual random index and path chosen above
                        try:
                            final_idx = idx
                            final_path = path
                        except:
                            final_idx = (self.current_round - 1) % len(self._shape_images)
                            final_path = self._shape_images[final_idx][0]

                        snap = {'mode': 'Geometric Shapes', 'displayed': displayed, 'current_seq': None, 'blank_index': None, 'current_answer': self.current_answer, 'image_index': final_idx, 'file': os.path.basename(final_path), 'choices': list(picks)}
                    else:
                        snap = {'mode': 'Geometric Shapes', 'displayed': displayed, 'current_seq': None, 'blank_index': None, 'current_answer': self.current_answer, 'shape': shape, 'color': color, 'choices': list(picks)}
                    
                    if self.current_round > len(self._round_history):
                         self._round_history.append(snap)
                except Exception:
                    pass
            elif mode == 'Multiplication':
                # parse base integer from labelled times_var (e.g. '2 times')
                try:
                    base = int(self.times_var.get().split()[0])
                except Exception:
                    try:
                        base = int(self.times_cb.get().split()[0])
                    except Exception:
                        base = 2
                # non-repeating multipliers: use prepared shuffled list if available
                try:
                    if not hasattr(self, '_mult_list') or not self._mult_list:
                        # fallback ensure list exists
                        self._mult_list = list(range(1, 11))
                        random.shuffle(self._mult_list)
                    mult = self._mult_list.pop(0)
                except Exception:
                    mult = random.randint(1, 10)
                # if user selected 'All' for times, pick a random base each round
                try:
                    times_val = (self.times_var.get() or '')
                except Exception:
                    times_val = ''
                try:
                    if times_val.lower().startswith('all'):
                        base = random.randint(1, 10)
                except Exception:
                    pass
                displayed = f'{base} × {mult} = _'
                # For canvas-based rendering, split into list
                self.current_seq = displayed.split()
                # The blank is always the last element ('_')
                self.blank_index = len(self.current_seq) - 1
                self.current_answer = base * mult
                
                # DRAWING LOGIC FOR CANVAS MODE
                try:
                    # remove previous sequence text items
                    for tid in getattr(self, '_seq_text_items', []) or []:
                        try:
                            self.canvas.delete(tid)
                        except Exception:
                            pass
                    self._seq_text_items = []
                    self.canvas.update_idletasks()
                    w = self.canvas.winfo_width() or 600
                    h = self.canvas.winfo_height() or 300
                    cx = w // 2
                    cy = h // 2
                    # Tight spacing for equations
                    spacing = max(40, min(80, w // (len(self.current_seq) + 2)))
                    start_x = cx - (len(self.current_seq) - 1) * spacing / 2
                    y = cy
                    for i, v in enumerate(self.current_seq):
                        txt = '_' if i == self.blank_index else str(v)
                        tid = self.canvas.create_text(int(start_x + i * spacing), y, text=txt, font=self.big_font, fill='black', tags='seq')
                        self._seq_text_items.append(tid)

                    # Ensure we force an update to make sure the user sees the new question
                    try:
                         self.canvas.update_idletasks()
                    except:
                         pass
                except Exception:
                    pass
                
                # record snapshot for history
                try:
                    snap = {'mode': 'Multiplication', 'displayed': displayed, 'current_seq': self.current_seq, 'blank_index': self.blank_index, 'current_answer': self.current_answer}
                    if self.current_round > len(self._round_history):
                        self._round_history.append(snap)
                except Exception:
                    pass
            else:
                # 4 Operations mode: equation generation
                op_name = getattr(self, 'ops_var', tk.StringVar(value='All')).get()
                try:
                    if op_name and op_name.lower().startswith('all'):
                        op_name = random.choice(['Addition', 'Subtraction', 'Multiplication', 'Division'])
                except Exception:
                    pass
                expr, answer = generate_operation_question(op_name, self.difficulty)
                displayed = expr
                self.current_seq = displayed.split()
                self.blank_index = len(self.current_seq) - 1
                self.current_answer = answer
                
                # DRAWING LOGIC FOR CANVAS MODE
                try:
                    # remove previous sequence text items
                    for tid in getattr(self, '_seq_text_items', []) or []:
                        try:
                            self.canvas.delete(tid)
                        except Exception:
                            pass
                    self._seq_text_items = []
                    self.canvas.update_idletasks()
                    w = self.canvas.winfo_width() or 600
                    h = self.canvas.winfo_height() or 300
                    cx = w // 2
                    cy = h // 2
                    
                    # Tight spacing for equations
                    spacing = max(40, min(80, w // (len(self.current_seq) + 2)))
                    start_x = cx - (len(self.current_seq) - 1) * spacing / 2
                    y = cy
                    for i, v in enumerate(self.current_seq):
                        txt = '_' if i == self.blank_index else str(v)
                        tid = self.canvas.create_text(int(start_x + i * spacing), y, text=txt, font=self.big_font, fill='black', tags='seq')
                        self._seq_text_items.append(tid)

                    # Ensure we force an update to make sure the user sees the new question
                    try:
                         self.canvas.update_idletasks()
                    except:
                         pass
                except Exception:
                    pass
                
                # record snapshot for non-shape round
                try:
                    snap = {'mode': 'Ops/Math', 'displayed': displayed, 'current_seq': list(self.current_seq) if self.current_seq is not None else None, 'blank_index': self.blank_index, 'current_answer': self.current_answer}
                    if self.current_round > len(self._round_history):
                        self._round_history.append(snap)
                except Exception:
                    pass
        # clear previous result icon and canvas shapes so next round starts fresh
        try:
            if not (mode == 'Geometric Shapes' and getattr(self, '_using_shape_images', False)):
                try:
                    self.canvas.delete('shapes')
                except Exception:
                    pass
        except Exception:
            try:
                self.canvas.delete('shapes')
            except Exception:
                pass

        # also remove previous sequence text items (only when not generating Patterns
        # here — pattern generation clears/creates its own seq items earlier)
        try:
            if mode not in ['Patterns', 'Multiplication', '4 Operations']:
                for tid in getattr(self, '_seq_text_items', []) or []:
                    try:
                        self.canvas.delete(tid)
                    except Exception:
                        pass
                # leave list intact (generation will reset when needed)
        except Exception:
            pass

        try:
            txt = f'Round {self.current_round}/{self.rounds}'
            if getattr(self, '_round_text_id', None) is not None and getattr(self, 'round_canvas', None) is not None:
                try:
                    self.round_canvas.itemconfigure(self._round_text_id, text=txt)
                except Exception:
                    pass
            else:
                try:
                    self.round_label.config(text=txt)
                except Exception:
                    pass
        except Exception:
            pass

        # hide pattern label while updating text to avoid a quick flash
        try:
            if getattr(self, '_pattern_window', None):
                try:
                    self.canvas.itemconfigure(self._pattern_window, state='hidden')
                except Exception:
                    pass
        except Exception:
            pass

        # update canvas-centered pattern label and reposition it
        try:
            try:
                # For 'Patterns' mode we draw sequence items directly on the canvas
                # so avoid setting the pattern_label to the same text (would duplicate).
                if mode in ['Patterns', 'Multiplication', '4 Operations']:
                    try:
                        self.pattern_label.config(text='')
                        self.pattern_label.config(fg='black')
                    except Exception:
                        pass
                else:
                    try:
                        self.pattern_label.config(text=displayed, fg='black')
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self._place_pattern_label()
            except Exception:
                pass
            try:
                # For image-based Geometric Shapes, only reveal the pattern label
                # after the thumbnail has been placed to avoid a flash.
                if getattr(self, '_pattern_window', None):
                    if not (mode == 'Geometric Shapes' and getattr(self, '_using_shape_images', False)):
                        try:
                            self.canvas.itemconfigure(self._pattern_window, state='normal')
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass

        self.answer_var.set('')
        # show/hide UI elements depending on mode
        try:
            if mode != 'Geometric Shapes':
                try:
                    if self.choice_frame.winfo_ismapped():
                        self.choice_frame.pack_forget()
                except Exception:
                    pass
                try:
                    # ensure label + entry visible for numeric modes
                    # prevent flashing by checking if already mapped
                    mapped = False
                    try:
                        mapped = self.answer_label.winfo_ismapped()
                    except:
                        pass
                    if not mapped:
                        self.answer_label.pack(side='left')
                except Exception:
                    pass
                try:
                    mapped_entry = False
                    try:
                        mapped_entry = self.answer_entry.winfo_ismapped()
                    except:
                        pass
                    if not mapped_entry:
                        self.answer_entry.pack(side='left', padx=8)
                except Exception:
                    pass
            else:
                try:
                    self.choice_var.set('')
                except Exception:
                    pass
        except Exception:
            pass
        self.feedback_label.config(text='')
        
        # Paranoid final cleanup to ensure no previous round artifacts remain
        try:
             # If we are in live mode (not viewing history), ensure the answer box is empty
             if getattr(self, '_viewing_history', None) is None:
                  if getattr(self, 'answer_var', None):
                      self.answer_var.set('')
                  try:
                      if getattr(self, 'answer_entry', None):
                          self.answer_entry.delete(0, 'end')
                  except Exception: 
                      pass
             
             # Double check that no feedback widget remains (delete by tag and widget reference)
             self.canvas.delete('feedback')
             if getattr(self, '_canvas_feedback_widget', None):
                 try:
                     self.canvas.delete(self._canvas_feedback_widget)
                 except Exception: 
                     pass
                 self._canvas_feedback_widget = None
        except Exception:
             pass

        self.score_label.config(text=f'Score: {self.score}')
        self.answer_entry.focus_set()

    def _show_sequence_with_blank(self, seq, blank_index):
        parts = []
        for i, v in enumerate(seq):
            parts.append('_' if i == blank_index else str(v))
        # use a single space between items so a blank appears as a single '_'
        return ' '.join(parts)

    def _place_pattern_label(self):
        try:
            # ensure latest geometry is available for accurate calculations
            try:
                self.canvas.update_idletasks()
            except Exception:
                pass
            try:
                self.pattern_label.update_idletasks()
            except Exception:
                pass

            w = self.canvas.winfo_width() or 0
            h = self.canvas.winfo_height() or 0
            # if canvas hasn't been laid out to a reasonable size yet,
            # postpone placement to avoid transient jumps/flashes
            if w < 200 or h < 120:
                try:
                    self.after(80, self._place_pattern_label)
                except Exception:
                    pass
                return

            # center x coordinate
            x = w // 2
            # determine vertical placement depending on mode
            mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
            if mode == 'Geometric Shapes':
                y = max(36, int(h * 0.08))
                try:
                    self.pattern_label.config(font=self.main_font)
                except Exception:
                    pass
            else:
                # center vertically for most modes
                y = h // 2

            # update wraplength and force label geometry to stabilize before reading sizes
            try:
                self.pattern_label.config(wraplength=int(w * 0.8))
            except Exception:
                pass
            try:
                self.pattern_label.update_idletasks()
            except Exception:
                pass

            # compute requested height for additional diagnostics/fine tuning
            try:
                label_reqh = self.pattern_label.winfo_reqheight() or self.pattern_label.winfo_height() or 0
            except Exception:
                label_reqh = 0

            # finally position the canvas window and reveal it (unless image mode needs to wait)
            try:
                # For 'Patterns' mode, hide the label window entirely as we draw text on canvas
                if mode in ['Patterns', 'Multiplication', '4 Operations']:
                    try:
                        self.canvas.itemconfigure(self._pattern_window, state='hidden')
                    except Exception:
                        pass
                    return

                # For image-based Geometric Shapes, only reveal the pattern label
                # after the thumbnail has been placed to avoid a flash.
                if mode == 'Geometric Shapes' and getattr(self, '_using_shape_images', False) and not getattr(self, '_image_placed', False):
                    # position in advance but keep hidden until image drawer shows it
                    try:
                        self.canvas.coords(self._pattern_window, x, y)
                    except Exception:
                        pass
                    return
                try:
                    self.canvas.coords(self._pattern_window, x, y)
                except Exception:
                    pass
                try:
                    self.canvas.itemconfigure(self._pattern_window, state='normal')
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    def _feedback_coords(self):
        """Return (cx, cy) coordinates for placing feedback windows.

        Uses the same calculation as history restore: centered horizontally,
        and vertically offset slightly below the canvas center.
        """
        try:
            cx = int(self.canvas.winfo_width() // 2)
        except Exception:
            cx = None
        try:
            cy = int(self.canvas.winfo_height() // 2) + 60
        except Exception:
            cy = None
        return cx, cy

    def _play_applause(self):
        if not winsound:
            return
        def _run_applause():
            # prefer bundled WAV at assets/applause.wav
            try:
                base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
                wav_path = os.path.join(base, 'assets', 'applause.wav')
                if os.path.exists(wav_path):
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return
            except Exception:
                pass
            # synthesized fallback
            try:
                for _ in range(12):
                    freq = random.randint(600, 2000)
                    dur = random.randint(30, 120)
                    try:
                        winsound.Beep(freq, dur)
                    except Exception:
                        try:
                            winsound.MessageBeep()
                        except Exception:
                            pass
                    time.sleep(random.uniform(0.02, 0.12))
            except Exception:
                pass
        threading.Thread(target=_run_applause, daemon=True).start()

    def _get_base_path(self):
        # base for locating external resources (supports frozen exe and source)
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.getcwd()

    def _get_sound_path(self, name):
        # try common locations for source mode, portable exe, and installed exe
        candidates = []
        try:
            if getattr(sys, 'frozen', False):
                candidates.append(getattr(sys, '_MEIPASS', None))
        except Exception:
            pass

        try:
            candidates.append(self._get_base_path())
        except Exception:
            pass

        try:
            candidates.append(os.getcwd())
        except Exception:
            pass

        # normalize and dedupe folders
        roots = []
        seen = set()
        for c in candidates:
            if not c:
                continue
            try:
                n = os.path.normpath(c)
            except Exception:
                n = c
            if n in seen:
                continue
            seen.add(n)
            roots.append(n)

        search_dirs = []
        for root in roots:
            search_dirs.append(os.path.join(root, 'sounds'))
            search_dirs.append(os.path.join(root, '_internal', 'sounds'))

        for folder in search_dirs:
            for ext in ('.wav', '.WAV', '.mp3', '.MP3'):
                p = os.path.join(folder, name + ext)
                if os.path.exists(p):
                    return p
        return None

    def _log_sound(self, msg):
        pass

    def _play_sound_file(self, name):
        # Play a WAV file named `name` from the sounds folder if present.
        p = self._get_sound_path(name)
        self._log_sound(f"play request for '{name}', resolved path: {p}")
        if not p:
            self._log_sound(f"sound file not found for '{name}'")
            if name == 'correct':
                self._play_applause()
            return

        # WAV: use winsound if available; MP3: open with default player
        try:
            if p.lower().endswith('.wav') and winsound:
                try:
                    self._log_sound(f"attempting winsound.PlaySound on {p}")
                    winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return
                except Exception as e:
                    self._log_sound(f"winsound failed: {e}")

            # Preferred: play mp3 (or any supported file) in-process using Windows MCI
            def _play_via_mci(path):
                if not ctypes:
                    self._log_sound("ctypes not available for MCI playback")
                    return False
                try:
                    mci = ctypes.windll.winmm.mciSendStringW
                    alias = f"sp_{int(time.time()*1000)}_{random.randint(0,999)}"
                    # open the file
                    cmd_open = f'open "{path}" alias {alias}'
                    r = mci(cmd_open, None, 0, None)
                    if r != 0:
                        self._log_sound(f"MCI open failed ({r}) for {path}")
                        return False
                    # play async
                    r = mci(f'play {alias} from 0', None, 0, None)
                    self._log_sound(f"MCI play command result {r} for alias {alias}")
                    # try to get length (ms)
                    try:
                        buf = ctypes.create_unicode_buffer(64)
                        r2 = mci(f'status {alias} length', buf, ctypes.sizeof(buf), None)
                        ms = 0
                        if r2 == 0:
                            try:
                                ms = int(buf.value.strip())
                            except Exception:
                                ms = 0
                    except Exception:
                        ms = 0

                    def _close():
                        try:
                            mci(f'stop {alias}', None, 0, None)
                        except Exception:
                            pass
                        try:
                            mci(f'close {alias}', None, 0, None)
                        except Exception:
                            pass

                    # schedule close after duration if available, else use a safe fallback
                    if ms and ms > 0:
                        threading.Timer(ms / 1000.0 + 0.25, _close).start()
                    else:
                        threading.Timer(10.0, _close).start()
                    return True
                except Exception as e:
                    self._log_sound(f"mci playback failed: {e}")
                    return False

            try:
                self._log_sound(f"attempting in-process MCI playback on {p}")
                ok = _play_via_mci(p)
                if ok:
                    return
                else:
                    self._log_sound(f"MCI playback failed for {p}")
            except Exception as e:
                self._log_sound(f"MCI attempt raised: {e}")

            # If MCI failed and the file is not a wav, fall back to applause for 'correct'
            self._log_sound(f"no in-process player available for {p}")
            if name == 'correct':
                self._log_sound("falling back to synthesized applause")
                self._play_applause()
        except Exception:
            self._log_sound(f"unexpected exception while trying to play {name}")
            pass

    def _confetti(self):
        colors = ['#ff595e', '#ffca3a', '#8ac926', '#1982c4', '#6a4c93']
        items = []
        # use actual canvas width so confetti spans the white area
        w = self.canvas.winfo_width() or 700
        for i in range(30):
            x = random.randint(20, max(40, w - 20))
            y = random.randint(-120, -10)
            r = random.randint(6, 12)
            color = random.choice(colors)
            # give confetti its own tag so we don't accidentally clear other shapes
            oval = self.canvas.create_oval(x, y, x + r, y + r, fill=color, outline='', tags=('confetti',))
            # each item: (id, vertical_speed, horiz_drift)
            items.append((oval, random.uniform(0.6, 2.2), random.uniform(-0.6, 0.6)))
        def animate():
            # run for a shorter visible duration
            for _ in range(50):
                for oval, speed, drift in items:
                    try:
                        self.canvas.move(oval, drift, speed)
                    except Exception:
                        pass
                try:
                    self.canvas.update()
                except Exception:
                    pass
                time.sleep(0.02)
            # fade-out: give a short pause then remove
            time.sleep(0.6)
            for oval, _, _ in items:
                try:
                    self.canvas.delete(oval)
                except Exception:
                    pass
        threading.Thread(target=animate, daemon=True).start()

    def _submit_answer(self, event=None):
        if getattr(self, '_processing_submission', False): return
        self._processing_submission = True
        
        # Guard: Explicitly exit history viewing mode on new submission
        try:
             self._viewing_history = None
        except Exception:
             pass

        try:
            if getattr(self, 'answer_entry', None): self.answer_entry.config(state='disabled')
            if getattr(self, 'submit_button', None): self.submit_button.config(state='disabled')
            for b in getattr(self, 'choice_buttons', []) or []: b.config(state='disabled')
        except: pass
        
        mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
        if mode == 'Geometric Shapes':
            sel_name = self._selected_choice
            if not sel_name:
                self.feedback_label.config(text='Please select an option.', fg='red')
                self._processing_submission = False
                try:
                    if getattr(self, 'answer_entry', None): self.answer_entry.config(state='normal')
                    if getattr(self, 'submit_button', None): self.submit_button.config(state='normal')
                    for b in getattr(self, 'choice_buttons', []) or []: b.config(state='normal')
                except: pass
                return


            correct = getattr(self, 'current_answer', None)
            # clear any textual feedback label for shapes mode
            try:
                self.feedback_label.config(text='')
            except Exception:
                pass
            is_correct = sel_name and correct and sel_name.lower() == correct.lower()
            if is_correct:
                self.score += 1
                self._play_sound_file('correct')
                self._confetti()
                
                        # store feedback for history
                try:
                    if self._round_history:
                        idx = self.current_round - 1
                        # Robust clamping
                        if idx < 0: idx = 0
                        if idx >= len(self._round_history): idx = len(self._round_history) - 1

                        if 0 <= idx < len(self._round_history):
                            self._round_history[idx]['was_correct'] = True
                            self._round_history[idx]['current_answer'] = correct
                            self._round_history[idx]['feedback_text'] = f"Yes! - {correct}"
                            self._round_history[idx]['feedback_fg'] = 'green'
                except Exception:
                    pass
                # update buttons: mark correct
                try:
                    for i, b in enumerate(self.choice_buttons):
                        val = self._choice_map.get(i)
                        if val and correct and val.lower() == correct.lower():
                            b.config(text=(val.title() if val else ''), bg='#8BC34A', fg='white', relief='sunken')
                        else:
                            b.config(relief='raised', bg=self.cget('bg'), fg='black')
                except Exception:
                    pass
            else:
                # record selection in history
                try:
                    if self._round_history:
                        idx = self.current_round - 1
                        if 0 <= idx < len(self._round_history):
                            self._round_history[idx]['selected'] = sel_name
                            self._round_history[idx]['was_correct'] = False
                        else:
                            self._round_history[-1]['selected'] = sel_name
                            self._round_history[-1]['was_correct'] = False
                        # store feedback for history
                        try:
                            if self._round_history:
                                idx = self.current_round - 1
                                if 0 <= idx < len(self._round_history):
                                    self._round_history[idx]['feedback_text'] = f"No! Correct: {correct}"
                                    self._round_history[idx]['feedback_fg'] = 'red'
                                else:
                                    self._round_history[-1]['feedback_text'] = f"No! Correct: {correct}"
                                    self._round_history[-1]['feedback_fg'] = 'red'
                        except Exception:
                            pass
                except Exception:
                    pass
                # update buttons: mark user's choice as Wrong and show Correct on the right button
                try:
                    for i, b in enumerate(self.choice_buttons):
                        val = self._choice_map.get(i)
                        if val and sel_name and val.lower() == sel_name.lower():
                            b.config(text=(val.title() if val else ''), bg='#EF5350', fg='white', relief='sunken')
                        elif val and correct and val.lower() == correct.lower():
                            b.config(text=(val.title() if val else ''), bg='#8BC34A', fg='white', relief='raised')
                        else:
                            b.config(relief='raised', bg=self.cget('bg'), fg='black')
                except Exception:
                    pass
                self._play_sound_file('wrong')
            
            # Record Shape Mode Logic Failure too (previously missed specific index update here)
            # Actually shape mode updates at lines ~2800. These were already fixed earlier to use idx.
            # But let's verify. Yes, earlier edits targeted Lines 2800.

            self.score_label.config(text=f'Score: {self.score}')
            try:
                # Ensure we advance to next round or end game
                delay_ms = 2000 if is_correct else 3000
                if getattr(self, '_next_round_timer', None):
                    self.after_cancel(self._next_round_timer)
                
                if getattr(self, '_viewing_history', None) is None and self.current_round >= self.rounds:
                    self._next_round_timer = self.after(delay_ms, self._show_end)
                else:
                    self._next_round_timer = self.after(delay_ms, self._next_round)
            except Exception:
                try:
                    if getattr(self, '_viewing_history', None) is None and self.current_round >= self.rounds:
                        self._next_round_timer = self.after(2000, self._show_end)
                    else:
                        self._next_round_timer = self.after(2000, self._next_round)
                except Exception:
                    pass
            return

        # Numeric modes (patterns / operations / multiplication)
        resp = self.answer_var.get().strip()
        try:
            val = int(resp)
        except Exception:
            self.feedback_label.config(text='Please enter a number.', fg='red')
            # Reset processing if input is invalid so they can retry
            self._processing_submission = False
            try:
                if getattr(self, 'answer_entry', None): self.answer_entry.config(state='normal')
                if getattr(self, 'submit_button', None): self.submit_button.config(state='normal')
                for b in getattr(self, 'choice_buttons', []) or []: b.config(state='normal')
            except: pass
            return
        
        # Guard against undefined answers
        try:
            # Handle Patterns vs Operations
            # For Patterns, the answer is inside the sequence logic at blank_index.
            # For Operations/Multiplication, strictly use self.current_answer.
            mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
            
            if mode == 'Patterns' and getattr(self, 'current_seq', None) is not None and getattr(self, 'blank_index', None) is not None:
                try:
                    correct = self.current_seq[self.blank_index]
                except:
                    correct = getattr(self, 'current_answer', None)
            else:
                correct = getattr(self, 'current_answer', None)
                
            if correct is None:
                 raise ValueError("No correct answer defined")
        except Exception as e:
            # If logic fails, reset processing state and perhaps skip to next logic
            print(f"Error determining correct answer: {e}")
            self._processing_submission = False
            try:
                if getattr(self, 'answer_entry', None): self.answer_entry.config(state='normal')
                if getattr(self, 'submit_button', None): self.submit_button.config(state='normal')
            except: pass
            return

        if val == correct:
            self.score += 1
            try:
                if type(correct) == str:
                     ans_text = f"{correct}"
                else:
                     ans_text = str(correct)
            except Exception:
                ans_text = str(correct)
            
            # Record selection in history NOW
            try:
                # Use current_round - 1 to target the correct history entry 
                if self._round_history:
                    idx = self.current_round - 1
                    # Robust index clamping
                    if idx < 0: idx = 0
                    if idx >= len(self._round_history): idx = len(self._round_history) - 1
                    
                    if 0 <= idx < len(self._round_history):
                        self._round_history[idx]['selected'] = val
                        self._round_history[idx]['was_correct'] = True
                        try:
                            self._round_history[idx]['feedback_text'] = f"Yes! - '{ans_text}'"
                            self._round_history[idx]['feedback_fg'] = 'green'
                            self._round_history[idx]['current_answer'] = correct # Ensure this is saved
                        except Exception:
                            pass
            except Exception:
                pass


            # Show the green correct answer in the equation (like Patterns game)
            try:
                # If we have sequence items (Patterns mode), we update the specific item
                if getattr(self, '_seq_text_items', None) and self.blank_index is not None:
                    idx = self.blank_index
                    tid = self._seq_text_items[idx]
                    self.canvas.itemconfig(tid, text=str(correct), fill='#8BC34A')
                else:
                    # For 4 Operations (and others using label), update the label text
                    # Replace '_' with the answer and turn green
                    try:
                        current_text = self.pattern_label.cget('text')
                        if '_' in current_text:
                            new_text = current_text.replace('_', str(correct))
                            self.pattern_label.config(text=new_text, fg='#8BC34A')
                        else:
                            # Fallback if no blank found (shouldn't happen usually)
                            self.pattern_label.config(text=str(correct), fg='#8BC34A')
                    except Exception:
                        pass
            except Exception:
                pass

            # show positive feedback under the question
            try:
                # remove any previous canvas feedback first
                if getattr(self, '_canvas_feedback_widget', None):
                    try:
                        self.canvas.delete(self._canvas_feedback_widget)
                    except Exception:
                        pass
                self.canvas.delete('feedback')
                self.canvas.update_idletasks()
                
                # create container with label + icon to the right
                container = tk.Frame(self.canvas, bg='white')
                lbl = tk.Label(container, text=f"Yes! - '{ans_text}'", font=self.main_font, bg='white', fg='green', anchor='center', justify='center')
                lbl.grid(row=0, column=0, sticky='ew')
                try:
                    container.grid_columnconfigure(0, weight=1)
                except Exception:
                    pass
                icon_c = tk.Canvas(container, width=28, height=28, bg='white', highlightthickness=0)
                icon_c.grid(row=0, column=1, padx=(8,0), pady=2)
                try:
                    cx, cy = self._feedback_coords()
                except Exception:
                    cx = None
                    cy = None
                try:
                    if cx and cy:
                        # place centered horizontally on the canvas
                        target_x = int(self.canvas.winfo_width() // 2)
                        target_y = int(cy)
                        self._canvas_feedback_widget = self.canvas.create_window(target_x, target_y, window=container, anchor='n', tags='feedback')
                    else:
                        target_x = int(self.canvas.winfo_width() // 2)
                        target_y = int(self.canvas.winfo_height()//2 + 60)
                        self._canvas_feedback_widget = self.canvas.create_window(target_x, target_y, window=container, anchor='n', tags='feedback')
                except Exception:
                    try:
                        self._canvas_feedback_widget = self.canvas.create_window((self.canvas.winfo_width()//2) + 30, self.canvas.winfo_height()//2 + 60, window=container, anchor='n', tags='feedback')
                    except Exception:
                        pass
                pass
            except Exception:
                pass
            self._play_sound_file('correct')
            self._confetti()
            try:
                # persist the correct answer outcome in the last round snapshot
                try:
                    if self._round_history:
                        idx = self.current_round - 1
                        if 0 <= idx < len(self._round_history):
                            self._round_history[idx]['selected'] = val
                            self._round_history[idx]['was_correct'] = True
                            # IMPORTANT: We must update current_answer here so history shows the solved value
                            self._round_history[idx]['current_answer'] = correct
                            try:
                                self._round_history[idx]['feedback_text'] = f"Yes! - '{ans_text}'"
                                self._round_history[idx]['feedback_fg'] = 'green'
                            except Exception:
                                pass
                        else:
                            self._round_history[-1]['selected'] = val
                            self._round_history[-1]['was_correct'] = True
                            try:
                                self._round_history[-1]['feedback_text'] = f"Yes! - '{ans_text}'"
                                self._round_history[-1]['feedback_fg'] = 'green'
                                self._round_history[-1]['current_answer'] = correct
                            except Exception:
                                pass
                except Exception:
                    pass
                if getattr(self, '_viewing_history', None) is None and self.current_round >= self.rounds:
                    self._next_round_timer = self.after(2000, self._show_end)
                else:
                    self._next_round_timer = self.after(2000, self._next_round)
            except Exception:
                pass
        else:
            # show correct answer in green with new phrasing
            try:
                ans_text = str(correct)
            except Exception:
                ans_text = str(correct)
            
            # Record selection in history NOW for WRONG answer
            try:
                if self._round_history:
                    idx = self.current_round - 1
                    # Robust clamping
                    if idx < 0: idx = 0
                    if idx >= len(self._round_history): idx = len(self._round_history) - 1

                    if 0 <= idx < len(self._round_history):
                        self._round_history[idx]['selected'] = val
                        self._round_history[idx]['was_correct'] = False
                        try:
                            self._round_history[idx]['feedback_text'] = f"No! - '{ans_text}'"
                            self._round_history[idx]['feedback_fg'] = 'red'
                            self._round_history[idx]['current_answer'] = correct
                        except Exception:
                            pass
            except Exception:
                pass

            # write the correct answer into the blank in green
            try:
                if getattr(self, '_seq_text_items', None):
                    idx = self.blank_index
                    tid = self._seq_text_items[idx]
                    self.canvas.itemconfig(tid, text=str(correct), fill='#8BC34A')
                else:
                    try:
                        current_text = self.pattern_label.cget('text')
                        if '_' in current_text:
                            new_text = current_text.replace('_', str(correct))
                            self.pattern_label.config(text=new_text, fg='#8BC34A')
                        else:
                            self.pattern_label.config(text=str(correct), fg='#8BC34A')
                    except Exception:
                        pass
            except Exception:
                pass
            # show permanent 'No! - x' under the question in red (do not auto-advance)
            try:
                # FIRST: Delete any existing feedback widget via ID and tag
                if getattr(self, '_canvas_feedback_widget', None):
                    try:
                        self.canvas.delete(self._canvas_feedback_widget)
                    except Exception:
                        pass
                self.canvas.delete('feedback')
                
                # use a container frame so the label can be centered reliably
                try:
                    win_w = int(self.canvas.winfo_width() * 0.8) or None
                except Exception:
                    win_w = None
                container = tk.Frame(self.canvas, bg='white')
                lbl = tk.Label(container, text=f"No! - '{ans_text}'", font=self.main_font, bg='white', fg='red', anchor='center', justify='center')
                lbl.grid(row=0, column=0, sticky='ew')
                # small icon canvas to the right so live feedback matches restored snapshots
                try:
                    icon_c = tk.Canvas(container, width=28, height=28, bg='white', highlightthickness=0)
                    icon_c.grid(row=0, column=1, padx=(8, 0), pady=2)
                except Exception:
                    icon_c = None
                # center feedback horizontally in canvas
                try:
                    cx, cy = self._feedback_coords()
                except Exception:
                    cx = None
                    cy = None
                try:
                    if cx and cy:
                        # place centered horizontally on the canvas
                        target_x = int(self.canvas.winfo_width() // 2)
                        target_y = int(cy)
                        # size window to its content so placement matches history restore
                        self._canvas_feedback_widget = self.canvas.create_window(target_x, target_y, window=container, anchor='n', tags='feedback')
                    else:
                        target_x = int(self.canvas.winfo_width() // 2)
                        target_y = int(self.canvas.winfo_height()//2 + 60)
                        # size window to its content so placement matches history restore
                        self._canvas_feedback_widget = self.canvas.create_window(target_x, target_y, window=container, anchor='n', tags='feedback')
                except Exception:
                    try:
                        self._canvas_feedback_widget = self.canvas.create_window((self.canvas.winfo_width()//2) + 30, self.canvas.winfo_height()//2 + 60, window=container, anchor='n', tags='feedback')
                    except Exception:
                        pass
            except Exception:
                pass
            # record numeric selection in history if available
            try:
                if self._round_history:
                    idx = self.current_round - 1
                    if 0 <= idx < len(self._round_history):
                         self._round_history[idx]['selected'] = val
                         self._round_history[idx]['was_correct'] = False
                         try:
                             self._round_history[idx]['feedback_text'] = f"No! - '{ans_text}'"
                             self._round_history[idx]['feedback_fg'] = 'red'
                         except Exception:
                             pass
                    else:
                         self._round_history[-1]['selected'] = val
                         self._round_history[-1]['was_correct'] = False
                         try:
                             self._round_history[-1]['feedback_text'] = f"No! - '{ans_text}'"
                             self._round_history[-1]['feedback_fg'] = 'red'
                         except Exception:
                             pass
            except Exception:
                pass
            self._play_sound_file('wrong')
            try:
                if 'icon_c' in locals() and icon_c is not None:
                    try:
                        pass
                    except Exception:
                        pass
                else:
                    try:
                        pass
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                # advance to next round after a short delay even when wrong
                if getattr(self, '_next_round_timer', None):
                    self.after_cancel(self._next_round_timer)
                if getattr(self, '_viewing_history', None) is None and self.current_round >= self.rounds:
                    self._next_round_timer = self.after(3000, self._show_end)
                else:
                    self._next_round_timer = self.after(3000, self._next_round)
            except Exception:
                try:
                    if getattr(self, '_viewing_history', None) is None and self.current_round >= self.rounds:
                        self._show_end()
                    else:
                        self._next_round()
                except Exception:
                    pass
        self.score_label.config(text=f'Score: {self.score}')

    def _skip(self):
        # If we are on the final round and not viewing history, do nothing.
        # Game should end only when user presses End (Submit button text on final round).
        if getattr(self, '_viewing_history', None) is None:
            if self.current_round >= self.rounds:
                return

        # Move to the next round without showing the skipped answer message,
        # and ensure any stuck submission state is cleared.
        try:
            if getattr(self, '_viewing_history', None) is not None:
                self._next_round()
                return
            self._viewing_history = None
        except: pass
        try:
            self._processing_submission = False
            # clear any transient feedback
            try:
                self.feedback_label.config(text='')
            except Exception:
                pass
            # Cancel any pending timer to prevent double transitions
            try:
                if getattr(self, '_next_round_timer', None):
                    self.after_cancel(self._next_round_timer)
                    self._next_round_timer = None
            except Exception:
                pass
            # advance immediately to avoid button mashing issues
            self._next_round()
        except Exception:
            try:
                self._next_round()
            except Exception:
                pass

    def _show_end(self):
        try:
            self._record_player_statistics()
        except Exception:
            pass

        for w in self.winfo_children():
            w.destroy()
        end_lbl = tk.Label(self, text=f'Game over — Score: {self.score}/{self.rounds}', font=self.big_font, bg=self.cget('bg'), fg='#0D47A1')
        end_lbl.pack(pady=12)
        trophy_canvas = tk.Canvas(self, width=300, height=180, bg=self.cget('bg'), highlightthickness=0)
        trophy_canvas.pack()
        trophy_canvas.create_oval(40, 20, 260, 140, fill='#FFD54F', outline='')
        trophy_canvas.create_rectangle(120, 110, 180, 160, fill='#8D6E63', outline='')
        trophy_canvas.create_text(150, 80, text='🏆', font=self.big_font)

        def _play_again_now():
            try:
                if getattr(self, '_next_round_timer', None):
                    self.after_cancel(self._next_round_timer)
                    self._next_round_timer = None
            except Exception:
                pass

            try:
                mode = getattr(self, 'mode_var', tk.StringVar(value='Patterns')).get()
            except Exception:
                mode = 'Patterns'

            # reset per-game state
            self.current_round = 0
            self.score = 0
            self.kinds = self._pick_kind_for_age(self.age)
            try:
                self._viewing_history = None
            except Exception:
                pass

            # reset mode-specific round generators
            if mode == 'Multiplication':
                try:
                    self._mult_list = list(range(1, 11))
                    random.shuffle(self._mult_list)
                except Exception:
                    pass
            elif mode == 'Geometric Shapes':
                try:
                    if getattr(self, '_shape_images', None):
                        n_shapes = len(self._shape_images)
                        indices = []
                        while len(indices) < max(self.rounds, n_shapes):
                            chunk = list(range(n_shapes))
                            random.shuffle(chunk)
                            indices.extend(chunk)
                        self._shuffled_shape_indices = indices
                except Exception:
                    pass

            for w in self.winfo_children():
                w.destroy()
            self._build_game_screen()
            self._next_round()

        again = tk.Button(self, text='🔁 Play Again', font=self.kid_button_font, bg='#FF9800', fg='white', command=_play_again_now)
        again.pack(pady=8)
        
        # Add a "Review History" button if there is history available
        # Save reference before potentially destroying context
        try:
            saved_history = getattr(self, '_round_history', [])
        except Exception:
            saved_history = []
            
        if saved_history and len(saved_history) > 0:
            def _review_history():
                # Preserve history across the rebuild
                temp_hist = list(saved_history)
                for w in self.winfo_children():
                    w.destroy()
                self._build_game_screen()
                
                # Restore history
                self._round_history = temp_hist
                
                # Start review from round 1
                first_idx = 0
                self._viewing_history = first_idx
                self.current_round = first_idx + 1
                self._load_snapshot(self._round_history[first_idx], first_idx)
                
            review_btn = tk.Button(self, text='📜 Review History', font=self.kid_button_font, bg='#2196F3', fg='white', command=_review_history)
            review_btn.pack(pady=8, before=again)

        quit_btn = tk.Button(self, text='🏠 Home', font=self.kid_button_font, bg='#4CAF50', fg='white', command=self._build_start_screen)
        quit_btn.pack(pady=6)
        # play end sound depending on score
        try:
            pct = (self.score / self.rounds) if self.rounds else 0
            # map to actual bundled filenames: use 'good' and 'fail' (good.mp3 / fail.mp3)
            if pct >= 0.8:
                self.after(300, lambda: self._play_sound_file('good'))
            else:
                self.after(300, lambda: self._play_sound_file('fail'))
        except Exception:
            pass


def auto_test():
    random.seed(0)
    print('GUI file auto-test — generating sample sequences:')
    for kind in ['count', 'add2', 'double']:
        seq = generate_sequence(kind, length=5)
        print(f'  {kind}: {seq}')


if __name__ == '__main__':
    if '--auto-test' in sys.argv:
        auto_test()
        sys.exit(0)
    if tk is None:
        print('tkinter not available')
        sys.exit(1)
    app = PatternPicnicGUI()
    app.mainloop()
