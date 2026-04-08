"""
Nova Voice Assistant - Visual UI
Place in same folder as nova_assistance.py
Run with: python nova_ui.py
"""

import tkinter as tk
import threading
import math
import time
import os

# ── Colours ───────────────────────────────────────────────
BG       = "#0a0a0f"
TEXT_COL = "#e0e0e0"
MUTED    = "#555577"
ACCENT   = "#e94560"
BLUE     = "#00b4d8"

# ── Shared state updated by Nova, read by UI ──────────────
nova_state = {
    "mode": "idle",
    "text": "Starting Nova...",
    "sub":  ""
}

# ── Thread lock for safe state updates ────────────────────
state_lock = threading.Lock()

def set_state(mode, text, sub=""):
    with state_lock:
        nova_state["mode"] = mode
        nova_state["text"] = text
        nova_state["sub"]  = sub


# ═══════════════════════════════════════════════════════════
#  SPHERE
# ═══════════════════════════════════════════════════════════
class Sphere(tk.Canvas):
    def __init__(self, parent, size=280):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0)
        self.cx    = size // 2
        self.cy    = size // 2
        self.r     = size // 2 - 28
        self.phase = 0.0
        self._tick()

    def _tick(self):
        self.delete("all")
        with state_lock:
            mode = nova_state["mode"]
        p = self.phase

        if   mode == "speaking":  self._speaking(p)
        elif mode == "listening": self._listening(p)
        else:                     self._idle(p)

        self.phase += 0.05
        self.after(33, self._tick)

    # ── Idle ─────────────────────────────────────────────
    def _idle(self, p):
        pulse = 0.93 + 0.07 * math.sin(p)
        r     = int(self.r * pulse)
        cx, cy = self.cx, self.cy

        for i in range(5, 0, -1):
            self.create_oval(
                cx-r-i*9, cy-r-i*9, cx+r+i*9, cy+r+i*9,
                fill="", outline=self._mix("#0f3460", BG, i/5), width=1)

        for i in range(8, 0, -1):
            t   = i / 8
            col = self._mix("#0d0d1a", "#1e3a5f", t)
            off = int((1-t) * r * 0.3)
            self.create_oval(cx-r+off, cy-r+off, cx+r, cy+r,
                             fill=col, outline="")

        self._ring(r, p * 0.4, "#0f3460")
        self._glow(r, 0.28)

        if math.sin(p * 1.5) > 0:
            self.create_oval(cx-4, cy+r-14, cx+4, cy+r-6,
                             fill=MUTED, outline="")

    # ── Speaking ──────────────────────────────────────────
    def _speaking(self, p):
        energy = abs(math.sin(p * 3.5))
        r      = int(self.r * (0.87 + 0.13 * energy))
        cx, cy = self.cx, self.cy

        for i in range(6, 0, -1):
            rr  = r + i * 11
            col = self._mix(ACCENT, BG, (i/6) * energy)
            self.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                             fill="", outline=col, width=1)

        for i in range(8, 0, -1):
            t   = i / 8
            col = self._mix("#1a0008", ACCENT, t*(0.35+0.25*energy))
            off = int((1-t) * r * 0.25)
            self.create_oval(cx-r+off, cy-r+off, cx+r, cy+r,
                             fill=col, outline="")

        for w in range(4):
            wv  = math.sin(p * 6 + w * 1.5)
            y   = cy + int(r * 0.25 * (w/3 - 0.5))
            amp = int(r * 0.18 * abs(wv))
            x1  = cx - int(r * 0.55)
            x2  = cx + int(r * 0.55)
            self.create_line(x1, y, x2, y+amp,
                             fill="#f5a62366", width=1)

        self._ring(r, p, ACCENT)
        self._glow(r, 0.32)

    # ── Listening ────────────────────────────────────────
    def _listening(self, p):
        r      = int(self.r * (0.96 + 0.04 * math.sin(p*2)))
        cx, cy = self.cx, self.cy

        for i in range(5):
            rph = (p * 1.8 + i * 1.2) % (2 * math.pi)
            rr  = r + int(35 * (rph / (2*math.pi)))
            alp = 1 - rph / (2*math.pi)
            col = self._mix(BLUE, BG, 1-alp)
            self.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                             fill="", outline=col, width=1)

        for i in range(8, 0, -1):
            t   = i / 8
            col = self._mix("#001520", BLUE, t*0.4)
            off = int((1-t) * r * 0.25)
            self.create_oval(cx-r+off, cy-r+off, cx+r, cy+r,
                             fill=col, outline="")

        dr = int(9 + 5 * abs(math.sin(p*4)))
        self.create_oval(cx-dr, cy-dr, cx+dr, cy+dr,
                         fill=BLUE, outline="")

        self._ring(r, -p*0.9, BLUE)
        self._glow(r, 0.28)

    # ── Helpers ──────────────────────────────────────────
    def _glow(self, r, s):
        ox = int(r * 0.3)
        oy = int(r * 0.3)
        hr = int(r * s)
        self.create_oval(
            self.cx-ox-hr, self.cy-oy-hr,
            self.cx-ox+hr, self.cy-oy+hr,
            fill="white", outline="", stipple="gray25")

    def _ring(self, r, phase, colour):
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60 + phase
            x = self.cx + int((r+10) * math.cos(a))
            y = self.cy + int((r+10) * 0.22 * math.sin(a))
            pts.append((x, y))
        for i in range(len(pts)):
            x1, y1 = pts[i]
            x2, y2 = pts[(i+1) % len(pts)]
            self.create_line(x1, y1, x2, y2, fill=colour, width=1)

    @staticmethod
    def _mix(h1, h2, t):
        t = max(0.0, min(1.0, t))
        r1,g1,b1 = int(h1[1:3],16),int(h1[3:5],16),int(h1[5:7],16)
        r2,g2,b2 = int(h2[1:3],16),int(h2[3:5],16),int(h2[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))


