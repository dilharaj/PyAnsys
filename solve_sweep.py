import time
import os
import math
import numpy as np
import concurrent.futures
import ansys.fluent.core as pyfluent

def run_solve_sweep(variables, const, case_folder, id, RPM, Vinf):


    n_out = 11  # Number of outputs
    error_out = [-1.0] * n_out  # Error output 
    nproc_mesh = id.inputs.nproc_mesh  # Number of processors
    nproc_cfd = id.inputs.nproc_cfd  # Number of processors for CFD solver
    
    gui = id.inputs.gui # Use GUI for meshing and solver
    gui = True
    gpu_cfd = id.inputs.gpu_cfd  # Use GPU for CFD solver

    fluent_niter = id.inputs.fluent_niter  # Number of iterations
    fluent_nloops = id.inputs.fluent_nloops  # Number of loops tof thrust convergence

    file = open(f"{case_folder}\\mesh_info.txt","r")
    lines = file.readlines()
    file.close()
    success = int(lines[0].split()[0])
    mode = int(lines[0].split()[1])
    if success == 0:
        print("Meshing failed")
        exit()


    mesh_file = rf"{case_folder}\\mesh.msh.h5"

    solver = pyfluent.launch_fluent(
            precision="double",
            processor_count=nproc_cfd,
            mode="solver",
            version="3d",
            show_gui=gui,
            gpu=gpu_cfd
        )

    T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, Vinf_out, prop_eff = run_case_sweep(solver, variables, const, mesh_file, case_folder, fluent_niter, fluent_nloops, gpu_cfd, mode, id, RPM, Vinf)
        
    #input("Solver finished. Press Enter to exit...\n") 
    solver.exit()

    return T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, Vinf_out, prop_eff

def read_params(filename):
    params = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            params[key.strip()] = float(value.strip())

    return params



