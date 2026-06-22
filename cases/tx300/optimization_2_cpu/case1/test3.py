import os
if not os.getenv('FLUENT_PROD_DIR'):
    import ansys.fluent.core as pyfluent
    flglobals = pyfluent.setup_for_fluent(product_version="25.2.0", mode="solver", dimension=3, precision="double", processor_count=60, ui_mode="gui", graphics_driver="dx11", gpu=False)
    globals().update(flglobals)

solver.settings.setup.mesh_interfaces.turbo_create.create(mesh_interface_name = 's2', adjacent_cell_zone_1 = 'all', zone1 = 'down_near', adjacent_cell_zone_2 = 'all', zone2 = 'down_nested', paired_zones = [], turbo_choice = 'Mixing-Plane')
solver.exit()
