import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from pathlib import Path  
import os   

#results_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_oc_sweep\results.csv"
#results_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_varients\case1_straight_duct\results.csv"
#results_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_varients\case2_converging_duct\results.csv"
results_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_varients\case3_thin_conv_duct\results.csv"

fp = Path(results_file)
plot_dir = fp.parent / "plots"
if not plot_dir.exists():
    plot_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(results_file)
#df.to_csv(results_file, index=False)

# Pivot or reshape the data into a grid for contour plotting
# X-axis could be Vinf, Y-axis could be RPM, or vice-versa. 
# Usually contour plots require a 2D meshgrid.
vinf_unique = np.sort(df['Vinf'].unique())
rpm_unique = np.sort(df['RPM'].unique())

X, Y = np.meshgrid(vinf_unique, rpm_unique)

print("X shape:", X.shape)
print("Y shape:", Y.shape)


df['Duct_Share'] = df['Duct_Share'].clip(lower=0)
df['Prop_Eff'] = df['Prop_Eff'].clip(lower=0)
df['PL'] = df['PL'].clip(lower=0)
df['DL'] = df['DL'].clip(lower=0)
df.loc[df['T_total'] < 0, 'DL'] = 0.0
df.loc[df['T_total'] < 0, 'PL'] = 0.0
df.loc[df['T_total'] < 0, 'Duct_Share'] = 0.0
df.loc[df['T_total'] < 0, 'Prop_Eff'] = 0.0

column_mapping = {
    "T_total": "Total Thrust",
    "T_blade": "Blade Thrust",
    "T_duct": "Duct Thrust",
    "T_hub": "Hub Thrust",
    "P": "Power",
    "DL": "Disk Loading",
    "PL": "Power Loading",
    "Prop_Eff": "Propulsive Efficiency",
    "Duct_Share": "Duct Share",
}
df = df.rename(columns=column_mapping)

df["Power"] = df["Power"] / 1000.0
df["Propulsive Efficiency"] = df["Propulsive Efficiency"] * 100.0
df["Duct Share"] = df["Duct Share"] * 100.0
df["Total Thrust (lb)"] = df["Total Thrust"] * 0.2248089431 
df["Vinf (mph)"] = df["Vinf"] * 2.23694

variables = [col for col in df.columns if col not in ['RPM', 'Vinf']]

label = ["Total Thrust [N]","Blade Thrust [N]","Duct Thrust [N]","Hub Thrust [N]","Torque [Nm]","omega [rad/s]","Power [kW]","Figure of Merit","Disk Loading [kg/m2]","Power Loading [kg/kW]","Propulsive Efficiency %","Duct Share %","Total Thrust [lb]","Forward Speed [mph]"]

i = 0
for var in variables:
    df[var] = pd.to_numeric(df[var], errors='coerce')
    df[var] = df[var].fillna(0)
    Z = df[var].values.reshape(len(rpm_unique), len(vinf_unique))
    fig, ax = plt.subplots()
    cp = ax.contourf(X, Y, Z, cmap='viridis')
    fig.colorbar(cp, ax=ax, label=label[i])
    ax.set_xlabel('Forward Speed (m/s)')
    ax.set_ylabel('RPM')
    ax.set_title(f'Contour Plot of {var}')
    fig.tight_layout()
    plt.show()
    fig.savefig(os.path.join(plot_dir,f"contour_{var}.png"))
    plt.close(fig)
    i += 1


x = df["Vinf (mph)"]
y = df["Total Thrust (lb)"]
z1 = df["Propulsive Efficiency"]
z2 = df["Power"]

n = 200
xi = np.linspace(x.min(), x.max(), n)
yi = np.linspace(y.min(), y.max(), n)
xi, yi = np.meshgrid(xi, yi)

xi_scaled = (xi - x.min()) / (x.max() - x.min())
yi_scaled = (yi - y.min()) / (y.max() - y.min())
x_scaled = (x - x.min()) / (x.max() - x.min())
y_scaled = (y - y.min()) / (y.max() - y.min())
zi1 = griddata((x_scaled, y_scaled), z1, (xi_scaled, yi_scaled), method="linear")
zi2 = griddata((x_scaled, y_scaled), z2, (xi_scaled, yi_scaled), method="linear")
            



