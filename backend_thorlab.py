from machinelogic import Machine
from thorlab.thorlab import ThorlabSensor
import time

class RobotController:
    def __init__(self, ip='192.168.5.2'):
        self.machine = Machine(ip)
        self.robot = self.machine.get_robot("ARNOLD")
        self.thorlab = ThorlabSensor()
        self.thorlab.connect()
        self.data = []
        self.well_id = 1
        self.x_leds = 2
        self.y_leds = 4
        self.distance_leds = 9
        self.linear_velocity = 300  # mm/s
        self.linear_acceleration = 500  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit
        self.joint_acceleration = 50  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]
        self.initial_position = [-220.00, 164.00, 780.50, 0.00, 0.00, 0.00]

    def home(self):
        self.robot.movej(self.j_Home, self.joint_velocity, self.joint_acceleration)
        return "Moved to Home Position"

    def calibration(self):
        for x in range(self.x_leds):
            for y in range(self.y_leds):
                self.robot.movej(self.robot.compute_inverse_kinematics([ 
                    self.initial_position[0] - 9*x, # Change +/- according to direction
                    self.initial_position[1] + 9*y, # Change +/- according to direction
                    self.initial_position[2], 
                    self.initial_position[3], 
                    self.initial_position[4], 
                    self.initial_position[5]
                ]), self.joint_velocity, self.joint_acceleration)

                measurement = self.thorlab.measure(num_samples=5)
                measurement = {'well_id': self.well_id, 'x': x+1, 'y': y+1, **measurement}
                self.well_id += 1
                self.data.append(measurement)
        
        return "Calibration Complete"

    def initial_position(self):
        self.robot.movej(self.robot.compute_inverse_kinematics(self.initial_position), self.joint_velocity, self.joint_acceleration)
        return "Initial position reached"
    
    def get_position(self):
        current_position = self.robot.state.cartesian_position
        return current_position
    
    def get_data(self):
        return self.data