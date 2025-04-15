import serial
import threading
import time

# Update with your actual port
arduino = serial.Serial('COM8', 9600, timeout=1)
time.sleep(2)  # Give Arduino time to reset

running = True
touch_detected = 0  # Shared variable reflecting Arduino's touchDetected state

# This function runs in a separate thread to listen to Arduino messages
def listen_to_arduino():
    global running, touch_detected
    while running:
        if arduino.in_waiting:
            line = arduino.readline().decode().strip()
            if line:
                # Detect if touch is triggered
                if "TouchDetected: 1" in line:
                    touch_detected = 1
                else:
                    print(f"Arduino says: {line}")

# Start the listening thread
listener_thread = threading.Thread(target=listen_to_arduino)
listener_thread.start()

# Main loop to send commands
try:
    while running:

        cmd = input("Enter command (1 = extend, 2 = retract, 0 = exit): ").strip()
        if cmd in ['0', '1', '2']:
            arduino.write((cmd + "\n").encode())

            if cmd == '1':
                touch_detected = 0  # 👈 Reset touch state in Python as well
            elif cmd == '0':
                running = False
        else:
            print("⚠️ Invalid input. Use 0, 1, or 2.")

        # 👀 You can now use this variable anywhere you want
        print(f"[Status] touch_detected = {touch_detected}")



except KeyboardInterrupt:
    running = False

# Cleanup
listener_thread.join()
arduino.close()
print("Program stopped.")
