# Python Script, API Version = V242
import shutil
# USER INPUT
case_folder = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6"
num_blades = 10
# Set 3D View
mode = InteractionMode.Solid
sketch_result = ViewHelper.SetViewMode(mode)
# General Definitions
z_axis = Line.Create(Point.Origin, Direction.DirZ)
scale_factor = GetActiveWindow().Units.Length.ConversionFactor
scale_origin = Point.Create(MM(0), MM(0), MM(0))
angle = 2 * math.pi / 10
half_angle = angle / 2
# Clear Project
selection = Selection.SelectAll()
if selection.Count > 0:
    Delete.Execute(selection)
ComponentHelper.DeleteEmptyComponents(GetRootPart())
# Blade
airfoil_files = []
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_0.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_1.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_2.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_3.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_4.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_5.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_6.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_7.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_8.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\blade_cross_9.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
selection = FaceSelection.Create([af.CreatedFaces[0] for af in airfoil_files])
options = LoftOptions()
options.GeometryCommandOptions = GeometryCommandOptions()
blade_result = Loft.Create(selection, None, options)
blade_body = blade_result.GetCreated[IDesignBody]()[0]
# Blade Patterning
selection = BodySelection.Create(blade_body)
options = MoveOptions()
options.CreatePatterns = True
init_pattern_result = Move.Rotate(selection, z_axis, angle, options)
pattern = ComponentSelection.Create(init_pattern_result.GetCreated[IComponent]())
data = CircularPatternModificationData()
data.CircularCount = num_blades
data.StepAngle = angle
pattern_result = Pattern.ModifyCircular(pattern, data)
pattern_bodies = BodySelection.Create(pattern.Components[0].GetAllBodies())
ComponentHelper.MoveBodiesToComponent(pattern_bodies, GetRootPart(), False)
ComponentHelper.DeleteEmptyComponents(GetRootPart())
num_sblades = 6
s_angle = 2 * math.pi / 6
s_half_angle = s_angle / 2
# Stator
s_airfoil_files = []
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_0.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_1.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_2.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_3.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_4.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_5.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_6.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_7.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_8.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\\\stator_cross_9.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
empty = Selection.Empty()
options = FillOptions()
s_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))
Delete.Execute(selection)
selection = FaceSelection.Create([af.CreatedFaces[0] for af in s_airfoil_files])
options = LoftOptions()
options.GeometryCommandOptions = GeometryCommandOptions()
stator_result = Loft.Create(selection, None, options)
stator_body = stator_result.GetCreated[IDesignBody]()[0]
# Stator Blade Patterning
selection = BodySelection.Create(stator_body)
options = MoveOptions()
options.CreatePatterns = True
init_pattern_result = Move.Rotate(selection, z_axis, s_angle, options)
pattern = ComponentSelection.Create(init_pattern_result.GetCreated[IComponent]())
data = CircularPatternModificationData()
data.CircularCount = num_sblades
data.StepAngle = s_angle
spattern_result = Pattern.ModifyCircular(pattern, data)
spattern_bodies = BodySelection.Create(pattern.Components[0].GetAllBodies())
ComponentHelper.MoveBodiesToComponent(spattern_bodies, GetRootPart(), False)
ComponentHelper.DeleteEmptyComponents(GetRootPart())
# Duct
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\duct.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
secondarySelection = Selection.Empty()
options = FillOptions()
result = Fill.Execute(selection, secondarySelection, options, FillMode.ThreeD)
Delete.Execute(selection)
selection = Selection.Create(result.GetCreated[IDesignFace]()[0])
options = RevolveFaceOptions()
axisSelection = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[2])
axis = RevolveFaces.GetAxisFromSelection(selection, axisSelection, True)
options.ExtrudeType = ExtrudeType.Add
result = RevolveFaces.Execute(selection, axis, DEG(360), options)
# Hub
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\hub.txt")
selection = Selection.Create([GetRootPart().Curves[0]])
result = Scale.Execute(selection, scale_origin, scale_factor, False)
secondarySelection = Selection.Empty()
options = FillOptions()
result = Fill.Execute(selection, secondarySelection, options, FillMode.ThreeD)
Delete.Execute(selection)
selection = Selection.Create(result.GetCreated[IDesignFace]()[0])
z_axis = Line.Create(Point.Origin, Direction.DirZ)
options = RevolveFaceOptions()
options.ExtrudeType = ExtrudeType.Cut
result = RevolveFaces.Execute(selection, z_axis, DEG(-360), options)
rotor_body = result.GetModified[IDesignBody]()[0]
stl_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\\geo.stl"
# Save Project As
File.SaveAs(stl_file)
# EndBlock
# Save Project As
File.SaveAs(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\geo0.dsco")
# Enclosure
sectionPlane = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(0)),Direction.DirZ, Direction.DirX))
result = ViewHelper.SetSketchPlane(sectionPlane)
point1 = Point2D.Create(M(0.16514625176476092),M(0))
point2 = Point2D.Create(M(-0.28505331153670876),M(0))
point3 = Point2D.Create(M(-0.28505331153670876),M(0.2549998411764893))
result = SketchRectangle.Create(point1, point2, point3)
point1 = Point2D.Create(M(1.5),M(0))
point2 = Point2D.Create(M(-1.5),M(0))
point3 = Point2D.Create(M(-1.5),M(1.5))
result = SketchRectangle.Create(point1, point2, point3)
point1 = Point2D.Create(M(0.05343749999999999),M(0))
point2 = Point2D.Create(M(-0.06378493275643177),M(0))
point3 = Point2D.Create(M(-0.06378493275643177),M(0.16499999999999998))
result = SketchRectangle.Create(point1, point2, point3)
mode = InteractionMode.Solid
sketch_result = ViewHelper.SetViewMode(mode)
get_faces = sketch_result.GetCreated[IDesignFace]()
options = RevolveFaceOptions()
options.PullSymmetric = True
options.ExtrudeType = ExtrudeType.ForceIndependent
revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), z_axis, s_half_angle, options)
targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())
merge_result_0 = Combine.Merge(targets)
revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), z_axis, s_half_angle, options)
targets = Selection.Create(revolve_result_1.GetCreated[IDesignBody]())
merge_result_1 = Combine.Merge(targets)
revolve_result_2 = RevolveFaces.Execute(Selection.Create([get_faces[2]]), z_axis, half_angle, options)
targets = Selection.Create(revolve_result_2.GetCreated[IDesignBody]())
merge_result_2 = Combine.Merge(targets)
targets = BodySelection.Create(merge_result_2.GetModified[IDesignBody]()[0])
tools = BodySelection.Create(rotor_body)
options = MakeSolidsOptions()
options.KeepCutter = True
options.SubtractFromTarget = True
result = Combine.Intersect(targets, tools, options)
tools = BodySelection.Create(rotor_body)
options = MakeSolidsOptions()
options.KeepCutter = False
options.SubtractFromTarget = True
targets = BodySelection.Create(merge_result_0.GetModified[IDesignBody]()[0])
result = Combine.Intersect(targets, tools, options)
nested = merge_result_0.GetModified[IDesignBody]()[0]
offbody = merge_result_1.GetModified[IDesignBody]()[0]
nearbody = merge_result_2.GetModified[IDesignBody]()[0]
lf = open(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\log.dat","w")
lf.write("Check1\n")
# Named Selections
n = len(nearbody.Faces)
cent_x = []
cent_y = []
cent_z = []
for i in range(n):
    face = nearbody.Faces[i]
    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))
    cent_x.append(face_center.X)
    cent_y.append(face_center.Y)
    cent_z.append(face_center.Z)
