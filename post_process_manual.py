import numpy as np
import os
import math
import matplotlib.pyplot as plt
import subprocess

from scipy.interpolate import interp1d

    
# constants for post-processing
P_REF = 20e-6  # Reference Pressure in Pa
MU = 1.789e-5 # Dynamic Viscosity of Air in Pa.s
RHO_REF = 1.225 # Density in kg/m3
N_R = 25 # Number of radial sections on the blade 

# acoustics
A0 = 340
NTIME = 360
NOBS = 9
ROBS = 3.0
acum_executable_path = os.getenv('ACUM_EXECUTABLE_PATH')
CCW = 1
CW = 0


# functions
def post_process(rpm,radius,case_folder,rr,rtheta,istator=0,rs=None,stheta=None):
    
    surf_name_rotor = rf"{case_folder}/surface.dat"
    surf_name_stator = rf"{case_folder}/stator.dat"
    volup_fname = rf"{case_folder}/slice_up.dat"
    voldown_fname = rf"{case_folder}/slice_down.dat"
    
    fout_inflow = rf"{case_folder}/inflow.csv"
    
    
    omega = rpm*2*np.pi/60

    data_up, n_up = read_vol_data(volup_fname)
    data_down, n_down = read_vol_data(voldown_fname)
    
    rotor =  read_blade_data(surf_name_rotor,radius,CCW,rr,rtheta) 

    if istator:
        stator =  read_blade_data(surf_name_stator,radius,CW,rs,stheta)  
    
    r = rotor["r"]
    rd = rotor["rd"]
    rb = rotor["rb"]
    
    vz = np.zeros(N_R)
    vs = np.zeros(N_R)
    vr = np.zeros(N_R)
    svz = np.zeros(N_R)
    r_n1 = np.zeros(N_R)
    r_n2 = np.zeros(N_R)
    vrel = np.zeros(N_R)
    phi = np.zeros(N_R)
    sphi = np.zeros(N_R)
    ur = np.zeros(N_R)
    us = np.zeros(N_R)

    for i in range(n_up):
        for j in range(N_R):
            if data_up[i][6] >= rb[j] and data_up[i][6] < rb[j+1]:
                r_n1[j] += 1
                vz[j] -= data_up[i][3]
                break

    for i in range(n_down):
        for j in range(N_R):
            if data_down[i][6] >= rb[j] and data_down[i][6] < rb[j+1]:
                r_n2[j] += 1
                vs[j] += data_down[i][4]
                vr[j] += data_down[i][5]
                svz[j] -= data_down[i][3]
                break
        
    for i in range(N_R):
        vz[i] /= r_n1[i]
        svz[i] /= r_n2[i]
        vs[i] /= r_n2[i]
        vr[i] /= r_n2[i]
        vrel[i] = omega*rd[i]
        phi[i] = math.atan(vz[i]/(vrel[i]))*180/np.pi
        ur[i] = math.sqrt(vz[i]**2 + vrel[i]**2)
        us[i] = math.sqrt(svz[i]**2 + vs[i]**2)
        sphi[i] = math.atan(svz[i]/(vs[i]))*180/np.pi
        # print(f"i:{i}, svz:{svz[i]:.1f}, vs:{vs[i]:.1f}, sphi:{sphi[i]:.1f}")
       

    rotor = calculate_coefficients(rotor,ur,phi)
    rotor["name"] = "rotor"
    if istator:
        stator = calculate_coefficients(stator,us,sphi)
        stator["name"] = "stator"
    
    ## Plotting

    ## Volume / Flow
    fig, axs = plt.subplots(3,1,figsize=(5,6),sharex=True)

    axs[0].plot(r,vz,label='inflow',marker=".")
    axs[1].plot(r,vs,label='average',marker=".")
    axs[2].plot(r,vr,label='average',marker=".")
    
    ylabel = ["Axial Velocity / (m/s)","Swirl / (m/s)","Radial Velocity / (m/s)"]
    for i in range(3):
        axs[i].set_xlabel("r/R")
        axs[i].set_ylabel(ylabel[i])
        axs[i].grid()
    fig.savefig(rf"{case_folder}/inflow.png")
    plt.tight_layout()


    ## rotor sectional loads dtdq
    fig, axs = plt.subplots(4,1,figsize=(5,8))
    axs[0].plot(r,rotor["dtdr"],marker='.')
    axs[1].plot(r,rotor["dddr"],marker='.')
    axs[2].plot(r,rotor["dqdr"],marker='.')
    axs[3].plot(r,rotor["dtdq"],marker='.')
    ylabel = ["dtdr","dddr","dqdr","dtdq"]
    title = ["Thrust","Drag","Torque","Thrust per torque"]
    for i in range(4):
        axs[i].set_ylabel(ylabel[i])
        axs[i].set_title(title[i])
        axs[i].grid(True)
    axs[3].set_xlabel("r/R")
    plt.tight_layout()
    fig.savefig(rf"{case_folder}/dtdq.png")

    #plt.show()

    file = open(fout_inflow,"w")

    file.write("r,Axial Velocity/(m/s),Swirl/(m/s),Radial Velocity/(m/s),Axial Velocity/(ft/s),Swirl/(ft/s),Radial Velocity/(ft/s)\n")

    for i in range(N_R):
        file.write("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n"%(r[i],vz[i],vs[i],vr[i],vz[i]*3.28084,vs[i]*3.28084,vr[i]*3.28084))

    file.close()

    plot_blade_data(rotor,case_folder)

    if istator:
        plot_blade_data(stator,case_folder)





