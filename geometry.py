from click import File
import numpy as np
import math
import time
from classes import Rotor,Duct,Hub,Stator
import os
from airfoil_gen import naca_airfoil_4digits







def run_geo(variables,constants,case_folder,id,istator=False):

    time0 = time.time()
    

    try:
        os.makedirs(case_folder, exist_ok=True)
    except FileExistsError:
        print(f"Directory '{case_folder}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{case_folder}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    time1 = time.time()
    print(f"Folder created: {case_folder}")
   

    
    
    rotor = Rotor(variables,constants,id)
    duct = Duct(variables,constants,id)
    hub = Hub(variables,constants,id)

    
    
    if istator:
        stator = Stator(variables,constants,rotor,hub,duct,id)
        make_stator_curves(stator,case_folder)
        print("Stator structure created, airfoil files written.")

        blade_zmax = min(1.3*max(rotor.chord)*0.25,min(max(duct.xz[:,1])*0.95,max(hub.xz[:,1])*0.95))
        blade_zmin = max(-1.3*max(rotor.chord)*0.75,max(stator.Z) + max(stator.chord)*0.25*1.1)

        if blade_zmin > -max(rotor.chord)*0.75:
            raise ValueError("Not enough clearance between rotor and stator")

    else:
        stator = None
        blade_zmax = min(1.5*max(rotor.chord),min(duct.xz[:,1],hub.xz[:,1]))
        blade_z_min = -1.5*max(rotor.chord)
        

    blade_lims = [blade_zmax, blade_zmin]



    time2 = time.time()
    print(f"Rotor, duct, and hub structures created in {time2-time1:.1f} seconds")

    make_curves(rotor,duct,hub,case_folder)
    time3 = time.time()
    print(f"Curve files written in {time3-time2:.1f} seconds")
    
    if istator:
        script_file = make_discovery_script(rotor,duct,hub,case_folder,blade_lims,istator,stator)
    else:
        script_file = make_discovery_script(rotor,duct,hub,case_folder,blade_lims,istator)
    time3 = time.time()
    print(f"Discovery script written in {time3-time2:.1f} seconds")
   
    return script_file, blade_lims, rotor, stator


def make_stator_curves(stator,case_folder):
    for i in range(stator.nr):
        pts = []
        pts = naca_airfoil_4digits(stator.chord[i],stator.air_camber[i]/100,0.4,stator.air_thick[i]/100,stator.theta[i]*np.pi/180,sweep=0)
        file = open(os.path.join(case_folder,f"stator_cross_{i}.txt"),'w')
        file.write("3d=true\npolyline=false\nfit=false\n")
        for j in range(len(pts)):
            z = pts[j][1] + stator.Z[i]
            x = stator.r[i]*stator.R_tip
            y = -pts[j][0] #clockwise
            file.write(f"{z} {x} {y}\n")
        file.close()    



def make_curves(rotor,duct,hub,case_folder):

    # duct
    file = open(os.path.join(case_folder,"duct.txt"),'w')
    file.write("3d=true\npolyline=false\nfit=false\n")
    for i in range(len(duct.xz)):
        #file.write(f"0 {duct.xz[i][0]} {duct.xz[i][1]}\n")
        file.write(f"{duct.xz[i][1]} 0 {duct.xz[i][0]}\n")
    file.close()

    # hub
    file = open(os.path.join(case_folder,"hub.txt"),'w')
    file.write("3d=true\npolyline=false\nfit=false\n")
    for i in range(len(hub.xz)-1,-1,-2):
        file.write(f"{hub.xz[i][1]} 0 {-hub.xz[i][0]}\n")
    for i in range(len(hub.xz)):
        file.write(f"{hub.xz[i][1]} 0 {hub.xz[i][0]}\n") 
    file.close()

    # blade profiles
    for i in range(rotor.nr):
        pts = []
        pts = naca_airfoil_4digits(rotor.chord[i],rotor.air_camber[i]/100,0.4,rotor.air_thick[i]/100,rotor.theta[i]*np.pi/180,rotor.sweep[i])
        file = open(os.path.join(case_folder,f"blade_cross_{i}.txt"),'w')
        file.write("3d=true\npolyline=false\nfit=false\n")
        for j in range(len(pts)):
            z = pts[j][1]
            x = rotor.r[i]*rotor.R_tip
            y = pts[j][0]
            if x == 0:
                dspi = 0
            else:
                dspi = math.atan(rotor.sweep[i]/(x))
            x2 = x #x*math.cos(dspi) - y*math.sin(dspi)
            y2 = y #x*math.sin(dspi) + y*math.cos(dspi)
            file.write(f"{z} {x2} {y2}\n")
            #file.write(f"{pts[j][1]} {rotor.r[i]*rotor.R_tip} {pts[j][0]}\n")   
        file.close()    

def make_discovery_script(rotor,duct,hub,case_folder,blade_lims,istator=False,stator=None):
    
    near_zmax = max(max(hub.xz[:,1]),max(duct.xz[:,1])) + rotor.R_tip/2
    near_zmin = min(min(hub.xz[:,1]),min(duct.xz[:,1])) - rotor.R_tip/2
    near_rmax = max(duct.xz[:,0]) + rotor.R_tip/2

    off_zmax = rotor.R_tip * 10
    off_zmin = -rotor.R_tip * 10
    off_rmax = rotor.R_tip * 10

    if istator:
        blade_zmax = blade_lims[0] #min(1.5*max(rotor.chord),min(duct.xz[:,1],hub.xz[:,1]))
        blade_zmin = blade_lims[1] #max(-1.5*max(rotor.chord),max(stator.Z) + max(stator.chord)*0.25)
        blade_rmax = rotor.R_tip + duct.Width/2

    #script_file = case_folder+f'\\disc_script.py'
    script_file = os.path.join(case_folder,f'DiscoveryGeometryBuilder.py')
    file = open(script_file,'w')
    
    file.write("# Python Script, API Version = V242\nimport shutil\n# USER INPUT\n")
    file.write(f"case_folder = r\"{case_folder}\"\n")
    file.write(f"num_blades = {rotor.Nb}\n")

    file.write("# Set 3D View\nmode = InteractionMode.Solid\nsketch_result = ViewHelper.SetViewMode(mode)\n")

    file.write(
        f"# General Definitions\n"
        f"z_axis = Line.Create(Point.Origin, Direction.DirZ)\n"
        f"scale_factor = GetActiveWindow().Units.Length.ConversionFactor\n"
        f"scale_origin = Point.Create(MM(0), MM(0), MM(0))\n"
        f"angle = 2 * math.pi / {rotor.Nb}\n"
        f"half_angle = angle / 2\n"
    )

    file.write(
        f"# Clear Project\n"
        f"selection = Selection.SelectAll()\n"
        f"if selection.Count > 0:\n"
        f"    Delete.Execute(selection)\n"
        f"ComponentHelper.DeleteEmptyComponents(GetRootPart())\n"
    )

    file.write(
        f'# Blade\n'
        f'airfoil_files = []\n'
    )

    for i in range(rotor.nr):
        file.write(
            fr'File.InsertGeometry(r"{case_folder}\\\\blade_cross_{i}.txt")'
            f'\nselection = Selection.Create([GetRootPart().Curves[0]])\n'
            f'result = Scale.Execute(selection, scale_origin, scale_factor, False)\n'
            f'empty = Selection.Empty()\n'
            f'options = FillOptions()\n'
            f'airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))\n'
            f'Delete.Execute(selection)\n'
        )

    file.write(
        'selection = FaceSelection.Create([af.CreatedFaces[0] for af in airfoil_files])\n'
        'options = LoftOptions()\n'
        'options.GeometryCommandOptions = GeometryCommandOptions()\n'
        'blade_result = Loft.Create(selection, None, options)\n'
        'blade_body = blade_result.GetCreated[IDesignBody]()[0]\n'
    )

    file.write(
        '# Blade Patterning\n'
        'selection = BodySelection.Create(blade_body)\n'
        'options = MoveOptions()\n'
        'options.CreatePatterns = True\n'
        'init_pattern_result = Move.Rotate(selection, z_axis, angle, options)\n'
        'pattern = ComponentSelection.Create(init_pattern_result.GetCreated[IComponent]())\n'
        'data = CircularPatternModificationData()\n'
        'data.CircularCount = num_blades\n'
        'data.StepAngle = angle\n'
        'pattern_result = Pattern.ModifyCircular(pattern, data)\n'
        'pattern_bodies = BodySelection.Create(pattern.Components[0].GetAllBodies())\n'
        'ComponentHelper.MoveBodiesToComponent(pattern_bodies, GetRootPart(), False)\n'
        'ComponentHelper.DeleteEmptyComponents(GetRootPart())\n'
    )

   ## If stator required
   #  
    if istator:
        file.write(f"num_sblades = {stator.Nb}\n")

        file.write(
            f"s_angle = 2 * math.pi / {stator.Nb}\n"
            f"s_half_angle = s_angle / 2\n"
        )

        file.write(
            f'# Stator\n'
            f's_airfoil_files = []\n'
        )

        for i in range(rotor.nr):
            file.write(
                fr'File.InsertGeometry(r"{case_folder}\\\\stator_cross_{i}.txt")'
                f'\nselection = Selection.Create([GetRootPart().Curves[0]])\n'
                f'result = Scale.Execute(selection, scale_origin, scale_factor, False)\n'
                f'empty = Selection.Empty()\n'
                f'options = FillOptions()\n'
                f's_airfoil_files.append(Fill.Execute(selection, empty, options, FillMode.ThreeD))\n'
                f'Delete.Execute(selection)\n'
            )

        file.write(
            'selection = FaceSelection.Create([af.CreatedFaces[0] for af in s_airfoil_files])\n'
            'options = LoftOptions()\n'
            'options.GeometryCommandOptions = GeometryCommandOptions()\n'
            'stator_result = Loft.Create(selection, None, options)\n'
            'stator_body = stator_result.GetCreated[IDesignBody]()[0]\n'
        )

        file.write(
            '# Stator Blade Patterning\n'
            'selection = BodySelection.Create(stator_body)\n'
            'options = MoveOptions()\n'
            'options.CreatePatterns = True\n'
            'init_pattern_result = Move.Rotate(selection, z_axis, s_angle, options)\n'
            'pattern = ComponentSelection.Create(init_pattern_result.GetCreated[IComponent]())\n'
            'data = CircularPatternModificationData()\n'
            'data.CircularCount = num_sblades\n'
            'data.StepAngle = s_angle\n'
            'spattern_result = Pattern.ModifyCircular(pattern, data)\n'
            'spattern_bodies = BodySelection.Create(pattern.Components[0].GetAllBodies())\n'
            'ComponentHelper.MoveBodiesToComponent(spattern_bodies, GetRootPart(), False)\n'
            'ComponentHelper.DeleteEmptyComponents(GetRootPart())\n'
        )




    file.write(
        f'# Duct\n'
        fr'File.InsertGeometry(r"{case_folder}\\duct.txt")'
        '\nselection = Selection.Create([GetRootPart().Curves[0]])\n'
        'result = Scale.Execute(selection, scale_origin, scale_factor, False)\n'
        'secondarySelection = Selection.Empty()\n'
        'options = FillOptions()\n'
        'result = Fill.Execute(selection, secondarySelection, options, FillMode.ThreeD)\n'
        'Delete.Execute(selection)\n'
        'selection = Selection.Create(result.GetCreated[IDesignFace]()[0])\n'
        'options = RevolveFaceOptions()\n'
        'axisSelection = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[2])\n'
        'axis = RevolveFaces.GetAxisFromSelection(selection, axisSelection, True)\n'
        'options.ExtrudeType = ExtrudeType.Add\n'
        'result = RevolveFaces.Execute(selection, axis, DEG(360), options)\n'
        # EndBlock"
    )

    file.write(
        f'# Hub\n'
        fr'File.InsertGeometry(r"{case_folder}\\hub.txt")'
        '\nselection = Selection.Create([GetRootPart().Curves[0]])\n'
        'result = Scale.Execute(selection, scale_origin, scale_factor, False)\n'
        'secondarySelection = Selection.Empty()\n'
        'options = FillOptions()\n'
        'result = Fill.Execute(selection, secondarySelection, options, FillMode.ThreeD)\n'
        'Delete.Execute(selection)\n'
        'selection = Selection.Create(result.GetCreated[IDesignFace]()[0])\n'
        'z_axis = Line.Create(Point.Origin, Direction.DirZ)\n'
        'options = RevolveFaceOptions()\n'
        'options.ExtrudeType = ExtrudeType.Cut\n'
        'result = RevolveFaces.Execute(selection, z_axis, DEG(-360), options)\n'
        'rotor_body = result.GetModified[IDesignBody]()[0]\n'
    )

    
    file.write(
        fr'stl_file = r"{case_folder}\\geo.stl"'
        f'\n# Save Project As\nFile.SaveAs(stl_file)\n# EndBlock\n'
    )

    geo_file0 = f"{case_folder}\\geo0.dsco"
    if os.path.exists(geo_file0):
        print("Ovewriting")
        os.remove(geo_file0)
    file.write(f"# Save Project As\nFile.SaveAs(r\"{geo_file0}\")\n")


    if istator:
        file.write(
            '# Enclosure\n'
            'sectionPlane = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(0)),Direction.DirZ, Direction.DirX))\n'
            'result = ViewHelper.SetSketchPlane(sectionPlane)\n'
            f'point1 = Point2D.Create(M({near_zmax}),M(0))\n'
            f'point2 = Point2D.Create(M({near_zmin}),M(0))\n'
            f'point3 = Point2D.Create(M({near_zmin}),M({near_rmax}))\n'
            'result = SketchRectangle.Create(point1, point2, point3)\n'
            f'point1 = Point2D.Create(M({off_zmax}),M(0))\n'
            f'point2 = Point2D.Create(M({off_zmin}),M(0))\n'
            f'point3 = Point2D.Create(M({off_zmin}),M({off_rmax}))\n'
            'result = SketchRectangle.Create(point1, point2, point3)\n'
            f'point1 = Point2D.Create(M({blade_zmax}),M(0))\n'
            f'point2 = Point2D.Create(M({blade_zmin}),M(0))\n'
            f'point3 = Point2D.Create(M({blade_zmin}),M({blade_rmax}))\n'
            'result = SketchRectangle.Create(point1, point2, point3)\n'
            'mode = InteractionMode.Solid\n'
            'sketch_result = ViewHelper.SetViewMode(mode)\n'
            'get_faces = sketch_result.GetCreated[IDesignFace]()\n'
            'options = RevolveFaceOptions()\n'
            'options.PullSymmetric = True\n'
            'options.ExtrudeType = ExtrudeType.ForceIndependent\n'
            'revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), z_axis, s_half_angle, options)\n'
            'targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())\n'
            'merge_result_0 = Combine.Merge(targets)\n'
            'revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), z_axis, s_half_angle, options)\n'
            'targets = Selection.Create(revolve_result_1.GetCreated[IDesignBody]())\n'
            'merge_result_1 = Combine.Merge(targets)\n'
            'revolve_result_2 = RevolveFaces.Execute(Selection.Create([get_faces[2]]), z_axis, half_angle, options)\n'
            'targets = Selection.Create(revolve_result_2.GetCreated[IDesignBody]())\n'
            'merge_result_2 = Combine.Merge(targets)\n'
            'targets = BodySelection.Create(merge_result_2.GetModified[IDesignBody]()[0])\n'
            'tools = BodySelection.Create(rotor_body)\n'
            'options = MakeSolidsOptions()\n'
            'options.KeepCutter = True\n'
            'options.SubtractFromTarget = True\n'
            'result = Combine.Intersect(targets, tools, options)\n'
            'tools = BodySelection.Create(rotor_body)\n'
            'options = MakeSolidsOptions()\n'
            'options.KeepCutter = False\n'
            'options.SubtractFromTarget = True\n'
            'targets = BodySelection.Create(merge_result_0.GetModified[IDesignBody]()[0])\n'
            'result = Combine.Intersect(targets, tools, options)\n'
        )

        file.write(
            'nested = merge_result_0.GetModified[IDesignBody]()[0]\n'
            'offbody = merge_result_1.GetModified[IDesignBody]()[0]\n'
            'nearbody = merge_result_2.GetModified[IDesignBody]()[0]\n'
        )

    else:
        file.write(
            '# Enclosure\n'
            'sectionPlane = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(0)),Direction.DirZ, Direction.DirX))\n'
            'result = ViewHelper.SetSketchPlane(sectionPlane)\n'
            f'point1 = Point2D.Create(M({near_zmax}),M(0))\n'
            f'point2 = Point2D.Create(M({near_zmin}),M(0))\n'
            f'point3 = Point2D.Create(M({near_zmin}),M({near_rmax}))\n'
            'result = SketchRectangle.Create(point1, point2, point3)\n'
            f'point1 = Point2D.Create(M({off_zmax}),M(0))\n'
            f'point2 = Point2D.Create(M({off_zmin}),M(0))\n'
            f'point3 = Point2D.Create(M({off_zmin}),M({off_rmax}))\n'
            'result = SketchRectangle.Create(point1, point2, point3)\n'
            'mode = InteractionMode.Solid\n'
            'sketch_result = ViewHelper.SetViewMode(mode)\n'
            'get_faces = sketch_result.GetCreated[IDesignFace]()\n'
            'options = RevolveFaceOptions()\n'
            'options.PullSymmetric = True\n'
            'options.ExtrudeType = ExtrudeType.ForceIndependent\n'
            'revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), z_axis, half_angle, options)\n'
            'targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())\n'
            'merge_result_0 = Combine.Merge(targets)\n'
            'revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), z_axis, half_angle, options)\n'
            'targets = Selection.Create(revolve_result_1.GetCreated[IDesignBody]())\n'
            'merge_result_1 = Combine.Merge(targets)\n'
            'targets = BodySelection.Create(merge_result_0.GetModified[IDesignBody]()[0], merge_result_1.GetModified[IDesignBody]()[0])\n'
            'tools = BodySelection.Create(rotor_body)\n'
            'options = MakeSolidsOptions()\n'
            'options.KeepCutter = False\n'
            'options.SubtractFromTarget = True\n'
            'result = Combine.Intersect(targets, tools, options)\n'
        )

        file.write(
            'b1 = GetRootPart().Bodies[0]\n'
            'selection = Selection.Create([b1])\n'
            'centroid = MeasureHelper.GetCenterOfMass(selection)\n' 
            f'if centroid.X > {rotor.R_tip}:\n'
            '    offbody = b1\n'
            '    nearbody = GetRootPart().Bodies[1]\n'
            'else:\n'
            '    offbody = GetRootPart().Bodies[1]\n'
            '    nearbody = b1\n'
        )

    log_file = f"{case_folder}\\log.dat"
    if os.path.exists(log_file):
        print("Ovewriting")
        os.remove(log_file)

    file.write(f"lf = open(r\"{log_file}\",\"w\")\n")
    file.write("lf.write(\"Check1\\n\")\n")

    

    if istator:
        file.write(
            '# Named Selections\n'
            'n = len(nearbody.Faces)\n'
            'cent_x = []\n'
            'cent_y = []\n'
            'cent_z = []\n'
            'for i in range(n):\n'
            '    face = nearbody.Faces[i]\n'
            '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
            '    cent_x.append(face_center.X)\n'
            '    cent_y.append(face_center.Y)\n'
            '    cent_z.append(face_center.Z)\n'
        )
        file.write(
            'i_per1_near = cent_y.index(min(cent_y))\n'
            'i_per2_near = cent_y.index(max(cent_y))\n'
            f'cent_x[i_per1_near] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_per2_near] = {-1000*rotor.R_tip}\n'
            'i_duct_near = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct_near] = {-1000*rotor.R_tip}\n'
            'i_up_near = cent_z.index(max(cent_z))\n'
            'i_down_near = cent_z.index(min(cent_z))\n'
            f'cent_x[i_up_near] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_down_near] = {-1000*rotor.R_tip}\n'
            'i_blade1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_blade1] = {-1000*rotor.R_tip}\n'
            'i_blade2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_blade2] = {-1000*rotor.R_tip}\n'
            'if cent_z[i_blade1] < cent_z[i_blade2]:\n'
            '    temp = i_blade1\n'
            '    i_blade1 = i_blade2\n'
            '    i_blade2 = temp\n'
            'i_hub_near = cent_x.index(max(cent_x))\n'
            f'cent_x[i_hub_near] = {-1000*rotor.R_tip}\n'

        )
            
        file.write(
            'n = len(nested.Faces)\n'
            'cent_x = []\n'
            'cent_y = []\n'
            'cent_z = []\n'
            'for i in range(n):\n'
            '    face = nested.Faces[i]\n'
            '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
            '    cent_x.append(face_center.X)\n'
            '    cent_y.append(face_center.Y)\n'
            '    cent_z.append(face_center.Z)\n'
        )
        file.write(
            'i_per1_nested = cent_y.index(min(cent_y))\n'
            'i_per2_nested = cent_y.index(max(cent_y))\n'
            'i_up = cent_z.index(max(cent_z))\n'
            'i_down = cent_z.index(min(cent_z))\n'
            'i_side = cent_x.index(max(cent_x))\n'
            f'cent_x[i_per1_nested] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_per2_nested] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_per1_nested] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_per2_nested] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_side] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_side] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_up] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_up] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_down] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_down] = {-1000*rotor.R_tip}\n'
            'i_duct1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct1] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_duct1] = {-1000*rotor.R_tip}\n'
            'i_duct2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct2] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_duct2] = {-1000*rotor.R_tip}\n'
            'i_duct3 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct3] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_duct3] = {-1000*rotor.R_tip}\n'
            'i_hub1 = cent_z.index(max(cent_z))\n'
            f'cent_x[i_hub1] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_hub1] = {-1000*rotor.R_tip}\n'
        )
        file.write(
            'i_up_nested = cent_z.index(max(cent_z))\n'
            f'cent_x[i_up_nested] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_up_nested] = {-1000*rotor.R_tip}\n'
            'i_down_nested = cent_z.index(max(cent_z))\n'
            f'cent_x[i_down_nested] = {-1000*rotor.R_tip}\n'
            f'cent_z[i_down_nested] = {-1000*rotor.R_tip}\n'
        )
        
        file.write(
            'i_stator1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_stator1] = {-1000*rotor.R_tip}\n'
            'i_stator2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_stator2] = {-1000*rotor.R_tip}\n'
            'if cent_z[i_stator1] < cent_z[i_stator2]:\n'
            '    temp = i_stator1\n'
            '    i_stator1 = i_stator2\n'
            '    i_stator2 = temp\n'
            'i_hub2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_hub2] = {-1000*rotor.R_tip}\n'
            'i_hub3 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_hub3] = {-1000*rotor.R_tip}\n'

        )

        file.write(
            'n = len(offbody.Faces)\n'
            'cent_x = []\n'
            'cent_y = []\n'
            'cent_z = []\n'
            'for i in range(n):\n'
            '    face = offbody.Faces[i]\n'
            '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
            '    cent_x.append(face_center.X)\n'
            '    cent_y.append(face_center.Y)\n'
            '    cent_z.append(face_center.Z)\n'
        )

        file.write(
            'i_per1_off = cent_y.index(min(cent_y))\n'
            'i_per2_off = cent_y.index(max(cent_y))\n'
            'i_wall = cent_x.index(max(cent_x))\n'
            'i_inlet = cent_z.index(max(cent_z))\n'
            'i_outlet = cent_z.index(min(cent_z))\n'
        )

        file.write(
            '# Create Named Selection Group\n'
            'primarySelection = Selection.Create([offbody])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")\n'
            'primarySelection = Selection.Create([nested])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "nested")\n'
            'primarySelection = Selection.Create([nearbody])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "nearbody")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_inlet]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "inlet")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_wall]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "wall")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_outlet]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "outlet")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_per1_off],nested.Faces[i_per1_nested]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per1_off")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_per1_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per1_near")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_per2_off],nested.Faces[i_per2_nested]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per2_off")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_per2_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per2_near")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_blade1],nearbody.Faces[i_blade2]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "blade")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_duct_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "duct1")\n'
            'primarySelection = Selection.Create([nested.Faces[i_duct1],nested.Faces[i_duct2],nested.Faces[i_duct3]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "duct2")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_hub_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "hub1")\n'
            'primarySelection = Selection.Create([nested.Faces[i_hub1],nested.Faces[i_hub2],nested.Faces[i_hub3]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "hub2")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_up_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "interface_up_near")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_down_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "interface_down_near")\n'
            'primarySelection = Selection.Create([nested.Faces[i_stator1],nested.Faces[i_stator2]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "stator")\n'
        )
        
        
        file.write(
            'primarySelection = Selection.Create([nested.Faces[i_up_nested]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "interface_up_nested")\n'
            'primarySelection = Selection.Create([nested.Faces[i_down_nested]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "interface_down_nested")\n'
        )
        
        
    else:

        file.write(
            '# Named Selections\n'
            'n = len(nearbody.Faces)\n'
            'cent_x = []\n'
            'cent_y = []\n'
            'cent_z = []\n'
            'for i in range(n):\n'
            '    face = nearbody.Faces[i]\n'
            '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
            '    cent_x.append(face_center.X)\n'
            '    cent_y.append(face_center.Y)\n'
            '    cent_z.append(face_center.Z)\n'
        )
        file.write(
            'i_per1_near = cent_y.index(min(cent_y))\n'
            'i_per2_near = cent_y.index(max(cent_y))\n'
            f'cent_x[i_per1_near] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_per2_near] = {-1000*rotor.R_tip}\n'
            'i_side = cent_x.index(max(cent_x))\n'
            f'cent_x[i_side] = {-1000*rotor.R_tip}\n'
            'i_up = cent_z.index(max(cent_z))\n'
            'i_down = cent_z.index(min(cent_z))\n'
            f'cent_x[i_up] = {-1000*rotor.R_tip}\n'
            f'cent_x[i_down] = {-1000*rotor.R_tip}\n'
            'i_duct1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct1] = {-1000*rotor.R_tip}\n'
            'i_duct2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_duct2] = {-1000*rotor.R_tip}\n'
            'i_blade1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_blade1] = {-1000*rotor.R_tip}\n'
            'i_blade2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_blade2] = {-1000*rotor.R_tip}\n'
            'if cent_z[i_blade1] < cent_z[i_blade2]:\n'
            '    temp = i_blade1\n'
            '    i_blade1 = i_blade2\n'
            '    i_blade2 = temp\n'
            'i_hub1 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_hub1] = {-1000*rotor.R_tip}\n'
            'i_hub2 = cent_x.index(max(cent_x))\n'
            f'cent_x[i_hub2] = {-1000*rotor.R_tip}\n'

        )

        file.write(
            'n = len(offbody.Faces)\n'
            'cent_x = []\n'
            'cent_y = []\n'
            'cent_z = []\n'
            'for i in range(n):\n'
            '    face = offbody.Faces[i]\n'
            '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
            '    cent_x.append(face_center.X)\n'
            '    cent_y.append(face_center.Y)\n'
            '    cent_z.append(face_center.Z)\n'
        )

        file.write(
            'i_per1_off = cent_y.index(min(cent_y))\n'
            'i_per2_off = cent_y.index(max(cent_y))\n'
            'i_wall = cent_x.index(max(cent_x))\n'
            'i_inlet = cent_z.index(max(cent_z))\n'
            'i_outlet = cent_z.index(min(cent_z))\n'
        )

        file.write(
            '# Create Named Selection Group\n'
            'primarySelection = Selection.Create([offbody])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")\n'
            'primarySelection = Selection.Create([nearbody])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "nearbody")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_inlet]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "inlet")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_wall]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "wall")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_outlet]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "outlet")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_per1_off],nearbody.Faces[i_per1_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per1")\n'
            'primarySelection = Selection.Create([offbody.Faces[i_per2_off],nearbody.Faces[i_per2_near]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "per2")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_blade1]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "blade1")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_blade2]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "blade2")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_duct1]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "duct1")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_duct2]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "duct2")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_hub1]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "hub1")\n'
            'primarySelection = Selection.Create([nearbody.Faces[i_hub2]])\n'
            'secondarySelection = Selection.Empty()\n'
            'result = NamedSelection.Create(primarySelection, secondarySelection, "hub2")\n'
        )

    # Share Topology

    if istator:
        file.write(
            'options = ShareTopologyOptions()\n'
            'options.Tolerance = MM(0.0005)\n'
            'command = ShareTopology(options)\n'
            'problemAreas = command.FindProblemAreas()\n'
            'command.ExcludeProblemArea(FaceSelection.Create([nested.Faces[i_up_nested],nearbody.Faces[i_up_near]]))\n'
            'command.ExcludeProblemArea(FaceSelection.Create([nested.Faces[i_down_nested],nearbody.Faces[i_down_near]]))\n'
            'result = command.Fix()\n'
        )
    else:
        file.write(f"options = ShareTopologyOptions()\noptions.Tolerance = M(0.0005)\nresult = ShareTopology.FindAndFix(options)\n")
    

    geo_file = f"{case_folder}\\geo.dsco"
    if os.path.exists(geo_file):
        print("Ovewriting")
        os.remove(geo_file)
    file.write(f"# Save Project As\nFile.SaveAs(r\"{geo_file}\")\n")

    
    if istator:
        # file.write(
        #     'selection = Selection.Create([nearbody])\n'
        #     'options = MoveOptions()\n'
        #     'axisSelection = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[2])\n'
        #     'shift_angle = half_angle + s_half_angle + 1\n'
        #     'result = Move.Rotate(selection, z_axis, shift_angle, options)\n'
        # )
            
        fluent_file_near = f"{case_folder}\\case_near.pmdb"
        fluent_file_off = f"{case_folder}\\case_off.pmdb"
        if os.path.exists(fluent_file_near):
            print("Ovewriting")
            os.remove(fluent_file_near)
        if os.path.exists(fluent_file_off):
            print("Ovewriting")
            os.remove(fluent_file_off)
        file.write(
            'simulation = Solution.Simulation.GetByLabel("Simulation 1")\n'
            'selection = BodySelection.Create([nested])\n'
            'simulation.SuppressBodies(selection,True)\n'
            'simulation = Solution.Simulation.GetByLabel("Simulation 1")\n'
            'selection = BodySelection.Create([offbody])\n'
            'simulation.SuppressBodies(selection,True)\n'
        )
        file.write(f'Workbench.Fluent.ExportPMDB(r\"{fluent_file_near}\")\n')
        file.write(
            'simulation = Solution.Simulation.GetByLabel("Simulation 1")\n'
            'selection = BodySelection.Create(nested)\n'
            'simulation.SuppressBodies(selection, False)\n'
            'simulation = Solution.Simulation.GetByLabel("Simulation 1")\n'
            'selection = BodySelection.Create([offbody])\n'
            'simulation.SuppressBodies(selection, False)\n'
            'simulation = Solution.Simulation.GetByLabel("Simulation 1")\n'
            'selection = BodySelection.Create([nearbody])\n'
            'simulation.SuppressBodies(selection,True)\n'
        )
        file.write(f'Workbench.Fluent.ExportPMDB(r\"{fluent_file_off}\")\n')
        # EndBlock

    else:
        fluent_file = f"{case_folder}\\case.pmdb"
        if os.path.exists(fluent_file):
            print("Ovewriting")
            os.remove(fluent_file)
        file.write(f"Workbench.Fluent.ExportPMDB(r\"{fluent_file}\")\n")
        
    

    fluent_file = f"{case_folder}\\case.pmdb"
    if os.path.exists(fluent_file):
        print("Ovewriting")
        os.remove(fluent_file)
    file.write(f"Workbench.Fluent.ExportPMDB(r\"{fluent_file}\")\n")


    file.close()

    return script_file




def run_geo_custom(case_folder,input_geo_file):

    time0 = time.time()
    

    try:
        os.makedirs(case_folder, exist_ok=True)
    except FileExistsError:
        print(f"Directory '{case_folder}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{case_folder}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    time1 = time.time()
    print(f"Folder created in {time1-time0}")

    time2 = time.time()
    
    script_file = make_custom_discovery_script(case_folder, input_geo_file)
    time3 = time.time()
    print(f"Discovery script written in {time3-time2:.1f} seconds")
   
    return script_file


def make_custom_discovery_script(case_folder,input_geo_file):
    
    near_zmax = float(input("Enter nearbody zmax: "))
    near_zmin = float(input("Enter near body zmin: "))
    near_rmax = float(input("Enter near body rmax: "))
    R_tip = float(input("Enter rotor tip radius: "))
    Nb = int(input("Enter number of blades: "))

    off_zmax = R_tip * 10
    off_zmin = -R_tip * 10
    off_rmax = R_tip * 10

    cwd = os.getcwd()
    case_folder = os.path.join(cwd, case_folder)
    #script_file = case_folder+f'\\disc_script.py'
    script_file = case_folder+f'\\DiscoveryGeometryBuilder.py'
    file = open(script_file,'w')
    
    file.write("# Python Script, API Version = V242\nimport shutil\n# USER INPUT\n")
    file.write(f"case_folder = r\"{case_folder}\"\n")
    file.write(f"num_blades = {Nb}\n")

    file.write("# Set 3D View\nmode = InteractionMode.Solid\nsketch_result = ViewHelper.SetViewMode(mode)\n")

    file.write(
        f"# General Definitions\n"
        f"z_axis = Line.Create(Point.Origin, Direction.DirZ)\n"
        f"scale_factor = GetActiveWindow().Units.Length.ConversionFactor\n"
        f"scale_origin = Point.Create(MM(0), MM(0), MM(0))\n"
        f"angle = 2 * math.pi / {Nb}\n"
        f"half_angle = angle / 2\n"
    )

    file.write(
        f"# Clear Project\n"
        f"selection = Selection.SelectAll()\n"
        f"if selection.Count > 0:\n"
        f"    Delete.Execute(selection)\n"
        f"ComponentHelper.DeleteEmptyComponents(GetRootPart())\n"
    )
    
    file.write(
        f"# Insert Geometry\n"
        f"File.InsertGeometry(r\"{input_geo_file}\")\n"
        f"rotor_body = BodySelection.Create(GetRootPart().Components[0].Content.Bodies[0])\n"
    )
    file.write(
        fr'stl_file = r"{case_folder}\\geo.stl"'
        f'\n# Save Project As\nFile.SaveAs(stl_file)\n# EndBlock\n'
    )

    geo_file0 = f"{case_folder}\\geo0.dsco"
    # if os.path.exists(geo_file0):
    #     print("Ovewriting")
    #     os.remove(geo_file0)
    file.write(f"# Save Project As\nFile.SaveAs(r\"{geo_file0}\")\n")

    file.write(
        '# Enclosure\n'
        'sectionPlane = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(0)),Direction.DirZ, Direction.DirX))\n'
        'result = ViewHelper.SetSketchPlane(sectionPlane)\n'
        f'point1 = Point2D.Create(M({near_zmax}),M(0))\n'
        f'point2 = Point2D.Create(M({near_zmin}),M(0))\n'
        f'point3 = Point2D.Create(M({near_zmin}),M({near_rmax}))\n'
        'result = SketchRectangle.Create(point1, point2, point3)\n'
        f'point1 = Point2D.Create(M({off_zmax}),M(0))\n'
        f'point2 = Point2D.Create(M({off_zmin}),M(0))\n'
        f'point3 = Point2D.Create(M({off_zmin}),M({off_rmax}))\n'
        'result = SketchRectangle.Create(point1, point2, point3)\n'
        'mode = InteractionMode.Solid\n'
        'sketch_result = ViewHelper.SetViewMode(mode)\n'
        'get_faces = sketch_result.GetCreated[IDesignFace]()\n'
        'options = RevolveFaceOptions()\n'
        'options.PullSymmetric = True\n'
        'options.ExtrudeType = ExtrudeType.ForceIndependent\n'
        'revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), z_axis, half_angle, options)\n'
        'targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())\n'
        'merge_result_0 = Combine.Merge(targets)\n'
        'revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), z_axis, half_angle, options)\n'
        'targets = Selection.Create(revolve_result_1.GetCreated[IDesignBody]())\n'
        'merge_result_1 = Combine.Merge(targets)\n'
        'targets = BodySelection.Create(merge_result_0.GetModified[IDesignBody]()[0], merge_result_1.GetModified[IDesignBody]()[0])\n'
        'tools = rotor_body\n'
        'options = MakeSolidsOptions()\n'
        'options.KeepCutter = False\n'
        'options.SubtractFromTarget = True\n'
        'result = Combine.Intersect(targets, tools, options)\n'
    )

    file.write(
        'b1 = GetRootPart().Bodies[0]\n'
        'selection = Selection.Create([b1])\n'
        'centroid = MeasureHelper.GetCenterOfMass(selection)\n' 
        f'if centroid.X > {R_tip}:\n'
        '    offbody = b1\n'
        '    nearbody = GetRootPart().Bodies[1]\n'
        'else:\n'
        '    offbody = GetRootPart().Bodies[1]\n'
        '    nearbody = b1\n'
    )

    log_file = f"{case_folder}\\log.dat"
    # if os.path.exists(log_file):
    #     print("Ovewriting")
    #     os.remove(log_file)

    file.write(f"lf = open(r\"{log_file}\",\"w\")\n")
    file.write("lf.write(\"Check1\\n\")\n")

    file.write(
        '# Named Selections\n'
        'n = len(nearbody.Faces)\n'
        'cent_x = []\n'
        'cent_y = []\n'
        'cent_z = []\n'
        'for i in range(n):\n'
        '    face = nearbody.Faces[i]\n'
        '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
        '    cent_x.append(face_center.X)\n'
        '    cent_y.append(face_center.Y)\n'
        '    cent_z.append(face_center.Z)\n'
    )

    file.write(
        'i_per1_near = cent_y.index(min(cent_y))\n'
        'i_per2_near = cent_y.index(max(cent_y))\n'
        f'cent_x[i_per1_near] = {-1000*R_tip}\n'
        f'cent_x[i_per2_near] = {-1000*R_tip}\n'
        'i_side = cent_x.index(max(cent_x))\n'
        f'cent_x[i_side] = {-1000*R_tip}\n'
        'i_up = cent_z.index(max(cent_z))\n'
        'i_down = cent_z.index(min(cent_z))\n'
        f'cent_x[i_up] = {-1000*R_tip}\n'
        f'cent_x[i_down] = {-1000*R_tip}\n'
        'i_duct1 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_duct1] = {-1000*R_tip}\n'
        'i_duct2 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_duct2] = {-1000*R_tip}\n'
        'i_blade1 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_blade1] = {-1000*R_tip}\n'
        'i_blade2 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_blade2] = {-1000*R_tip}\n'
        'if cent_z[i_blade1] < cent_z[i_blade2]:\n'
        '    temp = i_blade1\n'
        '    i_blade1 = i_blade2\n'
        '    i_blade2 = temp\n'
        'i_hub1 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_hub1] = {-1000*R_tip}\n'
        'i_hub2 = cent_x.index(max(cent_x))\n'
        f'cent_x[i_hub2] = {-1000*R_tip}\n'

    )

    file.write(
        'n = len(offbody.Faces)\n'
        'cent_x = []\n'
        'cent_y = []\n'
        'cent_z = []\n'
        'for i in range(n):\n'
        '    face = offbody.Faces[i]\n'
        '    face_center = MeasureHelper.GetCentroid(Selection.Create([face]))\n'
        '    cent_x.append(face_center.X)\n'
        '    cent_y.append(face_center.Y)\n'
        '    cent_z.append(face_center.Z)\n'
    )

    file.write(
        'i_per1_off = cent_y.index(min(cent_y))\n'
        'i_per2_off = cent_y.index(max(cent_y))\n'
        'i_wall = cent_x.index(max(cent_x))\n'
        'i_inlet = cent_z.index(max(cent_z))\n'
        'i_outlet = cent_z.index(min(cent_z))\n'
    )
    # Share Topology
    file.write(f"options = ShareTopologyOptions()\noptions.Tolerance = M(0.0005)\nresult = ShareTopology.FindAndFix(options)\n")
    # EndBlock

    file.write(
        '# Create Named Selection Group\n'
        'primarySelection = Selection.Create([offbody])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")\n'
        'primarySelection = Selection.Create([nearbody])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "nearbody")\n'
        'primarySelection = Selection.Create([offbody.Faces[i_inlet]])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "inlet")\n'
        'primarySelection = Selection.Create([offbody.Faces[i_wall]])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "wall")\n'
        'primarySelection = Selection.Create([offbody.Faces[i_outlet]])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "outlet")\n'
        'primarySelection = Selection.Create([offbody.Faces[i_per1_off],nearbody.Faces[i_per1_near]])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "per1")\n'
        'primarySelection = Selection.Create([offbody.Faces[i_per2_off],nearbody.Faces[i_per2_near]])\n'
        'secondarySelection = Selection.Empty()\n'
        'result = NamedSelection.Create(primarySelection, secondarySelection, "per2")\n'
        'input("Check current names selections and add blade1, blade2, duct1, duct2, hub1, and hub2.")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_blade1]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "blade1")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_blade2]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "blade2")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_duct1]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "duct1")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_duct2]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "duct2")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_hub1]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "hub1")\n'
        # 'primarySelection = Selection.Create([nearbody.Faces[i_hub2]])\n'
        # 'secondarySelection = Selection.Empty()\n'
        # 'result = NamedSelection.Create(primarySelection, secondarySelection, "hub2")\n'
    )
    
    

    # file.write(
    #     '# Create Named Selection Group\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "offbody")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[1]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "nearbody")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0].Faces[1]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "inlet")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0].Faces[2]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "wall")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0].Faces[3]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "outlet")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0].Faces[7],GetRootPart().Bodies[1].Faces[4]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "per1")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[0].Faces[0],GetRootPart().Bodies[1].Faces[0]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "per2")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[1].Faces[5]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "blade1")\n'
    #     'primarySelection = Selection.Create([ GetRootPart().Bodies[1].Faces[6]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "blade2")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[1].Faces[7]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "duct1")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[1].Faces[8]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "duct2")\n'
    #     'primarySelection = Selection.Create([GetRootPart().Bodies[1].Faces[9]])\n'
    #     'secondarySelection = Selection.Empty()\n'
    #     'result = NamedSelection.Create(primarySelection, secondarySelection, "hub")\n'
    # )
    
    
    
    
    geo_file = f"{case_folder}\\geo.dsco"
    # if os.path.exists(geo_file):
    #     print("Ovewriting")
    #     os.remove(geo_file)
    file.write(f"# Save Project As\nFile.SaveAs(r\"{geo_file}\")\n")
    
    fluent_file = f"{case_folder}\\case.pmdb"
    # if os.path.exists(fluent_file):
    #     print("Ovewriting")
    #     os.remove(fluent_file)
    file.write(f"Workbench.Fluent.ExportPMDB(r\"{fluent_file}\")\n")
    
    



    file.close()

    return script_file