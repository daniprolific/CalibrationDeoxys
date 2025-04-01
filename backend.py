from machinelogic import Machine
from spectrometer.spectrometer_class import Avantes
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
from pykachu.scripts.PikachuJSONBuilder import *
import statistics

import time

class RobotController:
    def __init__(self):

        self.machine = Machine('192.168.5.2')
        self.robot = self.machine.get_robot("ARNOLD")

        # SPECTROMETER
        self.spectrometer = Avantes()
        self.spectrometer.initialize_device()
        self.num_measurements = 5
        self.min_wavelength = 300
        self.max_wavelength = 800
        self.integration_time = 30

        # DEOXYS DATA
        self.name_device = 'D0U2_old'
        self.access_token ='f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'
        self.BLUE_465NM = 465
        self.RED_630NM = 630
        self.IRED_820NM = 820
        self.MAX_INTENSITY = 4095
        self.well_adu = 0
        self.well_id = 1
        
        # ROBOT DATA
        self.x_leds = 1
        self.y_leds = 2
        self.distance_leds = 9
        self.linear_velocity = 300  # mm/s
        self.linear_acceleration = 500  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit 
        self.joint_acceleration = 30  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]
        self.ini_position = [-245.50, 217.5, 752.50, 0.00, 0.00, 0.00]

        self.data = []

    def home(self):
        self.robot.movej(self.j_Home, self.joint_velocity, self.joint_acceleration)
        return "Moved to Home Position"
    
    def SetGroupADU(self, pikachu: Pikachu, group: str, color: int, adu: int):
        plan = IlluminationPlanJSON()
        plan.set_plan_id(2) # Do not care about plan id
        plan.add_stage(duration=10000)
        plan.add_condition_to_last_stage(groups=[group], color=color, adu=adu)
        pikachu.UploadJSONString(plan.to_json())
        pikachu.StartIllumination()

    def calibration(self):
        pikachu = Pikachu(self.name_device, self.access_token)
        pikachu.Mute()

        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] 
        numbers = list(range(12, 0, -1))  # [12, 11, ..., 1]
        well = {i + 1: f"{letters[i % 8]}{numbers[i // 8]}" for i in range(96)}
        

        for x in range(self.x_leds):
            for y in range(self.y_leds):

                self.well_adu = self.MAX_INTENSITY
                self.SetGroupADU(pikachu, well[self.well_id], self.BLUE_465NM, self.well_adu)
                # MOVE ROBOT
                self.robot.movej(self.robot.compute_inverse_kinematics([ 
                    self.ini_position[0] - 9*x, # Change +/- according to direction
                    self.ini_position[1] + 9*y, # Change +/- according to direction
                    self.ini_position[2], 
                    self.ini_position[3], 
                    self.ini_position[4], 
                    self.ini_position[5]
                ]) ,self.joint_velocity, self.joint_acceleration)
                time.sleep(0.5)

                # MEASURE SPECTROMETER
                power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,self.min_wavelength, self.max_wavelength)
                mean_power = sum(power_list) / len(power_list)
                std_dev = statistics.stdev(power_list)

                pikachu.StopIllumination()

                time.sleep(0.1)
               
                info = {'Well ID': self.well_id, 'Well': well[self.well_id], 'Well ADU': self.well_adu, 'Power (µW/(cm²)': mean_power, 'Standard deviation': std_dev, 
                        'Number measurements': self.num_measurements, 'Integration time': self.integration_time, 'Min wavelength':self.min_wavelength, 'Max wavelength':self.max_wavelength}
                self.well_id += 1
                self.data.append(info)

        self.spectrometer.disconnect()
        
        return "Calibration Complete"

    def initial_position(self):
        self.robot.movej(self.robot.compute_inverse_kinematics(self.ini_position), self.joint_velocity, self.joint_acceleration)
        return "Initial position reached"
    
    def get_position(self):
        current_position = self.robot.state.cartesian_position
        return current_position
    
    def get_data(self):
        return self.data
    