def read_blade_data(surf_name,radius,ccw,rr,rtheta):

    lst = []

    file = open(surf_name,"r")

    for line in file:
        lst += [line.split(",")]

    npts = len(lst) - 1
    npts_c = len(lst[0])
    ix = [-1,-1,-1]
    iAx = [-1,-1,-1]
    iSFx = [-1,-1,-1]
    iA = -1
    iP = -1


    for i in range(npts_c):
        lst[0][i] = lst[0][i].strip()
        if lst[0][i] == '"Points:0"' or lst[0][i] == '"Coordinate:0"' or lst[0][i] == 'x-coordinate':
            ix[0] = i
        if lst[0][i] == '"Points:1"' or lst[0][i] == '"Coordinate:1"' or lst[0][i] == 'y-coordinate':
            ix[1] = i
        if lst[0][i] == '"Points:2"' or lst[0][i] == '"Coordinate:2"' or lst[0][i] == 'z-coordinate':
            ix[2] = i
        if lst[0][i] == '"X_Face_Area"' or lst[0][i] == 'x-face-area':
            iAx[0] = i
        if lst[0][i] == '"Y_Face_Area"' or lst[0][i] == 'y-face-area':
            iAx[1] = i
        if lst[0][i] == '"Z_Face_Area"' or lst[0][i] == '"Z_Face_Area"\n' or lst[0][i] == 'z-face-area' or lst[0][i] == 'z-face-area\n':
            iAx[2] = i
        if lst[0][i] == '"SkinFriction:0"' or lst[0][i] == 'x-wall-shear':
            iSFx[0] = i
        if lst[0][i] == '"SkinFriction:1"' or lst[0][i] == 'y-wall-shear':
            iSFx[1] = i
        if lst[0][i] == '"SkinFriction:2"' or lst[0][i] == 'z-wall-shear':
            iSFx[2] = i
        if lst[0][i] == '"Face_Area_Magnitude"' or lst[0][i] == 'face-area-magnitude':
            iA = i
        if lst[0][i] == '"Pressure"' or lst[0][i] == '"Absolute_Pressure"' or lst[0][i] == 'pressure' or lst[0][i] =='absolute-pressure':
            iP = i

    if min(ix) == -1 or min(iAx) == -1 or min(iSFx) == -1 or min([iA, iP]) == -1:
        print("Surface data not provided")
        print(ix,iAx,iSFx,iA,iP)
        exit()

    x = np.zeros(npts,dtype=float)
    y = np.zeros(npts,dtype=float)
    z = np.zeros(npts,dtype=float)
    Ax = np.zeros(npts,dtype=float)
    Ay = np.zeros(npts,dtype=float)
    Az = np.zeros(npts,dtype=float)

    p = np.zeros(npts,dtype=float)
    SFx = np.zeros(npts,dtype=float)
    SFy = np.zeros(npts,dtype=float)
    SFz = np.zeros(npts,dtype=float)
    A = np.zeros(npts,dtype=float)

    
    for i in range(npts):
        x[i] = float(lst[i+1][ix[0]])
        y[i] = float(lst[i+1][ix[1]])
        z[i] = float(lst[i+1][ix[2]])
        p[i] = float(lst[i+1][iP])
        Ax[i] = float(lst[i+1][iAx[0]])
        Ay[i] = float(lst[i+1][iAx[1]])
        Az[i] = float(lst[i+1][iAx[2]])
        SFx[i] = float(lst[i+1][iSFx[0]])
        SFy[i] = float(lst[i+1][iSFx[1]])
        SFz[i] = float(lst[i+1][iSFx[2]])
        A[i] = float(lst[i+1][iA])

        
    dtdr = np.zeros(N_R)
    dddr = np.zeros(N_R)
    dqdr = np.zeros(N_R)
    dtdq = np.zeros(N_R)
    dtdr_p = np.zeros(N_R)
    dtdr_sf = np.zeros(N_R)
    dmdr = np.zeros(N_R)

    cz = np.zeros(N_R)
    cy = np.zeros(N_R)
    cm = np.zeros(N_R)
    cn = np.zeros(N_R)
    cc = np.zeros(N_R)
    cl = np.zeros(N_R)
    cd = np.zeros(N_R)
    clcd = np.zeros(N_R)

    r_min = 1
    r_max = 0

    for i in range(npts):
        r0 = math.sqrt(x[i]**2 + y[i]**2)
        if r0 < r_min:
            r_min = r0
        if r0 > r_max:
            r_max = r0


    
    dr = float((r_max-r_min)/N_R)

    rb = np.linspace(r_min,r_max,N_R+1)
    r = np.zeros(N_R)
    rd = np.zeros(N_R)
    # r_n1 = np.zeros(N_R)
    # r_n = np.zeros(N_R)

    for i in range(N_R):
        rd[i] = (rb[i] + rb[i+1])*0.5
        r[i] = rd[i]/radius

    theta_geo = np.zeros(N_R)
    theta_design = np.zeros(N_R)
    phi = np.zeros(N_R)
    alpha = np.zeros(N_R)
    c1 = np.zeros(N_R)
    c2 = np.zeros(N_R)
    c12 = np.zeros((N_R,2,2))
    c = np.zeros(N_R)
    
    points = [[] for _ in range(N_R)]
    cg = np.zeros((N_R,3))

    for i in range(N_R):
        for j in range(npts):
            if x[j] >= rb[i] and x[j] < rb[i+1]:
                points[i].append(j)
                cg[i][0] += x[j]
                cg[i][1] += y[j]
                cg[i][2] += z[j]

        if len(points[i]) > 0:
            for j in range(3):
                cg[i][j] /= len(points[i])

        for j in points[i]:
            if ccw:
                if y[j] > cg[i][1] and z[j] > cg[i][2]:
                    d = math.sqrt((y[j]-cg[i][1])**2+(z[j]-cg[i][2])**2)
                    if c1[i] < d:
                        c1[i] = d
                        c12[i][0][0] = y[j]
                        c12[i][0][1] = z[j]
                
                if y[j] < cg[i][1] and z[j] < cg[i][2]:
                    d = math.sqrt((y[j]-cg[i][1])**2+(z[j]-cg[i][2])**2)
                    if c2[i] < d:
                        c2[i] = d
                        c12[i][1][0] = y[j]
                        c12[i][1][1] = z[j]
            else:
                if y[j] < cg[i][1] and z[j] > cg[i][2]:
                    d = math.sqrt((z[j]-cg[i][2])**2) #math.sqrt((y[j]-cg[i][1])**2+(z[j]-cg[i][2])**2)
                    if c1[i] < d:
                        c1[i] = d
                        c12[i][0][0] = y[j]
                        c12[i][0][1] = z[j]
                
                if y[j] > cg[i][1] and z[j] < cg[i][2]:
                    d = math.sqrt((z[j]-cg[i][2])**2) #math.sqrt((y[j]-cg[i][1])**2+(z[j]-cg[i][2])**2)
                    if c2[i] < d:
                        c2[i] = d
                        c12[i][1][0] = y[j]
                        c12[i][1][1] = z[j]


            dtdr[i] += (p[j]*Az[j] + SFz[j]*A[j])/dr
            if ccw:
                dddr[i] += -(p[j]*Ay[j] + SFy[j]*A[j])/dr
                dqdr[i] += -(p[j]*Ay[j] + SFy[j]*A[j])/dr*r[i]*radius
                dmdr[i] += -(p[j]*Ay[j] + SFy[j]*A[j])*z[j]/dr + (p[j]*Az[j] + SFz[j]*A[j])*y[j]/dr
            else:
                dddr[i] += (p[j]*Ay[j] + SFy[j]*A[j])/dr
                dqdr[i] += (p[j]*Ay[j] + SFy[j]*A[j])/dr*r[i]*radius
                dmdr[i] += (p[j]*Ay[j] + SFy[j]*A[j])*z[j]/dr + (p[j]*Az[j] + SFz[j]*A[j])*y[j]/dr
           

        dtdq[i] = dtdr[i]/dqdr[i]
        c[i] = math.sqrt((c12[i][0][0]-c12[i][1][0])**2+(c12[i][0][1]-c12[i][1][1])**2)
        if ccw:
            theta_geo[i] = math.atan((c12[i][0][1]-c12[i][1][1])/(c12[i][0][0]-c12[i][1][0]))*180/np.pi
        else:
            theta_geo[i] = math.atan((c12[i][0][1]-c12[i][1][1])/(c12[i][1][0]-c12[i][0][0]))*180/np.pi
        
        f = interp1d(rr, rtheta, kind='cubic', fill_value="extrapolate")
        theta_design[i] = f(r[i])
        


    return {
        "name": None,
        # Radial Positions
        "rd": rd,
        "r": r,
        "rb": rb,
        "chord": c,
        "LTE": c12,
        
        # Angles (Degrees)
        "theta_geo": theta_geo,
        "theta_design": theta_design,
        "alpha": alpha,
        "phi": phi,
        
        # Sectional Forces & Moments (Gradients)
        "dtdr": dtdr,
        "dddr": dddr,
        "dqdr": dqdr,
        "dmdr": dmdr,
        "dtdq": dtdq,
        
        # # Non-Dimensional Aerodynamic Coefficients
        "cz": cz,
        "cy": cy,
        "cn": cn,
        "cc": cc,
        "cl": cl,
        "cd": cd,
        "clcd": clcd,
        "cm": cm
    }


