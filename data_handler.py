import serial
import time
import threading
import serial.tools.list_ports



class Data_Handler:
    """
    Handles serial communication with an Arduino and data saving
    """

    def __init__(self):
        """
        Initialize serial connection and start communication thread.
        """
        # Arduino Serial Communication Parameters
        self.port = "COM3"
        self.baudrate = 93000
        self.timeout = 1  # seconds
        self.delimiter = ","
        self.running = False
        self.thread = None
        self.serial = None

        # Variables to send and receive
        # self.data_out = [target_pressure, valve_state, setpoint]
        self.data_out = []
        self.received_data_lists = {}

        # Initialize connection to other objects
        self.UI = None  # Placeholder for UI object
        self.cs = None  # Placeholder for Control System object

    def connect_to_aurduino(self):
        """Establish serial connection to Arduino."""
        self.port = self.find_arduino_port(baudrate=self.baudrate, timeout=self.timeout)
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # allow Arduino to reset
            print(f"Connected to Arduino on {self.port}")
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")
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
                print("No serial ports found.")
            return None

        for port in ports:
            # Common Arduino identifiers (can be extended)
            arduino_keywords = ["arduino", "ch340", "usb serial", "mega", "uno", "nano", "leonardo"]

            desc = f"{port.description}".lower()
            hwid = f"{port.hwid}".lower()

            if any(keyword in desc or keyword in hwid for keyword in arduino_keywords):
                if self.verbose:
                    print(f"Detected Arduino-like device on {port.device} ({port.description})")
                # Verify communication
                try:
                    with serial.Serial(port.device, self.baudrate, self.timeout) as ser:
                        time.sleep(2)  # allow device reset
                        ser.write(b"ping\n")  # optional handshake
                        time.sleep(0.1)
                        response = ser.readline().decode(errors="ignore").strip()
                        if self.verbose:
                            print(f"Response from {port.device}: {response}")
                        # You can check for specific expected responses if you have a known sketch behavior
                        return port.device
                except (OSError, serial.SerialException):
                    continue

        if self.verbose:
            print("No Arduino detected on available ports.")
        return None

    def start(self):
        """Start background communication loop."""
        if not self.serial:
            print("Serial connection not established.")
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
        print("Serial communication stopped.")

    def _comm_loop(self):
        """Main background loop for sending and receiving data."""
        while self.running:
            try:
                self.send_data()
                self.read_data()
                time.sleep(self.refresh_rate)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
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
            print(f"Error sending data: {e}")

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
            print(f"Error reading data: {e}")

# Example usage
if __name__ == "__main__":
    data = Data_Handler(port="COM4", baudrate=115200, refresh_rate=0.2)
    data.start()

    try:
        while True:
            # Example: update data_out with new control values
            # arduino.data_out = [some_value, another_value]
            time.sleep(1)
    except KeyboardInterrupt:
        data.stop()
