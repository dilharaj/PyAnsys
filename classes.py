from input import Input
import numpy as np
import math
from scipy import interpolate
from scipy.interpolate import interp1d
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
import yaml
import sys

class Input:
    def __init__(self,inputs_file):

        """
        try:
            with open(inputs_file, 'r') as file:
                data = yaml.safe_load(file)

        except FileNotFoundError:
            print(f"Error: File '{inputs_file}' not found.")
        except yaml.YAMLError as exc:
            print(f"YAML parsing error: {exc}")
        """
        with open(inputs_file,'r') as f:
            data = yaml.load(f,Loader=yaml.SafeLoader)

        #print(data)
        # Assigning to variables
        opt = data.get('Optimization',{})
        general = data.get('General',{})
        rotor = data.get('Rotor',{})
        duct = data.get('Duct',{})
        hub = data.get('Hub',{})
        stator = data.get('Stator',{})

     
        self.npop = int(opt.get('npop', 1))
        self.niter = int(opt.get('niter', 1))
        self.nproc_mesh = int(opt.get('nproc_mesh', 1))
        self.nproc_cfd = int(opt.get('nproc_cfd', 1))
        self.root_folder = opt.get('root_folder', r"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\cases_temp")
        self.gui = opt.get('gui', False)
        self.gpu_cfd = opt.get('gpu_cfd', True)
        self.fluent_niter = int(opt.get('fluent_niter', 400))
        self.fluent_nloops = int(opt.get('fluent_nloops', 3))

        self.Density = float(general.get('Density', 0))
        self.Mu = float(general.get('Mu', 0))
        self.Vinf = float(general.get('Vinf', 0))
        self.Thrust = float(general.get('Thrust', 0))
        
        self.R = float(rotor.get('R', 0))
        self.RPM = int(rotor.get('RPM', 0))
        self.TP_type = int(rotor.get('TP_type', 0))
        self.TW_type = int(rotor.get('TW_type', 0))
        self.Solidity = list(map(float, rotor.get('Solidity', [])))
        self.Nb = list(map(int, rotor.get('Nb', [])))
        self.Rcout = list(map(float, rotor.get('Rcout', [])))
        self.Taper = list(map(float, rotor.get('Taper', [])))
        self.Twist = list(map(float, rotor.get('Twist', [])))
        self.Theta75 = list(map(float, rotor.get('Theta75', [])))
        self.Air_loc = list(map(float, rotor.get('Air_loc', [])))
        self.Air_thick_min = list(map(float, rotor.get('Air_thick_min', [])))
        self.Air_thick_max = list(map(float, rotor.get('Air_thick_max', [])))
        self.Air_camber_min = list(map(float, rotor.get('Air_camber_min', [])))
        self.Air_camber_max = list(map(float, rotor.get('Air_camber_max', [])))
        self.AR_min = list(map(float, rotor.get('AR_min', [])))
        self.AR_max = list(map(float, rotor.get('AR_max', [])))
        self.SW_min = list(map(float, rotor.get('SW_min', [])))
        self.SW_max = list(map(float, rotor.get('SW_max', [])))


        # Duct
        self.Length = list(map(float, duct.get('Length', [])))
        self.Width = list(map(float, duct.get('Width', [])))
        self.In_exp = list(map(float, duct.get('In_exp', [])))
        self.Out_exp = list(map(float, duct.get('Out_exp', [])))

        # Hub
        self.Hub_Length = list(map(float, hub.get('Length', [])))

        # Stator
        self.Stator_Nb = list(map(int, stator.get('Nb', [])))
        self.Stator_Solidity = list(map(float, stator.get('Solidity', [])))
        self.Stator_Taper = list(map(float, stator.get('Taper', [])))
        self.Stator_Twist = list(map(float, stator.get('Twist', [])))
        self.Stator_Theta75 = list(map(float, stator.get('Theta75', [])))
        self.Stator_Air_loc = list(map(float, stator.get('Air_loc', [])))
        self.Stator_Air_thick_min = list(map(float, stator.get('Air_thick_min', [])))
        self.Stator_Air_thick_max = list(map(float, stator.get('Air_thick_max', [])))
        self.Stator_Air_camber_min = list(map(float, stator.get('Air_camber_min', [])))
        self.Stator_Air_camber_max = list(map(float, stator.get('Air_camber_max', [])))
        self.Stator_Rake = list(map(float, stator.get('Rake', [])))
        self.Stator_Clearance = list(map(float, stator.get('Clearance', [])))



