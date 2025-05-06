from airtable_class import AirtableCalibrationUploader

# Configuration
API_KEY = 'patzZ4bX6yRFRauUE.95471454dcbbd994fa31bf3f9292bb93f64d5b8a6f3113558e17e7873e8e76d4'
BASE_ID = 'appjxfjyEex8LeD0Q'

deoxys_info = [{'dev_id': "Deox"},
                {'Operator': "Dan"}
                ]
 
measurements = [
    {'Wavelength': 465, 'wellID': 'A1', 'adu': 4095, 'Power': 50, 'peakWL': 470, 'centerWL': 465, 'SD': 5, 'minWL': 460, 'maxWL': 475},
    {'Wavelength': 630, 'wellID': 'A1', 'adu': 4095, 'Power': 20, 'peakWL': 635, 'centerWL': 630, 'SD': 5, 'minWL': 625, 'maxWL': 635},
    {'Wavelength': 465, 'wellID': 'A2', 'adu': 4095, 'Power': 52, 'peakWL': 468, 'centerWL': 464, 'SD': 4, 'minWL': 459, 'maxWL': 470},
    {'Wavelength': 630, 'wellID': 'A2', 'adu': 4095, 'Power': 21, 'peakWL': 632, 'centerWL': 631, 'SD': 3, 'minWL': 627, 'maxWL': 636},
]

color_sequence = [465, 630]

def organize_measurements(measurements):


    '''
    Organize measurements into different wavelengths

    Returns:

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

measurements_organized = organize_measurements(measurements)


# Create uploader instance and upload data
uploader = AirtableCalibrationUploader(
    api_key=API_KEY,
    base_id=BASE_ID,
)

uploader.upload_info(deoxys_info)

for color in color_sequence:
    result = uploader.upload_measurements( measurements_organized[color])
    print(result)

    if result:
        print("Data uploaded successfully!")
    else:
        print("Upload failed")


