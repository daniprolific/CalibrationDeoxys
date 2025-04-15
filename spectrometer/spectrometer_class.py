import sys
import time
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from .avaspec.avaspec import *
import numpy as np


class Avantes:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.wavelength_ini = [0.0] * 4096
        self.spectraldata_ini = [0.0] * 4096
        self.wavelength_total = None
        self.spectraldata_total = None
        self.spectraldata_masked = None
        self.wavelength_masked = None
        self.dev_handle = None 
        self.pixels = None
        self.mask_wavelenght = None
        self.NrScanned = 0
        self.calibration_factors = None
        self.cal_integration_time = None  
        self.current_integration_time = None

    def initialize_device(self):
        """Connect to spectrometer connected in the USB port"""

        AVS_Init(0)
        if AVS_GetNrOfDevices() == 0:
            raise RuntimeError("No spectrometer found")
        
        device_list = AVS_GetList(1)
        print("Found Serialnumber:", device_list[0].SerialNumber.decode("utf-8"))
        self.dev_handle = AVS_Activate(device_list[0])
        
        # Get device parameters including calibration data
        dev_params = AVS_GetParameter(self.dev_handle, 63484)
        self.pixels = dev_params.m_Detector_m_NrPixels
        self.wavelength_ini = AVS_GetLambda(self.dev_handle)
        
        # Extract irradiance calibration parameters
        self.calibration_factors = dev_params.m_Irradiance_m_IntensityCalib_m_aCalibConvers
        self.cal_integration_time = dev_params.m_Irradiance_m_IntensityCalib_m_CalInttime


    def count_distribution(self, integration_time , min_wavelength , max_wavelength):
        """Perform measurement and get power distribution in units: (Count / nm)"""
        self.current_integration_time = integration_time
        meas_config = MeasConfigType(
            m_StartPixel=0,
            m_StopPixel=self.pixels - 1,
            m_IntegrationTime=self.current_integration_time,
            m_NrAverages=1,
            m_SaturationDetection=1,
            m_Trigger_m_Mode=0,
            m_CorDynDark_m_Enable=1
        )
        
        AVS_UseHighResAdc(self.dev_handle, True)
        AVS_PrepareMeasure(self.dev_handle, meas_config)
        self.NrScanned = 0
        
        def measurement_callback(pparam1, pparam2):
            ret = AVS_GetScopeData(self.dev_handle)
            self.spectraldata_ini = ret[1]
            self.NrScanned += 1

        scans = 1
        callback = AVS_MeasureCallbackFunc(measurement_callback)
        AVS_MeasureCallback(self.dev_handle, callback, scans)

        while self.NrScanned < scans:
            time.sleep(0.01)
            self.app.processEvents()

        self.wavelength_total = np.array([self.wavelength_ini[i] for i in range(self.pixels)])
        self.spectraldata_total = np.array([self.spectraldata_ini[i] for i in range(self.pixels)])

        #CREATE A MASK IN THE DEFINED WAVELENGTH RANGE
        self.mask_wavelenght = (self.wavelength_total > min_wavelength) & (self.wavelength_total < max_wavelength)

        #APPLY THE MASK ON THE WAVELENGTHS AND THE MEASUREMENTS
        self.wavelength_masked = self.wavelength_total[self.mask_wavelenght]
        self.spectraldata_masked = self.spectraldata_total[self.mask_wavelenght]

        
    def power_distribution(self, integration_time , min_wavelength , max_wavelength):
        """Convert raw counts (Count / nm) to µW/(cm²·nm) using this formula
        
        ScopeData(i)   =  Measured A/D Counts at pixel i (AVS_GetScopeData) 
        DarkData(i)     =  Dark data at pixel i, saved in application software 
        IntensityCal(i) =  m_Irradiance.m_IntensityCalib.m_aCalibConvers[i] 
        CalInttime      =  m_Irradiance.m_IntensityCalib.m_CalInttime 
        CurInttime      =  Integration time in measurement (used in the PrepareMeasurement structure) 

        Inttimefactor = (CalInttime/CurInttime) 
        
        Irradiance Intensity =  ADCFactor * Inttimefactor * ((ScopeData(i) - DarkData(i))/IntensityCal(i)) """

        self.count_distribution(integration_time, min_wavelength, max_wavelength)

        ADCFactor = 0.0025
    
        calib = np.ctypeslib.as_array(self.calibration_factors)
        calib_convers = calib[0:2048]
        IntensityCal = calib_convers[self.mask_wavelenght]

        Inttimefactor = self.cal_integration_time / self.current_integration_time

        # DarkData is the count distribution with the ilumination off
        DarkData_total = np.load(r"C:\Users\madel\Desktop\Calibration\Code\Deoxys calibration\spectrometer\DarkData_30.npy")
        DarkData = DarkData_total[self.mask_wavelenght]

        ScopeData = self.spectraldata_masked

        power_dist = []
    
        for i in range (len(ScopeData)):
            power_dist.append(ADCFactor * Inttimefactor * ((ScopeData[i] - DarkData[i]) / IntensityCal[i]))

        return power_dist
    
    # def power_distribution(self):
    #     """Convert raw counts (Count / nm) to µW/(cm²·nm) using this formula
        
    #     ScopeData(i)   =  Measured A/D Counts at pixel i (AVS_GetScopeData) 
    #     DarkData(i)     =  Dark data at pixel i, saved in application software 
    #     IntensityCal(i) =  m_Irradiance.m_IntensityCalib.m_aCalibConvers[i] 
    #     CalInttime      =  m_Irradiance.m_IntensityCalib.m_CalInttime 
    #     CurInttime      =  Integration time in measurement (used in the PrepareMeasurement structure) 

    #     Inttimefactor = (CalInttime/CurInttime) 
        
    #     Irradiance Intensity =  ADCFactor * Inttimefactor * ((ScopeData(i) - DarkData(i))/IntensityCal(i)) """

    #     ADCFactor = 0.25
      
    #     calib = np.ctypeslib.as_array(self.calibration_factors)
    #     calib_convers = calib[0:2048]
    #     IntensityCal = calib_convers[self.mask_wavelenght]

    #     Inttimefactor = self.cal_integration_time / self.current_integration_time

    #     # DarkData is the count distribution with the ilumination off
    #     DarkData_total = np.load(r"C:\Users\madel\Desktop\Calibration\Code\Deoxys calibration\spectrometer\DarkData.npy")
    #     DarkData = DarkData_total[self.mask_wavelenght]

    #     ScopeData = self.spectraldata_masked

    #     power_dist = []
     
    #     for i in range (len(ScopeData)):
    #         power_dist.append(ADCFactor * Inttimefactor * ((ScopeData[i] - DarkData[i]) / IntensityCal[i]))

    #     return power_dist

    def power_value(self, power_dist):
        """Calculate total power in µW/cm² performing an integration in the power distribution"""
        return np.trapz(power_dist, self.wavelength_masked)
        

    def measure_power(self, num_measurements , integration_time , min_wavelength , max_wavelength):
        """Perform measurements and get the power values in a list"""
           
        power_list = []

        for measure in range (num_measurements):
            power_distribution = self.power_distribution(integration_time, min_wavelength, max_wavelength)
            power_val = self.power_value(power_distribution)
            power_list.append(power_val)
        
        return power_list

    # def measure_power(self, num_measurements , integration_time , min_wavelength , max_wavelength , averages=1, scans=1):
    #     """Perform measurements and get the power values in a list"""
           
    #     power_list = []

    #     for measure in range (num_measurements):
    #         self.count_distribution(integration_time, min_wavelength, max_wavelength, averages, scans)
    #         power_distribution = self.power_distribution()
    #         power_val = self.power_value(power_distribution)
    #         power_list.append(power_val)
        
    #     return power_list

    def disconnect(self):
        AVS_Deactivate(self.dev_handle)
        self.app.quit()

    def plot_power_dist(self, power_dist):
        plt.figure(figsize=(10, 6))
        plt.plot(self.wavelength_masked, power_dist, 'b-', linewidth=1)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Power Distribution [µW/(cm²·nm)]")
        plt.title("Spectral Measurement")
        plt.grid(True)
        plt.show()

if __name__ == "__main__":

    ### CREATE DARKDATA 
    # spectrometer = Avantes()
    # spectrometer.initialize_device()
    # spectrometer.count_distribution(30,300,800)
    # dark_data = spectrometer.spectraldata_total
    # np.save("DarkData.npy", dark_data)
    # spectrometer.disconnect()

    spectrometer = Avantes()
    spectrometer.initialize_device()
    int_time = [20,18]
    for i in int_time:
        power = spectrometer.measure_power(3,i,400,540)
        print('power for int time {}: {}'.format(i,power))
        time.sleep(1)
    

    spectrometer.disconnect()



 