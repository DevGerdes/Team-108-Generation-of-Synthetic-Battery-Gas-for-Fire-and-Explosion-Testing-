## Main control loop
# defines needed global variables for commnuication between proccesses
# Calls functions for UI and serial communication with Arduino

#Import all needed libraries
import tkinter as tk
from tkinter import scrolledtext
from tkinter import Tk, filedialog
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd


# Import functions or objects from other files
from UI import UI_Object
from Controls import ControlSystem
from data_handler import Data_Handler

### Start main code
if __name__ == "__main__":

    # Create UI and Controls System objects, then link them
    Gas_Mixing_UI = UI_Object()
    cs = ControlSystem()
    dh = Data_Handler()

    Gas_Mixing_UI.cs = cs
    Gas_Mixing_UI.dh = dh
    dh.UI = Gas_Mixing_UI
    cs.UI = Gas_Mixing_UI
    dh.cs = cs
    cs.dh = dh

    # Start the UI main loop
    Gas_Mixing_UI.write_to_terminal("App started.")


    # Start the Control System main loop
    cs.start()
    Gas_Mixing_UI.update_indicators(Gas_Mixing_UI.indicators[0])  # Initialize state indicator

    Gas_Mixing_UI.mainloop()

