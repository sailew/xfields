import matplotlib.pyplot as plt
import numpy as np
import time
from scipy.constants import c, e, m_p
from scipy.constants import e as qe
from numpy.fft import fft, ifft

from PyHEADTAIL.particles.slicing import UniformBinSlicer as PyHTUniformBinSlicer
from PyHEADTAIL.particles.particles import Particles as PyHTParticles
from PyHEADTAIL.impedances.wakes import CircularResonator as PyHTCircularResonator

from PyHEADTAIL.impedances.wakes import WakeField as PyHTWakeField
from PyHEADTAIL.machines.synchrotron import Synchrotron as PyHTSynchrotron

import xfields as xf
import xtrack as xt

# Machine settings

n_turns_wake = 3
flatten = False

n_macroparticles = 100000 # per bunch
intensity = 2.3e11

alpha = 53.86**-2

p0 = 7000e9 * e / c

accQ_x = 0.31
accQ_y = 0.32
Q_s = 2.1e-3
chroma = 0

h_RF = 600
bunch_spacing_buckets = 5
n_bunches = 12
n_slices = 250
plot_on = True

# h_RF = 20
# bunch_spacing_buckets = 5
# n_bunches = 4
# n_slices = 100
# plot_on = True

# h_RF = 20 * 20
# bunch_spacing_buckets = 5
# n_bunches = 4 * 20
# n_slices = 100
# plot_on = True

beta_x = 100 #circumference / (2.*np.pi*accQ_x)
beta_y = 100 #circumference / (2.*np.pi*accQ_y)

h_bunch = h_RF
circumference = 26658.883 / 35640 * h_RF

epsn_x = 2e-6
epsn_y = 2e-6
sigma_z = 0.09

machine = PyHTSynchrotron(
        optics_mode='smooth', circumference=circumference,
        n_segments=1, s=None, name=None,
        alpha_x=None, beta_x=beta_x, D_x=0,
        alpha_y=None, beta_y=beta_y, D_y=0,
        accQ_x=accQ_x, accQ_y=accQ_y, Qp_x=chroma, Qp_y=chroma,
        app_x=0, app_y=0, app_xy=0,
        alpha_mom_compaction=alpha, longitudinal_mode='linear',
        h_RF=np.atleast_1d(h_RF), p0=p0,
        charge=e, mass=m_p, wrap_z=False, Q_s=Q_s)

transverse_map = machine.transverse_map.segment_maps[0]

# Filling scheme

filling_scheme = [i*bunch_spacing_buckets for i in range(n_bunches)]

# Initialise beam
allbunches = machine.generate_6D_Gaussian_bunch(n_macroparticles, intensity,
                                                epsn_x, epsn_y, sigma_z=sigma_z,
                                                filling_scheme=filling_scheme,
                                                matched=False)

bucket_id_set = list(set(allbunches.bucket_id))
bucket_id_set.sort()

bucket_length = machine.circumference / h_RF
z_all = -allbunches.bucket_id * bucket_length + allbunches.z

amplitude = 1e-3
wavelength = 2
allbunches.x = amplitude * np.sin(2 * np.pi * z_all / wavelength)
allbunches.xp *= 0

# allbunches.x[z_all < 0] = 0

for b_id in bucket_id_set:
    mask = allbunches.bucket_id == b_id
    z_centroid = np.mean(allbunches.z[mask])
    z_std = np.std(allbunches.z[mask])
    mask_tails = mask & (np.abs(allbunches.z - z_centroid) > z_std)
    allbunches.x[mask_tails] = 0
    # if b_id != 0:
    #     allbunches.x[mask] = 0

beam = PyHTParticles(macroparticlenumber=allbunches.macroparticlenumber,
                 particlenumber_per_mp=allbunches.particlenumber_per_mp,
                 charge=allbunches.charge, mass=allbunches.mass,
                 circumference=allbunches.circumference, gamma=allbunches.gamma,
                 coords_n_momenta_dict=dict(x=allbunches.x.copy(),
                                            y=allbunches.y.copy(),
                                            xp=allbunches.xp.copy(),
                                            yp=allbunches.yp.copy(),
                                            z=z_all.copy(),
                                            dp=allbunches.dp.copy(),
                 ))

# Initialise wakes
slicer = PyHTUniformBinSlicer(n_slices, z_cuts=(-0.5*bucket_length, 0.5*bucket_length),
                          circumference=machine.circumference, h_bunch=h_bunch)



# pipe radius [m]
b = 13.2e-3
# length of the pipe [m]
L = 100000.
# conductivity of the pipe 1/[Ohm m]
sigma = 1. / 7.88e-10

