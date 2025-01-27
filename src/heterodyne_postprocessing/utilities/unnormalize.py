# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

#############################
# apply a normalization vector to a time resolved or long term measurement
# input: proc object from IRsweep processing scripts
# output: new array 'unnormalized' of the same format as transientTrans (time resolved)
#         transmission (long term)
#
# use example:
# unnorm_trans = unnormalizer(proc)
#############################

import numpy as np

def unnormalizer(proc):
    
    # check if this is a time resolved or long term measurement and process accordingly
    if proc.is_timeresolved() == True: #for time resolved
        #initialize the list to store the unnormalized data
        unnormalized = []
    
        # iterate through all acquisitions and multiply each time slice by the normalization vector
        for i in range(proc.data['transientTrans'].shape[-1]):
            ratio = [np.multiply(v,proc.data['normalizationVector'][...,i]) for v in proc.data['transientTrans'][...,i]] 
            unnormalized.append(np.array(ratio))
        
        unnormalized = np.moveaxis(np.array(unnormalized), [0,1,2],[2,0,1])

    elif proc.is_timeresolved() == False: #for long term
        unnormalized = [proc.data['transmission'][...,i]*proc.data['normalizationVector'][...,i] for i in range(proc.data['transmission'].shape[-1])]
        unnormalized = np.moveaxis(np.array(unnormalized), [0,1], [1,0])

    return unnormalized
