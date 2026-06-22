import os
if not os.getenv('FLUENT_PROD_DIR'):
    import ansys.fluent.core as pyfluent
    flglobals = pyfluent.setup_for_fluent(product_version="25.2.0", mode="solver", dimension=3, precision="double", processor_count=1, ui_mode="gui", graphics_driver="dx11", gpu=False)
    globals().update(flglobals)

