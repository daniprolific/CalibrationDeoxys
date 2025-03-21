from PyTLPMX import TLPMX
import time
import numpy as np

class ThorlabSensor:
    def __init__(self):
        """Initialize the Thorlab power meter connection."""
        self.device_name = self.connect()
        self.device = None  # Will be initialized when measuring

    def connect(self):
        """Find and connect to the first available Thorlab power meter."""
        tlPM = TLPMX()
        device_count = tlPM.findRsrc()

        if device_count == 0:
            print("No devices found!")
            return None

        print(f"Devices found: {device_count}")

        # Get the first available device
        resource_name = tlPM.getRsrcName(0)
        print(f"Connected to: {resource_name}")

        tlPM.close()
        return resource_name

    def measure(self, num_samples=20):
        """Take power measurements and return statistical data."""
        if not self.device_name:
            print("Error: No connected device!")
            return None

        # Connect to the power meter
        self.device = TLPMX(self.device_name, True, False)
        print("Taking measurements...")

        # Calibration message
        message = self.device.getCalibrationMsg()
        print(f"Calibration message: {message}")

        time.sleep(1)

        # Collect measurements
        measurements = []
        for _ in range(num_samples):
            power = self.device.measPower() * 1000000
            print(power)
            measurements.append(power)
            time.sleep(0.2)

        # Query device information
        self.device.writeRaw("*IDN?\n")
        raw_value = self.device.readRaw(1024)
        print(raw_value)

        # Compute statistics
        mean_value = np.mean(measurements)
        std_dev = np.std(measurements)
        data_sensor = {
            "Mean(μW)": mean_value,
            "standard_deviation": std_dev,
            "number_of_measurements": len(measurements)
        }

        # Close connection
        self.device.close()
        print("End program")

        return data_sensor
