import yaml

# input class

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

