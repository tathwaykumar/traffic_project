"""
main.py  —  Smart Traffic Signal Optimization System
=====================================================
Tkinter GUI  |  run with:  python main.py

Layout (1060 × 700 px)
──────────────────────────────────────────────────────────────────────
 ┌─ HEADER (title + mode badge) ──────────────────────────────────────┐
 │                                                                      │
 ├─ LEFT PANEL (280 px) ──┬─ CANVAS (500 px) ──┬─ RIGHT PANEL (280 px)┤
 │  How it works legend   │  Intersection       │  Lane queue meters   │
 │  Mode explanation      │  animation          │  Signal timers       │
 │  Control buttons       │                     │  Live stats          │
 │                        │                     │  Vehicle legend      │
 ├────────────────────────┴────────────────────┴──────────────────────┤
 │  STATUS BAR (elapsed time + current action description)             │
 └──────────────────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import random

from simulation import Simulation, DIRECTIONS
from traffic_light import TrafficLight

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    'bg':        '#0f1923',   # deep navy background
    'panel':     '#162030',   # slightly lighter panel
    'card':      '#1e2d40',   # card / section bg
    'road':      '#253344',   # road surface
    'lane':      '#2e4055',   # lane marking area
    'stripe':    '#3a5068',   # dashed centre line
    'green':     '#00c96e',   # traffic green
    'red':       '#e84545',   # traffic red
    'amber':     '#f5a623',   # amber / warning
    'blue':      '#4da8ff',   # accent blue
    'purple':    '#b07aff',   # truck colour
    'orange':    '#ff7c2b',   # ambulance / emergency
    'text':      '#d4e8ff',   # main text
    'dim':       '#6a8caa',   # secondary text
    'border':    '#2a4060',   # border / separator
    'highlight': '#1a3050',   # hover / active bg
}

TICK_MS      = 100     # canvas refresh rate (ms)
SIM_DURATION = 60      # seconds per mode in comparison run


class TrafficApp(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title("Smart Traffic Signal Optimization System")
        self.configure(bg=C['bg'])
        self.resizable(False, False)

        self.sim      = Simulation(mode='normal')
        self.sim.on_tick_callback = self._on_tick
        self._snap    = {}
        self._running = False
        self._thread  = None

        self._build_ui()
        self._start_sim('normal')

    # =========================================================================
    # UI BUILD
    # =========================================================================

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg='#0a1520', height=52)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        tk.Label(hdr, text='🚦', font=('Segoe UI Emoji', 20),
                 bg='#0a1520', fg=C['green']).pack(side='left', padx=(16, 6), pady=10)
        tk.Label(hdr, text='Smart Traffic Signal Optimization System',
                 font=('Courier New', 15, 'bold'),
                 bg='#0a1520', fg=C['text']).pack(side='left')

        # Mode badge (top-right)
        badge_frame = tk.Frame(hdr, bg='#0a1520')
        badge_frame.pack(side='right', padx=16)
        tk.Label(badge_frame, text='CURRENT MODE:', font=('Courier New', 8),
                 bg='#0a1520', fg=C['dim']).pack(anchor='e')
        self._mode_lbl = tk.Label(badge_frame, text='NORMAL  (Fixed Timing)',
                                  font=('Courier New', 10, 'bold'),
                                  bg='#0a1520', fg=C['amber'])
        self._mode_lbl.pack(anchor='e')

        # ── Body (left | canvas | right) ──────────────────────────────────────
        body = tk.Frame(self, bg=C['bg'])
        body.pack(fill='both', expand=True, padx=0, pady=0)

        self._build_left(body)
        self._build_canvas(body)
        self._build_right(body)

        # ── Status bar ────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg='#0a1520', height=28)
        bar.pack(fill='x')
        bar.pack_propagate(False)

        self._elapsed_var = tk.StringVar(value='⏱  Elapsed: 0s')
        tk.Label(bar, textvariable=self._elapsed_var,
                 font=('Courier New', 8), fg=C['dim'], bg='#0a1520'
                 ).pack(side='left', padx=12)

        self._status_var = tk.StringVar(value='Simulation started in Normal mode.')
        tk.Label(bar, textvariable=self._status_var,
                 font=('Courier New', 8), fg=C['green'], bg='#0a1520'
                 ).pack(side='right', padx=12)

    # ── LEFT PANEL ────────────────────────────────────────────────────────────

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=C['panel'], width=275)
        left.pack(side='left', fill='y')
        left.pack_propagate(False)

        # Section: How It Works
        self._section(left, '❓  HOW IT WORKS')

        steps = [
            ('1', 'Vehicles arrive randomly in each lane queue.'),
            ('2', 'Only the GREEN lane can let vehicles through.'),
            ('3', 'Normal: each lane gets 10 s green in order.'),
            ('4', 'Smart: busiest lane gets longer green time.'),
            ('5', '🚨 Ambulance skips the queue immediately.'),
        ]
        for num, text in steps:
            row = tk.Frame(left, bg=C['panel'])
            row.pack(fill='x', padx=12, pady=2)
            tk.Label(row, text=num, font=('Courier New', 8, 'bold'),
                     bg=C['card'], fg=C['blue'], width=2, relief='flat'
                     ).pack(side='left', padx=(0, 6))
            tk.Label(row, text=text, font=('Courier New', 8),
                     fg=C['text'], bg=C['panel'], wraplength=200,
                     justify='left', anchor='w'
                     ).pack(side='left', fill='x')

        # Section: Mode explanation cards
        self._section(left, '🔀  MODE COMPARISON')

        # Normal card
        norm = tk.Frame(left, bg=C['card'], relief='flat')
        norm.pack(fill='x', padx=12, pady=4)
        tk.Label(norm, text='▶  NORMAL MODE',
                 font=('Courier New', 8, 'bold'), fg=C['amber'],
                 bg=C['card']).pack(anchor='w', padx=8, pady=(6, 0))
        tk.Label(norm,
                 text='Fixed 10-second green for each lane\n'
                      'in rotation: N → S → E → W → repeat.\n'
                      'Simple but ignores actual traffic.',
                 font=('Courier New', 7), fg=C['dim'],
                 bg=C['card'], justify='left'
                 ).pack(anchor='w', padx=8, pady=(2, 6))

        # Smart card
        smart = tk.Frame(left, bg=C['card'], relief='flat')
        smart.pack(fill='x', padx=12, pady=4)
        tk.Label(smart, text='⚡  SMART MODE',
                 font=('Courier New', 8, 'bold'), fg=C['green'],
                 bg=C['card']).pack(anchor='w', padx=8, pady=(6, 0))
        tk.Label(smart,
                 text='Green time ∝ queue size (5–20 s).\n'
                      'Busiest lane gets priority — fewer\n'
                      'vehicles wait longer unnecessarily.',
                 font=('Courier New', 7), fg=C['dim'],
                 bg=C['card'], justify='left'
                 ).pack(anchor='w', padx=8, pady=(2, 6))

        # Section: Controls
        self._section(left, '🎮  CONTROLS')

        btns = [
            ('▶  Start Normal Mode',  C['amber'],  lambda: self._start_sim('normal')),
            ('⚡  Start Smart Mode',   C['green'],  lambda: self._start_sim('smart')),
            ('⏸  Pause / Resume',     C['blue'],   self._toggle_pause),
            ('🚨  Spawn Ambulance',    C['orange'], self._spawn_ambulance),
            ('📊  Compare Both Modes', C['blue'],   self._show_comparison),
            ('↺  Reset',              C['dim'],    self._reset_sim),
        ]
        for label, color, cmd in btns:
            b = tk.Button(left, text=label, fg=color, bg=C['card'],
                          font=('Courier New', 8, 'bold'),
                          activebackground=C['highlight'], activeforeground=color,
                          bd=0, pady=5, cursor='hand2', command=cmd,
                          relief='flat')
            b.pack(fill='x', padx=12, pady=2)

    # ── CANVAS (intersection) ─────────────────────────────────────────────────

    def _build_canvas(self, parent):
        wrap = tk.Frame(parent, bg=C['bg'])
        wrap.pack(side='left', padx=0)

        self._canvas = tk.Canvas(wrap, width=500, height=620,
                                 bg=C['bg'], highlightthickness=0)
        self._canvas.pack()

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=C['panel'], width=275)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)

        # Section: Lane queue meters
        self._section(right, '🚗  LANE QUEUES  (vehicles waiting)')

        self._lane_widgets = {}
        for d in DIRECTIONS:
            card = tk.Frame(right, bg=C['card'])
            card.pack(fill='x', padx=12, pady=3)

            # Direction label
            top = tk.Frame(card, bg=C['card'])
            top.pack(fill='x', padx=8, pady=(5, 2))
            tk.Label(top, text=d, font=('Courier New', 9, 'bold'),
                     fg=C['text'], bg=C['card'], width=6, anchor='w'
                     ).pack(side='left')
            count_lbl = tk.Label(top, text='0 vehicles',
                                 font=('Courier New', 8), fg=C['dim'],
                                 bg=C['card'])
            count_lbl.pack(side='right')

            # Progress bar
            bar_bg = tk.Frame(card, bg=C['lane'], height=10)
            bar_bg.pack(fill='x', padx=8, pady=(0, 4))
            bar_bg.pack_propagate(False)
            bar_fill = tk.Frame(bar_bg, bg=C['blue'], height=10)
            bar_fill.place(x=0, y=0, width=0, relheight=1)

            # Signal indicator dot + timer
            bot = tk.Frame(card, bg=C['card'])
            bot.pack(fill='x', padx=8, pady=(0, 5))
            dot = tk.Label(bot, text='●', font=('Courier New', 10),
                           fg=C['red'], bg=C['card'])
            dot.pack(side='left')
            timer_lbl = tk.Label(bot, text='RED  —  waiting',
                                 font=('Courier New', 7), fg=C['red'],
                                 bg=C['card'])
            timer_lbl.pack(side='left', padx=4)

            self._lane_widgets[d] = {
                'count': count_lbl,
                'fill':  bar_fill,
                'bar':   bar_bg,
                'dot':   dot,
                'timer': timer_lbl,
            }

        # Section: Live statistics
        self._section(right, '📈  LIVE STATISTICS')

        stats_card = tk.Frame(right, bg=C['card'])
        stats_card.pack(fill='x', padx=12, pady=4)
        self._stat_labels = {}
        rows = [
            ('total_spawned', '🚘  Total vehicles spawned'),
            ('total_cleared', '✅  Vehicles cleared'),
            ('avg_wait',      '⏳  Avg waiting time (s)'),
            ('throughput',    '📊  Throughput (veh / min)'),
        ]
        for key, label in rows:
            r = tk.Frame(stats_card, bg=C['card'])
            r.pack(fill='x', padx=8, pady=3)
            tk.Label(r, text=label, font=('Courier New', 7),
                     fg=C['dim'], bg=C['card'], anchor='w'
                     ).pack(side='left')
            v = tk.Label(r, text='0', font=('Courier New', 9, 'bold'),
                         fg=C['text'], bg=C['card'])
            v.pack(side='right')
            self._stat_labels[key] = v

        # Section: Vehicle legend
        self._section(right, '🔑  VEHICLE LEGEND')

        legend_card = tk.Frame(right, bg=C['card'])
        legend_card.pack(fill='x', padx=12, pady=4)
        legend_items = [
            (C['blue'],   '■', 'Car         (70% of traffic)'),
            (C['purple'], '■', 'Truck       (20% of traffic)'),
            (C['orange'], '■', 'Ambulance   (10% — emergency)'),
        ]
        for color, icon, text in legend_items:
            r = tk.Frame(legend_card, bg=C['card'])
            r.pack(fill='x', padx=8, pady=3)
            tk.Label(r, text=icon, font=('Courier New', 12),
                     fg=color, bg=C['card']).pack(side='left')
            tk.Label(r, text=text, font=('Courier New', 7),
                     fg=C['dim'], bg=C['card']).pack(side='left', padx=6)

        # Signal legend
        self._section(right, '🚦  SIGNAL LEGEND')
        sig_card = tk.Frame(right, bg=C['card'])
        sig_card.pack(fill='x', padx=12, pady=4)
        for color, lbl in [(C['green'], '●  GREEN — vehicles moving'),
                           (C['red'],   '●  RED   — vehicles waiting'),
                           (C['orange'],'●  ORANGE— emergency active')]:
            r = tk.Frame(sig_card, bg=C['card'])
            r.pack(fill='x', padx=8, pady=2)
            left_txt, right_txt = lbl.split('—')
            tk.Label(r, text=left_txt, font=('Courier New', 8, 'bold'),
                     fg=color, bg=C['card']).pack(side='left')
            tk.Label(r, text='—' + right_txt, font=('Courier New', 7),
                     fg=C['dim'], bg=C['card']).pack(side='left')

    # ── Section header helper ─────────────────────────────────────────────────

    def _section(self, parent, title: str):
        f = tk.Frame(parent, bg=C['panel'])
        f.pack(fill='x', padx=0, pady=(10, 2))
        tk.Label(f, text=title, font=('Courier New', 8, 'bold'),
                 fg=C['blue'], bg=C['panel']
                 ).pack(side='left', padx=12)
        tk.Frame(f, bg=C['border'], height=1).pack(
            side='left', fill='x', expand=True, padx=(4, 12))

    # =========================================================================
    # SIMULATION THREAD
    # =========================================================================

    def _start_sim(self, mode: str):
        self._stop_thread()
        self.sim = Simulation(mode=mode)
        self.sim.on_tick_callback = self._on_tick
        self.sim.start()

        if mode == 'normal':
            self._mode_lbl.config(text='NORMAL  (Fixed Timing)', fg=C['amber'])
            self._status_var.set('Normal mode: each lane gets 10 s green in order.')
        else:
            self._mode_lbl.config(text='SMART  (Dynamic Timing)', fg=C['green'])
            self._status_var.set('Smart mode: green time is proportional to queue size.')

        self._running = True
        self._thread  = threading.Thread(target=self._sim_loop, daemon=True)
        self._thread.start()
        self.after(TICK_MS, self._gui_refresh)

    def _sim_loop(self):
        while self._running and self.sim.running:
            self.sim.tick()
            time.sleep(0.1)

    def _stop_thread(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _toggle_pause(self):
        self.sim.pause()
        if self.sim.paused:
            self._status_var.set('⏸  Simulation paused.')
        else:
            self._status_var.set('▶  Simulation resumed.')

    def _reset_sim(self):
        self._start_sim(self.sim.mode)

    def _spawn_ambulance(self):
        busiest = max(DIRECTIONS, key=lambda d: len(self.sim.lanes[d]))
        self.sim.spawn_emergency(busiest)
        self._status_var.set(
            f'🚨  Ambulance spawned in {busiest} lane — '
            f'signal will switch immediately!')

    def _on_tick(self, snapshot: dict):
        self._snap = snapshot

    # =========================================================================
    # GUI REFRESH
    # =========================================================================

    def _gui_refresh(self):
        if not self._running:
            return
        snap = self._snap
        if snap:
            self._draw_intersection(snap)
            self._update_right_panel(snap)
            e = snap['elapsed']
            self._elapsed_var.set(f'⏱  Elapsed: {int(e // 60)}m {int(e % 60)}s')
        self.after(TICK_MS, self._gui_refresh)

    # ── Right panel update ────────────────────────────────────────────────────

    def _update_right_panel(self, snap: dict):
        MAX_V = 20
        for d in DIRECTIONS:
            w     = self._lane_widgets[d]
            count = snap['lane_counts'][d]
            state = snap['light_states'][d]
            t_l   = snap['light_time_left'][d]
            emerg = snap.get('emergency_dir') == d
            active = d == snap['current_green']

            # Count label
            w['count'].config(text=f'{count} vehicle{"s" if count != 1 else ""}')

            # Bar fill
            bar_w   = w['bar'].winfo_width() or 220
            fill_w  = min(int((count / MAX_V) * bar_w), bar_w)
            fc = C['orange'] if emerg else (C['green'] if active else C['blue'])
            w['fill'].place(x=0, y=0, width=fill_w, relheight=1)
            w['fill'].config(bg=fc)

            # Dot + timer
            if state == 'green':
                dot_c = C['orange'] if emerg else C['green']
                desc  = f'GREEN — {t_l:.1f}s left'
                if emerg:
                    desc = '🚨 EMERGENCY GREEN'
            else:
                dot_c = C['red']
                desc  = 'RED  —  waiting'
            w['dot'].config(fg=dot_c)
            w['timer'].config(text=desc, fg=dot_c)

        # Stats
        self._stat_labels['total_spawned'].config(text=str(snap['total_spawned']))
        self._stat_labels['total_cleared'].config(text=str(snap['total_cleared']))
        self._stat_labels['avg_wait'].config(text=f"{snap['avg_wait']:.1f}")
        self._stat_labels['throughput'].config(text=f"{snap['throughput']:.1f}")

    # =========================================================================
    # CANVAS DRAWING
    # =========================================================================

    def _draw_intersection(self, snap: dict):
        c  = self._canvas
        c.delete('all')

        W, H   = 500, 620
        cx, cy = 250, 300    # intersection centre
        rw     = 100          # road width (pixels)
        hw     = rw // 2      # half road width

        # ── Background ────────────────────────────────────────────────────────
        c.create_rectangle(0, 0, W, H, fill=C['bg'], outline='')

        # ── Road arms ─────────────────────────────────────────────────────────
        # Vertical (North–South)
        c.create_rectangle(cx - hw, 0, cx + hw, H, fill=C['road'], outline='')
        # Horizontal (East–West)
        c.create_rectangle(0, cy - hw, W, cy + hw, fill=C['road'], outline='')
        # Centre box (overlap)
        c.create_rectangle(cx - hw, cy - hw, cx + hw, cy + hw,
                            fill=C['lane'], outline='')

        # ── Centre line dashes ─────────────────────────────────────────────────
        dash = (10, 8)
        lw   = 2
        c.create_line(cx, 0,       cx, cy - hw, fill=C['stripe'], dash=dash, width=lw)
        c.create_line(cx, cy + hw, cx, H,       fill=C['stripe'], dash=dash, width=lw)
        c.create_line(0,       cy, cx - hw, cy, fill=C['stripe'], dash=dash, width=lw)
        c.create_line(cx + hw, cy, W,       cy, fill=C['stripe'], dash=dash, width=lw)

        # ── Stop lines (thick white bar across each approach) ─────────────────
        stop_offset = 6
        for d in DIRECTIONS:
            if d == 'North':
                c.create_rectangle(cx - hw + 2, cy - hw - stop_offset,
                                   cx + hw - 2, cy - hw - stop_offset + 3,
                                   fill='#ffffff', outline='')
            elif d == 'South':
                c.create_rectangle(cx - hw + 2, cy + hw + stop_offset - 3,
                                   cx + hw - 2, cy + hw + stop_offset,
                                   fill='#ffffff', outline='')
            elif d == 'East':
                c.create_rectangle(cx + hw + stop_offset - 3, cy - hw + 2,
                                   cx + hw + stop_offset,     cy + hw - 2,
                                   fill='#ffffff', outline='')
            elif d == 'West':
                c.create_rectangle(cx - hw - stop_offset,     cy - hw + 2,
                                   cx - hw - stop_offset + 3, cy + hw - 2,
                                   fill='#ffffff', outline='')

        # ── Traffic lights ─────────────────────────────────────────────────────
        # Positioned at each corner of the intersection box
        light_pos = {
            'North': (cx + hw + 16, cy - hw - 16),
            'South': (cx - hw - 16, cy + hw + 16),
            'East':  (cx + hw + 16, cy + hw + 16),
            'West':  (cx - hw - 16, cy - hw - 16),
        }
        for d, (lx, ly) in light_pos.items():
            state = snap['light_states'][d]
            emerg = snap.get('emergency_dir') == d
            self._draw_signal_box(c, lx, ly, state, emerg)

        # ── Direction arrow labels ─────────────────────────────────────────────
        dir_info = {
            'North': (cx, 18,    '▼ NORTH'),
            'South': (cx, H - 18,'▲ SOUTH'),
            'East':  (W - 20, cy,'◀ EAST'),
            'West':  (20,     cy,'WEST ▶'),
        }
        for d, (lx, ly, arrow) in dir_info.items():
            count  = snap['lane_counts'][d]
            active = d == snap['current_green']
            fc     = C['green'] if active else C['dim']
            c.create_text(lx, ly,
                          text=f'{arrow}  [{count}]',
                          fill=fc, font=('Courier New', 9, 'bold'))

        # ── Vehicles ───────────────────────────────────────────────────────────
        self._draw_vehicles(c, snap, cx, cy, hw)

        # ── Active green banner ────────────────────────────────────────────────
        self._draw_green_banner(c, snap, cx, H, hw)

        # ── Compass rose (small, bottom-right) ────────────────────────────────
        self._draw_compass(c, W - 28, H - 28)

    # ── Traffic light box ─────────────────────────────────────────────────────

    def _draw_signal_box(self, c, x, y, state, is_emergency):
        """Draw a realistic traffic light housing with red and green bulbs."""
        bw, bh = 16, 32   # box width, height
        # Housing
        c.create_rectangle(x - bw//2, y - bh//2, x + bw//2, y + bh//2,
                            fill='#1a1a1a', outline=C['border'], width=1)
        # Red bulb (top)
        red_on  = (state == 'red')
        c.create_oval(x - 5, y - bh//2 + 3, x + 5, y - 2,
                      fill=C['red'] if red_on else '#3a0000', outline='')
        if red_on:
            # glow
            c.create_oval(x - 7, y - bh//2 + 1, x + 7, y,
                          fill='', outline=C['red'], width=1)

        # Green bulb (bottom)
        green_on = (state == 'green')
        gc = C['orange'] if is_emergency else C['green']
        c.create_oval(x - 5, y + 2, x + 5, y + bh//2 - 3,
                      fill=gc if green_on else '#003a00', outline='')
        if green_on:
            c.create_oval(x - 7, y, x + 7, y + bh//2 - 1,
                          fill='', outline=gc, width=1)

        # Post
        c.create_rectangle(x - 2, y + bh//2, x + 2, y + bh//2 + 10,
                            fill='#555', outline='')

    # ── Vehicles ──────────────────────────────────────────────────────────────

    def _draw_vehicles(self, c, snap, cx, cy, hw):
        """Draw queued vehicles as small labelled rectangles approaching the box."""
        gap = 20      # pixels between vehicles
        MAX = 6       # max vehicles to render per lane

        counts = snap['lane_counts']
        fronts = snap['front_vehicle']

        # North: vehicles drive down from the top, queue above intersection
        for i in range(min(counts['North'], MAX)):
            vtype = fronts['North'] if i == 0 else 'car'
            y0    = cy - hw - 14 - i * gap
            self._draw_car(c, cx - 12, y0, 24, 12, vtype, facing='down')

        # South: vehicles drive up from bottom, queue below intersection
        for i in range(min(counts['South'], MAX)):
            vtype = fronts['South'] if i == 0 else 'car'
            y0    = cy + hw + 14 + i * gap
            self._draw_car(c, cx - 12, y0 - 12, 24, 12, vtype, facing='up')

        # East: vehicles drive left from right, queue right of intersection
        for i in range(min(counts['East'], MAX)):
            vtype = fronts['East'] if i == 0 else 'car'
            x0    = cx + hw + 14 + i * gap
            self._draw_car(c, x0, cy - 6, 12, 12, vtype, facing='left')

        # West: vehicles drive right from left, queue left of intersection
        for i in range(min(counts['West'], MAX)):
            vtype = fronts['West'] if i == 0 else 'car'
            x0    = cx - hw - 14 - i * gap
            self._draw_car(c, x0 - 12, cy - 6, 12, 12, vtype, facing='right')

    def _draw_car(self, c, x, y, w, h, vtype, facing='down'):
        """Draw a single vehicle rectangle with type-coded colour."""
        if vtype == 'ambulance':
            body_c = C['orange']
        elif vtype == 'truck':
            body_c = C['purple']
        else:
            body_c = C['blue']

        # Body
        c.create_rectangle(x, y, x + w, y + h,
                            fill=body_c, outline='#0a1520', width=1)

        # Windshield (small lighter rect at front)
        ws_c = '#c8e8ff'
        if facing == 'down':
            c.create_rectangle(x + 3, y + 2, x + w - 3, y + 5,
                                fill=ws_c, outline='')
        elif facing == 'up':
            c.create_rectangle(x + 3, y + h - 5, x + w - 3, y + h - 2,
                                fill=ws_c, outline='')
        elif facing == 'left':
            c.create_rectangle(x + 2, y + 3, x + 5, y + h - 3,
                                fill=ws_c, outline='')
        elif facing == 'right':
            c.create_rectangle(x + w - 5, y + 3, x + w - 2, y + h - 3,
                                fill=ws_c, outline='')

        # Ambulance cross
        if vtype == 'ambulance':
            mx, my = x + w // 2, y + h // 2
            c.create_line(mx - 3, my, mx + 3, my, fill='white', width=2)
            c.create_line(mx, my - 3, mx, my + 3, fill='white', width=2)

    # ── Active green banner ───────────────────────────────────────────────────

    def _draw_green_banner(self, c, snap, cx, H, hw):
        """Horizontal progress bar at the bottom showing green time remaining."""
        active  = snap['current_green']
        t_left  = snap['light_time_left'].get(active, 0)
        dur     = self.sim.lights[active].green_duration
        emerg   = snap.get('emergency_dir') is not None

        bar_w   = 300
        bar_h   = 12
        bx      = cx - bar_w // 2
        by      = H - 52

        # Background bar
        c.create_rectangle(bx, by, bx + bar_w, by + bar_h,
                           fill=C['card'], outline=C['border'])

        # Fill
        fill_w = int((t_left / dur) * bar_w) if dur > 0 else 0
        fill_c = C['orange'] if emerg else C['green']
        if fill_w > 0:
            c.create_rectangle(bx, by, bx + fill_w, by + bar_h,
                                fill=fill_c, outline='')

        # Label above bar
        if emerg:
            label = f'🚨  EMERGENCY — {snap["emergency_dir"]} lane has priority'
            fc    = C['orange']
        else:
            label = f'GREEN LIGHT → {active}   |   {t_left:.1f}s remaining'
            fc    = C['green']

        c.create_text(cx, by - 10, text=label,
                      fill=fc, font=('Courier New', 9, 'bold'))

        # Small legend below bar
        c.create_text(cx, by + bar_h + 10,
                      text='▲  Timer bar: shows how much green time is left',
                      fill=C['dim'], font=('Courier New', 7))

    # ── Compass rose ─────────────────────────────────────────────────────────

    def _draw_compass(self, c, x, y):
        for label, dx, dy in [('N', 0, -12), ('S', 0, 12),
                               ('E', 12, 0), ('W', -12, 0)]:
            c.create_text(x + dx, y + dy, text=label,
                          fill=C['dim'], font=('Courier New', 7, 'bold'))
        c.create_oval(x - 8, y - 8, x + 8, y + 8,
                      outline=C['border'], fill='')

    # =========================================================================
    # COMPARISON FEATURE
    # =========================================================================

    def _show_comparison(self):
        self._stop_thread()
        self._status_var.set(
            f'Running comparison ({SIM_DURATION}s each) — please wait…')

        def run():
            results = {}
            for mode in ('normal', 'smart'):
                sim = Simulation(mode=mode, arrival_rate=0.5)
                sim.start()
                t0 = time.time()
                while time.time() - t0 < SIM_DURATION:
                    sim.tick()
                    time.sleep(0.05)
                sim.stop()
                results[mode] = sim.get_stats()
            self.after(0, lambda: self._show_results(results))
            self.after(0, lambda: self._start_sim(self.sim.mode))

        threading.Thread(target=run, daemon=True).start()

    def _show_results(self, results: dict):
        win = tk.Toplevel(self)
        win.title('Mode Comparison Results')
        win.configure(bg=C['bg'])
        win.resizable(False, False)

        tk.Label(win, text='📊  COMPARISON RESULTS',
                 font=('Courier New', 14, 'bold'),
                 fg=C['blue'], bg=C['bg']).pack(pady=(18, 4))
        tk.Label(win,
                 text=f'Each mode ran for {SIM_DURATION} seconds with the same traffic rate.',
                 font=('Courier New', 8), fg=C['dim'], bg=C['bg']).pack(pady=(0, 12))

        n, s = results['normal'], results['smart']

        # Table
        tbl = tk.Frame(win, bg=C['card'])
        tbl.pack(padx=24, pady=4, fill='x')

        headers = ['Metric', 'Normal', 'Smart', 'Winner']
        widths  = [22,        10,       10,       14]
        for col, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(tbl, text=h, font=('Courier New', 8, 'bold'),
                     fg=C['blue'], bg=C['card'], width=w, anchor='center',
                     pady=6).grid(row=0, column=col, padx=2)

        metrics = [
            ('Vehicles Cleared',  n['total_cleared'],  s['total_cleared'],  'higher'),
            ('Avg Wait (s)',       round(n['avg_wait'],  2), round(s['avg_wait'],  2), 'lower'),
            ('Throughput (v/m)',   round(n['throughput'],2), round(s['throughput'],2), 'higher'),
        ]
        for ri, (label, nv, sv, pref) in enumerate(metrics, 1):
            if pref == 'higher':
                winner = ('Smart ✅', C['green']) if sv >= nv else ('Normal ✅', C['amber'])
            else:
                winner = ('Smart ✅', C['green']) if sv <= nv else ('Normal ✅', C['amber'])

            for ci, (txt, w, col) in enumerate([
                    (label, 22, C['text']),
                    (str(nv), 10, C['amber']),
                    (str(sv), 10, C['green']),
                    (winner[0], 14, winner[1])]):
                tk.Label(tbl, text=txt, font=('Courier New', 8),
                         fg=col, bg=C['card'], width=w,
                         anchor='center', pady=5
                         ).grid(row=ri, column=ci, padx=2)

        # Explanation
        expl = tk.Frame(win, bg=C['panel'])
        expl.pack(padx=24, pady=10, fill='x')
        tk.Label(expl, text='WHY SMART IS BETTER:',
                 font=('Courier New', 8, 'bold'), fg=C['green'],
                 bg=C['panel']).pack(anchor='w', padx=10, pady=(8, 2))
        tk.Label(expl,
                 text='Smart mode allocates green time based on how many vehicles are\n'
                      'actually waiting — so a busy lane gets more time, and an empty\n'
                      'lane does not waste the signal. This reduces average wait time\n'
                      'and increases throughput, especially under uneven traffic loads.',
                 font=('Courier New', 7), fg=C['dim'],
                 bg=C['panel'], justify='left'
                 ).pack(anchor='w', padx=10, pady=(0, 8))

        # Matplotlib chart
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            fig, axes = plt.subplots(1, 3, figsize=(9, 3))
            fig.patch.set_facecolor(C['bg'])

            chart_data = [
                ('Vehicles Cleared', n['total_cleared'],  s['total_cleared']),
                ('Avg Wait (s)',      n['avg_wait'],       s['avg_wait']),
                ('Throughput (v/m)', n['throughput'],     s['throughput']),
            ]
            for ax, (title, nv, sv) in zip(axes, chart_data):
                bars = ax.bar(['Normal', 'Smart'], [nv, sv],
                              color=[C['amber'], C['green']], width=0.5)
                ax.set_title(title, color=C['text'], fontsize=8, pad=6)
                ax.set_facecolor(C['card'])
                ax.tick_params(colors=C['dim'], labelsize=7)
                for spine in ax.spines.values():
                    spine.set_edgecolor(C['border'])
                for bar, val in zip(bars, [nv, sv]):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() * 1.02,
                            f'{val:.1f}', ha='center', va='bottom',
                            color=C['text'], fontsize=7)

            fig.tight_layout(pad=1.5)
            chart_widget = FigureCanvasTkAgg(fig, master=win)
            chart_widget.draw()
            chart_widget.get_tk_widget().pack(padx=24, pady=(0, 10))

        except ImportError:
            tk.Label(win,
                     text='Install matplotlib for charts:  pip install matplotlib',
                     font=('Courier New', 8), fg=C['dim'], bg=C['bg']
                     ).pack(pady=6)

        tk.Button(win, text='  Close  ', bg=C['card'], fg=C['text'],
                  font=('Courier New', 9, 'bold'), bd=0, pady=6,
                  command=win.destroy, cursor='hand2'
                  ).pack(pady=(0, 18))


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = TrafficApp()
    app.mainloop()
