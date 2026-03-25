### Synthetic Battery Gas Generation System for Fire and Explosion Testing
# Jensen Hughes VT ME Senior Design Project, Fall 2025-Spring 2026
#
# VT Senior Design Team 108 Members:
# Devin Gerdes - Code, Team Lead/Project Manager
# Emma Watson - Hardware and Testing Planner, Controls Team
# Clay Mercer - Controls Hardware, Controls Team
# Aidan Hounshell - Safety Expert, Mechanical Design, and Fabrication, Mechanical Team
# Gerard (Gary) Resulaj - Mechanical Design and Fabrication, Mechanical Team
# Remy Nioche - CAD and Fabrication, Mechanical Team
#
# Graduated Spring 2026, Virginia Tech, Mechanical Engineering
#
# Primarily coded by Devin Gerdes
# Test plan conversion coded by Emma Watson
# 


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
    Gas_Mixing_UI.write_to_terminal("Number of MFCs: " + str(dh.num_mfcs) + "\n MAKE SURE THIS IS CORRECT")


    # Start the Control System main loop
    cs.start()
    Gas_Mixing_UI.update_indicators(Gas_Mixing_UI.indicators[0])  # Initialize state indicator

    Gas_Mixing_UI.mainloop()