def run_case_sweep(solver,var,const,mesh_file,case_folder,niter_fluent,nloops,gpu_cfd,mode,id,RPM,Vinf):

    # runs simulation
    time0 = time.time()

    eps = 0.01 # convergence criteria
    temp = 288.15 # sea level
    niter_avg = 30 # average over n steps
    a0 = math.sqrt(1.4*287*temp)
    igpu = True

    
    nb = int(var[id.rnb])
    R = const[id.r]
 
    #input("Enter")
    print(mesh_file)
    solver.file.read_mesh(file_name=mesh_file)
    solver.mesh.check()

    # define material
    solver.setup.materials.fluid["air"] = {
        "density": {
            "option": "ideal-gas"
        },
    }

    # boundary conditions

    boundary_conditions = solver.setup.boundary_conditions
    

    boundary_conditions.wall['duct1'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['duct2'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['hub1'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['hub2'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }


    

    # report definitions
    if gpu_cfd:
        if mode == 1:
            solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "report_output_type": "Force"}
            solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "report_output_type": "Moment"}
        else:
            solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1"], "report_output_type": "Force"}
            solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "report_output_type": "Moment"}
            # solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            # solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "report_output_type": "Force"}
            # solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "report_output_type": "Moment"}

        solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "report_output_type": "Force"}
        solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "report_output_type": "Force"}
        
    else:
        if mode == 1:
            solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"]}
            solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
        else:    
            solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","duct1","duct2","hub1","hub2"]}
            solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
        
        solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True}
        solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "retain_instantaneous_values" : True}

    fname2 = f"{case_folder}\\torques.out"
    
    

    solver.solution.monitor.report_plots['total_thrust'] = {"print" : True, "report_defs" : ["total_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['blade_thrust'] = {"print" : True, "report_defs" : ["blade_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['duct_thrust'] = {"print" : True, "report_defs" : ["duct_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['hub_thrust'] = {"print" : True, "report_defs" : ["hub_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['torque'] = {"print" : True, "report_defs" : ["torque"], "plot_instantaneous_values" : True}

    # convergence criteria
     
    solver.tui.solve.monitors.residual.convergence_criteria(
        "1e-4","1e-4","1e-4","1e-4","1e-3","1e-4",
    )

    solver.tui.solve.monitors.residual.check_convergence("no","no","no","no","no","no","no")

    solver.solution.monitor.convergence_conditions = {"convergence_reports" : {"conv_thrust" : {"report_defs" : "total_thrust", "print" : True, "previous_values_to_consider" : niter_avg, "stop_criterion" : 0.001}}}
    solver.solution.monitor.convergence_conditions = {"convergence_reports" : {"conv_torque" : {"report_defs" : "torque", "print" : True, "previous_values_to_consider" : niter_avg, "stop_criterion" : 0.001}}}
    
    
    
    solver.setup.reference_values.compute(from_zone_type = "velocity-inlet", from_zone_name = "inlet", phase = "mixture")
    
    

    time1 = time.time()

    print(f"Solver configured in  {(time1-time0)/60} mins")

    #input("enter")
    # Run simulation
    solver.settings.solution.methods.p_v_coupling.flow_scheme = "Coupled"
    solver.settings.solution.methods.pseudo_time_method.formulation.coupled_solver = "global-time-step"
    #solver.tui.solve.set.p_v_coupling("24")
    #solver.tui.solve.set.pseudo_time_method.formulation("1")
    solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = "user-specified"
    
    #input("Initialization complete. Press Enter to start iterations...\n")

    A = math.pi * const[id.r]**2  # disk area
    sigma = var[id.dout_exp]    # duct outlet expansion ratio
    rho = const[id.rho]  # Air density at sea level (kg/m^3)

    ns_error = 0

    #input("Initialization complete. Press Enter to start iterations...\n")

    T_total_list = []
    T_blade_list = []
    T_duct_list = []
    T_hub_list = []
    Q_list = []
    FM_list = []
    omega_list = []
    P_list = []
    DL_list = []
    PL_list = []
    Vinf_list = []
    prop_eff_list = []

    
    icase = 0

    for rpm in RPM:
        for vinf in Vinf:
            
            icase += 1
            fname = rf"{case_folder}\\forces_{icase}.out"
            if os.path.exists(fname):
                os.remove(fname)
    
            solver.solution.monitor.report_files['forces'] = {"report_defs" : ["total_thrust","torque","blade_thrust","duct_thrust","hub_thrust"], "write_instantaneous_values" : True, "print" : True, "file_name": fname}
    
            omega = rpm*2*np.pi/60

            solver.settings.setup.cell_zone_conditions.fluid['nearbody'] = {
                "reference_frame" : {
                    "reference_frame_zone_motion_function" : "none", 
                    "reference_frame_axis_direction" : [0, 0, 1], 
                    "reference_frame_axis_origin" : [0., 0., 0.], 
                    "reference_frame_velocity" : [0., 0., 0.], 
                    "mrf_omega" : omega, 
                    "mrf_relative_to_thread" : "absolute", 
                    "frame_motion" : True
                }
            }

            boundary_conditions.velocity_inlet['inlet'] = {
                "momentum" : {
                    "flow_direction" : [0, 0, -1], 
                    "velocity" : {"value" : vinf}, 
                    "velocity_specification_method" : "Magnitude and Direction"
                },
                "thermal" : {
                    "temperature": {"value": temp}
                }
            }

            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = 1.5 * 1.0/omega  # 2.5 x dt
            #solver.tui.solve.set.pseudo_time_method.global_time_step_settings("no", f"{1/omega}")
            solver.solution.initialization.hybrid_initialize()

            #input("Press Enter to continue...\n")
    
            #input("Press Enter to continue to next loop...\n")
            solver.solution.run_calculation.iterate(iter_count=niter_fluent)
            T_total,T_blade,T_duct,T_hub,Q,convergence = read_force(fname,igpu,nb,ns_error,fname2)

            print(f"Full system numbers:\n    T_total = {T_total:.3f} N, T_blade = {T_blade:.3f} N, T_duct = {T_duct:.3f} N, T_hub = {T_hub:.3f} N, Q = {Q:.3f} Nm")
            
            #input("enter to continue")
            
            time2 = time.time()

            print(f"Simulation run in  {(time2-time1)/60} mins")

            if convergence == 0:
                print("Case did not converge")

            P = Q * omega
            if P != 0:
                if T_total>0:
                    power_loading = (T_total/9.81) / (P/1000) # kg/kW
                    disk_loading = T_total / 9.81 / A # disk loading in kg/m2
                    FM = T_total**1.5 / (P * math.sqrt(4 * rho * A * sigma))  # Figure of Merit
                    duct_share = T_duct / T_total * 100 if T_total != 0 else 0
                    prop_eff = T_total * vinf / P
                else:
                    power_loading = 0
                    disk_loading = 0
                    FM = 0
                    duct_share = 0
                    prop_eff = 0
                    
                print(f"Thrust: {T_total:.2f} N | Power: {P:.2f} W | Torque: {Q:.2f} Nm | RPM: {rpm:.2f} | Vinf: {vinf:.2f} | Duct Share: {duct_share:.1f}% | Disk Loading: {disk_loading:.2f} kg/m^2 | Power Loading: {power_loading:.2f} kg/kW | FM: {FM:.3f} | Prop Efficiency: {prop_eff*100:.2f}%")
            else:
                print("Thrust: Undefined | Power: Undefined | Torque: Undefined | RPM: Undefined | Duct Share: Undefined | Disk Loading: Undefined | Power Loading: Undefined | FM: Undefined")
            
            T_total_list.append(T_total)
            T_blade_list.append(T_blade)
            T_duct_list.append(T_duct)
            T_hub_list.append(T_hub)
            Q_list.append(Q)
            FM_list.append(FM)
            omega_list.append(omega)
            P_list.append(P)
            DL_list.append(disk_loading)
            PL_list.append(power_loading)
            Vinf_list.append(vinf)
            prop_eff_list.append(prop_eff)


            #input("Simulation complete. Press Enter to continue...\n")

    return T_total_list, T_blade_list, T_duct_list, T_hub_list, Q_list, omega_list, P_list, FM_list, DL_list, PL_list, Vinf_list, prop_eff_list

def read_force(file_path,igpu,nb,ns_error,file_torque):
    # Reads final forces and moments
    niter_avg = 30


    with open(file_path,"r") as file:
        lst = [line.strip().split() for line in file]

    niter_avg = min(niter_avg,len(lst)-3)


    
    if igpu:
        T_total = 0.0
        T_blade = 0.0
        T_duct = 0.0
        T_hub = 0.0
        Q = 0.0
        for j in range(niter_avg):
            T_total += float(lst[-niter_avg+j][1])/niter_avg
            Q += float(lst[-niter_avg+j][2])/niter_avg
            T_blade += float(lst[-niter_avg+j][3])/niter_avg
            T_duct += float(lst[-niter_avg+j][4])/niter_avg
            T_hub += float(lst[-niter_avg+j][5])/niter_avg
                    
    else:
        T_total = float(lst[-1][1])
        Q = float(lst[-1][3])
        T_blade = float(lst[-1][5])
        T_duct = float(lst[-1][7])
        T_hub = float(lst[-1][9])

    if ns_error == 1:
        with open(file_torque,"r") as file:
            lst2 = [line.strip().split() for line in file]
        if igpu:
            Q1 = 0.0
            Q2 = 0.0
            Q3 = 0.0
            Q4 = 0.0
            Q5 = 0.0
            for j in range(niter_avg):
                Q1 += float(lst2[-niter_avg+j][1])/niter_avg
                Q2 += float(lst2[-niter_avg+j][2])/niter_avg
                Q3 += float(lst2[-niter_avg+j][3])/niter_avg
                Q4 += float(lst2[-niter_avg+j][4])/niter_avg
                Q5 += float(lst2[-niter_avg+j][5])/niter_avg
                        
        else:
            Q1 = float(lst2[-1][1])
            Q2 = float(lst2[-1][3])
            Q3 = float(lst2[-1][5])
            Q4 = float(lst2[-1][7])
            Q5 = float(lst2[-1][9])
        Q = max(Q1,Q2,Q3,Q4,Q5)
        T_blade= 0
        T_duct = 0
        T_hub = 0

    print(f"\nSlice specific numbers:\n    Total Thrust: {T_total:.2f} N, Blade Thrust: {T_blade:.2f} N, Duct Thrust: {T_duct:.2f} N, Hub Thrust: {T_hub:.2f} N, Torque: {Q:.2f} Nm, Nb: {nb}")

    return T_total*nb,T_blade*nb,T_duct*nb,T_hub*nb,Q*nb,1


