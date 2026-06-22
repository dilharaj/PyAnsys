
import time
import os
import math
import numpy as np
import concurrent.futures
import ansys.fluent.core as pyfluent

def run_solve(variables, const, case_folder, id, achieve_T_target, blade_lims, istator=False, solver=None):


    n_out = 12  # Number of outputs
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
    
    if istator:
        gpu_cfd = 0 # CPU only for stator sims
        out_file_near = f"{case_folder}\\mesh_near.msh.h5"
        out_file_off = f"{case_folder}\\mesh_off.msh.h5"
    else: 
        out_file = rf"{case_folder}\\mesh.msh.h5"

    if solver == None:
        solver = pyfluent.launch_fluent(
                precision="double",
                processor_count=nproc_cfd,
                mode="solver",
                version="3d",
                show_gui=gui,
                gpu=gpu_cfd
            )
        if istator:
            solver.file.read_mesh(file_name=out_file_off)
            solver.mesh.modify_zones.append_mesh(file_name=out_file_near)
        else:   
            solver.file.read_mesh(file_name=out_file)
    else:
        if istator:
            solver.mesh.modify_zones.append_mesh(file_name=out_file_near)
        else:   
            solver.file.read_mesh(file_name=out_file)


    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_case, solver, variables, const, case_folder, fluent_niter, fluent_nloops, gpu_cfd, mode, id, achieve_T_target, blade_lims, istator)
        try:
            T_total, T_blade, T_duct, T_hub, T_stator, Q, omega, P, FM, DL, PL, OF_out = future.result(timeout=12000) # Wait for up to 200 minutes
        except Exception as e:
            print(f"Error in solver execution: {e}")
            solver.exit()
            return [3 * x for x in error_out]  # Return error output
 
    #input("Solver finished. Press Enter to exit...\n") 
    solver.exit()

    return T_total, T_blade, T_duct, T_hub, T_stator, Q, omega, P, FM, DL, PL, OF_out

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