# wakes = CircularResistiveWall(b, L, sigma, b/c, beta_beam=machine.beta)
wakes = PyHTCircularResonator(R_shunt=135e6, frequency=1.97e9*0.6, Q=31000/100, n_turns_wake=n_turns_wake)

# mpi_settings = 'circular_mpi_full_ring_fft'
# wake_field = WakeField(slicer, wakes, mpi=mpi_settings, Q_x=accQ_x, Q_y=accQ_y, beta_x=beta_x, beta_y=beta_y)

R_s = wakes.R_shunt
Q = wakes.Q
f_r = wakes.frequency
omega_r = 2 * np.pi * f_r
alpha_t = omega_r / (2 * Q)
omega_bar = np.sqrt(omega_r**2 - alpha_t**2)
p0_SI = machine.p0


mpi_settings = False
mpi_settings = 'memory_optimized'
mpi_settings = 'linear_mpi_full_ring_fft'
wake_field = PyHTWakeField(slicer, wakes, mpi=mpi_settings)

# Wake full beam

n_buckets_slicer = max(filling_scheme) + 2
n_buckets_slicer = max(filling_scheme) + 1

slicer_full_beam = PyHTUniformBinSlicer(n_buckets_slicer * slicer.n_slices,
                                    z_cuts=((0.5 - n_buckets_slicer)*bucket_length, 0.5*bucket_length),
                                    circumference=machine.circumference, h_bunch=h_bunch)
slicer_full_beam.force_absolute = True

wakes_full_beam = PyHTCircularResonator(R_shunt=wakes.R_shunt, frequency=wakes.frequency, Q=wakes.Q, n_turns_wake=wakes.n_turns_wake)
wake_field_full_beam = PyHTWakeField(slicer_full_beam, wakes_full_beam, mpi=False)


plt.close('all')

if plot_on:
    fig0, (ax00, ax01) = plt.subplots(2, 1)
    ax01.sharex(ax00)

    skip = 10
    ax00.plot(z_all[::skip], allbunches.x[::skip], '.')
    ax00.plot(beam.z[::skip], beam.x[::skip], '.')

x_at_wake_allbunches = []
xp_before_wake_allbunches = []
xp_after_wake_allbunches = []
slice_set_before_wake_allbunches = []
slice_set_after_wake_allbunches = []

x_at_wake_beam = []
xp_before_wake_beam = []
xp_after_wake_beam = []
slice_set_before_wake_beam = []
slice_set_after_wake_beam = []

n_turns = n_turns_wake
store_charge_per_mp = allbunches.charge_per_mp
store_particlenumber_per_mp = allbunches.particlenumber_per_mp

z_source_matrix_multiturn = np.zeros((n_bunches, n_slices, n_turns))
dipole_moment_matrix_multiturn = np.zeros((n_bunches, n_slices, n_turns))

from wakefield import Wakefield, TempResonatorFunction

wf = Wakefield(
    source_moments=['num_particles', 'x', 'y'],
    kick='px',
    scale_kick=None, # The kick is scaled by position of the particle for quadrupolar, would be None for dipolar
    function=TempResonatorFunction(R_shunt=wakes.R_shunt, frequency=wakes.frequency, Q=wakes.Q),
    zeta_range=(-0.5*bucket_length, 0.5*bucket_length), # These are [a, b] in the paper
    num_slices=n_slices, # Per bunch, this is N_1 in the paper
    bunch_spacing_zeta=bunch_spacing_buckets*bucket_length, # This is P in the paper
    #num_periods=n_bunches, # This is N_S
    num_bunches=h_RF//bunch_spacing_buckets, # This is N_S
    num_turns=n_turns_wake,
    circumference=circumference,
    _flatten=flatten
)

xf_slicer = xf.UniformBinSlicer(
    zeta_range=(-0.5*bucket_length, 0.5*bucket_length),
    num_slices=n_slices,
    i_bunch_0=0, num_bunches=n_bunches,
    bunch_spacing_zeta=bunch_spacing_buckets*bucket_length)

xf_slicer_after = xf.UniformBinSlicer(
    zeta_range=(-0.5*bucket_length, 0.5*bucket_length),
    num_slices=n_slices,
    i_bunch_0=0, num_bunches=n_bunches,
    bunch_spacing_zeta=bunch_spacing_buckets*bucket_length)


