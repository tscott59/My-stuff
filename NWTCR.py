import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageDraw, ImageFont

# =========================
# AUTO-INSTALL CHECK: PILLOW
# =========================
def ensure_pillow():
    try:
        import PIL  # noqa
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno(
            "Missing Dependency",
            "The 'Pillow' library is required for this program.\n\nInstall it automatically now?"
        ):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            messagebox.showinfo("Installed", "Pillow was successfully installed.\nRestarting the app...")
            root.destroy()
            subprocess.Popen([sys.executable, __file__])
            sys.exit(0)
        else:
            messagebox.showwarning("Exiting", "Cannot continue without Pillow.")
            sys.exit(1)

ensure_pillow()

# =========================
# CONFIG / CONSTANTS
# =========================
APP_TITLE = "New World True Crit-Rate"
WINDOW_W, WINDOW_H = 540, 540
LEFT_COL_W = 220
TABLE_VISIBLE_ROWS = 12
ROW_HEIGHT = 18

COLOR_BG_DARK = "#1a1a1a"
COLOR_PANEL_BG = "#000000"
COLOR_TEXT = "#ffffff"
COLOR_ACCENT_BASE = "#2a1e38"
COLOR_ACCENT_HOVER = "#4f3a63"
COLOR_GLOW = "#4f3a63"

COLOR_LOW = "#ff5555"
COLOR_MID = "#ffd966"
COLOR_HIGH = "#82e682"

# =========================
# IMAGE PATH HANDLING FOR EXECUTABLE
# =========================
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # PyInstaller temp folder
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

bg_image_path = os.path.join(base_path, "NWTCRBG.JPG")

# =========================
# CORE CALC LOGIC
# =========================
def color_tag_for_prob(pct: float) -> str:
    if pct < 50:
        return "low"
    elif pct < 70:
        return "mid"
    return "high"

def compute_sequence(base_pct: float, modifiers_pct: float, cap_at_100=True, hard_cap_hits=20000):
    p_start = max(0.0, base_pct + modifiers_pct)
    delta = max(0.0, base_pct)
    rows = []
    k100 = None
    raw_at_k100 = None

    if delta == 0 and p_start < 100:
        for k in range(1, min(250, hard_cap_hits) + 1):
            raw = p_start
            cap = min(100.0, raw) if cap_at_100 else raw
            rows.append({"hit": k, "chance": cap, "tag": color_tag_for_prob(cap)})
        return rows, None, None
    for k in range(1, hard_cap_hits + 1):
        raw = p_start + (k - 1) * delta
        cap = min(100.0, raw) if cap_at_100 else raw
        rows.append({"hit": k, "chance": cap, "tag": color_tag_for_prob(cap)})
        if k100 is None and raw >= 100.0:
            k100 = k
            raw_at_k100 = raw
            break

    return rows, k100, raw_at_k100

def expected_crits_and_percentage(base_pct: float, modifiers_pct: float, num_hits: int):
    p_start = max(0.0, min(100.0, base_pct + modifiers_pct)) / 100.0
    delta = max(0.0, base_pct) / 100.0
    p = []
    cur = p_start
    while True:
        p.append(min(1.0, max(0.0, cur)))
        if p[-1] >= 1.0:
            break
        cur += delta
        if len(p) > 100000:
            break

    M = len(p)
    dist = [0.0] * M
    dist[0] = 1.0
    expected_crits = 0.0
    for _ in range(num_hits):
        e_this = sum(dist[i] * p[i] for i in range(M))
        expected_crits += e_this
        nxt = [0.0] * M
        for i in range(M):
            pi = p[i]
            nxt[0] += dist[i] * pi
            nxt[min(i + 1, M - 1)] += dist[i] * (1 - pi)
        dist = nxt
    percentage = (expected_crits / num_hits) * 100.0
    return expected_crits, percentage

# =========================
# GUI SETUP
# =========================
root = tk.Tk()
root.title(APP_TITLE)
root.geometry(f"{WINDOW_W}x{WINDOW_H}")
root.minsize(500, 500)
root.resizable(False, False)