def calculate_coefficients(blade,u,phi):

    for i in range(N_R):
        blade["cz"][i] = blade["dtdr"][i]/(0.5*RHO_REF*u[i]**2*blade["chord"][i])
        blade["cy"][i] = blade["dddr"][i]/(0.5*RHO_REF*u[i]**2*blade["chord"][i])
        blade["cn"][i] = blade["cz"][i]*math.cos(blade["theta_design"][i]*np.pi/180) + blade["cy"][i]*math.sin(blade["theta_design"][i]*np.pi/180)
        blade["cc"][i] = -blade["cz"][i]*math.sin(blade["theta_design"][i]*np.pi/180) + blade["cy"][i]*math.cos(blade["theta_design"][i]*np.pi/180)
        blade["cl"][i] = blade["cz"][i]*math.cos(phi[i]*np.pi/180) + blade["cy"][i]*math.sin(phi[i]*np.pi/180)
        blade["cd"][i] = -blade["cz"][i]*math.sin(phi[i]*np.pi/180) + blade["cy"][i]*math.cos(phi[i]*np.pi/180)
        blade["clcd"][i] = blade["cl"][i]/blade["cd"][i]
        blade["cm"][i] = blade["dmdr"][i]/(0.5*RHO_REF*u[i]**2*blade["chord"][i]**2)
        blade["phi"][i] = phi[i]
        blade["alpha"][i] = blade["theta_design"][i] - blade["phi"][i]

    return blade



