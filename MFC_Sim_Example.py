import tkinter as tk
from tkinter import ttk
import time
import threading
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

from MFC_Sim_Object import MFC_Simulator  # Import your simulator class

matplotlib.use("TkAgg")


class MFC_UI:
    def __init__(self, root, resolution=0.2):
        self.root = root
        self.root.title("MFC Simulator Control Panel")

        # Parameters
        self.resolution = resolution
        self.window_length = 10.0  # seconds of history to plot
        self.max_points = int(self.window_length / self.resolution)

        # Create simulator
        self.mfc = MFC_Simulator(Kp=0.8, Ki=0.2, Kd=0.05)

        # Time-series data
        self.time_data = deque(maxlen=self.max_points)
        self.response_data = deque(maxlen=self.max_points)
        self.setpoint_data = deque(maxlen=self.max_points)
        self.start_time = time.time()

        # --- UI Layout ---
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Setpoint entry
        ttk.Label(main_frame, text="Setpoint:").grid(row=0, column=0, sticky="w")
        self.setpoint_var = tk.DoubleVar(value=0.0)
        setpoint_entry = ttk.Entry(main_frame, textvariable=self.setpoint_var, width=10)
        setpoint_entry.grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Apply", command=self.update_setpoint).grid(row=0, column=2)

        # --- Matplotlib Figure ---
        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.ax.set_title("MFC Response vs Setpoint")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")

        self.response_line, = self.ax.plot([], [], label="Response", color="blue")
        self.setpoint_line, = self.ax.plot([], [], label="Setpoint", color="red", linestyle="--")
        self.ax.legend()

        # Embed figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, columnspan=3, pady=10)

        # Start periodic updates
        self.update_plot()

    def update_setpoint(self):
        """Set a new setpoint in the simulator."""
        new_sp = self.setpoint_var.get()
        self.mfc.set_setpoint(new_sp)

    def update_plot(self):
        """Update the live plot with current response and setpoint."""
        current_time = time.time() - self.start_time
        response = self.mfc.get_value()
        setpoint = self.mfc.setpoint

        # Append new data points
        self.time_data.append(current_time)
        self.response_data.append(response)
        self.setpoint_data.append(setpoint)

        # Update line data
        self.response_line.set_data(self.time_data, self.response_data)
        self.setpoint_line.set_data(self.time_data, self.setpoint_data)

        # Keep 10-second rolling window
        if len(self.time_data) > 1:
            self.ax.set_xlim(max(0, self.time_data[-1] - self.window_length), self.time_data[-1])
            all_values = list(self.response_data) + list(self.setpoint_data)
            self.ax.set_ylim(min(all_values) - 1, max(all_values) + 1)

        self.canvas.draw()

        # Schedule next update
        self.root.after(int(self.resolution * 1000), self.update_plot)


if __name__ == "__main__":
    root = tk.Tk()
    app = MFC_UI(root, resolution=0.2)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.mfc.stop(), root.destroy()))
    root.mainloop()
