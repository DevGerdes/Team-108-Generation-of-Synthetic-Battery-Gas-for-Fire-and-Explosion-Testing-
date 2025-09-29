import tkinter as tk
from tkinter import scrolledtext
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class UI_Object(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gas_Mixing_UI")
        self.geometry("1200x800")
        self.configure(bg=STYLES["bg"])
        self.state("zoomed")

        self.main_display_names = ["Overview", "Controls", "Logs", "Graph", "Settings"]
        self.main_display_titles = ["Overview", "Controls", "Logs", "Graph", "Settings"]

        self.window_nav_frame = tk.Frame(self, bg=STYLES["panel_bg"])
        self.window_nav_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, minsize=150)

        self.main_display_frame = tk.Frame(self, bg=STYLES["bg"])
        self.main_display_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.grid_columnconfigure(1, weight=3)

        self.terminal_frame = tk.Frame(self, bg=STYLES["panel_bg"])
        self.terminal_frame.grid(row=0, column=2, sticky="nsew", padx=(0,8), pady=8)
        self.grid_columnconfigure(2, minsize=250)

        self.bottom_frame = tk.Frame(self, bg=STYLES["panel_bg"], height=60)
        self.bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0,8))
        self.bottom_frame.grid_propagate(False)

        self.grid_rowconfigure(0, weight=1)

        self._build_terminal()
        self._build_window_nav()
        self._build_center_displays()
        self._build_bottom_buttons()

    def _build_window_nav(self):
        label = tk.Label(self.window_nav_frame, text="Displays",
                         fg=STYLES["text"], bg=STYLES["panel_bg"],
                         font=("Segoe UI", 10, "bold"))
        label.pack(pady=(8,6))

        self.center_buttons = []
        self.displays = {}

        for n in self.main_display_names:
            b = tk.Button(self.window_nav_frame, text=n,
                          command=lambda name=n: self.show_display(name),
                          bg=STYLES["button_bg"], fg=STYLES["text"],
                          activebackground=STYLES["button_active"],
                          relief="flat", padx=8, pady=8)
            b.pack(fill="x", padx=6, pady=6)
            self.center_buttons.append(b)

    def _build_center_displays(self):
        self.center_stack = tk.Frame(self.main_display_frame, bg=STYLES["bg"])
        self.center_stack.pack(fill="both", expand=True)

        for i, name in enumerate(self.main_display_names):
            self._make_main_display_frame(name, self.main_display_titles[i])

        self._build_overview_display()

        self.show_display(self.main_display_names[0])

    def _make_main_display_frame(self, name, label_text):
        f = tk.Frame(self.center_stack, bg=STYLES["bg"])
        l = tk.Label(f, text=label_text, fg=STYLES["text"],
                     bg=STYLES["bg"], font=("Segoe UI", 16, "bold"))
        l.pack(pady=16)
        f.place(in_=self.center_stack, x=0, y=0, relwidth=1, relheight=1)
        self.displays[name] = f

    def _build_overview_display(self):
        frame = self.displays["Overview"]

        # Indicators row
        indicator_frame = tk.Frame(frame, bg=STYLES["bg"])
        indicator_frame.pack(side="top", pady=10)

        self.indicators = []
        for i in range(3):
            lbl = tk.Label(indicator_frame, text=f"Indicator {i+1}",
                           fg=STYLES["text"], bg="green", font=("Segoe UI", 14, "bold"), width=20)
            lbl.pack(side="left", padx=10)
            self.indicators.append(lbl)

        # Matplotlib 3x3 grid
        fig, axes = plt.subplots(3, 3, figsize=(8, 8))
        t = np.arange(0, 10, 1)
        for i, ax in enumerate(axes.flatten()):
            var = np.random.rand(10)
            ax.plot(t, var, marker="o")
            ax.set_title(f"var{i+1} vs t{i+1}", fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_indicators(self, values, colors):
        for i, lbl in enumerate(self.indicators):
            lbl.config(text=values[i], bg=colors[i])

    def show_display(self, name):
        if name not in self.displays:
            self.write_to_terminal(f"[ERROR] No display: {name}")
            return
        self.displays[name].lift()
        self.write_to_terminal(f"[INFO] Display switched to {name}")
        for b in self.center_buttons:
            b.configure(bg=STYLES["accent"] if b["text"] == name else STYLES["button_bg"])

    def _build_terminal(self):
        lbl = tk.Label(self.terminal_frame, text="Terminal",
                       fg=STYLES["text"], bg=STYLES["panel_bg"],
                       font=("Segoe UI", 10, "bold"))
        lbl.pack(pady=(8,4))

        self.terminal = scrolledtext.ScrolledText(self.terminal_frame,
            bg=STYLES["terminal_bg"], fg=STYLES["text"],
            insertbackground=STYLES["text"], relief="flat", wrap="word", state="disabled")
        self.terminal.pack(fill="both", expand=True, padx=8, pady=(0,8))

    def write_to_terminal(self, text, timestamp=True):
        ts = f"[{time.strftime('%H:%M:%S')}] " if timestamp else ""
        self.terminal.configure(state="normal")
        self.terminal.insert("end", ts + text + "\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def _build_bottom_buttons(self):
        for n in ["Func A", "Func B", "Func C", "Func D", "Func E"]:
            b = tk.Button(self.bottom_frame, text=n,
                          command=lambda name=n: self.on_bottom_press(name),
                          bg=STYLES["button_bg"], fg=STYLES["text"],
                          activebackground=STYLES["button_active"],
                          relief="flat", padx=12, pady=8)
            b.pack(side="left", padx=8, pady=8)

    def on_bottom_press(self, name):
        self.write_to_terminal(f"[ACTION] {name} pressed")


STYLES = {
    "bg": "#0f1115",
    "panel_bg": "#111316",
    "accent": "#1f6feb",
    "muted": "#9aa4b2",
    "text": "#e6eef6",
    "button_bg": "#16181c",
    "button_active": "#233c72",
    "entry_bg": "#0d1013",
    "terminal_bg": "#05070a",
}


if __name__ == "__main__":
    Gas_Mixing_UI = UI_Object()
    Gas_Mixing_UI.write_to_terminal("App started.")
    Gas_Mixing_UI.mainloop()
