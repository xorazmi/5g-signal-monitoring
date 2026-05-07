import tkinter as tk
from tkinter import ttk, messagebox
import math
import threading
import urllib.request
import json
import subprocess
import sys

# ─── Kutubxonalarni o'rnatish ─────────────────────────────────────────────────
def install_if_missing(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])

install_if_missing("tkintermapview")
import tkintermapview

# ─── Fizik konstantalar ───────────────────────────────────────────────────────
TECHS = {
    "3G (2100 MHz)": {"freq": 2100, "bw": 5,   "pt": 30, "noise": -104, "ba": 12},
    "4G (1800 MHz)": {"freq": 1800, "bw": 20,  "pt": 30, "noise": -108, "ba": 15},
    "5G (3500 MHz)": {"freq": 3500, "bw": 100, "pt": 30, "noise": -101, "ba": 20},
}

COLORS = {
    "bg":     "#F8F7F4",
    "card":   "#FFFFFF",
    "border": "#E0DED6",
    "accent": "#534AB7",
    "good":   "#1D9E75",
    "ok":     "#639922",
    "mid":    "#EF9F27",
    "bad":    "#E24B4A",
    "text":   "#2C2C2A",
    "muted":  "#888780",
}

UZ_DISTRICTS = [
    ("Toshkent — Markaz",          41.2995, 69.2401),
    ("Toshkent — Chilonzor",       41.2856, 69.2017),
    ("Toshkent — Yunusobod",       41.3425, 69.2842),
    ("Toshkent — Mirzo Ulug'bek",  41.3123, 69.3275),
    ("Toshkent — Shayxontohur",    41.3097, 69.2467),
    ("Toshkent — Olmazor",         41.3331, 69.2267),
    ("Toshkent — Bektemir",        41.2647, 69.3483),
    ("Toshkent — Yakkasaroy",      41.2914, 69.2686),
    ("Toshkent — Uchtepa",         41.3003, 69.2153),
    ("Toshkent — Sergeli",         41.2367, 69.2481),
    ("Samarqand — Markaz",         39.6542, 66.9597),
    ("Buxoro — Markaz",            39.7747, 64.4286),
    ("Namangan — Markaz",          41.0011, 71.6726),
    ("Andijon — Markaz",           40.7821, 72.3442),
    ("Farg'ona — Markaz",          40.3842, 71.7843),
    ("Nukus — Markaz",             42.4606, 59.6166),
    ("Qarshi — Markaz",            38.8604, 65.7883),
    ("Termiz — Markaz",            37.2242, 67.2783),
]

def calc_signal(tech_key, dist_m, bdens, pt_override=None, pr_override=None):
    cfg   = TECHS[tech_key]
    freq  = cfg["freq"]
    bw    = cfg["bw"]
    pt    = pt_override if pt_override is not None else cfg["pt"]
    noise = cfg["noise"]
    ba    = cfg["ba"]
    dist_km = max(dist_m, 1) / 1000.0
    PL = 20 * math.log10(freq) + 20 * math.log10(dist_km) + 32.44
    BL = bdens * dist_m * ba / 1000.0
    Pr = pr_override if pr_override is not None else pt - (PL + BL)
    SNR        = Pr - noise
    SNR_linear = 10 ** (SNR / 10.0)
    throughput = bw * math.log2(1 + SNR_linear)
    if   Pr > -65:  quality, q_color = "Ajoyib",   COLORS["good"]
    elif Pr > -85:  quality, q_color = "Yaxshi",   COLORS["ok"]
    elif Pr > -100: quality, q_color = "O'rtacha", COLORS["mid"]
    else:           quality, q_color = "Zaif",     COLORS["bad"]
    return {"PL": PL, "BL": BL, "Pr": Pr, "SNR": SNR,
            "throughput": throughput, "quality": quality,
            "q_color": q_color, "pt": pt, "freq": freq, "bw": bw}

def get_location_by_ip(callback):
    def fetch():
        try:
            url = "https://ipwho.is/"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode())
            callback({"lat": data.get("latitude", 41.2995),
                      "lon": data.get("longitude", 69.2401),
                      "city": data.get("city", "")})
        except Exception as e:
            callback({"error": str(e)})
    threading.Thread(target=fetch, daemon=True).start()

