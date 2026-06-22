import os
if not os.getenv('FLUENT_PROD_DIR'):
    import ansys.fluent.core as pyfluent
    flglobals = pyfluent.setup_for_fluent(product_version="25.2.0", mode="meshing", dimension=3, precision="double", processor_count=1, ui_mode="gui", graphics_driver="dx11", gpu=False)
    globals().update(flglobals)

workflow.InitializeWorkflow(WorkflowType=r'Fault-tolerant Meshing')
PartManagement.InputFileChanged(FilePath=r'Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/cases/tx300/optimization_2_cpu/case2/case.pmdb')
workflow.TaskObject['Import CAD and Part Management'].Arguments.set_state({r'Append': False,r'Context': 0,r'FMDFileName': r'Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/cases/tx300/optimization_2_cpu/case2/case.pmdb',r'ObjectSetting': r'DefaultObjectSetting',})
solver.settings.results.graphics.lighting.lighting_interpolation = 'Flat'
workflow.TaskObject['Import CAD and Part Management'].Execute()
workflow.TaskObject['Describe Geometry and Flow'].Arguments.set_state({r'AddEnclosure': r'No',r'DescribeGeometryAndFlowOptions': {r'AdvancedOptions': False,},r'LocalRefinementRegions': r'Yes',})
workflow.TaskObject['Describe Geometry and Flow'].UpdateChildTasks(SetupTypeChanged=False)
workflow.TaskObject['Describe Geometry and Flow'].Execute()
workflow.TaskObject['Describe Geometry and Flow'].Revert()
workflow.TaskObject['Describe Geometry and Flow'].Arguments.set_state({r'AddEnclosure': r'No',r'DescribeGeometryAndFlowOptions': {r'AdvancedOptions': False,},r'LocalRefinementRegions': r'No',})
workflow.TaskObject['Describe Geometry and Flow'].UpdateChildTasks(SetupTypeChanged=False)
workflow.TaskObject['Describe Geometry and Flow'].Execute()
workflow.TaskObject['Identify Regions'].Arguments.set_state({r'X': 0,r'Y': 0,r'Z': 0,})
workflow.TaskObject['Identify Regions'].Arguments.set_state({r'AddChild': r'yes',r'GraphicalSelection': True,r'LinkConstruction': r'no',r'MaterialPointsName': r'fluid-region-1',r'MptMethodType': r'Centroid of Objects',r'NewRegionType': r'fluid',r'ObjectSelectionList': [r'geo'],r'OffsetX': 0,r'OffsetY': 0,r'OffsetZ': 0,r'SelectionType': r'object',r'ShowCoordinates': False,r'X': 750,r'Y': 0,r'Z': 0,})
workflow.TaskObject['Identify Regions'].AddChildAndUpdate(DeferUpdate=False)
workflow.TaskObject['Define Leakage Threshold'].AddChildAndUpdate(DeferUpdate=False)
workflow.TaskObject['Import CAD and Part Management'].Revert()
PartManagement.InitializeTemplate(templateType=r'External Flow')
workflow.TaskObject['Import CAD and Part Management'].Arguments.set_state({r'Append': False,r'Context': 0,r'CreateObjectPer': r'One per part',r'FMDFileName': r'Z:/UFX_dilhara/Ansys/3D_CFD_Optimizer/Manual/cases/tx300/optimization_2_cpu/case2/case.pmdb',r'ObjectSetting': r'DefaultObjectSetting',})
solver.settings.results.graphics.lighting.lighting_interpolation = 'Flat'
workflow.TaskObject['Import CAD and Part Management'].Execute()
workflow.TaskObject['Describe Geometry and Flow'].Arguments.set_state({r'AddEnclosure': r'No',r'CloseCaps': r'No',r'DescribeGeometryAndFlowOptions': {r'AdvancedOptions': True,},r'FlowType': r'Both external and internal flow',r'LocalRefinementRegions': r'No',})
workflow.TaskObject['Describe Geometry and Flow'].UpdateChildTasks(SetupTypeChanged=False)
workflow.TaskObject['Describe Geometry and Flow'].Execute()
workflow.TaskObject['Identify Regions'].Arguments.set_state({r'AddChild': r'yes',r'LabelSelectionList': [r'nearbody', r'nested', r'offbody'],r'ObjectSelectionList': [r'geo'],r'SelectionType': r'label',r'X': 275.4031197545713,r'Y': -0.3697081646190084,r'Z': -22.41996805882845,})
workflow.TaskObject['fluid-region-1'].Arguments.set_state({r'AddChild': r'yes',r'GraphicalSelection': True,r'LabelSelectionList': [r'nearbody', r'nested', r'offbody'],r'LinkConstruction': r'no',r'MaterialPointsName': r'fluid-region-1',r'MptMethodType': r'Centroid of Objects',r'NewRegionType': r'fluid',r'ObjectSelectionList': [r'geo'],r'OffsetX': 0,r'OffsetY': 0,r'OffsetZ': 0,r'SelectionType': r'label',r'ShowCoordinates': False,r'X': 275.4031197545713,r'Y': -0.3697081646190084,r'Z': -22.41996805882845,})
workflow.TaskObject['fluid-region-1'].Execute()
workflow.TaskObject['Define Leakage Threshold'].Arguments.set_state(None)
workflow.TaskObject['Define Leakage Threshold'].AddChildAndUpdate(DeferUpdate=False)
workflow.TaskObject['Update Region Settings'].Arguments.set_state({r'AllRegionFilterCategories': [r'2', r'1'],r'AllRegionLeakageSizeList': [r'none', r'none'],r'AllRegionLinkedConstructionSurfaceList': [r'n/a', r'no'],r'AllRegionMeshMethodList': [r'none', r'surface mesh'],r'AllRegionNameList': [r'geo', r'fluid-region-1'],r'AllRegionOversetComponenList': [r'no', r'no'],r'AllRegionSourceList': [r'object', r'mpt'],r'AllRegionTypeList': [r'void', r'fluid'],r'AllRegionVolumeFillList': [r'none', r'hexcore'],r'OldRegionLeakageSizeList': [r''],r'OldRegionMeshMethodList': [r'wrap'],r'OldRegionNameList': [r'fluid-region-1'],r'OldRegionOversetComponenList': [r'no'],r'OldRegionTypeList': [r'fluid'],r'OldRegionVolumeFillList': [r'hexcore'],r'RegionLeakageSizeList': [r''],r'RegionMeshMethodList': [r'surface mesh'],r'RegionNameList': [r'fluid-region-1'],r'RegionOversetComponenList': [r'no'],r'RegionTypeList': [r'fluid'],r'RegionVolumeFillList': [r'hexcore'],})
workflow.TaskObject['Update Region Settings'].Revert()
workflow.TaskObject['Update Region Settings'].Arguments.set_state({r'AllRegionFilterCategories': [r'2', r'1'],r'AllRegionLeakageSizeList': [r'none', r'none'],r'AllRegionLinkedConstructionSurfaceList': [r'n/a', r'no'],r'AllRegionMeshMethodList': [r'none', r'wrap'],r'AllRegionNameList': [r'geo', r'fluid-region-1'],r'AllRegionOversetComponenList': [r'no', r'no'],r'AllRegionSourceList': [r'object', r'mpt'],r'AllRegionTypeList': [r'void', r'fluid'],r'AllRegionVolumeFillList': [r'none', r'hexcore'],r'OldRegionLeakageSizeList': [r''],r'OldRegionMeshMethodList': [r'wrap'],r'OldRegionNameList': [r'fluid-region-1'],r'OldRegionOversetComponenList': [r'no'],r'OldRegionTypeList': [r'fluid'],r'OldRegionVolumeFillList': [r'hexcore'],r'RegionLeakageSizeList': [r''],r'RegionMeshMethodList': [r'wrap'],r'RegionNameList': [r'fluid-region-1'],r'RegionOversetComponenList': [r'no'],r'RegionTypeList': [r'fluid'],r'RegionVolumeFillList': [r'hexcore'],})
workflow.TaskObject['Update Region Settings'].Execute()
workflow.TaskObject['Choose Mesh Control Options'].Arguments.set_state({r'MeshControlOptions': {r'AdvancedOptions': True,},})
workflow.TaskObject['Choose Mesh Control Options'].Execute()
workflow.TaskObject['Generate the Surface Mesh'].Execute()
workflow.TaskObject['Describe Geometry and Flow'].Revert()
workflow.TaskObject['Import CAD and Part Management'].Revert()
workflow.InitializeWorkflow(WorkflowType=r'Watertight Geometry')
workflow.InitializeWorkflow(WorkflowType=r'Fault-tolerant Meshing')


Total Thrust: 10.70 N, Blade Thrust: 11.80 N, Duct Thrust: -1.71 N, Hub Thrust: 0.10 N, Stator Thrust: 
0.84 N, Torque: 1.09 Nm, Nb: 10, sNb: 6
CFD iteration 1 of 3 with omega = 1019.447 rad/s
    T_target = 140.000N, T_total = 106.959 N, T_blade = 117.986 N, T_duct = -17.134 N, T_hub = 1.041 N, T_stator = 5.066 N, Q = 10.898 Nm
Press Enter to continue...
Error in solver execution: 

Simulation run in  18.300830046335857 mins
Thrust: 106.96 N | Power: 11109.62 W | Torque: 10.90 Nm | RPM: 9735.00 | Duct Share: -16.0% | Disk Loading: 154.25 kg/m^2 | Power Loading: 0.98 kg/kW | FM: 0.173
