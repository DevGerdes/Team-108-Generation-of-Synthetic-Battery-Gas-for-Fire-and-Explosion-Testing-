## Main control loop
# defines needed global variables for commnuication between proccesses
# Calls functions for UI and serial communication with Arduino

#Import all needed libraries
import tkinter as tk
from tkinter import scrolledtext
import time

# Import functions from other files
from UI import UI_Object

### Define global variables
# State change definitions
STATE = 0  # 0 = hardware setup, 1 = idle (MFC's closed, data read on), 2 = run controls loop, 3 = non-dangerous erorr, 4 = EMERGENCY STOP

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

    # Build and run UI
    Gas_Mixing_UI = UI_Object()
    Gas_Mixing_UI.write_to_terminal("App started.")
    Gas_Mixing_UI.mainloop()