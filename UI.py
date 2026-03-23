import tkinter as tk
from tkinter import scrolledtext
from tkinter import Tk, filedialog, simpledialog
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd
import os
import csv

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
        self.function_buttons = ["START TEST", "STOP TEST","TEST RECIPE LOAD", "REPORT VALUES", "EMERGENCY STOP", "Connect","Send Setpoints","Save Data","Clear Data","Ambient Calibration"]
        self.indicators = ["State","Valve","Arduino"]

        # Define graph names and variable names for overview display
        self.mfc_graphs = ["Test Plan Preview", "MFC 1 Response", "MFC 2 Response","MFC 3 Response","MFC 4 Response","MFC 5 Response",]
        self.sensor_graphs = ["Pressure Sensors","Gas Sensors"]
        self.graph_names = self.mfc_graphs+self.sensor_graphs
        self.graph_variable_names = [["Flow Rate (SLPM)", "Heat Release Rate (kW)"],"Flow Rate (SLPM)", "Flow Rate (SLPM)","Flow Rate (SLPM)","Flow Rate (SLPM)","Flow Rate (SLPM)", "Pressure (psi)","Gas Sensor Response (PPM)",]

        # Variables to report for the Live values screen
        # Each element cooresponds to a column of values
        self.report_variables = [["MFC 1 Setpoint: ", "MFC 2 Setpoint: ", "MFC 3 Setpoint: ", "MFC 4 Setpoint: ", "MFC 5 Setpoint: "],
            ["MFC 1 Response: ","MFC 2 Response: ","MFC 3 Response: ","MFC 4 Response: ","MFC 5 Response: "],                  
            ["Pressure Sensor 1: ","Pressure Sensor 2: "],
            ["Gas Sensor 1: ","Gas Sensor 2: ","Line Temperature: "]]

        # Variables for loading in test data
        self.valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4","NA"]
        self.test_columns = [] # [Title1,Title2,Title3,...]
        self.test_plan = [] # [[Time1, Val1.1, Val2.1, ...], [Time2, Val1.2, Val2.2,...], ...]

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
                self.cs.emergency_stop() 
                time.sleep(0.5) # Give some time for threads to stop and resources to release
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
        self._build_values_display()
        self._build_troubleshooting()

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
                ax.set_ylabel(self.graph_variable_names[i][0])
                continue

            # MFC graphs: two lines (setpoint, actual)
            if name in self.mfc_graphs:
                line1, = ax.plot([], [], label="Setpoint", linestyle="-")
                line2, = ax.plot([], [], label="Actual", linestyle="--")
                ax.legend(fontsize=6, frameon=False, loc="upper right")
                self.graphs[name] = {"ax": ax, "lines": [line1, line2]}
                continue

            # Pressure sensor graphs
            if name == self.sensor_graphs[0]:
                line1, = ax.plot([], [], label="150 psi sensor", linestyle="-")
                line2, = ax.plot([], [], label="50 psi sensor", linestyle="-")
                ax.legend(fontsize=6, frameon=False, loc="upper right")
                self.graphs[name] = {"ax": ax, "lines": [line1, line2]}
                continue

            # Gas sensor graphs
            if name == self.sensor_graphs[1]:
                line1, = ax.plot([], [], label="Gas Sensor 1", linestyle="-")
                line2, = ax.plot([], [], label="Gas Sensor 2", linestyle="-")
                ax.legend(fontsize=6, frameon=False, loc="upper right")
                self.graphs[name] = {"ax": ax, "lines": [line1, line2]}
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

    def _build_values_display(self):
        """Build a matrix of blank labels for report variables.
        Each inner list in self.report_variables defines one column of variable names.
        """

        frame = self.displays.get("Live Values")
        if frame is None:
            self.write_to_terminal("[ERROR] 'Live Values' display not found.")
            return

        container = tk.Frame(frame, bg=self.styles["bg"])
        container.pack(fill="both", expand=True, pady=10)

        self.value_labels = {}

        # Determine max number of rows (longest column)
        max_rows = max(len(col) for col in self.report_variables)

        for c, col_vars in enumerate(self.report_variables):
            for r, var in enumerate(col_vars):
                lbl_name = tk.Label(container, text=var,
                                    fg=self.styles["text"], bg=self.styles["bg"],
                                    font=("Segoe UI", 11, "bold"), anchor="e", width=18)
                lbl_name.grid(row=r, column=c*2, padx=(1,1), pady=4, sticky="e")

                lbl_val = tk.Label(container, text="—",
                                   fg=self.styles["muted"], bg=self.styles["bg"],
                                   font=("Segoe UI", 11), anchor="w", width=10)
                lbl_val.grid(row=r, column=c*2 + 1, padx=(1,1), pady=4, sticky="w")

                self.value_labels[var] = lbl_val

        # Row expansion based on the longest column
        for i in range(max_rows):
            container.grid_rowconfigure(i, weight=1)

    def _build_troubleshooting(self):
        """Build the Troubleshooting and Best Practices display from Troubleshooting_Info.txt."""

        frame = self.displays.get("TroubleShooting and Best Practices")
        if frame is None:
            self.write_to_terminal("[ERROR] 'TroubleShooting and Best Practices' display not found.")
            return
        container = tk.Frame(frame, bg=self.styles["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        # Try loading the troubleshooting info from file
        try:
            with open("Troubleshooting_Info.txt", "r", encoding="utf-8") as f:
                self.troubleshooting_text = f.read()
        except FileNotFoundError:
            self.troubleshooting_text = "[INFO] Troubleshooting_Info.txt not found.\n\n" \
                                        "Create this file in the program directory to display information here."
        except Exception as e:
            self.troubleshooting_text = f"[ERROR] Unable to load troubleshooting info: {e}"

        # Create the readonly text box
        text_box = tk.Text(container, wrap="word",
                           bg=self.styles["panel_bg"], fg=self.styles["text"],
                           insertbackground=self.styles["text"], relief="flat",
                           font=("Segoe UI", 11), height=25)
        text_box.insert("1.0", self.troubleshooting_text)
        text_box.config(state="disabled")
        text_box.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, command=text_box.yview)
        text_box.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.troubleshooting_box = text_box

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
                if self.test_plan == []:
                    self.write_to_terminal("[ERROR] No test plan loaded. Cannot start test.")
                    return
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
        if name == self.function_buttons[5]: # Connect button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.dh.connect_to_arduino()
        if name == self.function_buttons[6]:  # Send Setpoints button
            self.write_to_terminal(f"[ACTION] {name} pressed")

            popup = tk.Toplevel(self)
            popup.title("Send Setpoints")
            popup.resizable(False, False)
            popup.transient(self)
            popup.grab_set()

            tk.Label(
                popup,
                text="Enter setpoints in SLPM:",
                justify="left"
            ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5))

            valve_var = tk.IntVar(value=1)  # default OPEN
            tk.Checkbutton(
                popup,
                text="Valve Open",
                variable=valve_var
            ).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)

            sp_vars = []
            for i in range(5):
                tk.Label(popup, text=f"MFC {i+1}:").grid(
                    row=i+2, column=0, sticky="e", padx=5, pady=2
                )
                v = tk.StringVar()
                tk.Entry(popup, textvariable=v, width=12).grid(
                    row=i+2, column=1, padx=5, pady=2
                )
                sp_vars.append(v)

            def submit(): # Gather, process, and send data from window when enter button pressed
                setpoints = []
                for v in sp_vars:
                    text = v.get().strip()
                    setpoints.append(float(text) if text else 0.0)

                custom_send = [3, valve_var.get(), *setpoints] # [State (3 = custom setpoints), Valve, MFC1, MFC2, MFC3, MFC4, MFC5]
                self.cs.custom_setpoints = custom_send
                self.cs.set_state(3)
                self.write_to_terminal(f"[UI] Sent custom setpoints: {custom_send}")
                popup.destroy()

            tk.Button(popup, text="Enter", command=submit).grid(
                row=7, column=0, columnspan=2, pady=10
            )

        if name == self.function_buttons[7]:  # Save Data button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.save_histories_to_excel()
        if name == self.function_buttons[8]:  # Clear Data button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.dh.setpoint_history = [[0,0,0,0,0]]
            self.dh.response_history = [[0,0,0,0,0]]
            self.dh.sensor_history = [[0,0,0,0,0,0]]
            self.dh.valve_history = [[0,0]]
            self.update_graphs()
            self.write_to_terminal("[INFO] All data histories cleared.")
        if name == self.function_buttons[9]:  # Ambient Calibration button
            self.write_to_terminal(f"[ACTION] {name} pressed")
            self.cs.set_state(4) # Set state to AMBIENT CALIBRATION


    
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
            elif self.cs.STATE == 3:
                color = "orange"
                text = "CUSTOM SETPOINTS"
            elif self.cs.STATE == 4:
                color = "orange"
                text = "AMBIENT CALIBRATION"
            self.indicator_widgets[name].config(text=text)
            self.indicator_widgets[name].config(bg=color)
        elif name == self.indicators[1]: # Valve state indicator
            valve_state = self.dh.valve_history[-1][1]
            if valve_state == 1:
                color = "yellow"
                text = "VALVE OPEN"
            else:
                color = "green"
                text = "VALVE CLOSED"
            self.indicator_widgets[name].config(text=text)
            self.indicator_widgets[name].config(bg=color)
        elif name == self.indicators[2]: # Arduino Connection Indicator
            if self.dh.Arduino_connected:
                color = "green"
                text = "ARDUINO CONNECTED"
            else:
                color = "red"
                text = "ARDUINO DISCONNECTED"
            self.indicator_widgets[name].config(text=text)
            self.indicator_widgets[name].config(bg=color)
        else:
            self.write_to_terminal(f"[ERROR] Indicator '{name}' not found.")

    def update_graphs(self):
        """Update all graphs using stored data (no inputs)."""
        now = time.time()
        window = 60*5  # 5 minutes [seconds]

        # [t, ...] entries exsisting within window
        def recent(data):
            return [d for d in data if len(d) > 0 and (now - d[0]) <= window]

        #Collect and filter histories
        setpoints = recent(self.dh.setpoint_history)
        responses = recent(self.dh.response_history)
        sensors  = recent(self.dh.sensor_history)

        # split sensors into pressure and gas sensor lists
        pressure_sensors = [[s[0]] + s[1:3] for s in sensors if len(s) > 3] # [[time, pressure1, pressure2],...]
        gas_sensors = [[s[0]] + s[3:5] for s in sensors if len(s) > 3]

        # Test Plan Preview
        if not self.dh.running == True:

            ax = self.graphs[self.mfc_graphs[0]]["ax"]
            ax.clear()
            if not self.test_columns or not self.test_plan or len(self.test_plan) < 2:
                ax.text(0.5, 0.5, "No Test Plan Loaded", color="gray",
                        ha="center", va="center", transform=ax.transAxes)
            else:
                time_data = [row[0] for row in self.test_plan]

                # Plot Gas SLPM columns (indices 1-6 in test_plan, columns 0-5 in test_columns)
                for i in range(1, 6):
                    col_name = self.test_columns[i - 1]
                    y_data = [row[i] for row in self.test_plan]
                    ax.plot(time_data, y_data, label=col_name)

                ax.autoscale_view()
                ax.set_title(self.graph_names[0])
                ax.set_xlabel(self.test_columns[0])
                ax.set_ylabel(self.graph_variable_names[0][0])

                # Plot HRR on secondary axis (index 7 in test_plan, index 6 in test_columns)
                ax2 = ax.twinx()
                y_data_secondary = [row[7] for row in self.test_plan]
                ax2.plot(time_data, y_data_secondary, color="orange", label=self.test_columns[5])
                ax2.set_ylabel(self.graph_variable_names[0][1])

                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                
                ax2.legend(lines1 + lines2, labels1 + labels2,
                        loc="upper right", fontsize=6, frameon=False)

        # MFC Graphs (each has two lines)
        for i, name in enumerate(self.mfc_graphs[1:], start=0):  # skip test plan
            if name not in self.graphs:
                continue
            graph = self.graphs[name]
            ax = graph["ax"]
            lines = graph["lines"]

            # Verify data presence
            # if not setpoints or not responses: # If no data, continue
                # setpoints = [[0,0,0,0,0]]  # Dummy data to prevent errors
                # responses = [[0,0,0,0,0]]
                # ax.clear()
                # ax.set_title(name)
                # ax.text(0.5, 0.5, "No MFC Data", color="gray",
                #         ha="center", va="center", transform=ax.transAxes)
                # continue

            try:
                # Extract data for this MFC index
                times_sp = [row[0]-now for row in setpoints]
                sp_vals  = [row[i+1] for row in setpoints]
                times_rp = [row[0]-now for row in responses]
                rp_vals  = [row[i+1] for row in responses]

                lines[0].set_data(times_sp, sp_vals)
                lines[1].set_data(times_rp, rp_vals)
                ax.relim()
                ax.autoscale_view()
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Updating {name}: {e}")

        # Sensor Graphs
        if pressure_sensors:
            times = [row[0]-now for row in pressure_sensors]
            name = self.sensor_graphs[0] # Pressure Sensors
            graph = self.graphs[name]
            ax = graph["ax"]
            lines = graph["lines"]

            try:
                lines[0].set_data(times, [row[1] for row in pressure_sensors])
                lines[1].set_data(times, [row[2] for row in pressure_sensors])
                ax.relim()
                ax.autoscale_view()
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Updating {name}: {e}")
                    
        # Gas sensor Graphs
        if gas_sensors:
            times = [row[0]-now for row in gas_sensors]
            name = self.sensor_graphs[1] # Gas Sensors
            graph = self.graphs[name]
            ax = graph["ax"]
            lines = graph["lines"]

            try:
                lines[0].set_data(times, [row[1] for row in gas_sensors])
                lines[1].set_data(times, [row[2] for row in gas_sensors])
                ax.relim()
                ax.autoscale_view()
            except Exception as e:
                self.write_to_terminal(f"[ERROR] Updating {name}: {e}")
        # else:
        #     # Clear all if no sensor data
        #     for name in self.sensor_graphs:
        #         if name in self.graphs:
        #             ax = self.graphs[name]["ax"]
        #             ax.clear()
        #             ax.set_title(name)
        #             ax.text(0.5, 0.5, "No Sensor Data", color="gray",
        #                     ha="center", va="center", transform=ax.transAxes)

        # Redraw all graphs
        self.canvas.draw_idle()

    def update_values_display(self):

        values = {
        "MFC 1 Setpoint: ": lambda: self.dh.setpoint_history[-1][1],
        "MFC 2 Setpoint: ": lambda: self.dh.setpoint_history[-1][2],
        "MFC 3 Setpoint: ": lambda: self.dh.setpoint_history[-1][3],
        "MFC 4 Setpoint: ": lambda: self.dh.setpoint_history[-1][4],
        "MFC 5 Setpoint: ": lambda: self.dh.setpoint_history[-1][5],
        "MFC 1 Response: ": lambda: self.dh.response_history[-1][1],
        "MFC 2 Response: ": lambda: self.dh.response_history[-1][2],
        "MFC 3 Response: ": lambda: self.dh.response_history[-1][3],
        "MFC 4 Response: ": lambda: self.dh.response_history[-1][4],
        "MFC 5 Response: ": lambda: self.dh.response_history[-1][5],                  
        "Pressure Sensor 1: ": lambda: self.dh.sensor_history[-1][1],
        "Pressure Sensor 2: ": lambda: self.dh.sensor_history[-1][2],
        "Gas Sensor 1: ": lambda: self.dh.sensor_history[-1][3],
        "Gas Sensor 2: ": lambda: self.dh.sensor_history[-1][4],
        "Line Temperature: ": lambda: self.dh.sensor_history[-1][5],
        }

        for var, lbl in self.value_labels.items():
            if var not in values:
                continue

            val = values[var]

            # Allow callables so you can pass references later
            if callable(val):
                try:
                    val = val()
                except Exception as e:
                    val = "—"
                    print(f"[ERROR] Getting value for {var} in live values: {e}")

            lbl.config(text=f"{val}")

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
        data = pd.read_excel(file_path, header=None).to_numpy()

        t = [row[0] for row in data[4:]] # Time in seconds
        HRR = [row[7] for row in data[4:]] # Heat release rate in kW

        # Heat of combustion for all inputted gasses in kj/kg
        Gas_1_Heat_Comb = data[2][1]
        Gas_2_Heat_Comb = data[2][2]
        Gas_3_Heat_Comb = data[2][3]
        Gas_4_Heat_Comb = data[2][4]
        Gas_5_Heat_Comb = data[2][5]
        Gas_6_Heat_Comb = data[2][6]

        # Fuel density for all inputted gasses at STP in g/L 
        Gas_1_density = data[3][1]
        Gas_2_density = data[3][2]
        Gas_3_density = data[3][3]
        Gas_4_density = data[3][4]
        Gas_5_density = data[3][5]
        Gas_6_density = data[3][6]

        Gas_1_percent = [row[1] for row in data[4:]]
        Gas_2_percent = [row[2] for row in data[4:]]
        Gas_3_percent = [row[3] for row in data[4:]]
        Gas_4_percent = [row[4] for row in data[4:]]
        Gas_5_percent = [row[5] for row in data[4:]]
        Gas_6_percent = [row[6] for row in data[4:]]

        Gas_1_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_1_percent, [Gas_1_Heat_Comb] * len(Gas_1_percent), [Gas_1_density] * len(Gas_1_percent)))]
        Gas_2_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_2_percent, [Gas_2_Heat_Comb] * len(Gas_2_percent), [Gas_2_density] * len(Gas_2_percent)))]
        Gas_3_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_3_percent, [Gas_3_Heat_Comb] * len(Gas_3_percent), [Gas_3_density] * len(Gas_3_percent)))]
        Gas_4_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_4_percent, [Gas_4_Heat_Comb] * len(Gas_4_percent), [Gas_4_density] * len(Gas_4_percent)))]
        Gas_5_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_5_percent, [Gas_5_Heat_Comb] * len(Gas_5_percent), [Gas_5_density] * len(Gas_5_percent)))]
        Gas_6_SLPM = [0 if heat_comb == 0 else percent * (HRR[i] / heat_comb) * 60000 / density for i, (percent, heat_comb, density) in enumerate(zip(Gas_6_percent, [Gas_6_Heat_Comb] * len(Gas_6_percent), [Gas_6_density] * len(Gas_6_percent)))]


        # convert to graphable format according to standard in rest of code
        self.test_plan = [] # [[Time1, Val1.1, Val2.1, ...], [Time2, Val1.2, Val2.2,...], ...]
        for i in range(len(t)):
            self.test_plan.append([t[i], Gas_1_SLPM[i], Gas_2_SLPM[i], Gas_3_SLPM[i], Gas_4_SLPM[i], Gas_5_SLPM[i], Gas_6_SLPM[i], HRR[i]])

        # Interpolate the plan for smooth execution
        if len(self.test_plan) >= 2:
            interpolated = []
            for i in range(len(self.test_plan) - 1):
                t0, t1 = self.test_plan[i][0], self.test_plan[i + 1][0]
                vals0, vals1 = self.test_plan[i][1:], self.test_plan[i + 1][1:]

                t = t0
                while t < t1:
                    alpha = (t - t0) / (t1 - t0)
                    interp_vals = [v0 + alpha * (v1 - v0) for v0, v1 in zip(vals0, vals1)]
                    interpolated.append([t] + interp_vals)
                    t += resolution

            interpolated.append(self.test_plan[-1][:])
            self.test_plan[:] = interpolated



        self.test_columns = [data[0][1], data[0][2], data[0][3], data[0][4], data[0][5], data[0][6]]

        self.update_graphs()




    def print_variables(self):
        self.write_to_terminal(f"Test Columns: {self.test_columns}")
        self.write_to_terminal(f"Test Plan (first 5 rows):")
        for row in self.test_plan:
            self.write_to_terminal(f"{row}")

    def save_histories_to_excel(self):

        if self.dh.setpoint_history == [] and self.dh.response_history == [] and self.dh.sensor_history == [] and self.dh.valve_history == []:
            self.write_to_terminal("[ERROR] No data to save.")
            return
        root = tk.Tk()
        root.withdraw()

        path = filedialog.asksaveasfilename(
            title="Save data",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not path:
            return

        # --- extract time (assume uniform) ---
        time = [row[0]-self.dh.run_start for row in self.dh.response_history]

        n_mfc_set = 5
        n_mfc_resp = 5
        n_sensors = 5 

        data = {"Time": time}

        for i in range(n_mfc_set):
            data[f"MFC {i+1} setpoint"] = [row[i+1] for row in self.dh.setpoint_history]

        for i in range(n_mfc_resp):
            data[f"MFC {i+1} response"] = [row[i+1] for row in self.dh.response_history]

        sensor_names = ["MC Pressure", "Line Pressure", "Gas 1", "Gas 2","Line Temperature"]
        for i in range(n_sensors):
            name = sensor_names[i] if i < len(sensor_names) else f"Sensor {i+1}"
            data[name] = [row[i+1] for row in self.dh.sensor_history]

        data["Valve state"] = [row[1] for row in self.dh.valve_history]

        pd.DataFrame(data).to_excel(path, index=False)

