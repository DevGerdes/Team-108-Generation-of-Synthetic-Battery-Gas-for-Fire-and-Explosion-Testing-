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

        # dark mode style coloring
        self.styles = {
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
        self.title("Gas_Mixing_UI")
        self.geometry("1200x800")
        self.configure(bg=self.styles["bg"])
        self.state("zoomed")

     
        # Define names for main displays and buttons
        self.main_display_names = ["Overview and Control", "Live Values","TroubleShooting and Best Practices"]
        self.main_display_titles = self.main_display_names
        self.function_buttons = ["START TEST", "STOP TEST","TEST RECIPE LOAD", "REPORT VALUES", "EMERGENCY STOP"]
        self.indicators = ["State","Indicator 1","Indicator 2"]

        # Define graph names and variable names for overview display
        self.mfc_graphs = ["Test Plan Preview", "MFC 1 Response", "MFC 2 Response"]
        self.sensor_graphs = ["Pressure Sensor 1"]
        self.graph_names = self.mfc_graphs+self.sensor_graphs
        self.graph_variable_names = [["Composition Percents", "Heat Release Rate (kW)"],"Flow Rate (SLPM)", "Flow Rate (SLPM)", "Pressure (psi)"]

        # Variables for loading in test data
        self.valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4"]
        self.test_columns = []
        self.test_plan = []

        # Start building the display
        self.window_nav_frame = tk.Frame(self, bg=self.styles["panel_bg"])
        self.window_nav_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, minsize=150)

        self.main_display_frame = tk.Frame(self, bg=self.styles["bg"])
        self.main_display_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.grid_columnconfigure(1, weight=3)

        self.terminal_frame = tk.Frame(self, bg=self.styles["panel_bg"])
        self.terminal_frame.grid(row=0, column=2, sticky="nsew", padx=(0,8), pady=8)
        self.grid_columnconfigure(2, minsize=250)

        self.bottom_frame = tk.Frame(self, bg=self.styles["panel_bg"], height=60)
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
                         fg=self.styles["text"], bg=self.styles["panel_bg"],
                         font=("Segoe UI", 10, "bold"))
        label.pack(pady=(8,6))

        self.center_buttons = []
        self.displays = {}

        # make the buttons
        for n in self.main_display_names:
            b = tk.Button(self.window_nav_frame, text=n,
                          command=lambda name=n: self.show_display(name),
                          bg=self.styles["button_bg"], fg=self.styles["text"],
                          activebackground=self.styles["button_active"],
                          relief="flat", padx=8, pady=8)
            b.pack(fill="x", padx=6, pady=6)
            self.center_buttons.append(b)

    def _build_center_displays(self):
        # Populate each center display with objects

        # Create a stack frame to hold all center displays
        self.center_stack = tk.Frame(self.main_display_frame, bg=self.styles["bg"])
        self.center_stack.pack(fill="both", expand=True)

        # Create each display frame and add to stack
        for i, name in enumerate(self.main_display_names):
            f = tk.Frame(self.center_stack, bg=self.styles["bg"])
            l = tk.Label(f, text=self.main_display_titles[i], fg=self.styles["text"],
                        bg=self.styles["bg"], font=("Segoe UI", 16, "bold"))
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
        indicator_frame = tk.Frame(frame, bg=self.styles["bg"])
        indicator_frame.pack(side="top", pady=10)

        self.indicator_widgets = {}
        for name in self.indicators:
            lbl = tk.Label(indicator_frame, text=name,
                        fg=self.styles["text"], bg="green",
                        font=("Segoe UI", 14, "bold"), width=20)
            lbl.pack(side="left", padx=10)
            self.indicator_widgets[name] = lbl

        num_graphs = len(self.graph_names)
        ncols = 2
        nrows = math.ceil(num_graphs / ncols)

        fig, axes = plt.subplots(nrows, ncols, figsize=(8, 3 * nrows))
        axes = axes.flatten() if num_graphs > 1 else [axes]
        self.fig = fig
        self.graphs = {}

        for i, name in enumerate(self.graph_names):
            ax = axes[i]
            ax.set_title(name, fontsize=8)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(self.graph_variable_names[i])

            # Test Plan Preview
            if name == self.graph_names[0]:
                ax.legend([], loc="upper right", fontsize=6, frameon=False)
                self.graphs[name] = {"ax": ax, "line": None, "lines": []}
                continue

            # MFC graphs: two lines (setpoint, actual)
            if name in self.mfc_graphs:
                line1, = ax.plot([], [], label="Setpoint", linestyle="-")
                line2, = ax.plot([], [], label="Actual", linestyle="--")
                ax.legend(fontsize=6, frameon=False, loc="upper right")
                self.graphs[name] = {"ax": ax, "lines": [line1, line2]}
                continue

            # Sensor graphs: single line 
            if name in self.sensor_graphs:
                (line,) = ax.plot([], [], label="Sensor")
                ax.legend(fontsize=6, frameon=False, loc="upper right")
                self.graphs[name] = {"ax": ax, "lines": [line]}
                continue

        # Hide unused subplots
        for j in range(len(self.graph_names), len(axes)):
            axes[j].axis("off")

        fig.subplots_adjust(left=0.07, right=0.95, top=0.92, bottom=0.08,
                            wspace=0.35, hspace=0.45)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas


    def _build_terminal(self):
        lbl = tk.Label(self.terminal_frame, text="Terminal",
                       fg=self.styles["text"], bg=self.styles["panel_bg"],
                       font=("Segoe UI", 10, "bold"))
        lbl.pack(pady=(8,4))

        self.terminal = scrolledtext.ScrolledText(self.terminal_frame,
            bg=self.styles["terminal_bg"], fg=self.styles["text"],
            insertbackground=self.styles["text"], relief="flat", wrap="word", state="disabled")
        self.terminal.pack(fill="both", expand=True, padx=8, pady=(0,8))
    
    def _build_bottom_buttons(self):
            # Create bottom buttons
            for n in self.function_buttons:
                b = tk.Button(self.bottom_frame, text=n,
                            command=lambda name=n: self.on_bottom_press(name),
                            bg=self.styles["button_bg"], fg=self.styles["text"],
                            activebackground=self.styles["button_active"],
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
            b.configure(bg=self.styles["accent"] if b["text"] == name else self.styles["button_bg"])

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

    def update_graphs(self):
        """Update all graphs using stored data (no inputs)."""
        now = time.time()
        window = 600  # 10 minutes [seconds]

        # [t, ...] entries by last 10 min
        def recent(data):
            return [d for d in data if len(d) > 0 and (now - d[0]) <= window]

        #Collect and filter histories
        setpoints = recent(getattr(self.dh, "setpoint_history", []))
        responses = recent(getattr(self.dh, "mfc_response_history", []))
        sensors  = recent(getattr(self, "sensor_history", []))

        # Test Plan Preview
        if self.mfc_graphs[0] in self.graphs:
            ax = self.graphs[self.mfc_graphs[0]]["ax"]
            ax.clear()
            if not self.test_columns or not self.test_plan or len(self.test_plan) < 2:
                ax.text(0.5, 0.5, "No Test Plan Loaded", color="gray",
                        ha="center", va="center", transform=ax.transAxes)
            else:
                time_data = self.test_plan[0]
                n_cols = len(self.test_columns)
                for i, col_name in enumerate(self.test_columns[1:], start=1):
                    if i == 6:
                        continue
                    y_data = self.test_plan[i]
                    ax.plot(time_data, y_data, label=col_name)
                ax.set_ylim([0, 1])
                ax.set_title(self.graph_names[0])
                ax.set_xlabel(self.test_columns[0])
                ax.set_ylabel(self.graph_variable_names[0][0])

                if n_cols > 6:
                    ax2 = ax.twinx()
                    y_data_secondary = self.test_plan[6]
                    ax2.plot(time_data, y_data_secondary, color="orange", label=self.test_columns[6])
                    ax2.set_ylabel(self.graph_variable_names[0][1])
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax2.legend(lines1 + lines2, labels1 + labels2,
                            loc="upper right", fontsize=6, frameon=False)
                else:
                    ax.legend(loc="upper right", fontsize=6, frameon=False)

        # MFC Graphs (each has two lines)
        for i, name in enumerate(self.mfc_graphs[1:], start=0):  # skip test plan
            if name not in self.graphs:
                continue
            graph = self.graphs[name]
            ax = graph["ax"]
            lines = graph["lines"]

            # Verify data presence
            if not setpoints or not responses:
                ax.clear()
                ax.set_title(name)
                ax.text(0.5, 0.5, "No MFC Data", color="gray",
                        ha="center", va="center", transform=ax.transAxes)
                continue

            try:
                # Extract data for this MFC index
                times_sp = [t for t, _ in setpoints]
                sp_vals  = [vals[i] for _, vals in setpoints]
                times_rp = [t for t, _ in responses]
                rp_vals  = [vals[i] for _, vals in responses]

                lines[0].set_data(times_sp, sp_vals)
                lines[1].set_data(times_rp, rp_vals)
                ax.relim()
                ax.autoscale_view()
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Updating {name}: {e}")

        # Sensor Graphs (single line)
        if sensors:
            times = [t for t, *_ in sensors]
            for j, name in enumerate(self.sensor_graphs, start=1):
                if name not in self.graphs:
                    continue
                graph = self.graphs[name]
                ax = graph["ax"]
                lines = graph["lines"]

                if len(sensors[0]) <= j:  # sensor not present in data
                    ax.clear()
                    ax.set_title(name)
                    ax.text(0.5, 0.5, "No Data", color="gray",
                            ha="center", va="center", transform=ax.transAxes)
                    continue

                try:
                    vals = [row[j] for row in sensors]
                    lines[0].set_data(times, vals)
                    ax.relim()
                    ax.autoscale_view()
                except Exception as e:
                    self.write_to_terminal(f"[ERROR] Updating {name}: {e}")
        else:
            # Clear all if no sensor data
            for name in self.sensor_graphs:
                if name in self.graphs:
                    ax = self.graphs[name]["ax"]
                    ax.clear()
                    ax.set_title(name)
                    ax.text(0.5, 0.5, "No Sensor Data", color="gray",
                            ha="center", va="center", transform=ax.transAxes)

        # Redraw all graphs
        self.canvas.draw_idle()

    def load_and_interpolate_excel(self,resolution=0.1):        
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
        if not all(title in self.valid_titles for title in df.columns):
            self.write_to_terminal("Error: One or more column titles are invalid. "
                f"Expected only these: {self.valid_titles}")
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
        self.test_columns = column_titles
        self.test_plan = interpolated_data

        self.update_graph(self.graph_names[0], new_time, interpolated_data[1])  # Example: update first data column

    def print_variables(self):
        self.write_to_terminal(f"Test Columns: {self.test_columns}")
        self.write_to_terminal(f"Test Plan (first 5 rows):")
        for row in self.test_plan:
            self.write_to_terminal(f"{row}")