color_list = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
for i_turn in range(n_turns):

    needs_restore = False
    x_beam_before_wake = beam.x.copy()
    x_allbunches_before_wake = allbunches.x.copy()
    # if i_turn != 0:
    #     beam.x[:] = 0
    #     allbunches.x[:] = 0
    #     needs_restore = True

    allbunches.clean_slices()
    slice_set_before_wake_allbunches.append(allbunches.get_slices(slicer,
                        statistics=['mean_x', 'mean_xp', 'mean_y', 'mean_yp']))
    allbunches.clean_slices()

    # Continue with PyHEADTAIL
    beam.clean_slices()
    slice_set_before_wake_beam.append(beam.get_slices(slicer_full_beam,
                        statistics=['mean_x', 'mean_xp', 'mean_y', 'mean_yp']))
    beam.clean_slices()

    x_at_wake_allbunches.append(allbunches.x.copy())
    xp_before_wake_allbunches.append(allbunches.xp.copy())

    x_at_wake_beam.append(beam.x.copy())
    xp_before_wake_beam.append(beam.xp.copy())

    # Xfields wake implementation
    xt_part_temp = xt.Particles(
        mass0=xt.PROTON_MASS_EV,
        gamma0=beam.gamma,
        x=beam.x,
        px=beam.xp,
        y=beam.y,
        py=beam.yp,
        zeta=beam.z,
        delta=beam.dp,
        weight = beam.particlenumber_per_mp,
    )

    # Measure slice moments and get slice indeces
    t0 = time.perf_counter()
    i_slice_particles = xt_part_temp.particle_id * 0 + -999
    i_bunch_particles = xt_part_temp.particle_id * 0 + -9999
    xf_slicer.slice(xt_part_temp, i_slice_particles=i_slice_particles,
                    i_bunch_particles=i_bunch_particles)
    t1 = time.perf_counter()
    print(f'T xfields slice {(t1 - t0)*1e3:.2f} ms')

    # Trash oldest turn
    t0 = time.perf_counter()
    wf.moments_data.data[:, 1:, :] = wf.moments_data.data[:, :-1, :]
    wf.moments_data.data[:, 0, :] = 0
    t1 = time.perf_counter()
    print(f'T xfields trash {(t1 - t0)*1e3:.2f} ms')

    # Set moments for latest turn
    t0 = time.perf_counter()
    for i_bunch in range(n_bunches):
        wf.moments_data.set_moments(moments={
             'x': xf_slicer.mean('x')[i_bunch, :], # This is very slow!!!
             'num_particles': xf_slicer.particles_per_slice[i_bunch, :],
             },
            i_turn=0, i_source=i_bunch)
    t1 = time.perf_counter()
    print(f'T xfields set bunch moments {(t1 - t0)*1e3:.2f} ms')

    # Compute convolution
    t0 = time.perf_counter()
    wf._compute_convolution(moment_names=['x', 'num_particles'])
    t1 = time.perf_counter()
    dt_xht_sec = t1 - t0
    print(f'T xfields convolution {dt_xht_sec * 1e3:.2f} ms')

    # Apply kicks
    wf.moments_data.moments_names
    t0 = time.perf_counter()
    # interpolated_result = np.interp(xt_part_temp.zeta, z_res, res)

    interpolated_result = xt_part_temp.zeta * 0
    assert wf.moments_data.moments_names[-1] == 'result'
    md = wf.moments_data
    # data = md.data
    # data_1d = md.data.flatten()
    # for ipart in range(len(i_bunch_particles)):
    #     print(f'ipart = {ipart} / {len(i_bunch_particles)}', end='\r', flush=True)
    #     i_bunch = i_bunch_particles[ipart]
    #     i_slice = i_slice_particles[ipart]
    #     i_start_in_moments_data = (md._N_S - i_bunch - 1) * md._N_aux
    #     rr = data_1d[data.shape[2] * data.shape[1] * (data.shape[0] - 1) +
    #                  # data.shape[0] * (i_turn) # i_turn is zero for the result
    #                  i_start_in_moments_data + i_slice]
    #     # rr = wf.moments_data.data[i_moment_res, i_turn_res, i_start_in_moments_data + i_slice]
    #     interpolated_result[ipart] = rr



    wf.moments_data._interp_result(particles=xt_part_temp,
                data_shape_0=md.data.shape[0],
                data_shape_1=md.data.shape[1],
                data_shape_2=md.data.shape[2],
                data=md.data,
                i_bunch_particles=i_bunch_particles,
                i_slice_particles=i_slice_particles,
                out=interpolated_result)

    # interpolated result will be zero for lost particles (so nothing to do for them)
    scaling_constant = -xt_part_temp.q0**2 * qe**2 / (xt_part_temp.p0c * qe)
    getattr(xt_part_temp, wf.kick)[:] += scaling_constant * interpolated_result # remember to handle lost particles!!!
    t1 = time.perf_counter()
    print(f'T xfields apply kicks {(t1 - t0)*1e3:.2f} ms')

    # measure slice moments after wake
    xf_slicer_after.slice(xt_part_temp)

    # Back to pyheadtail
    wf.moments_data['result']

    wake_field.track(allbunches)
    wake_field_full_beam.track(beam)

    allbunches.clean_slices()
    slice_set_after_wake_allbunches.append(allbunches.get_slices(slicer,
                        statistics=['mean_x', 'mean_xp', 'mean_y', 'mean_yp']))
    allbunches.clean_slices()

    beam.clean_slices()
    slice_set_after_wake_beam.append(beam.get_slices(slicer_full_beam,
                        statistics=['mean_x', 'mean_xp', 'mean_y', 'mean_yp']))
    beam.clean_slices()

    xp_after_wake_allbunches.append(allbunches.xp.copy())
    xp_after_wake_beam.append(beam.xp.copy())

    if needs_restore:
        beam.x[:] = x_beam_before_wake
        allbunches.x[:] = x_allbunches_before_wake

    transverse_map.track(allbunches)
    transverse_map.track(beam)

    z_centers = slice_set_before_wake_beam[-1].z_centers
    mean_x_slice = slice_set_before_wake_beam[-1].mean_x
    num_charges_slice = slice_set_before_wake_beam[-1].charge_per_slice/e
    dip_moment_slice = num_charges_slice * mean_x_slice

    for i_bunch in range(n_bunches):
        i_bucket = bucket_id_set[::-1][i_bunch]
        print(f"{i_bunch=} {i_bucket=}")
        i_z_bunch_center = np.argmin(np.abs(z_centers - (-i_bucket * bucket_length)))

        i_z_a_bunch = i_z_bunch_center - n_slices//2
        if i_z_a_bunch == -1: # Rounding error
            i_z_a_bunch = 0

        dipole_moment_matrix_multiturn[i_bunch, :, i_turn] = dip_moment_slice[
                                            i_z_a_bunch : i_z_a_bunch+n_slices]

        z_source_matrix_multiturn[i_bunch, :, i_turn] = z_centers[
                                        i_z_a_bunch : i_z_a_bunch+n_slices]

    if plot_on:
        ax00.plot(slice_set_after_wake_beam[-1].z_centers,
                slice_set_after_wake_beam[-1].mean_x, '-', color=color_list[i_turn],
                label=f"turn {i_turn}")

        ax00.plot(
            xf_slicer.zeta_centers.T,
            xf_slicer.mean('x').T, '.', color=color_list[i_turn])

        ax01.plot(
            slice_set_after_wake_beam[-1].z_centers,
            slice_set_after_wake_beam[-1].mean_xp - slice_set_before_wake_beam[-1].mean_xp,
            '-', color=color_list[i_turn], label=f"turn {i_turn}")

        ax01.plot(
            xf_slicer.zeta_centers.T,
            xf_slicer_after.mean('px').T - xf_slicer.mean('px').T, 'x', color=color_list[i_turn])


