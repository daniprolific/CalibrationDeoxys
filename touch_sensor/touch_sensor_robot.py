import serial
import threading
import time

arduino = serial.Serial('COM8', 9600, timeout=1)
time.sleep(2)  # Allow Arduino to reset

running = True
touch_detected = 0  # Shared variable for touch status

def listen_to_arduino():
    global running, touch_detected
    while running:
        if arduino.in_waiting:
            line = arduino.readline().decode().strip()
            if line:
                if line.startswith("TouchDetected: "):
                    touch_detected = int(line.split(": ")[1])
                else:
                    print(f"Arduino says: {line}")

listener_thread = threading.Thread(target=listen_to_arduino)
listener_thread.start()

try:
    while running:
        cmd = input("Enter command (1=extend, 2=retract, t=status, 0=exit): ").strip().lower()
        
        if cmd in ['0', '1', '2', 't']:
            arduino.write((cmd + "\n").encode())
            
            if cmd == '1':
                touch_detected = 0  # Reset on extend
            elif cmd == '0':
                running = False
            elif cmd == 't':
                print(touch_detected)
        else:
            print("⚠️ Invalid input. Use 0, 1, 2, or t.")
        

except KeyboardInterrupt:
    running = False

listener_thread.join()
arduino.close()
print("Program stopped.")