i_per1_near = cent_y.index(min(cent_y))
i_per2_near = cent_y.index(max(cent_y))
cent_x[i_per1_near] = -150.0
cent_x[i_per2_near] = -150.0
i_duct_near = cent_x.index(max(cent_x))
cent_x[i_duct_near] = -150.0
i_up_near = cent_z.index(max(cent_z))
i_down_near = cent_z.index(min(cent_z))
cent_x[i_up_near] = -150.0
cent_x[i_down_near] = -150.0
i_blade1 = cent_x.index(max(cent_x))
cent_x[i_blade1] = -150.0
i_blade2 = cent_x.index(max(cent_x))
cent_x[i_blade2] = -150.0
if cent_z[i_blade1] < cent_z[i_blade2]:
    temp = i_blade1
    i_blade1 = i_blade2
    i_blade2 = temp
i_hub_near = cent_x.index(max(cent_x))
cent_x[i_hub_near] = -150.0
n = len(nested.Faces)
cent_x = []
cent_y = []
cent_z = []
for i in range(n):
    face = nested.Faces[i]
    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))
    cent_x.append(face_center.X)
    cent_y.append(face_center.Y)
    cent_z.append(face_center.Z)
i_per1_nested = cent_y.index(min(cent_y))
i_per2_nested = cent_y.index(max(cent_y))
i_up = cent_z.index(max(cent_z))
i_down = cent_z.index(min(cent_z))
i_side = cent_x.index(max(cent_x))
cent_x[i_per1_nested] = -150.0
cent_x[i_per2_nested] = -150.0
cent_z[i_per1_nested] = -150.0
cent_z[i_per2_nested] = -150.0
cent_x[i_side] = -150.0
cent_z[i_side] = -150.0
cent_x[i_up] = -150.0
cent_z[i_up] = -150.0
cent_x[i_down] = -150.0
cent_z[i_down] = -150.0
i_duct1 = cent_x.index(max(cent_x))
cent_x[i_duct1] = -150.0
cent_z[i_duct1] = -150.0
i_duct2 = cent_x.index(max(cent_x))
cent_x[i_duct2] = -150.0
cent_z[i_duct2] = -150.0
i_duct3 = cent_x.index(max(cent_x))
cent_x[i_duct3] = -150.0
cent_z[i_duct3] = -150.0
i_hub1 = cent_z.index(max(cent_z))
cent_x[i_hub1] = -150.0
cent_z[i_hub1] = -150.0
i_up_nested = cent_z.index(max(cent_z))
cent_x[i_up_nested] = -150.0
cent_z[i_up_nested] = -150.0
i_down_nested = cent_z.index(max(cent_z))
cent_x[i_down_nested] = -150.0
cent_z[i_down_nested] = -150.0
i_stator1 = cent_x.index(max(cent_x))
cent_x[i_stator1] = -150.0
i_stator2 = cent_x.index(max(cent_x))
cent_x[i_stator2] = -150.0
if cent_z[i_stator1] < cent_z[i_stator2]:
    temp = i_stator1
    i_stator1 = i_stator2
    i_stator2 = temp
