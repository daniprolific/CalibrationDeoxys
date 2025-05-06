from machinelogic import Machine
from spectrometer.spectrometer_class import Avantes
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
# from pykachu.src.pykachu.serial.Pikachu import Pikachu
from pykachu.scripts.PikachuJSONBuilder import *
from touch_sensor.touch_sensor_class import TouchSensor
import statistics
import numpy as np
from airtable.airtable_class import AirtableCalibrationUploader
import time
import os
from dotenv import load_dotenv


class RobotController:
    def __init__(self):

        # --- ROBOT ---
        self.machine = Machine('192.168.5.2')
        self.robot = self.machine.get_robot("ARNOLD")
        print('robot:',self.robot)

        # --- SPECTROMETER ---
        self.spectrometer = Avantes()
        self.spectrometer.initialize_device()

        # --- PIKACHU CONTROLLER ---
        load_dotenv("C:/Users/madel/Desktop/Calibration/Code/Deoxys calibration/Pikachu.env")
        self.controller = os.getenv("PARTICLE_DEVICE_ID")
        self.access_token = os.getenv("PARTICLE_ACCESS_TOKEN")
        self.pikachu = Pikachu(self.controller, self.access_token)
        print(self.pikachu.IsConnected())

        # --- TOUCH SENSOR ---
        self.touch_sensor = TouchSensor('COM8')

        
        self.BLUE_465NM = 465
        self.RED_630NM = 630
        self.IRED_820NM = 780
        self.MAX_INTENSITY = 4095
 
        # ROBOT DATA
        self.linear_velocity = 50.0  # mm/s
        self.linear_acceleration = 25.0  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit 
        self.joint_acceleration = 30  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]  # joint coordinates
        self.ini_position = [-364.2, 173.4]  
        # self.ini_position = [-347.8, 173.5] #OLD SPEC


        # TOUCH SENSOR
        self.heights = None
        # self.heights = [753.07, 752.56, 753.28]  # FOR TESTING
        self.max_z = 753.0
        self.positions_get_heights = [[-364.0, 104.2], [-265.0, 104.2], [-364.0, 181.0]]

        # DATA AIRTABLE
        self.API_KEY = 'patzZ4bX6yRFRauUE.95471454dcbbd994fa31bf3f9292bb93f64d5b8a6f3113558e17e7873e8e76d4'
        self.BASE_ID = 'appjxfjyEex8LeD0Q'
        self.measurements = []
        self.deoxys_info = []


        # CALIBRATION DATA
        # self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        # self.numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.letters = ['A']
        self.numbers = [1, 2, 3]
        self.color_sequence = [465, 630, 780]
        self.adu_sequence = [4095]
        self.int_time = {'465': {'1024':100, '2048':50, '4095':20}, '630': {'1024':500, '2048':270, '4095':150}, '780': {'1024':800, '2048':700, '4095':600}}


    def home(self):
        self.robot.movej(self.j_Home, self.joint_velocity, self.joint_acceleration)
        return "Moved to Home Position"
    

    def create_ilumination_plan(self, pikachu: Pikachu, well_sequence, color_sequence, adu_sequence):
        '''
        Uploads ilumination plan for Deoxys

        Parameters
        ----------
        - well_sequnce = ["A1", "A2", "A3", ...]
        - color_sequnce = [465, 630, 780]
        - adu_sequence = [4095, 2048, 1024]

        '''
        plan = IlluminationPlanJSON()
        plan.set_plan_id(1)

        # First stage is OFF
        plan.add_stage(0)
        plan.add_condition_to_last_stage(groups=['A1'], color=465, adu=0)

        for well in well_sequence:
            for color in color_sequence:
                for adu in adu_sequence:
                    plan.add_stage(0)
                    plan.add_condition_to_last_stage(groups=[well], color=color, adu=adu)

        pikachu.UploadJSONString(plan.to_json())


    def initial_position(self):
        '''Move robot to hardcoded initial position '''

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
        '''
        Returns
        ---------
        Coordinates [x,y,z,ox,oy,oz]'''

        current_position = self.robot.state.cartesian_position
        return current_position
    
    def get_orientation(self):
        '''
        Returns
        ---------
        Coordinates [x,y]'''

        current_position = self.robot.state.cartesian_position
        orientation = current_position[:2]
        return orientation
    
    def check_corners(self, corner, orientation):
        '''
        Move robot to the selected corner

        Parameters
        ----------
        - corner = ["A1"]
        - orientation = [x,y]
        '''

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
        '''Move robot in X direction
        
        Parameters
        ----------
        - displacement: mm you want to move'''

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
        '''Move robot in Y direction
        
        Parameters
        ----------
        - displacement: mm you want to move'''

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
    
    def get_heights(self):
        """
        Use touch sensor to get the heights of the positions defined in self.positions_get_heights

        Returns 
        ---------
        [h1, h2, h3] list with the heights of the positions
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
                    break
                else:
                    continue

            height = self.get_position()[2]
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
                    break
                else:
                    continue
            final_position = self.get_position()
            self.heights.append(final_position[2] + 1.4)  # CHANGE THIS TO GO LOWER   
        print('heights:',self.heights)

        return "Heights saved"
    
    def estimate_height(self, new_position):
        """
        Estimate the height at a new (x, y) position on a plane defined by 3 known (x, y, z) points.

        Returns
        -----------
        - The estimated height (z value) at the new (x, y)
        """
        positions_estimate_height = [[x, y + 65] for x, y in self.positions_get_heights]  # y + 65 to  get position of spectrometer
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
    
    def create_well_sequence(self, letters, numbers):
        '''Create well sequence from  letters and numbers
        
            well_sequence = ['A1', 'A2', 'A3',...]
        '''
        well_sequence =  [f"{letter}{number}" for letter in letters for number in numbers]
        return well_sequence

    
    def calibration_final_cloud(self, orientation):
        '''Run estandard calibration sequence via cloud'''
        self.measurements = []

        # CONNECT PIKACHU
        # pikachu = Pikachu(self.controller, self.access_token)
        self.pikachu.Mute()
        dev_id = self.pikachu.IlluminatorId()

        # UPDATA DEOXYS_INFO
        self.deoxys_info.append({'DevID': dev_id})

        # CREATE WELL SEQUENCE AND ILUMINATION PLAN
        well_sequence = self.create_well_sequence(self.letters, self.numbers)
        self.pikachu.StopIllumination()
        self.create_ilumination_plan(self.pikachu, well_sequence, self.color_sequence, self.adu_sequence)
        self.pikachu.StartIllumination()

        wellid = 0
        y_value = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
        for y in self.letters:
            for x in self.numbers:

                height = self.estimate_height([orientation[0] + 9*(x-1), orientation[1] + 9*(y_value[y])])
                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*(x-1), 
                    orientation[1] + 9*(y_value[y]), 
                    height, 
                    0.00, 
                    0.00, 
                    0.00
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(0.2)

                for color in self.color_sequence:
                    for adu in self.adu_sequence:
                        
                        self.pikachu.AdvanceIllumination()
                        time.sleep(0.2)

                        # MEASURE SPECTROMETER
                        data = self.spectrometer.measure(self.int_time[str(color)][str(adu)])
                        data = { 'Wavelength': color, 'wellID': well_sequence[wellid], 'adu': adu, **data}
                        self.measurements.append(data)
                
                wellid = wellid + 1


        self.pikachu.StopIllumination()
        return "Calibration Completed"
    
    def calibration_final_serial(self, orientation):
        '''Run estandard calibration sequence via serial'''
        self.measurements = []

        # CONNECT PIKACHU
        pikachu = Pikachu("COM7")
        pikachu.connect()
        pikachu.set_illumination_state(True)

        # UPDATA DEOXYS_INFO
        self.deoxys_info.append({'DevID': "-"})

        # CREATE WELL SEQUENCE
        well_sequence = self.create_well_sequence(self.letters, self.numbers) 

        wellid = 0
        y_value = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
        for y in self.letters:
            for x in self.numbers:

                height = self.estimate_height([orientation[0] + 9*(x-1), orientation[1] + 9*(y_value[y])])
                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*(x-1), 
                    orientation[1] + 9*(y_value[y]), 
                    height, 
                    0.00, 
                    0.00, 
                    0.00
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(0.2)

                for color in self.color_sequence:
                    for adu in self.adu_sequence:
                        #TURN ON DEOXYS
                        pikachu.set_group_intensity(well_sequence[wellid],color,adu)
                        time.sleep(0.2)

                        # MEASURE SPECTROMETER
                        data = self.spectrometer.measure(self.int_time[str(color)][str(adu)])
                        data = { 'Wavelength': color, 'wellID': well_sequence[wellid], 'adu': adu, **data}
                        self.measurements.append(data)
                        time.sleep(0.2)
                        #TURN OFF DEOXYS
                        pikachu.set_group_intensity(well_sequence[wellid],color,0)
                
                wellid = wellid + 1

        return "Calibration Completed"        

    def modified_calibration(self, orientation, letters, numbers, color_sequence, adu_sequence):
        '''Run modified calibration sequence via cloud'''
        self.measurements = []

        # CONNECT PIKACHU
        pikachu = Pikachu(self.controller, self.access_token)
        pikachu.Mute()
        dev_id = pikachu.IlluminatorId()

        # UPDATA DEOXYS_INFO
        self.deoxys_info.append({'DevID': dev_id})

        # CREATE WELL SEQUENCE AND ILUMINATION PLAN
        well_sequence = self.create_well_sequence(letters, numbers)
        pikachu.StopIllumination()
        self.create_ilumination_plan(pikachu, well_sequence, color_sequence, adu_sequence)
        pikachu.StartIllumination()

        wellid = 0
        y_value = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
        for y in letters:
            for x in numbers:

                height = self.estimate_height([orientation[0] + 9*(x-1), 
                                               orientation[1] + 9*(y_value[y])])
                # MOVE ROBOT
                self.robot.movel([ 
                    orientation[0] + 9*(x-1), 
                    orientation[1] + 9*(y_value[y]), 
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
                        data = self.spectrometer.measure(self.int_time[str(color)][str(adu)])
                        print(wellid)
                        data = { 'Wavelength': color, 'wellID': well_sequence[wellid], 'adu': adu, **data}
                        self.measurements.append(data)

                wellid = wellid + 1

        pikachu.StopIllumination()
        return "Calibration Completed"


    def organize_measurements(self, measurements):
        '''
        Organize measurements to upload to Airtable

        Returns
        ---------
        - {'465':[{'Wavelength': 465},{....},{....}], '630':[{'Wavelength': 630},{....},{....}]}
        '''
        organized_measurements = {}

        # First, find all unique wavelengths from measurements
        wavelengths = set(m['Wavelength'] for m in measurements)

        # Initialize the structure
        for wavelength in wavelengths:
            organized_measurements[wavelength] = [{'Wavelength': wavelength}]

        # Fill the structure
        for m in measurements:
            wavelength = m['Wavelength']
            entry = {k: v for k, v in m.items() if k != 'Wavelength'}
            organized_measurements[wavelength].append(entry)
        
        return organized_measurements        

    
    def get_data(self):
        return self.deoxys_info, self.measurements
    
    def upload_airtable(self, deoxys_info, organized_measurements):
        '''Upload data to Airtable'''
        uploader = AirtableCalibrationUploader(
        api_key=self.API_KEY,
        base_id=self.BASE_ID,
        )

        uploader.upload_info(deoxys_info)

        # UPLOAD EACH COLOR IN SEQUENCE
        for color in self.color_sequence:
            result = uploader.upload_measurements(organized_measurements[color])

            if result:
                print("Data uploaded successfully!")
            else:
                print("Upload failed")



    