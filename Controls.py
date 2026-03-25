import time
import numpy as np
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
        self.oldstate = 1 # for controls loop logic
        self.custom_setpoints = [] # Placeholder for custom setpoints (STATE,Valve, MFC1, MFC2, MFC3, MFC4, MFC5)

    # ---------- Core Loop ---------- #
    def _loop(self):
        while self.running:
            if not self.STATE == self.oldstate: # If state has changed
                self.oldstate = self.STATE
                if self.STATE == 0: # Emergency Stop
                    self.emergency_stop()
                elif self.STATE == 1: # Idle
                    self.dh.running = False
                    self.idle()
                elif self.STATE == 2: # Run Test
                    self.dh.run_start = time.time()
                    self.dh.running = True
                    self.run_test()
                elif self.STATE == 3: # Run custom setpoints
                    # Custom setpoints should be sent immediately when state changes, so just maintain them here
                    self.dh.run_start = time.time()
                    self.dh.running = True
                    self.run_custom()
                elif self.STATE == 4: # Ambient Calibration
                    self.dh.run_start = time.time()
                    self.dh.running = True
                    self.UI.write_to_terminal("[STATE: AMBIENT CALIBRATION] Starting ambient calibration...")
                    self.ambient_calibration()
                    self.set_state(1) # Return to idle when done

                else:
                    self.UI.write_to_terminal(f"[STATE: UNKNOWN] No handler for self.STATE '{self.STATE}'")
                    self.STATE = 0
                    self.emergency_stop()
            time.sleep(self.resolution/10)

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
            self.set_state(1)
            self.UI.write_to_terminal("[ControlSystem] Stopped main loop.")

    def set_state(self, new_state):
        """Changes the system self.STATE dynamically."""
        self.UI.write_to_terminal(f"[ControlSystem] STATE changed to '{new_state}'")
        self.STATE = new_state
        self.UI.update_indicators(name=self.UI.indicators[0])

    ######### State specific logic

    def emergency_stop(self):
        self.UI.write_to_terminal("[STATE: EMERGENCY STOP] System or user detected emergency conditions...")
        while self.STATE == 0:
            if self.STATE != 0:
                break
            self.dh.update_setpoints([0,0,0,0,0,0,0]) # Send zero flow to all MFC's and close valve
            time.sleep(self.resolution)

    def idle(self):
        self.dh.update_setpoints([1,0,0,0,0,0,0]) # Send zero flow to all MFC's and close valve
        self.UI.write_to_terminal("[STATE: IDLE] System is standing by...")
            

    def run_test(self):
        self.UI.write_to_terminal("[STATE: RUNNING] Running test...")

        # Grab interpolated schedule
        plan = self.UI.test_plan
        t_vec = [row[0] for row in plan]   # time axis
        data_cols = [row[1:] for row in plan]    # signals
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

            self.UI.update_graphs() # Update graphs at each loop iteration
            self.UI.update_values_display()
            time.sleep(self.resolution)
        
        self.set_state(1) # Return to idle when done

    def run_custom(self):
        self.UI.write_to_terminal(f"[CONTROLS: RUNNING CUSTOM SETPOINTS]: {self.custom_setpoints}")
        self.dh.update_setpoints(self.custom_setpoints)
        while self.STATE == 3:
            self.dh.check_emergency_conditions()
            if self.STATE != 3:
                break
            self.dh.update_setpoints(self.custom_setpoints)
            self.UI.update_graphs() # Update graphs at each loop iteration
            self.UI.update_values_display()
            time.sleep(self.resolution)

    def ambient_calibration(self):
        self.UI.write_to_terminal("[CONTROLS: AMBIENT CALIBRATION] Starting ambient calibration procedure...")
        self.dh.update_setpoints([1,0,0,0,0,0,0]) # Open valve and set no flow to all MFCs
        calibration_start = time.time()
        calibration_duration = 30 # seconds to run calibration for
        while self.STATE == 4:
            if self.STATE != 4:
                break

            if time.time() - calibration_start < calibration_duration: # if time within conditions recording time
                self.dh.update_setpoints([1,0,0,0,0,0,0]) # send and recieve new data
                self.UI.update_graphs() # Update graphs at each loop iteration
                self.UI.update_values_display()
                #time.sleep(self.resolution)
            else:
                # process and store averages for each sensor value, then return to idle
                # self.dh.sensor_history = [[time, Mixing Chamber Pressure, Line Pressure, Methane, Gas Sensor 2,...],...]
                mixing_chamber_pressure_avg = np.mean([entry[1] for entry in self.dh.sensor_history])
                line_pressure_avg = np.mean([entry[2] for entry in self.dh.sensor_history])
                gas_sensor_1_avg = np.mean([entry[3] for entry in self.dh.sensor_history])
                gas_sensor_2_avg = np.mean([entry[4] for entry in self.dh.sensor_history])


                self.dh.state_saver("store", "mixing_chamber_pressure", mixing_chamber_pressure_avg)
                self.dh.state_saver("store", "line_pressure", line_pressure_avg)
                self.dh.state_saver("store", "Methane_Sensor", gas_sensor_1_avg)
                self.dh.state_saver("store", "gas_sensor_2", gas_sensor_2_avg)

                break
