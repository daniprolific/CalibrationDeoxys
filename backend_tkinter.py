from machinelogic import Machine
from spectrometer.spectrometer_class import Avantes
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
# from pykachu.src.pykachu.serial.Pikachu import Pikachu
from pykachu.scripts.PikachuJSONBuilder import *
from touch_sensor.touch_sensor_class import TouchSensor
import statistics
import numpy as np

import time

class RobotController:
    def __init__(self):

        self.machine = Machine('192.168.5.2')
        self.robot = self.machine.get_robot("ARNOLD")

        # SPECTROMETER
        self.spectrometer = Avantes()
        self.spectrometer.initialize_device()
        self.num_measurements = 5
        self.min_wavelength = 400
        self.max_wavelength = 540
        self.integration_time = 20

        # DEOXYS DATA
        self.controller = 'CALI'
        self.access_token ='f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'
        self.sensor_serial = '123459' #MAKE SURE WHAT IS THIS
        self.BLUE_465NM = 465
        self.RED_630NM = 630
        self.IRED_820NM = 780
        self.MAX_INTENSITY = 4095
        self.well_adu = 0
        self.well_id = 1
        self.wavelength = 0
        
        # ROBOT DATA
        self.x_leds = 3
        self.y_leds = 1
        self.distance_leds = 9
        self.linear_velocity = 50.0  # mm/s
        self.linear_acceleration = 25.0  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit 
        self.joint_acceleration = 30  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]  # joint coordinates
        self.ini_position = [-364.2, 173.4]  
        # self.ini_position = [-347.8, 173.5] #OLD SPEC


        # TOUCH SENSOR
        self.touch_sensor = TouchSensor('COM8')

        # self.heights = None
        self.heights = [753.07, 752.56, 753.28]
        self.max_z = 753.0
        self.positions_get_heights = [[-364.0, 104.2], [-265.0, 104.2], [-364.0, 181.0]]

        # DATA AIRTABLE
        self.measurements = []
        self.deoxys_info = []

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

    
    def CreateIluminationPlan(self, pikachu: Pikachu, well_sequence, color_sequence, adu_sequence):
        plan = IlluminationPlanJSON()
        plan.set_plan_id(1)

        # First stage is OFF
        plan.add_stage(0)
        plan.add_condition_to_last_stage(groups=['A1'], color=465, adu=0)

        for y in range(self.y_leds):
            for x in range(self.x_leds):

                wellid = x + 12*y

                for color in color_sequence:
                    for adu in adu_sequence:
                    
                        plan.add_stage(0)
                        plan.add_condition_to_last_stage(groups=[well_sequence[wellid]], color=color, adu=adu)
                    
        pikachu.UploadJSONString(plan.to_json())

    def initial_position(self):

        height = self.estimate_height([self.ini_position[0], self.ini_position[1]])

        self.robot.movel(([ 
            self.ini_position[0], # Change +/- according to direction
            self.ini_position[1], # Change +/- according to direction
            height, 
            0.00, 
            0.00, 
            0.00
        ]) ,self.linear_velocity, self.linear_acceleration)
        return "Initial position reached"
    
    def get_position(self):
        current_position = self.robot.state.cartesian_position
        return current_position
    
    def get_orientation(self):
        current_position = self.robot.state.cartesian_position
        orientation = current_position[:2]
        return orientation
    
    def check_corners(self, corner, orientation):
        # Coordinates of corners
        corners = {'A1': [0,0], 'A12': [11, 0], 'H1': [0, 7], 'H12': [11,7]}
        position = str(corner)
        x = corners[position][0]
        y = corners[position][1]
        height = self.estimate_height([orientation[0] + 9*x, orientation[1] + 9*y])

        # MOVE ROBOT
        self.robot.movel(([ 
            orientation[0] + 9*x, # Change +/- according to direction
            orientation[1] + 9*y, # Change +/- according to direction
            height, 
            0.00, 
            0.00, 
            0.00
        ]) ,self.linear_velocity, self.linear_acceleration)

        return 'Corner {} reached'.format(corner)
    
    
    def move_robot_x(self, displacement):
        actual_position = self.get_position()
        self.robot.movel(([ 
            actual_position[0] + displacement,
            actual_position[1], 
            actual_position[2],
            0.00, 
            0.00, 
            0.00
            ]) ,self.linear_velocity, self.linear_acceleration)
        return "Robot moved {}mm in x".format(displacement)
    
    def move_robot_y(self, displacement):
        actual_position = self.get_position()
        self.robot.movel(([ 
            actual_position[0],
            actual_position[1] + displacement, 
            actual_position[2],
            0.00, 
            0.00, 
            0.00
            ]) ,self.linear_velocity, self.linear_acceleration)
        return "Robot moved {}mm in y".format(displacement)
    
    # def calibration(self, orientation, height):
    #     self.measurements = []

    #     # CONNECT PIKACHU
    #     pikachu = Pikachu("COM7")
    #     pikachu.connect()
    #     pikachu.set_illumination_state(True)

    #     # CREATE WELL SEQUENCE
    #     letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    #     values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
    #     well = {i: values[i] for i in range(len(values))}   

    #     self.well_adu = self.MAX_INTENSITY
    #     self.wavelength = self.BLUE_465NM
    #     # self.measurements.append({'Wavelength': self.wavelength})

    #     for y in range(self.y_leds):
    #         for x in range(self.x_leds):
    #             wellid = x + 12*y

    #             # TURN ON PIKACHU
    #             pikachu.set_group_intensity(well[wellid],self.wavelength,self.well_adu)

    #             # MOVE ROBOT
    #             self.robot.movel([ 
    #                 orientation[0] + 9*x, 
    #                 orientation[1] + 9*y, 
    #                 height, 
    #                 0.00, 
    #                 0.00, 
    #                 0.00
    #             ] ,self.linear_velocity, self.linear_acceleration)
    #             time.sleep(1)

    #             # MEASURE SPECTROMETER
    #             power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,433, 491)
    #             mean_power = sum(power_list) / len(power_list)
    #             std_dev = statistics.stdev(power_list)

    #             time.sleep(0.3)

    #             #TURN OFF PIKACHU
    #             pikachu.set_group_intensity(well[wellid],self.wavelength,0)

                
               
    #             info = {'WellID': well[wellid],'MaxPD': mean_power, 'SDMaxPD': std_dev, 'nMaxPDMeasurements': self.num_measurements}

    #             self.measurements.append(info)

    #             time.sleep(0.3)
    #     print(self.measurements)
    #     return "Calibration Completed"
    
    def get_heights(self):
        """
        max_z: Maximum height the robot can go (to avoid collision if the touch sensor fails)

        Returns: [h1, h2, ...] list with the heights of the positions
        """
        self.heights = []
   
        for pos in self.positions_get_heights:

            self.home() 
            self.touch_sensor.extend()
            detected = self.touch_sensor.get_status()

            for z in range (11):
                self.robot.movel(([ 
                    pos[0],
                    pos[1], 
                    self.max_z - 10 + z, 
                    0.0, 
                    0.0, 
                    0.0
                ]) ,self.linear_velocity, self.linear_acceleration)

                time.sleep(0.4)
                detected = self.touch_sensor.get_status()

                if detected == 1:
                    print('STOP, object detected')
                    break
                else:
                    continue

            print('Position',self.get_position())
            height = self.get_position()[2]
            print('Height detected:', height)

            self.robot.movel(([ 
                    pos[0],
                    pos[1], 
                    height - 2, 
                    0.0, 
                    0.0, 
                    0.0
                ]) ,self.linear_velocity, self.linear_acceleration)
            time.sleep(1)
            
            self.touch_sensor.extend()
            detected = self.touch_sensor.get_status()
            
            for z in np.arange(0, 2.1, 0.1):  # 2.1 to include 2.0
                self.robot.movel(([ 
                    pos[0],
                    pos[1], 
                    height - 1.5 + z, 
                    0.0, 
                    0.0, 
                    0.0
                ]) ,self.linear_velocity, self.linear_acceleration)

                time.sleep(0.4)
                detected = self.touch_sensor.get_status()

                if detected == 1:
                    print('STOP, object detected')
                    break
                else:
                    continue
            final_position = self.get_position()
            self.heights.append(final_position[2] + 1.2)  # CHANGE THIS TO GO LOWER
        print('heights:',self.heights)

        return "Heights saved"
    
    def estimate_height(self, new_position):
        """
        Estimate the height at a new (x, y) position on a plane defined by 3 known (x, y, z) points.

        Parameters:
        - xy_coords: List of 3 (x, y) coordinates (e.g., [[x1, y1], [x2, y2], [x3, y3]])
        - heights: List of 3 z (height) values corresponding to each coordinate
        - new_xy: [x, y] representing the new point to evaluate

        Returns:
        - The estimated height (z value) at the new (x, y)
        """
        positions_estimate_height = [[x, y + 70.3] for x, y in self.positions_get_heights]
        # Create matrix A and vector b to solve Ax = h
        A = np.array([[x, y, 1] for x, y in positions_estimate_height])
        h = np.array(self.heights)

        # Solve for plane coefficients a, b, c
        coeffs = np.linalg.solve(A, h)
        a, b, c = coeffs

        # Compute height at new (x, y)
        x_new, y_new = new_position
        z_new = a * x_new + b * y_new + c
        return z_new
    
    def calibration_new(self, orientation):
        self.measurements = []

        # CONNECT PIKACHU
        pikachu = Pikachu("COM7")
        pikachu.connect()
        pikachu.set_illumination_state(True)

        # CREATE WELL SEQUENCE
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
        well = {i: values[i] for i in range(len(values))}   

        self.well_adu = self.MAX_INTENSITY
        self.wavelength = self.BLUE_465NM
        # self.measurements.append({'Wavelength': self.wavelength})

        for y in range(self.y_leds):
            for x in range(self.x_leds):

                wellid = x + 12*y
                height = self.estimate_height([orientation[0] + 9*x, orientation[1] + 9*y])

                # TURN ON PIKACHU
                pikachu.set_group_intensity(well[wellid],self.wavelength,self.well_adu)

                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*x, 
                    orientation[1] + 9*y, 
                    height, 
                    0.00, 
                    0.00, 
                    0.00
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(1)

                # MEASURE SPECTROMETER
                power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,433, 491)
                mean_power = sum(power_list) / len(power_list)
                std_dev = statistics.stdev(power_list)

                time.sleep(0.3)

                #TURN OFF PIKACHU
                pikachu.set_group_intensity(well[wellid],self.wavelength,0)
                
               
                info = {'WellID': well[wellid],'MaxPD': mean_power, 'SDMaxPD': std_dev, 'nMaxPDMeasurements': self.num_measurements}

                self.measurements.append(info)

                time.sleep(0.3)
        print(self.measurements)
        return "Calibration Completed"
    
    def calibration_final_serial(self, orientation):
        self.measurements = []

        # CONNECT PIKACHU
        pikachu = Pikachu("COM7")
        pikachu.connect()
        pikachu.set_illumination_state(True)

        # CREATE WELL SEQUENCE
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
        well = {i: values[i] for i in range(len(values))}   

        wavelength_sequence = [465, 630]
        adu_sequence = [4095]
        int_time = {'465': {'1024':100, '2048':50, '4095':20}, '630': {'1024':500, '2048':270, '4095':150}, '780': {'1024':500, '2048':270, '4095':150}}

        for y in range(self.y_leds):
            for x in range(self.x_leds):

                wellid = x + 12*y
                height = self.estimate_height([orientation[0] + 9*x, orientation[1] + 9*y])

                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*x, 
                    orientation[1] + 9*y, 
                    height, 
                    0.00, 
                    0.00, 
                    0.00
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(0.2)

                for wavelength in wavelength_sequence:
                    for adu in adu_sequence:

                        # TURN ON PIKACHU
                        pikachu.set_group_intensity(well[wellid],wavelength,adu)
                        time.sleep(0.1)

                        # MEASURE SPECTROMETER
                        data = self.spectrometer.measure(int_time[str(wavelength)][str(adu)])
                        data = {'WellID': well[wellid], **data}

                        time.sleep(0.5)

                        #TURN OFF PIKACHU
                        pikachu.set_group_intensity(well[wellid],wavelength,0)

                        self.measurements.append(data)

        print(self.measurements)
        return "Calibration Completed"        

    def calibration_final_cloud(self, orientation):
        self.measurements = []

        # CONNECT PIKACHU
        pikachu = Pikachu(self.controller, self.access_token)

        # CREATE WELL SEQUENCE
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]

        well_sequence = {i: values[i] for i in range(len(values))}   
        color_sequence = [465, 630]
        adu_sequence = [4095]

        int_time = {'465': {'1024':100, '2048':50, '4095':20}, '630': {'1024':500, '2048':270, '4095':150}, '780': {'1024':500, '2048':270, '4095':150}}

        self.CreateIluminationPlan(pikachu, well_sequence, color_sequence, adu_sequence)
        pikachu.StartIllumination()

        for y in range(self.y_leds):
            for x in range(self.x_leds):

                wellid = x + 12*y
                height = self.estimate_height([orientation[0] + 9*x, orientation[1] + 9*y])

                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*x, 
                    orientation[1] + 9*y, 
                    height, 
                    0.00, 
                    0.00, 
                    0.00
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(0.2)

                for color in color_sequence:
                    for adu in adu_sequence:
                        pikachu.AdvanceIllumination()
                        time.sleep(0.2)

                        # MEASURE SPECTROMETER
                        data = self.spectrometer.measure(int_time[str(color)][str(adu)])
                        data = {'WellID': well_sequence[wellid], **data}
                        self.measurements.append(data)

        print(self.measurements)
        pikachu.StopIllumination()
        return "Calibration Completed"        

    
    def get_data(self):
        return self.deoxys_info, self.measurements

    