import os
import sys
from classes import ID, Rotor, Input
from geometry import run_geo, run_geo_custom
from ansys.geometry.core import launch_modeler
import ansys.fluent.core as pyfluent
from mesh import run_mesh, make_mesh_cpu
from solve import run_solve
from solve_sweep import run_solve_sweep
from solve_cruise import run_solve_cruise
from tip_deflection import Rotor_structure, Elem, Str, structural_design
from post_process import post_process
from post_process import run_acoustics
import numpy as np
from pathlib import Path
import shutil
import copy
from utils import remove_file

"""
This is a script to run 3D slices of ducted rotors (no stator) in Ansys Fluent with GPU. 
Steps: 
1. Create a parent folder to house all sub cases and copy the input.yaml file to the parent folder.
2. Create the environment variable ACUM_EXECUTABLE_PATH using $env:ACUM_EXECUTABLE_PATH="path_to_acum_executable" in powershell. For example, if the acum executable is located at "Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/acum.exe", run the following command in powershell:
3. Run this script with the path to the input.yaml file as an argument. For example, if the input.yaml file is located at "Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/input.yaml", run the following command in the terminal:
python main.py Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/input.yaml

"""
A0 = 340 # speed of sound


def run_default(variables, const, case_folder,id,skip_acum,achieve_T_target):

    fout = Path(case_folder) / "results.csv"
    foutname = str(fout)
    if not os.path.exists(foutname):
        with open(foutname, "w") as f:
            f.write("blade_count,root_cutout,solidity,twist,theta75,air_thick_1,air_thick_2,air_thick_3,air_camber_1,air_camber_2,air_camber_3,AR_1,AR_2,AR_3,SW_1,SW_2,SW_3,dout_exp,din_exp,dlength,dwidth,Vinf,T_total,T_blade,T_duct,T_hub,Q,omega,RPM,P,FM,Prop_eff,Ytip,DL,PL,OF,Duct_Share,OASPL_A_max,OASPL_A_mean\n")

    with open(foutname, "r") as f:
        caseID = sum(1 for line in f)
    parent_folder = case_folder
    case_folder = os.path.join(case_folder,f"case{caseID}")
    if not os.path.exists(case_folder):
        os.makedirs(case_folder)
        shutil.copyfile(rf"{parent_folder}/inputs.yaml", rf"{case_folder}/inputs.yaml")

    
    script_file = run_geo(variables,const,case_folder,id)

    modeler = launch_modeler(mode='discovery')
    print(modeler)
    print("#### script file",script_file)

    result = modeler.run_discovery_script_file(file_path=script_file)

    modeler.close()

    mesh_file = run_mesh(variables, const, case_folder, id)


    T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, OF_out = run_solve(variables, const, case_folder, id, achieve_T_target)

    prop_eff = T_total * const[id.vinf] / P

    # Structural design
    from classes import Rotor
    rotor = Rotor(variables,const,id)
    crotor = Rotor_structure(variables[id.rnb], variables[id.rcout]*const[id.r], const[id.r], omega*60/(2*np.pi), T_blade)
    celem  = Elem(rotor.nr, rotor.r*rotor.R_tip, rotor.theta, rotor.chord)
    cstr   = Str(rotor.air_thick[0])

    # Code
    ytip, feas  = structural_design(crotor, celem, cstr)
    print("Tip deflection (mm):", ytip)
    OF = OF_out
    print("Objective Function:", OF)
    duct_share = T_duct/T_total

    mesh_file = rf"{case_folder}\\mesh.msh.h5"
    try:
        os.remove(mesh_file)
    except FileNotFoundError:
        pass
    except PermissionError:
        print("File is in use and cannot be deleted.")
    
    rpm = omega*60/(2*np.pi)
    mtip = omega*rotor.R_tip/A0
        
    print(f"Total Thrust: {T_total:.2f} N\nBlade Thrust: {T_blade:.2f} N\nDuct Thrust: {T_duct:.2f} N\nHub Thrust: {T_hub:.2f} N\nTorque: {Q:.2f} Nm\nRPM: {rpm:.2f} RPM\nMtip: {mtip}\nPower: {P:.2f} W\nFigure of Merit: {FM:.3f}\nDisk Loading: {DL:.2f} kg/m^2\nPower Loading: {PL:.2f} kg/kW\nPropulsive Efficiency: {prop_eff*100:.2f}%\nDuct Share: {duct_share*100:.2f}%")


     ## post-process

    post_process(rpm, const[id.r], case_folder, rotor.r, rotor.theta)
    
    if skip_acum == 0:
        mean_OASPL, mean_OASPL_A, max_OASPL, max_OASPL_A = run_acoustics(case_folder, omega, rotor.R_tip, rotor.Nb)
    else:
        mean_OASPL = 0
        mean_OASPL_A = 0
        max_OASPL = 0
        max_OASPL_A = 0


    ## Append to file

    
    while True:
        try:
            with open(foutname, "a") as f:
                f.write(f"{variables[id.rnb]},{variables[id.rcout]},{variables[id.rsolidity]},{variables[id.rtwist]},{variables[id.rtheta75]},{variables[id.rair_thick[0]]},{variables[id.rair_thick[1]]},{variables[id.rair_thick[2]]},"
                f"{variables[id.rair_camber[0]]},{variables[id.rair_camber[1]]},{variables[id.rair_camber[2]]},{variables[id.rtaper[0]]},{variables[id.rtaper[1]]},{variables[id.rtaper[2]]},{variables[id.rsweep[0]]},"
                f"{variables[id.rsweep[1]]},{variables[id.rsweep[2]]},{variables[id.dout_exp]},{variables[id.din_exp]},{variables[id.dlength]},{variables[id.dwidth]},{const[id.vinf]},{T_total},{T_blade},{T_duct},{T_hub},{Q},{omega},"
                f"{rpm},{P},{FM},{prop_eff},{ytip},{DL},{PL},{OF},{duct_share},{max_OASPL_A},{mean_OASPL_A}\n"
                )
            break
        except Exception as e:
            print(f"Error writing to file: {e}")
            input("Close output CSV file and Press Enter to save current varient...\n")




