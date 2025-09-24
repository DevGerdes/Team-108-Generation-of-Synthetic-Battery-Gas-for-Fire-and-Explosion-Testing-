import tkinter as tk
from tkinter import scrolledtext
import time

class UI_Object(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gas_Mixing_UI")
        self.geometry("1000x640")
        self.configure(bg=STYLES["bg"])

        #default to fullscreen
        self.state("zoomed")

        # ~~~~~~
        # Define display characteristics
        self.main_display_names = ["Overview", "Controls", "Logs", "Graph", "Settings"]
        self.main_display_titles = ["Overview", "Controls", "Logs", "Graph", "Settings"]
        self.bottom_button_names = ["Func A", "Func B", "Func C", "Func D", "Func E"]

        # ~~~~~~
        #  Define and build UI architecture
        # Left window nav frame
        self.window_nav_frame = tk.Frame(self, bg=STYLES["panel_bg"])
        self.window_nav_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, minsize=150)
        # Center main display
        self.main_display_frame = tk.Frame(self, bg=STYLES["bg"])
        self.main_display_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.grid_columnconfigure(1, minsize=900, weight=3)  
        # Right terminal frame
        self.terminal_frame = tk.Frame(self, bg=STYLES["panel_bg"])
        self.terminal_frame.grid(row=0, column=2, sticky="nsew", padx=(0,8), pady=8)
        self.grid_columnconfigure(2, minsize=0)  
        # Bottom
        self.bottom_frame = tk.Frame(self, bg=STYLES["panel_bg"], height=60)
        self.bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0,8))
        self.bottom_frame.grid_propagate(False)
        # Weighting: how frames stretch woth window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  
        self.grid_columnconfigure(1, weight=1)  
        self.grid_columnconfigure(2, weight=0)  
        self._build_terminal()          # build terminal first
        self._build_window_nav()
        self._build_center_displays()
        self._build_bottom_buttons()
        # ~~~~~~

    # left side buttons for center window nav
    def _build_window_nav(self):
        label = tk.Label(self.window_nav_frame, text="Displays",
                         fg=STYLES["text"], bg=STYLES["panel_bg"],
                         font=("Segoe UI", 10, "bold"))
        label.pack(pady=(8,6))

        self.center_buttons = []
        self.displays = {}   # name -> frame

        for n in self.main_display_names:
            b = tk.Button(self.window_nav_frame, text=n,
                          command=lambda name=n: self.show_display(name),
                          bg=STYLES["button_bg"], fg=STYLES["text"],
                          activebackground=STYLES["button_active"],
                          relief="flat", padx=8, pady=8)
            b.pack(fill="x", padx=6, pady=6)
            self.center_buttons.append(b)

    # Main display function
    def _build_center_displays(self):
        self.center_stack = tk.Frame(self.main_display_frame, bg=STYLES["bg"])
        self.center_stack.pack(fill="both", expand=True)

        # Hardcode 5 frames (easily add more by copy-pasting)
        self._make_main_display_frame(self.main_display_names[0], self.main_display_titles[0])
        self._make_main_display_frame(self.main_display_names[1], self.main_display_titles[1])
        self._make_main_display_frame(self.main_display_names[2], self.main_display_titles[2])
        self._make_main_display_frame(self.main_display_names[3], self.main_display_titles[3])
        self._make_main_display_frame(self.main_display_names[4], self.main_display_titles[4])

        self.show_display(self.main_display_names[0])

    def _make_main_display_frame(self, name, label_text):
        f = tk.Frame(self.center_stack, bg=STYLES["bg"])
        l = tk.Label(f, text=label_text, fg=STYLES["text"],
                     bg=STYLES["bg"], font=("Segoe UI", 16, "bold"))
        l.pack(pady=16)
        f.place(in_=self.center_stack, x=0, y=0, relwidth=1, relheight=1)
        self.displays[name] = f

    def show_display(self, name):
        if name not in self.displays:
            self.write_to_terminal(f"[ERROR] No display: {name}")
            return
        self.displays[name].lift()
        self.write_to_terminal(f"[INFO] Display switched to {name}")
        for b in self.center_buttons:
            b.configure(bg=STYLES["accent"] if b["text"] == name else STYLES["button_bg"])

    # ------------------------
    # Right side (terminal)
    # ------------------------
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

    # build the bottom buttons
    def _build_bottom_buttons(self):
        for n in self.bottom_button_names:
            b = tk.Button(self.bottom_frame, text=n,
                          command=lambda name=n: self.on_bottom_press(name),
                          bg=STYLES["button_bg"], fg=STYLES["text"],
                          activebackground=STYLES["button_active"],
                          relief="flat", padx=12, pady=8)
            b.pack(side="left", padx=8, pady=8)

    # Individual bottom button press handlers
    def on_func_a_press(self):
        self.write_to_terminal(f"[ACTION] Func A pressed")

    def on_func_b_press(self):
        self.write_to_terminal(f"[ACTION] Func B pressed")

    def on_func_c_press(self):
        self.write_to_terminal(f"[ACTION] Func C pressed")

    def on_func_d_press(self):
        self.write_to_terminal(f"[ACTION] Func D pressed")

    def on_func_e_press(self):
        self.write_to_terminal(f"[ACTION] Func E pressed")

    # Handle bottom button presses using button name mapped to function
    def on_bottom_press(self, name):
        # Map button names to their handler functions
        button_handlers = {
            "Func A": self.on_func_a_press,
            "Func B": self.on_func_b_press,
            "Func C": self.on_func_c_press,
            "Func D": self.on_func_d_press,
            "Func E": self.on_func_e_press
        }
        
        # Call the appropriate handler function
        if name in button_handlers:
            button_handlers[name]()
        else:
            self.write_to_terminal(f"[ERROR] No handler for button: {name}")


# ---- Dark mode style dictionary ----
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