i_hub2 = cent_x.index(max(cent_x))
cent_x[i_hub2] = -150.0
i_hub3 = cent_x.index(max(cent_x))
cent_x[i_hub3] = -150.0
n = len(offbody.Faces)
cent_x = []
cent_y = []
cent_z = []
for i in range(n):
    face = offbody.Faces[i]
    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))
    cent_x.append(face_center.X)
    cent_y.append(face_center.Y)
    cent_z.append(face_center.Z)
i_per1_off = cent_y.index(min(cent_y))
i_per2_off = cent_y.index(max(cent_y))
i_wall = cent_x.index(max(cent_x))
i_inlet = cent_z.index(max(cent_z))
i_outlet = cent_z.index(min(cent_z))
# Create Named Selection Group
primarySelection = Selection.Create([offbody])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")
primarySelection = Selection.Create([nested])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "nested")
primarySelection = Selection.Create([nearbody])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "nearbody")
primarySelection = Selection.Create([offbody.Faces[i_inlet]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "inlet")
primarySelection = Selection.Create([offbody.Faces[i_wall]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "wall")
primarySelection = Selection.Create([offbody.Faces[i_outlet]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "outlet")
primarySelection = Selection.Create([offbody.Faces[i_per1_off],nested.Faces[i_per1_nested]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per1_off")
primarySelection = Selection.Create([nearbody.Faces[i_per1_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per1_near")
primarySelection = Selection.Create([offbody.Faces[i_per2_off],nested.Faces[i_per2_nested]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per2_off")
primarySelection = Selection.Create([nearbody.Faces[i_per2_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per2_near")
primarySelection = Selection.Create([nearbody.Faces[i_blade1],nearbody.Faces[i_blade2]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "blade")
primarySelection = Selection.Create([nearbody.Faces[i_duct_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "duct1")
primarySelection = Selection.Create([nested.Faces[i_duct1],nested.Faces[i_duct2],nested.Faces[i_duct3]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "duct2")
primarySelection = Selection.Create([nearbody.Faces[i_hub_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "hub1")
primarySelection = Selection.Create([nested.Faces[i_hub1],nested.Faces[i_hub2],nested.Faces[i_hub3]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "hub2")
primarySelection = Selection.Create([nearbody.Faces[i_up_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "interface_up_near")
primarySelection = Selection.Create([nearbody.Faces[i_down_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "interface_down_near")
primarySelection = Selection.Create([nested.Faces[i_stator1],nested.Faces[i_stator2]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "stator")
primarySelection = Selection.Create([nested.Faces[i_up_nested]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "interface_up_nested")
primarySelection = Selection.Create([nested.Faces[i_down_nested]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "interface_down_nested")
options = ShareTopologyOptions()
options.Tolerance = MM(0.0005)
command = ShareTopology(options)
problemAreas = command.FindProblemAreas()
command.ExcludeProblemArea(FaceSelection.Create([nested.Faces[i_up_nested],nearbody.Faces[i_up_near]]))
command.ExcludeProblemArea(FaceSelection.Create([nested.Faces[i_down_nested],nearbody.Faces[i_down_near]]))
result = command.Fix()
# Save Project As
File.SaveAs(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\geo.dsco")
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create([nested])
simulation.SuppressBodies(selection,True)
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create([offbody])
simulation.SuppressBodies(selection,True)
Workbench.Fluent.ExportPMDB(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\case_near.pmdb")
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create(nested)
simulation.SuppressBodies(selection, False)
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create([offbody])
simulation.SuppressBodies(selection, False)
simulation = Solution.Simulation.GetByLabel("Simulation 1")
selection = BodySelection.Create([nearbody])
simulation.SuppressBodies(selection,True)
Workbench.Fluent.ExportPMDB(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\case_off.pmdb")
Workbench.Fluent.ExportPMDB(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\optimization_2_cpu\case6\case.pmdb")
