# Python Script, API Version = V242
import shutil
# USER INPUT
case_folder = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case"
num_blades = 13
# Set 3D View
mode = InteractionMode.Solid
sketch_result = ViewHelper.SetViewMode(mode)
# General Definitions
y_axis = Line.Create(Point.Origin, Direction.DirZ)
scale_factor = GetActiveWindow().Units.Length.ConversionFactor
scale_origin = Point.Create(MM(0), MM(0), MM(0))
angle = 2 * math.pi / 13
half_angle = angle / 2
# Clear Project
selection = Selection.SelectAll()
if selection.Count > 0:
    Delete.Execute(selection)
ComponentHelper.DeleteEmptyComponents(GetRootPart())
# Insert Geometry
File.InsertGeometry(r"Z:\UFX_dilhara\Ansys\tempest-2\case60\case60_noStator.STEP")
rotor_body = BodySelection.Create(GetRootPart().Components[0].Content.Bodies[0])
stl_file = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case\\geo.stl"
# Save Project As
File.SaveAs(stl_file)
# EndBlock
# Save Project As
File.SaveAs(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case\geo0.dsco")
# Enclosure
sectionPlane = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(0)),Direction.DirZ, Direction.DirX))
result = ViewHelper.SetSketchPlane(sectionPlane)
point1 = Point2D.Create(M(0.2),M(0))
point2 = Point2D.Create(M(-0.54),M(0))
point3 = Point2D.Create(M(-0.54),M(0.45))
result = SketchRectangle.Create(point1, point2, point3)
point1 = Point2D.Create(M(3.0),M(0))
point2 = Point2D.Create(M(-3.0),M(0))
point3 = Point2D.Create(M(-3.0),M(3.0))
result = SketchRectangle.Create(point1, point2, point3)
mode = InteractionMode.Solid
sketch_result = ViewHelper.SetViewMode(mode)
get_faces = sketch_result.GetCreated[IDesignFace]()
options = RevolveFaceOptions()
options.PullSymmetric = True
options.ExtrudeType = ExtrudeType.ForceIndependent
revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), y_axis, half_angle, options)
targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())
merge_result_0 = Combine.Merge(targets)
revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), y_axis, half_angle, options)
targets = Selection.Create(revolve_result_1.GetCreated[IDesignBody]())
merge_result_1 = Combine.Merge(targets)
targets = BodySelection.Create(merge_result_0.GetModified[IDesignBody]()[0], merge_result_1.GetModified[IDesignBody]()[0])
tools = rotor_body
options = MakeSolidsOptions()
options.KeepCutter = False
options.SubtractFromTarget = True
result = Combine.Intersect(targets, tools, options)
b1 = GetRootPart().Bodies[0]
selection = Selection.Create([b1])
centroid = MeasureHelper.GetCenterOfMass(selection)
if centroid.X > 0.3:
    offbody = b1
    nearbody = GetRootPart().Bodies[1]
else:
    offbody = GetRootPart().Bodies[1]
    nearbody = b1
lf = open(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case\log.dat","w")
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
cent_x[i_per1_near] = -300.0
cent_x[i_per2_near] = -300.0
i_side = cent_x.index(max(cent_x))
cent_x[i_side] = -300.0
i_up = cent_z.index(max(cent_z))
i_down = cent_z.index(min(cent_z))
cent_x[i_up] = -300.0
cent_x[i_down] = -300.0
i_duct1 = cent_x.index(max(cent_x))
cent_x[i_duct1] = -300.0
i_duct2 = cent_x.index(max(cent_x))
cent_x[i_duct2] = -300.0
i_blade1 = cent_x.index(max(cent_x))
cent_x[i_blade1] = -300.0
i_blade2 = cent_x.index(max(cent_x))
cent_x[i_blade2] = -300.0
if cent_z[i_blade1] < cent_z[i_blade2]:
    temp = i_blade1
    i_blade1 = i_blade2
    i_blade2 = temp
i_hub1 = cent_x.index(max(cent_x))
cent_x[i_hub1] = -300.0
i_hub2 = cent_x.index(max(cent_x))
cent_x[i_hub2] = -300.0
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
options = ShareTopologyOptions()
options.Tolerance = M(0.0005)
result = ShareTopology.FindAndFix(options)
# Create Named Selection Group
primarySelection = Selection.Create([offbody])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")
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
primarySelection = Selection.Create([offbody.Faces[i_per1_off],nearbody.Faces[i_per1_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per1")
primarySelection = Selection.Create([offbody.Faces[i_per2_off],nearbody.Faces[i_per2_near]])
secondarySelection = Selection.Empty()
result = NamedSelection.Create(primarySelection, secondarySelection, "per2")
input("Check current names selections and add blade1, blade2, duct1, duct2, hub1, and hub2.")
# Save Project As
File.SaveAs(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case\geo.dsco")
Workbench.Fluent.ExportPMDB(r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\test\general_case\case.pmdb")
