# app.py

import streamlit as st
import pandas as pd
import time
from backend_spec import RobotController
import base64

#----------------------HEADER---------------------------

# Function to encode image as base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert logo to base64
image_base64 = get_base64_image("header.png")

# Inject custom CSS for a fixed header with the company logo in the center-right
st.markdown(f"""
    <style>
        .header-container {{
            position: fixed;
            top: 20;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 0px;  /* Reduce padding to make it thinner */
            height: 100px;  /* Set a fixed height to make the header less thick */
            z-index: 300;
            text-align: center;
            border-bottom: 2px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: flex-end; /* Align content to the right */
            overflow: hidden;
        }}
        .header-container img {{
            max-width: none;
            width: 100%;
            height: 100%;
            object-fit: cover;  /* Ensures the image covers the area */
            object-position: right center; /* Focuses on the center-right part */
        }}
        .content {{
            padding-top: 50px; /* Prevents content overlap with header */
        }}
    </style>
    <div class="header-container">
        <img src="data:image/png;base64,{image_base64}">
    </div>
""", unsafe_allow_html=True)

# Add padding to prevent content overlap
st.markdown('<div class="content">', unsafe_allow_html=True)

#--------------------------------------------------------------

# Add padding to prevent content overlap
st.markdown('<div class="content">', unsafe_allow_html=True)
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
    df = pd.DataFrame(data)
    st.dataframe(df)  # Display the table

    # Plot the data
    st.subheader("Power Measurements Visualization")
    st.line_chart(df.set_index("well_id")[["Power"]]) 
else:
    st.write("No data available. Run Calibration first!")
