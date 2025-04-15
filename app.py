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
    st.subheader("Home position")
    if st.button("Go home position"):
        message = robot.home()
        st.success(message)

# with col2:
#     if st.button("Run Calibration Sequence"):
#         with st.spinner("Running calibration... Please wait"):
#             message = robot.calibration()
#             st.success(message)
#             message2 = robot.home()
#             st.success(message2)

with col2:
    st.subheader("Calibration sequence")
    operator = st.text_input("Enter operator name", "", key="operator_name")
    if st.button("Run calibration"):
        if operator.strip():  # Ensure the user enters a name
            with st.spinner("Running calibration... Please wait"):
                message = robot.calibration_serial()
                st.success(message)
                message2 = robot.home()
                st.success(message2)
        else:
            st.warning("Please enter operator name before running calibration.")

with col3:
    st.subheader("Check height")
    if st.button("Go initial position"):
        with st.spinner("Moving initial position..."):
            message = robot.initial_position()
            st.success(message)

with col4:
    st.subheader("Check corners")
    corner = st.number_input("Enter corner number (1,2,3,4):",1,4)
    if st.button("Go to corner"):
        corner_check = robot.check_corners(corner)
        st.success(corner_check)

#Send data Airtable
API_KEY = 'patzZ4bX6yRFRauUE.95471454dcbbd994fa31bf3f9292bb93f64d5b8a6f3113558e17e7873e8e76d4'
BASE_ID = 'appjxfjyEex8LeD0Q'
deoxys_info, measurements = robot.get_data()


# Display collected data
st.subheader("Measurement Data")

if measurements:
    # deoxys_info.append({'operator': operator})

    # airtable = AirtableCalibrationUploader(
    #     api_key=API_KEY,
    #     base_id=BASE_ID,
    #     deoxys_info=deoxys_info
    # )

    # result = airtable.upload_measurements(measurements)

    # if result:
    #     st.success("Data uploaded successfully to Airtable!")
    # else:
    #     st.warning("Airtable upload failed")
    df = pd.DataFrame(measurements[1:])
    st.dataframe(df)  # Display the table

    # Plot the data
    st.subheader("Power Measurements Visualization")
    st.line_chart(df.set_index("WellID")[["MaxPD"]]) 
else:
    st.write("No data available. Run Calibration first!")
