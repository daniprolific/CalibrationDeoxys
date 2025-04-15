import serial
import threading
import time

class TouchSensor:
    def __init__(self, port='COM8'):
        """Initialize connection to Arduino touch sensor"""
        self.serial = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)  # Allow Arduino to initialize
        self.running = True
        self.touch_detected = 0
        
        # Start background listener thread
        self.listener_thread = threading.Thread(target=self._listen_to_arduino)
        self.listener_thread.start()

    def _listen_to_arduino(self):
        """Background thread listening for Arduino messages"""
        while self.running:
            if self.serial.in_waiting:
                line = self.serial.readline().decode().strip()
                if line.startswith("TouchDetected: "):
                    self.touch_detected = int(line.split(": ")[1])

    def extend(self):
        """Extend the sensor tip and reset detection"""
        self.serial.write(b'1\n')
        self.touch_detected = 0

    def retract(self):
        """Retract the sensor tip"""
        self.serial.write(b'2\n')

    def get_status(self):
        """Get current touch status (1 = detected, 0 = not detected)"""
        self.serial.write(b't\n')  # Request status update
        return self.touch_detected

    def close(self):
        """Cleanly close connection"""
        self.running = False
        self.listener_thread.join()
        self.serial.close()
        print("Disconnected from Arduino")


# Example usage:
if __name__ == "__main__":
    sensor = TouchSensor('COM8')
    
    try:
        while True:
            cmd = input("Command (E=extend, R=retract, S=status, Q=quit): ").upper()
            
            if cmd == 'E':
                sensor.extend()
                print("Tip extended")
            elif cmd == 'R':
                sensor.retract()
                print("Tip retracted")
            elif cmd == 'S':
                print(f"Touch status: {sensor.get_status()}")
            elif cmd == 'Q':
                break
            else:
                print("Invalid command. Use E/R/S/Q")
                
    finally:
        sensor.close()