class ID:
    def __init__(self, inputs):
        self.inputs = inputs # Input(rf"{case_folder}\inputs.yaml")

        self.nrair = len(self.inputs.Air_loc)
        self.nsair = len(self.inputs.Stator_Air_loc)

        # defines indices for optimization variable array
        #print("test1")
        self.var_names = ['Nb', 'Solidity', 'Rcout', 'Twist', 'Theta75']

        self.rnb = 0
        self.rsolidity = 1
        self.rcout = 2
        self.rtwist = 3
        self.rtheta75 = 4

        ind = 5



        if self.inputs.TP_type == 1:
            self.rtaper = ind
            self.ntaper = 1
            ind += 1
            self.var_names.append('Taper')
        else:
            self.rtaper = np.zeros(self.nrair,dtype=int)
            self.rsweep = np.zeros(self.nrair,dtype=int)
            for i in range(self.nrair):
                self.rtaper[i] = ind
                ind += 1
                self.var_names.append(f'AR_{i+1}')
            for i in range(self.nrair):
                self.rsweep[i] = ind
                ind += 1
                self.var_names.append(f'SW_{i+1}')
            self.ntaper = self.nrair
            self.nsweep = self.nrair


        self.rair_thick = np.zeros(self.nrair,dtype=int)
        self.rair_camber = np.zeros(self.nrair,dtype=int)
        for i in range(self.nrair):
            self.rair_thick[i] = ind
            ind += 1
            self.var_names.append(f'Air_thick_{i+1}')
        for i in range(self.nrair):
            self.rair_camber[i] = ind
            ind += 1
            self.var_names.append(f'Air_camber_{i+1}')

        self.dlength = ind
        self.dwidth = ind+1
        self.din_exp = ind+2
        self.dout_exp = ind+3

        self.hlength = ind+4

        self.snb = ind+5
        self.ssolidity = ind+6
        self.staper = ind+7
        self.stwist = ind+8
        self.stheta75 = ind+9
                
        self.var_names.append('Duct_Length')
        self.var_names.append('Duct_Width')
        self.var_names.append('Duct_In_exp')
        self.var_names.append('Duct_Out_exp')
        self.var_names.append('Hub_Length')
        self.var_names.append('Stator_Nb')
        self.var_names.append('Stator_Solidity')
        self.var_names.append('Stator_Taper')
        self.var_names.append('Stator_Twist')
        self.var_names.append('Stator_Theta75')

        ind = ind+10
        self.sair_thick = np.zeros(self.nsair,dtype=int)
        self.sair_camber = np.zeros(self.nsair,dtype=int)
        for i in range(self.nsair):
            self.sair_thick[i] = ind
            ind += 1
            self.var_names.append(f'Stator_Air_thick_{i+1}')
        for i in range(self.nsair):
            self.sair_camber[i] = ind
            ind += 1
            self.var_names.append(f'Stator_Air_camber_{i+1}')

        self.srake = ind
        self.sclear = ind+1
        self.var_names.append('Stator_Rake')
        self.var_names.append('Stator_Clearance')

        self.nvar = ind+2  # total number of variables in the optimization

        # defines indices for constants array

        self.rho = 0
        self.mu = 1
        self.vinf = 2
        self.r = 3
        self.rpm = 4
        self.rtp_type = 5
        self.rtw_type = 6
        self.thrust = 7
        ind = 8
        self.rair_loc = np.zeros(self.nrair,dtype=int)
        for i in range(self.nrair):
            self.rair_loc[i] = ind
            ind += 1

        self.sair_loc = np.zeros(self.nsair,dtype=int)
        for i in range(self.nsair):
            self.sair_loc[i] = ind
            ind += 1

        self.nconst = ind

        # make min and max arrays and constant array

        self.vmax = np.zeros(self.nvar,dtype=float)
        self.vmin = np.zeros(self.nvar,dtype=float)
        self.const = np.zeros(self.nconst,dtype=float)

        # min array
        self.vmin[self.rnb] = self.inputs.Nb[0]
        self.vmin[self.rsolidity] = self.inputs.Solidity[0]
        self.vmin[self.rcout] = self.inputs.Rcout[0]
        self.vmin[self.rtaper] = self.inputs.Taper[0]
        self.vmin[self.rtwist] = self.inputs.Twist[0]
        self.vmin[self.rtheta75] = self.inputs.Theta75[0]
        if self.inputs.TP_type == 1:
            self.vmin[self.rtaper] = self.inputs.Taper[0]
        else:
            for i in range(self.ntaper):
                self.vmin[self.rtaper[i]] = self.inputs.AR_min[i]
            for i in range(self.nsweep):
                self.vmin[self.rsweep[i]] = self.inputs.SW_min[i]

        for i in range(self.nrair):
            self.vmin[self.rair_thick[i]] = self.inputs.Air_thick_min[i]
        for i in range(self.nrair):
            self.vmin[self.rair_camber[i]] = self.inputs.Air_camber_min[i]

        self.vmin[self.dlength] = self.inputs.Length[0]
        self.vmin[self.dwidth] = self.inputs.Width[0]
        self.vmin[self.din_exp] = self.inputs.In_exp[0]
        self.vmin[self.dout_exp] = self.inputs.Out_exp[0]

        self.vmin[self.hlength] = self.inputs.Hub_Length[0]

        self.vmin[self.snb] = self.inputs.Stator_Nb[0]
        self.vmin[self.ssolidity] = self.inputs.Stator_Solidity[0]
        self.vmin[self.staper] = self.inputs.Stator_Taper[0]
        self.vmin[self.stwist] = self.inputs.Stator_Twist[0]
        self.vmin[self.stheta75] = self.inputs.Stator_Theta75[0]
        self.vmin[self.staper] = self.inputs.Stator_Taper[0]

        for i in range(self.nsair):
            self.vmin[self.sair_thick[i]] = self.inputs.Stator_Air_thick_min[i]
        for i in range(self.nrair):
            self.vmin[self.sair_camber[i]] = self.inputs.Stator_Air_camber_min[i]

        self.vmin[self.srake] = self.inputs.Stator_Rake[0]
        self.vmin[self.sclear] = self.inputs.Stator_Clearance[0]

        # max array
        self.vmax[self.rnb] = self.inputs.Nb[1]
        self.vmax[self.rsolidity] = self.inputs.Solidity[1]
        self.vmax[self.rcout] = self.inputs.Rcout[1]
        self.vmax[self.rtaper] = self.inputs.Taper[1]
        self.vmax[self.rtwist] = self.inputs.Twist[1]
        self.vmax[self.rtheta75] = self.inputs.Theta75[1]
        if self.inputs.TP_type == 1:
            self.vmax[self.rtaper] = self.inputs.Taper[1]
        else:
            for i in range(self.ntaper):
                self.vmax[self.rtaper[i]] = self.inputs.AR_max[i]
            for i in range(self.nsweep):
                self.vmax[self.rsweep[i]] = self.inputs.SW_max[i]

        for i in range(self.nrair):
            self.vmax[self.rair_thick[i]] = self.inputs.Air_thick_max[i]
        for i in range(self.nrair):
            self.vmax[self.rair_camber[i]] = self.inputs.Air_camber_max[i]

        self.vmax[self.dlength] = self.inputs.Length[1]
        self.vmax[self.dwidth] = self.inputs.Width[1]
        self.vmax[self.din_exp] = self.inputs.In_exp[1]
        self.vmax[self.dout_exp] = self.inputs.Out_exp[1]

        self.vmax[self.hlength] = self.inputs.Hub_Length[1]

        self.vmax[self.snb] = self.inputs.Stator_Nb[1]
        self.vmax[self.ssolidity] = self.inputs.Stator_Solidity[1]
        self.vmax[self.staper] = self.inputs.Stator_Taper[1]
        self.vmax[self.stwist] = self.inputs.Stator_Twist[1]
        self.vmax[self.stheta75] = self.inputs.Stator_Theta75[1]
        self.vmax[self.staper] = self.inputs.Stator_Taper[1]

        for i in range(self.nsair):
            self.vmax[self.sair_thick[i]] = self.inputs.Stator_Air_thick_max[i]
        for i in range(self.nrair):
            self.vmax[self.sair_camber[i]] = self.inputs.Stator_Air_camber_max[i]
        self.vmax[self.srake] = self.inputs.Stator_Rake[1]
        self.vmax[self.sclear] = self.inputs.Stator_Clearance[1]

        # constants
        self.const[self.rho] = self.inputs.Density
        self.const[self.mu] = self.inputs.Mu 
        self.const[self.vinf] = self.inputs.Vinf
        self.const[self.thrust] = self.inputs.Thrust
        self.const[self.r] = self.inputs.R
        self.const[self.rpm] = self.inputs.RPM
        self.const[self.rtp_type] = self.inputs.TP_type
        self.const[self.rtw_type] = self.inputs.TW_type


        for i in range(self.nrair):
            self.const[self.rair_loc[i]] = self.inputs.Air_loc[i]

        for i in range(self.nsair):
            self.const[self.sair_loc[i]] = self.inputs.Stator_Air_loc[i]



