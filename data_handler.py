import serial
import serial.tools.list_ports
import time
import threading
import time
import gc

from MFC_Sim_Object import MFC_Simulator


class Data_Handler:
    """
    Handles serial communication with an Arduino and data saving
    """

    def __init__(self):
        """
        Initialize serial connection and start communication thread.
        """

        # data saving parameters 
        # mfc_history = [ [time1,[mfc1_response,mfc2_response,...,Valve_State]] , [time2,[mfc1_response,mfc2_response,...,Valve_State]] , ...]
        self.setpoint_history = []
        self.response_history = [] 
        self.sensor_history = [] # [[time, pressure1, sensor2, Gas Sensor 1, Gas Sensor 2,...],...]
        self.valve_history = [] # [[time, valve_state],...]

        # Arduino Serial Communication Parameters
        self.Arduino_connected = False
        self.port = "COM3"
        self.baudrate = 115200
        self.timeout = 1  # seconds
        self.delimiter = ","
        self.running = False
        self.thread = None
        self.serial = None
        self.num_mfcs = 0

    
        # simulation variables as needed
        self.do_sim = False
        self.sim_mfcs = []

        # Initialize connection to other objects
        self.UI = None  # Placeholder for UI object
        self.cs = None  # Placeholder for Control System object

    def connect_to_arduino(self):
        """Establish serial connection to Arduino."""
        self.UI.write_to_terminal("Attempting to connect to Arduino...")
        self.port = self.find_arduino_port()
        try:
            if self.port == None:
                self.UI.write_to_terminal("No Arduino found. Cannot connect.")
                return
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # allow Arduino to reset
            self.UI.write_to_terminal(f"Connected to Arduino on {self.port}")
            self.Arduino_connected = True
        except serial.SerialException as e:
            self.UI.write_to_terminal(f"Error connecting to Arduino: {e}")
            self.serial = None
        self.UI.update_indicators(name=self.UI.indicators[2])

    def find_arduino_port(self):
        """
        Automatically detect which COM port an Arduino is connected to.
        Tries to open each available serial port and look for Arduino-like identifiers.

        Returns:
            str: The detected port name (e.g. "COM3") or None if not found.
        """
        # List all available ports
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            self.UI.write_to_terminal("No serial ports found.")
            return None

        for port in ports:
            # Common Arduino identifiers (can be extended)
            arduino_keywords = ["arduino", "ch340", "usb serial", "mega", "uno", "nano", "leonardo"]

            desc = f"{port.description}".lower()
            hwid = f"{port.hwid}".lower()

            if any(keyword in desc or keyword in hwid for keyword in arduino_keywords):
                self.UI.write_to_terminal(f"Detected Arduino-like device on {port.device} ({port.description})")
                # Verify communication
                try:
                    with serial.Serial(
                            port=port.device,
                            baudrate=self.baudrate,
                            timeout=self.timeout
                        ) as ser:
                        self.UI.write_to_terminal(f"Opened {port.device}")
                        return port.device
                except (OSError, serial.SerialException):
                    continue

        self.UI.write_to_terminal("No Arduino detected on available ports.")
        return None


    def send_data(self,new_setpoints):
        """Send the list of data values to Arduino."""
        self.UI.write_to_terminal(f"[Data_Handler] Sending setpoints: {new_setpoints}")
        if self.Arduino_connected == False: # check if arduino connected
            self.UI.write_to_terminal("[Data_Handler] Cannot send data, Arduino not connected.")
            return

        try:
            # new_setpoints = [State (3 = custom setpoints), Valve, MFC1, MFC2, MFC3, MFC4, MFC5]
            # Convert list to string for sending
            # Example: "1.0,0,23.4\n"
            out_string = self.delimiter.join(map(str, new_setpoints)) + "\n"
            self.serial.write(out_string.encode("utf-8")) # Send the data
            self.setpoint_history.append([time.time(), list(new_setpoints[2:7])]) # Save mfc setpoints
            self.UI.write_to_terminal(f"[Data_Handler] Sent data: {out_string.strip()}")

        except Exception as e:
            self.UI.write_to_terminal(f"Error sending data: {e}")

        time.sleep(.26)
        self.read_data() # Immediately read response after sending setpoints to minimize delay

    def read_data(self):
        """Read and parse incoming data from Arduino with seq heartbeat check."""
        self.UI.write_to_terminal("Checking for incoming data from Arduino...")
        if not self.serial or not self.serial.in_waiting:
            self.UI.write_to_terminal("No data available to read.")
            return

        try:
            line = self.serial.readline().decode("utf-8", errors="ignore").strip()
            # Should recieve:
            # Seq, State, Valve state, MFC1 Response, MFC2 Response, MFC3 Response,
            #  MFC4 Response, MFC5 Response, Mixing Chamber Pressure, Pipe Pressure, Gas Sensor 1, Gas Sensor 2
            if not line:
                self.UI.write_to_terminal("Received empty line from Arduino.")
                return

            parts = line.split(",")
            if len(parts) != 12: # Should recieve the number of elements as descirbed above
                self.UI.write_to_terminal(f"Malformed data packet: {line}")
                print(line)
                return  # hard drop malformed packets

            seq = int(parts[0])

            # initialize on first run
            if not hasattr(self, "last_seq"):
                self.last_seq = seq
                self.heartbeat = 0

            # heartbeat logic
            if seq == self.last_seq:
                self.heartbeat += 1

            # seq changed → accept data
            self.last_seq = seq
            self.heartbeat = 0
            t = time.time()

            # parse values
            valve = int(parts[2])

            mfc_vals = list(map(float, parts[3:8]))          # MFC1–MFC5
            sensor_vals = list(map(float, parts[8:13]))      # pressures + gas sensors

            # store histories (raw lists, no labels)
            self.response_history.append([t, *mfc_vals])
            self.valve_history.append([t, valve])
            self.sensor_history.append([t, *sensor_vals])
            self.UI.write_to_terminal(f"[Data_Handler] Received data: Seq={seq}, Valve={valve}, MFCs={mfc_vals}, Sensors={sensor_vals}")

        except Exception as e:
            self.UI.write_to_terminal(f"[Data_Handler] Error reading arduino data: {e}")



    def update_setpoints(self, new_setpoints):
        """Update the data_out list with new setpoints."""
        if self.running == False: # check if arduino connected or sim running
            self.UI.write_to_terminal("[Data_Handler] Cannot update setpoints, communication/simulation not running.")
            return
        
        # if self.do_sim: # Running a simulation
        #     if len(new_setpoints) != len(self.sim_mfcs): # check for data compatability
        #         self.UI.write_to_terminal(f"[Data_Handler] Number of setpoints ({len(new_setpoints)}) does not match number of simulated MFCs ({len(self.sim_mfcs)}).")
        #         return
        #     for i in range(len(self.sim_mfcs)): # Update each simulated MFC setpoint
        #         self.sim_mfcs[i].set_setpoint(new_setpoints[i])
        #     self.setpoint_history.append([time.time(),enumerate(new_setpoints)]) # Save mfc setpoints

        #     # save mfc response current value
        #     self.mfc_response_history.append([time.time(),[self.sim_mfcs[i].get_value() for i in range(len(self.sim_mfcs))]])

        if self.Arduino_connected: # Running Arduino communication
            self.UI.write_to_terminal("Sending Setpoints")
            self.send_data(new_setpoints)
        else:
            self.UI.write_to_terminal("[Data_Handler] Unknown operation mode.")

    # ### # Define similair functions for simulation instead of arduino communication
    # def start_sim(self,number_of_mfcs=5):
    #     """Create and start mfc simulation objects"""
    #     self.do_sim = True
    #     self.running = True
    #     self.sim_mfcs = []
    #     self.num_mfcs = number_of_mfcs
    #     for i in range(self.num_mfcs):
    #         self.sim_mfcs.append(MFC_Simulator())
    #         self.sim_mfcs[i].start()

    # def end_sim(self):
    #     """Stop and fully clear all MFC simulators."""
    #     self.do_sim = False
    #     for sim in self.sim_mfcs:
    #         try:
    #             sim.stop()
    #         except Exception as e:
    #             print(f"Warning: failed to stop simulator: {e}")
    #     self.sim_mfcs.clear()  # now it's []
    #     gc.collect()

    def check_emergency_conditions(self):
        # Emergency condition values
        # Name, Test type, Value, Min, warning min, warning max, max 
        # If test is binary (T/F) then use 0,0,0,1 where last value is desired state

        MFC_setpoint_tests = [
            [f"MFC {i+1} Setpoint",
             "All",
               self.setpoint_history[-1][1][i], 0, 0, 9, 10]
            for i in range(len(self.setpoint_history[-1][1]))
        ]

        MFC_response_tests = [[f"MFC {i+1} Response",
                                "All", self.setpoint_history[-1][i+1],
                                  0, 0, 1.1*MFC_setpoint_tests[i][2], 1.2*MFC_setpoint_tests[i][2]]
                                    for i in range(len(self.setpoint_history[-1][1:]))] # Warning at over 110% of setpoint, max at 120%
        MFC_response_Error_delta_tests = [[f"MFC {i+1} Response Error Delta",
                                            "All",
                                              abs(self.response_history[-1][i+1]-self.setpoint_history[-1][1:][i])/self.setpoint_history[-1][1:][i], 0, 0, 0.1, 0.2]
                                                for i in range(len(self.setpoint_history[-1][1:]))] # Warning at over 10% error, max at 20%

        emergency_tests = [
            MFC_setpoint_tests,
            MFC_response_tests,
            MFC_response_Error_delta_tests,
            ["Pressure Sensor 1", "All", self.sensor_history[-1][1], 0, 0, 135, 150],
            ["Pressure Sensor 2", "All", self.sensor_history[-1][2], 0, 0, 40, 50],
            ["Gas Sensor 1", "All", self.sensor_history[-1][3], 0, 0, 40, 50],
            ["Gas Sensor 2", "All", self.sensor_history[-1][4], 0, 0, 40, 50],
            ["Valve State", "Binary", self.valve_history[-1][1], 0, 0, 1, self.setpoint_history[-1][-1]], # test if valve state matches the most recent setpoint issued
            ["Arduino Connected", "Binary", self.Arduino_connected, 0, 0, 1, 1] # 0 = disconnected, 1 = connected
        ]

        # Cylce through each test and check for violations
        violations = []
        for test in emergency_tests:
            if test[1] == "All":
                if test[2] < test[3]: # if the value is below min
                    violations.append(f"{test[0]} below minimum")
                elif test[2] < test[4]: # if value below warning min
                    violations.append(f"{test[0]} below warning threshold")
                elif test[2] > test[5]: # if value above warning max
                    violations.append(f"{test[0]} above warning threshold")
                elif test[2] > test[6]: # if value above max
                    violations.append(f"{test[0]} above maximum")
            elif test[1] == "Binary":
                # Handle binary tests
                if test[2] != test[6]:
                    violations.append(f"{test[0]} not in desired state")
            else:
                self.UI.write_to_terminal(f"Unknown test type '{test[1]}' for {test[0]}")
        if violations != []:
            self.UI.write_to_terminal(f"Warning: {', '.join(violations)}")
            self.cs.STATE = 0
