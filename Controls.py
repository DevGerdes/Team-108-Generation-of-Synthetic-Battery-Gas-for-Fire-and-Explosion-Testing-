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
    def __init__(self):
        self.running = False              # Thread control flag
        self.thread = None                # Worker thread reference
        self.resolution = .2      # Loop resolution in seconds
        # Initialize conection to UI and data handler
        self.UI = None
        self.dh = None
        ### Define global variables
        #self.STATE change definitions
        #  0 = Emergency Stop
        #  1 = Idle
        # 2 = Run Test
        # 3 = Run custom setpoints
        self.STATE = 1  # Default to Idle state  
        self.custom_setpoints = [0,0,0,0,0,0,0] # Placeholder for custom setpoints (STATE,Valve, MFC1, MFC2, MFC3, MFC4, MFC5)

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
                elif self.STATE == 3: # Run custom setpoints
                    # Custom setpoints should be sent immediately when state changes, so just maintain them here
                    self.run_custom()
                else:
                    print(f"[STATE: UNKNOWN] No handler for self.STATE '{self.STATE}'")
                    self.STATE = 0
                    self.emergency_stop()
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
        self.dh.update_setpoints([0,0,0,0,0,0,0]) # Send zero flow to all MFC's and close valve
        self.UI.write_to_terminal("[STATE: EMERGENCY STOP] System or user detected emergency conditions...")

    def idle(self):
        self.dh.update_setpoints([1,0,0,0,0,0,0]) # Send zero flow to all MFC's and close valve
        self.UI.write_to_terminal("[STATE: IDLE System is standing by...")
            

    def run_test(self):
        self.UI.write_to_terminal("[STATE: RUNNING] Running test...")

        # Grab interpolated schedule
        plan = self.UI.test_plan
        t_vec = plan[0]          # time axis
        data_cols = plan[1:]    # signals
        if len(t_vec) == 0:
            self.UI.write_to_terminal("ERROR: Empty test plan")
            return
        test_start = time.time()
        idx = 0                 # index into test_plan time vector

        # Run until stopped or end of test
        while self.STATE == 2 and idx < len(t_vec):
            self.dh.check_emergency_conditions()
            if self.STATE != 2:
                break

            # Elapsed test time
            t_now = time.time() - test_start
            # Advance index while current test time exceeds scheduled time
            while idx < len(t_vec) and t_now >= t_vec[idx]:

                data = []
                for col_i in range(1,len(data_cols) - 1): # Skip time column
                    data.append(data_cols[col_i][idx])

                self.dh.update_setpoints(data)
                idx += 1


            time.sleep(self.resolution)

    def run_custom(self, setpoints):
        self.UI.write_to_terminal(f"[CONTROLS: RUNNING CUSTOM SETPOINTS]: {setpoints}")
        self.set_state(3)
        self.dh.update_setpoints(setpoints)
        while self.STATE == 3:
            self.dh.check_emergency_conditions()
            if self.STATE != 3:
                break
            time.sleep(self.resolution)