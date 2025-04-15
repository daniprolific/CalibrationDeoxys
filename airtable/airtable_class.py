# airtable_uploader.py
import requests

class AirtableCalibrationUploader:
    def __init__(self, api_key, base_id, deoxys_info):
        self.API_KEY = api_key
        self.BASE_ID = base_id
        self.deoxys_info = deoxys_info
        
    def _create_record(self, table_name, fields):
        """Internal method to create records"""
        url = f"https://api.airtable.com/v0/{self.BASE_ID}/{table_name}"
        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"records": [{"fields": fields}]}
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()['records'][0]
        except requests.exceptions.RequestException as e:
            print(f"Error creating record in {table_name}: {str(e)}")
            return None

    def upload_measurements(self, measurements):
        """
        Main method to upload all calibration data

        Measurement Datastructure example:

            measurements = [{'Wavelength': 20},
                {'WellID': 'A1', 'MaxPD': 90, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10},
                {'WellID': 'A2', 'MaxPD': 91, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10}
                ]
        """
        # Create parent device calibration record
        dev_cal_record = self._create_record('DevCalibrations', {
            'DevID': self.deoxys_info[0]['dev_id'],
            'Operator': self.deoxys_info[2]['operator'],
            'SensorSerial': self.deoxys_info[1]['sensor_serial']
        })
        
        if not dev_cal_record:
            print("Failed to create DevCalibration record. Aborting.")
            return False

        parent_id = dev_cal_record['id']
        
        # Process color measurements
        
        color_record = self._create_record('ColorCalibs', {
            'DevCalib': [parent_id],
            'Wavelength': measurements[0]['Wavelength']
        })
        
        if not color_record:
            print(f"Skipping spots for wavelength {measurements[0]['Wavelength']}")
            
        # Process spot measurements
        for spot in measurements[1:]:
            self._create_record('SpotCalibs', {
                'ColorCalib': [color_record['id']],
                'wellID': spot['WellID'],
                'MaxPD': spot['MaxPD'],
                'SDMaxPD': spot['SDMaxPD'],
                'nMaxPDMeasurements': spot['nMaxPDMeasurements']
            })
    
        return True