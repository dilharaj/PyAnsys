# Python Script, API Version = V242

# Suppress/Unsuppress Physics
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(GetRootPart().Bodies[0])
simulation.SuppressBodies(selection,True)
# EndBlock

# Suppress/Unsuppress Physics
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(GetRootPart().Bodies[1])
simulation.SuppressBodies(selection,True)
# EndBlock

# 
Workbench.Fluent.ExportPMDB("Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case4\case_nearbody.pmdb")
# EndBlock

# Suppress/Unsuppress Physics
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(GetRootPart().Bodies[1])
simulation.SuppressBodies(selection, False)
# EndBlock

# Suppress/Unsuppress Physics
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(GetRootPart().Bodies[0])
simulation.SuppressBodies(selection, False)
# EndBlock

# Suppress/Unsuppress Physics
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(GetRootPart().Bodies[2])
simulation.SuppressBodies(selection,True)
# EndBlock

# 
Workbench.Fluent.ExportPMDB("Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case4\case_offbody.pmdb")
# EndBlock