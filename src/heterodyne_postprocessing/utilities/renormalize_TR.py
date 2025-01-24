# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

#############################
# example for how to exchange the normalization vectors of two time resolved measurements
# input: file names for the measurement you wish to renormalize, the measurement
# containing the new background, and the calibrated calibration file for both
# output: renormalized array in the same format as 'transientTrans' and matching wnAxis
#############################


import numpy as np
from itertools import islice
from heterodyne_postprocessing.processing.postProcessor import PostProcessor


#############################
# USER INPUT STARTS HERE
# the measurement you wish to renormalize
measurement_a = r'C:/xxx/xxx/my_measurement_processed_data.h5'
calibration_a = r'C:/xxx/xxx/my_measurement_calibration_calibrated_processed_data.h5'

# the measurement containing the new normalization
measurement_bg = r'C:/xxx/xxx/my_measurement_with_new_background_processed_data.h5'
# the code provided may fail if different calibration files are used
calibration_bg = calibration_a 

# decide if you want to overwrite the old 'transientTrans'; this this allows wavenumber
# and acquisition averaging to be used as usual but it may interfere with other functions
overwrite_tT = True
# USER INPUT ENDS HERE
#############################



# method for processing and calibrating
def make_proc(measurement_name, calibrated_calibration_name):
    proc = PostProcessor()
    proc.load_configuration(measurement_name)
    proc.load_transmission()
    proc.calibrateWNaxisOfMeasurement(calibFilename=calibrated_calibration_name, plotOn=False) 
    return proc

# method for finding the indeces of overlapping elements of two arrays
def find_overlap(wn_axis_a, wn_axis_bg):
    if wn_axis_a[0] > wn_axis_a[1] or wn_axis_bg[0] > wn_axis_bg[1]:
        print("Please ensure that both Wavenumber axes are in ascending order")
        return
    else:
        overlap_idx_a = []
        overlap_idx_bg = []
        # shortcut value to avoide needlessly iterating 
        shortcut = 0
        # iterate over all elements of one wavenumber axis
        for i, va in enumerate(wn_axis_a):
            # iterate over all elements of the second wavenumber axis, starting at shortcut
            for j, vb in islice(enumerate(wn_axis_bg), shortcut, None): 
                # check if element va has a close equivalent in vb and note down if it does
                if np.isclose(va, vb, rtol=1e-05, atol=1e-08,):
                    overlap_idx_a.append(i)
                    overlap_idx_bg.append(j)
                # move on once vb is bigger than va, since it is pointless to continue
                elif vb > va:
                    break
                #increase shortcut by 1 if va > vb, since iterating over the lower values would be pointless
                else:
                    shortcut +=1
        return overlap_idx_a, overlap_idx_bg


# process and calibrate measurements 
proc_a = make_proc(measurement_a, calibration_a)
proc_bg = make_proc(measurement_bg, calibration_bg)

# unnormalize the measurement of interest
# initialize the list to store the unnormalized data
unnormalized_a = []

# iterate through all acquisitions and multiply each time slice by the normalization vector
for i in range(proc_a.data['transientTrans'].shape[-1]):
    ratio = [np.multiply(v,proc_a.data['normalizationVector'][...,i]) for v in proc_a.data['transientTrans'][...,i]] 
    unnormalized_a.append(np.array(ratio))

# restore original format
unnormalized_a = np.moveaxis(np.array(unnormalized_a), [0,1,2],[2,0,1])

# calculate the spectral overlap of the two measurements 
overlap_a, overlap_bg = find_overlap(proc_a.data['wnAxis'], proc_bg.data['wnAxis'])

# cut measurement to overlapping regions
unnormalized_a = unnormalized_a[:,overlap_a[0]:overlap_a[-1],:]

# cut new normalization vector to overlapping regions
new_bg = proc_bg.data['normalizationVector'][overlap_bg[0]:overlap_bg[-1],:]

# apply the new normalization vector to the measurement
# initialize the list to store the renormalized data
renormalized = []

# iterate through all acquisitions and multiply each time slice by the normalization vector
for i in range(unnormalized_a.shape[-1]):
    ratio = [np.divide(v,new_bg[...,i]) for v in unnormalized_a[...,i]] 
    renormalized.append(np.array(ratio))

# reshape to match the original
renormalized = np.moveaxis(np.array(renormalized), [0,1,2],[2,0,1])

# overwrite the old transientTrans and wnAxis arrays; 
if overwrite_tT == True:
    proc_a.data['wnAxis'] = proc_a.data['wnAxis'][overlap_a[0]:overlap_a[-1]]
    proc_a.data['transientTrans'] = renormalized