def run_case(solver,var,const,case_folder,niter_fluent,nloops,gpu_cfd,mode,id,achieve_T_target, blade_lims, istator=False):


    
    # runs simulation
    time0 = time.time()

    eps = 0.01 # convergence criteria
    temp = 288.15 # sea level
    niter_avg = 30 # average over n steps
    a0 = math.sqrt(1.4*287*temp)
    
    
    vinf = const[id.vinf]
    omega = const[id.rpm]*2*np.pi/60
    nb = int(var[id.rnb])
    if istator:
        snb = int(var[id.snb])
    else:
        snb = 0
    T_target = const[id.thrust]
    print("Target Thrust:",T_target)
    print(const)
    R = const[id.r]
 
   
    # define material
    solver.setup.materials.fluid["air"] = {
        "density": {
            "option": "ideal-gas"
        },
    }

    # input("check")
    # boundary conditions

    boundary_conditions = solver.setup.boundary_conditions
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

    boundary_conditions.wall['duct1'] = {
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


    if not istator:
        boundary_conditions.wall['duct2'] = {
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
           
        solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "report_output_type": "Force"}
        solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "report_output_type": "Force"}
        
    else:
        if mode == 1:
            if istator:
                solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade","duct1","duct2","hub1","hub2","stator"]}
                solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade"], "retain_instantaneous_values" : True}
                solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}

            else:
                solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"]}
                solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True}
                solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
        else:    
            if istator:
                solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade","duct1","duct2","hub1","hub2","stator"]}
                solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade"], "retain_instantaneous_values" : True}
                solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
            else:
                solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","duct1","duct2","hub1","hub2"]}
                solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1"], "retain_instantaneous_values" : True}
                solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
            
        if istator:
            solver.solution.report_definitions.force['rotary_duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.force['rotary_hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["hub1"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.force['stationary_duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct2"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.force['stationary_hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["hub2"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.force['stator_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["stator"], "retain_instantaneous_values" : True}
        else:
            solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "retain_instantaneous_values" : True}

    fname = f"{case_folder}\\forces.out"
    fname2 = f"{case_folder}\\torques.out"
    
    if os.path.exists(fname):
        os.remove(fname)

    if istator:
        solver.solution.monitor.report_files['forces'] = {"report_defs" : ["total_thrust","torque","blade_thrust","rotary_duct_thrust","rotary_hub_thrust","stationary_duct_thrust","stationary_hub_thrust","stator_thrust"], "write_instantaneous_values" : True, "print" : True, "file_name": fname}
        solver.solution.monitor.report_plots['total_thrust'] = {"print" : True, "report_defs" : ["total_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['blade_thrust'] = {"print" : True, "report_defs" : ["blade_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['rotary_duct_thrust'] = {"print" : True, "report_defs" : ["rotary_duct_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['rotary_hub_thrust'] = {"print" : True, "report_defs" : ["rotary_hub_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['stationary_duct_thrust'] = {"print" : True, "report_defs" : ["stationary_duct_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['stationary_hub_thrust'] = {"print" : True, "report_defs" : ["stationary_hub_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['stator_thrust'] = {"print" : True, "report_defs" : ["stator_thrust"], "plot_instantaneous_values" : True}
        solver.solution.monitor.report_plots['torque'] = {"print" : True, "report_defs" : ["torque"], "plot_instantaneous_values" : True}
    else:
        solver.solution.monitor.report_files['forces'] = {"report_defs" : ["total_thrust","torque","blade_thrust","duct_thrust","hub_thrust"], "write_instantaneous_values" : True, "print" : True, "file_name": fname}
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

    print(f"Solver configured in  {(time1-time0)/60:.1f} mins")


    if istator:
        solver.settings.setup.cell_zone_conditions.fluid['nested'] = {
            "reference_frame" : {
                "reference_frame_axis_direction" : [0, 0, 1], 
                "reference_frame_axis_origin" : [0., 0., 0.], 
            }
        }
        
        solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_nested'], new_type = 'interface')
        solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_nested'], new_type = 'interface')
        solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_near'], new_type = 'interface')
        solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_near'], new_type = 'interface')

        
        solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['nested-offbody'], new_type = 'interior')
        
        solver.settings.setup.turbo_models.enabled = True

        interface1 = ( 
            solver.settings.setup.mesh_interfaces.turbo_create.create(
                adjacent_cell_zone_1="nested",
                adjacent_cell_zone_2="nearbody",
                mesh_interface_name="s1",
                turbo_choice="Mixing-Plane",
                zone1="interface_down_nested",
                zone2="interface_down_near",
            )
        )
        interface2 = (
            solver.settings.setup.mesh_interfaces.turbo_create.create(
                adjacent_cell_zone_1="nested",
                adjacent_cell_zone_2="nearbody",
                mesh_interface_name="s2",
                turbo_choice="Mixing-Plane",
                zone1="interface_up_nested",
                zone2="interface_up_near",
            )
        )

        


    # Run simulation
    solver.settings.solution.methods.p_v_coupling.flow_scheme = "Coupled"
    solver.settings.solution.methods.pseudo_time_method.formulation.coupled_solver = "global-time-step"
    #solver.tui.solve.set.p_v_coupling("24")
    #solver.tui.solve.set.pseudo_time_method.formulation("1")
    solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = "user-specified"
    solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = 1.5 * 1.0/omega  # 2.5 x dt
    #solver.tui.solve.set.pseudo_time_method.global_time_step_settings("no", f"{1/omega}")
    
    solver.mesh.check()

    solver.solution.initialization.hybrid_initialize()
 
    #input("Initialization complete. Press Enter to start iterations...\n")

    A = math.pi * const[id.r]**2  # disk area
    sigma = var[id.dout_exp]    # duct outlet expansion ratio
    rho = const[id.rho]  # Air density at sea level (kg/m^3)

    ns_error = 0

    #input("Initialization complete. Press Enter to start iterations...\n")

    if achieve_T_target:
        Error = 1.0
        iter = 0
        while Error > eps:
            if iter >= nloops:
                break
            
            #input("Press Enter to continue to next loop...\n")
            solver.solution.run_calculation.iterate(iter_count=niter_fluent)
            if istator:
                T_total,T_blade,T_duct,T_hub,T_stator,Q,convergence = read_force_stator(fname,nb,snb)
            else:
                T_total,T_blade,T_duct,T_hub,Q,convergence = read_force(fname,gpu_cfd,nb,ns_error,fname2)
                T_stator = 0
            
            
            print(f"CFD iteration {iter+1} of {3} with omega = {omega:.3f} rad/s")
            print(f"    T_target = {T_target:.3f}N, T_total = {T_total:.3f} N, T_blade = {T_blade:.3f} N, T_duct = {T_duct:.3f} N, T_hub = {T_hub:.3f} N, T_stator = {T_stator:.3f} N, Q = {Q:.3f} Nm")
            
            if iter == 0:
                niter_fluent /= 2

            iter += 1
            
            omega_new = math.sqrt(abs(T_target/T_total)) * omega

            Error = abs((omega_new - omega)/omega)
            
            print(f"    Error = {Error:.3f}, omega_new = {omega_new:.3f} rad/s")
            
            FM = T_total**1.5 / (Q*omega * math.sqrt(4 * rho * A * sigma))  # Figure of Merit
        
            if FM > 1.1:
                if istator:
                    raise ValueError("FM > 1 not defined for stator simulations")
                # Apparently Discovery screws up the named selections (temporary fix)
                if gpu_cfd:
                    if mode == 1:
                        solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
                        solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "report_output_type": "Force"}
                        solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "report_output_type": "Force"}
                    else:
                        solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
                        solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "report_output_type": "Force"}
                        solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "report_output_type": "Force"}

                    solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "report_output_type": "Force"}
                    solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1","duct2"], "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque1'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "report_output_type": "Moment"}
                    if mode==1:
                        solver.solution.report_definitions.moment['torque2'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade2"], "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque3'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1"], "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque4'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct2"], "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque5'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["hub1","hub2"], "report_output_type": "Moment"}
                    
                else:
                    if mode == 1:
                        solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"]}
                        solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "retain_instantaneous_values" : True}
                        solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "retain_instantaneous_values" : True}
                    else:
                        solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","duct1","duct2","hub1","hub2"]}
                        solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "retain_instantaneous_values" : True}
                        solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "retain_instantaneous_values" : True}
                        
                    solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True}
                    solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque1'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    if mode == 1:
                        solver.solution.report_definitions.moment['torque2'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque3'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque4'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    solver.solution.report_definitions.moment['torque5'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["hub1","hub2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                    


                solver.solution.monitor.report_files['forces'] = {"report_defs" : ["torque1","torque2","torque3","torque4","torque5"], "write_instantaneous_values" : True, "print" : True, "file_name": fname2}
                ns_error = 1
                Error = 1.0
                print("Changing named selections to fix Discovery issue")

            omega = omega_new
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = 1.0/omega*1.5
            solver.settings.setup.cell_zone_conditions.fluid['nearbody'] = {
            "reference_frame" : {
                "mrf_omega" : omega, 
            }
            }

    else: # no trim
        solver.solution.run_calculation.iterate(iter_count=niter_fluent)
        if istator:
                T_total,T_blade,T_duct,T_hub,T_stator,Q,convergence = read_force_stator(fname,nb,snb)
        else:
            T_total,T_blade,T_duct,T_hub,Q,convergence = read_force(fname,gpu_cfd,nb,ns_error,fname2)
            T_stator = 0
    
        print(f"    T_target = {T_target:.2f}N, T_total = {T_total:.2f} N, T_blade = {T_blade:.2f} N, T_duct = {T_duct:.2f} N, T_hub = {T_hub:.2f} N, T_stator = {T_stator:.2f} N, Q = {Q:.2f} Nm, omega = {omega:.1f} rad/s")
            
        
    #input("Press Enter to continue...\n")
       
    time2 = time.time()

    print(f"Simulation run in  {(time2-time1)/60:.2f} mins")

    if convergence == 0:
        print("Case did not converge")

    P = Q * omega
    
    if P != 0:
        if T_total>0:
            power_loading = (T_total/9.81) / (P/1000) # kg/kW
            disk_loading = T_total / 9.81 / A # disk loading in kg/m2
            FM = T_total**1.5 / (P * math.sqrt(4 * rho * A * sigma))  # Figure of Merit
            duct_share = T_duct / T_total * 100 if T_total != 0 else 0
            OF_out = P / T_total  # Objective function: Power / Total Thrust

        else:
            power_loading = 0
            disk_loading = 0
            FM = 0
            duct_share = 0
            OF_out = 1e5

        rpm = omega * 60 / (2 * math.pi)
        
        print(f"Thrust: {T_total:.2f} N | Power: {P:.2f} W | Torque: {Q:.2f} Nm | RPM: {rpm:.2f} | Duct Share: {duct_share:.1f}% | Disk Loading: {disk_loading:.2f} kg/m^2 | Power Loading: {power_loading:.2f} kg/kW | FM: {FM:.3f}")
    else:
        print("Thrust: Undefined | Power: Undefined | Torque: Undefined | RPM: Undefined | Duct Share: Undefined | Disk Loading: Undefined | Power Loading: Undefined | FM: Undefined")
    

    # Access the graphics object
    # graphics = solver.settings.results.graphics
    # # Set the hardcopy format for saving the image
    # graphics.picture.driver_options.hardcopy_format = "png" 
    # # Set View
    # contour_view = graphics.views.display_states.create("contour_view")
    # contour_view.front_faces_transparent = "disable"
    # contour_view.view_name = "front"
    # pressure_contour = graphics.contour.create(name="pressure_contour")
    # pressure_contour.field = "pressure"
    # if mode == 1:
    #     pressure_contour.surfaces_list = ["blade1","blade2","duct1","duct2","hub1","hub2"]
    # else:
    #     pressure_contour.surfaces_list = ["blade1","duct1","duct2","hub1","hub2"]
    # pressure_contour.display_state_name = contour_view.name()
    # pressure_contour.display()
    # pressure_contour.color_map.visible = False
    # pressure_contour.color_map.font_size = 12
    # #graphics.views.camera.target = [0.2, 0.0, 0.0]
    # #graphics.views.camera.position = [-0.95, -1.25, 0.95]
    # graphics.views.auto_scale()
    # if graphics.picture.use_window_resolution.is_active():
    #     graphics.picture.use_window_resolution = False
    
    # graphics.picture.x_resolution = 1920
    # graphics.picture.y_resolution = 1440   
    # graphics.picture.save_picture(file_name=f"{case_folder}\\surface.png")

    solver.settings.results.surfaces.plane_slice['plane-1'] = {'normal' : [0, 0, 1], 'distance_from_origin' : blade_lims[0]*1.01}
    solver.settings.results.surfaces.plane_slice['plane-2'] = {'normal' : [0, 0, 1], 'distance_from_origin' : blade_lims[1]*1.01}

    if istator:
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface.dat", 
                                          surface_name_list = ["blade"], 
                                          delimiter = 'comma', 
                                          cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                          location = 'cell-center'
                                          )
    else:
        if mode == 1: 
            solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface.dat", 
                                            surface_name_list = ["blade1", "blade2"], 
                                            delimiter = 'comma', 
                                            cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                            location = 'cell-center'
                                            )
            # solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface_acum.dat", 
            #                                   surface_name_list = ["blade1", "blade2","duct1","duct2","hub1","hub2"], 
            #                                   delimiter = 'comma', 
            #                                   cell_func_domain = ['pressure','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
            #                                   location = 'cell-center'
            #                                   )
        else:
            solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface.dat", 
                                            surface_name_list = ["blade1"], 
                                            delimiter = 'comma', 
                                            cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                            location = 'cell-center'
                                            )

  
        # solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface_acum.dat", 
        #                                   surface_name_list = ["blade1","duct1","duct2","hub1","hub2"], 
        #                                   delimiter = 'comma', 
        #                                   cell_func_domain = ['pressure','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
        #                                   location = 'cell-center'
        #                                   )
        

    if istator:
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\stator.dat", 
                                        surface_name_list = ["stator"], 
                                        delimiter = 'comma', 
                                        cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                        location = 'cell-center'
                                        )

    solver.settings.file.export.ascii(file_name = f"{case_folder}\\slice_up.dat", 
                                      surface_name_list = ["plane-1"], 
                                      delimiter = 'comma', 
                                      cell_func_domain = ['density', 'pressure', 'velocity-magnitude', 'x-velocity', 'y-velocity', 'z-velocity','vorticity-mag'], 
                                      location = 'cell-center'
                                      )
    solver.settings.file.export.ascii(file_name = f"{case_folder}\\slice_down.dat", 
                                      surface_name_list = ["plane-2"], 
                                      delimiter = 'comma', 
                                      cell_func_domain = ['density', 'pressure', 'velocity-magnitude', 'x-velocity', 'y-velocity', 'z-velocity','vorticity-mag'], 
                                      location = 'cell-center'
                                      )
    

    #input("Simulation complete. Press Enter to continue...\n")

    return T_total, T_blade, T_duct, T_hub, T_stator, Q, omega, P, FM, disk_loading, power_loading, OF_out

