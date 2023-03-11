# calculations
import numpy as np
import warnings

# plotting and animation
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
# import matplotlib.cm as cm
# import matplotlib.gridspec as gridspec

# other
import copy

# simulation
from classes.Constants import Constants

warnings.simplefilter(action='ignore', category=FutureWarning)

class Visualisation(Constants):
    def __init__(self, args, geometry, phonon):
        super(Visualisation, self).__init__()
        print('Initialising visualisation class...')

        self.args = args
        self.phonon = phonon
        self.geometry = geometry

        self.folder = self.args.results_folder

        self.convergence_file = self.folder+'convergence.txt'
        self.particle_file    = self.folder+'particle_data.txt'
        self.mode_file        = self.folder+'modes_data.txt'
        self.subvol_file      = self.folder+'subvol_data.txt'

        self.dt         = self.args.timestep[0]

        self.unique_modes = np.stack(np.meshgrid( np.arange(phonon.number_of_qpoints), np.arange(phonon.number_of_branches) ), axis = -1 ).reshape(-1, 2).astype(int)

        self.set_style_dicts()
    
    def set_style_dicts(self):
        
        self.theme = 'light'

        figcolor  = 'whitesmoke'
        facecolor = 'whitesmoke'
        linecolor = 'black'
        gridcolor = 'slategrey'
        textcolor = 'black'

        if self.args.theme[0] == 'dark':
            self.theme = 'dark'

            facecolor = (np.array([29,34,38])/255)*2
            figcolor  = np.array([29,34,38])/255
            linecolor = 'lightsteelblue'
            gridcolor = 'slategrey'
            textcolor = 'lightsteelblue'
        elif self.args.theme[0] not in ['light', 'dark']:
            Warning('Invalid theme. Defaulting to light theme.')

        if self.geometry.subvol_type == 'slice':
            self.profile_plot_style = dict(linestyle   = ':',
                                           color       = linecolor,
                                           marker = 'o',
                                           markersize  = 5,
                                           capsize = 5 )
        else:
            self.profile_plot_style = dict(linestyle   = 'None',
                                           color       = linecolor   ,
                                           marker = 'o'   ,
                                           markersize  = 5    ,
                                           capsize = 5)
        
        self.convergence_plot_style = dict(linestyle = '-')
        
        self.grid_style = dict(ls    = '--'       ,
                               lw    = 1          ,
                               color = gridcolor)
        
        self.ax_style = dict(figcolor = figcolor,
                             facecolor = facecolor,
                             axiscolor = linecolor,
                             textcolor = textcolor)
        
        self.mean_plot_style = dict(linestyle = '--',
                                    color     = linecolor )
        
        self.stdev_plot_style = dict(color     = 'r' ,
                                     linestyle = '--')
        
    def preprocess(self):
        print('Generating preprocessing plots...')
        
        print('Scattering probability...')
        self.scattering_probability()
        print('Density of states...')
        self.density_of_states()

    def postprocess(self, verbose = True):
        # convergence data

        if verbose: print('Reading convergence data')
        self.read_convergence()

        if self.sim_time.shape[0] > 1:
        #     if verbose: print('Plotting convergence...')
            self.plot_convergence_general(property_list = ['e', 'T', 'Np', 'phi', 'kappa'], cmap = None)

        if self.n_of_reservoirs >0 :
            if verbose: print('Plotting energy balance convergence...')
            self.convergence_energy_balance()

        # final particles states
        if self.n_of_reservoirs >0 :
            if verbose: print('Reading particle data...')
            self.read_particles(verbose)
            if self.args.subvolumes[0] == 'slice':
                if verbose: print('Plotting thermal conductivity with frequency...')
                with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                    self.flux_contribution()
        self.plot_kappa_path()

    def scattering_probability(self):
        '''Plots the scattering probability of the maximum temperature (in which scattering mostly occurs)
        and gives information about simulation instability due to de ratio dt/tau.'''

        max_res_T = max([self.geometry.res_values[i] for i, bc in enumerate(self.geometry.res_bound_cond) if bc == 'T'])
        T = max(self.phonon.T_reference, max_res_T)
        
        fig = plt.figure(figsize = (8,8), dpi = 200)
        
        x_data = self.phonon.omega[self.unique_modes[:, 0], self.unique_modes[:, 1]]

        # calculating y data
        ax = fig.add_subplot(111)

        Tqj = np.hstack( ( ( np.ones(self.unique_modes.shape[0])*T).reshape(-1, 1), self.unique_modes ) )
        
        lifetime = self.phonon.lifetime_function(Tqj)

        min_lt = lifetime[lifetime > 0].min()

        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
            scat_prob = np.where(lifetime>0, 1-np.exp(-self.dt/lifetime), 0)

        y_data = scat_prob

        # setting limits and colors based on y data
        min_y = 0
        max_y = 1

        unstable_scat_prob    = 1-np.exp(-2)
        oscillating_scat_prob = 1-np.exp(-1)

        max_dt = -min_lt*np.log(1-unstable_scat_prob)
        max_non_oscil_dt = -min_lt*np.log(1-oscillating_scat_prob)

        unstable_modes = np.where(y_data > unstable_scat_prob, 1, 0).sum()/y_data.shape[0]
        unstable_modes *= 100

        colors = ['royalblue', 'royalblue', 'gold', 'gold', 'crimson', 'crimson']
        nodes  = np.array([0.0, oscillating_scat_prob-0.01, oscillating_scat_prob+0.01, unstable_scat_prob-0.01, unstable_scat_prob+0.01, 1])
        cmap = LinearSegmentedColormap.from_list('byr', list(zip(nodes, colors)))

        ax.scatter(x_data, y_data, s = 1,
                    c = y_data, cmap = cmap,
                    vmin = 0,
                    vmax = 1)
        ax.plot([0, self.phonon.omega.max()], [   unstable_scat_prob,    unstable_scat_prob], color = 'gray', linestyle='--', alpha = 0.5)
        ax.text(x = 0, y = unstable_scat_prob - 0.01,
                s = r'Instability limit - $dt/\tau = 2$',
                va = 'top',
                ha = 'left',
                fontsize = 'large',
                color = 'gray')
        ax.plot([0, self.phonon.omega.max()], [oscillating_scat_prob, oscillating_scat_prob], color = 'gray', linestyle='--', alpha = 0.5)
        ax.text(x = 0, y = oscillating_scat_prob - 0.01,
                s = r'Oscillations limit - $dt/\tau = 1$',
                va = 'top',
                ha = 'left',
                fontsize = 'large',
                color = 'gray')
        
        ax.set_xlabel(r'Angular frequency $\omega$ [rad THz]',
                        fontsize = 'large')
        ax.set_ylabel(r'Scattering probability $P = 1-\exp(-dt/\tau)$',
                        fontsize = 'large')

        ax.set_ylim(min_y, max_y)

        ax.text(x = 0, y = max_y*0.97,
                s = 'T = {:.1f} K\nUnstable modes = {:.2f} %\nMax stable dt = {:.3f} ps\nMax non-oscillatory dt = {:.3f} ps'.format(T, unstable_modes, max_dt, max_non_oscil_dt),
                va = 'top',
                ha = 'left',
                fontsize = 'large',
                linespacing = 1.1)

        fig.suptitle(r'Scattering probability with $dt = ${:.2f} ps'.format(self.dt),
                     fontsize = 'xx-large')

        plt.tight_layout()
        plt.savefig(self.folder+'scattering_prob.png')

        plt.close(fig)

        if np.any(y_data > unstable_scat_prob):
            print('MCPhonon Warning: Timestep is too large! Check scattering probability plot for details.')
        
    def get_lifetime(self, mode, T):
        return self.phonon.lifetime_function[mode[0]][mode[1]](T)

    def density_of_states(self):

        omega = self.phonon.omega[self.unique_modes[:, 0], self.unique_modes[:, 1]]

        n_bins    = 200
        
        d_omega   = omega.max()/n_bins

        intervals = np.arange(0, omega.max()+d_omega, d_omega)
        
        below = (omega.reshape(-1, 1) < intervals)[:, 1:]
        above = (omega.reshape(-1, 1) >= intervals)[:, :-1]
        
        dos = below & above

        dos = dos.sum(axis = 0)
        dos = dos/d_omega

        x_data = intervals[:-1]+d_omega
        y_data = dos

        fig = plt.figure(figsize = (10,8), dpi = 120)
        ax = fig.add_subplot(111)

        # ax.plot(x_data, y_data, color = 'k')
        ax.fill_between(x_data, 0, y_data, facecolor = 'slategray')

        ax.set_ylim(0)

        ax.set_xlabel(r'Angular Frequency $\omega$ [THz]', fontsize = 'x-large')
        ax.set_ylabel(r'Density of states $g(\omega)$ [THz$^{-1}$]', fontsize = 'x-large')

        plt.title(r'Density of states. {:d} bins, $d\omega = $ {:.3f} THz'.format(n_bins, d_omega), fontsize = 'xx-large')

        plt.tight_layout()
        plt.savefig(self.folder+'density_of_states.png')
        plt.close(fig)

    def read_convergence(self):
        f = open(self.convergence_file, 'r')

        lines = f.readlines()

        f.close()

        data = [ i.strip().split(' ') for i in lines]
        data = data[1:]
        data = [ list(filter(None, i)) for i in data]
        data = np.array(data)

        self.n_of_subvols    = self.geometry.n_of_subvols
        self.n_of_reservoirs = self.geometry.n_of_reservoirs
        self.n_of_subvol_con = self.geometry.n_of_subvol_con

        self.datetime = data[:, 0].astype('datetime64[us]')
        self.timestep = data[:, 1].astype(int)
        self.sim_time = data[:, 2].astype(float)
        self.total_en = data[:, 3].astype(float)
        self.en_res   = data[:, 4                                            : 4+  self.n_of_reservoirs                     ].astype(float)
        self.phi_res  = data[:, 4+  self.n_of_reservoirs                     : 4+4*self.n_of_reservoirs                     ].astype(float)
        self.mtm_res  = data[:, 4+4*self.n_of_reservoirs                     : 4+7*self.n_of_reservoirs                     ].astype(float)
        self.N_p      = data[:, 4+7*self.n_of_reservoirs                                                                    ].astype(int  )
        self.T        = data[:, 5+7*self.n_of_reservoirs                     : 5+7*self.n_of_reservoirs+   self.n_of_subvols].astype(float)
        self.sv_en    = data[:, 5+7*self.n_of_reservoirs+   self.n_of_subvols: 5+7*self.n_of_reservoirs+ 2*self.n_of_subvols].astype(float)
        self.sv_phi   = data[:, 5+7*self.n_of_reservoirs+ 2*self.n_of_subvols: 5+7*self.n_of_reservoirs+ 5*self.n_of_subvols].astype(float)
        self.sv_mtm   = data[:, 5+7*self.n_of_reservoirs+ 5*self.n_of_subvols: 5+7*self.n_of_reservoirs+ 8*self.n_of_subvols].astype(float)
        self.sv_Np    = data[:, 5+7*self.n_of_reservoirs+ 8*self.n_of_subvols: 5+7*self.n_of_reservoirs+ 9*self.n_of_subvols].astype(float)
        if self.geometry.subvol_type == 'slice':
            self.sv_k = data[:, 5+7*self.n_of_reservoirs+ 9*self.n_of_subvols: 5+7*self.n_of_reservoirs+10*self.n_of_subvols].astype(float)
            self.k    = data[:, 5+7*self.n_of_reservoirs+10*self.n_of_subvols                                               ].astype(float)
        else:
            self.con_k  = data[:, 5+7*self.n_of_reservoirs+ 9*self.n_of_subvols: 5+7*self.n_of_reservoirs+ 9*self.n_of_subvols+self.n_of_subvol_con].astype(float)

        del(data)

        # mean and stdev
        self.n_mean = int(self.args.n_mean[0])
        N = self.n_mean

        self.mean_total_en = self.total_en[-N:].mean(axis = 0)
        self.mean_en_res   = self.en_res[-N:, :].mean(axis = 0)
        self.mean_phi_res  = self.phi_res[-N:, :].mean(axis = 0)
        self.mean_mtm_res  = self.mtm_res[-N:, :].mean(axis = 0)
        self.mean_Np       = self.N_p[-N:].mean(axis = 0)
        self.mean_T        = self.T[-N:, :].mean(axis = 0)
        self.mean_sv_en    = self.sv_en[-N:, :].mean(axis = 0)
        self.mean_sv_phi   = self.sv_phi[-N:, :].mean(axis = 0)
        self.mean_sv_mtm   = self.sv_mtm[-N:, :].mean(axis = 0)
        self.mean_sv_Np    = self.sv_Np[-N:, :].mean(axis = 0)
        if self.geometry.subvol_type == 'slice':
            self.mean_sv_k  = np.nanmean(self.sv_k[-N:, :], axis = 0)
        else:
            self.mean_con_k  = np.nanmean(self.con_k[-N:, :], axis = 0)
            self.mean_con_dT = np.nanmean(self.T[-N:, self.geometry.subvol_connections[:, 1]] - self.T[-N:, self.geometry.subvol_connections[:, 0]], axis = 0)
            
            self.mean_con_phi = np.zeros(self.geometry.n_of_subvol_con)
            for i, con in enumerate(self.geometry.subvol_connections):
                phi = (self.sv_phi[-N:, 3*con[0]:3*(con[0]+1)] + self.sv_phi[-N:, 3*con[1]:3*(con[1]+1)])/2
                dx  = np.copy(self.geometry.subvol_con_vectors[i, :])
                dx /= np.linalg.norm(dx)
                self.mean_con_phi[i] = np.nanmean(np.sum(phi*dx, axis = 1))

        self.std_total_en = self.total_en[-N:].std(axis = 0)
        self.std_en_res   = self.en_res[-N:, :].std(axis = 0)
        self.std_phi_res  = self.phi_res[-N:, :].std(axis = 0)
        self.std_mtm_res  = self.mtm_res[-N:, :].std(axis = 0)
        self.std_Np       = self.N_p[-N:].std(axis = 0)
        self.std_T        = self.T[-N:, :].std(axis = 0)
        self.std_sv_en    = self.sv_en[-N:, :].std(axis = 0)
        self.std_sv_phi   = self.sv_phi[-N:, :].std(axis = 0)
        self.std_sv_mtm   = self.sv_mtm[-N:, :].std(axis = 0)
        self.std_sv_Np    = self.sv_Np[-N:, :].std(axis = 0)
        if self.geometry.subvol_type == 'slice':
            self.std_sv_k  = np.nanstd(self.sv_k[-N:, :], axis = 0)
        else:
            self.std_con_k = np.nanstd(self.con_k[-N:, :], axis = 0)
            self.std_con_dT = np.nanstd(self.T[-N:, self.geometry.subvol_connections[:, 1]] - self.T[-N:, self.geometry.subvol_connections[:, 0]], axis = 0)
            
            self.std_con_phi = np.zeros(self.geometry.n_of_subvol_con)
            for i, con in enumerate(self.geometry.subvol_connections):
                phi = (self.sv_phi[-N:, 3*con[0]:3*(con[0]+1)] + self.sv_phi[-N:, 3*con[1]:3*(con[1]+1)])/2
                dx  = np.copy(self.geometry.subvol_con_vectors[i, :])
                dx /= np.linalg.norm(dx)
                self.std_con_phi[i] = np.nanstd(np.sum(phi*dx, axis = 1))

        if self.geometry.subvol_type != 'slice':
            i = np.absolute(self.mean_con_k) < self.std_con_k
            self.mean_con_k[i] = np.nan
            self.std_con_k[i]  = np.nan

    def read_particles(self, verbose = True):

        data = np.loadtxt(self.particle_file, delimiter = ',')

        if verbose: print('Finished reading particle data')

        if data.shape[0] > 0:
            self.q_point    = data[:, 0].astype(int)
            self.branch     = data[:, 1].astype(int)
            self.position   = data[:, 2:5].astype(float)
            self.occupation = data[:, 5].astype(float)
        else:
            self.q_point    = np.zeros(0).astype(int)
            self.branch     = np.zeros(0).astype(int)
            self.position   = np.zeros((0, 3))
            self.occupation = np.zeros(0)

        del(data)

    def read_subvols(self):
        print('Reading subvol data')
        
        data           = np.loadtxt(self.subvol_file, delimiter = ',')
        self.sv_center = data[:, 1:4]
        self.sv_vol    = data[:, 4]

        del(data)
    
    def adjust_style_dict(self, plot, dict):
        if plot == 'profile':
            a = copy.copy(self.profile_plot_style)
        elif plot == 'convergence':
            a = copy.copy(self.convergence_plot_style)
        elif plot == 'grid':
            a = copy.copy(self.grid_style)
        elif plot == 'mean':
            a = copy.copy(self.mean_plot_style)
        elif plot == 'stdev':
            a = copy.copy(self.stdev_plot_style)
        
        if dict is None:
            return a
        else:
            for k in dict.keys():
                a[k] = dict[k]
            return a

    def plot_convergence_general(self, property_list = [], cmap = None, conv_dict = None, prof_dict = None, grid_dict = None, mean_dict = None, stdev_dict = None):
        
        # adjust style dict
        conv_dict  = self.adjust_style_dict('convergence', conv_dict )
        prof_dict  = self.adjust_style_dict('profile'    , prof_dict )
        grid_dict  = self.adjust_style_dict('grid'       , grid_dict )
        mean_dict  = self.adjust_style_dict('mean'       , mean_dict )
        stdev_dict = self.adjust_style_dict('stdev'      , stdev_dict)

        # setting colormaps
        if cmap is not None:
            cmap = matplotlib.colormaps[cmap]

        for prop in property_list:
            # defining data
            if prop in ['temperature', 'T']:
                data             = self.T
                n_plot           = data.shape[1]
                mean_prof        = self.mean_T
                std_prof         = self.std_T
                filename         = 'convergence_T'
                suptitle         = r'Temperatures for each subvolume: evolution over time and local $\mu$ and $\sigma$.'
                ylabel           = ['Local T [K]']
                nrows            = 1
                sharey           = True
                sharex           = False
                prof_x           = np.arange(self.geometry.n_of_subvols)
                prof_xlabel      = 'Subvolume'
                prof_xticks      = np.arange(self.geometry.n_of_subvols)
                prof_xticklabels = np.arange(self.geometry.n_of_subvols, dtype = int)
                conv_labels      = ['Sv {:d}'.format(i) for i in np.arange(self.geometry.n_of_subvols, dtype = int)]
            elif prop in ['flux', 'phi']:
                data             = self.sv_phi
                n_plot           = int(data.shape[1]/3)
                mean_prof        = self.mean_sv_phi
                std_prof         = self.std_sv_phi
                filename         = 'convergence_phi'
                suptitle         = r'Heat flux for each subvolume: evolution over time and local $\mu$ and $\sigma$.'
                ylabel           = [r'Local $\phi_{{{}}}$ [W/m²]'.format(i) for i in ['x', 'y', 'z']]
                nrows            = 3
                sharey           = 'all'
                sharex           = 'col'
                prof_x           = np.arange(self.geometry.n_of_subvols)
                prof_xlabel      = 'Subvolume'
                prof_xticks      = np.arange(self.geometry.n_of_subvols)
                prof_xticklabels = np.arange(self.geometry.n_of_subvols, dtype = int)
                conv_labels      = ['Sv {:d}'.format(i) for i in np.arange(self.geometry.n_of_subvols, dtype = int)]
            elif prop in ['particles', 'Np']:
                data             = self.sv_Np
                n_plot           = data.shape[1]
                mean_prof        = self.mean_sv_Np
                std_prof         = self.std_sv_Np
                filename         = 'convergence_Np'
                suptitle         = r'Number of particles for each subvolume: evolution over time and local $\mu$ and $\sigma$.'
                ylabel           = [r'$N_p$ [-]']
                nrows            = 1
                sharey           = True
                sharex           = False
                prof_x           = np.arange(self.geometry.n_of_subvols)
                prof_xlabel      = 'Subvolume'
                prof_xticks      = np.arange(self.geometry.n_of_subvols)
                prof_xticklabels = np.arange(self.geometry.n_of_subvols, dtype = int)
                conv_labels      = ['Sv {:d}'.format(i) for i in np.arange(self.geometry.n_of_subvols, dtype = int)]
            elif prop in ['energy', 'e']:
                data             = self.sv_en
                n_plot           = data.shape[1]
                mean_prof        = self.mean_sv_en
                std_prof         = self.std_sv_en
                filename         = 'convergence_e'
                suptitle         = r'Energy density for each subvolume: evolution over time and local $\mu$ and $\sigma$.'
                ylabel           = [r'Local $e$ [eV/$\AA^3$]']
                nrows            = 1
                sharey           = True
                sharex           = False
                prof_x           = np.arange(self.geometry.n_of_subvols)
                prof_xlabel      = 'Subvolume'
                prof_xticks      = np.arange(self.geometry.n_of_subvols)
                prof_xticklabels = np.arange(self.geometry.n_of_subvols, dtype = int)
                conv_labels      = ['Sv {:d}'.format(i) for i in np.arange(self.geometry.n_of_subvols, dtype = int)]
            elif prop in ['conductivity', 'kappa']:
                filename  = 'convergence_kappa'
                suptitle  = r'Thermal conductivity: evolution over time and local $\mu$ and $\sigma$.'
                if self.geometry.subvol_type == 'slice':
                    data             = self.sv_k
                    data_total       = self.k
                    n_plot           = data.shape[1]
                    mean_prof        = self.mean_sv_k
                    std_prof         = self.std_sv_k
                    ylabel           = [r'{} $\kappa$ [W/m$\cdot$K]'.format(i) for i in ['Local', 'Total']]
                    nrows            = 2
                    sharey           = 'all'
                    sharex           = False
                    prof_x           = np.arange(self.geometry.n_of_subvols)
                    prof_xlabel      = 'Subvolume'
                    prof_xticks      = np.arange(self.geometry.n_of_subvols)
                    prof_xticklabels = np.arange(self.geometry.n_of_subvols, dtype = int)
                    conv_labels      = ['Sv {:d}'.format(i) for i in np.arange(self.geometry.n_of_subvols, dtype = int)]
                else:
                    data             = self.con_k*np.where(np.isnan(self.mean_con_k), np.nan, 1)
                    n_plot           = data.shape[1]
                    mean_prof        = self.mean_con_k
                    std_prof         = self.std_con_k
                    ylabel           = [r'Local $\kappa$ [W/m$\cdot$K]']
                    nrows            = 1
                    sharey           = True
                    sharex           = False
                    prof_x           = np.arange(self.geometry.n_of_subvol_con)
                    prof_xlabel      = 'Connection'
                    prof_xticks      = np.arange(self.geometry.n_of_subvol_con)
                    prof_xticklabels = ['{:d}-{:d}'.format(i[0], i[1]) for i in self.geometry.subvol_connections]
                    conv_labels      = ['Con {:d}-{:d}'.format(i[0], i[1]) for i in self.geometry.subvol_connections]
                                    
            # parameters in common for all figures
            dpi         = 200 # resolution in dots per inch
            cell_length = 5   # the standard size is cell_length*1.5*ncols, cell_length*nrows
            ncols       = 2
            conv_x = self.sim_time
            conv_xlabel = 'Time [ps]'

            if len(conv_labels) > 20 and len(conv_labels) <= 30:
                legend_fontsize = 'small'
                prof_xtick_fontdict = {'fontsize': 'small', 'rotation':45}
            elif len(conv_labels) > 30:
                legend_fontsize = 'x-small'
                prof_xtick_fontdict = {'fontsize': 'x-small', 'rotation':90}
            else:
                legend_fontsize = 'medium'
                prof_xtick_fontdict = {'fontsize': 'medium', 'rotation':0}

            # generate axes and figure
            if nrows == 2:
                fig, ax = plt.subplot_mosaic([['left', 'right'],['bottom', 'bottom']], sharey = True,
                                             dpi     = dpi  ,
                                             figsize = (ncols*1.5*cell_length, nrows*cell_length))
            else:
                fig, ax = plt.subplots(nrows   = nrows,
                                       ncols   = ncols,
                                       dpi     = dpi  ,
                                       figsize = (ncols*1.5*cell_length, nrows*cell_length),
                                       sharey  = sharey,
                                       sharex  = sharex)

            if cmap is not None:
                if nrows == 1:
                    n_lines = data.shape[1]
                    ax[0].set_prop_cycle(plt.cycler('color', cmap(np.linspace(0, 1, n_lines))))
                elif nrows == 2:
                    n_lines = data.shape[1]
                    ax['left'].set_prop_cycle(plt.cycler('color', cmap(np.linspace(0, 1, n_lines))))
                else:
                    n_lines = int(data.shape[1]/3) # dimensional data
                    for a in ax[:, 0]:
                        a.set_prop_cycle(plt.cycler('color', cmap(np.linspace(0, 1, n_lines))))

            # plotting data:
            if nrows == 3:
                for d in range(3):
                    for i in range(n_plot):
                        ax[d, 0].plot(conv_x, data[:, 3*i+d], **conv_dict)
                        ax[d, 0].set_ylabel(ylabel[d])
                    ax[d, 1].errorbar(prof_x, mean_prof[np.arange(n_plot)*3+d], yerr = std_prof[np.arange(n_plot)*3+d], **prof_dict)
                ax[-1, 0].set_xlabel(conv_xlabel)
                ax[-1, 1].set_xlabel(prof_xlabel)
                ax[-1, 1].set_xticks(prof_xticks)
                ax[-1, 1].set_xticklabels(prof_xticklabels, fontdict = prof_xtick_fontdict)
                if len(conv_labels) <= 70:
                    for a in ax[:, 0]:
                        a.legend(conv_labels, ncols = 1+len(conv_labels)//10,
                                fontsize = legend_fontsize,
                                facecolor = self.ax_style['facecolor'],
                                edgecolor = self.ax_style['axiscolor'],
                                labelcolor = self.ax_style['textcolor'])
                
            elif nrows == 2:
                for i in range(n_plot):
                    ax['left'].plot(conv_x, data[:, i], **conv_dict)
                ax['right'].errorbar(prof_x, mean_prof, yerr = std_prof, **prof_dict)
                ax['bottom'].plot(conv_x, data_total, **conv_dict)

                N = int(self.args.n_mean[0])
                rol_mean = np.convolve(data_total                , np.ones(N)/N, mode = 'full')[:-N+1]
                rol_std  = (np.convolve((data_total - rol_mean)**2, np.ones(N)/N, mode = 'full')[:-N+1])**0.5
                
                ax['bottom'].plot(conv_x, rol_mean, **mean_dict )
                ax['bottom'].plot(conv_x, rol_std , **stdev_dict)
                if len(conv_labels) <= 70:
                    ax['left'].legend(conv_labels, ncols = 1+len(conv_labels)//10, fontsize = legend_fontsize,
                                    facecolor = self.ax_style['facecolor'],
                                    edgecolor = self.ax_style['axiscolor'],
                                    labelcolor = self.ax_style['textcolor'])
                ax['left'].set_xlabel(conv_xlabel)
                ax['left'].set_ylabel(ylabel[0])

                ax['right'].set_xticks(prof_xticks)
                ax['right'].set_xlabel(prof_xlabel)
                ax['right'].set_xticklabels(prof_xticklabels, fontdict = prof_xtick_fontdict)

                ax['bottom'].legend(['Instantaneous', r'Rolling $\mu$ ({} datapoints)'.format(N), r'Rolling $\sigma$ ({} datapoints)'.format(N)],
                                    facecolor = self.ax_style['facecolor'],
                                    edgecolor = self.ax_style['axiscolor'],
                                    labelcolor = self.ax_style['textcolor'])
                ax['bottom'].set_xlabel(conv_xlabel)
                ax['bottom'].set_ylabel(ylabel[1])

                text_y = min(0, np.nanmin(mean_prof)*1.5) + (max(0, np.nanmax(mean_prof)*1.5) - min(0, np.nanmin(mean_prof)*1.5))*0.75
                props = dict(boxstyle='round', facecolor='white', alpha=0.5)
                
                ax['bottom'].text(conv_x[-1], text_y,
                                  r'$\kappa$ = {:.2f}$\pm${:.2f} W/m$\cdot$K'.format(rol_mean[-1], rol_std[-1]),
                                  ha = 'right', bbox = props)
                
            else:
                for i in range(n_plot):
                    ax[0].plot(conv_x, data[:, i], **conv_dict)
                ax[0].set_xlabel(conv_xlabel)
                ax[0].set_ylabel(ylabel[0])

                ax[1].errorbar(prof_x, mean_prof, yerr = std_prof, **prof_dict)
                ax[1].set_xlabel(prof_xlabel)
                ax[1].set_xticks(prof_xticks)
                ax[1].set_xticklabels(prof_xticklabels, fontdict = prof_xtick_fontdict)

                ax[0].set_xlabel(conv_xlabel)
                if len(conv_labels) <= 70:
                    ax[0].legend(conv_labels, ncols = 1+len(conv_labels)//10,
                                fontsize = legend_fontsize,
                                facecolor = self.ax_style['facecolor'],
                                edgecolor = self.ax_style['axiscolor'],
                                labelcolor = self.ax_style['textcolor'])
            
            if prop in ['kappa', 'conductivity']:
                y_max = max(0, 1.5*np.nanmax(mean_prof))
                y_min = min(0, 1.5*np.nanmin(mean_prof))
                if type(ax) == dict:
                    for key in ax.keys():
                        ax[key].set_ylim(y_min, y_max)
                else:
                    ax.ravel()[0].set_ylim(y_min, y_max)
            
            if type(ax) == dict:
                for key in ax.keys():
                    ax[key].grid(True, **grid_dict)
                    ax[key].ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,3), useOffset = False)
            else:
                for a in ax.ravel():
                    a.grid(True, **grid_dict)
                    a.ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,3), useOffset = False)
            
            if type(ax) == dict:
                for a in ax:
                    ax[a].set_facecolor(self.ax_style['facecolor'])
                    fig.patch.set_facecolor(self.ax_style['figcolor'])

                    for s in ax[a].spines:
                        ax[a].spines[s].set_color(self.ax_style['axiscolor'])
                    
                    ax[a].xaxis.label.set_color(self.ax_style['textcolor'])
                    ax[a].yaxis.label.set_color(self.ax_style['textcolor'])
                    ax[a].tick_params(axis='both', colors=self.ax_style['axiscolor'])

            else:
                for a in ax.ravel():
                    a.set_facecolor(self.ax_style['facecolor'])
                    fig.patch.set_facecolor(self.ax_style['figcolor'])

                    for s in a.spines:
                        a.spines[s].set_color(self.ax_style['axiscolor'])
                    
                    a.xaxis.label.set_color(self.ax_style['textcolor'])
                    a.yaxis.label.set_color(self.ax_style['textcolor'])
                    a.tick_params(axis='both', colors=self.ax_style['axiscolor'])

            plt.suptitle(suptitle, fontsize = 'xx-large', color = self.ax_style['textcolor']) # figure title
            plt.tight_layout() # pack everything
            plt.savefig(self.folder + filename) # save figure
            plt.close(fig)

    def flux_contribution(self):
        
        # particle data
        omega    = self.phonon.omega[self.q_point, self.branch]
        velocity = self.phonon.group_vel[self.q_point, self.branch, self.geometry.slice_axis]
        occupation = self.occupation
        slice_id = self.geometry.subvol_classifier.predict(self.position)
        
        n = self.n_mean
        slice_res_T = np.zeros(self.n_of_subvols+2)
        slice_res_T[ 0]   = self.geometry.res_values[0]   # THIS IS A PLACEHOLDER. CORRECT LATER FOR THE GENERAL CASE
        slice_res_T[1:-1] = self.T[-n:, :].mean(axis = 0)
        slice_res_T[-1]   = self.geometry.res_values[1]

        subvol_Np = self.sv_Np[-n:, :].mean(axis = 0)

        # calculating contributions
        mode_flux = self.phonon.normalise_to_density(self.hbar*occupation*omega*velocity) # eV/ps a² - (SV, Q, J)

        mode_flux = mode_flux*self.eVpsa2_in_Wm2                        # W/m² - (SV, Q, J)

        dX = 2*self.geometry.slice_length*self.a_in_m                   # m

        dT = slice_res_T[2:] - slice_res_T[:-2]  # K

        dT = dT[slice_id]
        
        mode_k = mode_flux*(-dX/dT) # (W/m²) * (m/K) = W/m K ; Central difference --> [T(+1) - T(-1)]/[x(+1) - x(-1)] - - (SV, Q, J)

        # flux considering all the domain
        dX_total = self.geometry.slice_length*(self.n_of_subvols-1)*self.a_in_m # m
        dT_total = slice_res_T[-1] - slice_res_T[0]                             # K

        mode_k_total = mode_flux*(-dX_total/dT_total) # W/m² - (Q, J)
        
        # defining bins

        n_bins = 100

        step = self.phonon.omega.max()/(n_bins-1)

        omega_bins = np.linspace(0-step/2, self.phonon.omega.max()+step/2, n_bins+1)
        omega_center = (omega_bins[:-1] + omega_bins[1:])/2

        # generating figure

        fig, ax = plt.subplots(nrows = 2, ncols = 1, figsize = (15, 20), dpi = 100, sharex = 'all')

        k_omega = np.zeros((self.n_of_subvols, n_bins))
        k_omega_total = np.zeros(n_bins)

        for b in range(n_bins):
        
            bin_mask = (omega >= omega_bins[b]) & (omega < omega_bins[b+1]) # identifying omega bin - (Q, J,)

            k_omega_total[b] = mode_k[bin_mask].sum()*self.phonon.number_of_modes/subvol_Np.sum()
        
            for sv in range(self.n_of_subvols):
                i = (slice_id == sv) & bin_mask
                k_omega[sv, b] = mode_k[i].sum()*self.phonon.number_of_modes/subvol_Np[sv]
                
        for sv in range(self.n_of_subvols):
            
            ax[0].plot(omega_center, k_omega[sv, :], alpha = 0.5, linewidth = 3)
            ax[1].plot(omega_center, np.cumsum(k_omega[sv, :]), alpha = 0.5, linewidth = 3)
        
        ax[0].plot(omega_center, k_omega_total           , color = 'k', linestyle = '--')
        ax[1].plot(omega_center, np.cumsum(k_omega_total), color = 'k', linestyle = '--')
        
        labels = ['Slice {:d}'.format(i+1) for i in range(self.n_of_subvols)]
        labels += ['Domain']
        if len(labels) < 25:
            ax[0].legend(labels, fontsize = 'x-large')
        ax[0].set_xlabel(r'Angular Frequency $\omega$ [rad THz]', fontsize = 'x-large')
        ax[0].set_ylabel(r'Thermal conductivity in band $k(\omega)$ [W/mK]', fontsize = 'x-large')

        ax[0].ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,0), useOffset = False)
        ax[0].ticklabel_format(axis = 'x', useOffset = False)

        if len(labels) < 25:
            ax[1].legend(labels, fontsize = 'x-large')
        ax[1].set_xlabel(r'Angular Frequency $\omega$ [rad THz]', fontsize = 'x-large')
        ax[1].set_ylabel(r'Cumulated Thermal conductivity in band $k(\omega)$ [W/mK]', fontsize = 'x-large')

        ax[1].ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,0), useOffset = False)
        ax[1].ticklabel_format(axis = 'x', useOffset = False)

        text_x = ax[1].get_xlim()[1]-np.array(ax[1].get_xlim()).ptp()*0.05
        text_y = ax[1].get_ylim()[0]+np.array(ax[1].get_ylim()).ptp()*0.05

        ax[1].text(text_x, text_y, r'$\kappa$ = {:.3e} W/mK'.format(k_omega_total.sum()),
                 verticalalignment   = 'bottom',
                 horizontalalignment = 'right',
                 fontsize = 'xx-large')
        
        for a in ax:
            a.tick_params(axis = 'both', labelsize = 'x-large')
            a.grid(True)
        
        plt.suptitle('Contribution of each frequency band to thermal conductivity. {:d} bands.'.format(n_bins), fontsize = 'xx-large')

        plt.tight_layout(pad = 3)
        plt.savefig(self.folder + 'k_contribution.png')

        plt.close(fig)

    def convergence_energy_balance(self):
        fig = plt.figure( figsize = (15, 5) )
        x_axis = self.sim_time

        ax1 = fig.add_subplot(121)

        # Energy balance
        y_axis = self.en_res
        
        ax1.plot(x_axis, y_axis)
        ax1.plot(x_axis, y_axis.sum(axis = 1), linestyle = '--', color = 'k')
        
        ax1.set_xlabel('Simulation time [ps]', fontsize = 12)
        ax1.set_ylabel('Energy balance on surface [eV]', fontsize = 12)
        
        labels = ['Surface {}'.format(i+1) for i in range(self.n_of_reservoirs)]
        labels.append('Balance')

        if self.n_of_reservoirs <=10:
            ax1.legend(labels)

        ax1.grid(True, ls = '--', lw = 1, color = 'slategray')

        ax1.ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,0), useOffset = False)

        ax2 = fig.add_subplot(122)

        # Flux balance
        y_axis = self.phi_res
        for i in range(self.n_of_reservoirs*3):
            ax2.plot(x_axis, y_axis[:, i])
        
        # line = ['--', ':', '-.']
        # for d in range(3):
        #     i = np.arange(self.n_of_reservoirs)*3+d
        #     ax2.plot(x_axis, np.sum(y_axis[:, i], axis = 1), linestyle = line[d], color = 'k')
        
        ax2.set_xlabel('Simulation time [ps]', fontsize = 12)
        ax2.set_ylabel('Heat flux balance on surface [W/m²]', fontsize = 12)
        
        phi_labels = [r'$\phi_{}$, Res {}'.format(a, r) for r in range(self.n_of_reservoirs) for a in ['x', 'y', 'z']]
        # phi_labels += ['Balance {}'.format(d) for d in ['x', 'y', 'z']]

        if self.n_of_reservoirs <=10:
            ax2.legend(phi_labels)

        ax2.grid(True, ls = '--', lw = 1, color = 'slategray')

        ax2.ticklabel_format(axis = 'y', style = 'sci', scilimits=(0,0), useOffset = False)

        plt.suptitle('Energy and Heat Flux balance over time.', fontsize = 'xx-large')

        plt.tight_layout()
        plt.savefig(self.folder+'convergence_en_balance.png')

        plt.close(fig)

    def plot_kappa_path(self):
        
        fig, ax = self.geometry.plot_facet_boundaries(self.geometry.mesh)
        
        cmap = matplotlib.colormaps['jet']

        if self.geometry.subvol_type == 'slice':
            k = (self.mean_sv_k[self.geometry.subvol_connections[:, 0]] + 
                 self.mean_sv_k[self.geometry.subvol_connections[:, 1]])/2
        else:
            k = np.copy(self.mean_con_k)
        
        min_k = np.floor(np.nanmin(k)/10)*10
        max_k = np.ceil(np.nanmax(k)/10)*10
        
        norm_k = (k - min_k)/(max_k - min_k)

        colors = cmap(norm_k)

        for i, con in enumerate(self.geometry.subvol_connections):
            if k[i] != np.nan:
                ax.plot(self.geometry.subvol_center[con, 0],
                        self.geometry.subvol_center[con, 1],
                        self.geometry.subvol_center[con, 2],
                        color = colors[i],
                        linewidth = 5)

        # divider = make_axes_locatable(plt.gca())
        # cax = divider.append_axes("bottom", "5%", pad="3%")
        # norm = matplotlib.colors.Normalize(vmin=np.nanmin(k), vmax=np.nanmax(k))

        norm = matplotlib.colors.Normalize(vmin=min_k, vmax=max_k)
        cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap),
                     ax = ax,
                     location = 'bottom',
                     orientation = 'horizontal',
                     fraction = 0.05,
                     aspect = 30,
                     shrink = 0.8,
                     pad = -0.1)
        
        cb.set_label(label = 'Thermal Conductivity [W/mK]', size = 'small')

        ticks = ['{:.1f}'.format(i) for i in np.arange(6)/5*(max_k - min_k)+min_k]
        cb.set_ticks([float(i) for i in ticks])
        cb.set_ticklabels(ticks, size = 'small')
        
        plt.tight_layout()
        # plt.show()
        plt.savefig(self.folder + 'kappa_con.png')
        plt.close(fig)




