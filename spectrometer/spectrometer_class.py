#!/usr/bin/env python3
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
        self.spectral_data = None
        self.wavelengths = None
        self.dev_handle = 0
        self.pixels = 4096
        self.wavelength = [0.0] * 4096
        self.spectraldata = [0.0] * 4096
        self.NrScanned = 0

    def initialize_device(self):
        AVS_Init(0)
        if AVS_GetNrOfDevices() == 0:
            raise RuntimeError("No spectrometer found")
        
        # devices = AVS_GetList(AVS_GetNrOfDevices())
        # globals.dev_handle = AVS_Activate(devices[0])
        mylist = AvsIdentityType * 1
        mylist = AVS_GetList(1)
        serienummer = str(mylist[0].SerialNumber.decode("utf-8"))
        print("Found Serialnumber: " + serienummer)
        self.dev_handle = AVS_Activate(mylist[0])
        
        dev_params = AVS_GetParameter(self.dev_handle, 63484)
        self.pixels = dev_params.m_Detector_m_NrPixels
        self.wavelength = AVS_GetLambda(self.dev_handle)

    def perform_measurement(self, integration_time=500.0, averages=1, scans=2):
        meas_config = MeasConfigType(
            m_StartPixel=0,
            m_StopPixel=self.pixels - 1,
            m_IntegrationTime=integration_time,
            m_NrAverages=averages,
            m_SaturationDetection=1,
            m_Trigger_m_Mode=0,
            m_CorDynDark_m_Enable = 1
        )
        
        AVS_PrepareMeasure(self.dev_handle, meas_config)
        self.NrScanned = 0
        
        def measurement_callback(pparam1, pparam2):
            ret = AVS_GetScopeData(self.dev_handle)
            self.spectraldata = ret[1]
            self.NrScanned += 1

        callback = AVS_MeasureCallbackFunc(measurement_callback)
        AVS_MeasureCallback(self.dev_handle, callback, scans)

        while self.NrScanned < scans:
            time.sleep(0.01)
            self.app.processEvents()

        self.wavelengths = [self.wavelength[i] for i in range(self.pixels)]
        self.spectral_data = [self.spectraldata[i] for i in range(self.pixels)]

        # AVS_Deactivate(self.dev_handle)
        # self.app.quit()
    
    def disconnect(self):
        AVS_Deactivate(self.dev_handle)
        self.app.quit()


    def calculate_power(self):
        """
        Calculate the total power by integrating the spectral data across the wavelengths.
        
        Parameters:
            wavelengths (list or numpy array): The wavelength values in nm.
            spectral_data (list or numpy array): The measured luminosity values ((mW/cm^2)/nm).
        
        Returns:
            float: The total integrated power in mW/cm^2.
        """
        return np.trapz(self.spectral_data, self.wavelengths)

    def plot_results(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.wavelengths, self.spectral_data, 'b-', linewidth=1)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Intensity (counts)")
        plt.title("Spectral Measurement")
        plt.grid(True)
        plt.show()


if __name__ == "__main__":
    spectrometer = Avantes()

    spectrometer.initialize_device()
    spectrometer.perform_measurement()
    spectrometer.plot_results()
    power = spectrometer.calculate_power()


    print(spectrometer.spectral_data[:10])
    print(spectrometer.wavelengths[:10])
    print('power:',power)