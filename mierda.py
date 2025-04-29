
# Example setup
measurements = [{'Wavelength': 465, 'wellID': 'A1', 'adu': 4095, 'Power': 53.767783870278144, 'peakWL': 462.92584228515625, 'centerWL': 463.2688607183168, 'SD': 9.695369897194382, 'minWL': 434.1827510267336, 'maxWL': 492.3549704098999}, {'Wavelength': 630, 'wellID': 'A1', 'adu': 4095, 'Power': 8.96023959186335, 'peakWL': 631.3226318359375, 'centerWL': 629.8817236374857, 'SD': 8.393102086301523, 'minWL': 604.7024173785811, 'maxWL': 655.0610298963903}, {'Wavelength': 465, 'wellID': 'A2', 'adu': 4095, 'Power': 56.170769212968416, 'peakWL': 462.92584228515625, 'centerWL': 463.3238714815301, 'SD': 9.756085398856309, 'minWL': 434.05561528496116, 'maxWL': 492.592127678099}, {'Wavelength': 630, 'wellID': 'A2', 'adu': 4095, 'Power': 9.402546558978194, 'peakWL': 633.05419921875, 'centerWL': 630.1765731538273, 'SD': 8.433400275424086, 'minWL': 604.8763723275551, 'maxWL': 655.4767739800996}, {'Wavelength': 465, 'wellID': 'A3', 'adu': 4095, 'Power': 56.098490044623496, 'peakWL': 462.3378601074219, 'centerWL': 462.9892286603466, 'SD': 9.583716894548076, 'minWL': 434.23807797670236, 'maxWL': 491.74037934399087}, {'Wavelength': 630, 'wellID': 'A3', 'adu': 4095, 'Power': 9.629148460549866, 'peakWL': 631.3226318359375, 'centerWL': 629.2305673381464, 'SD': 8.466004278543688, 'minWL': 603.8325545025153, 'maxWL': 654.6285801737776}]


def organize_measurements(measurements):
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

organized_measurements = organize_measurements(measurements)


for wavelength, data_list in organized_measurements.items():
    print(data_list)