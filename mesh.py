import os
import time
import concurrent.futures
import ansys.fluent.core as pyfluent

def run_mesh(variables, const, case_folder, id, istator=False):

    nproc_mesh = id.inputs.nproc_mesh  # Number of processors
    nproc_cfd = id.inputs.nproc_cfd  # Number of processors for CFD solver
    
    gui = id.inputs.gui # Use GUI for meshing and solver
    gui = True
    
    alpha_per = 360.0/variables[id.rnb]
    n_out = 11  # Number of outputs
    error_out = [-1.0] * n_out  # Error output 

    R_tip = const[id.r]

    geo_file = f"{case_folder}\\case.pmdb"
    out_file = f"{case_folder}\\mesh.msh.h5"
     # start meshing
    meshing = pyfluent.launch_fluent(
    precision="double",
    processor_count=nproc_mesh,
    mode="meshing",
    show_gui=gui,
    )

    # if istator:
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         mode = 1
    #         future = executor.submit(make_mesh_cpu, meshing, variables, const, case_folder, id)
    #         try:
    #             mesh_file = future.result(timeout=600) # Wait for up to 10 minutes
    #         except Exception as e:
    #             print(f"Error in mesh generation: {e}")
    #             return [2 * x for x in error_out]  # Return error output
    
    # else:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mode = 1
        future = executor.submit(make_mesh, meshing, geo_file, out_file, alpha_per, mode, R_tip)
        try:
            mesh_file = future.result(timeout=600) # Wait for up to 10 minutes
        except Exception as e:
            mode = 2
            try:
                mesh_file = make_mesh(meshing, geo_file, out_file, alpha_per, mode, R_tip)
            except Exception as e:
                print(f"Error in mesh generation: {e}")
                meshing.exit()
                file = open(rf"{case_folder}\mesh_info.txt", "w")
                file.write(f"0 {mode}\n")
                file.close()
                print("Exiting meshing due to error...")
                return [2 * x for x in error_out]  # Return error output
    

    meshing.exit()

    file = open(rf"{case_folder}\mesh_info.txt", "w")
    file.write(f"1 {mode}\n")
    file.close()
    return mesh_file

