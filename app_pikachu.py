import streamlit as st
import time
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode

# Define LED colors
COLOR_OPTIONS = {
    "Blue (465nm)": 465,
    "Red (630nm)": 630,
    "Infrared (820nm)": 820
}
MAX_INTENSITY = 4095

# Device credentials
name_device = 'D0U2'
access_token = 'f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'

# Initialize Pikachu device
pikachu = Pikachu(name_device, access_token)

st.title("LED Illuminator Control")

if pikachu.IsConnected():
    st.success("Connected to the LED illuminator")
else:
    st.error("Failed to connect to the LED illuminator")

# User inputs
color = st.selectbox("Select LED Color", list(COLOR_OPTIONS.keys()))
intensity = st.slider("Select Intensity", 0, MAX_INTENSITY, MAX_INTENSITY)
duration = st.slider("Select Duration (seconds)", 1, 30, 6)

if st.button("Start Illumination"):
    status = pikachu.SetSimpleIlluminationPlan(
        duration_s=10000,
        color_nm=COLOR_OPTIONS[color],
        intensity=intensity,
        tOn_s=0,
        tOff_s=0,
        plan_id=11
    )
    if status != PikachuReturnCode.GOOD:
        st.error(f"Error: {status}")
    else:
        st.success("Starting Illumination Plan")
        pikachu.StartIllumination()
        time.sleep(duration)
        pikachu.StopIllumination()
        st.success("Illumination Stopped")
