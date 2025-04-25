import tkinter as tk
from tkinter import messagebox, ttk
from backend_tkinter import RobotController
import os
import csv
from datetime import datetime


# GUI class
class RobotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibration Deoxys Interface")
        self.robot = RobotController()
        self.orientation = None

        # Create main frame with padding
        main_frame = ttk.Frame(root, padding=30)
        main_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=("Arial", 14, "bold"))

        # Use a grid layout to simulate columns
        for i in range(5):  # adjust for 5 columns
            main_frame.columnconfigure(i, weight=1, pad=20)

        # ----------------- Column 1: Home Position -----------------
        col1 = ttk.LabelFrame(main_frame, text="🏠 Home Position", padding=10, style="Bold.TLabelframe")
        col1.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        ttk.Button(col1, text="Go home position", width=20, command=self.go_home).pack(pady=10)

        # ----------------- Column 2: Check Height -----------------
        col2 = ttk.LabelFrame(main_frame, text="📏 Check Height", padding=10, style="Bold.TLabelframe")
        col2.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        ttk.Button(col2, text="Get height", width=20, command=self.get_height).pack(pady=10)

        # ----------------- Column 3: Define Orientation -----------------
        col3 = ttk.LabelFrame(main_frame, text="🧭 Define Orientation", padding=10, style="Bold.TLabelframe")
        col3.grid(row=0, column=2, padx=15, pady=10, sticky="nsew")

        ttk.Button(col3, text="Go to initial position", width=25, command=self.go_initial_position).pack(pady=10)

        ttk.Label(col3, text="Move in X", font=("Arial", 12, "bold")).pack(pady=(15, 5))

        self.x_distance_var = tk.StringVar()
        x_distance_dropdown = ttk.Combobox(col3, textvariable=self.x_distance_var, state="readonly", width=15)
        x_distance_dropdown['values'] = ["5 mm", "1 mm", "0.1 mm"]
        x_distance_dropdown.pack()

        x_button_frame = ttk.Frame(col3)
        x_button_frame.pack(pady=5)
        ttk.Button(x_button_frame, text="↑", width=5, command=self.move_x_positive).pack(side="left", padx=5)
        ttk.Button(x_button_frame, text="↓", width=5, command=self.move_x_negative).pack(side="left", padx=5)

        ttk.Label(col3, text="Move in Y", font=("Arial", 12, "bold")).pack(pady=(15, 5))

        self.y_distance_var = tk.StringVar()
        y_distance_dropdown = ttk.Combobox(col3, textvariable=self.y_distance_var, state="readonly", width=15)
        y_distance_dropdown['values'] = ["5 mm", "1 mm", "0.1 mm"]
        y_distance_dropdown.pack()

        y_button_frame = ttk.Frame(col3)
        y_button_frame.pack(pady=5)
        ttk.Button(y_button_frame, text="←", width=5, command=self.move_y_negative).pack(side="left", padx=5)
        ttk.Button(y_button_frame, text="→", width=5, command=self.move_y_positive).pack(side="left", padx=5)

        ttk.Button(col3, text="Save initial position", width=25, command=self.save_initial_position).pack(pady=(15, 5))

        # ----------------- Column 4: Check Corners -----------------
        col4 = ttk.LabelFrame(main_frame, text="📍 Check Corners", padding=10, style="Bold.TLabelframe")
        col4.grid(row=0, column=3, padx=15, pady=10, sticky="nsew")

        ttk.Label(col4, text="Select Corner:", font=("Arial", 11)).pack(pady=(5, 0))
        self.corner = tk.StringVar(value="A1")
        ttk.Combobox(col4, textvariable=self.corner, values=["A1", "A12", "H1", "H12"], state="readonly", width=15).pack()
        ttk.Button(col4, text="Go to corner", width=20, command=self.go_to_corner).pack(pady=10)

        # ----------------- Column 5: Calibration -----------------
        col5 = ttk.LabelFrame(main_frame, text="🧪 Calibration", padding=10, style="Bold.TLabelframe")
        col5.grid(row=0, column=4, padx=15, pady=10, sticky="nsew")

        ttk.Label(col5, text="Operator name:", font=("Arial", 11)).pack(pady=(5, 0))
        self.operator_name = tk.StringVar()
        ttk.Entry(col5, textvariable=self.operator_name, width=22).pack()

        ttk.Button(col5, text="Run calibration", width=22, command=self.run_calibration_sequence).pack(pady=10)
        ttk.Button(col5, text="Plot results calibration", width=22, command=self.plot_calibration_results).pack(pady=5)






    def go_home(self):
        message = self.robot.home()
        messagebox.showinfo("Home", message)

    def get_height(self):
        message = self.robot.get_heights()
        messagebox.showinfo("Get heights", message)


    def go_to_corner(self):
        corner_id = self.corner.get()
        
        if self.orientation is None or len(self.robot.heights)!= 3:
            messagebox.showwarning("Missing Data", "Height and Initial position needed")
            return

        result = self.robot.check_corners(corner_id, self.orientation)
        messagebox.showinfo("Corner Check", result)

    def go_initial_position(self):
        if self.robot.heights is None:
            messagebox.showwarning("Height required", "You must get the height before going to initial position.")
            return
        result = self.robot.initial_position()
        messagebox.showinfo("Initial Position", result)

    def get_selected_distance(self):
        selected = self.x_distance_var.get()
        if selected == "5 mm":
            return 5
        elif selected == "1 mm":
            return 1
        elif selected == "0.1 mm":
            return 0.1
        else:
            return None

    def move_x_positive(self):
        distance = self.get_selected_distance()
        if distance is None:
            messagebox.showwarning("Missing selection", "Please select distance to move.")
            return
        result = self.robot.move_robot_x(distance)
        messagebox.showinfo("Moved", result)

    def move_x_negative(self):
        distance = self.get_selected_distance()
        if distance is None:
            messagebox.showwarning("Missing selection", "Please select distance to move.")
            return
        result = self.robot.move_robot_x(-distance)
        messagebox.showinfo("Moved", result)

    def get_selected_distance_y(self):
        selected = self.y_distance_var.get()
        if selected == "5 mm":
            return 5
        elif selected == "1 mm":
            return 1
        elif selected == "0.1 mm":
            return 0.1
        else:
            return None

    def move_y_positive(self):
        distance = self.get_selected_distance_y()
        if distance is None:
            messagebox.showwarning("Missing selection", "Please select distance to move.")
            return
        result = self.robot.move_robot_y(+distance)
        messagebox.showinfo("Moved", result)

    def move_y_negative(self):
        distance = self.get_selected_distance_y()
        if distance is None:
            messagebox.showwarning("Missing selection", "Please select distance to move.")
            return
        result = self.robot.move_robot_y(-distance)
        messagebox.showinfo("Moved", result)

    def save_initial_position(self):
        self.orientation = self.robot.get_orientation()
        messagebox.showinfo("Saved", "Initial orientation has been saved.")

    def run_calibration_sequence(self):
        name = self.operator_name.get()
        if not name:
            messagebox.showwarning("Warning", "Please introduce Operator name")
            return
        if self.orientation is None or len(self.robot.heights)!= 3:
            messagebox.showwarning("Warning", "Height and Initial position needed")
            return
        message = self.robot.calibration_final_cloud(self.orientation)
        self.robot.home()
        messagebox.showwarning("Calibration", message)

    def plot_calibration_results(self):
        deoxys_info, measurements = self.robot.get_data()
        
        if not measurements:
            messagebox.showwarning("No Data", "Please run calibration to plot the data")
            return

        # Create a new window using the root, not self
        table_window = tk.Toplevel(self.root)
        table_window.title("Calibration Results")

        # Table headings
        ttk.Label(table_window, text="WellID", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5)
        ttk.Label(table_window, text="MaxPD", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, pady=5)

        # Fill table with data
        for i, entry in enumerate(measurements):
            ttk.Label(table_window, text=entry['WellID']).grid(row=i+1, column=0, padx=10, pady=2)
            ttk.Label(table_window, text=str(entry['MaxPD'])).grid(row=i+1, column=1, padx=10, pady=2)

        # Save measurements to CSV
        save_dir = r"C:\Users\madel\Desktop\Calibration\Calibration_measurements"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"calibration_results_{timestamp}.csv"
        filepath = os.path.join(save_dir, filename)

        try:
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["WellID", "MaxPD"])
                for entry in measurements:
                    writer.writerow([entry['WellID'], entry['MaxPD']])
            print(f"Calibration results saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save CSV: {e}")



# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotGUI(root)
    root.mainloop()
