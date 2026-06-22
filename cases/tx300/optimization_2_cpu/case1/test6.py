import math
import os

import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples
# Download the mesh file from the examples repository
# Impeller and volute mesh files
# nearbody_mesh = examples.download_file(
#     "impeller.msh.h5",
#     "pyfluent/examples/pump-volute",
#     save_path=os.getcwd(),
# )

# offbody_mesh = examples.download_file(
#     "volute.msh.h5",
#     "pyfluent/examples/pump-volute",
#     save_path=os.getcwd(),
# )
# density_water = 998.2  # kg/m^3
# viscosity_water = 0.001002  # kg/(m.s)
# g = 9.81  # m/s^2
# # Impeller speed
# impeller_speed = 1450  # rpm
# # Convert to rad/s
# impeller_speed_rad = impeller_speed * 2 * math.pi / 60  # rad/s

solver_session = pyfluent.launch_fluent(
    mode="solver",
    processor_count=4,
    show_gui=True,
)
print(solver_session.get_fluent_version())

nearbody_mesh = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case4\case_nearbody1.msh.h5"
offbody_mesh = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case4\case_offbody1.msh.h5"

# Read Impeller mesh file
solver_session.settings.file.read_mesh(file_name=nearbody_mesh)
# Append Volute mesh file
solver_session.settings.mesh.modify_zones.append_mesh(file_name=offbody_mesh)

solver_session.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_nested'], new_type = 'interface')
solver_session.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_nested'], new_type = 'interface')
solver_session.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_down_near'], new_type = 'interface')
solver_session.settings.setup.boundary_conditions.set_zone_type(zone_list = ['interface_up_near'], new_type = 'interface')


nearbody_cell_zone = solver_session.settings.setup.cell_zone_conditions.fluid[
    "nearbody"
]

nearbody_cell_zone.reference_frame.reference_frame_axis_origin = [0, 0, 0]
nearbody_cell_zone.reference_frame.reference_frame_axis_direction = [0, 0, 1]
nearbody_cell_zone.reference_frame.frame_motion = True

nested_cell_zone = solver_session.settings.setup.cell_zone_conditions.fluid[
    "nested"
]

nested_cell_zone.reference_frame.reference_frame_axis_origin = [0, 0, 0]
nested_cell_zone.reference_frame.reference_frame_axis_direction = [0, 0, 1]

solver_session.settings.setup.turbo_models.enabled = True

input("check")
impeller_volute_interface = (
    solver_session.settings.setup.mesh_interfaces.turbo_create.create(
        adjacent_cell_zone_1="nested",
        adjacent_cell_zone_2="nearbody",
        mesh_interface_name="s1",
        turbo_choice="Mixing-Plane",#"No-Pitch-Scale",
        zone1="interface_up_nested",
        zone2="interface_up_near",
    )
)

impeller_volute_interface = (
    solver_session.settings.setup.mesh_interfaces.turbo_create.create(
        adjacent_cell_zone_1="nested",
        adjacent_cell_zone_2="nearbody",
        mesh_interface_name="s2",
        turbo_choice="Mixing-Plane",#"No-Pitch-Scale",
        zone1="interface_down_nested",
        zone2="interface_down_near",
    )
)



input("Check stop")