class Rotor:
    def __init__(self,vars,consts,id):

        # Inputs
        self.R_tip = consts[id.r]   # rotor radius
        self.Solidity = vars[id.rsolidity]
        self.TP_type = consts[id.rtp_type] # taper definition 1-linear 
        self.TW_type = consts[id.rtw_type] # twist definition 1-linear 2- hy

        if self.TP_type == 1:
            self.Taper = vars[id.rtaper]
        else:
            rAR = np.zeros(id.ntaper,dtype=float)
            for i in range(id.ntaper):
                rAR[i] = vars[id.rtaper[i]]
            rSW = np.zeros(id.nsweep,dtype=float)
            for i in range(id.nsweep):
                rSW[i] = vars[id.rsweep[i]]

        self.Nb = round(vars[id.rnb])  # number of blades
        self.Rcout = vars[id.rcout] # root cutout fraction
        self.RPM = consts[id.rpm] 
        self.Twist = vars[id.rtwist] # hub to root twist (hub pitch minus root pitch)
        self.Theta75 = vars[id.rtheta75] # 3/4th span collective (R_75 defined as 0.75 * R_tip)
       
        dWidth = vars[id.dwidth]
        rAir_loc = np.zeros(id.nrair,dtype=float)
        rAir_thick = np.zeros(id.nrair,dtype=float)
        rAir_camber = np.zeros(id.nrair,dtype=float)
        for i in range(id.nrair):
            rAir_loc[i] = consts[id.rair_loc[i]]
            rAir_thick[i] = vars[id.rair_thick[i]]
            rAir_camber[i] = vars[id.rair_camber[i]]

        # Constraints
        self.Twist = min(self.Twist,90-self.Theta75)
        # Internal variables
        self.nr = 10 # number of spanwise section definitions
        self.r = np.zeros(self.nr) # spanwise length array
        self.chord = np.zeros(self.nr) # chord
        self.sweep = np.zeros(self.nr)
        self.theta = np.zeros(self.nr) # pitch

        self.R_root = self.R_tip * self.Rcout  # Root radius

        r1 = 0/self.R_tip
        r2 = min(self.R_tip*1.05,self.R_tip+dWidth/2)/self.R_tip
        
        self.r = np.linspace(r1,r2,self.nr)
        i = max(1,np.argmin(abs(self.r-self.Rcout)))
        i_rcout = i
        self.r[i] = self.Rcout
        i = min(self.nr-2,np.argmin(abs(self.r-1)))
        self.r[i]  = 1
        self.dr = (r2-r1)/(self.nr-1)
        
        # twist
        if self.TW_type == 1:  # linear twist
            for i in range(self.nr):
                self.theta[i] = self.Theta75 - self.Twist/(1-self.Rcout)*(self.r[i] - 0.75)
            self.Theta0 = self.Theta75 - self.Twist/(1-self.Rcout)*(self.Rcout - 0.75) # Root Collective
            
        elif self.TW_type == 2:  # hyperbolic twist
            theta_hub = self.Theta75 + self.Twist/(self.R_tip/self.R_root - 1)*(1/self.Rcout - 1/0.75)
            tw_dr_hub =  (self.Twist/(self.R_tip/self.R_root - 1)*(1/self.Rcout - 1/0.75) -  self.Twist/(self.R_tip/self.R_root - 1)*(1/(self.Rcout+self.dr) - 1/0.75))/self.dr
            theta0 = min(100,theta_hub + tw_dr_hub*(self.Rcout))
            self.Theta0 = theta_hub  # Root Collective

            q = [0,self.Rcout/2,self.Rcout,self.Rcout+self.dr,self.Rcout+self.dr*2]
            p = [theta0,(theta0+theta_hub)/2,theta_hub,self.Twist/(self.R_tip/self.R_root - 1)*(1/(self.Rcout+self.dr) - 1/0.75),self.Twist/(self.R_tip/self.R_root - 1)*(1/(self.Rcout+self.dr*2) - 1/0.75)]
            tck = interpolate.splrep(q,p)
            for i in range(self.nr):
                if self.r[i] < self.Rcout:
                    self.theta[i] =interpolate.splev(self.r[i],tck) #np.interp(self.r[i],q,p)
                else:
                    self.theta[i] = self.Theta75 + self.Twist/(self.R_tip/self.R_root - 1)*(1/self.r[i] - 1/0.75)

                bad_idx = [3, 4]

                # mask for the remaining points
                mask = np.ones(len(self.r), dtype=bool)
                mask[bad_idx] = False

                # data used to build spline
                r_good = self.r[mask]
                theta_good = self.theta[mask]

                # cubic spline from remaining points
                cs = CubicSpline(r_good, theta_good)

                # recompute only the bad points
                self.theta[3] = cs(self.r[3])
                self.theta[4] = cs(self.r[4])

        elif self.TW_type == 3: # automated cruise twist
            vinf = consts[id.vinf]
            if vinf <= 0:
                print("Freestream velocity is zero or negative. Cannot compute cruise twist. Exiting run...") 
                sys.exit(1)
            
            print("### Calculating twist for cruise configuration...")
            omega = 2*math.pi*self.RPM/60
            
            dtheta_75 = self.Theta75 #- math.degrees(math.atan(vinf/(self.R_tip*0.75*omega)))
            for i in range(1,self.nr):
                self.theta[i] = math.degrees(math.atan(vinf/(self.R_tip*self.r[i]*omega))) + dtheta_75
            
            self.theta[0] = 90 + dtheta_75

        elif self.TW_type == 4: # custom twist definition
            x0 = [0, 0.2, 0.4, 0.6, 0.8, 1.1]
            theta0 = [95, 75, 59, 50, 43, 36]

            self.theta = np.interp(self.r,x0,theta0)  

            # plt.plot(self.r, self.theta, label="Pitch", color="blue", linestyle="--", marker="o")

            # # 3. Add labels and title
            # plt.xlabel("r/R")
            # plt.ylabel("Pitch/deg.")
            # plt.title("Rotor Blade Pitch")
            # plt.show()
        

        Nair = len(rAir_loc) # number of airfoil locations

        # taper
        if self.TP_type == 1:  # linear taper

            root_chord_max = 2*np.pi*self.R_root/self.Nb*0.8/math.cos(self.Theta0*np.pi/180)
            chord0_max = self.Rcout*self.R_tip/(0.75*abs(math.cos(self.theta[0]*np.pi/180))) * 0.7
            self.C_root = self.Solidity * np.pi * (self.R_tip**2)*2/(self.Nb*(self.R_tip-self.R_root)*(1+1/self.Taper)) # Root chord
            bi_taper = 0
            if self.C_root > root_chord_max:
                R_int = self.C_root*1.2/(2*np.pi)*self.Nb*math.cos(self.Theta0*np.pi/180)/self.R_tip
                r_int = R_int/self.R_tip
                bi_taper = 1
                sol1 = (self.Nb*(self.R_tip-R_int)*self.C_root*(1+1/self.Taper)/2)/(np.pi*(self.R_tip**2))
                int_chord = self.C_root
                self.C_root = (self.Solidity-sol1)*(np.pi*(self.R_tip**2))/(self.Nb*(R_int-self.R_root))*2 - int_chord
                if self.C_root < 0:
                    self.C_root = root_chord_max/5
                if self.C_root > root_chord_max:
                    self.C_root = root_chord_max
       
        
            if bi_taper == 0:
                for i in range(self.nr):
                    self.chord[i] = self.C_root * (1-(1-1/self.Taper)*(self.r[i]-self.Rcout)/(1-self.Rcout))
                    if self.r[i] < self.Rcout:
                        self.chord[i] = min(self.chord[i],chord0_max)
            else:
                for i in range(self.nr):
                    if self.r[i] < r_int:
                        self.chord[i] = (self.C_root *(r_int-self.r[i]) + int_chord * (self.r[i] - self.Rcout))/(r_int-self.Rcout)
                        if self.r[i] < self.Rcout:
                            self.chord[i] = min(self.chord[i],chord0_max)
                    else:
                        self.chord[i] = (int_chord *(1-self.r[i]) + int_chord/self.Taper * (self.r[i] - r_int))/(1-r_int)

            rr = np.linspace(r1,r2,50)
            tck = interpolate.splrep(self.r,self.chord)
            cc = interpolate.splev(rr,tck)
            self.chord = np.interp(self.r,rr,cc)

        elif self.TP_type == 2 or self.TP_type == 3: # based on aspect ratio defined at airfoil definition locations
            
            cc = np.zeros(Nair,dtype=float)
            sw = np.zeros(Nair,dtype=float)
            for i in range(Nair):
                cc[i] = self.R_tip/rAR[i]
                sw[i] = rSW[i] * cc[i]
                #print(sw[i],rSW[i])
            sw[0] = 0 # no sweep at beginning

            sigma = 0
            flag1 = 0
            for i in range(self.nr):
                if self.r[i] < rAir_loc[0]:
                    self.chord[i] = cc[0]
                    self.sweep[i] = sw[0]
                elif self.r[i] > rAir_loc[-1]:
                    self.chord[i] = cc[-1]
                    self.sweep[i] = sw[-1]
                else:
                    if Nair > 3:
                        f_cubic = interp1d(rAir_loc,cc,kind='cubic')
                        self.chord[i] = f_cubic(self.r[i])
                        f_cubic = interp1d(rAir_loc,sw,kind='cubic')
                        self.sweep[i] = f_cubic(self.r[i])
                    elif Nair == 3:
                        f_cubic = interp1d(rAir_loc,cc,kind='quadratic')
                        self.chord[i] = f_cubic(self.r[i])
                        f_cubic = interp1d(rAir_loc,sw,kind='quadratic')
                        self.sweep[i] = f_cubic(self.r[i]) 
                    elif Nair == 2:
                        self.chord[i] = np.interp(self.r[i],rAir_loc,cc)
                        self.sweep[i] = np.interp(self.r[i],rAir_loc,sw)
                    else:
                        self.chord[i] = cc[0]
                        self.sweep[i] = sw[0]
                if self.r[i] < self.Rcout:
                    flag1 = 1
                    r1 = self.Rcout
                    r2 = self.Rcout
                elif self.r[i] >= self.Rcout and self.r[i] <= 1:
                    if flag1 == 1:
                        r1 = self.Rcout
                        r2 = self.r[i]
                        flag1 = 0
                    else:
                        r1 = max(self.Rcout,min(1,(self.r[i-1] + self.r[i])/2))
                        if i < self.nr-1:
                            r2 = min(1,(self.r[i] + self.r[i+1])/2)
                        else:
                            r2 = 1
                else:
                    r1 = 1
                    r2 = 1

                sigma += self.chord[i] * (r2-r1)*self.R_tip * self.Nb /(np.pi*(self.R_tip**2))

                        

               
            if self.TP_type == 3:
                for i in range(self.nr):
                    # scale chord to reflect solidity
                    self.chord[i] = self.chord[i] * self.Solidity/sigma
                    
            for i in range(self.nr):    
                chord_max = max(self.r[i],self.Rcout) * self.R_tip * math.sin(np.pi/self.Nb) /(0.75*abs(math.cos(self.theta[i]*np.pi/180))) * 0.85
                self.chord[i] = min(self.chord[i],chord_max)

            chord_Rcout = self.Rcout * self.R_tip * math.sin(np.pi/self.Nb) /(0.75*abs(math.cos(self.theta[i_rcout]*np.pi/180))) * 0.85
                
            for i in range(i_rcout):
                self.chord[i] = min(self.chord[i],chord_Rcout)
            
                #print(self.r[i],self.sweep[i])
                  
            # root_chord_max = self.R_root * math.sin(np.pi/self.Nb) * 2 / math.cos(self.Theta0*np.pi/180) * 0.7 #2*np.pi*self.R_root/self.Nb/math.cos(self.Theta0*np.pi/180) * 0.65 # maximum allowable chord at root to avoid overlap
            # chord0_max = self.R_root/(0.75*abs(math.cos(self.theta[0]*np.pi/180))) * 0.5 # max allowable chord at r=0
            # self.C_root = np.interp(self.Rcout,self.r,self.chord) # Root chord
            # self.C_tip = self.chord[-1] # tip chord
            # bi_taper = 0

            # print("#####",self.chord[0],self.C_root,root_chord_max,chord0_max,self.Solidity,sigma,self.Nb,self.R_tip,self.R_root)
            # print("#####",self.chord)
            # if self.C_root > root_chord_max:
            #     print("#### Adjusting root chord to avoid overlap")
            #     R_int = self.C_root*1.2/(2*np.pi)*self.Nb*math.cos(self.Theta0*np.pi/180) # intermediate radius for bi-taper
            #     r_int = R_int/self.R_tip
            #     bi_taper = 1
            #     sol1 = (self.Nb*(self.R_tip-R_int)*(self.C_root+self.C_tip)/2)/(np.pi*(self.R_tip**2))
            #     int_chord = self.C_root
            #     self.C_root = (self.Solidity-sol1)*(np.pi*(self.R_tip**2))/(self.Nb*(R_int-self.R_root))*2 - int_chord
            #     if self.C_root < 0:
            #         self.C_root = root_chord_max/5
            #     if self.C_root > root_chord_max:
            #         self.C_root = root_chord_max
       
        
            # if bi_taper == 0:
            #     for i in range(self.nr):
            #         if self.r[i] < self.Rcout:
            #             self.chord[i] = min(self.chord[i],chord0_max)
            # else:
            #     for i in range(self.nr):
            #         if self.r[i] < r_int:
            #             self.chord[i] = (self.C_root *(r_int-self.r[i]) + int_chord * (self.r[i] - self.Rcout))/(r_int-self.Rcout)
            #             if self.r[i] < self.Rcout:
            #                 self.chord[i] = min(self.chord[i],chord0_max)
                    
            rr = np.linspace(r1,r2,50)
            tck = interpolate.splrep(self.r,self.chord)
            cc = interpolate.splev(rr,tck)
            #self.chord = np.interp(self.r,rr,cc)

            tck = interpolate.splrep(self.r,self.sweep)
            sw = interpolate.splev(rr,tck)
            #self.sweep = np.interp(self.r,rr,sw)
           # print(self.sweep)


        # Airfoils
        
        self.air_thick = np.zeros(self.nr)
        self.air_camber = np.zeros(self.nr)

        for i in range(self.nr):
            if self.r[i] < rAir_loc[0]:
                self.air_thick[i] = rAir_thick[0]
                self.air_camber[i] = rAir_camber[0]
            elif self.r[i] > rAir_loc[-1]:
                self.air_thick[i] = rAir_thick[-1]
                self.air_camber[i] = rAir_camber[-1]
            else:
                f_cubic = interp1d(rAir_loc,rAir_thick,kind='quadratic')
                self.air_thick[i] = f_cubic(self.r[i]) #np.interp(self.r[i],rAir_loc,rAir_thick)
                f_cubic = interp1d(rAir_loc,rAir_camber,kind='quadratic')
                self.air_camber[i] = f_cubic(self.r[i]) #np.interp(self.r[i],rAir_loc,rAir_camber)
                
        
        """
        fig, axes = plt.subplots(2, 2, figsize=(10, 10))  # 2 row, 2 columns
        axes[0,0].plot(self.r,self.theta, marker='o')
        axes[0,0].grid(True)        
        axes[1,0].plot(self.r,self.chord, marker='o')
        axes[1,0].grid(True)
        axes[0,1].plot(self.r,self.air_thick, marker='o')
        axes[0,1].grid(True)        
        axes[1,1].plot(self.r,self.air_camber, marker='o')
        axes[1,1].grid(True)
        plt.show()
        """
