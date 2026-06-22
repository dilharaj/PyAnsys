from run import run_default, run_oc_sweep, run_cruise_sweep, run_cpu
import os
import sys
import argparse
from pathlib import Path
from classes import ID, Rotor, Input


#Use the latest pyansys installation or "& c:\Users\TRServer02\.ansys_python_venvs\optislang_python_3_10_16\Scripts\python.exe .\main.py <path-to-inputs.yaml>" on the TR-server-2 to run the CPU version(mode=3) (Mixing plane definition)

if __name__ == "__main__":


    mode = 3 # 0=default mode; 1=operating conditions sweep, geometry defined in a STEP file; 2= cruise optimization with 5% tweak in variables; 3= simulation with stator (CPU)
    
    
    skip_acum = 1 # skip acoustics
    achieve_T_target = 0 # trim to target thrust or not

    parser = argparse.ArgumentParser(description="Process a YAML configuration file.")
    
    # Define the yaml file argument
    parser.add_str_arg = parser.add_argument(
        "config", 
        type=str, 
        help="Path to the input YAML file"
    )
    
    args = parser.parse_args()

    if not args.config:
        parser.error("No YAML file path provided. Usage: python main.py <path_to_yaml>")

    config_path = Path(args.config)
    parent_folder = config_path.parent
    case_folder = parent_folder #os.path.join(parent_folder, "general_case")

    if not os.path.exists(case_folder):
        os.makedirs(case_folder)

    print(args.config)
    #try:
    inputs = Input(args.config)
    id = ID(inputs)
    variables = id.vmin
    const = id.const

    
    if mode == 0: 
        run_default(variables, const, case_folder, id, skip_acum, achieve_T_target)

    elif mode == 1: # operating conditions sweep
        
        ####################################
        # Configure inputs
        ####################################
        R_tip = 0.15
        duct_outlet_expansion = 0.9184
        density = 1.225

        #RPM = [2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        #RPM = [8500, 9000, 9500, 10000, 10500, 11000, 11500, 12000, 12500, 13000, 13500, 14000]
        #Vinf = [72]
        RPM = [10724]
        Vinf = [113]
        
        #Vinf = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        #input_geo_file = rf"{case_folder}\geometry.STEP"
        #input_geo_file = rf"Z:\UFX_dilhara\Ansys\tempest-2\case60\case60_noStator.STEP"
        #input_geo_file = rf"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_varients\case1_straight_duct\case1.STEP"
        #input_geo_file = rf"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx600_varients\case2_converging_duct\case2.STEP"
        input_geo_file = rf"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\tx1200_c76\case76.STEP"
        
        ################################

        const[id.r] = R_tip
        variables[id.dout_exp] = duct_outlet_expansion
        const[id.rho] = density
        



        run_oc_sweep(variables, const, case_folder, id, RPM, Vinf, input_geo_file)

    # except Exception as e:
    #     print(f"Error1: {e}")
    #     sys.exit(1)

    elif mode == 2: # cruise optimization sweep
        
        
        RPM = [7000, 9000, 11000, 13000, 15000]
        
        ################################

        run_cruise_sweep(variables, const, case_folder, id, skip_acum, RPM)


    elif mode == 3: # CPU simulation with stator

        run_cpu(variables, const, case_folder, id, skip_acum, achieve_T_target)


