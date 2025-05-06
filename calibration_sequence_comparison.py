from machinelogic import Machine
from spectrometer.spectrometer_class import Avantes
# from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
from pykachu.src.pykachu.serial.Pikachu import Pikachu
from pykachu.scripts.PikachuJSONBuilder import *
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
        self.IRED_780NM = 780
        self.MAX_INTENSITY = 4095
        self.well_adu = 0
        self.well_id = 1
        self.wavelength = 0
        
        # ROBOT DATA
        self.x_leds = 1
        self.y_leds = 1
        self.distance_leds = 9
        self.linear_velocity = 100.0  # mm/s
        self.linear_acceleration = 50.0  # mm/s²
        self.joint_velocity = self.robot.configuration.joint_velocity_limit 
        self.joint_acceleration = 30  # deg/s²
        self.j_Home = [-180.0, -175.0, 125, 140, -90, 90]
        # self.ini_position = [-364.0, 173.2, 753.5, 0.00, 0.00, 0.00] 
        self.ini_position = [-364.2, 173.4, 753.3, 0.00, 0.00, 0.00]  #-364.2, 173.4

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

    def calibration_multiple_colors_cloud(self):
        pikachu = Pikachu(self.controller, self.access_token)
        pikachu.Mute()
        dev_id = pikachu.IlluminatorId()

        # UPDATA DEOXYS_INFO
        self.deoxys_info.append({'dev_id': dev_id})
        self.deoxys_info.append({'sensor_serial': self.sensor_serial})

        # WELL SEQUENCE
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
        well = {i: values[i] for i in range(len(values))}  #A1, A2, A3 ...

        # WAVELENGTH SEQUENCE
        # wavelength_sequence = [465, 630, 820]
        # adu_sequence = [1024, 2048, 4095]
        # integration_time_sequence = {'465': [100,50,20], '630': [500,270,150], '820': [80,80,80]}  # RUN EXPERIMENTS
        # integration_range = {'465': [400, 540], '630': [560, 700], '820': [700, 900]}
        wavelength_sequence = [465, 630]
        adu_sequence = [1024, 2048, 4095]
        integration_time_sequence = {'465': [100,50,20], '630': [500,270,150]}  # RUN EXPERIMENTS
        integration_range = {'465': [400, 540], '630': [560, 700]}

        self.well_adu = self.MAX_INTENSITY
        self.wavelength = self.RED_630NM
        self.integration_time = 18  # DEPENDS ON COLOR AND WAVELENGTH

        for x in range(self.x_leds):
            for y in range(self.y_leds):
                wellid = x + 12*y
                # MOVE ROBOT
                self.robot.movel([ 
                self.ini_position[0] + 9*x, # Change +/- according to direction
                self.ini_position[1] + 9*y, # Change +/- according to direction
                self.ini_position[2], 
                self.ini_position[3], 
                self.ini_position[4], 
                self.ini_position[5]
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(0.1)

                # DarkData = self.spectrometer.count_distribution(100)

                for color in wavelength_sequence:
                    for adu in adu_sequence:
                        self.SetGroupADU(pikachu, well[wellid], color, adu)
                        time.sleep(0.1)

                        self.integration_time = integration_time_sequence[str(color)][adu_sequence.index(adu)]  # Get integration time depending on color and adu
                        self.min_wavelength = integration_range[str(color)][0]
                        self.max_wavelength = integration_range[str(color)][1]
                        # MEASURE SPECTROMETER
                        # power_dist, wavelengths = self.spectrometer.power_distribution(DarkData, self.integration_time)
                        power_dist = self.spectrometer.power_distribution(self.integration_time, self.min_wavelength,self.max_wavelength)
                        #Standard deviation 
                        std_distribution = np.std(power_dist, ddof=0) 

                        # Find the position of max power
                        max_power_pos = np.argmax(power_dist)

                        # Get the corresponding element in array2
                        amplitude = power_dist[max_power_pos]
                        # center_wl = wavelengths[max_power_pos]

                        power =self.spectrometer.power_value(power_dist)
                        # power = self.spectrometer.power_value(power_dist, wavelengths, self.min_wavelength, self.max_wavelength)

                        data = {'wellID': well[wellid], 'wavelength' : color, 'DC': adu, 'amplitude': amplitude, 'SD': std_distribution, 'minWL': self.min_wavelength, 'maxWL': self.max_wavelength, 'PD': power, 'IntTime': self.integration_time}
                        self.measurements.append(data)
                        print(data)
                        pikachu.StopIllumination()
                
                self.well_id += 1

        self.spectrometer.disconnect()
        
        return "Calibration Complete"
    
    def calibration_complete_data(self):
        pikachu = Pikachu("COM7")
        pikachu.connect()
        pikachu.set_illumination_state(True)

        # UPDATA DEOXYS_INFO
        # self.deoxys_info.append({'dev_id': dev_id})
        self.deoxys_info.append({'sensor_serial': self.sensor_serial})


        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
        well = {i: values[i] for i in range(len(values))}  #A1, A2, A3 ...

        self.well_adu = self.MAX_INTENSITY
        self.wavelength = self.IRED_820NM
        self.integration_time = 20
        # self.measurements.append({'Wavelength': self.wavelength})

        for y in range(self.y_leds):
            for x in range(self.x_leds):
                wellid = x + 12*y
                # TURN ON PIKACHU
                pikachu.set_group_intensity(well[wellid],self.wavelength,self.well_adu)
                # MOVE ROBOT
                self.robot.movel([ 
                    self.ini_position[0] + 9*x, # Change +/- according to direction
                    self.ini_position[1] + 9*y, # Change +/- according to direction
                    self.ini_position[2], 
                    self.ini_position[3], 
                    self.ini_position[4], 
                    self.ini_position[5]
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(1)

                # MEASURE SPECTROMETER
                data = self.spectrometer.measure(20)
                

                #TURN OFF PIKACHU
                # pikachu.StopIllumination()
                time.sleep(0.3)
                pikachu.set_group_intensity(well[wellid],self.wavelength,0)


                self.measurements.append(data)

        self.spectrometer.disconnect()
        print(self.measurements)
        return "Calibration Complete"
        
        return "Calibration Complete"
    
    def calibration_simple(self):
        pikachu = Pikachu("COM7")
        pikachu.connect()
        pikachu.set_illumination_state(True)

        # UPDATA DEOXYS_INFO
        # self.deoxys_info.append({'dev_id': dev_id})
        self.deoxys_info.append({'sensor_serial': self.sensor_serial})


        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        values = [f"{letter}{i}" for letter in letters for i in range(1, 13)]
        well = {i: values[i] for i in range(len(values))}  #A1, A2, A3 ...

        self.well_adu = self.MAX_INTENSITY
        self.wavelength = self.BLUE_465NM
        self.integration_time = 20
        # self.measurements.append({'Wavelength': self.wavelength})

        for y in range(self.y_leds):
            for x in range(self.x_leds):
                wellid = x + 12*y
                # TURN ON PIKACHU
                pikachu.set_group_intensity(well[wellid],self.wavelength,self.well_adu)
                # MOVE ROBOT
                self.robot.movel([ 
                    self.ini_position[0] + 9*x, # Change +/- according to direction
                    self.ini_position[1] + 9*y, # Change +/- according to direction
                    self.ini_position[2], 
                    self.ini_position[3], 
                    self.ini_position[4], 
                    self.ini_position[5]
                ] ,self.linear_velocity, self.linear_acceleration)
                time.sleep(1)

                # MEASURE SPECTROMETER
                power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,433, 491)
                mean_power = sum(power_list) / len(power_list)
                std_dev = statistics.stdev(power_list)

                #TURN OFF PIKACHU
                # pikachu.StopIllumination()
                time.sleep(0.3)
                pikachu.set_group_intensity(well[wellid],self.wavelength,0)

                
               
                info = {'WellID': well[wellid],'MaxPD': mean_power, 'SDMaxPD': std_dev, 
                        'nMaxPDMeasurements': self.num_measurements}

                self.measurements.append(info)

        self.spectrometer.disconnect()
        print(self.measurements)
        return "Calibration Complete"


    def initial_position(self):
        self.robot.movej(self.robot.compute_inverse_kinematics(self.ini_position), self.joint_velocity, self.joint_acceleration)
        return "Initial position reached"
    
    def get_position(self):
        current_position = self.robot.state.cartesian_position
        return current_position
    
    def test_allignment(self, corner):
        # Coordinates of corners
        corners = {'1': [2,0], '2': [11, 0], '3': [0, 7], '4': [11,7]}
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

        self.spectrometer.disconnect()
    
    def get_data(self):
        return self.deoxys_info, self.measurements
    
    def test_ori(self):
        for y in np.arange(0, 3.1, 0.2):
            # TURN ON PIKACHU
            # MOVE ROBOT
            self.robot.movel([ 
                self.ini_position[0] , # Change +/- according to direction
                self.ini_position[1] + y, # Change +/- according to direction
                self.ini_position[2], 
                self.ini_position[3], 
                self.ini_position[4], 
                self.ini_position[5]
            ] ,self.linear_velocity, self.linear_acceleration)
            time.sleep(0.5)

            # MEASURE SPECTROMETER
            power_list = self.spectrometer.measure_power(self.num_measurements,self.integration_time,433, 491)
            mean_power = sum(power_list) / len(power_list)
            print('position y: {}: Power: {}'.format(self.ini_position[1] + y, mean_power))

        self.spectrometer.disconnect()
        
        return "Calibration Complete"

    
if __name__ == "__main__":
        robot = RobotController()
        # robot.test_ori()
        robot.test_allignment(1)
        # robot.calibration_simple()
        # robot.home()
