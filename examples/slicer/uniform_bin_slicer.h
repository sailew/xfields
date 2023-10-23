// copyright ################################# //
// This file is part of the Xfields Package.   //
// Copyright (c) CERN, 2021.                   //
// ########################################### //

#ifndef XFIELDS_UNIFORM_BIN_SLICER_H
#define XFIELDS_UNIFORM_BIN_SLICER_H


/*gpufun*/
void UniformBinSlicer_slice(UniformBinSlicerData el,
                LocalParticle* part0,
                /*gpuglmem*/ int64_t* i_slice_for_particles){

    int64_t const num_slices = UniformBinSlicerData_get_num_slices(el);
    double const z_min = UniformBinSlicerData_get_z_min(el);
    double const dzeta = UniformBinSlicerData_get_dzeta(el);

    //start_per_particle_block (part0->part)
        double zeta = LocalParticle_get_zeta(part);
        const int64_t ipart = part->ipart;

        int64_t i_slice = floor((zeta - z_min) / dzeta);

        if (i_slice >= 0 && i_slice < num_slices){
            i_slice_for_particles[ipart] = i_slice;
        } else {
            i_slice_for_particles[ipart] = -1;
        }
    //end_per_particle_block


}

/*gpufun*/
void UniformBinSlicer_track_local_particle(UniformBinSlicerData el,
                LocalParticle* part0){

}

#endif