# Background (blurred)
try:
    bg_img = Image.open(bg_image_path)
except FileNotFoundError:
    bg_img = Image.new("RGB", (WINDOW_W, WINDOW_H), (40, 45, 60))
    draw = ImageDraw.Draw(bg_img)
    draw.text((50, 50), "Background image not found.", fill=(255, 255, 255), font=ImageFont.load_default())

bg_blur = bg_img.filter(ImageFilter.GaussianBlur(1))
bg_tk = ImageTk.PhotoImage(bg_blur)
canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H, highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_tk, anchor="nw")

# Glow & panel
glow = tk.Label(root, bg=COLOR_GLOW)
glow.place(relx=0.5, rely=0.5, anchor="center", width=WINDOW_W - 90, height=WINDOW_H - 130)

panel = tk.Frame(root, bg=COLOR_PANEL_BG, bd=0, highlightthickness=0)
panel.place(relx=0.5, rely=0.5, anchor="center", width=WINDOW_W - 100, height=WINDOW_H - 140)

glass = tk.Label(panel, bg=COLOR_BG_DARK, fg=COLOR_TEXT)
glass.place(relx=0, rely=0, relwidth=1, relheight=1)
glass.lower()

# Styles
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT, font=("Segoe UI", 10))
style.configure("Header.TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT, font=("Segoe UI", 11, "bold"))
style.configure("TEntry", fieldbackground="#222831", foreground=COLOR_TEXT, insertcolor=COLOR_TEXT)
style.configure("TFrame", background=COLOR_BG_DARK)
style.configure("Summary.TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT, font=("Segoe UI Semibold", 9))
style.configure("Compact.Treeview", background=COLOR_BG_DARK, fieldbackground=COLOR_BG_DARK,
                foreground=COLOR_TEXT, rowheight=ROW_HEIGHT, font=("Segoe UI", 9))
style.configure("Compact.Treeview.Heading", font=("Segoe UI", 9, "bold"))

# Layout containers
left = ttk.Frame(panel, padding=(5, 0, 0, 0), style="TFrame")
right = ttk.Frame(panel, padding=(0, 0, 0, 0), style="TFrame")
left.place(relx=0.0, rely=0.0, relheight=1.0, width=LEFT_COL_W)
right.place(relx=0.0, y=0, relheight=1.0, x=LEFT_COL_W, relwidth=1.0, anchor="nw")

# LEFT: Legend & Inputs
legend = ttk.Frame(left, style="TFrame")
legend.pack(anchor="w", pady=(0, 0))
ttk.Label(legend, text="Legend:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 2))
ttk.Label(legend, text="< 50%   (Low)").grid(row=1, column=0, sticky="w")
ttk.Label(legend, text="50–69% (Med)").grid(row=2, column=0, sticky="w")
ttk.Label(legend, text="≥ 70%   (High)").grid(row=3, column=0, sticky="w")

ttk.Label(left, text="Inputs", style="Header.TLabel").pack(anchor="w", pady=(110, 0))

var_base = tk.StringVar(value="8")
var_mod = tk.StringVar(value="10")
var_inc = tk.StringVar(value=var_base.get())

def add_input(label_text, var, readonly=False):
    ttk.Label(left, text=label_text).pack(anchor="w")
    state = "readonly" if readonly else "normal"
    e = ttk.Entry(left, width=12, textvariable=var, justify="center", state=state)
    e.pack(anchor="w", pady=(0, 0))
    return e

entry_base = add_input("Base weapon Crit Chance (%)", var_base)
entry_mod = add_input("Total Crit Chance Modifiers (%)", var_mod)
entry_inc = add_input("Increase on non-crit (%)", var_inc, readonly=True)

def hex_color_mix(c1, c2, factor=0.5):
    c1 = int(c1.lstrip("#"), 16)
    c2 = int(c2.lstrip("#"), 16)
    r = int(((c1 >> 16) & 0xFF) * (1-factor) + ((c2 >> 16) & 0xFF) * factor)
    g = int(((c1 >> 8) & 0xFF) * (1-factor) + ((c2 >> 8) & 0xFF) * factor)
    b = int((c1 & 0xFF) * (1-factor) + (c2 & 0xFF) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def on_enter(e): btn_calc.config(bg=hex_color_mix(COLOR_ACCENT_BASE, COLOR_ACCENT_HOVER, 0.5))
def on_leave(e): btn_calc.config(bg=COLOR_ACCENT_BASE)
def sync_inc_from_base(*_): var_inc.set(var_base.get())
var_base.trace_add("write", sync_inc_from_base)

btn_calc = tk.Button(left, text="Calculate", fg="white", bg=COLOR_ACCENT_BASE,
                     activebackground="#16212b", activeforeground="white",
                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=12, pady=6, highlightthickness=0)
btn_calc.pack(anchor="w", pady=(2, 0))
btn_calc.bind("<Enter>", on_enter)
btn_calc.bind("<Leave>", on_leave)

# RIGHT: Results
ttk.Label(right, text="Per-Hit Breakdown", style="Header.TLabel").pack(anchor="w", padx=(40,0), pady=(0, 0))
table_frame = ttk.Frame(right, style="TFrame")
table_frame.pack(anchor="nw", padx=(35, 6), pady=(0, 8), fill="x", expand=False)
columns = ("hit", "chance")
tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=TABLE_VISIBLE_ROWS, style="Compact.Treeview")
tree.heading("hit", text="Hit", anchor="center")
tree.heading("chance", text="Crit %", anchor="center")
tree.column("hit", width=60, anchor="center", stretch=False)
tree.column("chance", width=60, anchor="center", stretch=False)
vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)
tree.pack(side="left", padx=2, pady=2)
vsb.pack(side="left", fill="y")
tree.tag_configure("low", foreground=COLOR_LOW)
tree.tag_configure("mid", foreground=COLOR_MID)
tree.tag_configure("high", foreground=COLOR_HIGH)

totals = ttk.Frame(right, style="TFrame")
totals.pack(fill="x", pady=(6, 0))
ttk.Label(totals, text="Expected Crits & Percentage", style="Header.TLabel").grid(row=0, column=0, sticky="w", columnspan=5, pady=(0, 0))

def make_total_row(parent, r, label):
    ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w")
    ttk.Label(parent, text="Crits:").grid(row=r, column=1, sticky="w")
    exp_lbl = ttk.Label(parent, text="-", style="Summary.TLabel")
    exp_lbl.grid(row=r, column=2, sticky="w")
    ttk.Label(parent, text="Crit %:").grid(row=r, column=3, sticky="w")
    pct_lbl = ttk.Label(parent, text="-", style="Summary.TLabel")
    pct_lbl.grid(row=r, column=4, sticky="w")
    return exp_lbl, pct_lbl

exp10, pct10 = make_total_row(totals, 1, "10 hits ")
exp50, pct50 = make_total_row(totals, 2, "50 hits ")
exp100, pct100 = make_total_row(totals, 3, "100 hits")
exp1k, pct1k = make_total_row(totals, 4, "1000 hits")

def calculate(*_):
    for item in tree.get_children():
        tree.delete(item)
    try:
        base = float(var_base.get())
        mods = float(var_mod.get())
    except ValueError:
        messagebox.showerror("Invalid input", "Please enter valid numeric values for Base and Modifiers.")
        return
    var_inc.set(var_base.get())
    rows, _, _ = compute_sequence(base, mods, cap_at_100=True)
    for row in rows:
        tree.insert("", "end", values=(row["hit"], f"{row['chance']:.2f}"), tags=(row["tag"],))
    for N, exp_lbl, pct_lbl in [(10, exp10, pct10), (50, exp50, pct50), (100, exp100, pct100), (1000, exp1k, pct1k)]:
        expected, pct = expected_crits_and_percentage(base, mods, N)
        exp_lbl.config(text=f"{expected:.2f}")
        pct_lbl.config(text=f"{pct:.2f}%")

btn_calc.config(command=calculate)
root.bind("<Return>", calculate)
calculate()
root.mainloop()