letters = ['A', 'B']
numbers = [1,2]

def create_well_sequence(letters, numbers):
    well_sequence =  [f"{letter}{number}" for letter in letters for number in numbers]
    return well_sequence

w = create_well_sequence(letters, numbers)

wellid = 0
for y in letters:
    for x in numbers:

        for color in range(2):
            for adu in range (2):
                print (w[wellid])
        wellid+=1