def plot_blade_data(blade,case_folder):
    fout_blade = rf"{case_folder}/{blade['name']}_blade.csv"
    fout_forces = rf"{case_folder}/{blade['name']}_sectional_forces.csv"
    
    fig, axs = plt.subplots(4,1,figsize=(5,8))
    axs[0].plot(blade["r"],blade["cl"],marker='.')
    axs[1].plot(blade["r"],blade["cd"],marker='.')
    axs[2].plot(blade["r"],blade["clcd"],marker='.')
    #axs[2].set_ylim(0,15)
    axs[3].plot(blade["r"],blade["cm"],marker='.')
    ylabel = ["cl","cd","cl/cd","cm"]
    title = ["Coefficient of Lift", "Coefficient of Drag","Lift-to-Drag Ratio", "Coefficient of Moment"]
    for i in range(4):
        axs[i].set_ylabel(ylabel[i])
        axs[i].set_title(title[i])
        axs[i].grid(True)
    axs[3].set_xlabel("r/R")
    plt.tight_layout()
    fig.savefig(rf"{case_folder}/{blade['name']}_cl_cd.png")
    #plt.show()

    fig, axs = plt.subplots(3,1,figsize=(5,6))
    axs[0].plot(blade["r"],blade["cn"],marker='.')
    axs[1].plot(blade["r"],blade["cc"],marker='.')
    axs[2].plot(blade["r"],blade["cm"],marker='.')
    ylabel = ["cn","cc","cm"]
    title = ["Coefficient of Normal Force", "Coefficient of Chordwise Force", "Coefficient of Pitching Moment"]
    for i in range(3):
        axs[i].set_ylabel(ylabel[i])
        axs[i].set_title(title[i])
        axs[i].grid(True)
    axs[2].set_xlabel("r/R")
    plt.tight_layout()
    fig.savefig(rf"{case_folder}/{blade['name']}_cn_cc.png")
    #plt.show()

    fig, axs = plt.subplots(3,1,figsize=(5,6),sharex=True)

    axs[0].plot(blade["r"],blade["theta_geo"],label='Pitch',marker=".")
    axs[0].plot(blade["r"],blade["theta_design"],label='Design Pitch',marker=".")
    axs[0].plot(blade["r"],blade["phi"],label='Inflow angle',marker=".")
    axs[0].legend()
    axs[1].plot(blade["r"],blade["alpha"],label='alpha',marker=".")
    axs[2].plot(blade["r"],blade["chord"]*1000,label='chord',marker=".")

    ylabel = ["Angle / deg","Alpha / deg","Chord / mm"]
    for i in range(3):
        axs[i].grid()
        axs[i].set_xlabel("r/R")
        axs[i].set_ylabel(ylabel[i])
    plt.tight_layout()

    fig.savefig(rf"{case_folder}/{blade['name']}_chord_angles.png")

    file = open(fout_forces,"w")

    file.write("r,Cl,Cd,Cn,Cc,Cm,Cz,Cy,Chord/mm,Pitch/deg.,Inflow angle/deg.,Angle of attack/deg.\n")

    for i in range(N_R):
        file.write("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n"%(blade["r"][i],blade["cl"][i],blade["cd"][i],blade["cn"][i],blade["cc"][i],blade["cm"][i],blade["cz"][i],blade["cy"][i],blade["chord"][i],blade["theta_design"][i],blade["phi"][i],blade["alpha"][i]))

    file.close()

    file = open(fout_blade,"w")

    file.write("x/mm,LE_y/mm,LE_z/mm,TE_y/mm,TE_z,mm,chord/mm,pitch/deg.\n")

    for i in range(N_R):
        file.write("%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.3f\n"%(blade["rd"][i]*1000,blade["LTE"][i][0][0]*1000,blade["LTE"][i][0][1]*1000,blade["LTE"][i][1][0]*1000,blade["LTE"][i][1][1]*1000,blade["chord"][i]*1000,blade["theta_design"][i]))

    file.close()


