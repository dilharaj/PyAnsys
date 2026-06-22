import os
#if not os.getenv('FLUENT_PROD_DIR'):
import ansys.fluent.core as pyfluent
    # flglobals = pyfluent.setup_for_fluent(product_version="25.2.0", mode="solver", dimension=3, precision="double", processor_count=10, ui_mode="gui", graphics_driver="dx11", gpu=False)
    # globals().update(flglobals)

solver = pyfluent.launch_fluent(
            precision="double",
            processor_count=10,
            mode="solver",
            version="3d",
            show_gui=True,
            gpu=0
        )



solver.settings.file.read_case(file_name = r'Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case4\mesh.msh.h5')
solver.settings.setup.turbo_models.enabled = True
solver.settings.setup.mesh_interfaces.turbo_create.create(mesh_interface_name = 's1', adjacent_cell_zone_1 = 'all', zone1 = [], adjacent_cell_zone_2 = 'all', zone2 = [], paired_zones = [], turbo_choice = 'Mixing-Plane')
solver.settings.setup.mesh_interfaces.turbo_create.create(mesh_interface_name = 's1', adjacent_cell_zone_1 = 'all', zone1 = [], adjacent_cell_zone_2 = 'all', zone2 = [], paired_zones = [], turbo_choice = False)
solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_near'], new_type = 'interface')
solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_nested'], new_type = 'interface')
solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_nested'], new_type = 'interface')
solver.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_near'], new_type = 'interface')
solver.settings.setup.cell_zone_conditions.fluid['nearbody'] = {'reference_frame' : {'reference_frame_axis_direction' : [0, 0, 1], 'reference_frame_axis_origin' : [0., 0., 0.]}}
solver.settings.setup.cell_zone_conditions.fluid['nested'] = {'reference_frame' : {'reference_frame_axis_direction' : [0, 0, 1], 'reference_frame_axis_origin' : [0., 0., 0.]}}
solver.settings.setup.turbo_interfaces.create(mesh_interface_name = 's1', adjacent_cell_zone_1 = 'all', zone1 = 'interface_up_near', adjacent_cell_zone_2 = 'all', zone2 = 'interface_up_nested', paired_zones = [], turbo_choice = 'No-Pitch-Scale')


input("checl")