def run_oc_sweep(variables, const, case_folder, id, RPM, Vinf, input_geo_file):
    
    fout = Path(case_folder) / "results.csv"
    foutname = str(fout)

    i_run_geo = int(input("Do you need to (re)generate the geometry? (Yes=1, No=0): "))   
    i_make_mesh = int(input("Do you need to (re)generate the mesh? (Yes=1, No=0): ")) 

    if i_run_geo:
        script_file = run_geo_custom(case_folder, input_geo_file)

        modeler = launch_modeler(mode='discovery')
        print(modeler)

        #result = modeler.run_discovery_script_file(file_path=script_file)
        print(f"Discovery script written to {script_file}. \nDiscovery cannot automate named selections on custom geometries.\nPlease run the script in Ansys Discovery to create the geometry,\n add required named selections, save case.pmdb, then press Enter to continue.")
        input("Run the discovery script in Ansys Discovery, then press Enter to continue...\n")

        modeler.close()

    if i_make_mesh:
        mesh_file = run_mesh(variables, const, case_folder, id)


    T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, Vinf_list, prop_eff = run_solve_sweep(variables, const, case_folder, id, RPM=RPM, Vinf=Vinf)


        
    # if os.path.exists(foutname):
    #     os.remove(foutname)

    if not os.path.exists:
        with open(foutname, "w") as f:
            f.write("RPM,Vinf,T_total,T_blade,T_duct,T_hub,Q,omega,P,FM,DL,PL,Prop_Eff,Duct_Share\n")

    while True:
        try:
            with open(foutname, "a") as f:
                for i in range(len(T_total)):
                    f.write(f"{omega[i]*60/(2*np.pi):.2f},{Vinf_list[i]:.2f},{T_total[i]:.2f},{T_blade[i]:.2f},{T_duct[i]:.2f},{T_hub[i]:.2f},{Q[i]:.2f},{omega[i]:.2f},{P[i]:.2f},{FM[i]:.3f},{DL[i]:.2f},{PL[i]:.2f},{prop_eff[i]:.3f},{T_duct[i]/T_total[i]:.3f}\n")
            break
        except Exception as e:
            print(f"Error writing to file: {e}")
            input("Close output CSV file and Press Enter to save current varient...\n")