if plot_on:
    ax00.legend()

z_source_matrix_multiturn = z_source_matrix_multiturn[:, :, ::-1] # last turn on top
dipole_moment_matrix_multiturn = dipole_moment_matrix_multiturn[:, :, ::-1] # last turn on top

print(f'Circumference occupancy {n_bunches * bunch_spacing_buckets/h_RF*100:.2f} %')



# t0 = time.perf_counter()
# wf._compute_convolution(moment_names=['x', 'num_particles'])
# t1 = time.perf_counter()
# dt_xht_sec = t1 - t0
# print(f'T xheadtail {dt_xht_sec * 1e3:.2f} ms')

z_profile, res_profile = wf.get_moment_profile(moment_name='result', i_turn=0)

for i_turn in range(1, n_turns_wake):
    zz, rr = wf.get_moment_profile(moment_name='result', i_turn=i_turn)
    res_profile += rr

res_profile_scaled = res_profile * (-e**2 / (p0_SI * c))

if plot_on:
    plt.figure(200)
    plt.plot(wf.z_wake.T, wf.G_aux.T * (-e**2 / (p0_SI * c)), alpha=0.5)

    ax01.plot(z_profile, res_profile_scaled, 'b.')

print(f'T pyht accumulate ({mpi_settings}) {wake_field.wake_kicks[0].time_last_accumulate * 1e3:.2f} ms')
print(f'T pyht convolution ({mpi_settings}) {wake_field.time_last_field_computation * 1e3:.2f} ms')

plt.show()