class Stator:
    def __init__(self,vars,consts,rotor,hub,duct,id):

        # Inputs
        self.Taper = vars[id.staper]
        self.Nb = round(vars[id.snb])  # number of blades
        self.Twist = vars[id.stwist] # hub to root twist (hub pitch minus root pitch)
        self.Theta75 = vars[id.stheta75] # 3/4th span collective (R_75 defined as 0.75 * R_tip)
        self.Clearance = vars[id.sclear]
        self.Rake = vars[id.srake]

        # Internal variables
        self.nr = 10 # number of spanwise section definitions
        self.r = np.zeros(self.nr) # spanwise length array
        self.Z = np.zeros(self.nr) # vertical position array
        self.chord = np.zeros(self.nr) # chord
        self.theta = np.zeros(self.nr) # pitch
        self.Solidity = vars[id.ssolidity]
        R = consts[id.r]
        Rcout = vars[id.rcout]
        self.R_root = R * Rcout
        self.R_tip = R

        self.C_root = self.Solidity * np.pi * (self.R_tip**2)*2/(self.Nb*(self.R_tip-self.R_root)*(1+1/self.Taper)) # Root chord
        self.C_tip = self.C_root / self.Taper

        self.Z_root = -self.Clearance * hub.Length - (rotor.chord[0]*0.75 + self.C_root*0.25)
        self.Z_tip = self.Z_root - (self.R_tip - self.R_root) * math.tan(self.Rake*np.pi/180)


        ## Check clearance at hub

        hub_zmin = min(hub.xz[:,1])

        if self.Z_root - self.C_root < hub_zmin * 0.9:
            self.Z_root = hub_zmin*0.9 + self.C_root
            self.Clearance = -(self.Z_root + (rotor.chord[0]*0.75 + self.C_root*0.25))/hub.Length
            print("Stator root chord does not fit the hub under current rotor clearance. Clearance is reduced to make it fit")

            if self.Clearance < 0.05:
                raise ValueError("Insufficient clearance between stator and rotor (<5%) at hub. Reduce (1) stator solidity, (2) stator taper, or (3) increase hub length. Exiting computation...")


        ## check clearance at tip (duct)
        
        duct_zmin = min(duct.xz[:,1])

        if self.Z_tip - self.C_tip < duct_zmin * 0.9:
            self.Z_tip = duct_zmin*0.9 + self.C_tip
            self.Rake = math.atan((self.Z_root-self.Z_tip)/(self.R_tip-self.R_root)) / (np.pi/180)
            print("Stator tip chord does not fit the duct under current rake value. Rake is reduced to make it fit")

            if self.Rake < 0:
                raise ValueError("Rake angle becomes negative. Increase duct length, reduce dLE, reduce stator solidity, or increase stator taper to avoid negative rake. Exiting computation...")

        if self.Z_tip + self.C_tip*0.25 > -rotor.chord[-1]*0.75:
            raise ValueError("Insufficienct clearance between rotor and stator")   


        
        
        
        r_beg = 0
        z_beg = self.Z_root

        nd = len(duct.xz)
        R1 = np.interp(self.Z_tip,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0])
        R2 = np.interp(self.Z_tip,duct.xz[nd:nd//2:-1,1],duct.xz[nd:nd//2:-1,0])

        R_end = (R1+R2)/2
        z_end = self.Z_root - (R_end- self.R_root) * math.tan(self.Rake*np.pi/180)

        
        C_end = self.C_root + (self.C_tip-self.C_root)/(self.R_tip-self.R_root)*(R_end-self.R_root)

        r_up1 = np.interp(z_end+C_end*0.25,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0]) # internal duct radius at stator tip LE
        r_up2 = np.interp(z_end+C_end*0.25,duct.xz[nd:nd//2:-1,1],duct.xz[nd:nd//2:-1,0]) # external duct radius at stator tip LE
        
        r_dn1 = np.interp(z_end-C_end*0.75,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0]) # internal duct radius at stator tip TE
        r_dn2 = np.interp(z_end-C_end*0.75,duct.xz[nd:nd//2:-1,1],duct.xz[nd:nd//2:-1,0]) # external duct radius at stator tip TE

        if duct.Out_exp > 1:
            R_end = r_up2*0.2 + r_dn1*0.8

            if r_up2 - r_dn1 < R*0.01:
                raise ValueError("Duct too thin and/or aggressively diverging to fir stator tip")
        else:
            R_end = r_up1*0.8 + r_dn2*0.2

            if r_dn2 - r_up1 < R*0.01:
                raise ValueError("Duct too thin and/or aggressively converging to fir stator tip")
        
        d_up1 = R_end - r_up1# clearance on stator tip LE with internal duct surface
        d_up2 = r_up2 - R_end # clearance on stator tip LE with external duct surface
        
        
        if d_up1 < 0:
            R_end -= d_up1*1.05
        if d_up2 < 0:
            R_end += d_up2*1.05
 
        d_dn1 = R_end - r_dn1 # clearance on stator tip TE with internal duct surface
        d_dn2 = r_dn2 - R_end # clearance on stator tip TE with external duct surface

        if d_dn1 < 0:
            R_end -= d_dn1*1.05
        if d_dn2 < 0:
            R_end += d_dn2*1.05

        d_up1 = R_end - np.interp(z_end+C_end*0.25,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0]) # clearance on stator tip LE with internal duct surface
        d_up2 = np.interp(z_end+C_end*0.25,duct.xz[nd:nd//2:-1,1],duct.xz[nd:nd//2:-1,0]) - R_end # clearance on stator tip LE with external duct surface
        d_dn1 = R_end - np.interp(z_end-C_end*0.75,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0]) # clearance on stator tip TE with internal duct surface
        d_dn2 = np.interp(z_end-C_end*0.75,duct.xz[nd:nd//2:-1,1],duct.xz[nd:nd//2:-1,0]) - R_end # clearance on stator tip TE with external duct surface

        if d_up1 < 0 or d_up2 < 0 or d_dn1 < 0 or d_dn2 < 0:
            raise ValueError(f"Stator tip does not fit the duct due to too much contraction or divergence. d_up1:{d_up1}, d_up2:{d_up2} d_dn1:{d_dn1}, d_dn2:{d_dn2}")

        kk = np.argmin(abs(hub.xz[:,1]-z_beg-self.C_root*0.8))
        r1 = hub.xz[kk][0]/self.R_tip

        r1 = 0
        r2 = R_end/self.R_tip        

        self.r = np.linspace(r1,r2,self.nr)
        i = max(1,np.argmin(abs(self.r-Rcout)))
        self.r[i] = Rcout
        i = min(self.nr-2,np.argmin(abs(self.r-1)))
        self.r[i]  = 1
        self.dr = (r2-r1)/(self.nr-1)
        
        for i in range(self.nr):
            #self.Z[i] = self.Z_root - (self.r[i]*R - self.R_root) * math.tan(self.Rake*np.pi/180)
            self.Z[i] = self.Z_root - (self.r[i]*R) * math.tan(self.Rake*np.pi/180)

        # twist
        for i in range(self.nr):
            self.theta[i] = self.Theta75 - self.Twist/(1-Rcout)*(self.r[i] - 0.75)
        self.Theta0 = self.Theta75 - self.Twist/(1-Rcout)*(Rcout - 0.75) # Root Collective
        
      
        # taper
        nh = len(hub.xz)
        R_h = np.interp(self.Z_root,hub.xz[0:nd-2,1],hub.xz[0:nd-2,0])
        
        chord0_max = R_h/(0.75*abs(math.cos(self.theta[0]*np.pi/180))) * 0.7
            
        for i in range(self.nr):
            self.chord[i] = self.C_root * (1-(1-1/self.Taper)*(self.r[i]-Rcout)/(1-Rcout))
            #if self.r[i] < Rcout:
            #    self.chord[i] = min(self.chord[i],chord0_max)
        

        # Airfoils
        sAir_loc = np.zeros(id.nsair,dtype=float)
        sAir_thick = np.zeros(id.nsair,dtype=float)
        sAir_camber = np.zeros(id.nsair,dtype=float)
        for i in range(id.nsair):
            sAir_loc[i] = consts[id.sair_loc[i]]
            sAir_thick[i] = vars[id.sair_thick[i]]
            sAir_camber[i] = vars[id.sair_camber[i]]

        Nair = len(sAir_loc) # number of airfoil locations
        self.air_thick = np.zeros(self.nr)
        self.air_camber = np.zeros(self.nr)

        for i in range(self.nr):
            if self.r[i] < sAir_loc[0]:
                self.air_thick[i] = sAir_thick[0]
                self.air_camber[i] = sAir_camber[0]
            elif self.r[i] > sAir_loc[-1]:
                self.air_thick[i] = sAir_thick[-1]
                self.air_camber[i] = sAir_camber[-1]
            else:
                self.air_thick[i] = np.interp(self.r[i],sAir_loc,sAir_thick)
                self.air_camber[i] = np.interp(self.r[i],sAir_loc,sAir_camber)

        """
        fig, axes = plt.subplots(2, 2, figsize=(10, 10))  # 2 row, 2 columns
        axes[0,0].plot(self.r,self.theta, marker='o')
        axes[0,0].grid(True)        
        axes[1,0].plot(self.r,self.chord, marker='o')
        axes[1,0].grid(True)
        axes[0,1].plot(self.r,self.air_thick, marker='o')
        axes[0,1].grid(True)        
        axes[1,1].plot(self.r,self.air_camber, marker='o')
        axes[1,1].grid(True)
        plt.show()
        """
class Duct:
    def __init__(self,vars,consts,id):
        ## 4 point definition
        # p1-LE, p2- outer TE, p3 - inner TE, p4 - closest point to blade tip


        z_up = 0.03
        z_down = -0.055

        max_alpha = 8 # maximum divergence angle in degrees
        R = consts[id.r]
        self.Width = vars[id.dwidth] * R
        self.Length = vars[id.dlength] * R
        self.R_duct = consts[id.r]
        self.In_exp = vars[id.din_exp]
        self.Out_exp = vars[id.dout_exp]
        self.dLE = 0.3  # LE distance as a fraction of duct length, currently at 0.3 to match max thickness loc in NACA airfoils

        # Constraints
        alpha = math.atan((self.R_duct*abs(1-math.sqrt(self.In_exp)))/(self.Length*(1-self.dLE)))*180/np.pi

        if alpha > max_alpha:
            self.Length = (self.R_duct*abs(1-math.sqrt(self.In_exp)))/(math.tan(max_alpha*np.pi/180)*(1-self.dLE))



        # Calculate the NACA parameters
        chord = self.Length
        R_0 = self.R_duct + self.Width/2  # distance to cambe line from center at rotor plane
        t = self.Width/chord   # thickness
        R_in = self.R_duct * math.sqrt(self.In_exp)
        R_out = self.R_duct * math.sqrt(self.Out_exp)

        if R_in - self.R_duct > self.Width/1.5:
            self.Width = (R_in-self.R_duct)*1.5
            t = self.Width/chord   # thickness
        
        if R_out - self.R_duct > self.Width/1.5:
            self.Width = (R_out-self.R_duct)*1.5
            t = self.Width/chord   # thickness
        
        self.R_in = R_in
        self.R_out = R_out
        #print(R_in,R_out,R_0)
        
        m1 = (R_0 - R_in)/chord # inlet camber
        m2 = (R_0 - R_out)/chord # outlet camber
        p = self.dLE # rotor plane position

        n_points = 100

        # Generate the airfoil
        points = []
        for i in range(n_points):

            # Make it a exponential distribution so the points are more concentrated
            # near the leading edge
            x = (1 - np.cos(i / (n_points - 1) * np.pi)) / 2

            # Check if it is a symmetric airfoil
            if p == 0 and m == 0:
                # Camber line is zero in this case
                yc = 0
                dyc_dx = 0
            else:
                # Compute the camber line
                if x < p:
                    m = m1
                    yc = m / p**2 * (2 * p * x - x**2) - m1
                    dyc_dx = 2 * m / p**2 * (p - x)
                else:
                    m = m2
                    yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2) - m2
                    dyc_dx = 2 * m / (1 - p) ** 2 * (p - x)

            # Compute the thickness
            yt = 5 * t * (0.2969 * x**0.5
                        - 0.1260 * x
                        - 0.3516 * x**2
                        + 0.2843 * x**3
                        - 0.1015 * x**4)

            # Compute the angle
            theta = np.arctan(dyc_dx)

            # Compute the points (upper and lower side of the airfoil)
            xu = x - yt * np.sin(theta)
            yu = yc + yt * np.cos(theta)
            xl = x + yt * np.sin(theta)
            yl = yc - yt * np.cos(theta)

            points.append([xu*chord, yu*chord])
            points.insert(0,[xl*chord, yl*chord])

            # Remove the first point since it is repeated
            if i == 0:
                points.pop(0)

        n = len(points)
        self.xz = np.zeros((n,2))
        for i in range(n):
            self.xz[i][0] = points[i][1] + R_0 
            self.xz[i][1] = -points[i][0] + self.dLE * self.Length

        # izup = np.argmin(abs(self.xz[0:n_points,1]-z_up))
        # self.xz[izup][0] += 0.005
        # self.xz[izup+1][0] += 0.005

        # izdown = np.argmin(abs(self.xz[0:n_points,1]-z_down))
        # self.xz[izdown][0] += 0.005
        # self.xz[izdown+1][0] += 0.005
        

        """
        plt.plot(self.xz[:,0],self.xz[:,1])
        plt.axis('equal')
        plt.grid(True)
        plt.show()
        """
class Hub:
    def __init__(self,vars,consts,id):
        
        z_up = 0.03
        z_down = -0.045

        max_div_angle = 12
        xle = 0.25

        self.Length = vars[id.hlength] * consts[id.r]
        self.R = consts[id.r] * vars[id.rcout]
       
        alpha = math.atan(self.R/(self.Length*(1-xle)))*180/np.pi

        if alpha > max_div_angle:
            self.Length = self.R/(math.tan(max_div_angle*np.pi/180)*(1-xle))


        t = self.R*2/self.Length   # thickness

        n_points = 100
        # Generate the airfoil
        points = []
        for i in range(n_points):

            # Make it a exponential distribution so the points are more concentrated
            # near the leading edge
            x = (1 - np.cos(i / (n_points - 1) * np.pi)) / 2

            yc = 0
            dyc_dx = 0
            
            # Compute the thickness
            yt = 5 * t * (0.2969 * x**0.5
                        - 0.1260 * x
                        - 0.3516 * x**2
                        + 0.2843 * x**3
                        - 0.1015 * x**4)


            # Compute the points (upper and lower side of the airfoil)
            xu = x
            yu = yc + yt
            points.append([xu*self.Length, yu*self.Length])


        n = len(points)
        self.xz = np.zeros((n,2))
        for i in range(n):
            self.xz[i][0] = points[i][1] 
            self.xz[i][1] = -points[i][0] + self.Length*xle

        # izup = np.argmin(abs(self.xz[:,1]-z_up))
        # #print(izup,self.xz[izup][0],self.xz[izup][1])
        # self.xz[izup][0] -= 0.005
        # self.xz[izup+1][0] -= 0.005

        # izdown = np.argmin(abs(self.xz[:,1]-z_down))
        # self.xz[izdown][0] -= 0.005
        # self.xz[izdown+1][0] -= 0.005

        """
        plt.plot(self.xz[:,0],self.xz[:,1])
        plt.axis('equal')
        plt.grid(True)
        plt.show()
        """