# ═══════════════════════════════════════════════════════════
#  WINDOW
# ═══════════════════════════════════════════════════════════
class NovaApp:
    def __init__(self, root):
        self.root = root
        root.title("Nova — Voice Assistant")
        root.configure(bg=BG)
        root.resizable(False, False)

        W, H = 400, 560
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        root.protocol("WM_DELETE_WINDOW", self._quit)

        self._build()
        self._refresh()

    def _build(self):
        r = self.root

        # Top bar
        top = tk.Frame(r, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(top, text="NOVA",
                 font=("Courier New", 13, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(top, text="  Voice Assistant",
                 font=("Courier New", 10),
                 fg=MUTED, bg=BG).pack(side="left")
        self.dot = tk.Label(top, text="●",
                            font=("Courier New", 11),
                            fg=MUTED, bg=BG)
        self.dot.pack(side="right")

        # Sphere
        sf = tk.Frame(r, bg=BG)
        sf.pack(pady=(14, 0))
        self.sphere = Sphere(sf, size=280)
        self.sphere.pack()

        # Mode label
        self.mode_lbl = tk.Label(r, text="IDLE",
                                 font=("Courier New", 9, "bold"),
                                 fg=MUTED, bg=BG)
        self.mode_lbl.pack(pady=(6, 0))

        # Text box
        box = tk.Frame(r, bg="#0d0d1a",
                       highlightbackground="#1a1a2e",
                       highlightthickness=1)
        box.pack(fill="x", padx=20, pady=(10, 0))
        self.main_lbl = tk.Label(box,
                                 text="Starting Nova...",
                                 font=("Courier New", 11),
                                 fg=TEXT_COL, bg="#0d0d1a",
                                 wraplength=330,
                                 justify="center",
                                 pady=14, padx=14)
        self.main_lbl.pack()

        # Sub label
        self.sub_lbl = tk.Label(r, text="",
                                font=("Courier New", 9),
                                fg=MUTED, bg=BG,
                                wraplength=340,
                                justify="center")
        self.sub_lbl.pack(pady=(6, 0))

        # Bottom bar
        bot = tk.Frame(r, bg=BG)
        bot.pack(side="bottom", fill="x", padx=20, pady=14)
        tk.Label(bot, text="Say  'Nova'  to activate",
                 font=("Courier New", 9),
                 fg=MUTED, bg=BG).pack(side="left")
        q = tk.Label(bot, text="Quit  ✕",
                     font=("Courier New", 9),
                     fg=MUTED, bg=BG, cursor="hand2")
        q.pack(side="right")
        q.bind("<Button-1>", lambda e: self._quit())

    def _refresh(self):
        with state_lock:
            mode = nova_state["mode"]
            text = nova_state["text"]
            sub  = nova_state["sub"]

        colours = {
            "idle":      (MUTED,  "IDLE"),
            "speaking":  (ACCENT, "SPEAKING"),
            "listening": (BLUE,   "LISTENING"),
        }
        col, label = colours.get(mode, (MUTED, "IDLE"))

        self.mode_lbl.config(text=label, fg=col)
        self.dot.config(fg=col)
        self.main_lbl.config(text=text)
        self.sub_lbl.config(text=sub)

        # Schedule next refresh
        self.root.after(100, self._refresh)

    def _quit(self):
        os._exit(0)


# ═══════════════════════════════════════════════════════════
#  LOAD AND PATCH NOVA
# ═══════════════════════════════════════════════════════════
def load_and_patch():
    import importlib.util

    folder    = os.path.dirname(os.path.abspath(__file__))
    path      = os.path.join(folder, "nova_assistance.py")

    if not os.path.exists(path):
        set_state("idle", "ERROR: nova_assistance.py not found!")
        return None

    set_state("idle", "Loading Nova...")

    try:
        spec   = importlib.util.spec_from_file_location("nova_asst", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        set_state("idle", f"Load error: {e}")
        return None

    # Patch speak()
    _orig_speak = module.speak
    def patched_speak(text):
        set_state("speaking", text)
        _orig_speak(text)
        set_state("idle", "Ready — say Nova")
    module.speak = patched_speak

    # Patch listen()
    _orig_listen = module.listen
    def patched_listen():
        set_state("listening", "Listening...", "Speak now")
        result = _orig_listen()
        if result:
            set_state("idle", "Ready — say Nova",
                      f'Heard:  "{result}"')
        else:
            set_state("idle", "Ready — say Nova", "Nothing heard")
        return result
    module.listen = patched_listen

    return module


# ═══════════════════════════════════════════════════════════
#  NOVA BACKGROUND THREAD
# ═══════════════════════════════════════════════════════════
def nova_thread(module):
    time.sleep(1.5)
    if module:
        try:
            module.main()
        except Exception as e:
            set_state("idle", f"Nova error: {e}")
    else:
        set_state("idle", "Could not load Nova.")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 1. Build the UI window on the main thread
    root = tk.Tk()
    app  = NovaApp(root)

    # 2. Load and patch Nova
    nova_mod = load_and_patch()

    # 3. Run Nova in a background daemon thread
    t = threading.Thread(target=nova_thread,
                         args=(nova_mod,), daemon=True)
    t.start()

    # 4. Hand control to tkinter — never blocks
    root.mainloop()
