# Readme for submission to Computer Physics Communications

Detailed instructions of these are in the original [README](README.md) and [HOWTO](tutorials/howto.md). Nevertheless, the basics are all here.

## Installation

Nano-k runs on Python 3.9, and requires the installation of the following Python modules:

- scipy
- matplotlib
- h5py
- trimesh
- shapely
- phonopy
- imageio
- pandas

The proficient user can install them in their environment of choice. In general, it is advised to use conda. A detailed description can be found in the original [README](README.MD) file, which is also on the main page of the [GitHub repository](https://github.com/brunohs1993/Nanokappa).

## Execution

An example parameter file is located in the base directory, called [parameters_test.txt](parameters_test.txt). The user can execute a simulation with:

    python nanokappa.py -ff parameters_test.txt

Detailed explanations for each simulation parameter are in the [HOWTO](tutorials/howto.md) file, also on [GitHub](https://github.com/brunohs1993/Nanokappa/blob/main/tutorials/howto.md).

## Output

If using the sample parameters_test.txt, the results of your simulation will be found in `Nanokappa/test_results/test_0`. They should closely reproduce the overall behaviour found in the figures in `Nanokappa/test_results/sample`, with some random deviations. Convergence plots should show the evolution of relevant quantities over time, and geometry plots should be used to inspect the subvolume distribution, the boundary conditions, energy distribution and thermal conductivity between subvolumes.

Text files include:
- convergence.txt with all simulation information over time;
- particle_data.txt with the final state describing the mode, position and occupation of all particles in the domain at the end of the simulation;
- subvolumes.txt with information about subvolumes at the end;
- subvol_connections.txt (when relevant) with information about temperature gradients, heat fluxes and thermal conductivity between subvolumes.

There are also additional plots such as:
- contribution of frequency to thermal conductivity;
- density of states of the material;
- scattering probability of modes;
- boundary scattering correspondences of velocity, frequency and wavevector, for each unique normal of rough faces.

## Directory Structure

    Nanokappa/
    ├─ classes/
    │  ├─ Constants.py
    │  ├─ Geometry.py
    │  ├─ Mesh.py
    │  ├─ Phonon.py
    │  ├─ Population.py
    │  ├─ Visualisation.py
    ├─ readme_fig/
    │  ├─ logo_black.png
    │  ├─ logo_white.png
    │  ├─ voronoi.png
    ├─ routines/
    │  ├─ geo3d.py
    │  ├─ subvolumes.py
    ├─ set_env/
    │  ├─ modules.txt
    │  ├─ set_env.py
    ├─ test_material/
    │  ├─ kappa-m313131.hdf5
    │  ├─ POSCAR
    ├─ test_results/
    │  ├─ sample/
    │  │  ├─ arguments.txt
    │  │  ├─ BC_plot.png
    │  │  ├─ convergence.txt
    │  │  ├─ convergence_e.png
    │  │  ├─ convergence_en_balance.png
    │  │  ├─ convergence_kappa.png
    │  │  ├─ convergence_Np.png
    │  │  ├─ convergence_phi.png
    │  │  ├─ convergence_T.png
    │  │  ├─ density_of_states.png
    │  │  ├─ fig_energy.png
    │  │  ├─ k_contribution.png
    │  │  ├─ kappa_con.png
    │  │  ├─ particle_data.txt
    │  │  ├─ residue.txt
    │  │  ├─ scattering_prob.png
    │  │  ├─ spec[-0. -0. 1.].png
    │  │  ├─ spec[-0. -0. -1.].png
    │  │  ├─ specular_correspondences.txt
    │  │  ├─ subvol_connections.png
    │  │  ├─ subvolumes.txt
    ├─ tutorials/
    │  ├─ howto.md
    ├─ argument_parser.py
    ├─ LICENSE.md
    ├─ nanokappa.py
    ├─ parameters_test.txt
    ├─ README.md