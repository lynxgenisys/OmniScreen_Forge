import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import os
import json
import ffmpeg
from PIL import Image, ImageTk
from screeninfo import get_monitors
import sv_ttk
import threading
import queue
import re
import subprocess

# --- Data Structures ---

class MonitorConfig:
    def __init__(self, name="Monitor", diag=24.0, res_w=1920, res_h=1080, x=0.0, y=0.0, os_x=0, os_y=0):
        self.name = name
        self.diag = diag
        self.res_w = res_w
        self.res_h = res_h
        self.x = x
        self.y = y
        self.os_x = os_x
        self.os_y = os_y

    @property
    def phys_w(self):
        try:
            ppi = math.sqrt(self.res_w**2 + self.res_h**2) / self.diag
            return self.res_w / ppi
        except ZeroDivisionError:
            return 16.0

    @property
    def phys_h(self):
        try:
            ppi = math.sqrt(self.res_w**2 + self.res_h**2) / self.diag
            return self.res_h / ppi
        except ZeroDivisionError:
            return 9.0

    def to_dict(self):
        return {
            "name": self.name,
            "diag": self.diag,
            "res_w": self.res_w,
            "res_h": self.res_h,
            "x": self.x,
            "y": self.y,
            "os_x": self.os_x,
            "os_y": self.os_y
        }

    @classmethod
    def from_dict(cls, data):
        if 'offset_y' in data: del data['offset_y']
        if 'x' not in data: data['x'] = 0.0
        if 'y' not in data: data['y'] = 0.0
        if 'os_x' not in data: data['os_x'] = 0
        if 'os_y' not in data: data['os_y'] = 0
        return cls(**data)

