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
        self.mfc_response_history = [] 
        self.sensor_history = [] # [[time, pressure1, sensor2,...],...]

        # Arduino Serial Communication Parameters
        self.Arduino_connected = False
        self.port = "COM3"
        self.baudrate = 93000
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

    def start(self):
        """Start background communication loop."""
        if not self.serial:
            self.UI.write_to_terminal("Serial connection not established.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._comm_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop communication and close serial port."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.UI.write_to_terminal("Serial communication stopped.")

    def _comm_loop(self):
        """Main background loop for sending and receiving data."""
        while self.running:
            try:
                self.send_data()
                self.read_data()
                time.sleep(self.refresh_rate)
            except serial.SerialException as e:
                self.UI.write_to_terminal(f"Serial error: {e}")
                self.running = False
                self.Arduino_connected = False

    def send_data(self,new_setpoints):
        """Send the list of data values to Arduino."""
        if self.Arduino_connected == False: # check if arduino connected
            self.UI.write_to_terminal("[Data_Handler] Cannot send data, Arduino not connected.")
            return

        try:
            # Convert list to string for sending
            # Example: "1.0,0,23.4\n"
            out_string = self.delimiter.join(map(str, new_setpoints)) + "\n"
            self.serial.write(out_string.encode("utf-8"))
            self.setpoint_history.append([time.time(),enumerate(new_setpoints)]) # Save mfc and valve setpoints
        except Exception as e:
            self.UI.write_to_terminal(f"Error sending data: {e}")

    def read_data(self):
        """Read and parse incoming data from Arduino."""
        if not self.serial or not self.serial.in_waiting: # if no data
            return

        try:
            line = self.serial.readline().decode("utf-8").strip()
            if not line:
                return

            parts = line.split(self.delimiter)
            # Example of assigning parsed values:
            # ---------------------------------------
            # value1, value2, value3 = map(float, parts)
            # self.sensor_readings.append(value1)
            # self.timestamps.append(time.time())
            # ---------------------------------------
        except Exception as e:
            self.UI.write_to_terminal(f"Error reading data: {e}")

    def update_setpoints(self, new_setpoints):
        """Update the data_out list with new setpoints."""
        if self.running == False: # check if arduino connected or sim running
            self.UI.write_to_terminal("[Data_Handler] Cannot update setpoints, communication/simulation not running.")
            return
        
        if self.do_sim: # Running a simulation
            if len(new_setpoints) != len(self.sim_mfcs): # check for data compatability
                self.UI.write_to_terminal(f"[Data_Handler] Number of setpoints ({len(new_setpoints)}) does not match number of simulated MFCs ({len(self.sim_mfcs)}).")
                return
            for i in range(len(self.sim_mfcs)): # Update each simulated MFC setpoint
                self.sim_mfcs[i].set_setpoint(new_setpoints[i])
            self.setpoint_history.append([time.time(),enumerate(new_setpoints)]) # Save mfc setpoints

            # save mfc response current value
            self.mfc_response_history.append([time.time(),[self.sim_mfcs[i].get_value() for i in range(len(self.sim_mfcs))]])

        elif not self.do_sim: # Running Arduino communication
            self.send_data(new_setpoints)
        else:
            self.UI.write_to_terminal("[Data_Handler] Unknown operation mode.")

    ### # Define similair functions for simulation instead of arduino communication
    def start_sim(self,number_of_mfcs=5):
        """Create and start mfc simulation objects"""
        self.do_sim = True
        self.running = True
        self.sim_mfcs = []
        self.num_mfcs = number_of_mfcs
        for i in range(self.num_mfcs):
            self.sim_mfcs.append(MFC_Simulator())
            self.sim_mfcs[i].start()

    def end_sim(self):
        """Stop and fully clear all MFC simulators."""
        self.do_sim = False
        for sim in self.sim_mfcs:
            try:
                sim.stop()
            except Exception as e:
                print(f"Warning: failed to stop simulator: {e}")
        self.sim_mfcs.clear()  # now it's []
        gc.collect()

    def check_emergency_conditions(self, new_setpoints):
        # Emergency condition values
        # Name, Test type, Value, Min, warning min, warning max, max 
        # If test is binary (T/F) then use 0,0,1,1 where max values are desired state
        num_mfcs = len(new_setpoints)
        MFC_setpoint_tests = [[f"MFC {i+1} Setpoint", "All", new_setpoints[i], 0, 0, 9, 10] for i in range(num_mfcs)]
        MFC_response_tests = [[f"MFC {i+1} Response", "All", self.mfc_response_history[-1][i+1], 0, 0, 1.1*MFC_setpoint_tests[i], 1.2*MFC_setpoint_tests[i]] for i in range(num_mfcs)] # Warning at over 110% of setpoint, max at 120%
        MFC_response_Error_delta_tests = [[f"MFC {i+1} Response Error Delta", "All", abs(self.mfc_response_history[-1][i+1]-new_setpoints[i])/new_setpoints[i], 0, 0, 0.1, 0.2] for i in range(num_mfcs)] # Warning at over 10% error, max at 20%

        emergency_tests = [
            MFC_setpoint_tests,
            MFC_response_tests,
            MFC_response_Error_delta_tests,
            ["Pressure Sensor 1", "All", self.pressure_sensor_1, 0, 0, 135, 150],
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
            print("Warning:", ", ".join(violations))
            self.cs.STATE = 0
