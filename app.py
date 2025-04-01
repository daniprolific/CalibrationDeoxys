# app.py

import streamlit as st
import pandas as pd
import time
from backend_FINAL import RobotController
import base64
from airtable.airtable_class import AirtableCalibrationUploader
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

# Add padding to prevent content overlap
st.title("Robot Control Panel 🤖")

# Initialize Robot Controller
robot = RobotController()

# Create columns for buttons to be displayed in the same row
col1, col2, col3, col4 = st.columns(4)

# Buttons to control the robot in the same row
with col1:
    if st.button("Home Position"):
        message = robot.home()
        st.success(message)

with col2:
    if st.button("Run Calibration Sequence"):
        with st.spinner("Running calibration... Please wait"):
            message = robot.calibration()
            st.success(message)
            message2 = robot.home()
            st.success(message2)

with col3:
    if st.button("Initial position"):
        with st.spinner("Moving initial position..."):
            message = robot.initial_position()
            st.success(message)

with col4:
    if st.button("Define position:"):
        current_position = robot.get_position()
        st.success(current_position)

# Display collected data
st.subheader("Measurement Data")
data = robot.get_data()

if data:
    df = pd.DataFrame(data[1:])
    st.dataframe(df)  # Display the table

    # Plot the data
    st.subheader("Power Measurements Visualization")
    st.line_chart(df.set_index("WellID")[["MaxPD", "SDMaxPD"]]) 
else:
    st.write("No data available. Run Calibration first!")
