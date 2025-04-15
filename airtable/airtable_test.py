from airtable_class import AirtableCalibrationUploader

# Configuration
API_KEY = 'patzZ4bX6yRFRauUE.95471454dcbbd994fa31bf3f9292bb93f64d5b8a6f3113558e17e7873e8e76d4'
BASE_ID = 'appjxfjyEex8LeD0Q'

deoxys_info = [{'dev_id': "DX02"},
                {'sensor_serial': "888"},
                {'operator': "Dani"}
                ]
 
measurements = [{'Wavelength': 20},
                {'WellID': 'A1', 'MaxPD': 90, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10},
                {'WellID': 'A2', 'MaxPD': 91, 'SDMaxPD': 1.500, 'nMaxPDMeasurements': 10}
                ]


# Create uploader instance and upload data
uploader = AirtableCalibrationUploader(
    api_key=API_KEY,
    base_id=BASE_ID,
    deoxys_info=deoxys_info
)

result = uploader.upload_measurements(measurements)
print(result)

if result:
    print("Data uploaded successfully!")
else:
    print("Upload failed")