def make_mesh(meshing,in_file,out_file,alpha_per,mode,R_tip,istator):

    alpha_per_near = 10

    time0 = time.time()

    #mesh size definitions
    max_size = 100/0.3*R_tip # mm
    min_size_blade = 0.5/0.3*R_tip # mm
    min_size_blade2 = 0.05/0.3*R_tip # mm
    min_size_duct_hub = 1/0.3*R_tip # mm
    curv_angle = 5 # deg
    cell_size_blade = 3/0.3*R_tip # mm
    cell_size_blade2 = 0.3/0.3*R_tip # mm
    cell_size_duct_hub = 6 /0.3*R_tip# mm
    cell_size_nearbody = 8/0.3*R_tip # mm
    growth_rate = 1.2
    nBL = 3 # number of boundary layers


    # max_size = 100 # mm
    # min_size_blade = 0.01 # mm
    # min_size_duct_hub = 0.8 # mm
    # curv_angle = 5 # deg
    # cell_size_blade = 2 # mm
    # cell_size_duct_hub = 4 # mm
    # cell_size_nearbody = 8 # mm
    # growth_rate = 1.2
    # nBL = 15 # nu

    print("Launching Fluent Meshing...\n")
   



    if os.path.exists(out_file):
        print("Ovewriting")
        os.remove(out_file)
    else:
        print("Writing new mesh file")
    print(meshing.get_fluent_version()) 
    #input("check")
    meshing.workflow.InitializeWorkflow(WorkflowType='Watertight Geometry')
    workflow = meshing.workflow
    
    print("Importing geometry\n")
    workflow.TaskObject['Import Geometry'].Arguments.set_state({r'FileName': in_file,r'LengthUnit': r'mm',})
    workflow.TaskObject['Import Geometry'].Execute()
    print("Adding local sizing...\n")
    
    if mode == 1:
        if istator:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade',r'stator'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
        else:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade1'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face2',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade2,r'BOIZoneorLabel': r'label',})
    
    else:
        if istator:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade',r'stator'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
        else:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade1',r'blade2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})

        

    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'duct1',r'duct2', r'hub1', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    
    if mode == 1:
        if istator:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade',r'stator'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
        else:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade1'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
        
        
        #workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve2',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade2,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    else:
        if istator:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade',r'stator'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
        else:
            workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade1',r'blade2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
        
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'duct1',r'duct2', r'hub1', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'nearbody',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Body Size',r'BOIFaceLabelList': [r'nearbody'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_nearbody,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)

    #input("Local sizing added. Press Enter to continue...\n")
    workflow.TaskObject['Generate the Surface Mesh'].Arguments.set_state({r'ExecuteShareTopology': r'No',r'SurfaceMeshPreferences': {r'SelfIntersectCheck': r'no',r'ShowSurfaceMeshPreferences': True,}})
    #workflow.TaskObject['Generate the Surface Mesh'].Arguments.set_state({r'CFDSurfaceMeshControls': {r'MinSize': min_size_blade,},})
    workflow.TaskObject['Generate the Surface Mesh'].Execute()

    #input("Surface mesh generated. Press Enter to continue...\n")
    time1 = time.time()
    print(f"Surface mesh generated in {time1-time0:.1f} seconds\n")
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=False)
  
    if istator:
        workflow.TaskObject['Describe Geometry'].Arguments.set_state({r'InvokeShareTopology': r'No',r'NonConformal': r'No',r'SetupType': r'The geometry consists of only fluid regions with no voids',r'WallToInternal': r'No',})
    else:
        workflow.TaskObject['Describe Geometry'].Arguments.set_state({r'InvokeShareTopology': r'No',r'NonConformal': r'No',r'SetupType': r'The geometry consists of only fluid regions with no voids',r'WallToInternal': r'Yes',})
    
  

    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=True)
    workflow.TaskObject['Describe Geometry'].Execute()
    workflow.TaskObject['Update Boundaries'].Execute()
    workflow.TaskObject['Update Regions'].Execute()

    print("Boundaries and regions updated\n")
    #input("Enter to continue")
    if istator:
        workflow.TaskObject['Add Boundary Layers'].Arguments.set_state({r'BlLabelList': [r'blade',r'stator', r'duct1', r'duct2', r'hub1', r'hub2'],r'FaceScope': {r'GrowOn': r'selected-labels',},r'LocalPrismPreferences': {r'Continuous': r'Continuous',},r'NumberOfLayers': nBL,})
    else:
        workflow.TaskObject['Add Boundary Layers'].Arguments.set_state({r'BlLabelList': [r'blade1',r'blade2', r'duct1', r'duct2', r'hub1', r'hub2'],r'FaceScope': {r'GrowOn': r'selected-labels',},r'LocalPrismPreferences': {r'Continuous': r'Continuous',},r'NumberOfLayers': nBL,})
    
    workflow.TaskObject['Add Boundary Layers'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Boundary Layers'].InsertNextTask(CommandName=r'SetUpPeriodicBoundaries')
    
    print("Boundary layers added\n")
    
    #input("Enter to continue")
    if istator:
        workflow.TaskObject['Set Up Periodic Boundaries'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1_near', r'per2_near'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per_near,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
        workflow.TaskObject['Set Up Periodic Boundaries'].Execute()
        workflow.TaskObject['Set Up Periodic Boundaries'].InsertNextTask(CommandName=r'SetUpPeriodicBoundaries')
        workflow.TaskObject['Set Up Periodic Boundaries 1'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1_off', r'per2_off'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
        workflow.TaskObject['Set Up Periodic Boundaries 1'].Execute()
    
    
    else:
        workflow.TaskObject['Set Up Periodic Boundaries'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1', r'per2'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
        workflow.TaskObject['Set Up Periodic Boundaries'].Execute()
    print("Periodic boundary set up")
    
    workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'polyhedra',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    #workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'tetrahedral',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    workflow.TaskObject['Generate the Volume Mesh'].Execute()
    time2 = time.time()
    
    #input("Enter to continue")
    print(f"Volume mesh generated in {time2-time0:.1f} seconds")
    if os.path.exists(out_file):
        print("Ovewriting")
        os.remove(out_file)
    meshing.tui.file.write_mesh(out_file)
    print("Mesh file written")
    time3 = time.time()
    print(f"Total meshing time is {time3-time0:.1f} seconds")
    
    #print("Current working directory:", cwd)
    print("Meshing completed successfully\n Outfile: ", out_file)
    #input("Enter to exit meshing...\n")
    return out_file


def make_mesh_cpu(variables, const, case_folder, id):

    nproc_mesh = id.inputs.nproc_mesh  # Number of processors
    nproc_cfd = id.inputs.nproc_cfd  # Number of processors for CFD solver
    
    gui = id.inputs.gui # Use GUI for meshing and solver
    gui = True
    
    meshing = pyfluent.launch_fluent(
    precision="double",
    processor_count=nproc_cfd,
    mode="meshing",
    show_gui=gui,
    )

    # file definitions

    fluent_file_near = f"{case_folder}\\case_near.pmdb"
    fluent_file_off = f"{case_folder}\\case_off.pmdb"

    out_file_near = f"{case_folder}\\mesh_near.msh.h5"
    out_file_off = f"{case_folder}\\mesh_off.msh.h5"
    
    if os.path.exists(out_file_near):
        print("Ovewriting nearbody mesh file")
        os.remove(out_file_near)
    else:
        print("Writing new nearbody mesh file")
    
    if os.path.exists(out_file_off):
        print("Ovewriting offbody mesh file")
        os.remove(out_file_off)
    else:
        print("Writing new offbody mesh file")
    
    alpha_per_near = 360.0/variables[id.rnb]
    alpha_per_off = 360.0/variables[id.snb]

    

    print(meshing.get_fluent_version()) 

    R_tip = const[id.r]

    time0 = time.time()

    #mesh size definitions
    max_size = 100/0.3*R_tip # mm
    min_size_blade = 0.5/0.3*R_tip # mm
    min_size_duct_hub = 1/0.3*R_tip # mm
    curv_angle = 5 # deg
    cell_size_blade = 3/0.3*R_tip # mm
    cell_size_duct_hub = 6 /0.3*R_tip# mm
    cell_size_nearbody = 8/0.3*R_tip # mm
    cell_size_nested = 8/0.3*R_tip # mm
    growth_rate = 1.2
    nBL = 3 # number of boundary layers

    print("Launching Fluent Meshing...\n")

    
    meshing.workflow.InitializeWorkflow(WorkflowType='Watertight Geometry')
    workflow = meshing.workflow
    
    ## Nearbody
    print("Importing geometry for nearbody\n")
    workflow.TaskObject['Import Geometry'].Arguments.set_state({r'FileName': fluent_file_near,r'LengthUnit': r'mm',})
    workflow.TaskObject['Import Geometry'].Execute()
    print("Adding local sizing...\n")
    
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'duct1', r'hub1'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'nearbody',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Body Size',r'BOIFaceLabelList': [r'nearbody'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_nearbody,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'duct1', r'hub1'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
   
    #input("Local sizing added. Press Enter to continue...\n")
    workflow.TaskObject['Generate the Surface Mesh'].Execute()

    #input("Surface mesh generated. Press Enter to continue...\n")
    time1 = time.time()
    print(f"Surface mesh generated in {time1-time0:.1f} seconds\n")
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=False)
  
    workflow.TaskObject['Describe Geometry'].Arguments.set_state({r'InvokeShareTopology': r'No',r'NonConformal': r'No',r'SetupType': r'The geometry consists of only fluid regions with no voids',r'WallToInternal': r'No',})
    
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=True)
    workflow.TaskObject['Describe Geometry'].Execute()
    workflow.TaskObject['Update Boundaries'].Execute()
    workflow.TaskObject['Update Regions'].Execute()

    print("Boundaries and regions updated\n")
    #input("Enter to continue")
    workflow.TaskObject['Add Boundary Layers'].Arguments.set_state({r'BlLabelList': [r'blade', r'duct1', r'hub1'],r'FaceScope': {r'GrowOn': r'selected-labels',},r'LocalPrismPreferences': {r'Continuous': r'Continuous',},r'NumberOfLayers': nBL,})
    
    workflow.TaskObject['Add Boundary Layers'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Boundary Layers'].InsertNextTask(CommandName=r'SetUpPeriodicBoundaries')
    
    print("Boundary layers added\n")
    
    workflow.TaskObject['Set Up Periodic Boundaries'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1_near', r'per2_near'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per_near,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
    workflow.TaskObject['Set Up Periodic Boundaries'].Execute()
    
    print("Periodic boundary set up")
    
    workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'polyhedra',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    #workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'tetrahedral',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    workflow.TaskObject['Generate the Volume Mesh'].Execute()
    time2 = time.time()
    
    #input("Enter to continue")
    print(f"Volume mesh generated in {time2-time0:.1f} seconds")
    
    meshing.tui.file.write_mesh(out_file_near)
    print("Nearbody mesh file written")
    time3 = time.time()
    print(f"Total meshing time is {time3-time0:.1f} seconds")
    
    print("Nearbody meshing completed successfully\n Outfile: ", out_file_near)
    #input("Enter to exit meshing...\n")
    

    
    workflow.ResetWorkflow()

    meshing.workflow.InitializeWorkflow(WorkflowType='Watertight Geometry')
    workflow = meshing.workflow

    ## Offbody
    print("Importing geometry for offbody\n")
    workflow.TaskObject['Import Geometry'].Arguments.set_state({r'FileName': fluent_file_off,r'LengthUnit': r'mm',})
    workflow.TaskObject['Import Geometry'].Execute()
    print("Adding local sizing...\n")
    
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'stator'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'duct2', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'stator'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'nearbody',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Body Size',r'BOIFaceLabelList': [r'nested'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_nested,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'duct2', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
   
    #input("Local sizing added. Press Enter to continue...\n")
    workflow.TaskObject['Generate the Surface Mesh'].Execute()

    #input("Surface mesh generated. Press Enter to continue...\n")
    time1 = time.time()
    print(f"Surface mesh generated in {time1-time0:.1f} seconds\n")
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=False)
  
    workflow.TaskObject['Describe Geometry'].Arguments.set_state({r'InvokeShareTopology': r'No',r'NonConformal': r'No',r'SetupType': r'The geometry consists of only fluid regions with no voids',r'WallToInternal': r'No',})
    
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=True)
    workflow.TaskObject['Describe Geometry'].Execute()
    workflow.TaskObject['Update Boundaries'].Execute()
    workflow.TaskObject['Update Regions'].Execute()

    print("Boundaries and regions updated\n")
    #input("Enter to continue")
    workflow.TaskObject['Add Boundary Layers'].Arguments.set_state({r'BlLabelList': [r'stator', r'duct2', r'hub2'],r'FaceScope': {r'GrowOn': r'selected-labels',},r'LocalPrismPreferences': {r'Continuous': r'Continuous',},r'NumberOfLayers': nBL,})
    
    workflow.TaskObject['Add Boundary Layers'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Boundary Layers'].InsertNextTask(CommandName=r'SetUpPeriodicBoundaries')
    
    print("Boundary layers added\n")
    
    workflow.TaskObject['Set Up Periodic Boundaries'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1_off', r'per2_off'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per_off,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
    workflow.TaskObject['Set Up Periodic Boundaries'].Execute()
    
    print("Periodic boundary set up")
    
    workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'polyhedra',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    #workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'tetrahedral',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    workflow.TaskObject['Generate the Volume Mesh'].Execute()
    time2 = time.time()
    
    #input("Enter to continue")
    print(f"Volume mesh generated in {time2-time0:.1f} seconds")
    
    meshing.tui.file.write_mesh(out_file_off)
    print("Offbody mesh file written")
    time3 = time.time()
    print(f"Total meshing time is {time3-time0:.1f} seconds")
    
    print("Offbody meshing completed successfully\n Outfile: ", out_file_off)
    #input("Enter to exit meshing...\n")
    
    
    solver = meshing.switch_to_solver()
    
    
    file = open(rf"{case_folder}\mesh_info.txt", "w")
    file.write(f"1 1\n")
    file.close()


    return solver, out_file_near, out_file_off