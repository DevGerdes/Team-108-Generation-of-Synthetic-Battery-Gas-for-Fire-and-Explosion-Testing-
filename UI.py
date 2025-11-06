import tkinter as tk
from tkinter import scrolledtext
from tkinter import Tk, filedialog
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd

class UI_Object(tk.Tk):
    ## Define all UI variables and build the layout
    def __init__(self):
        super().__init__()
        self.title("Gas_Mixing_UI")
        self.geometry("1200x800")
        self.configure(bg=STYLES["bg"])
        self.state("zoomed")

        # Define names for main displays and buttons
        self.main_display_names = ["Overview and Control", "Live Values","TroubleShooting and Best Practices"]
        self.main_display_titles = self.main_display_names
        self.function_buttons = ["START TEST", "STOP TEST","TEST RECIPE LOAD", "REPORT VALUES", "EMERGENCY STOP"]
        self.indicators = ["State","Indicator 1","Indicator 2"]

        # Define graph names and variable names for overview display
        self.graph_names = ["Test Plan Preview", "MFC 1 Response", "MFC 2 Response", "MFC 3 Response"]
        self.graph_variable_names = [["Composition Percents", "Heat Release Rate (kW)"],"Flow Rate (SLPM)", "Flow Rate (SLPM)", "Flow Rate (SLPM)"]

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

        # Initialize connection to Control System
        self.cs = None
        self.dh = None

        # Close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Ensure clean shutdown when the window is closed."""
        try:
            if self.cs is not None:
                # Optionally stop threads, close connections, etc.
                self.cs.set_state(0)
        except Exception:
            pass
        self.destroy()
        self.quit()


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
        frame = self.displays[self.main_display_names[0]]

        # Indicators row
        indicator_frame = tk.Frame(frame, bg=STYLES["bg"])
        indicator_frame.pack(side="top", pady=10)

        # Create indicator labels and store by name
        self.indicator_widgets = {}
        for name in self.indicators:
            lbl = tk.Label(indicator_frame, text=name,
                        fg=STYLES["text"], bg="green",
                        font=("Segoe UI", 14, "bold"), width=20)
            lbl.pack(side="left", padx=10)
            self.indicator_widgets[name] = lbl

        # Determine layout
        num_graphs = len(self.graph_names)
        ncols = 2
        nrows = math.ceil(num_graphs / ncols)

        # Matplotlib grid
        fig, axes = plt.subplots(nrows, ncols, figsize=(8, 3 * nrows))
        axes = axes.flatten() if num_graphs > 1 else [axes]
        self.fig = fig
        self.graphs = {}

        for i, name in enumerate(self.graph_names):
            ax = axes[i]

            # Create empty line
            (line,) = ax.plot([], [], marker="o")
            ax.set_title(name, fontsize=8)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(self.graph_variable_names[i])

            # If this is the Test Plan Overview graph, set up for multiple series + legend
            if name == self.graph_names[0]:
                ax.legend([], loc="upper right", fontsize=6, frameon=False)
                self.graphs[name] = {"ax": ax, "line": None, "lines": []}
            else:
                self.graphs[name] = {"ax": ax, "line": line}

        # Hide unused subplots if total < nrows*ncols
        for j in range(len(self.graph_names), len(axes)):
            axes[j].axis("off")

        # Adjust subplot spacing for better visual separation
        fig.subplots_adjust(
            left=0.07,   # widen left margin
            right=0.95,  # widen right margin
            top=0.92,    # add space above titles
            bottom=0.08, # add space below x-axis labels
            wspace=0.35, # horizontal spacing between plots
            hspace=0.45  # vertical spacing between plots
            )


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
                b = tk.Button(self.bottom_frame, text=n,
                            command=lambda name=n: self.on_bottom_press(name),
                            bg=STYLES["button_bg"], fg=STYLES["text"],
                            activebackground=STYLES["button_active"],
                            relief="flat", padx=12, pady=8)
                b.pack(side="left", padx=8, pady=8)

    #######################
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
            try:
                self.cs.set_state(2) # Set state to RUN TEST
                self.write_to_terminal("[INFO] Test started.")
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Could not start test: {e}")
        if name == self.function_buttons[1]: # Stop button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            try:
                self.cs.set_state(1) # Set state to IDLE
                self.write_to_terminal("[INFO] Test stopped.")
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Could not stop test: {e}")
        if name == self.function_buttons[2]: # TEST RECIPE LOAD button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.load_and_interpolate_excel()
        if name == self.function_buttons[3]: # REPORT VARIABLES button"
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.print_variables()
        if name == self.function_buttons[4]: # EMERGENCY STOP button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.cs.set_state(0) # Set state to EMERGENCY STOP
            self.update_indicators()
    
    def show_display(self, name):
        # Handle navigation button presses to switch center display
        if name not in self.displays:
            self.write_to_terminal(f"[ERROR] No display: {name}")
            return
        self.displays[name].lift()
        self.write_to_terminal(f"[INFO] Display switched to {name}")
        for b in self.center_buttons:
            b.configure(bg=STYLES["accent"] if b["text"] == name else STYLES["button_bg"])

    def update_indicators(self, name):
        """Update one indicator by name"""
        if name == self.indicators[0]: # Update State indicator
            if self.cs.STATE == 0:
                color = "red"
                text = "EMERGENCY STOP"
            elif self.cs.STATE == 1:
                color = "blue"
                text = "IDLE"
            elif self.cs.STATE == 2:
                color = "green"
                text = "RUNNING"
            self.indicator_widgets[name].config(text=text)
            self.indicator_widgets[name].config(bg=color)
        elif name == self.indicators[1]: # Update Indicator 1
            pass
        elif name == self.indicators[2]: # Update Indicator 2
            pass
        else:
            self.write_to_terminal(f"[ERROR] Indicator '{name}' not found.")

    def update_graph(self, graph_name, x_data=None, y_data=None):
        """Update a specific graph by name with new data."""
        global test_columns, test_plan

        if graph_name not in self.graphs:
            self.write_to_terminal(f"[ERROR] Graph '{graph_name}' not found.")
            return

        graph = self.graphs[graph_name]
        ax = graph["ax"]

        # Handle special case for Test Plan Overview
        if graph_name == self.graph_names[0]:
            ax.clear()
            if not test_columns or not test_plan or len(test_plan) < 2:
                ax.text(0.5, 0.5, "No Test Plan Loaded", color="gray",
                        ha="center", va="center", transform=ax.transAxes)
            else:
                time_data = test_plan[0]
                n_cols = len(test_columns)

                # Primary axis (left)
                for i, col_name in enumerate(test_columns[1:], start=1):
                    # Skip 6th column for now (will go on right axis)
                    if i == 6:
                        continue
                    y_data = test_plan[i]
                    ax.plot(time_data, y_data, label=col_name)
                ax.set_ylim([0,1])
                ax.set_title(self.graph_names[0])
                ax.set_xlabel(test_columns[0])
                ax.set_ylabel(self.graph_variable_names[0][0])

                # Secondary axis (right)
                if n_cols > 6:
                    ax2 = ax.twinx()
                    y_data_secondary = test_plan[6]
                    ax2.plot(time_data, y_data_secondary, color="orange", label=test_columns[6])
                    ax2.set_ylabel(self.graph_variable_names[0][1])
                    # Combine legends
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2,
                            loc="upper right", fontsize=6, frameon=False)
                else:
                    ax.legend(loc="upper right", fontsize=6, frameon=False)

            self.canvas.draw_idle()
            return

        # Normal case: update existing single-line graph
        if "line" not in graph or graph["line"] is None:
            self.write_to_terminal(f"[ERROR] Graph '{graph_name}' has no line object.")
            return

        line = graph["line"]
        line.set_data(x_data, y_data)
        ax.relim()
        ax.autoscale_view()
        self.canvas.draw_idle()

    def load_and_interpolate_excel(self,resolution=0.1):
        global valid_titles, test_columns, test_plan
        
        # Hide the tkinter root window
        root = Tk()
        root.withdraw()

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Excel File",filetypes=[("Excel files", "*.xlsx *.xls")])

        if not file_path:
            self.write_to_terminal("No file selected.")
            return None, None

        # Load the Excel file
        df = pd.read_excel(file_path)

        ## Check test file validity
        # ---- 1. Check column titles ----
        if not all(title in valid_titles for title in df.columns):
            self.write_to_terminal("Error: One or more column titles are invalid. "
                f"Expected only these: {valid_titles}")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 2. Check for empty cells ----
        if df.isnull().values.any():
            self.write_to_terminal("Error: The file contains empty cells. "
                "Please fill or remove missing data before loading.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 3. Ensure numeric data in main columns (excluding first column) ----
        for col in df.columns[1:]:
            if not pd.to_numeric(df[col], errors='coerce').notna().all():
                self.write_to_terminal(f"Error: Non-numeric values found in data column '{col}'.")
                return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 4. Check that time values are numeric ----
        time = pd.to_numeric(df.iloc[:, 0], errors='coerce')
        if not time.notna().all():
            self.write_to_terminal("Error: Time column contains non-numeric or missing values.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 5. Check that time values are strictly increasing ----
        if not all(np.diff(time) > 0):
            self.write_to_terminal("Error: Time values are not strictly increasing.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 6. Check that time values do not exceed 3600 seconds ----
        if time.max() > 3600:
            self.write_to_terminal(f"Error: Time values exceed 3600 seconds (found max={time.max():.2f}).")
            return df.columns.tolist(), [[0] * len(df.columns)]


        # Extract column titles
        column_titles = df.columns.tolist()
        # Ensure first column is numeric time data
        time = pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna().to_numpy()
        start_t, end_t = time[0], time[-1]
        # Generate new time vector with desired resolution
        new_time = np.arange(start_t, end_t + resolution, resolution)

        # Interpolate remaining columns
        interpolated_data = [new_time.tolist()]  # first column is time
        for col in df.columns[1:]:
            y = pd.to_numeric(df[col], errors='coerce').to_numpy()
            valid = ~np.isnan(y)
            interp_y = np.interp(new_time, time[valid], y[valid])
            interpolated_data.append(interp_y.tolist())

        # Replace original first column title with the same
        self.write_to_terminal(f"Interpolated data from {start_t:.2f}s to {end_t:.2f}s at {resolution:.1f}s resolution.")
        self.write_to_terminal(f"Columns: {', '.join(column_titles)}")
        test_columns = column_titles
        test_plan = interpolated_data

        self.update_graph(self.graph_names[0], new_time, interpolated_data[1])  # Example: update first data column

    def print_variables(self):
        self.write_to_terminal(f"Test Columns: {test_columns}")
        self.write_to_terminal(f"Test Plan (first 5 rows):")
        for row in test_plan:
            self.write_to_terminal(f"{row}")



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
valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4"]
test_columns = []
test_plan = []

if __name__ == "__main__":
    Gas_Mixing_UI = UI_Object()
    Gas_Mixing_UI.write_to_terminal("App started.")
    Gas_Mixing_UI.mainloop()
