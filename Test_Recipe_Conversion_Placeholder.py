import pandas as pd
import numpy as np
from tkinter import Tk, filedialog

def load_and_interpolate_excel(self,resolution=0.1):        
        # Hide the tkinter root window
        root = Tk()
        root.withdraw()

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Excel File",filetypes=[("Excel files", "*.xlsx *.xls")])

        if not file_path:
            self.write_to_terminal("No file selected.")
            return None, None


        # Load the Excel file
        df = pd.read_excel(file_path)

        ## Check test file validity
        # ---- 1. Check column titles ----
        if not all(title in valid_titles for title in df.columns):
            print("Error: One or more column titles are invalid. "
                f"Expected only these: {valid_titles}")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 2. Check for empty cells ----
        if df.isnull().values.any():
            print("Error: The file contains empty cells. "
                "Please fill or remove missing data before loading.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 3. Ensure numeric data in main columns (excluding first column) ----
        for col in df.columns[1:]:
            if not pd.to_numeric(df[col], errors='coerce').notna().all():
                print(f"Error: Non-numeric values found in data column '{col}'.")
                return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 4. Check that time values are numeric ----
        time = pd.to_numeric(df.iloc[:, 0], errors='coerce')
        if not time.notna().all():
            print("Error: Time column contains non-numeric or missing values.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 5. Check that time values are strictly increasing ----
        if not all(np.diff(time) > 0):
            print("Error: Time values are not strictly increasing.")
            return df.columns.tolist(), [[0] * len(df.columns)]
        # ---- 6. Check that time values do not exceed 3600 seconds ----
        if time.max() > 3600:
            print(f"Error: Time values exceed 3600 seconds (found max={time.max():.2f}).")
            return df.columns.tolist(), [[0] * len(df.columns)]


        # Extract column titles
        column_titles = df.columns.tolist()
        # Ensure first column is numeric time data
        time = pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna().to_numpy()
        start_t, end_t = time[0], time[-1]
        # Generate new time vector with desired resolution
        new_time = np.arange(start_t, end_t + resolution, resolution)

        # Interpolate remaining columns
        interpolated_data = [new_time.tolist()]  # first column is time
        for col in df.columns[1:]:
            y = pd.to_numeric(df[col], errors='coerce').to_numpy()
            valid = ~np.isnan(y)
            interp_y = np.interp(new_time, time[valid], y[valid])
            interpolated_data.append(interp_y.tolist())

        # Replace original first column title with the same
        print(f"Interpolated data from {start_t:.2f}s to {end_t:.2f}s at {resolution:.1f}s resolution.")
        print(f"Columns: {', '.join(column_titles)}")
        test_columns = column_titles
        test_plan = interpolated_data

def convert_testplan_to_MFC_flows():
    load_and_interpolate_excel() # load in and populate test_columns and test_plan variables
    ############## YOUR CODE HERE

    ### NOT READY YET

    ##############
    print(test_plan)
    print(test_columns)




valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4"]
test_columns = []
test_plan = []
