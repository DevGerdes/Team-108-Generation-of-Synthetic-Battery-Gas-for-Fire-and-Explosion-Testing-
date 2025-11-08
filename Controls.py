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
        # Initialize conection to UI and data handler
        self.UI = None
        self.dh = None
        ### Define global variables
        #self.STATE change definitions
        #  0 = Emergency Stop
        #  1 = Idle
        # 2 = Run Test
        self.STATE = 1  # Default to Idle state  

    # ---------- Core Loop ---------- #
    def _loop(self):
        while self.running:
            oldstate = self.STATE
            if not self.STATE == oldstate: # If state has changed
                if self.STATE == 0: # Emergency Stop
                    self.emergency_stop()
                elif self.STATE == 1: # Idle
                    self.idle()
                elif self.STATE == 2: # Run Test
                    self.run_test()
                else:
                    print(f"[STATE: UNKNOWN] No handler forself.STATE '{self.STATE}'")
            time.sleep(self.resolution)

    # Control Methods
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
            self.UI.write_to_terminal("[ControlSystem] Stopped main loop.")

    def set_state(self, new_state):
        """Changes the system self.STATE dynamically."""
        self.UI.write_to_terminal(f"[ControlSystem] STATE changed to '{new_state}'")
        self.STATE = new_state
        self.UI.update_indicators(name=self.UI.indicators[0])

    ######### State specific logic

    def emergency_stop(self):
        self.UI.write_to_terminal("[STATE: EMERGENCY STOP] System or user detected emergency conditions...")

    def idle(self):
        self.UI.write_to_terminal("[STATE: IDLE System is standing by...")

    def run_test(self):
        self.UI.write_to_terminal("[STATE: RUNNING] Running test...")
        time.sleep(self.resolution)

        while self.STATE == 2:
            self.dh.check_emergency_conditions()
            if self.STATE == 0:
                return