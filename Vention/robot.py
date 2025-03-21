from machinelogic import Machine, ActuatorGroup
from machinelogic import MachineException, MachineMotionException, ActuatorGroupException, RobotException, DigitalInputException, DigitalOutputException
from thorlab import ThorlabSensor
import time



machine = Machine('192.168.5.2')

# Configured Robots
robot = machine.get_robot("ARNOLD")

# Variables
linear_velocity = 300 # mm/s
linear_acceleration = 500 #mm/s2
joint_velocity = robot.configuration.joint_velocity_limit
joint_acceleration = 50 # deg/s2

# x_leds = 12
# y_leds = 8
x_leds = 4
y_leds = 4
distance_leds = 9
well_id = 1

data = []

# Joint Positions 
j_Home = [-180,-165,115,140,-90,0]

# Cartesian targets
initial_position = [-450, -21.48, 961.5, 0, 0, 0]


# Program robot sequence

def Home():
    robot.movej (
        j_Home,
        joint_velocity,
        joint_acceleration,
    )
    print("Home position")

def Calibration():
    for x in range (x_leds):
        for y in range (y_leds):
            
            robot.movej(robot.compute_inverse_kinematics([-450+9*x, -21.48+9*y, 965, 0, 0, 0]), joint_velocity, joint_acceleration)
            print("position {}, {}".format(x+1, y+1))
            time.sleep(0.5)

def Test():
    robot.movej(robot.compute_inverse_kinematics(initial_position), joint_velocity, joint_acceleration)

### Program ###
Home()
# Test()
Calibration()
Home()