def read_vol_data(fname):

    lst1 = []
    file = open(fname)
    for line in file:
        lst1 += [line.split(",")]
    file.close()

    n = len(lst1)-1
    nc = len(lst1[0])
    ix = [-1,-1,-1]
    ivx = -1
    ivy = -1
    ivz = -1
    ivort = -1
    ivel = -1

    for i in range(nc):
        lst1[0][i] = lst1[0][i].strip()
        if lst1[0][i] == '"Points:0"' or lst1[0][i] == '"Coordinate:0"'  or lst1[0][i] == 'x-coordinate':
            ix[0] = i
        if lst1[0][i] == '"Points:1"' or lst1[0][i] == '"Coordinate:1"'  or lst1[0][i] == 'y-coordinate':
            ix[1] = i
        if lst1[0][i] == '"Points:2"' or lst1[0][i] == '"Coordinate:2"'  or lst1[0][i] == 'z-coordinate':
            ix[2] = i
        if lst1[0][i] == '"Velocity:0"'  or lst1[0][i] == 'x-velocity':
            ivx = i
        if lst1[0][i] == '"Velocity:1"'  or lst1[0][i] == 'y-velocity':
            ivy = i
        if lst1[0][i] == '"Velocity:2"' or lst1[0][i] == '"Velocity:2"\n'  or lst1[0][i] == 'z-velocity'  or lst1[0][i] == 'z-velocity\n':
            ivz = i
        if lst1[0][i] == '"VelocityMagnitude"' or lst1[0][i] == 'velocity-magnitude':
            ivel = i
        if lst1[0][i] == '"VorticityMagnitude"' or lst1[0][i] == 'vorticity-mag':
            ivort = i

    if min(ix) == -1 or min([ivx,ivy,ivz,ivel,ivort]) == -1:
        print(lst1[0])
        print(ix,ivx,ivy,ivz,ivel,ivort)
        print("Volume data not provided for volume slice",fname)
        exit()


    data = np.zeros((n,11)) # x,y,z,uz,utheta,ur,r,vorticity,velocity,vx,vy

    for i in range(n):
        for j in range(3):
            data[i][j] = float(lst1[1+i][ix[j]]) # x,y,z
        
        nrx = data[i][0]
        nry = data[i][1]
        dist = math.sqrt(nrx**2 + nry**2)
        
        data[i][6] = dist # r

        nrx /= dist
        nry /= dist
        ntx = -nry
        nty = nrx

        data[i][3] = float(lst1[1+i][ivz]) # vz
        data[i][7] = float(lst1[1+i][ivort]) # vorticity
        data[i][8] = float(lst1[1+i][ivel]) # velocity
        data[i][9] = float(lst1[1+i][ivx]) # vx
        data[i][10] = float(lst1[1+i][ivy]) # vy

        data[i][4] = float(lst1[i+1][ivx])*ntx + float(lst1[i+1][ivy])*nty # v_swirl
        data[i][5] = float(lst1[i+1][ivx])*nrx + float(lst1[i+1][ivy])*nry # v_r

    return data, n




if __name__ == "__main__":
    rpm = 12326
    radius = 0.15
    case_folder = r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cases\tx300\case6_duct_sweep\80_ms\case29"

    rr = [0.00, 0.12, 0.22, 0.35, 0.47, 0.58, 0.70, 0.82, 1.00, 1.05]
    rtheta = [100.4, 87.0, 75.0, 63.0, 52.5, 44.0, 39.0, 36.0, 33.0, 32.0]

    post_process(rpm,radius,case_folder,rr,rtheta)
