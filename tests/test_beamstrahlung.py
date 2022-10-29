import numpy as np
import xobjects as xo
import xtrack as xt
import xfields as xf
import xpart as xp

def test_beambeam3d_beamstrahlung_single_collision():
    for context in xo.context.get_test_contexts():

        if not isinstance(context, xo.ContextCpu):
            print(f'skipping test_beambeam3d_beamstrahlung_single_collision for context {context}')
            continue

        ###########
        # ttbar 2 #
        ###########
        bunch_intensity     = 2.3e11  # [1]
        energy              = 182.5  # [GeV]
        p0c                 = 182.5e9  # [eV]
        mass0               = .511e6  # [eV]
        phi                 = 15e-3  # [rad] half xing
        u_sr                = 9.2  # [GeV]
        u_bs                = .0114  # [GeV]
        k2_factor           = .4  # [1]
        qx                  = .554  # [1] half arc
        qy                  = .588  # [1]
        qs                  = .0436  # [1]
        physemit_x          = 1.46e-09  # [m]
        physemit_y          = 2.9e-12  # [m]
        beta_x              = 1  # [m]
        beta_y              = .0016  # [m]
        sigma_x             = np.sqrt(physemit_x*beta_x)  # [m]
        sigma_px            = np.sqrt(physemit_x/beta_x)  # [m]
        sigma_y             = np.sqrt(physemit_y*beta_y)  # [m]
        sigma_py            = np.sqrt(physemit_y/beta_y)  # [m]
        sigma_z             = .00194  # [m] sr
        sigma_z_tot         = .00254  # [m] sr+bs
        sigma_delta         = .0015  # [m]
        sigma_delta_tot     = .00192  # [m]
        beta_s              = sigma_z/sigma_delta  # [m]
        physemit_s          = sigma_z*sigma_delta  # [m]
        physemit_s_tot      = sigma_z_tot*sigma_delta_tot  # [m]
        n_macroparticles_b1 = int(1e6)
        n_macroparticles_b2 = int(1e6)
        
        n_slices = 100
        
        #############
        # particles #
        #############
        
        #e-
        particles_b1 = xp.Particles(
                    _context = context, 
                    q0        = -1,
                    p0c       = p0c,
                    mass0     = mass0,
                    x         = sigma_x        *np.random.randn(n_macroparticles_b1),
                    y         = sigma_y        *np.random.randn(n_macroparticles_b1),
                    zeta      = sigma_z_tot    *np.random.randn(n_macroparticles_b1),
                    px        = sigma_px       *np.random.randn(n_macroparticles_b1),
                    py        = sigma_py       *np.random.randn(n_macroparticles_b1),
                    delta     = sigma_delta_tot*np.random.randn(n_macroparticles_b1),
                    )
        
        # e+
        particles_b2 = xp.Particles(
                    _context = context, 
                    q0        = 1,
                    p0c       = p0c,
                    mass0     = mass0,
                    x         = sigma_x        *np.random.randn(n_macroparticles_b2),
                    y         = sigma_y        *np.random.randn(n_macroparticles_b2),
                    zeta      = sigma_z_tot    *np.random.randn(n_macroparticles_b2),
                    px        = sigma_px       *np.random.randn(n_macroparticles_b2),
                    py        = sigma_py       *np.random.randn(n_macroparticles_b2),
                    delta     = sigma_delta_tot*np.random.randn(n_macroparticles_b2),
                    )
        
        particles_b1.name = "b1"
        particles_b2.name = "b2"
        
        particles_b1._init_random_number_generator()
        particles_b2._init_random_number_generator()
        
        bin_edges = sigma_z_tot*np.linspace(-3.0,3.0,n_slices+1)
        slicer = xf.TempSlicer(bin_edges=bin_edges)
        strong_slice_moments = slicer.compute_moments(particles_b2)
        
        # slice intensity [num. real particles] n_slices inferred from length of this
        slices_other_beam_num_particles = strong_slice_moments[:n_slices]
        # unboosted strong beam moments  
        slices_other_beam_x_center    = strong_slice_moments[n_slices:2*n_slices]
        slices_other_beam_zeta_center = strong_slice_moments[5*n_slices:6*n_slices]
        slices_other_beam_Sigma_11    = strong_slice_moments[7*n_slices:8*n_slices]
        slices_other_beam_Sigma_22    = strong_slice_moments[11*n_slices:12*n_slices]
        slices_other_beam_Sigma_33    = strong_slice_moments[14*n_slices:15*n_slices]
        slices_other_beam_Sigma_44    = strong_slice_moments[16*n_slices:17*n_slices]
        # only if BS on
        slices_other_beam_zeta_bin_width = np.abs(np.diff(slicer.bin_edges))
        
        # change nans to 0
        slices_other_beam_x_center[np.isnan(slices_other_beam_x_center)] = 0
        slices_other_beam_zeta_center[np.isnan(slices_other_beam_zeta_center)] = 0
        slices_other_beam_Sigma_11[np.isnan(slices_other_beam_Sigma_11)] = 0
        slices_other_beam_Sigma_22[np.isnan(slices_other_beam_Sigma_22)] = 0
        slices_other_beam_Sigma_33[np.isnan(slices_other_beam_Sigma_33)] = 0
        slices_other_beam_Sigma_44[np.isnan(slices_other_beam_Sigma_44)] = 0
            
        el_beambeam_b1 = xf.BeamBeamBiGaussian3D(
                _context=context,
                config_for_update = None,
                other_beam_q0=1,
                phi=phi,
                alpha=0,
                # decide between round or elliptical kick formula
                min_sigma_diff     = 1e-28,
                # slice intensity [num. real particles] n_slices inferred from length of this
                slices_other_beam_num_particles      = bunch_intensity/n_macroparticles_b2*slices_other_beam_num_particles,
                # unboosted strong beam moments  
                slices_other_beam_x_center    = slices_other_beam_x_center,
                slices_other_beam_zeta_center = slices_other_beam_zeta_center,
                slices_other_beam_Sigma_11    = slices_other_beam_Sigma_11,
                slices_other_beam_Sigma_22    = slices_other_beam_Sigma_22,
                slices_other_beam_Sigma_33    = slices_other_beam_Sigma_33,
                slices_other_beam_Sigma_44    = slices_other_beam_Sigma_44,
                # only if BS on
                flag_beamstrahlung = 1,
                slices_other_beam_zeta_bin_width_star = slices_other_beam_zeta_bin_width/np.cos(phi),  # boosted dz
                # has to be set
                slices_other_beam_Sigma_12    = n_slices*[0],
                slices_other_beam_Sigma_34    = n_slices*[0],
        )
        
        #########################
        # track for 1 collision #
        #########################
        
        line = xt.Line(elements = [el_beambeam_b1])
        
        tracker = xt.Tracker(line=line)
        record = tracker.start_internal_logging_for_elements_of_type(xf.BeamBeamBiGaussian3D, capacity={"beamstrahlungtable": int(3e5)})
        tracker.track(particles_b1, num_turns=1)
        tracker.stop_internal_logging_for_elements_of_type(xf.BeamBeamBiGaussian3D)

        ###################################
        # compare spectrum with guineapig #
        ###################################

        fname="../test_data_beamstrahlung/guineapig_ttbar2_beamstrahlung_photon_energies_gev.txt"
        guinea_photons = np.loadtxt(fname)  # contains about 250k photons emitted from 1e6 macroparticles in 1 collision
        n_bins = 10
        bins = np.logspace(np.log10(1e-14), np.log10(1e1), n_bins)
        xsuite_hist = np.histogram(record.beamstrahlungtable.photon_energy/1e9, bins=bins)[0]
        guinea_hist = np.histogram(guinea_photons, bins=bins)[0]
        
        bin_rel_errors = np.abs(xsuite_hist - guinea_hist) / guinea_hist
        print(f"bin relative errors [1]: {bin_rel_errors}")
        
        # test if relative error in the last 5 bins is smaller than 1e-1
        assert np.allclose(xsuite_hist[-5:], guinea_hist[-5:], rtol=1e-1, atol=0)
        

