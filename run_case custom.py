import shutil
import subprocess
import time
import os
import math
from unittest import case
from scipy import interpolate
#from classes import Rotor
#from classes import Duct
#from classes import Hub
#from typing import List, Union
import os
import numpy as np
import sys

import concurrent.futures
import ansys.fluent.core as pyfluent

from ansys.geometry.core import launch_modeler
from airfoil_gen import naca_airfoil_4digits
import shutil
#import id
#from id import inputs
#from id import vmin
#from id import vmax
#from id import const
from input import Input
import numpy as np
from scipy.interpolate import interp1d
from post_process import post_process
from post_process import run_acoustics
from scipy.interpolate import CubicSpline




class ID:
    def __init__(self):
        self.inputs = Input(rf"{case_folder}\inputs.yaml")

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
    def __init__(self,vars,consts):

        # Inputs
        self.R_tip = consts[id.r]   # rotor radius
        self.Solidity = vars[id.rsolidity]
        self.TP_type = consts[id.rtp_type] # taper definition 1-linear 
        self.TW_type = consts[id.rtw_type] # twist definition 1-linear 2- hy

        # self.TP_type = 4
        # self.TW_type = 4

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
        self.RPM = vars[id.rpm] 
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

        if self.TP_type == 4 and self.TW_type ==4:  # preset rotor
            self.theta = [
                100.4,
                87.0,
                75.0,
                64.0,
                55.0,
                48.0,
                43.0,
                39.0,
                35.0,
                34.3
            ]
            #     39.3, #39.0,
            #     35.6, #35.0,
            #     35 #34.3
            # ]

            # self.chord = [
            #     0.060,
            #     0.058,
            #     0.057,
            #     0.054,
            #     0.052,
            #     0.048,
            #     0.045,
            #     0.043,
            #     0.044,
            #     0.045
            # ]

            # self.chord = [
            #     0.060,
            #     0.060,
            #     0.059,
            #     0.058,
            #     0.057,
            #     0.056,
            #     0.054,
            #     0.052,
            #     0.050,
            #     0.050

            # ]

            # self.chord = [
            #     0.0542,
            #     0.0537,
            #     0.0531,
            #     0.0522,
            #     0.0513,
            #     0.0501,
            #     0.0486,
            #     0.0472,
            #     0.0450,
            #     0.0446
            # ]

            self.chord = [
                0.0600,
                0.0583,
                0.0567,
                0.0548,
                0.0530,
                0.0513,
                0.0495,
                0.0478,
                0.0450,
                0.0443

            ]

            self.r = np.array([
                0.00,
                0.12,
                0.22,
                0.35,
                0.47,
                0.58,
                0.70,
                0.82,
                1.00,
                1.05
            ])

            

            self.Rcout = vars[id.rcout]
            self.R_root = self.R_tip * self.Rcout
            self.Theta0 = np.interp(self.Rcout,self.r,self.theta)
            self.C_root = np.interp(self.Rcout,self.r,self.chord)



            
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
    def __init__(self,vars,consts,hub,duct):

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

        self.Z_root = -self.Clearance * hub.Length
        self.Z_tip = self.Z_root - (self.R_tip - self.R_root) * math.tan(self.Rake*np.pi/180)

        r_beg = 0
        z_beg = self.Z_root

        nd = len(duct.xz)
        R1 = np.interp(self.Z_tip,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0])
        R2 = np.interp(self.Z_tip,duct.xz[nd//2:nd,1],duct.xz[nd//2:nd,0])

        R_end = (R1+R2)/2
        z_end = self.Z_root - (R_end- self.R_root) * math.tan(self.Rake*np.pi/180)

        if z_end <  -(1-duct.dLE - 0.1) * duct.Length:
            z_end = -(1-duct.dLE - 0.1) * duct.Length 
            self.Rake = math.atan((z_beg-z_end)/(R_end-self.R_root))*180/np.pi

        self.C_root = self.Solidity * np.pi * (self.R_tip**2)*2/(self.Nb*(self.R_tip-self.R_root)*(1+1/self.Taper)) # Root chord
            
        self.C_tip = self.C_root / self.Taper

        C_end = self.C_root + (self.C_tip-self.C_root)/(self.R_tip-self.R_root)*(R_end-self.R_root)

        d_up1 = R_end - np.interp(z_end+C_end*0.25,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0])
        d_up2 = np.interp(z_end+C_end*0.25,duct.xz[nd//2:nd,1],duct.xz[nd//2:nd,0]) - R_end
        
        if d_up1 < 0:
            R_end -= d_up1*1.05
        if d_up2 < 0:
            R_end += d_up2*1.05

        d_dn1 = R_end - np.interp(z_end-C_end*0.75,duct.xz[0:nd//2,1],duct.xz[0:nd//2,0])
        d_dn2 = np.interp(z_end-C_end*0.75,duct.xz[nd//2:nd,1],duct.xz[nd//2:nd,0]) - R_end

        if d_dn1 < 0 or d_dn2 < 0:
            self.tip_connection = False
        else:
            self.tip_connection = True

        kk = np.argmin(abs(hub.xz[:,1]-z_beg-self.C_root*0.8))
        r1 = hub.xz[kk][0]/self.R_tip

        r1 = Rcout*0.7
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
    def __init__(self,vars,consts):
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
    def __init__(self,vars,consts):
        
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
def run_geo(variables,constants,case_folder):

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

    
    rotor = Rotor(variables,constants)
    duct = Duct(variables,constants)
    hub = Hub(variables,constants)
    time2 = time.time()
    print(f"Rotor, duct, and hub structures created in {time2-time1} seconds")

    make_curves(rotor,duct,hub,case_folder)
    time3 = time.time()
    print(f"Curve files written in {time3-time2} seconds")
    
    
    script_file = make_discovery_script(rotor,duct,hub,case_folder)
    time3 = time.time()
    print(f"Discovery script written in {time3-time2} seconds")
   
    return script_file
def make_curves(rotor,duct,hub,case_folder):

    # duct
    file = open(case_folder+"\\duct.txt",'w')
    file.write("3d=true\npolyline=false\nfit=false\n")
    for i in range(len(duct.xz)):
        #file.write(f"0 {duct.xz[i][0]} {duct.xz[i][1]}\n")
        file.write(f"{duct.xz[i][1]} 0 {duct.xz[i][0]}\n")
    file.close()

    # hub
    file = open(case_folder+"\\hub.txt",'w')
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
        file = open(case_folder+f"\\blade_cross_{i}.txt",'w')
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
def make_discovery_script(rotor,duct,hub,case_folder):
    
    near_zmax = max(max(hub.xz[:,1]),max(duct.xz[:,1])) + rotor.R_tip/2
    near_zmin = min(min(hub.xz[:,1]),min(duct.xz[:,1])) - rotor.R_tip/2
    near_rmax = max(duct.xz[:,0]) + rotor.R_tip/2

    off_zmax = rotor.R_tip * 10
    off_zmin = -rotor.R_tip * 10
    off_rmax = rotor.R_tip * 10

    #script_file = case_folder+f'\\disc_script.py'
    script_file = case_folder+f'\\DiscoveryGeometryBuilder.py'
    file = open(script_file,'w')
    
    file.write("# Python Script, API Version = V242\nimport shutil\n# USER INPUT\n")
    file.write(f"case_folder = r\"{case_folder}\"\n")
    file.write(f"num_blades = {rotor.Nb}\n")

    file.write("# Set 3D View\nmode = InteractionMode.Solid\nsketch_result = ViewHelper.SetViewMode(mode)\n")

    file.write(
        f"# General Definitions\n"
        f"y_axis = Line.Create(Point.Origin, Direction.DirZ)\n"
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
        'init_pattern_result = Move.Rotate(selection, y_axis, angle, options)\n'
        'pattern = ComponentSelection.Create(init_pattern_result.GetCreated[IComponent]())\n'
        'data = CircularPatternModificationData()\n'
        'data.CircularCount = num_blades\n'
        'data.StepAngle = angle\n'
        'pattern_result = Pattern.ModifyCircular(pattern, data)\n'
        'pattern_bodies = BodySelection.Create(pattern.Components[0].GetAllBodies())\n'
        'ComponentHelper.MoveBodiesToComponent(pattern_bodies, GetRootPart(), False)\n'
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
        '#options.ExtrudeType = ExtrudeType.Cut\n'
        'result = RevolveFaces.Execute(selection, y_axis, 2*math.pi, options)\n'
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
        'y_axis = Line.Create(Point.Origin, Direction.DirZ)\n'
        'options = RevolveFaceOptions()\n'
        'options.ExtrudeType = ExtrudeType.Cut\n'
        'result = RevolveFaces.Execute(selection, y_axis, DEG(-360), options)\n'
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
        'revolve_result_0 = RevolveFaces.Execute(Selection.Create([get_faces[0]]), y_axis, half_angle, options)\n'
        'targets = Selection.Create(revolve_result_0.GetCreated[IDesignBody]())\n'
        'merge_result_0 = Combine.Merge(targets)\n'
        'revolve_result_1 = RevolveFaces.Execute(Selection.Create([get_faces[1]]), y_axis, half_angle, options)\n'
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
    
    
    
    # Share Topology
    file.write(f"options = ShareTopologyOptions()\noptions.Tolerance = M(0.0005)\nresult = ShareTopology.FindAndFix(options)\n")
    # EndBlock
    geo_file = f"{case_folder}\\geo.dsco"
    if os.path.exists(geo_file):
        print("Ovewriting")
        os.remove(geo_file)
    file.write(f"# Save Project As\nFile.SaveAs(r\"{geo_file}\")\n")
    
    fluent_file = f"{case_folder}\\case.pmdb"
    if os.path.exists(fluent_file):
        print("Ovewriting")
        os.remove(fluent_file)
    file.write(f"Workbench.Fluent.ExportPMDB(r\"{fluent_file}\")\n")
    
    



    file.close()

    return script_file
def make_mesh(meshing,in_file,out_file,alpha_per,mode,R_tip):

    time0 = time.time()

    #mesh size definitions
    max_size = 100 *R_tip/0.3 # mm
    min_size_blade = 0.5 *R_tip/0.3 # mm
    min_size_blade2 = 0.05 *R_tip/0.3 # mm
    min_size_duct_hub = 1 *R_tip/0.3 # mm
    curv_angle = 5 # deg
    cell_size_blade = 3  *R_tip/0.3# mm
    cell_size_blade2 = 0.3 *R_tip/0.3 # mm
    cell_size_duct_hub = 6  *R_tip/0.3# mm
    cell_size_nearbody = 8 *R_tip/0.3 # mm
    growth_rate = 1.2
    nBL = 3 # number of boundary layers


    # max_size = 100 # mm
    # min_size_blade = 0.01 # mm
    # min_size_duct_hub = 0.8 # mm
    # curv_angle = 5 # deg
    # cell_size_blade = 2 # mm
    # cell_size_duct_hub = 4 # mm
    # cell_size_nearbody = 8 # mm
    # growth_rate = 1.2
    # nBL = 15 # nu

    print("Launching Fluent Meshing...\n")
   

    if os.path.exists(out_file):
        print("Ovewriting")
        os.remove(out_file)
    else:
        print("Writing new mesh file")
    print(meshing.get_fluent_version()) 
    meshing.workflow.InitializeWorkflow(WorkflowType='Watertight Geometry')
    workflow = meshing.workflow
    
    print("Importing geometry\n")
    workflow.TaskObject['Import Geometry'].Arguments.set_state({r'FileName': in_file,r'LengthUnit': r'mm',})
    workflow.TaskObject['Import Geometry'].Execute()
    print("Adding local sizing...\n")
    
    if mode == 1:
        workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade1'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
        workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face2',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade2,r'BOIZoneorLabel': r'label',})
    else:
        workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'blade1',r'blade2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_blade,r'BOIZoneorLabel': r'label',})
    
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_face',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Face Size',r'BOIFaceLabelList': [r'duct1',r'duct2', r'hub1', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    
    if mode == 1:
        workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade1'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
        #workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve2',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade2,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    else:
        workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'blade_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'blade1',r'blade2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_blade,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'duct_hub_curve',r'BOICurvatureNormalAngle': curv_angle,r'BOIExecution': r'Curvature',r'BOIFaceLabelList': [r'duct1',r'duct2', r'hub1', r'hub2'],r'BOIGrowthRate': growth_rate,r'BOIMaxSize': max_size,r'BOIMinSize': min_size_duct_hub,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Local Sizing'].Arguments.set_state({r'AddChild': r'yes',r'BOICellsPerGap': 1,r'BOIControlName': r'nearbody',r'BOICurvatureNormalAngle': 18,r'BOIExecution': r'Body Size',r'BOIFaceLabelList': [r'nearbody'],r'BOIGrowthRate': growth_rate,r'BOISize': cell_size_nearbody,r'BOIZoneorLabel': r'label',r'DrawSizeControl': True,})
    workflow.TaskObject['Add Local Sizing'].AddChildAndUpdate(DeferUpdate=False)

    #input("Local sizing added. Press Enter to continue...\n")
    #workflow.TaskObject['Generate the Surface Mesh'].Arguments.set_state({r'CFDSurfaceMeshControls': {r'CurvatureNormalAngle': curv_angle,r'MaxSize': max_size,r'MinSize': min_size_blade,},})
    #workflow.TaskObject['Generate the Surface Mesh'].Arguments.set_state({r'CFDSurfaceMeshControls': {r'MinSize': min_size_blade,},})
    workflow.TaskObject['Generate the Surface Mesh'].Execute()

    #input("Surface mesh generated. Press Enter to continue...\n")
    time1 = time.time()
    print(f"Surface mesh generated in {time1-time0} seconds\n")
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=False)
    workflow.TaskObject['Describe Geometry'].Arguments.set_state({r'InvokeShareTopology': r'No',r'NonConformal': r'No',r'SetupType': r'The geometry consists of only fluid regions with no voids',r'WallToInternal': r'Yes',})
    workflow.TaskObject['Describe Geometry'].UpdateChildTasks(Arguments={r'v1': True,}, SetupTypeChanged=True)
    workflow.TaskObject['Describe Geometry'].Execute()
    workflow.TaskObject['Update Boundaries'].Execute()
    workflow.TaskObject['Update Regions'].Execute()

    print("Boundaries and regions updated\n")
    #input("Enter to continue")
    workflow.TaskObject['Add Boundary Layers'].Arguments.set_state({r'BlLabelList': [r'blade1',r'blade2', r'duct1', r'duct2', r'hub1', r'hub2'],r'FaceScope': {r'GrowOn': r'selected-labels',},r'LocalPrismPreferences': {r'Continuous': r'Continuous',},r'NumberOfLayers': nBL,})
    workflow.TaskObject['Add Boundary Layers'].AddChildAndUpdate(DeferUpdate=False)
    workflow.TaskObject['Add Boundary Layers'].InsertNextTask(CommandName=r'SetUpPeriodicBoundaries')
    
    print("Boundary layers added\n")
    
    #input("Enter to continue")
    workflow.TaskObject['Set Up Periodic Boundaries'].Arguments.set_state({r'AutoMultiplePeriodic': r'no',r'LCSOrigin': {r'OriginX': 0,r'OriginY': 0,r'OriginZ': 0,},r'LCSVector': {r'VectorX': 0,r'VectorY': 0,r'VectorZ': 0,},r'LabelList': [r'per1', r'per2'],r'ListAllLabelToggle': False,r'MeshObject': r'',r'Method': r'Automatic - pick both sides',r'MultipleOption': r'Paired',r'PeriodicityAngle': alpha_per,r'RemeshBoundariesOption': r'auto',r'SelectionType': r'label',r'TransShift': {r'ShiftX': 0,r'ShiftY': 0,r'ShiftZ': 1,},r'Type': r'Rotational',})
    workflow.TaskObject['Set Up Periodic Boundaries'].Execute()
    print("Periodic boundary set up")
    
    #input("Enter to continue")
    workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'polyhedra',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    #workflow.TaskObject['Generate the Volume Mesh'].Arguments.set_state({r'VolumeFill': r'tetrahedral',r'VolumeFillControls': {r'GrowthRate': growth_rate,r'TetPolyMaxCellLength': max_size,},})
    workflow.TaskObject['Generate the Volume Mesh'].Execute()
    time2 = time.time()
    
    #input("Enter to continue")
    print(f"Volume mesh generated in {time2-time0} seconds")
    if os.path.exists(out_file):
        print("Ovewriting")
        os.remove(out_file)
    meshing.tui.file.write_mesh(out_file)
    print("Mesh file written")
    time3 = time.time()
    print(f"Total meshing time is {time3-time0} seconds")
    
    return out_file
def run_solver(solver,var,const,mesh_file,case_folder,niter_fluent,nloops,gpu_cfd,mode):

    # runs simulation
    time0 = time.time()

    eps = 0.01 # convergence criteria
    temp = 288.15 # sea level
    niter_avg = 30 # average over n steps
    a0 = math.sqrt(1.4*287*temp)
    igpu = True

    
    vinf = const[id.vinf]
    omega = const[id.rpm]*2*np.pi/60
    nb = int(var[id.rnb])
    T_target = const[id.thrust]
    print("Target Thrust:",T_target)
    print(const)
    R = const[id.r]
 
    #input("Enter")
    print(mesh_file)
    solver.file.read_mesh(file_name=mesh_file)
    solver.mesh.check()

    # define material
    solver.setup.materials.fluid["air"] = {
        "density": {
            "option": "ideal-gas"
        },
    }

    # boundary conditions

    boundary_conditions = solver.setup.boundary_conditions
    boundary_conditions.velocity_inlet['inlet'] = {
        "momentum" : {
            "flow_direction" : [0, 0, -1], 
            "velocity" : {"value" : vinf}, 
            "velocity_specification_method" : "Magnitude and Direction"
        },
        "thermal" : {
            "temperature": {"value": temp}
        }
    }

    boundary_conditions.wall['duct1'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['duct2'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['hub1'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }
    boundary_conditions.wall['hub2'] = {
        "momentum" :{
            "wall_motion" : "Moving Wall",
            "relative" : False,
            "rotating" : True,
            "rotation_axis_direction" : [0, 0, 1],
            "rotation_speed" : 0,
        }
    }


    solver.settings.setup.cell_zone_conditions.fluid['nearbody'] = {
        "reference_frame" : {
            "reference_frame_zone_motion_function" : "none", 
            "reference_frame_axis_direction" : [0, 0, 1], 
            "reference_frame_axis_origin" : [0., 0., 0.], 
            "reference_frame_velocity" : [0., 0., 0.], 
            "mrf_omega" : omega, 
            "mrf_relative_to_thread" : "absolute", 
            "frame_motion" : True
        }
    }


    # report definitions
    if gpu_cfd:
        if mode == 1:
            solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "report_output_type": "Force"}
            solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "report_output_type": "Moment"}
        else:
            solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1"], "report_output_type": "Force"}
            solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "report_output_type": "Moment"}
            # solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
            # solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "report_output_type": "Force"}
            # solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "report_output_type": "Moment"}

        solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "report_output_type": "Force"}
        solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "report_output_type": "Force"}
        
    else:
        if mode == 1:
            solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"]}
            solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1","blade2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
        else:    
            solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","duct1","duct2","hub1","hub2"]}
            solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1"], "retain_instantaneous_values" : True}
            solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
        
        solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True}
        solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["hub1","hub2"], "retain_instantaneous_values" : True}

    fname = f"{case_folder}\\forces.out"
    fname2 = f"{case_folder}\\torques.out"
    
    if os.path.exists(fname):
        os.remove(fname)

    solver.solution.monitor.report_files['forces'] = {"report_defs" : ["total_thrust","torque","blade_thrust","duct_thrust","hub_thrust"], "write_instantaneous_values" : True, "print" : True, "file_name": fname}
    solver.solution.monitor.report_plots['total_thrust'] = {"print" : True, "report_defs" : ["total_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['blade_thrust'] = {"print" : True, "report_defs" : ["blade_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['duct_thrust'] = {"print" : True, "report_defs" : ["duct_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['hub_thrust'] = {"print" : True, "report_defs" : ["hub_thrust"], "plot_instantaneous_values" : True}
    solver.solution.monitor.report_plots['torque'] = {"print" : True, "report_defs" : ["torque"], "plot_instantaneous_values" : True}

    # convergence criteria
     
    solver.tui.solve.monitors.residual.convergence_criteria(
        "1e-4","1e-4","1e-4","1e-4","1e-3","1e-4",
    )

    solver.tui.solve.monitors.residual.check_convergence("no","no","no","no","no","no","no")

    solver.solution.monitor.convergence_conditions = {"convergence_reports" : {"conv_thrust" : {"report_defs" : "total_thrust", "print" : True, "previous_values_to_consider" : niter_avg, "stop_criterion" : 0.001}}}
    solver.solution.monitor.convergence_conditions = {"convergence_reports" : {"conv_torque" : {"report_defs" : "torque", "print" : True, "previous_values_to_consider" : niter_avg, "stop_criterion" : 0.001}}}
    
    
    
    solver.setup.reference_values.compute(from_zone_type = "velocity-inlet", from_zone_name = "inlet", phase = "mixture")
    
    

    time1 = time.time()

    print(f"Solver configured in  {(time1-time0)/60} mins")

    #input("enter")
    # Run simulation
    solver.settings.solution.methods.p_v_coupling.flow_scheme = "Coupled"
    solver.settings.solution.methods.pseudo_time_method.formulation.coupled_solver = "global-time-step"
    #solver.tui.solve.set.p_v_coupling("24")
    #solver.tui.solve.set.pseudo_time_method.formulation("1")
    solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = "user-specified"
    solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = 1.5 * 1.0/omega  # 2.5 x dt
    #solver.tui.solve.set.pseudo_time_method.global_time_step_settings("no", f"{1/omega}")
    solver.solution.initialization.hybrid_initialize()
 
    #input("Initialization complete. Press Enter to start iterations...\n")

    Error = 1.0
    iter = 0
    A = math.pi * const[id.r]**2  # disk area
    sigma = var[id.dout_exp]    # duct outlet expansion ratio
    rho = const[id.rho]  # Air density at sea level (kg/m^3)

    ns_error = 0

    #input("Initialization complete. Press Enter to start iterations...\n")
    while Error > eps:
        if iter >= nloops:
            break
        
        #input("Press Enter to continue to next loop...\n")
        solver.solution.run_calculation.iterate(iter_count=niter_fluent)
        T_total,T_blade,T_duct,T_hub,Q,convergence = read_force(fname,igpu,nb,ns_error,fname2)

         
        
        print(f"CFD iteration {iter+1} of {3} with omega = {omega:.3f} rad/s")
        print(f"    T_target = {T_target:.3f}N, T_total = {T_total:.3f} N, T_blade = {T_blade:.3f} N, T_duct = {T_duct:.3f} N, T_hub = {T_hub:.3f} N, Q = {Q:.3f} Nm")
        
        
        if iter == 0:
            niter_fluent /= 2


        iter += 1
        
        
        omega_new = math.sqrt(abs(T_target/T_total)) * omega

        Error = abs((omega_new - omega)/omega)
        
        print(f"    Error = {Error:.3f}, omega_new = {omega_new:.3f} rad/s")
        
        FM = T_total**1.5 / (Q*omega * math.sqrt(4 * rho * A * sigma))  # Figure of Merit
       
        if FM > 1.1:

            # Apparently Discovery screws up the named selections (temporary fix)
            if gpu_cfd:
                if mode == 1:
                    solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
                    solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "report_output_type": "Force"}
                    solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "report_output_type": "Force"}
                else:
                    solver.solution.report_definitions.force['total_thrust'] = {"force_vector" : [0, 0, 1],  "zones" : ["blade1","duct1","duct2","hub1","hub2"], "report_output_type": "Force"}
                    solver.solution.report_definitions.force['duct_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "report_output_type": "Force"}
                    solver.solution.report_definitions.force['hub_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "report_output_type": "Force"}

                solver.solution.report_definitions.force['blade_thrust'] = {"force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "report_output_type": "Force"}
                solver.solution.report_definitions.moment['torque'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1","duct2"], "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque1'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "report_output_type": "Moment"}
                if mode==1:
                    solver.solution.report_definitions.moment['torque2'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade2"], "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque3'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1"], "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque4'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct2"], "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque5'] = {"mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["hub1","hub2"], "report_output_type": "Moment"}
                
            else:
                if mode == 1:
                    solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","blade2","duct1","duct2","hub1","hub2"]}
                    solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "retain_instantaneous_values" : True}
                    solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","blade2","hub1","hub2"], "retain_instantaneous_values" : True}
                else:
                    solver.solution.report_definitions.force['total_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "retain_instantaneous_values" : True, "zones" : ["blade1","duct1","duct2","hub1","hub2"]}
                    solver.solution.report_definitions.force['duct_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "retain_instantaneous_values" : True}
                    solver.solution.report_definitions.force['hub_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["blade1","hub1","hub2"], "retain_instantaneous_values" : True}
                    
                solver.solution.report_definitions.force['blade_thrust'] = {"average_over" : niter_avg, "force_vector" : [0, 0, 1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True}
                solver.solution.report_definitions.moment['torque'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1","duct2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque1'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                if mode == 1:
                    solver.solution.report_definitions.moment['torque2'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["blade2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque3'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct1"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque4'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["duct2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                solver.solution.report_definitions.moment['torque5'] = {"average_over" : niter_avg, "mom_center" : [0, 0., 0.], "mom_axis" : [0, 0, -1], "zones" : ["hub1","hub2"], "retain_instantaneous_values" : True, "report_output_type": "Moment"}
                


            solver.solution.monitor.report_files['forces'] = {"report_defs" : ["torque1","torque2","torque3","torque4","torque5"], "write_instantaneous_values" : True, "print" : True, "file_name": fname2}
            ns_error = 1
            Error = 1.0
            print("Changing named selections to fix Discovery issue")

        omega = omega_new
        solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = 1.0/omega*1.5
        solver.settings.setup.cell_zone_conditions.fluid['nearbody'] = {
        "reference_frame" : {
            "mrf_omega" : omega, 
        }
        }

        #input("enter to continue")
       
    time2 = time.time()

    print(f"Simulation run in  {(time2-time1)/60} mins")

    if convergence == 0:
        print("Case did not converge")

    P = Q * omega
    DL = T_total / 9.81 / A  # disk loading in kg/m^2
    PL = (T_total/9.81) / (P/1000) # power loading in kg/kW
    OF_out = P / T_total  # Objective function: Power / Total Thrust

    if P != 0:
        power_loading = (T_total/9.81) / (P/1000) # kg/kW
        disk_loading = T_total / 9.81 / A # disk loading in kg/m2
        FM = T_total**1.5 / (P * math.sqrt(4 * rho * A * sigma))  # Figure of Merit
        rpm = omega * 60 / (2 * math.pi)
        duct_share = T_duct / T_total * 100 if T_total != 0 else 0
        print(f"Thrust: {T_total:.2f} N | Power: {P:.2f} W | Torque: {Q:.2f} Nm | RPM: {rpm:.2f} | Duct Share: {duct_share:.1f}% | Disk Loading: {disk_loading:.2f} kg/m^2 | Power Loading: {power_loading:.2f} kg/kW | FM: {FM:.3f}")
    else:
        print("Thrust: Undefined | Power: Undefined | Torque: Undefined | RPM: Undefined | Duct Share: Undefined | Disk Loading: Undefined | Power Loading: Undefined | FM: Undefined")
    

    # Access the graphics object
    # graphics = solver.settings.results.graphics
    # # Set the hardcopy format for saving the image
    # graphics.picture.driver_options.hardcopy_format = "png" 
    # # Set View
    # contour_view = graphics.views.display_states.create("contour_view")
    # contour_view.front_faces_transparent = "disable"
    # contour_view.view_name = "front"
    # pressure_contour = graphics.contour.create(name="pressure_contour")
    # pressure_contour.field = "pressure"
    # if mode == 1:
    #     pressure_contour.surfaces_list = ["blade1","blade2","duct1","duct2","hub1","hub2"]
    # else:
    #     pressure_contour.surfaces_list = ["blade1","duct1","duct2","hub1","hub2"]
    # pressure_contour.display_state_name = contour_view.name()
    # pressure_contour.display()
    # pressure_contour.color_map.visible = False
    # pressure_contour.color_map.font_size = 12
    # #graphics.views.camera.target = [0.2, 0.0, 0.0]
    # #graphics.views.camera.position = [-0.95, -1.25, 0.95]
    # graphics.views.auto_scale()
    # if graphics.picture.use_window_resolution.is_active():
    #     graphics.picture.use_window_resolution = False
    
    # graphics.picture.x_resolution = 1920
    # graphics.picture.y_resolution = 1440   
    # graphics.picture.save_picture(file_name=f"{case_folder}\\surface.png")

    solver.settings.results.surfaces.plane_slice['plane-1'] = {'normal' : [0, 0, 1], 'distance_from_origin' : 0.05}
    solver.settings.results.surfaces.plane_slice['plane-2'] = {'normal' : [0, 0, 1], 'distance_from_origin' : -0.05}
    if mode == 1: 
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface.dat", 
                                          surface_name_list = ["blade1", "blade2"], 
                                          delimiter = 'comma', 
                                          cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                          location = 'cell-center'
                                          )
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface_acum.dat", 
                                          surface_name_list = ["blade1", "blade2","duct1","duct2","hub1","hub2"], 
                                          delimiter = 'comma', 
                                          cell_func_domain = ['pressure','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                          location = 'cell-center'
                                          )
    else:
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface.dat", 
                                          surface_name_list = ["blade1"], 
                                          delimiter = 'comma', 
                                          cell_func_domain = ['density', 'pressure', 'wall-shear', 'x-wall-shear', 'y-wall-shear', 'z-wall-shear','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                          location = 'cell-center'
                                          )
        solver.settings.file.export.ascii(file_name = f"{case_folder}\\surface_acum.dat", 
                                          surface_name_list = ["blade1","duct1","duct2","hub1","hub2"], 
                                          delimiter = 'comma', 
                                          cell_func_domain = ['pressure','face-area-magnitude', 'x-face-area', 'y-face-area', 'z-face-area'], 
                                          location = 'cell-center'
                                          )
        
    solver.settings.file.export.ascii(file_name = f"{case_folder}\\slice_up.dat", 
                                      surface_name_list = ["plane-1"], 
                                      delimiter = 'comma', 
                                      cell_func_domain = ['density', 'pressure', 'velocity-magnitude', 'x-velocity', 'y-velocity', 'z-velocity','vorticity-mag'], 
                                      location = 'cell-center'
                                      )
    solver.settings.file.export.ascii(file_name = f"{case_folder}\\slice_down.dat", 
                                      surface_name_list = ["plane-2"], 
                                      delimiter = 'comma', 
                                      cell_func_domain = ['density', 'pressure', 'velocity-magnitude', 'x-velocity', 'y-velocity', 'z-velocity','vorticity-mag'], 
                                      location = 'cell-center'
                                      )
    

    #input("Simulation complete. Press Enter to continue...\n")

    return T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, OF_out
def read_force(file_path,igpu,nb,ns_error,file_torque):
    # Reads final forces and moments
    niter_avg = 30


    with open(file_path,"r") as file:
        lst = [line.strip().split() for line in file]

    niter_avg = min(niter_avg,len(lst)-3)


    
    if igpu:
        T_total = 0.0
        T_blade = 0.0
        T_duct = 0.0
        T_hub = 0.0
        Q = 0.0
        for j in range(niter_avg):
            T_total += float(lst[-niter_avg+j][1])/niter_avg
            Q += float(lst[-niter_avg+j][2])/niter_avg
            T_blade += float(lst[-niter_avg+j][3])/niter_avg
            T_duct += float(lst[-niter_avg+j][4])/niter_avg
            T_hub += float(lst[-niter_avg+j][5])/niter_avg
                    
    else:
        T_total = float(lst[-1][1])
        Q = float(lst[-1][3])
        T_blade = float(lst[-1][5])
        T_duct = float(lst[-1][7])
        T_hub = float(lst[-1][9])

    if ns_error == 1:
        with open(file_torque,"r") as file:
            lst2 = [line.strip().split() for line in file]
        if igpu:
            Q1 = 0.0
            Q2 = 0.0
            Q3 = 0.0
            Q4 = 0.0
            Q5 = 0.0
            for j in range(niter_avg):
                Q1 += float(lst2[-niter_avg+j][1])/niter_avg
                Q2 += float(lst2[-niter_avg+j][2])/niter_avg
                Q3 += float(lst2[-niter_avg+j][3])/niter_avg
                Q4 += float(lst2[-niter_avg+j][4])/niter_avg
                Q5 += float(lst2[-niter_avg+j][5])/niter_avg
                        
        else:
            Q1 = float(lst2[-1][1])
            Q2 = float(lst2[-1][3])
            Q3 = float(lst2[-1][5])
            Q4 = float(lst2[-1][7])
            Q5 = float(lst2[-1][9])
        Q = max(Q1,Q2,Q3,Q4,Q5)
        T_blade= 0
        T_duct = 0
        T_hub = 0

    print(f"Total Thrust: {T_total:.2f} N, Blade Thrust: {T_blade:.2f} N, Duct Thrust: {T_duct:.2f} N, Hub Thrust: {T_hub:.2f} N, Torque: {Q:.2f} Nm, Nb: {nb}")

    return T_total*nb,T_blade*nb,T_duct*nb,T_hub*nb,Q*nb,1
def calculate_aerodynamic_Q(thrust, Lb, ne):
    # Inputs
    # thrust: function (Rn->Rn)
    # Lb: scalar
    # ne: scalar
    ## Parameters
    nn      = ne + 1    # number of nodes
    Le      = Lb/ne     # Longitud of an Element [m]

    ## Elemental Matrices
    Dl = np.diag([1, Le, 1, Le])
    Ab = np.array([ [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [1, 1, 1, 1],
                    [0, 1, 2, 3]])
    Hbar = np.linalg.inv(Ab).T
    H    = np.dot(Dl, Hbar)

    ## Basis
    neps  = 1000
    eps = np.linspace(0, 1, neps)

    ## Generalized Force
    Q   = np.zeros((2*nn, 1))
    Ie  = np.zeros((4,1))
    re  = 0
    for r in range(ne):
        thrust_eps = thrust(re + Le*eps)
        for kr in range(4):
            Ie[kr] = np.trapezoid(thrust_eps * eps**kr, eps)
        Qe = Le * (H @ Ie)
        
        p = [2*r + i for i in range(4)]
        Q[np.ix_(p)] += Qe
        
        re = re + Le
    return Q
def get_mass_and_stiffness(mu, EI, Lb, ne):
    # Inputs
    # mu: function (Rn->Rn)
    # EI: function (Rn->Rn)
    # Lb: scalar
    # ne: scalar
    ## Parameters
    nn      = ne + 1    # number of nodes
    Le      = Lb/ne     # Longitud of an Element [m]

    ## Elemental Matrices
    Dl = np.diag([1, Le, 1, Le])
    Ab = np.array([ [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [1, 1, 1, 1],
                    [0, 1, 2, 3]])
    Hbar = np.linalg.inv(Ab).T
    H    = np.dot(Dl, Hbar)

    ## Basis
    neps  = 1000
    eps = np.linspace(0, 1, neps)

    ## FEM
    M = np.zeros((2 * nn, 2 * nn))
    K = np.zeros((2 * nn, 2 * nn))

    Ime = np.zeros((4,4))
    Ike = np.zeros((4,4))
    re = 0
    for r in range(ne):
        ## Me
        mu_eps = mu(re + eps*Le)
        for kr in range(4):
            Ime[kr,kr] = np.trapezoid(mu_eps * eps**(2*kr), eps)
            for kc in range(kr+1, 4):
                Ime[kr, kc] = np.trapezoid(mu_eps * eps**(2*kr + kc - kr), eps)
                Ime[kc, kr] = Ime[kr, kc]
        Me = Le * (H @ Ime @ H.T)
        
        ## Ke
        EI_eps = EI(re + eps*Le)
        Ike[2,2] = np.trapezoid(EI_eps * 4, eps)
        Ike[3,3] = np.trapezoid(EI_eps * 36 * eps**2, eps)
        Ike[2,3] = np.trapezoid(EI_eps * 12 * eps, eps)
        Ike[3,2] = Ike[2,3]
        Ke  = (1/(Le**3)) * (H @ Ike @ H.T)
            
        ## M and K Matrices
        p = [2*r + i for i in range(4)]
        K[np.ix_(p, p)] += Ke
        M[np.ix_(p, p)] += Me
                
        re = re + Le
    return M, K
def get_static_deformation(K, Q, ds):
    q   = np.linalg.solve(K, Q)
    y   = q[ds]
    yadim = y / np.max(np.absolute(y))
    n   = len(y)
    return y, yadim, n
class Rotor_structure:
    def __init__(self, nb, rhub, rtip, rpm, thrustp):
        self.nb         = nb
        self.rhub       = rhub
        self.rtip       = rtip
        self.rcout      = rhub/rtip
        self.lb         = rtip - rhub
        self.rpm        = rpm
        self.thrustp    = thrustp
class Elem:
    def __init__(self, n, r, theta, chord):
        self.n      = n
        self.r      = np.array(r)
        self.theta  = np.array(theta)
        self.chord  = np.array(chord)
class Str:
    def _get_str_constants(self):
        self.max_stress  = 500e6 # Structural yield stress [Pa]
        self.rho_str     = 2000  # Structural density [kg/m3]
        self.rho_foam    = 200   # Foam density [kg/m3]
        self.lf          = 1.8   # Load Factor
        self.sf          = 1.5   # Safety Factor
        self.young       = 500e6 # Elastic module [Pa]

    def __init__(self, a_th):
        self._get_str_constants()
        self.a_th       = a_th   # Airfoil Thickness at the root as a fraction of the chord
def set_boundaries(A, type_, fixVariables, concentratedMass, concentratedStiffness, concentratedCentripetal):
    # Type must be: M, K, Q, Ms, Ks, Kn, Qw, Qa, ...  or ds
    if type_[0] == 'M':
        if type_ == "M" or type_ == 'Ms':
            A = add_mass(A, concentratedMass)
        A = fix_vars(A, fixVariables)
        n = A.shape[0]
    elif type_[0] == 'K':
        if type_ == 'K':
            A = add_stiff(A, concentratedStiffness)
            A = add_centripetal_stiff(A, concentratedCentripetal)
        elif type_ == 'Ks':
            A = add_stiff(A, concentratedStiffness)
        elif type_ == 'Kn':
            A = add_centripetal_stiff(A, concentratedCentripetal)
        A = fix_vars(A, fixVariables)
        n = A.shape[0]
    elif type_[0] == 'Q':
        if type_ == 'Q' or type_ == 'Qw':
            A = add_grav_mass(A, concentratedMass)
        A = fix_vars(A, fixVariables)
        n = A.shape[0]
    else:
        if type_ == 'ds':
            A = fix_vars(A, fixVariables)
            n = A.shape[0]
        else:
            raise ValueError("Incorrect Type")
    
    return A, n
def fix_vars(A, datavars):
    datavars = np.sort(datavars)[::-1]
    for i in range(len(datavars)):
        k = datavars[i]
        if A.ndim == 1: # Case Generalized Force
            A = np.delete(A, k)
        elif A.shape[1] == 1:
            A = np.delete(A, k, axis=0)
        else: # Case Mass, Stiffness or Damping Matrix
            A = np.delete(A, k, axis=0)
            A = np.delete(A, k, axis=1)
    return A
def add_mass(A, datamass):
    for i in range(datamass.shape[0]):
        k   = 2*datamass[i, 0]
        mt  =   datamass[i, 1]
        A[k, k] += mt
    return A
def add_grav_mass(A, datamass):
    g = 9.81
    for i in range(datamass.shape[0]):
        k    = 2*datamass[i,0]
        mt   =   datamass[i,1]
        A[k] = A[k] - g*mt
    return A
def add_stiff(A, datastiff):
    for i in range(datastiff.shape[0]):
        k   = datastiff[i,0]
        kt  = datastiff[i,1]
        A[k,k] = A[k,k] + kt
    return A
def add_centripetal_stiff(A, datacent):
    for i in range(datacent.shape[0]):
        k       = 2*datacent[i,0]
        mt      =   datacent[i,1]
        w       =   datacent[i,2]
        A[k,k]  = A[k,k] + mt*w^2
    return A
def structural_design(rotor, elem, str):
    ## Parameters
    nb    = rotor.nb
    rhub  = rotor.rhub # [m]
    lb    = rotor.lb   # [m]
    r     = elem.r     # [m]
    chord = elem.chord # [m]
    theta = elem.theta # [rad/s]
    
    lp    = r[1]-r[0]
    xb    = r - rhub
    xi    = xb/lb

    omega   = rotor.rpm*2*np.pi/60
    thrustp = rotor.thrustp/nb

    ## Admissible Stress [Pa]
    pen_shear   = 1.2
    sigma_adm   = str.max_stress / (str.sf*pen_shear)

    ## Maximum Bending Moment (at the root) [Nm]
    mb_max      = rotor.thrustp/rotor.nb * lb/2 * str.lf

    ## Maximum Distributions
    hr_d = 0.9 * str.a_th/100 * chord
    wr_d = 0.4 * chord
    Jx_str_max_d = wr_d*hr_d**3/12

    ## Design parameters
    chord_des   = 0.7*np.mean(chord)
    hr_des      = 0.9 * str.a_th/100 * chord_des    # Height of rectangular element and is equal to 90% of the airfoil thickness [m]
    wr_des      = 0.4 * chord_des                   # Width of rectangular element and is equal to 40% airfoil width [m]

    Jx_des = min(2*min(Jx_str_max_d), 0.7*np.mean(Jx_str_max_d))

    ## Skin of the blade
    t_skin 	    = 2*0.25e-3                # Thickness of the outermost/last carbon fiber layer around the blade. Also called the skin [m]
    wr_skin     = 1.5*wr_d
    hr_skin     = hr_d

    Jx_skin = (hr_skin**3*wr_skin)/12 - (wr_skin-2*t_skin)*(hr_skin-2*t_skin)**3/12
    Jy_skin = (wr_skin**3*hr_skin)/12 - (hr_skin-2*t_skin)*(wr_skin-2*t_skin)**3/12
    Jb_skin = (Jx_skin + Jy_skin )/2 + (Jx_skin - Jy_skin )/2 * np.cos(2*theta)

    ## Checking if Jx is feasible and Calculating Inertia and Area
    Jx_str      = Jx_des
    hr          = hr_des
    wr          = wr_des
    coefs = np.array([16, -8*(wr+3*hr), 12*(wr*hr+hr**2), -2*(hr**3+3*wr*hr**2), 12*Jx_str])
    p = np.roots(coefs)
    p = np.real(p[abs(np.imag(p))<1e-6])
    p = p[p > 0]
    if len(p) == 0:
        p = hr/2
    t = np.min(p)

    A_str   = hr*wr - (hr-2*t)*(wr-2*t);             # Area of Structure in blade at the root [m2]
    Jy_str  = hr*wr**3/12 - (hr-2*t)*(wr-2*t)**3/12; # Area moment of Inertia y of the structure at the root [m4]

    ## Vector
    Jb_str  = (Jx_str + Jy_str )/2 + (Jx_str - Jy_str )/2 * np.cos(2*theta)
    Jb_tot  = Jb_str + Jb_skin
    EJb     = Jb_tot*str.young
    
    ## Mass
    mass_str  = str.rho_str * A_str;                                # Mass of the structure at the root [kg/m]
    mass_skin = str.rho_str * chord*(2+0.1)*t_skin;                 # Mass of the skin at the root [kg/m]
    mass_foam = str.rho_foam*(chord*0.8*hr-A_str);                # Mass of the foam at the root [kg/m]
    mass_tot = mass_str + mass_skin + mass_foam;                    # Total mass of the blade [kg]

    ## Stress
    mb_hub  = mb_max
    nz_hub  = omega**2 * np.trapezoid(r*mass_tot, r)
    s_mb    = (mb_hub * ((xi - 1)**2) * hr/2) / Jb_tot
    s_nz    =  nz_hub * ((xi - 1)**2) / A_str

    ## FEM
    ne      = 20;       # Number of elements
    nn      = ne+1;     # Number of nodes

    def fthrust(x):
        return (thrustp / lb) * np.ones_like(x)

    mtip = 12/nb
    mu = interp1d(xb, mass_tot, kind='linear', fill_value='extrapolate')
    EJ = interp1d(xb, EJb, kind='linear', fill_value='extrapolate')

    node_cons = np.array([0, 1, 2*nn-1])
    add_mass  = np.array([nn, mtip])

    ## Ms, Ks and Qw
    _, Ks       = get_mass_and_stiffness(mu, EJ, lb, ne)
    # Qw        = calculate_gravity_Q(mu, lb, ne)

    ## ds
    ds = np.zeros(2*nn, dtype=bool)  # Crea un array booleano de False
    ds[0:2*nn:2] = True

    ## Qa and Kn
    Qa = calculate_aerodynamic_Q(fthrust, lb, ne)
    # Kn = calculate_centripetal_Q(mu, omega, rhub, lb, ne)

    # Ms, Ks and Qw constrained
    # Qw =          set_boundaries(Qw, 'Qw', node_cons, add_mass, [], []);
    Ks,_ = set_boundaries(Ks, 'Ks', node_cons, add_mass, np.array([]), np.array([]))
    ds,_ = set_boundaries(ds, 'ds', node_cons, add_mass, np.array([]), np.array([]))

    ## Kn and Qa constrained
    Qa,_ = set_boundaries(Qa , 'Qa', node_cons, add_mass, np.array([]), np.array([]))
    # Kn = set_boundaries(Kn , 'Kn', node_cons, add_mass, np.array([]), np.array([]))

    # y_sd_c, _, _ = get_static_deformation(Ks + Kn, Qw + Qa, ds)
    y_sd_c, _, _ = get_static_deformation(Ks, Qa, ds)

    odd_cons  = node_cons[np.mod(node_cons, 2) == 0]
    # even_cons = node_cons(np.mod(node_cons, 2) == 0)
    n_pos_cons= odd_cons//2


    ds_pos              = np.ones(nn, dtype=bool)
    ds_pos[n_pos_cons]  = False
    y_                  = np.zeros(nn)
    y_[ds_pos]          = y_sd_c.reshape(-1)
    sdy                 = y_

    ## Outputs
    feas    = np.min((sigma_adm - (s_mb + s_nz)) / sigma_adm)
    ytip    = sdy[-1]*1000

    return ytip, feas
def mesh(variables, const, case_folder):


    n_out = 11  # Number of outputs
    error_out = [-1.0] * n_out  # Error output 
    nproc_mesh = id.inputs.nproc_mesh  # Number of processors
    nproc_cfd = id.inputs.nproc_cfd  # Number of processors for CFD solver
    
    gui = id.inputs.gui # Use GUI for meshing and solver
    gui = True
    
    # Meshing

    out_file = f"{case_folder}\\mesh.msh.h5"
    geo_file = f"{case_folder}\\case.pmdb"

    alpha_per = 360.0/variables[id.rnb]
    
    # start meshing
    meshing = pyfluent.launch_fluent(
    precision="double",
    processor_count=nproc_mesh,
    mode="meshing",
    show_gui=gui,
    )
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        mode = 1
        future = executor.submit(make_mesh, meshing, geo_file, out_file, alpha_per, mode, const[id.r])
        try:
            mesh_file = future.result(timeout=600) # Wait for up to 10 minutes
        except Exception as e:
            mode = 2
            try:
                mesh_file = make_mesh(meshing, geo_file, out_file, alpha_per, mode, const[id.r])
            except Exception as e:
                print(f"Error in mesh generation: {e}")
                meshing.exit()
                file = open(rf"{case_folder}\mesh_info.txt", "w")
                file.write(f"0 {mode}\n")
                file.close()
                print("Exiting meshing due to error...")
                return [2 * x for x in error_out]  # Return error output
    
    meshing.exit()

    file = open(rf"{case_folder}\mesh_info.txt", "w")
    file.write(f"1 {mode}\n")
    file.close()

    return mesh_file
def solve(variables, const, case_folder):


    n_out = 11  # Number of outputs
    error_out = [-1.0] * n_out  # Error output 
    nproc_mesh = id.inputs.nproc_mesh  # Number of processors
    nproc_cfd = id.inputs.nproc_cfd  # Number of processors for CFD solver
    
    gui = id.inputs.gui # Use GUI for meshing and solver
    gui = True
    gpu_cfd = id.inputs.gpu_cfd  # Use GPU for CFD solver

    fluent_niter = id.inputs.fluent_niter  # Number of iterations
    fluent_nloops = id.inputs.fluent_nloops  # Number of loops tof thrust convergence

    file = open(f"{case_folder}\\mesh_info.txt","r")
    lines = file.readlines()
    file.close()
    success = int(lines[0].split()[0])
    mode = int(lines[0].split()[1])
    if success == 0:
        print("Meshing failed")
        exit()




    mesh_file = rf"{case_folder}\\mesh.msh.h5"

    solver = pyfluent.launch_fluent(
            precision="double",
            processor_count=nproc_cfd,
            mode="solver",
            version="3d",
            show_gui=gui,
            gpu=gpu_cfd
        )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_solver, solver, variables, const, mesh_file, case_folder, fluent_niter, fluent_nloops, gpu_cfd, mode)
        try:
            T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, OF_out = future.result(timeout=1200) # Wait for up to 20 minutes
        except Exception as e:
            print(f"Error in solver execution: {e}")
            solver.exit()
            return [3 * x for x in error_out]  # Return error output
 
    input("Solver finished. Press Enter to exit...\n") 
    solver.exit()

    return T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, OF_out
def read_params(filename):
    params = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            params[key.strip()] = float(value.strip())

    return params


case_folder = rf"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\OptiSlang\src\TX1500\case2"


try:
    os.makedirs(case_folder, exist_ok=True)
except FileExistsError:
    print(f"Directory '{case_folder}' already exists.")

global_input_file = rf"Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\OptiSlang\src\TX1500\inputs.yaml"

shutil.copy(global_input_file, case_folder)

id = ID()

# main code

variables = id.vmin
const = id.const
custom_inputs = 0

# values to default if not existing yet
if custom_inputs == 1: # custom mode

    print("Using custom inputs")
    blade_count = 13
    #root_cutout = 0.15
    solidity = 0.47
    twist = 45
    theta75 = 40
    air_thick_1 = 15
    air_thick_2 = 10
    air_thick_3 = 10
    air_camber_1 = 6
    air_camber_2 = 6
    air_camber_3 = 4
    AR_1 = 3.5
    AR_2 = 4
    AR_3 = 4
    SW_1 = 0.0
    SW_2 = 0.0
    SW_3 = 0.0

    dout_exp = 1.3
    din_exp = 1.3
    dlength = 1.5
    dwidth = 0.3




    variables[id.rnb] = blade_count
    variables[id.rsolidity] = solidity
    variables[id.rtwist] = twist
    variables[id.rtheta75] = theta75

    variables[id.rair_thick[0]] = air_thick_1
    variables[id.rair_thick[1]] = air_thick_2
    variables[id.rair_thick[2]] = air_thick_3
    variables[id.rair_camber[0]] = air_camber_1
    variables[id.rair_camber[1]] = air_camber_2
    variables[id.rair_camber[2]] = air_camber_3
    variables[id.rtaper[0]] = AR_1
    variables[id.rtaper[1]] = AR_2
    variables[id.rtaper[2]] = AR_3
    variables[id.rsweep[0]] = SW_1
    variables[id.rsweep[1]] = SW_2
    variables[id.rsweep[2]] = SW_3
    variables[id.dout_exp] = dout_exp  # duct outlet expansion ratio
    variables[id.din_exp] = din_exp  # duct inlet expansion ratio
    variables[id.dlength] = dlength  # duct length
    variables[id.dwidth] = dwidth  # duct thickness


blade_count = variables[id.rnb]
root_cutout = variables[id.rcout]
solidity = variables[id.rsolidity]
twist = variables[id.rtwist]    
theta75 = variables[id.rtheta75]
air_thick_1 = variables[id.rair_thick[0]]
air_thick_2 = variables[id.rair_thick[1]]
air_thick_3 = variables[id.rair_thick[2]]
air_camber_1 = variables[id.rair_camber[0]]
air_camber_2 = variables[id.rair_camber[1]]
air_camber_3 = variables[id.rair_camber[2]]
AR_1 = variables[id.rtaper[0]]
AR_2 = variables[id.rtaper[1]]
AR_3 = variables[id.rtaper[2]]
SW_1 = variables[id.rsweep[0]]
SW_2 = variables[id.rsweep[1]]
SW_3 = variables[id.rsweep[2]]
dout_exp = variables[id.dout_exp]  # duct outlet expansion ratio
din_exp = variables[id.din_exp]  # duct inlet expansion ratio
dlength = variables[id.dlength]  # duct length
dwidth = variables[id.dwidth]  # duct thickness



print("Done setting up variables")

#exit()

script_file = run_geo(variables,const,case_folder)

modeler = launch_modeler(mode='discovery')
print(modeler)
result = modeler.run_discovery_script_file(file_path=script_file)

modeler.close()

mesh_file = mesh(variables, const, case_folder)


T_total, T_blade, T_duct, T_hub, Q, omega, P, FM, DL, PL, OF_out = solve(variables, const, case_folder)


# Structural design

rotor = Rotor(variables,const)
crotor = Rotor_structure(variables[id.rnb], variables[id.rcout]*const[id.r], const[id.r], omega*60/(2*np.pi), T_blade)
celem  = Elem(rotor.nr, rotor.r*rotor.R_tip, rotor.theta, rotor.chord)
cstr   = Str(rotor.air_thick[0])

# Code
ytip, feas  = structural_design(crotor, celem, cstr)
print("Tip deflection (mm):", ytip)
OF = OF_out
print("Objective Function:", OF)
omega = omega
duct_share = T_duct/T_total

mesh_file = rf"{case_folder}\\mesh.msh.h5"
try:
    os.remove(mesh_file)
except FileNotFoundError:
    pass
except PermissionError:
    print("File is in use and cannot be deleted.")
    
print("Total Thrust (N):", T_total, "\nBlade Thrust (N):", T_blade, "\nDuct Thrust (N):", T_duct, "\nHub Thrust (N):", T_hub, "\nTorque (Nm):", Q, "\nOmega (rad/s):", omega, "\nPower (W):", P, "\nFigure of Merit:", FM, "\nDisk Loading (kg/m^2):", DL, "\nPower Loading (kg/kW):", PL, "\nObjective Function (W/N):", OF, "\nDuct Share (%):", duct_share*100)

rpm = omega*60/(2*np.pi)

    ## post-process

post_process(rpm, const[id.r], case_folder, rotor.r, rotor.theta)
#omega = 3400*2*np.pi/60  # rad/s
#mean_OASPL, mean_OASPL_A, max_OASPL, max_OASPL_A = run_acoustics(case_folder, omega, rotor.R_tip, rotor.Nb)

max_OASPL_A = 0
mean_OASPL_A = 0

jvar = 0
## Append to file

foutname = rf"{case_folder}\results.csv"

if not os.path.exists(foutname):
    with open(foutname, "w") as f:
        f.write("#,blade_count,root_cutout,solidity,twist,theta75,air_thick_1,air_thick_2,air_thick_3,air_camber_1,air_camber_2,air_camber_3,AR_1,AR_2,AR_3,SW_1,SW_2,SW_3,dout_exp,din_exp,dlength,dwidth,T_total,T_blade,T_duct,T_hub,Q,omega,RPM,P,FM,Ytip,DL,PL,OF,Duct_Share,OASPL_A_max,OASPL_A_mean\n")

while True:
    try:
        with open(foutname, "a") as f:
            f.write(f"{jvar},{blade_count},{root_cutout},{solidity},{twist},{theta75},{air_thick_1},{air_thick_2},{air_thick_3},{air_camber_1},{air_camber_2},{air_camber_3},{AR_1},{AR_2},{AR_3},{SW_1},{SW_2},{SW_3},{variables[id.dout_exp]},{variables[id.din_exp]},{variables[id.dlength]},{variables[id.dwidth]},{T_total},{T_blade},{T_duct},{T_hub},{Q},{omega},{rpm},{P},{FM},{ytip},{DL},{PL},{OF},{duct_share},{max_OASPL_A},{mean_OASPL_A}\n")
        break
    except Exception as e:
        print(f"Error writing to file: {e}")
        input("Close output CSV file and Press Enter to save current varient...\n")




