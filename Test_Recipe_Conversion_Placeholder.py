import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

def load_and_interpolate_excel(resolution=0.1):  
    global test_columns,test_plan
    # Open file dialog
    file_path = os.getcwd() + R"\Example_Test_Recipe.xlsx"
    print(file_path)
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
        print(f"Error: Time values exceed 3600 seconds (found max1={time.max1():.2f}).")
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


def plot_test_data(title, y1_title):
    global test_columns, test_plan
    if not test_columns or not test_plan:
        print("No data to plot.")
        return
    
    # Convert list of lists to columns
    
    fig, ax1 = plt.subplots() 
    
    if not test_columns or not test_plan or len(test_plan) < 2:
        ax1.text(0.5, 0.5, "No Test Plan Loaded", color="gray",
                ha="center", va="center", transform=ax1.transax1es)
    else:
        time_data = test_plan[0]
        n_cols = len(test_columns)
        for i, col_name in enumerate(test_columns[1:], start=1):
            if i == 6:
                continue
            y_data = test_plan[i]
            ax1.plot(time_data, y_data, label=col_name)
        ax1.set_ylim([0, 1])
        ax1.set_title(title)
        ax1.set_xlabel(test_columns[0])
        ax1.set_ylabel(y1_title)

        if n_cols > 6:
            ax12 = ax1.twinx()
            y_data_secondary = test_plan[6]
            ax12.plot(time_data, y_data_secondary, color="orange", label=test_columns[6])
            ax12.set_ylabel("Heat Release Rate")
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax12.get_legend_handles_labels()
            ax12.legend(lines1 + lines2, labels1 + labels2,
                    loc="upper right", fontsize=6, frameon=False)
        else:
            ax1.legend(loc="upper right", fontsize=6, frameon=False)
    
    plt.show()




def convert_testplan_to_MFC_flows():
    global test_plan,test_columns
    load_and_interpolate_excel() # load in and populate test_columns and test_plan variables
    plot_test_data("User Graph","Percent of Composition") # What the user will see
    ############## YOUR CODE HERE
    # May want to convert test_plan to columns rather than current format
    # data = list(zip(*test_plan)) # [time, var1, var2, var3, ...]
    # time = data[0]



    test_plan = []
    y1_title = "Mass Flow Rate" # For example. Whatever you want the mfc to do.
    ##############
    plot_test_data("Converted Recipe",y1_title) # Plot the values the MFC's will see
    print(test_columns)
    print(test_plan)




valid_titles = ["Time (s)","Heat Release Rate (kW)", "H2", "O2", "N2", "CO2", "CH4"]
test_columns = [] # [Title1,Title2,Title3,...]
test_plan = [] # [[Time1, Val1.1, Val2.1, ...], [Time2, Val1.2, Val2.2,...], ...]
convert_testplan_to_MFC_flows()