def test_beambeam3d_collective_beamstrahlung_single_collision():
    for context in xo.context.get_test_contexts():

        if not isinstance(context, xo.ContextCpu):
            print(f'skipping test_beambeam3d_collective_beamstrahlung_single_collision for context {context}')
            continue
    
        ###########
        # ttbar 2 #
        ###########
        bunch_intensity     = 2.3e11  # [1]
        energy              = 182.5  # [GeV]
        p0c                 = 182.5e9  # [eV]
        mass0               = .511e6  # [eV]
        phi                 = 15e-3  # [rad] half xing
        u_sr                = 9.2  # [GeV]
        u_bs                = .0114  # [GeV]
        k2_factor           = .4  # [1]
        qx                  = .554  # [1] half arc
        qy                  = .588  # [1]
        qs                  = .0436  # [1]
        physemit_x          = 1.46e-09  # [m]
        physemit_y          = 2.9e-12  # [m]
        beta_x              = 1  # [m]
        beta_y              = .0016  # [m]
        sigma_x             = np.sqrt(physemit_x*beta_x)  # [m]
        sigma_px            = np.sqrt(physemit_x/beta_x)  # [m]
        sigma_y             = np.sqrt(physemit_y*beta_y)  # [m]
        sigma_py            = np.sqrt(physemit_y/beta_y)  # [m]
        sigma_z             = .00194  # [m] sr
        sigma_z_tot         = .00254  # [m] sr+bs
        sigma_delta         = .0015  # [m]
        sigma_delta_tot     = .00192  # [m]
        beta_s              = sigma_z/sigma_delta  # [m]
        physemit_s          = sigma_z*sigma_delta  # [m]
        physemit_s_tot      = sigma_z_tot*sigma_delta_tot  # [m]
        n_macroparticles_b1 = int(1e6)
        n_macroparticles_b2 = int(1e6)
        
        n_slices = 100
        
        #############
        # particles #
        #############
        
        #e-
        particles_b1 = xp.Particles(
                    _context = context, 
                    q0        = -1,
                    p0c       = p0c,
                    mass0     = mass0,
                    x         = sigma_x        *np.random.randn(n_macroparticles_b1),
                    y         = sigma_y        *np.random.randn(n_macroparticles_b1),
                    zeta      = sigma_z_tot    *np.random.randn(n_macroparticles_b1),
                    px        = sigma_px       *np.random.randn(n_macroparticles_b1),
                    py        = sigma_py       *np.random.randn(n_macroparticles_b1),
                    delta     = sigma_delta_tot*np.random.randn(n_macroparticles_b1),
                    )
        
        # e+
        particles_b2 = xp.Particles(
                    _context = context, 
                    q0        = 1,
                    p0c       = p0c,
                    mass0     = mass0,
                    x         = sigma_x        *np.random.randn(n_macroparticles_b2),
                    y         = sigma_y        *np.random.randn(n_macroparticles_b2),
                    zeta      = sigma_z_tot    *np.random.randn(n_macroparticles_b2),
                    px        = sigma_px       *np.random.randn(n_macroparticles_b2),
                    py        = sigma_py       *np.random.randn(n_macroparticles_b2),
                    delta     = sigma_delta_tot*np.random.randn(n_macroparticles_b2),
                    )
        
        particles_b1.name = "b1"
        particles_b2.name = "b2"
        
        particles_b1._init_random_number_generator()
        particles_b2._init_random_number_generator()
        
        bin_edges = sigma_z_tot*np.linspace(-3.0,3.0,n_slices+1)
        slicer = xf.TempSlicer(bin_edges=bin_edges)
        strong_slice_moments = slicer.compute_moments(particles_b2)
        
        # this is different w.r.t WS test
        config_for_update=xf.ConfigForUpdateBeamBeamBiGaussian3D(
                        pipeline_manager=None,
                        element_name="beambeam",
                        slicer=slicer,
                        update_every=None, # Never updates (test in weakstrong mode)
                        )
        
        # slice intensity [num. real particles] n_slices inferred from length of this
        slices_other_beam_num_particles = strong_slice_moments[:n_slices]
        # unboosted strong beam moments  
        slices_other_beam_x_center    = strong_slice_moments[n_slices:2*n_slices]
        slices_other_beam_zeta_center = strong_slice_moments[5*n_slices:6*n_slices]
        slices_other_beam_Sigma_11    = strong_slice_moments[7*n_slices:8*n_slices]
        slices_other_beam_Sigma_22    = strong_slice_moments[11*n_slices:12*n_slices]
        slices_other_beam_Sigma_33    = strong_slice_moments[14*n_slices:15*n_slices]
        slices_other_beam_Sigma_44    = strong_slice_moments[16*n_slices:17*n_slices]
        # only if BS on
        slices_other_beam_zeta_bin_width = np.abs(np.diff(slicer.bin_edges))
        
        # change nans to 0
        slices_other_beam_x_center[np.isnan(slices_other_beam_x_center)] = 0
        slices_other_beam_zeta_center[np.isnan(slices_other_beam_zeta_center)] = 0
        slices_other_beam_Sigma_11[np.isnan(slices_other_beam_Sigma_11)] = 0
        slices_other_beam_Sigma_22[np.isnan(slices_other_beam_Sigma_22)] = 0
        slices_other_beam_Sigma_33[np.isnan(slices_other_beam_Sigma_33)] = 0
        slices_other_beam_Sigma_44[np.isnan(slices_other_beam_Sigma_44)] = 0
            
        el_beambeam_b1 = xf.BeamBeamBiGaussian3D(
                _context=context,
                config_for_update = config_for_update,
                other_beam_q0=1,
                phi=phi,
                alpha=0,
                # decide between round or elliptical kick formula
                min_sigma_diff     = 1e-28,
                # slice intensity [num. real particles] n_slices inferred from length of this
                slices_other_beam_num_particles      = bunch_intensity/n_macroparticles_b2*slices_other_beam_num_particles,
                # unboosted strong beam moments  
                slices_other_beam_x_center    = slices_other_beam_x_center,
                slices_other_beam_zeta_center = slices_other_beam_zeta_center,
                slices_other_beam_Sigma_11    = slices_other_beam_Sigma_11,
                slices_other_beam_Sigma_22    = slices_other_beam_Sigma_22,
                slices_other_beam_Sigma_33    = slices_other_beam_Sigma_33,
                slices_other_beam_Sigma_44    = slices_other_beam_Sigma_44,
                # only if BS on
                flag_beamstrahlung = 1,
                slices_other_beam_zeta_bin_width_star = slices_other_beam_zeta_bin_width/np.cos(phi),  # boosted dz
                # has to be set
                slices_other_beam_Sigma_12    = n_slices*[0],
                slices_other_beam_Sigma_34    = n_slices*[0],
        )
        el_beambeam_b1.name = "beambeam"
        
        #########################
        # track for 1 collision #
        #########################
        
        line = xt.Line(elements = [el_beambeam_b1])
        
        tracker = xt.Tracker(line=line)
        record = tracker.start_internal_logging_for_elements_of_type(xf.BeamBeamBiGaussian3D, capacity={"beamstrahlungtable": int(3e5)})
        tracker.track(particles_b1, num_turns=1)
        tracker.stop_internal_logging_for_elements_of_type(xf.BeamBeamBiGaussian3D)

        ###################################
        # compare spectrum with guineapig #
        ###################################

        fname="../test_data_beamstrahlung/guineapig_ttbar2_beamstrahlung_photon_energies_gev.txt"
        guinea_photons = np.loadtxt(fname)  # contains about 250k photons emitted from 1e6 macroparticles in 1 collision
        n_bins = 10
        bins = np.logspace(np.log10(1e-14), np.log10(1e1), n_bins)
        xsuite_hist = np.histogram(record.beamstrahlungtable.photon_energy/1e9, bins=bins)[0]
        guinea_hist = np.histogram(guinea_photons, bins=bins)[0]
        
        bin_rel_errors = np.abs(xsuite_hist - guinea_hist) / guinea_hist
        print(f"bin relative errors [1]: {bin_rel_errors}")
        
        # test if relative error in the last 5 bins is smaller than 1e-1
        assert np.allclose(xsuite_hist[-5:], guinea_hist[-5:], rtol=1e-1, atol=0)