def read_force(file_path,gpu_cfd,nb,ns_error,file_torque):
    # Reads final forces and moments
    niter_avg = 30


    with open(file_path,"r") as file:
        lst = [line.strip().split() for line in file]

    niter_avg = min(niter_avg,len(lst)-3)


    
    if gpu_cfd:
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
        if gpu_cfd:
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

    print(f"Total Thrust: {T_total:.2f} N, Blade Thrust: {T_blade:.2f} N, Duct Thrust: {T_duct:.2f} N, Hub Thrust: {T_hub:.2f} N, Torque: {Q:.2f} Nm, Nb: {nb}")

    return T_total*nb,T_blade*nb,T_duct*nb,T_hub*nb,Q*nb,1


def read_force_stator(file_path,nb,snb):
    # Reads final forces and moments
    niter_avg = 30


    with open(file_path,"r") as file:
        lst = [line.strip().split() for line in file]

    
                    
    Q = float(lst[-1][3])
    T_blade = float(lst[-1][5])
    T_rot_duct = float(lst[-1][7])
    T_rot_hub = float(lst[-1][9])
    T_stat_duct = float(lst[-1][11])
    T_stat_hub = float(lst[-1][13])
    T_stator = float(lst[-1][15])
   
    T_total = ((T_blade + T_rot_duct + T_rot_hub)*nb + (T_stat_duct + T_stat_hub + T_stator)*snb)/nb
    T_duct = (T_rot_duct*nb + T_stat_duct*snb)/nb
    T_hub = (T_rot_hub*nb + T_stat_hub*snb)/nb

    print(f"Total Thrust: {T_total:.2f} N, Blade Thrust: {T_blade:.2f} N, Duct Thrust: {T_duct:.2f} N, Hub Thrust: {T_hub:.2f} N, Stator Thrust: {T_stator:.2f} N, Torque: {Q:.2f} Nm, Nb: {nb}, sNb: {snb}")

    return T_total*nb,T_blade*nb,T_duct*nb,T_hub*nb,T_stator*snb,Q*nb,1

