# app.py

import streamlit as st
import pandas as pd
import time
from backend_spec import RobotController
import base64
from pykachu.src.pykachu.cloud.Pikachu import Pikachu, PikachuReturnCode

#----------------------HEADER---------------------------

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

image_base64 = get_base64_image("header3.png")

# Modified header section in app.py
st.markdown(f"""
    <style>
        .header-container {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 20%;  /* Increased height */
            background-color: white;
            z-index: 9999;  /* Maximum z-index */
            border-bottom: 2px solid #ddd;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}
        .header-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center right;
            margin: 0;
            padding: 0;
        }}
        .content {{
            margin-top: 50px;  /* Match header height */
            position: relative;
            z-index: 0;
        }}
        /* Remove Streamlit's default padding */
        .main .block-container {{
            padding: 0;
            margin: 0;
        }}
    </style>
    <div class="header-container">
        <img src="data:image/png;base64,{image_base64}">
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="content">', unsafe_allow_html=True)

#--------------------------------------------------------------

st.title("Robot Control Panel 🤖")

# Initialize Robot Controller
robot = RobotController()

# Initialize Pikachu device
COLOR_OPTIONS = {
    "Blue (465nm)": 465,
    "Red (630nm)": 630,
    "Infrared (820nm)": 820
}
MAX_INTENSITY = 4095
name_device = 'D0U2_old'
access_token = 'f7b398d48420fa9c6d8c7e8e18a500b968e0ff09'
pikachu = Pikachu(name_device, access_token)

if not pikachu.IsConnected():
    st.error("⚠️ LED illuminator connection failed")

# Create columns for buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Home Position"):
        message = robot.home()
        st.success(message)

with col2:
    # First button to reveal parameters
    if st.button("Calibration Deoxys"):
        st.session_state.show_calibration = True  # Initialize session state

    # Only show parameters if session state is active
    if st.session_state.get('show_calibration', False):
        with st.form(key='calibration_form'):
            st.write("#### Illumination Settings")
            color = st.selectbox("LED Color", list(COLOR_OPTIONS.keys()))
            intensity = st.slider("Intensity", 0, MAX_INTENSITY, MAX_INTENSITY)
            
            # Second button to start the process
            if st.form_submit_button("Start Calibration"):
                if not pikachu.IsConnected():
                    st.error("LED illuminator not connected")
                else:
                    status = pikachu.SetSimpleIlluminationPlan(
                        duration_s=10000,
                        color_nm=COLOR_OPTIONS[color],
                        intensity=intensity,
                        tOn_s=0,
                        tOff_s=0,
                        plan_id=11
                    )
                    if status == PikachuReturnCode.GOOD:
                        try:
                            pikachu.StartIllumination()
                            with st.spinner("Running calibration with illumination..."):
                                cal_message = robot.calibration()
                                st.success(cal_message)
                                home_message = robot.home()
                                st.success(home_message)
                        finally:
                            pikachu.StopIllumination()
                            st.success("Illumination stopped")
                    else:
                        st.error(f"Illumination error: {status}")

with col3:
    if st.button("Initial position"):
        with st.spinner("Moving initial position..."):
            message = robot.initial_position()
            st.success(message)

with col4:
    if st.button("Define position:"):
        current_position = robot.get_position()
        st.success(current_position)

# Display data
st.subheader("Measurement Data")
data = robot.get_data()

if data:
    df = pd.DataFrame(data)
    st.dataframe(df)
    st.subheader("Power Measurements Visualization")
    st.line_chart(df.set_index("well_id")["Power (µW/(cm²)"]) 
else:
    st.write("No data available. Run Calibration first!")