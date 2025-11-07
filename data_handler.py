import serial
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
        # mfc_history = [ [time1,[mfc1_response,mfc2_response,...]] , [time2,[mfc1_response,mfc2_response,...]] , ...]
        self.setpoint_history = []
        self.mfc_response_history = [] 
        self.sensor_history = [] # [[time, pressure1, sensor2,...],...]

        # Arduino Serial Communication Parameters
        self.port = "COM3"
        self.baudrate = 93000
        self.timeout = 1  # seconds
        self.delimiter = ","
        self.running = False
        self.thread = None
        self.serial = None
        self.num_mfcs = 0

        # Variables to send and receive
        # self.data_out = [target_pressure, valve_state, setpoint]
        self.data_out = []
        self.received_data_lists = {}

        # simulation variables as needed
        self.do_sim = False
        self.sim_mfcs = []

        # Initialize connection to other objects
        self.UI = None  # Placeholder for UI object
        self.cs = None  # Placeholder for Control System object

    def connect_to_aurduino(self):
        """Establish serial connection to Arduino."""
        self.port = self.find_arduino_port(baudrate=self.baudrate, timeout=self.timeout)
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # allow Arduino to reset
            self.UI.write_to_terminal(f"Connected to Arduino on {self.port}")
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
            if self.verbose:
                self.UI.write_to_terminal("No serial ports found.")
            return None

        for port in ports:
            # Common Arduino identifiers (can be extended)
            arduino_keywords = ["arduino", "ch340", "usb serial", "mega", "uno", "nano", "leonardo"]

            desc = f"{port.description}".lower()
            hwid = f"{port.hwid}".lower()

            if any(keyword in desc or keyword in hwid for keyword in arduino_keywords):
                if self.verbose:
                    self.UI.write_to_terminal(f"Detected Arduino-like device on {port.device} ({port.description})")
                # Verify communication
                try:
                    with serial.Serial(port.device, self.baudrate, self.timeout) as ser:
                        time.sleep(2)  # allow device reset
                        ser.write(b"ping\n")  # optional handshake
                        time.sleep(0.1)
                        response = ser.readline().decode(errors="ignore").strip()
                        if self.verbose:
                            self.UI.write_to_terminal(f"Response from {port.device}: {response}")
                        # You can check for specific expected responses if you have a known sketch behavior
                        return port.device
                except (OSError, serial.SerialException):
                    continue

        if self.verbose:
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

    def send_data(self):
        """Send the list of data values to Arduino."""
        if self.serial is None:
            return

        try:
            # Convert list to string for sending
            # Example: "1.0,0,23.4\n"
            out_string = self.delimiter.join(map(str, self.data_out)) + "\n"
            self.serial.write(out_string.encode("utf-8"))
        except Exception as e:
            self.UI.write_to_terminal(f"Error sending data: {e}")

    def read_data(self):
        """Read and parse incoming data from Arduino."""
        if not self.serial or not self.serial.in_waiting:
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
            # (Leave the above section blank until you decide what to do)
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
            pass

    ### # Define similair functions for simulation instead of arduino communication
    def start_sim(self,number_of_mfcs=2):
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





