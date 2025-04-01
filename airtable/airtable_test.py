from airtable_class import AirtableCalibrationUploader

# Configuration
API_KEY = 'patzZ4bX6yRFRauUE.95471454dcbbd994fa31bf3f9292bb93f64d5b8a6f3113558e17e7873e8e76d4'
BASE_ID = 'appjxfjyEex8LeD0Q'

device_info = {
    'dev_id': "LOL",
    'operator': "Dani",
    'sensor_serial': "11111"
}

measurements = [{'Wavelength': 20},
                {'WellID': 'A1', 'MaxPD': 90, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10},
                {'WellID': 'A2', 'MaxPD': 91, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10}
                ]


# Create uploader instance and upload data
uploader = AirtableCalibrationUploader(
    api_key=API_KEY,
    base_id=BASE_ID,
    device_info=device_info
)

result = uploader.upload_measurements(measurements)

if result:
    print("Data uploaded successfully!")
else:
    print("Upload failed")
