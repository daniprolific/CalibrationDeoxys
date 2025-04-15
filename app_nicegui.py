from nicegui import ui
from backend_nicegui import RobotController
from airtable.airtable_class import AirtableCalibrationUploader

# Initialize Robot Controller
robot = RobotController()

# Title
ui.label("🤖 Robot Control Panel").style('font-size: 24px; font-weight: bold')

# Space between title and controls
ui.separator()

# Create row of buttons and input
with ui.row():

    # --- Home Position ---
    with ui.column():
        ui.label("Home position")
        def go_home():
            message = robot.home()
            ui.notify(message, type='positive')
        ui.button("Go home position", on_click=go_home)

    # --- Calibration Sequence ---
    with ui.column():
        operator_name_input = ui.input("Enter operator name", placeholder="Operator").props('outlined')

        def run_calibration():
            name = operator_name_input.value.strip()
            if not name:
                ui.notify("Please enter operator name before running calibration.", type='warning')
                return
            with ui.dialog().props('persistent') as dialog, ui.card():
                ui.label("Running calibration... Please wait")
            dialog.open()
            # message = robot.calibration_serial()
            # ui.notify(message, type='positive')
            message2 = robot.home()
            ui.notify(message2, type='positive')
            dialog.close()

        ui.label("Calibration sequence")
        ui.button("Run calibration", on_click=run_calibration)


    # --- Check Height ---
    with ui.column():
        ui.label("Check height")
        def go_initial():
            with ui.dialog().props('persistent') as dialog, ui.card():
                ui.label("Moving to initial position...")
            dialog.open()
            message = robot.initial_position()
            ui.notify(message, type='positive')
            dialog.close()
        ui.button("Go initial position", on_click=go_initial)

    # --- Check Corners ---
    with ui.column():
        corner_input = ui.number(label="Enter corner number (1,2,3,4):", min=1, max=4, value=1)
        def go_corner():
            corner = int(corner_input.value)
            message = robot.check_corners(corner)
            ui.notify(message, type='positive')
        ui.label("Check corners")
        ui.button("Go to corner", on_click=go_corner)


# Run the app
ui.run(host='127.0.0.1', port=8081)