fig, ax = plt.subplots(figsize=(8, 6))
# Create filled contour plot for unstructured points
contour_tri = ax.contourf(xi, yi, zi1, levels=20, cmap='viridis')

# Add a colorbar to show the scale of Z
fig.colorbar(contour_tri, ax=ax, label='Propulsive Efficiency')

# Labeling and styling
ax.set_title('Propulsive Efficiency')
ax.set_xlabel('Forward Speed (mph)')
ax.set_ylabel('Thrust (lb)')

# Dynamic qualitative colormap to ensure unique colors per sweep
cmap_rpm = plt.get_cmap('tab20')

# 2. Plot lines and points categorized by RPM
for i, rpm in enumerate(rpm_unique):
    # Filter for rows matching the current RPM step
    mask = df["RPM"] == rpm
    df_sweep = df[mask].sort_values(by="Vinf (mph)")  # Sorted by speed to prevent criss-crossed lines
    
    rpm_color = cmap_rpm(i % 20) 
    
    # Draw the continuous operating line
    ax.plot(
        df_sweep["Vinf (mph)"], 
        df_sweep["Total Thrust (lb)"], 
        color=rpm_color, 
        linestyle='-', 
        linewidth=1.5, 
        alpha=0.8,       # Slightly transparent line so underlying contour gradients remain visible
        zorder=2         # Placed below the circles but above the contour fill
    )
    
    # Draw the specific sweep data points (only label the scatter to avoid double entries in the legend)
    ax.scatter(
        df_sweep["Vinf (mph)"], 
        df_sweep["Total Thrust (lb)"], 
        color=rpm_color, 
        marker='o', 
        s=35, 
        edgecolor='black', 
        linewidth=0.5, 
        zorder=3,        # Sits on top of the connection line
        label=f'{int(rpm)} RPM'
    )

# 3. Add the legend outside the plot box next to the colorbar
ax.legend(
    title="Operating Sweeps", 
    loc='upper left', 
    bbox_to_anchor=(1.35, 1.0), 
    frameon=True, 
    shadow=True
)
# Adjust layout and save image
plt.tight_layout()
plt.show()



## Power  ################################################



fig, ax = plt.subplots(figsize=(8, 6))
# Create filled contour plot for unstructured points
contour_tri = ax.contourf(xi, yi, zi2, levels=20, cmap='viridis')

# Add a colorbar to show the scale of Z
fig.colorbar(contour_tri, ax=ax, label='Power [kW]')

# Labeling and styling
ax.set_title('Power (kW)')
ax.set_xlabel('Forward Speed (mph)')
ax.set_ylabel('Thrust (lb)')

# Dynamic qualitative colormap to ensure unique colors per sweep
cmap_rpm = plt.get_cmap('tab20')

# 2. Plot lines and points categorized by RPM
for i, rpm in enumerate(rpm_unique):
    # Filter for rows matching the current RPM step
    mask = df["RPM"] == rpm
    df_sweep = df[mask].sort_values(by="Vinf (mph)")  # Sorted by speed to prevent criss-crossed lines
    
    rpm_color = cmap_rpm(i % 20) 
    
    # Draw the continuous operating line
    ax.plot(
        df_sweep["Vinf (mph)"], 
        df_sweep["Total Thrust (lb)"], 
        color=rpm_color, 
        linestyle='-', 
        linewidth=1.5, 
        alpha=0.8,       # Slightly transparent line so underlying contour gradients remain visible
        zorder=2         # Placed below the circles but above the contour fill
    )
    
    # Draw the specific sweep data points (only label the scatter to avoid double entries in the legend)
    ax.scatter(
        df_sweep["Vinf (mph)"], 
        df_sweep["Total Thrust (lb)"], 
        color=rpm_color, 
        marker='o', 
        s=35, 
        edgecolor='black', 
        linewidth=0.5, 
        zorder=3,        # Sits on top of the connection line
        label=f'{int(rpm)} RPM'
    )

# 3. Add the legend outside the plot box next to the colorbar
ax.legend(
    title="Operating Sweeps", 
    loc='upper left', 
    bbox_to_anchor=(1.35, 1.0), 
    frameon=True, 
    shadow=True
)
# Adjust layout and save image
plt.tight_layout()
plt.show()
