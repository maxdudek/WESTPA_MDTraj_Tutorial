import mdtraj as md
import numpy, westpa

def pcoord_loader(fieldname, pcoord_return_filename, segment, single_point=False):
    # fieldname: should always be 'pcoord' for this function, as it's the pcoord.

    # pcoord_return_filename: a string containing the filename of whatever is copied/piped
    # into $WEST_PCOORD_RETURN. In this case, it will be a trajectory file
    # which we are calculating the RMSD of.

    # segment: the segment object itself.  We'll be replacing
    # segment.pcoord with the progress coordinate (RMSD) we calculate here.

    # single_point: whether we're evaluating a basis/initial state or not.
    # During dynamics, it's false, which means our pcoord should be a numpy array
    # shaped as ndim/pcoord_length, as defined in west.cfg
    # Otherwise, it's a numpy array with shape = ndim.

    # Lets us reference variables from WESTPA
    system = westpa.rc.get_system_driver()

    # Make sure that the fieldname argument is 'pcoord'
    assert fieldname == 'pcoord'

    # Locate the topology file
    topFile = 'amber_config/P53.prmtop'

    # Load the reference crystal
    # The .load() function automatically recognizes the given file as a netcdf file
    # from the .nc extension
    crystal = md.load('bstates/P53.nc', top=topFile)

    # Load the trajectory
    # Here the .load_netcdf() function is used because the pcoord_return_filename file
    # does not have an extension, so we need to let MDTraj know that it is a netcdf file.
    traj = md.load_netcdf(pcoord_return_filename, top=topFile)

    # Calculate the rmsd of the trajectory relative to the crystal.
    # The .rmsd() function takes an optional third int argument which refers to
    # the frame in the reference to measure distances to. By default, the frame
    # is set to 0. A general form of the function is:
    # MDTraj.rmsd(target, reference, frame=0) which returns a numpy array
    rmsd = md.rmsd(traj,crystal)

    # Below we check to make sure the shape of the array is what WESTPA expects.
    # Here system.pcoord_ndim refers to the number of dimensions in the
    # progress coordinate, which in this case is 1.
    # system.pcoord_len refers to the number of times the trajectory coordinates
    # are saved during each iteration (100 in this case)

    # The check is different if we are checking a single point during initialization.
    # If single_point = True, then we only need the last value in the array.
    if single_point:
        rmsd = numpy.array(rmsd[-1]) # Get the last value in the array
        expected_shape = (system.pcoord_ndim,) # Expects a 1x1 array
        #Correct the shape if needed
        if rmsd.ndim == 0:
            rmsd.shape = (1,)

    # During dynamics, WESTPA expects a 2D array, with size (pcoord_len, pcoord_ndim)
    else:
        expected_shape = (system.pcoord_len, system.pcoord_ndim) # Expects a 100x1 array
        if rmsd.ndim == 1:
            rmsd.shape = (len(rmsd),1)

    # Send a debug message if the shape is different from what is expected
    if rmsd.shape != expected_shape:
        raise ValueError('progress coordinate data has incorrect shape {!r} [expected {!r}]'.format(rmsd.shape,
                                                                                                    expected_shape))

    # Send the calculated rmsd array to the segment object
    segment.pcoord = rmsd
