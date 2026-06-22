import numpy as np
from scipy.interpolate import interp1d



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