def reverse_geocode(lat, lon, callback):
    def fetch():
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "SignalAnalyzer/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
            addr  = data.get("address", {})
            city  = addr.get("city") or addr.get("town") or addr.get("village") or ""
            state = addr.get("state", "")
            callback({"city": city, "state": state})
        except:
            callback({"city": "", "state": ""})
    threading.Thread(target=fetch, daemon=True).start()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("5G Signal Analyzer")
        self.geometry("920x700")
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])
        self.selected_lat = tk.DoubleVar(value=41.2995)
        self.selected_lon = tk.DoubleVar(value=69.2401)
        self.map_marker   = None

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",     background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["border"],
                        foreground=COLORS["text"], padding=[12, 6], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",       background=[("selected", COLORS["card"])])
        style.configure("TCombobox",     fieldbackground=COLORS["card"], background=COLORS["card"])

        self._build_header()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tab1 = tk.Frame(nb, bg=COLORS["bg"])
        tab2 = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(tab1, text="  Signal hisoblash  ")
        nb.add(tab2, text="  Joylashuv (xarita)  ")
        self._build_calc_tab(tab1)
        self._build_location_tab(tab2)
        self._calculate()

    def _build_header(self):
        hdr = tk.Frame(self, bg=COLORS["accent"], height=54)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="3G / 4G / 5G  Signal Analyzer",
                 bg=COLORS["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="Fizik formulalar asosida",
                 bg=COLORS["accent"], fg="#BFBBF8",
                 font=("Segoe UI", 10)).pack(side="left")

    def _build_calc_tab(self, parent):
        left  = tk.Frame(parent, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(12,6), pady=12)
        right = tk.Frame(parent, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(6,12), pady=12)

        inp = self._card(left, "Kirish parametrlari")
        tk.Label(inp, text="Texnologiya:", bg=COLORS["card"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(6,2))
        self.tech_var = tk.StringVar(value="5G (3500 MHz)")
        cb = ttk.Combobox(inp, textvariable=self.tech_var,
                          values=list(TECHS.keys()), state="readonly", width=22)
        cb.pack(anchor="w")
        cb.bind("<<ComboboxSelected>>", lambda e: self._calculate())

        self.dist_var  = tk.IntVar(value=500)
        self.bdens_var = tk.DoubleVar(value=0.30)
        self.pt_var    = tk.IntVar(value=30)
        self._slider(inp,       "Antenna masofasi (m):",     self.dist_var,  50,  5000, " m")
        self._slider_float(inp, "Bino zichligi (0–1):",      self.bdens_var, 0.0, 1.0)
        self._slider(inp,       "Uzatish quvvati Pt (dBm):", self.pt_var,    10,  50,  " dBm")

        loc_f = self._card(left, "Tanlangan joylashuv")
        self.lbl_chosen = tk.Label(loc_f,
            text="Toshkent — Markaz  (41.2995, 69.2401)",
            bg=COLORS["card"], fg=COLORS["accent"],
            font=("Segoe UI", 9, "italic"), wraplength=280, anchor="w")
        self.lbl_chosen.pack(anchor="w", pady=(4,2))
        tk.Label(loc_f, text="'Joylashuv' tabidan o'zgartirishingiz mumkin",
                 bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")

        rsrp_f = self._card(left, "Android RSRP (real o'lchov)")
        tk.Label(rsrp_f, text="RSRP qiymati (dBm) — ixtiyoriy:",
                 bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6,2))
        self.rsrp_var = tk.StringVar()
        row = tk.Frame(rsrp_f, bg=COLORS["card"]); row.pack(anchor="w", pady=(0,4))
        tk.Entry(row, textvariable=self.rsrp_var, width=12,
                 font=("Segoe UI", 11)).pack(side="left")
        tk.Button(row, text="Qo'llan", command=self._apply_rsrp,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=3).pack(side="left", padx=(8,0))
        tk.Label(rsrp_f, text="(*#*#4636#*#* → Phone info → Signal strength)",
                 bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")

        res = self._card(right, "Hisoblash natijalari")
        self.lbl = {}
        for key, label in [("PL","Yo'l yo'qotishi (Path Loss)"),
                            ("BL","Bino yo'qotishi (Building Loss)"),
                            ("Pr","Qabul signal Pr"),
                            ("SNR","Signal/Shovqun SNR"),
                            ("TP","O'tkazuvchanlik"),
                            ("Q","Signal sifati")]:
            row = tk.Frame(res, bg=COLORS["card"]); row.pack(fill="x", pady=4)
            tk.Label(row, text=label+":", bg=COLORS["card"], fg=COLORS["muted"],
                     font=("Segoe UI", 9), width=28, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", bg=COLORS["card"], fg=COLORS["text"],
                           font=("Segoe UI", 10, "bold"), anchor="w")
            lbl.pack(side="left")
            self.lbl[key] = lbl

        bar_f = self._card(right, "Signal kuchi vizualizatsiyasi")
        self.bars = {}
        for key, label, color in [("Pr","Pr (dBm)",COLORS["good"]),
                                   ("SNR","SNR (dB)",COLORS["accent"]),
                                   ("TP","Throughput","#E24B4A")]:
            tk.Label(bar_f, text=label, bg=COLORS["card"], fg=COLORS["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(6,0))
            cv = tk.Canvas(bar_f, height=18, bg=COLORS["border"],
                           highlightthickness=0, relief="flat")
            cv.pack(fill="x", pady=(2,0))
            rect = cv.create_rectangle(0, 0, 0, 18, fill=color, width=0)
            self.bars[key] = (cv, rect, color)

        tk.Button(right, text="Hisoblash", command=self._calculate,
                  bg=COLORS["accent"], fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=8).pack(pady=10)

    def _build_location_tab(self, parent):
        top = tk.Frame(parent, bg=COLORS["bg"])
        top.pack(fill="x", padx=12, pady=(10,4))
        ctrl = self._card(top, "Joylashuvni tanlash usuli")

        tk.Label(ctrl, text="1. Ro'yxatdan tanlang:", bg=COLORS["card"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(6,2))
        dist_row = tk.Frame(ctrl, bg=COLORS["card"]); dist_row.pack(fill="x", pady=(0,6))
        self.district_var = tk.StringVar(value=UZ_DISTRICTS[0][0])
        ttk.Combobox(dist_row, textvariable=self.district_var,
                     values=[d[0] for d in UZ_DISTRICTS],
                     state="readonly", width=36).pack(side="left")
        tk.Button(dist_row, text="Tanlash →", command=self._select_district,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=3).pack(side="left", padx=(8,0))

        tk.Label(ctrl, text="2. IP manzil orqali avtomatik:", bg=COLORS["card"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(8,2))
        ip_row = tk.Frame(ctrl, bg=COLORS["card"]); ip_row.pack(fill="x", pady=(0,6))
        tk.Button(ip_row, text="IP orqali aniqla", command=self._fetch_location,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=3).pack(side="left")
        self.ip_status = tk.Label(ip_row, text="", bg=COLORS["card"],
                                  fg=COLORS["muted"], font=("Segoe UI", 9))
        self.ip_status.pack(side="left", padx=10)

        tk.Label(ctrl, text="3. Xaritada istalgan nuqtani bosib tanlang (eng aniq):",
                 bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(8,2))

        coord_row = tk.Frame(ctrl, bg=COLORS["card"]); coord_row.pack(fill="x", pady=(0,6))
        tk.Label(coord_row, text="Tanlangan:", bg=COLORS["card"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(side="left")
        self.coord_lbl = tk.Label(coord_row,
            text=f"{self.selected_lat.get():.4f}, {self.selected_lon.get():.4f}",
            bg=COLORS["card"], fg=COLORS["accent"],
            font=("Segoe UI", 9, "bold"))
        self.coord_lbl.pack(side="left", padx=6)
        self.city_lbl = tk.Label(coord_row, text="(Toshkent)", bg=COLORS["card"],
                                 fg=COLORS["text"], font=("Segoe UI", 9))
        self.city_lbl.pack(side="left")

        map_frame = tk.Frame(parent, bg=COLORS["bg"])
        map_frame.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.map_widget = tkintermapview.TkinterMapView(
            map_frame, width=880, height=380, corner_radius=8)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_position(41.2995, 69.2401)
        self.map_widget.set_zoom(12)
        self.map_widget.add_left_click_map_command(self._on_map_click)
        self.map_marker = self.map_widget.set_marker(41.2995, 69.2401, text="Toshkent — Markaz")

    def _on_map_click(self, coords):
        lat, lon = coords
        self._set_location(lat, lon)
        reverse_geocode(lat, lon, lambda d: self.after(0, lambda: self._update_city_label(d)))

    def _set_location(self, lat, lon, city_text=None):
        self.selected_lat.set(round(lat, 4))
        self.selected_lon.set(round(lon, 4))
        self.coord_lbl.config(text=f"{lat:.4f}, {lon:.4f}")
        label = city_text or f"{lat:.3f}, {lon:.3f}"
        if city_text:
            self.city_lbl.config(text=f"({city_text})")
            self.lbl_chosen.config(text=f"{city_text}  ({lat:.4f}, {lon:.4f})")
        else:
            self.lbl_chosen.config(text=f"{lat:.4f}, {lon:.4f}")
        if self.map_marker:
            self.map_marker.delete()
        self.map_marker = self.map_widget.set_marker(lat, lon, text=label)

    def _update_city_label(self, data):
        city  = data.get("city", "")
        state = data.get("state", "")
        full  = f"{city}, {state}" if state else city
        if full.strip():
            self.city_lbl.config(text=f"({full})")
            lat = self.selected_lat.get()
            lon = self.selected_lon.get()
            self.lbl_chosen.config(text=f"{full}  ({lat:.4f}, {lon:.4f})")
            if self.map_marker:
                self.map_marker.delete()
            self.map_marker = self.map_widget.set_marker(lat, lon, text=full)

    def _select_district(self):
        name = self.district_var.get()
        for d in UZ_DISTRICTS:
            if d[0] == name:
                self.map_widget.set_position(d[1], d[2])
                self.map_widget.set_zoom(13)
                self._set_location(d[1], d[2], city_text=d[0])
                break

    def _fetch_location(self):
        self.ip_status.config(text="Aniqlanmoqda...", fg=COLORS["muted"])
        def on_result(data):
            if "error" in data:
                self.ip_status.config(text="Xato: " + data["error"], fg=COLORS["bad"])
                return
            lat  = data["lat"]; lon = data["lon"]
            city = data.get("city", "")
            self.ip_status.config(text=f"✓ {city}", fg=COLORS["good"])
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(13)
            self._set_location(lat, lon, city_text=city)
        get_location_by_ip(lambda d: self.after(0, lambda: on_result(d)))

    def _card(self, parent, title=None, padx=12):
        wrapper = tk.Frame(parent, bg=COLORS["bg"]); wrapper.pack(fill="x", pady=4)
        card = tk.Frame(wrapper, bg=COLORS["card"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill="x")
        if title:
            tk.Label(card, text=title, bg=COLORS["card"], fg=COLORS["accent"],
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=padx, pady=(10,2))
            ttk.Separator(card, orient="horizontal").pack(fill="x", padx=padx)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="x", padx=padx, pady=(4,10))
        return inner

    def _slider(self, parent, label, var, mn, mx, suffix=""):
        tk.Label(parent, text=label, bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(8,2))
        row = tk.Frame(parent, bg=COLORS["card"]); row.pack(fill="x")
        val_lbl = tk.Label(row, text=str(var.get())+suffix, bg=COLORS["card"],
                           fg=COLORS["text"], font=("Segoe UI", 10, "bold"), width=8)
        val_lbl.pack(side="right")
        def update(v):
            val_lbl.config(text=str(int(float(v)))+suffix); self._calculate()
        ttk.Scale(row, from_=mn, to=mx, variable=var,
                  orient="horizontal", command=update).pack(side="left", fill="x", expand=True)

    def _slider_float(self, parent, label, var, mn, mx):
        tk.Label(parent, text=label, bg=COLORS["card"], fg=COLORS["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(8,2))
        row = tk.Frame(parent, bg=COLORS["card"]); row.pack(fill="x")
        val_lbl = tk.Label(row, text=f"{var.get():.2f}", bg=COLORS["card"],
                           fg=COLORS["text"], font=("Segoe UI", 10, "bold"), width=8)
        val_lbl.pack(side="right")
        def update(v):
            val_lbl.config(text=f"{float(v):.2f}"); self._calculate()
        ttk.Scale(row, from_=mn, to=mx, variable=var,
                  orient="horizontal", command=update).pack(side="left", fill="x", expand=True)

    def _calculate(self, pr_override=None):
        try:
            r = calc_signal(self.tech_var.get(), self.dist_var.get(),
                            self.bdens_var.get(), pt_override=self.pt_var.get(),
                            pr_override=pr_override)
        except Exception as e:
            messagebox.showerror("Xato", str(e)); return
        self.lbl["PL"].config(text=f"{r['PL']:.1f} dB")
        self.lbl["BL"].config(text=f"{r['BL']:.1f} dB")
        self.lbl["Pr"].config(text=f"{r['Pr']:.1f} dBm")
        self.lbl["SNR"].config(text=f"{r['SNR']:.1f} dB")
        tp = r["throughput"]
        self.lbl["TP"].config(text=f"{tp/1000:.2f} Gb/s" if tp >= 1000 else f"{tp:.1f} Mb/s")
        self.lbl["Q"].config(text=r["quality"], fg=r["q_color"])
        self.after(50, lambda: self._update_bars(r))

    def _update_bars(self, r):
        pr_pct  = max(0, min(1, (r["Pr"]  + 130) / 90))
        snr_pct = max(0, min(1, (r["SNR"] + 10)  / 60))
        tp_pct  = max(0, min(1, r["throughput"] / (r["bw"] * 12)))
        for key, pct in [("Pr", pr_pct), ("SNR", snr_pct), ("TP", tp_pct)]:
            cv, rect, _ = self.bars[key]
            w = cv.winfo_width() or 400
            cv.coords(rect, 0, 0, int(w * pct), 18)
            color = (COLORS["bad"] if pct < 0.25 else COLORS["mid"] if pct < 0.5
                     else COLORS["ok"] if pct < 0.75 else COLORS["good"])
            cv.itemconfig(rect, fill=color)

    def _apply_rsrp(self):
        try:
            self._calculate(pr_override=float(self.rsrp_var.get()))
        except ValueError:
            messagebox.showerror("Xato", "RSRP qiymati son bo'lishi kerak (masalan: -85)")

if __name__ == "__main__":
    app = App()
    app.mainloop()