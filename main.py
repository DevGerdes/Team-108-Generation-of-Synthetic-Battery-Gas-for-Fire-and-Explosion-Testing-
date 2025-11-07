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


"""Design Variables
The given value here is a default value but will change as program runs
"""
t_start = time.time()  # Record starting time of program
Vtot_std = 0 # Total Standard valoumetric flow rate [SLPM]
mole_fractions = [0, 0, 0, 0, 0]  # Mole fractions of each gas in the mixture per MFC
VHS_H2 = 0 # MFC full scale standard flow for H2m[SLPM]
u_gas = [0, 0, 0, 0, 0]  # fraction of flow per gas [SLPM]
P_mixing_chamber = 0  # Pressure in mixing chamber [PSI]
T_std = 20  # Standard temperature [C]
P_std = 14.7  # Standard pressure [PSI]
P_Nozzle = 0  # Pressure at nozzle [PSI]
E_STOP = False  # Emergency stop flag
sample_rate = .2  # Sample rate [sec]

"""Measured Variables"""
T_Line = 0  # Temperature in line [C]
P_Line = 1  # Pressure in line [PSI]

"""Computed Variables"""
# Calculated Once
sum_mole_fraction = np.sum(mole_fractions)  # Sum of mole fractions. Should be ~1
Vdot_gas = [m_i*Vtot_std for m_i in mole_fractions]  # Voloumetric flow rate per gas [SLPM]
Vtot_actual = Vtot_std * (T_Line / T_std) * (P_std / P_Line)

"""Calculated Continuously"""
#rho_mix_std = P_std/( (R_u * T_std) * np.sum([x*M for x,M in zip(x,mole_fractions)]) ) # Mixture density at standard conditions [kg/m^3]
#rho_mix_line = P_std/(R_u * T_Line)*np.sum([x*M for x,M in zip(x,mole_fractions)]) # Mixture density at standard conditions [kg/m^3]]
#mdot = [rho_std*Vdot_i for rho_std,Vdot_i in zip(rho_mix_std,Vdot_gas)]  # Mass flow rate per gas at standard conditions [kg/s]
#mdot_total = np.sum(mdot)  # Total mass flow rate at standard conditions [kg/s]
A_nozzle = .01 # Nozzle exit area [m^2]
#V_nozzle = math.sqrt(2*(P_mixing_chamber - P_Nozzle)/rho_mix_line)  # Nozzle exit velocity [m/s]
#LHW_mix = np.sum() # weighted average lower heating value for gas mix




"""MFC and Data Collection Variables"""
# Controls default variables
MFC_P = [1,1,1,1,1]  
MFC_I = [0.0, 0.0, 0.0, 0.0, 0.0]  
MFC_D = [0.0, 0.0, 0.0, 0.0, 0.0]
tau = [0.5, 0.5, 0.5, 0.5, 0.5]  # Time constant for each MFC [sec]
MFC_ON = [1, 1, 0, 0, 0] # [1 = ON, 0 = OFF]
MFC_SETPOINT = [0.0, 0.0, 0.0, 0.0, 0.0]
MFC_RESPONSE = [0.0, 0.0, 0.0, 0.0, 0.0]
# Data plotting and saving variables
MFC_1SETPOINT_HISTORY = []  # 5 lists for 5 MFC's
MFC_1_RESPONSE_HISTORY = []  # 5 lists for 5 MFC's
MFC_TIME_HISTORY = []

PRESSURE_SENOR_1_HISTORY = []
PRESSURE_SENOR_2_HISTORY = []

"""UI Variables"""
STYLES = {
    "bg": "#f0f0f0",
    "panel_bg": "#d9d9d9",
    "text": "#000000",
    "button_bg": "#e0e0e0",
    "button_active_bg": "#c0c0c0",
    "terminal_bg": "#1e1e1e",
    "terminal_fg": "#d4d4d4"
}
valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4"]
test_columns = []
test_plan = []

"""Controls Variables"""
resolution = .2 # rate of controls loop [sec]

### Start main code
if __name__ == "__main__":

    # Create UI and Controls System objects, then link them
    Gas_Mixing_UI = UI_Object()
    cs = ControlSystem(resolution)
    dh = Data_Handler()
    
    Gas_Mixing_UI.cs = cs
    Gas_Mixing_UI.dh = dh
    dh.UI = Gas_Mixing_UI
    cs.UI = Gas_Mixing_UI
    dh.cs = cs
    cs.dh = dh

    # Start the UI main loop
    Gas_Mixing_UI.write_to_terminal("App started.")
    Gas_Mixing_UI.mainloop()

    # Start the Control System main loop
    cs.start()
    cs.set_state(1) # Set initial state to Idle
    Gas_Mixing_UI.update_indicators(name=Gas_Mixing_UI.indicators[0])  # Initialize state indicator


    cs.stop()