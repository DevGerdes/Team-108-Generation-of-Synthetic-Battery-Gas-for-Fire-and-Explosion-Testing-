import time
import threading
import math

class MFC_Simulator:
    """
    A time-variant process simulator with PID-like dynamics.
    
    Attributes:
        Kp, Ki, Kd: PID gains
        setpoint: target value
        value: current process variable (response)
        update_rate: simulation time step in seconds
    """
    def __init__(self, Kp=1.0, Ki=0.1, Kd=0.05, update_rate=0.05):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.update_rate = update_rate

        self.setpoint = 0.0
        self.value = 0.0
        self._integral = 0.0
        self._prev_error = 0.0
        self._running = True

        # Thread for continuous simulation
        self._thread = threading.Thread(target=self._run_simulation, daemon=True)
        self._thread.start()

    def _run_simulation(self):
        """Continuously update the simulated process variable based on PID response."""
        while self._running:
            error = self.setpoint - self.value
            self._integral += error * self.update_rate
            derivative = (error - self._prev_error) / self.update_rate

            # PID output
            control = self.Kp * error + self.Ki * self._integral + self.Kd * derivative

            # Simulate the response (simple dynamic system)
            # The response rate is smoothed to prevent instantaneous jumps
            self.value += control * self.update_rate
            self._prev_error = error

            # Add small natural noise or damping to feel more "realistic"
            self.value += (math.sin(time.time() * 2) * 0.001)

            time.sleep(self.update_rate)

    def set_setpoint(self, new_setpoint):
        """Change the target setpoint."""
        self.setpoint = new_setpoint

    def get_value(self):
        """Return the current simulated process value."""
        return self.value

    def stop(self):
        """Stop the background simulation thread."""
        self._running = False
        self._thread.join(timeout=1.0)

# Example usage:
if __name__ == "__main__":
    mfc = MFC_Simulator(Kp=0.8, Ki=0.2, Kd=0.05)
    mfc.set_setpoint(10)

    for _ in range(50):
        print(f"Setpoint: {mfc.setpoint:.2f}, Response: {mfc.get_value():.2f}")
        time.sleep(0.1)

    mfc.stop()
