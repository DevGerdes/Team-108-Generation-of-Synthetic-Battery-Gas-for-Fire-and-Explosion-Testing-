import tkinter as tk
from tkinter import scrolledtext
from tkinter import Tk, filedialog
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd
import threading


class ControlSystem:
    def __init__(self,resolution):
        self.running = False              # Thread control flag
        self.thread = None                # Worker thread reference
        self.resolution = resolution      # Loop resolution in seconds
        # Initialize conection to UI
        self.UI = None

    # ---------- Core Loop ---------- #
    def _loop(self):
        global STATE
        while self.running:
            if STATE == 0: # Emergency Stop
                self.emergency_stop()
            elif STATE == 1: # Idle
                self.idle()
            elif STATE == 2: # Run Test
                self.run_test()
            else:
                print(f"[STATE: UNKNOWN] No handler for state '{STATE}'")
        time.sleep(self.resolution)


    # ---------- Example State Functions ---------- #
    def emergency_stop(self):
        print("[STATE: IDLE] System is idle...")

    def idle(self):
        print("[STATE: RUNNING] System is running process...")

    def run_test(self):
        print("[STATE: ERROR] System encountered an error!")

    # ---------- Control Methods ---------- #
    def start(self):
        """Starts the threaded control system loop."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.UI.write_to_terminal("[ControlSystem] Started main loop.")

    def stop(self):
        """Stops the threaded control system loop."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1)
            print("[ControlSystem] Stopped main loop.")

    def set_state(self, new_state):
        global STATE
        """Changes the system state dynamically."""
        print(f"[ControlSystem] State changed to '{new_state}'")
        STATE = new_state


# ---------- Example usage ---------- #
STATE = 0
resolution = .2

if __name__ == "__main__":
    cs = ControlSystem(resolution=0.2)
    cs.start()

    time.sleep(1)
    cs.set_state("RUNNING")
    time.sleep(1)
    cs.set_state("ERROR")
    time.sleep(1)
    cs.set_state("IDLE")

    cs.stop()
