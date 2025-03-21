#!/usr/bin/env python3
import sys
import time
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from avaspec import *
import globals

class AutomatedMeasurement:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.spectral_data = None
        self.wavelengths = None

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
        globals.dev_handle = AVS_Activate(mylist[0])
        
        dev_params = AVS_GetParameter(globals.dev_handle, 63484)
        globals.pixels = dev_params.m_Detector_m_NrPixels
        globals.wavelength = AVS_GetLambda(globals.dev_handle)

    def perform_measurement(self, integration_time=20.0, averages=1, scans=1):
        meas_config = MeasConfigType(
            m_StartPixel=0,
            m_StopPixel=globals.pixels - 1,
            m_IntegrationTime=integration_time,
            m_NrAverages=averages,
            m_SaturationDetection=1,
            m_Trigger_m_Mode=0,
            m_CorDynDark_m_Enable = 1
        )
        
        AVS_PrepareMeasure(globals.dev_handle, meas_config)
        globals.NrScanned = 0
        
        def measurement_callback(pparam1, pparam2):
            ret = AVS_GetScopeData(globals.dev_handle)
            globals.spectraldata = ret[1]
            globals.NrScanned += 1

        callback = AVS_MeasureCallbackFunc(measurement_callback)
        AVS_MeasureCallback(globals.dev_handle, callback, scans)

        while globals.NrScanned < scans:
            time.sleep(0.01)
            self.app.processEvents()

        self.wavelengths = [globals.wavelength[i] for i in range(globals.pixels)]
        self.spectral_data = [globals.spectraldata[i] for i in range(globals.pixels)]

    def plot_results(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.wavelengths, self.spectral_data, 'b-', linewidth=1)
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Intensity (counts)")
        plt.title("Spectral Measurement")
        plt.grid(True)
        plt.show()

    def run(self):
        try:
            self.initialize_device()
            self.perform_measurement()
            print("Measurement completed successfully!")
            self.plot_results()
            print(f"Wavelengths (first 10): {self.wavelengths[:10]}")
            print(f"Spectral data (first 10): {self.spectral_data[:10]}")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            AVS_Deactivate(globals.dev_handle)
            self.app.quit()

if __name__ == "__main__":
    meas = AutomatedMeasurement()
    meas.run()