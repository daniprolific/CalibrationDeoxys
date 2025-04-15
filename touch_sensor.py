from machinelogic import Machine
from spectrometer.spectrometer_class import Avantes
# from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
from pykachu.src.pykachu.serial.Pikachu import Pikachu
from pykachu.scripts.PikachuJSONBuilder import *
from touch_sensor.touch_sensor_class import TouchSensor
import statistics
import numpy as np

import time

class RobotController:
    def __init__(self):

        self.machine = Machine('192.168.5.2')
        self.robot = self.machine.get_robot("ARNOLD")

        # # SPECTROMETER
        # self.spectrometer = Avantes()
        # self.spectrometer.initialize_device()
        # self.num_measurements = 5
        # self.min_wavelength = 400
        # self.max_wavelength = 540
        # self.integration_time = 20

        # DEOXYS DATA
        self.controller = 'CALI'
        self.access_token ='f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'
        self.sensor_serial = '123459' #MAKE SURE WHAT IS THIS
        self.BLUE_465NM = 465
        self.RED_630NM = 630
        self.IRED_820NM = 820
        self.MAX_INTENSITY = 4095
        self.well_adu = 0
        self.well_id = 1
        self.wavelength = 0
        
        # ROBOT DATA
        self.x_leds = 3
        self.y_leds = 1
        self.distance_leds = 9
        self.linear_velocity = 100.0  # mm/s
        self.linear_acceleration = 50.0  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit 
        self.joint_acceleration = 30  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]
        # self.ini_position = [-331.5, 217.3, 740.4, 0.00, 0.00, 0.00]
        self.ini_position = [-331.5, 225.0, 755.0, 0.00, 0.00, 0.00]
         

        # DATA AIRTABLE
        self.measurements = []
        self.deoxys_info = []

        # TOUCH SENSOR
        self.touch_sensor = TouchSensor('COM8')

    def home(self):
        self.robot.movej(self.j_Home, self.joint_velocity, self.joint_acceleration)
        return "Moved to Home Position"
    
    def SetGroupADU(self, pikachu: Pikachu, group: str, color: int, adu: int):
        plan = IlluminationPlanJSON()
        plan.set_plan_id(1) 
        plan.add_stage(duration=10000)
        plan.add_condition_to_last_stage(groups=[group], color=color, adu=adu)
        pikachu.UploadJSONString(plan.to_json())
        pikachu.StartIllumination()

    
    # def calibration(self):
    #     pikachu = Pikachu("COM7")
    #     pikachu.connect()
    #     pikachu.set_illumination_state(True)

    #     # UPDATA DEOXYS_INFO
    #     # self.deoxys_info.append({'dev_id': dev_id})
    #     self.deoxys_info.append({'sensor_serial': self.sensor_serial})


    #     letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    #     values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
    #     well = {i: values[i] for i in range(len(values))}

    #     self.well_adu = self.MAX_INTENSITY
    #     self.wavelength = self.BLUE_465NM
    #     self.measurements.append({'Wavelength': self.wavelength})

    #     for y in range(self.y_leds):
    #         for x in range(self.x_leds):
    #             wellid = x + 12*y
    #             # self.SetGroupADU(pikachu, well[wellid], self.wavelength, self.well_adu)
    #             # TURN ON PIKACHU
    #             pikachu.set_group_intensity(well[wellid],self.wavelength,self.well_adu)
    #             # MOVE ROBOT
    #             self.robot.movel([ 
    #                 self.ini_position[0] + 9*x, # Change +/- according to direction
    #                 self.ini_position[1] + 9*y, # Change +/- according to direction
    #                 self.ini_position[2], 
    #                 self.ini_position[3], 
    #                 self.ini_position[4], 
    #                 self.ini_position[5]
    #             ] ,self.linear_velocity, self.linear_acceleration)
    #             time.sleep(0.1)

    #             # MEASURE SPECTROMETER
    #             power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,self.min_wavelength, self.max_wavelength)
    #             mean_power = sum(power_list) / len(power_list)
    #             std_dev = statistics.stdev(power_list)

    #             #TURN OFF PIKACHU
    #             # pikachu.StopIllumination()
    #             pikachu.set_group_intensity(well[wellid],self.wavelength,0)

    #             time.sleep(0.1)
               
    #             info = {'WellID': well[wellid],'MaxPD': mean_power, 'SDMaxPD': std_dev, 
    #                     'nMaxPDMeasurements': self.num_measurements}

    #             self.measurements.append(info)

    #     self.spectrometer.disconnect()
    #     print(self.measurements)
    #     return "Calibration Complete"


    def initial_position(self):
        self.robot.movej(self.robot.compute_inverse_kinematics(self.ini_position), self.joint_velocity, self.joint_acceleration)
        return "Initial position reached"
    
    def get_position(self):
        current_position = self.robot.state.cartesian_position
        return current_position
    
    def test_allignment(self, corner):
        # Coordinates of corners
        corners = {'1': [0,0], '2': [11, 0], '3': [0, 7], '4': [11,7]}
        position = str(corner)
        x = corners[position][0]
        y = corners[position][1]

        # MOVE ROBOT
        self.robot.movel(([ 
            self.ini_position[0] + 9*x, # Change +/- according to direction
            self.ini_position[1] + 9*y, # Change +/- according to direction
            self.ini_position[2], 
            self.ini_position[3], 
            self.ini_position[4], 
            self.ini_position[5]
        ]) ,self.linear_velocity, self.linear_acceleration)

        # self.spectrometer.disconnect()
    
    def get_data(self):
        return self.deoxys_info, self.measurements
    
    def get_height(self):
        self.home() #Move to home
        print('START')
        self.touch_sensor.extend()
        detected = self.touch_sensor.get_status()

        for z in range (10):
            self.robot.movel(([ 
                self.ini_position[0],
                self.ini_position[1], 
                self.ini_position[2] - 10 + z, 
                self.ini_position[3], 
                self.ini_position[4], 
                self.ini_position[5]
            ]) ,self.linear_velocity, self.linear_acceleration)

            time.sleep(0.2)
            detected = self.touch_sensor.get_status()
            print('moved z: {}, detected: {}'.format (z,detected))
            time.sleep(0.1)

            if detected == 1:
                print('STOP, object detected')
                break
            else:
                continue

        print('Position',self.get_position())
        height = self.get_position()[2]
        print('Height detected:', height)

        self.robot.movel(([ 
                self.ini_position[0],
                self.ini_position[1], 
                height - 2, 
                self.ini_position[3], 
                self.ini_position[4], 
                self.ini_position[5]
            ]) ,self.linear_velocity, self.linear_acceleration)
        time.sleep(0.1)
        
        self.touch_sensor.extend()
        detected = self.touch_sensor.get_status()
        
        for z in range (1,11):
            self.robot.movel(([ 
                self.ini_position[0],
                self.ini_position[1], 
                height - 2 + z/10, 
                self.ini_position[3], 
                self.ini_position[4], 
                self.ini_position[5]
            ]) ,self.linear_velocity, self.linear_acceleration)

            time.sleep(0.2)
            detected = self.touch_sensor.get_status()
            print('moved z: {}, detected: {}'.format (z,detected))
            time.sleep(0.1)

            if detected == 1:
                print('STOP, object detected')
                break
            else:
                continue
        print('Position',self.get_position())


    
if __name__ == "__main__":
        robot = RobotController()
        # robot.test_allignment(1)
        # robot.get_height()
        robot.home()

       