# --- GUI Application ---

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, bg="#1A1A1A", fg="#00FFFF", 
                 activebackground="#2A2A2A", activeforeground="#FF00FF",
                 font=("Segoe UI", 10, "bold"), radius=10, border_color="#404040", 
                 border_width=1, padx=10, pady=5, **kwargs):
        
        # Estimate size
        self.temp_label = tk.Label(parent, text=text, font=font)
        req_w = self.temp_label.winfo_reqwidth() + (padx * 2)
        req_h = self.temp_label.winfo_reqheight() + (pady * 2)
        self.temp_label.destroy()
        
        # Get parent background or default to main window color
        try:
            parent_bg = parent.cget("bg")
        except:
            parent_bg = "#1c1c1c"
            
        super().__init__(parent, width=req_w, height=req_h, bg=parent_bg, highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.active_bg = activebackground
        self.active_fg = activeforeground
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.text = text
        self.font = font
        
        self.rect_id = None
        self.text_id = None
        
        self.bind("<Configure>", self.draw)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def round_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
        return self.create_polygon(points, **kwargs, smooth=True)

    def draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10: return
        
        self.rect_id = self.round_rectangle(self.border_width, self.border_width, w-self.border_width, h-self.border_width, 
                                            r=self.radius, fill=self.bg_color, outline=self.border_color, width=self.border_width)
        self.text_id = self.create_text(w/2, h/2, text=self.text, font=self.font, fill=self.fg_color)
        
    def on_enter(self, e):
        self.itemconfig(self.rect_id, fill=self.active_bg, outline=self.active_fg)
        self.itemconfig(self.text_id, fill=self.active_fg)
        self.config(cursor="hand2")
        
    def set_colors(self, bg=None, fg=None, border=None):
        if bg:
            self.bg_color = bg
            self.itemconfig(self.rect_id, fill=bg)
        if fg:
            self.fg_color = fg
            self.itemconfig(self.text_id, fill=fg)
        if border:
            self.border_color = border
            self.itemconfig(self.rect_id, outline=border)

    def set_text(self, text):
        self.text = text
        self.itemconfig(self.text_id, text=text)

    def on_leave(self, e):
        self.itemconfig(self.rect_id, fill=self.bg_color, outline=self.border_color)
        self.itemconfig(self.text_id, fill=self.fg_color)
        self.config(cursor="")
        
    def on_click(self, e):
        self.itemconfig(self.rect_id, fill=self.border_color) # darker feedback
        
    def on_release(self, e):
        self.itemconfig(self.rect_id, fill=self.active_bg)
        if self.command:
            self.command()

class OmniScreenForgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OmniScreen Forge - Universal Multi-Monitor Rescaler")
        self.root.geometry("1100x950")
        
        self.apply_window_dark_titlebar(self.root)
        
        # Apply modern dark theme
        sv_ttk.set_theme("dark")
        self.root.configure(bg="#1c1c1c")

        # Load persisted settings
        self.settings_file = "bezel_settings.json"
        self.last_dirs = {"media_in": os.path.expanduser("~"), "preset_out": os.path.expanduser("~"), "render_out": os.path.expanduser("~")}
        self.load_settings()
        
        self.monitors = []
        self.input_file = tk.StringVar()
        self.bezel_gap = tk.DoubleVar(value=0.0) # Physical inches
        self.ui_vars = {}

        # Drag state
        self.drag_data = {"idx": -1, "mode": None, "start_x": 0, "start_y": 0, "orig_x": 0, "orig_y": 0, "orig_diag": 0}
        self.view_scale = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        
        # Bounding Box cache for draw_preview
        self.bb_min_x = 0
        self.bb_min_y = 0
        self.bb_max_x = 10
        self.bb_max_y = 10
        self.box_w = 10
        self.box_h = 10
        
        self.setup_ui()
        self.draw_preview()
        self.mon_canvas.bind('<Configure>', lambda e: self.mon_canvas.configure(scrollregion=self.mon_canvas.bbox("all")))
        
        last_preset = self.last_dirs.get("last_preset_file")
        if last_preset and os.path.exists(last_preset):
            try:
                with open(last_preset, 'r') as f:
                    self.monitors = [MonitorConfig.from_dict(d) for d in json.load(f)]
                self.refresh_monitor_list()
            except Exception as e:
                print(f"Failed to load last preset: {e}")
                self.auto_detect_monitors()
        else:
            self.auto_detect_monitors()

    def create_bordered_button(self, parent, text, command, **kwargs):
        # Override bg to match parent mostly
        btn_kwargs = {
            "bg": "#1A1A1A",
            "fg": "#00FFFF",
            "font": ("Segoe UI", 10, "bold"),
            "radius": 12,
            "border_color": "#404040",
            "border_width": 1,
            "activebackground": "#2A2A2A",
            "activeforeground": "#FF00FF"
        }
        btn_kwargs.update(kwargs)
        btn = RoundedButton(parent, text=text, command=command, **btn_kwargs)
        return btn

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        
        # Setup Menu
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Instructions", command=self.show_instructions)
        self.help_menu.add_command(label="Changelog", command=self.show_changelog)
        self.help_menu.add_command(label="About", command=self.show_about)
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Title and Coffee Button
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        title_str = "OmniScreen Forge"
        self.title_lbls = []
        self.title_base_colors = []
        for i, char in enumerate(title_str):
            t = i / max(1, len(title_str) - 1)
            r = int(0 + t * 255)
            g = int(255 - t * 255)
            b = 255
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            lbl = tk.Label(title_frame, text=char, font=("Segoe UI", 24, "bold"), fg=hex_color, bg="#1c1c1c", padx=0, pady=0)
            lbl.pack(side=tk.LEFT)
            self.title_lbls.append(lbl)
            self.title_base_colors.append(hex_color)
            
        try:
            from PIL import Image, ImageTk, ImageChops, ImageOps
            import os, webbrowser
            logo_path = os.path.join(os.path.dirname(__file__), "LynxGenLOGO.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path).convert("RGBA")
                
                # Create a solid green-cyan image
                blue_bg = Image.new("RGBA", img.size, "#00A86B")
                # Use the original image's alpha channel
                alpha = img.split()[3]
                blue_bg.putalpha(alpha)
                img = blue_bg
                
                img = img.resize((75, 75), Image.Resampling.LANCZOS)
                self.base_logo_img = img
                self.logo_photo = ImageTk.PhotoImage(img)
                
                self.logo_lbl = tk.Label(header_frame, image=self.logo_photo, bg="#1c1c1c", padx=0, pady=0, cursor="hand2")
                self.logo_lbl.pack(side=tk.LEFT, padx=(105, 30))
                self.logo_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://www.youtube.com/@LynxGenisys"))
                
            logo2_path = os.path.join(os.path.dirname(__file__), "GradMorls-Logo.png")
            if os.path.exists(logo2_path):
                img2 = Image.open(logo2_path)
                img2.thumbnail((250, 75), Image.Resampling.LANCZOS)
                self.base_logo2_img = img2
                self.logo2_photo = ImageTk.PhotoImage(img2)
                
                self.logo2_lbl = tk.Label(header_frame, image=self.logo2_photo, bg="#1c1c1c", padx=0, pady=0, cursor="hand2")
                self.logo2_lbl.pack(side=tk.LEFT, padx=(0, 0))
                self.logo2_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://gradient-morals.pages.dev/"))
                
            # Start shimmer loop
            self.root.after(30000, self.trigger_global_shimmer)
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        import webbrowser
        
        self.qr_btn = RoundedButton(
            header_frame, 
            text="QR", 
            command=self.show_qr,
            bg="#0A0A0A", 
            fg="#FF00FF", 
            font=("Segoe UI", 16, "bold"),
            radius=15,
            border_width=2,
            border_color="#FF00FF",
            activebackground="#050505",
            activeforeground="#00FFFF",
            padx=20,
            pady=8
        )
        self.qr_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.coffee_btn = RoundedButton(
            header_frame, 
            text="⚡ Buy me an energy drink!", 
            command=lambda: webbrowser.open("https://www.buymeacoffee.com/LynxGen"),
            bg="#0A0A0A", 
            fg="#00FFFF", 
            font=("Segoe UI", 16, "bold"),
            radius=15,
            border_width=2,
            border_color="#00FFFF",
            activebackground="#050505",
            activeforeground="#FF00FF",
            padx=20,
            pady=8
        )
        self.coffee_btn.pack(side=tk.RIGHT)
        
        self.shimmer_step = 0
        self.start_shimmer()

        file_frame = ttk.LabelFrame(main_frame, text="Input File", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Entry(file_frame, textvariable=self.input_file, width=80).pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        self.create_bordered_button(file_frame, text="Browse Media...", command=self.browse_file).pack(side=tk.LEFT)

        mon_container = ttk.Frame(main_frame)
        mon_container.pack(fill=tk.BOTH, expand=True, pady=0)
        
        self.monitors_frame = ttk.LabelFrame(mon_container, text="Physical Monitor Setup", padding="10")
        self.monitors_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 15))
        
        # Add a canvas and scrollbar for the monitor list
        self.mon_canvas = tk.Canvas(self.monitors_frame, width=390, highlightthickness=0)
        self.mon_scrollbar = ttk.Scrollbar(self.monitors_frame, orient="vertical", command=self.mon_canvas.yview)
        self.mon_list_frame = ttk.Frame(self.mon_canvas)
        
        self.mon_list_frame.bind(
            "<Configure>",
            lambda e: self.mon_canvas.configure(scrollregion=self.mon_canvas.bbox("all"))
        )
        self.mon_canvas.create_window((0, 0), window=self.mon_list_frame, anchor="nw")
        self.mon_canvas.configure(yscrollcommand=self.mon_scrollbar.set)
        
        self.mon_canvas.pack(side="left", fill="both", expand=True)
        self.mon_scrollbar.pack(side="right", fill="y")

        controls_frame = ttk.Frame(self.monitors_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        self.create_bordered_button(controls_frame, text="+ Add Monitor", command=self.add_monitor_ui).pack(side=tk.LEFT, padx=5)
        self.create_bordered_button(controls_frame, text="Auto-Detect Monitors", command=self.auto_detect_monitors).pack(side=tk.LEFT, padx=5)

        self.preview_frame = ttk.LabelFrame(mon_container, text="2D Layout Canvas (Drag to Move, Corner to Resize)", padding="5")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Sleek dark background for the canvas
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="#050505", highlightthickness=0, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<ButtonPress-1>", self.on_press)
        self.preview_canvas.bind("<B1-Motion>", self.on_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_release)

        settings_frame = ttk.LabelFrame(main_frame, text="Compositor Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Bezel Gap
        ttk.Label(settings_frame, text="Bezel Gap (inches):").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Scale(settings_frame, from_=0.0, to=5.0, variable=self.bezel_gap, orient=tk.HORIZONTAL, command=lambda e: self.draw_preview()).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(settings_frame, textvariable=self.bezel_gap).pack(side=tk.LEFT, padx=(5, 20))
        
        # Audio Toggle
        self.include_audio = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Include Source Audio", variable=self.include_audio).pack(side=tk.RIGHT, padx=5)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(20, 10))
        self.render_btn = self.create_bordered_button(controls_frame, text="Render Media!", command=self.render_ffmpeg, bg="#bf40ff", fg="#050505", border_color="#bf40ff", activebackground="#00FFFF", activeforeground="#050505", font=("Segoe UI", 12, "bold"))
        self.render_btn.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(controls_frame, text="Save JSON Preset", command=self.save_preset).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="Load JSON Preset", command=self.load_preset).pack(side=tk.LEFT)
        
        # --- Progress & Log Output ---
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=0)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = ttk.Label(self.progress_frame, text="Ready", font=("Segoe UI", 9))
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))
        
        self.log_text = tk.Text(self.progress_frame, height=8, bg="#121212", fg="#E0E0E0", font=("Consolas", 9), state=tk.DISABLED)
        self.log_scroll = ttk.Scrollbar(self.progress_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log queue for thread-safe UI updates
        self.log_queue = queue.Queue()
        self.is_rendering = False
        
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except ImportError:
            pass

    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if not files: return
        filepath = files[0]
            
        valid_exts = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.gif')
        if filepath.lower().endswith(valid_exts):
            self.input_file.set(filepath)
            self.update_render_btn()
            self.draw_preview()

    # --- Interaction Logic ---
    
    def on_press(self, event):
        for i, mon in reversed(list(enumerate(self.monitors))):
            x1 = mon.x * self.view_scale + self.view_offset_x
            y1 = mon.y * self.view_scale + self.view_offset_y
            x2 = x1 + mon.phys_w * self.view_scale
            y2 = y1 + mon.phys_h * self.view_scale
            
            handle_size = 12
            if x2 - handle_size <= event.x <= x2 and y2 - handle_size <= event.y <= y2:
                self.drag_data = {"idx": i, "mode": "resize", "start_x": event.x, "start_y": event.y, "orig_diag": mon.diag}
                return
            
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drag_data = {"idx": i, "mode": "move", "start_x": event.x, "start_y": event.y, "orig_x": mon.x, "orig_y": mon.y}
                return
        self.drag_data["mode"] = None

    def on_drag(self, event):
        idx = self.drag_data["idx"]
        if idx == -1 or not self.drag_data["mode"]: return
        
        mon = self.monitors[idx]
        
        if self.drag_data["mode"] == "move":
            dx_inch = (event.x - self.drag_data["start_x"]) / self.view_scale
            dy_inch = (event.y - self.drag_data["start_y"]) / self.view_scale
            mon.x = self.drag_data["orig_x"] + dx_inch
            mon.y = self.drag_data["orig_y"] + dy_inch
            self.refresh_ui_vars()
            self.draw_preview()
            
        elif self.drag_data["mode"] == "resize":
            dx_inch = (event.x - self.drag_data["start_x"]) / self.view_scale
            old_w = mon.phys_w
            new_w = max(1.0, old_w + dx_inch)
            mon.diag = self.drag_data["orig_diag"] * (new_w / old_w)
            self.refresh_ui_vars()
            self.draw_preview()

    def on_release(self, event):
        self.drag_data["mode"] = None
        self.draw_preview() # Force re-center

    def draw_preview(self):
        self.preview_canvas.delete("all")
        if not self.monitors: return

        cw = self.preview_canvas.winfo_width()
        ch = self.preview_canvas.winfo_height()
        if cw < 10 or ch < 10:
            self.root.after(100, self.draw_preview)
            return

        # Do not recalculate bounds during drag, to prevent screen oscillation!
        if self.drag_data["mode"] is None:
            self.bb_min_x = min([m.x for m in self.monitors] + [0])
            self.bb_min_y = min([m.y for m in self.monitors] + [0])
            self.bb_max_x = max([m.x + m.phys_w for m in self.monitors] + [1])
            self.bb_max_y = max([m.y + m.phys_h for m in self.monitors] + [1])
            self.box_w = self.bb_max_x - self.bb_min_x
            self.box_h = self.bb_max_y - self.bb_min_y
            
            self.view_scale = min(cw * 0.9 / max(self.box_w, 0.1), ch * 0.9 / max(self.box_h, 0.1))
            self.view_offset_x = (cw - self.box_w * self.view_scale) / 2 - self.bb_min_x * self.view_scale
            self.view_offset_y = (ch - self.box_h * self.view_scale) / 2 - self.bb_min_y * self.view_scale

        # Draw physical bounding box backdrop
        bb_x1 = self.bb_min_x * self.view_scale + self.view_offset_x
        bb_y1 = self.bb_min_y * self.view_scale + self.view_offset_y
        bb_x2 = self.bb_max_x * self.view_scale + self.view_offset_x
        bb_y2 = self.bb_max_y * self.view_scale + self.view_offset_y
        self.preview_canvas.create_rectangle(bb_x1, bb_y1, bb_x2, bb_y2, outline="#404040", dash=(4,4), fill="#121212")
        
        for i, m in enumerate(self.monitors):
            x1 = m.x * self.view_scale + self.view_offset_x
            y1 = m.y * self.view_scale + self.view_offset_y
            w = m.phys_w * self.view_scale
            h = m.phys_h * self.view_scale
            
            x2 = x1 + w
            y2 = y1 + h
            
            # Gradient Morals theme colors
            is_dragged = self.drag_data["idx"] == i
            fill_color = "#0A0A0A" if not is_dragged else "#1A1A1A"
            border_color = "#00FFFF" if not is_dragged else "#FF00FF"
            text_color = "#ECF0F1"
            subtext_color = "#BDC3C7"
            os_color = "#FF00FF"
            
            self.preview_canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=border_color, width=2)
            self.preview_canvas.create_text((x1+x2)/2, y1 + 20, text=f"Screen {i+1} ({m.diag:.1f}\")", fill=text_color, font=("Segoe UI", 10, "bold"))
            self.preview_canvas.create_text((x1+x2)/2, y1 + 40, text=f"Native OS: {m.res_w}x{m.res_h}", fill=subtext_color, font=("Segoe UI", 9))
            self.preview_canvas.create_text((x1+x2)/2, y1 + 60, text=f"Virtual X,Y: {m.os_x}, {m.os_y}", fill=os_color, font=("Segoe UI", 8))
            
            # Resize notch
            notch_color = border_color
            self.preview_canvas.create_polygon(x2-12, y2, x2, y2, x2, y2-12, fill=notch_color)

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.last_dirs, f)
        except:
            pass
            
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.last_dirs.update(data)
            except:
                pass

    def apply_window_dark_titlebar(self, window):
        try:
            import ctypes
            window.update() # Ensure window is drawn so hwnd is available
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE is 20 in Windows 11, 19 in Windows 10
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass # Fails gracefully on older/non-windows OS

    def show_instructions(self):
        top = tk.Toplevel(self.root)
        top.title("Instructions - OmniScreen Forge")
        top.geometry("750x600")
        top.configure(bg="#050505")
        self.apply_window_dark_titlebar(top)
        
        lbl = tk.Label(top, text="User Guide & Mechanics", font=("Segoe UI", 16, "bold"), fg="#FF00FF", bg="#050505")
        lbl.pack(pady=(10, 5))
        
        txt = tk.Text(top, bg="#1A1A1A", fg="#ECF0F1", font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
            txt.insert(tk.END, content)
        except Exception:
            txt.insert(tk.END, "README.md not found in the project directory.")
        
        txt.config(state=tk.DISABLED)

    def show_changelog(self):
        top = tk.Toplevel(self.root)
        top.title("Changelog - OmniScreen Forge")
        top.geometry("700x500")
        top.configure(bg="#050505")
        self.apply_window_dark_titlebar(top)
        
        lbl = tk.Label(top, text="Development Changelog", font=("Segoe UI", 16, "bold"), fg="#00FFFF", bg="#050505")
        lbl.pack(pady=(10, 5))
        
        txt = tk.Text(top, bg="#1A1A1A", fg="#ECF0F1", font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                content = f.read()
            txt.insert(tk.END, content)
        except Exception:
            txt.insert(tk.END, "CHANGELOG.md not found in the project directory.")
        
        txt.config(state=tk.DISABLED)

    def show_about(self):
        top = tk.Toplevel(self.root)
        top.title("About - OmniScreen Forge")
        top.geometry("750x800")
        top.configure(bg="#050505")
        top.resizable(False, False)
        self.apply_window_dark_titlebar(top)
        
        # Center window
        x = (self.root.winfo_screenwidth() - 750) // 2
        y = (self.root.winfo_screenheight() - 800) // 2
        top.geometry(f"+{x}+{y}")
        
        lbl = tk.Label(top, text="OmniScreen Forge", font=("Segoe UI", 26, "bold"), fg="#FF00FF", bg="#050505")
        lbl.pack(pady=(20, 5))
        
        lines = [
            "Universal Multi-Monitor Rescaler",
            "Version 1.1.0",
            "Developed specifically to solve physical",
            "monitor dimension disparities."
        ]
        
        for i, text in enumerate(lines):
            t = i / max(1, len(lines) - 1)
            r = int(0 + t * 255)
            g = int(255 - t * 255)
            b = 255
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            tk.Label(top, text=text, font=("Segoe UI", 14), fg=hex_color, bg="#050505").pack(pady=(0 if i > 0 else 5, 2))
            
        story_frame = tk.Frame(top, bg="#000000", highlightthickness=1, highlightbackground="#333333")
        story_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        story_text = (
            "I have been using the \"Lively Wallpaper\" program for a few years.\n"
            "However, my monitor setup is a 24\" stereoscopic 3d Led tv, (the ole playstation one,) a 21\" acer monitor beside that, and then i have a 42\" tv centered, above/behind those.\n\n"
            "I could arrange the layout in windows/nvidia, but not scale the background, so any background vids and images looked wonky, and distorted.\n"
            "I couldnt find a free option to fix this, so we developed this one afternoon.\n\n"
            "It gets your screen(s) and layout info etc, and then projection maps the video, so it displays properly. or at least in perspective on your background canvas.\n\n"
            "(I actualy got he idea when I stumbled across a video about projection mapping with projectors etc.)\n\n"
            "Anyways, enjoy!\n\n"
            "Feel free to hit that button top right corner and fire me off an energy drink!\n\n"
            "(Its 3:52 am as i write this.. I work at 8...)\n"
            " *Sighs* where does the time go... ?\"\n\n"
            "           ~L~"
        )
        msg = tk.Message(story_frame, text=story_text, bg="#000000", fg="#009900", font=("Consolas", 12), width=650, justify=tk.LEFT)
        msg.pack(padx=10, pady=10)
        
        btn = self.create_bordered_button(top, text="Close", command=top.destroy, padx=20)
        btn.pack(pady=(0, 10))

    def start_shimmer(self):
        # Calculate color gradient from Cyan (#00FFFF) to Magenta (#FF00FF)
        loop_length = 40 # Total steps for a full cycle back and forth
        
        # Determine current phase (0 to 1) based on alternating triangle wave pattern
        cycle_pos = self.shimmer_step % loop_length
        if cycle_pos < loop_length / 2:
            t = cycle_pos / (loop_length / 2)
        else:
            t = 1.0 - ((cycle_pos - (loop_length / 2)) / (loop_length / 2))
            
        # Stepping colors: r goes from 0 to 255. g goes from 255 to 0. b remains 255.
        r = int(0 + t * 255)
        g = int(255 - t * 255)
        b = 255
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.current_ambient_color = hex_color
        
        # Apply to buttons
        try:
            self.qr_btn.set_colors(fg=hex_color, border=hex_color)
            self.coffee_btn.set_colors(fg=hex_color, border=hex_color)
        except:
            pass # App closing
            
        # Make the render button dynamically shimmer too if it exists
        if hasattr(self, 'render_btn') and "!" in self.render_btn.text:
            self.render_btn.set_colors(bg=hex_color, border=hex_color)
            
        self.shimmer_step += 1
        self.root.after(100, self.start_shimmer)

    def trigger_global_shimmer(self):
        self.global_shimmer_phase = 0
        self.animate_global_shimmer()

    def draw_shimmer_frame(self, progress, base_img, lbl, photo_attr_name):
        from PIL import Image, ImageTk, ImageDraw, ImageChops
        overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = base_img.size
        center_x = int(progress * (w + h + 80)) - int(h/2) - 40
        
        # Widen the shimmer wave significantly
        draw.line([(center_x - 15, 0), (center_x - h - 15, h)], fill=(0, 255, 255, 110), width=25)
        draw.line([(center_x,      0), (center_x - h,      h)], fill=(255, 255, 255, 220), width=18)
        draw.line([(center_x + 15, 0), (center_x - h + 15, h)], fill=(255, 0, 255, 110), width=25)
        base_rgba = base_img.convert('RGBA')
        r, g, b, alpha = base_rgba.split()
        overlay_alpha = overlay.split()[3]
        overlay.putalpha(ImageChops.darker(overlay_alpha, alpha))
        shimmer_img = Image.alpha_composite(base_rgba, overlay)
        photo = ImageTk.PhotoImage(shimmer_img)
        setattr(self, photo_attr_name, photo)
        lbl.config(image=photo)

    def animate_global_shimmer(self):
        self.is_global_shimmering = True
        
        if self.global_shimmer_phase > 60:
            self.is_global_shimmering = False
            self.root.after(30000, self.trigger_global_shimmer)
            if hasattr(self, 'logo_photo') and hasattr(self, 'base_logo_img'):
                from PIL import ImageTk
                self.logo_photo = ImageTk.PhotoImage(self.base_logo_img)
                self.logo_lbl.config(image=self.logo_photo)
            if hasattr(self, 'logo2_photo') and hasattr(self, 'base_logo2_img'):
                from PIL import ImageTk
                self.logo2_photo = ImageTk.PhotoImage(self.base_logo2_img)
                self.logo2_lbl.config(image=self.logo2_photo)
            for i, lbl in enumerate(getattr(self, 'title_lbls', [])):
                lbl.config(fg=self.title_base_colors[i])
            return

        progress = self.global_shimmer_phase / 60.0

        for i, lbl in enumerate(getattr(self, 'title_lbls', [])):
            char_pos = (i / len(self.title_lbls)) * 0.4
            dist = abs(progress - char_pos)
            if dist < 0.05:
                lbl.config(fg="#FFFFFF")
            elif dist < 0.1:
                lbl.config(fg="#00FFFF")
            else:
                lbl.config(fg=self.title_base_colors[i])

        if hasattr(self, 'base_logo_img'):
            if 0.35 <= progress <= 0.65:
                logo_prog = (progress - 0.35) / 0.30
                self.draw_shimmer_frame(logo_prog, self.base_logo_img, self.logo_lbl, 'logo_photo')

        if hasattr(self, 'base_logo2_img'):
            if 0.65 <= progress <= 0.95:
                logo_prog = (progress - 0.65) / 0.30
                self.draw_shimmer_frame(logo_prog, self.base_logo2_img, self.logo2_lbl, 'logo2_photo')

        self.global_shimmer_phase += 1
        self.root.after(40, self.animate_global_shimmer)

    def show_qr(self):
        qr_path = "qr-code.png"
        if not os.path.exists(qr_path):
            messagebox.showerror("Error", f"Could not find {qr_path} in the project directory.")
            return
            
        top = tk.Toplevel(self.root)
        top.title("LynxGen QR")
        top.configure(bg="#050505")
        self.apply_window_dark_titlebar(top)
        
        # Get screen width and height
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        # Target size: half screen min dimension
        target_size = min(screen_w, screen_h) // 2
        
        try:
            img = Image.open(qr_path)
            img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            
            top.qr_image = ImageTk.PhotoImage(img)
            
            lbl = tk.Label(top, image=top.qr_image, bg="#050505", borderwidth=0)
            lbl.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Center the window
            x = (screen_w - img.width - 40) // 2
            y = (screen_h - img.height - 40) // 2
            top.geometry(f"{img.width + 40}x{img.height + 40}+{x}+{y}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load QR code:\n{str(e)}")
            top.destroy()

    def browse_file(self):
        filename = filedialog.askopenfilename(
            initialdir=self.last_dirs["media_in"],
            filetypes=[("All Supported Media", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.mpeg *.mpg *.jpg *.png *.jpeg *.bmp *.webp *.tiff *.gif"), 
                       ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.mpeg *.mpg *.gif"),
                       ("Image Files", "*.jpg *.png *.jpeg *.bmp *.webp *.tiff"),
                       ("All files", "*.*")]
        )
        if filename:
            self.last_dirs["media_in"] = os.path.dirname(filename)
            self.save_settings()
            
            self.input_file.set(filename)
            self.update_render_btn()
            self.draw_preview()
            
    def update_render_btn(self):
        input_path = self.input_file.get()
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff')):
            self.render_btn.set_text("Render Image (PIL)")
        elif input_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg', '.mpg', '.gif')):
            self.render_btn.set_text("Render Video (FFmpeg)")
        else:
            self.render_btn.set_text("Render Media!")

    def add_monitor_ui(self, config=None):
        if config is None:
            if self.monitors:
                max_x = max([m.x + m.phys_w for m in self.monitors])
                config = MonitorConfig(name=f"Monitor {len(self.monitors) + 1}", x=max_x + self.bezel_gap.get())
            else:
                config = MonitorConfig(name=f"Monitor 1")
        self.monitors.append(config)
        self.refresh_monitor_list()

    def refresh_ui_vars(self):
        for i, mon in enumerate(self.monitors):
            if i in self.ui_vars:
                self.ui_vars[i]['diag'].set(f"{mon.diag:.1f}")
                self.ui_vars[i]['x'].set(f"{mon.x:.1f}")
                self.ui_vars[i]['y'].set(f"{mon.y:.1f}")

    def refresh_monitor_list(self):
        for widget in self.mon_list_frame.winfo_children():
            widget.destroy()
        
        self.ui_vars = {}
        for i, mon in enumerate(self.monitors):
            f = ttk.Frame(self.mon_list_frame, padding="8", relief=tk.RAISED)
            f.pack(fill=tk.X, pady=4, padx=4)
            
            row1 = ttk.Frame(f)
            row1.pack(fill=tk.X, pady=(0, 5))
            ttk.Label(row1, text=f"Screen {i+1}", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=2)
            self.create_bordered_button(row1, text="X Remove", command=lambda idx=i: self.remove_monitor(idx), fg="#FF00FF").pack(side=tk.RIGHT, padx=2)
            
            row2 = ttk.Frame(f)
            row2.pack(fill=tk.X, pady=2)
            ttk.Label(row2, text="Diag (\"):").pack(side=tk.LEFT, padx=(0, 5))
            diag_str = tk.StringVar(value=f"{mon.diag:.1f}")
            e1 = ttk.Entry(row2, textvariable=diag_str, width=6)
            e1.pack(side=tk.LEFT, padx=(0, 15))
            
            ttk.Label(row2, text="Native Res:").pack(side=tk.LEFT, padx=(0, 5))
            resw_v = tk.IntVar(value=mon.res_w)
            e2 = ttk.Entry(row2, textvariable=resw_v, width=5)
            e2.pack(side=tk.LEFT, padx=1)
            ttk.Label(row2, text="x").pack(side=tk.LEFT)
            resh_v = tk.IntVar(value=mon.res_h)
            e3 = ttk.Entry(row2, textvariable=resh_v, width=5)
            e3.pack(side=tk.LEFT)

            row3 = ttk.Frame(f)
            row3.pack(fill=tk.X, pady=2)
            ttk.Label(row3, text="OS Virtual X,Y:").pack(side=tk.LEFT, padx=(0, 5))
            osx_v = tk.IntVar(value=mon.os_x)
            e4 = ttk.Entry(row3, textvariable=osx_v, width=6)
            e4.pack(side=tk.LEFT, padx=1)
            osy_v = tk.IntVar(value=mon.os_y)
            e5 = ttk.Entry(row3, textvariable=osy_v, width=6)
            e5.pack(side=tk.LEFT)

            row4 = ttk.Frame(f)
            row4.pack(fill=tk.X, pady=2)
            ttk.Label(row4, text="Physical X,Y:").pack(side=tk.LEFT, padx=(0, 5))
            x_str = tk.StringVar(value=f"{mon.x:.1f}")
            e6 = ttk.Entry(row4, textvariable=x_str, width=6)
            e6.pack(side=tk.LEFT, padx=1)
            y_str = tk.StringVar(value=f"{mon.y:.1f}")
            e7 = ttk.Entry(row4, textvariable=y_str, width=6)
            e7.pack(side=tk.LEFT)

            self.ui_vars[i] = {
                'diag': diag_str, 'resw': resw_v, 'resh': resh_v,
                'osx': osx_v, 'osy': osy_v, 'x': x_str, 'y': y_str
            }

            def update_from_entries(event=None, idx=i):
                try:
                    m = self.monitors[idx]
                    m.diag = float(self.ui_vars[idx]['diag'].get())
                    m.res_w = int(self.ui_vars[idx]['resw'].get())
                    m.res_h = int(self.ui_vars[idx]['resh'].get())
                    m.os_x = int(self.ui_vars[idx]['osx'].get())
                    m.os_y = int(self.ui_vars[idx]['osy'].get())
                    m.x = float(self.ui_vars[idx]['x'].get())
                    m.y = float(self.ui_vars[idx]['y'].get())
                    # Force center refresh
                    self.drag_data["mode"] = None
                    self.draw_preview()
                except ValueError: pass

            for entry in [e1, e2, e3, e4, e5, e6, e7]:
                entry.bind("<Return>", update_from_entries)
                entry.bind("<FocusOut>", update_from_entries)

        self.draw_preview()

    def remove_monitor(self, idx):
        self.monitors.pop(idx)
        self.refresh_monitor_list()

    def auto_detect_monitors(self):
        try:
            detected = get_monitors()
            if detected:
                self.monitors = []
                for m in detected:
                    diag = 24.0
                    if m.width_mm and m.height_mm:
                        diag = math.sqrt((m.width_mm / 25.4)**2 + (m.height_mm / 25.4)**2)
                    
                    phys_x = m.x / 100.0
                    phys_y = m.y / 100.0
                    
                    self.add_monitor_ui(MonitorConfig(
                        name=m.name or "Detected", 
                        diag=diag,
                        res_w=m.width, 
                        res_h=m.height,
                        x=phys_x,
                        y=phys_y,
                        os_x=m.x,
                        os_y=m.y
                    ))
        except Exception as e:
            print(f"Monitor detection failed: {e}")

    def save_preset(self):
        file_path = filedialog.asksaveasfilename(
            initialdir=self.last_dirs.get("presets", os.path.expanduser("~")),
            defaultextension=".json", 
            filetypes=[("JSON", "*.json")]
        )
        if file_path:
            self.last_dirs["presets"] = os.path.dirname(file_path)
            self.last_dirs["last_preset_file"] = file_path
            self.save_settings()
            with open(file_path, 'w') as f:
                json.dump([m.to_dict() for m in self.monitors], f)

    def load_preset(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.last_dirs.get("presets", os.path.expanduser("~")),
            filetypes=[("JSON", "*.json")]
        )
        if file_path:
            self.last_dirs["presets"] = os.path.dirname(file_path)
            self.last_dirs["last_preset_file"] = file_path
            self.save_settings()
            with open(file_path, 'r') as f:
                self.monitors = [MonitorConfig.from_dict(d) for d in json.load(f)]
                self.refresh_monitor_list()

    def get_reference_ppi(self):
        if not self.monitors: return 100
        return max([math.sqrt(m.res_w**2 + m.res_h**2) / m.diag for m in self.monitors])

    def render_ffmpeg(self):
        input_path = self.input_file.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid input file.")
            return
        if not self.monitors:
            messagebox.showerror("Error", "Please add at least one monitor.")
            return

        is_img = input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'))
        
        if is_img:
            out_path = filedialog.asksaveasfilename(
                title="Save Composited Image",
                initialdir=self.last_dirs["media_out"],
                defaultextension=".png", 
                filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg *.jpeg"), ("Bitmap", "*.bmp"), ("WebP Image", "*.webp"), ("TIFF Image", "*.tiff"), ("All", "*.*")])
            if not out_path: return
            self.last_dirs["media_out"] = os.path.dirname(out_path)
            self.save_settings()
            
            self.render_image(input_path, out_path)
            return

        out_path = filedialog.asksaveasfilename(
            title="Save Rendered Video",
            initialdir=self.last_dirs["media_out"],
            defaultextension=".mp4", 
            filetypes=[("MP4 Video", "*.mp4"), ("MKV Video", "*.mkv"), ("AVI Video", "*.avi"), ("MOV Video", "*.mov"), ("GIF Animation", "*.gif"), ("All files", "*.*")])
        if not out_path: return
        self.last_dirs["media_out"] = os.path.dirname(out_path)
        self.save_settings()

        min_phys_x = min([m.x for m in self.monitors])
        min_phys_y = min([m.y for m in self.monitors])
        max_phys_x = max([m.x + m.phys_w for m in self.monitors])
        max_phys_y = max([m.y + m.phys_h for m in self.monitors])
        
        map_ppi = 100.0 # Virtual coordinate system scaling
        map_w = int(max(1, (max_phys_x - min_phys_x) * map_ppi))
        map_h = int(max(1, (max_phys_y - min_phys_y) * map_ppi))
        map_w += map_w % 2
        map_h += map_h % 2
        
        # Determine OS Virtual Desktop bounds (can be negative!)
        min_os_x = min([m.os_x for m in self.monitors])
        min_os_y = min([m.os_y for m in self.monitors])
        max_os_x = max([m.os_x + m.res_w for m in self.monitors])
        max_os_y = max([m.os_y + m.res_h for m in self.monitors])
        
        out_w = max(1, max_os_x - min_os_x)
        out_h = max(1, max_os_y - min_os_y)
        out_w += out_w % 2
        out_h += out_h % 2
        
        splits = "".join([f"[m{i+1}]" for i in range(len(self.monitors))])
        filter_str = f"[0:v]scale={map_w}:{map_h},split={len(self.monitors)}{splits};"
        filter_str += f" color=c=black:s={out_w}x{out_h}[bg];"
        
        for i, mon in enumerate(self.monitors):
            crop_w = int(mon.phys_w * map_ppi)
            crop_h = int(mon.phys_h * map_ppi)
            crop_x = int((mon.x - min_phys_x) * map_ppi)
            crop_y = int((mon.y - min_phys_y) * map_ppi)
            
            crop_w += crop_w % 2
            crop_h += crop_h % 2
            crop_x += crop_x % 2
            crop_y += crop_y % 2
            
            crop = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
            scale = f"scale={mon.res_w}:{mon.res_h}"
            
            out_v = f"v{i+1}"
            filter_str += f" [m{i+1}]{crop},{scale}[{out_v}];"
        
        curr_bg = "bg"
        for i, mon in enumerate(self.monitors):
            out_bg = f"ov{i+1}" if i < len(self.monitors) - 1 else "outv"
            paste_x = mon.os_x - min_os_x
            paste_y = mon.os_y - min_os_y
            # We must specify :shortest=1 so that the infinite black [bg] layer 
            # stops generating when the finite [v{i+1}] source video ends!
            filter_str += f" [{curr_bg}][v{i+1}]overlay={paste_x}:{paste_y}:shortest=1[{out_bg}];"
            curr_bg = out_bg
        
        try:
            # Build the raw ffmpeg command list to avoid Python wrapper dictionary map mangling
            cmd = ['ffmpeg', '-y', '-i', input_path, '-filter_complex', filter_str]
            
            # Map the combined video output
            cmd.extend(['-map', '[outv]'])
            
            # Map the original audio if requested
            if self.include_audio.get():
                cmd.extend(['-map', '0:a?'])
                cmd.extend(['-c:a', 'copy'])
                
            # Set video codec
            cmd.extend(['-c:v', 'libx264', out_path])

            if self.is_rendering:
                messagebox.showwarning("Warning", "Already rendering!")
                return
            
            self.is_rendering = True
            self.render_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            
            # We need the total duration to calculate progress.
            try:
                probe = ffmpeg.probe(input_path)
                video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                duration = float(video_stream['duration']) if video_stream and 'duration' in video_stream else float(probe['format']['duration'])
            except:
                duration = 0
            
            self.progress_label.config(text="Starting FFmpeg Engine...")

            threading.Thread(target=self._run_ffmpeg_thread, args=(cmd, out_path, duration), daemon=True).start()
            self._process_log_queue()
                
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to start FFmpeg:\n{str(e)}")
            self.is_rendering = False
            self.render_btn.config(state=tk.NORMAL)

    def _run_ffmpeg_thread(self, cmd, out_path, total_duration):
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

            for line in process.stdout:
                self.log_queue.put(("log", line))
                
                # Parse progress
                match = time_pattern.search(line)
                if match and total_duration > 0:
                    hrs, mins, secs = map(float, match.groups())
                    curr_time = hrs * 3600 + mins * 60 + secs
                    progress = min(100.0, (curr_time / total_duration) * 100)
                    self.log_queue.put(("progress", progress))

            process.wait()
            
            if process.returncode == 0:
                self.log_queue.put(("done", out_path))
            else:
                self.log_queue.put(("error", "FFmpeg exited with error status. See Engine Log."))
                
        except Exception as e:
            self.log_queue.put(("error", str(e)))

    def _process_log_queue(self):
        try:
            while True:
                msg_type, data = self.log_queue.get_nowait()
                
                if msg_type == "log":
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, data)
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                elif msg_type == "progress":
                    self.progress_var.set(data)
                    self.progress_label.config(text=f"Rendering: {data:.1f}%")
                elif msg_type == "done":
                    self.progress_var.set(100)
                    self.progress_label.config(text="Render Engine Complete!")
                    messagebox.showinfo("Success", f"Render complete: {data}")
                    self.is_rendering = False
                    self.render_btn.config(state=tk.NORMAL)
                    return
                elif msg_type == "error":
                    self.progress_label.config(text="Render Engine Failed!")
                    messagebox.showerror("FFmpeg Error", data)
                    self.is_rendering = False
                    self.render_btn.config(state=tk.NORMAL)
                    return
        except queue.Empty:
            pass
            
        if self.is_rendering:
            self.root.after(100, self._process_log_queue)

    def render_image(self, input_path, output_path):
        try:
            img = Image.open(input_path).convert('RGB')
            
            min_phys_x = min([m.x for m in self.monitors])
            min_phys_y = min([m.y for m in self.monitors])
            max_phys_x = max([m.x + m.phys_w for m in self.monitors])
            max_phys_y = max([m.y + m.phys_h for m in self.monitors])
            
            map_ppi = 100.0
            map_w = int(max(1, (max_phys_x - min_phys_x) * map_ppi))
            map_h = int(max(1, (max_phys_y - min_phys_y) * map_ppi))
            mapped_img = img.resize((map_w, map_h), Image.Resampling.LANCZOS)
            
            min_os_x = min([m.os_x for m in self.monitors])
            min_os_y = min([m.os_y for m in self.monitors])
            max_os_x = max([m.os_x + m.res_w for m in self.monitors])
            max_os_y = max([m.os_y + m.res_h for m in self.monitors])
            
            out_w = max(1, max_os_x - min_os_x)
            out_h = max(1, max_os_y - min_os_y)
            master_canvas = Image.new('RGB', (out_w, out_h), (0, 0, 0))
            
            for mon in self.monitors:
                crop_x = int((mon.x - min_phys_x) * map_ppi)
                crop_y = int((mon.y - min_phys_y) * map_ppi)
                crop_w = int(mon.phys_w * map_ppi)
                crop_h = int(mon.phys_h * map_ppi)
                
                seg = mapped_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
                seg_native = seg.resize((mon.res_w, mon.res_h), Image.Resampling.LANCZOS)
                
                paste_x = mon.os_x - min_os_x
                paste_y = mon.os_y - min_os_y
                master_canvas.paste(seg_native, (paste_x, paste_y))
            
            valid_img_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff')
            if not output_path.lower().endswith(valid_img_exts): 
                output_path += ".png"
            master_canvas.save(output_path)
            messagebox.showinfo("Success", f"Image saved: {output_path}")
            
        except Exception as e:
            messagebox.showerror("Image Error", f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
            root = tk.Tk()
    app = OmniScreenForgeApp(root)
    root.mainloop()
