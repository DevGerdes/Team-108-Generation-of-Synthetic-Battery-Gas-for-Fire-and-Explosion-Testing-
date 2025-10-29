import tkinter as tk
from tkinter import scrolledtext
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math

class UI_Object(tk.Tk):
    ## Define all UI variables and build the layout
    def __init__(self):
        super().__init__()
        self.title("Gas_Mixing_UI")
        self.geometry("1200x800")
        self.configure(bg=STYLES["bg"])
        self.state("zoomed")

        # Define names for main displays and buttons
        self.main_display_names = ["Overview", "Controls", "Logs", "Graph", "Settings"]
        self.main_display_titles = ["Overview", "Controls", "Logs", "Graph", "Settings"]
        self.function_buttons = ["START", "STOP", "TEST RECIPE LOAD", "Func D", "EMERGENCY STOP"]

        # Define graph names and variable names for overview display
        self.graph_names = ["MFC 1 Response", "MFC 2 Response", "MFC 3 Response"]
        self.graph_variable_names = ["Flow Rate (SLPM)", "Flow Rate (SLPM)", "Flow Rate (SLPM)"]

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

    ######################
    ## Begin Build functions to make UI objects and screens, link to functions. Each called once. 
    def _build_window_nav(self):
        # Populate left frame with navigation buttons
        # Create frame label
        label = tk.Label(self.window_nav_frame, text="Displays",
                         fg=STYLES["text"], bg=STYLES["panel_bg"],
                         font=("Segoe UI", 10, "bold"))
        label.pack(pady=(8,6))

        self.center_buttons = []
        self.displays = {}

        # make the buttons
        for n in self.main_display_names:
            b = tk.Button(self.window_nav_frame, text=n,
                          command=lambda name=n: self.show_display(name),
                          bg=STYLES["button_bg"], fg=STYLES["text"],
                          activebackground=STYLES["button_active"],
                          relief="flat", padx=8, pady=8)
            b.pack(fill="x", padx=6, pady=6)
            self.center_buttons.append(b)

    def _build_center_displays(self):
        # Populate each center display with objects

        # Create a stack frame to hold all center displays
        self.center_stack = tk.Frame(self.main_display_frame, bg=STYLES["bg"])
        self.center_stack.pack(fill="both", expand=True)

        # Create each display frame and add to stack
        for i, name in enumerate(self.main_display_names):
            f = tk.Frame(self.center_stack, bg=STYLES["bg"])
            l = tk.Label(f, text=self.main_display_titles[i], fg=STYLES["text"],
                        bg=STYLES["bg"], font=("Segoe UI", 16, "bold"))
            l.pack(pady=16)
            f.place(in_=self.center_stack, x=0, y=0, relwidth=1, relheight=1)
            self.displays[name] = f

        # Build specific displays
        self._build_overview_display()

        # Show default display on start
        self.show_display(self.main_display_names[0])


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

        # Determine layout
        num_graphs = len(self.graph_names)
        ncols = 3
        nrows = math.ceil(num_graphs / ncols)

        # Matplotlib grid
        fig, axes = plt.subplots(nrows, ncols, figsize=(8, 3 * nrows))
        axes = axes.flatten() if num_graphs > 1 else [axes]

        self.fig = fig
        self.graphs = {}

        for i, name in enumerate(self.graph_names):
            ax = axes[i]
            (line,) = ax.plot([], [], marker="o")  # start blank
            ax.set_title(name, fontsize=8)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(self.graph_variable_names[i])
            self.graphs[name] = {"ax": ax, "line": line}

        # Hide unused subplots if total < nrows*ncols
        for j in range(len(self.graph_names), len(axes)):
            axes[j].axis("off")

        fig.tight_layout()

        # Embed figure in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

    
    def _build_terminal(self):
        lbl = tk.Label(self.terminal_frame, text="Terminal",
                       fg=STYLES["text"], bg=STYLES["panel_bg"],
                       font=("Segoe UI", 10, "bold"))
        lbl.pack(pady=(8,4))

        self.terminal = scrolledtext.ScrolledText(self.terminal_frame,
            bg=STYLES["terminal_bg"], fg=STYLES["text"],
            insertbackground=STYLES["text"], relief="flat", wrap="word", state="disabled")
        self.terminal.pack(fill="both", expand=True, padx=8, pady=(0,8))
    

    def _build_bottom_buttons(self):
            # Create bottom buttons
            for n in self.function_buttons:
                print(n)
                b = tk.Button(self.bottom_frame, text=n,
                            command=lambda name=n: self.on_bottom_press(name),
                            bg=STYLES["button_bg"], fg=STYLES["text"],
                            activebackground=STYLES["button_active"],
                            relief="flat", padx=12, pady=8)
                b.pack(side="left", padx=8, pady=8)

    ##################
    ## Begin function handling for UI actions
    def write_to_terminal(self, text, timestamp=True):
        ts = f"[{time.strftime('%H:%M:%S')}] " if timestamp else ""
        self.terminal.configure(state="normal")
        self.terminal.insert("end", ts + text + "\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def on_bottom_press(self, name):
        # Handle bottom button presses and call or perform appropriate actions
        if name == self.function_buttons[0]: # Start button
            self.write_to_terminal(f"[ACTION] {name} pressed")
        if name == self.function_buttons[1]: # Stop button
            self.write_to_terminal(f"[ACTION] {name} pressed")
        if name == self.function_buttons[2]: # Func C button
            self.write_to_terminal(f"[ACTION] {name} pressed")
        if name == self.function_buttons[3]: # Func D button"
            self.write_to_terminal(f"[ACTION] {name} pressed")
        if name == self.function_buttons[4]: # Func E button
            self.write_to_terminal(f"[ACTION] {name} pressed")
    
    def show_display(self, name):
        # Handle navigation button presses to switch center display
        if name not in self.displays:
            self.write_to_terminal(f"[ERROR] No display: {name}")
            return
        self.displays[name].lift()
        self.write_to_terminal(f"[INFO] Display switched to {name}")
        for b in self.center_buttons:
            b.configure(bg=STYLES["accent"] if b["text"] == name else STYLES["button_bg"])

    def update_indicators(self, values, colors):
        for i, lbl in enumerate(self.indicators):
            lbl.config(text=values[i], bg=colors[i])


###############
## UI test code
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
