import streamlit as st
import time
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode
from pykachu.scripts.PikachuJSONBuilder import *


# Define LED colors
COLOR_OPTIONS = {
    "Blue (465nm)": 465,
    "Red (630nm)": 630,
    "Infrared (820nm)": 820
}
MAX_INTENSITY = 4095

# Device credentials
name_device = 'D0U2_old'
access_token = 'f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'

# Initialize Pikachu device
pikachu = Pikachu(name_device, access_token)
pikachu.Mute()
# Create coordinate dictionary
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] 
numbers = list(range(12, 0, -1))  # [12, 11, ..., 1]
my_dict = {i + 1: f"{letters[i % 8]}{numbers[i // 8]}" for i in range(96)}
valid_coordinates = list(my_dict.values())

st.title("LED Illuminator Control")

# Connection check
if pikachu.IsConnected():
    st.success("Connected to the LED illuminator")
else:
    st.error("Failed to connect to the LED illuminator")
    st.stop()

# User inputs
color = st.selectbox("Select LED Color", list(COLOR_OPTIONS.keys()))
intensity = st.number_input("Enter Intensity", min_value=0, max_value=MAX_INTENSITY, value=MAX_INTENSITY, step=1)
duration = st.slider("Select Duration (seconds)", 1, 120, 6)
group = st.text_input("Enter Well Coordinate (e.g., A12, B11):").strip().upper()

def SetGroupADU(pikachu: Pikachu, group: str, color: int, adu: int):
    plan = IlluminationPlanJSON()
    plan.set_plan_id(2) # Do not care about plan id
    plan.add_stage(duration=10000)
    plan.add_condition_to_last_stage(groups=[group], color=color, adu=adu)
    print(pikachu.UploadJSONString(plan.to_json()))
    pikachu.StartIllumination()


# Illumination control
if st.button("Start Illumination"):
    if not group:
        st.error("Please enter a Well coordinate")
        st.stop()
        
    elif group not in valid_coordinates:
        st.error("Invalid Well coordinate. Examples: A12, B11, H1")
        st.stop()
    
    # Display "Illumination running" message
    illumination_status = st.empty()  # Create a placeholder
    illumination_status.success("Illumination RUNNING...")  

    SetGroupADU(pikachu, group, COLOR_OPTIONS[color], intensity)
    time.sleep(duration)

    pikachu.StopIllumination()

    # Update message to "Illumination finished"
    illumination_status.success("Illumination finished.")



