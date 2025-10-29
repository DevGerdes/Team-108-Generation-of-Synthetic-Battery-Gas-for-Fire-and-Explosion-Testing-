## Main control loop
# defines needed global variables for commnuication between proccesses
# Calls functions for UI and serial communication with Arduino

#Import all needed libraries
import tkinter as tk
from tkinter import scrolledtext
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math


# Import functions from other files
from UI import UI_Object
from Controls import ControlSystem

### Define global variables
# State change definitions
#  0 = System setup
#  1 = idle (MFC's closed, data read on)
#  2 = run controls loop
#  3 = non-dangerous erorr
#  4 = EMERGENCY STOP
#  5 = Device shut off
STATE = 0  # This is the global state variable that will be shared

# Controls default variables
MFC_P = [1,1,1,1,1]  
MFC_I = [0.0, 0.0, 0.0, 0.0, 0.0]  

MFC_SETPOINT = [0.0, 0.0, 0.0, 0.0, 0.0]
MFC_RESPONSE = [0.0, 0.0, 0.0, 0.0, 0.0]

# Data plotting and saving variables
MFC_1SETPOINT_HISTORY = []  # 5 lists for 5 MFC's
MFC_1_RESPONSE_HISTORY = []  # 5 lists for 5 MFC's
MFC_TIME_HISTORY = []

PRESSURE_SENOR_1_HISTORY = []
PRESSURE_SENOR_2_HISTORY = []



# For UI
STYLES = {
    "bg": "#f0f0f0",
    "panel_bg": "#d9d9d9",
    "text": "#000000",
    "button_bg": "#e0e0e0",
    "button_active_bg": "#c0c0c0",
    "terminal_bg": "#1e1e1e",
    "terminal_fg": "#d4d4d4"
}

### Start main code
if __name__ == "__main__":

    # Build UI
    Gas_Mixing_UI = UI_Object()
    Gas_Mixing_UI.write_to_terminal("App started.")
    Gas_Mixing_UI.mainloop()