def run_cruise_sweep(variables, const, case_folder,id,skip_acum, RPM):

    skip_acum = 1 # overwrite

    fout = Path(case_folder) / "results.csv"
    foutname = str(fout)
    if not os.path.exists(foutname):
        with open(foutname, "w") as f:
            f.write("blade_count,root_cutout,solidity,twist,theta75,air_thick_1,air_thick_2,air_thick_3,air_camber_1,air_camber_2,air_camber_3,AR_1,AR_2,AR_3,SW_1,SW_2,SW_3,dout_exp,din_exp,dlength,dwidth,Vinf,T_total,T_blade,T_duct,T_hub,Q,omega,RPM,P,FM,Prop_eff,Ytip,DL,PL,OF,Duct_Share,OASPL_A_max,OASPL_A_mean\n")
    
    with open(foutname, "r") as f:
        caseID0 = sum(1 for line in f)

    #nvarients = 21*2+1
    nvarients = 1
    parent_folder = case_folder
    
    modeler = launch_modeler(mode='discovery')
    print(modeler)
    
    variables0 = copy.deepcopy(variables)

    for ivarient in range(nvarients):
        
        caseID = caseID0 + ivarient
        case_folder = os.path.join(parent_folder,f"case{caseID}")
        if not os.path.exists(case_folder):
            os.makedirs(case_folder)
            
        if ivarient > 0:
            if (ivarient-1) %2 ==0:
                variables[(ivarient-1)//2] *= 0.9
            else:
                variables[(ivarient-1)//2] *= 1.1
    
        script_file = run_geo(variables,const,case_folder,id)

        
        print("#### script file",script_file)

        result = modeler.run_discovery_script_file(file_path=script_file)

        variables = copy.deepcopy(variables0)


    modeler.close()

    for ivarient in range(nvarients):
        
        caseID = caseID0 + ivarient
        case_folder = os.path.join(parent_folder,f"case{caseID}")
            
        if ivarient > 0:
            if (ivarient-1) %2 ==0:
                variables[(ivarient-1)//2] *= 0.9
            else:
                variables[(ivarient-1)//2] *= 1.1
    
        mesh_file = run_mesh(variables, const, case_folder, id)


        T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, prop_eff = run_solve_cruise(variables, const, case_folder, id, RPM=RPM)


        # Structural design
        from classes import Rotor
        rotor = Rotor(variables,const,id)
        crotor = Rotor_structure(variables[id.rnb], variables[id.rcout]*const[id.r], const[id.r], omega*60/(2*np.pi), T_blade)
        celem  = Elem(rotor.nr, rotor.r*rotor.R_tip, rotor.theta, rotor.chord)
        cstr   = Str(rotor.air_thick[0])

        # Code
        ytip, feas  = structural_design(crotor, celem, cstr)
        print("Tip deflection (mm):", ytip)
        OF = P/T_total
        print("Objective Function:", OF)
        duct_share = T_duct/T_total

        mesh_file = rf"{case_folder}\\mesh.msh.h5"
        try:
            os.remove(mesh_file)
        except FileNotFoundError:
            pass
        except PermissionError:
            print("File is in use and cannot be deleted.")
        
        rpm = omega*60/(2*np.pi)
        mtip = omega*rotor.R_tip/A0
            
        print(f"Total Thrust: {T_total:.2f} N\nBlade Thrust: {T_blade:.2f} N\nDuct Thrust: {T_duct:.2f} N\nHub Thrust: {T_hub:.2f} N\nTorque: {Q:.2f} Nm\nRPM: {rpm:.2f} RPM\nMtip: {mtip}\nPower: {P:.2f} W\nFigure of Merit: {FM:.3f}\nDisk Loading: {DL:.2f} kg/m^2\nPower Loading: {PL:.2f} kg/kW\nPropulsive Efficiency: {prop_eff*100:.2f}%\nDuct Share: {duct_share*100:.2f}%")


        ## post-process

        post_process(rpm, const[id.r], case_folder, rotor.r, rotor.theta)
        
        if skip_acum == 0:
            mean_OASPL, mean_OASPL_A, max_OASPL, max_OASPL_A = run_acoustics(case_folder, omega, rotor.R_tip, rotor.Nb)
        else:
            mean_OASPL = 0
            mean_OASPL_A = 0
            max_OASPL = 0
            max_OASPL_A = 0


        ## Append to file

        
        while True:
            try:
                with open(foutname, "a") as f:
                    f.write(f"{variables[id.rnb]},{variables[id.rcout]},{variables[id.rsolidity]},{variables[id.rtwist]},{variables[id.rtheta75]},{variables[id.rair_thick[0]]},{variables[id.rair_thick[1]]},{variables[id.rair_thick[2]]},"
                    f"{variables[id.rair_camber[0]]},{variables[id.rair_camber[1]]},{variables[id.rair_camber[2]]},{variables[id.rtaper[0]]},{variables[id.rtaper[1]]},{variables[id.rtaper[2]]},{variables[id.rsweep[0]]},"
                    f"{variables[id.rsweep[1]]},{variables[id.rsweep[2]]},{variables[id.dout_exp]},{variables[id.din_exp]},{variables[id.dlength]},{variables[id.dwidth]},{const[id.vinf]},{T_total},{T_blade},{T_duct},{T_hub},{Q},{omega},"
                    f"{rpm},{P},{FM},{prop_eff},{ytip},{DL},{PL},{OF},{duct_share},{max_OASPL_A},{mean_OASPL_A}\n"
                    )
                break
            except Exception as e:
                print(f"Error writing to file: {e}")
                input("Close output CSV file and Press Enter to save current varient...\n")


        variables = copy.deepcopy(variables0)
        


def run_cpu(variables, const, case_folder,id,skip_acum,achieve_T_target):

    solver = None
    istator = 1 # cpu version is defined to run with stator
    fout = Path(case_folder) / "results.csv"
    foutname = str(fout)
    if not os.path.exists(foutname):
        with open(foutname, "w") as f:
            f.write("blade_count,root_cutout,solidity,twist,theta75,air_thick_1,air_thick_2,air_thick_3,"
            "air_camber_1,air_camber_2,air_camber_3,AR_1,AR_2,AR_3,SW_1,SW_2,SW_3,dout_exp,din_exp,dlength,dwidth,Vinf,hlength,"
            "s_blade_count,s_solidity,s_taper,s_twist,s_theta75,s_air_thick_1,s_air_thick_2,s_air_thick_3,s_air_cam_1,s_air_cam_2,s_air_cam_3,"
            "s_rake,s_clearance,T_total,T_blade,T_duct,T_hub,T_stator,Q,omega,RPM,P,FM,Prop_eff,Ytip,DL,PL,OF,Duct_Share,OASPL_A_max,OASPL_A_mean\n"
            )

    with open(foutname, "r") as f:
        caseID = sum(1 for line in f)
    parent_folder = case_folder
    case_folder = os.path.join(case_folder,f"case{caseID}")
    if not os.path.exists(case_folder):
        os.makedirs(case_folder)
        shutil.copyfile(rf"{parent_folder}/inputs.yaml", rf"{case_folder}/inputs.yaml")

    
    script_file, blade_lims, rotor, stator = run_geo(variables,const,case_folder,id,istator=1)
    
    modeler = launch_modeler(mode='discovery')
    print(modeler)
    print("#### script file",script_file)
    result = modeler.run_discovery_script_file(file_path=script_file)
    modeler.close()
    solver, mesh_file_near, mesh_file_off = make_mesh_cpu(variables, const, case_folder, id)


    T_total, T_blade, T_duct, T_hub, T_stator, Q, omega, P, FM, DL, PL, OF_out = run_solve(variables, const, case_folder, id, achieve_T_target, blade_lims, istator, solver)

    prop_eff = T_total * const[id.vinf] / P

    # Structural design
    crotor = Rotor_structure(variables[id.rnb], variables[id.rcout]*const[id.r], const[id.r], omega*60/(2*np.pi), T_blade)
    celem  = Elem(rotor.nr, rotor.r*rotor.R_tip, rotor.theta, rotor.chord)
    cstr   = Str(rotor.air_thick[0])

    # Code
    ytip, feas  = structural_design(crotor, celem, cstr)
    print("Tip deflection (mm):", ytip)
    OF = OF_out
    print("Objective Function:", OF)
    duct_share = T_duct/T_total
    
    rpm = omega*60/(2*np.pi)
    mtip = omega*rotor.R_tip/A0


    # mesh_file = rf"{case_folder}\\mesh.msh.h5"
    mesh_file_off = rf"{case_folder}\\mesh_off.msh.h5"
    mesh_file_near = rf"{case_folder}\\mesh_near.msh.h5"
    remove_file(mesh_file_near)
    remove_file(mesh_file_off)

    
        
    print(f"Total Thrust: {T_total:.2f} N\nBlade Thrust: {T_blade:.2f} N\nDuct Thrust: {T_duct:.2f} N\nHub Thrust: {T_hub:.2f} N\nStator Thrust: {T_stator:.2f} N\nTorque: {Q:.2f} Nm\nRPM: {rpm:.2f} RPM\nMtip: {mtip}\nPower: {P:.2f} W\nFigure of Merit: {FM:.3f}\nDisk Loading: {DL:.2f} kg/m^2\nPower Loading: {PL:.2f} kg/kW\nPropulsive Efficiency: {prop_eff*100:.2f}%\nDuct Share: {duct_share*100:.2f}%")


     ## post-process


    post_process(rpm, const[id.r], case_folder, rotor.r, rotor.theta, istator, stator.r, stator.theta)
    
    if skip_acum == 0:
        mean_OASPL, mean_OASPL_A, max_OASPL, max_OASPL_A = run_acoustics(case_folder, omega, rotor.R_tip, rotor.Nb)
    else:
        mean_OASPL = 0
        mean_OASPL_A = 0
        max_OASPL = 0
        max_OASPL_A = 0


    ## Append to file

    while True:
        try:
            with open(foutname, "a") as f:
                f.write(f"{variables[id.rnb]},{variables[id.rcout]},{variables[id.rsolidity]},{variables[id.rtwist]},{variables[id.rtheta75]},{variables[id.rair_thick[0]]},{variables[id.rair_thick[1]]},{variables[id.rair_thick[2]]},"
                f"{variables[id.rair_camber[0]]},{variables[id.rair_camber[1]]},{variables[id.rair_camber[2]]},{variables[id.rtaper[0]]},{variables[id.rtaper[1]]},{variables[id.rtaper[2]]},{variables[id.rsweep[0]]},"
                f"{variables[id.rsweep[1]]},{variables[id.rsweep[2]]},{variables[id.dout_exp]},{variables[id.din_exp]},{variables[id.dlength]},{variables[id.dwidth]},{const[id.vinf]},{variables[id.hlength]},"
                f"{variables[id.snb]},{variables[id.ssolidity]},{variables[id.staper]},{variables[id.stwist]},{variables[id.stheta75]},{variables[id.sair_thick[0]]},{variables[id.sair_thick[1]]},{variables[id.sair_thick[2]]},"
                f"{variables[id.sair_camber[0]]},{variables[id.sair_camber[1]]},{variables[id.sair_camber[2]]},{variables[id.srake]},{variables[id.sclear]},{T_total:.1f},{T_blade:.1f},{T_duct:.1f},{T_hub:.1f},{T_stator:.1f},{Q:.1f},{omega:.1f},"
                f"{rpm:.1f},{P:.1f},{FM:.3f},{prop_eff:.3f},{ytip:.1f},{DL:.1f},{PL:.2f},{OF:.1f},{duct_share:.3f},{max_OASPL_A:.1f},{mean_OASPL_A:.1f}\n"
                )
            break
        except Exception as e:
            print(f"Error writing to file: {e}")
            input("Close output CSV file and Press Enter to save current varient...\n")


