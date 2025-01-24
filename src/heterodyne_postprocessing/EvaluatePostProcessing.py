# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from heterodyne_postprocessing.processing.postProcessor import PostProcessor
import matplotlib.pyplot as plt

# %% Manual wavelength calibration of calibration measurement
# !!!!! Only execute this section, if you really want to (re)calibrate the calibration measurement !!!!

# calibration_name = r'C:\xxxxx\xxxxx\XXXXXXXXXXXXXXXXXXXX_processed_data.h5'
# reference_name = r'C:\xxxxx\xxxxx\XXXXXXXXXXXXX.mat'

# calibProc = PostProcessor()
# calibProc.load_configuration(calibration_name)
# calibProc.load_transmission()
# calibProc.calibrateWNaxisOfCalibration(calibFilename=calibration_name, refFilename=reference_name, plotOn=False)

# %% Definition of the files
measurement_name = r'C:\xxxxx\xxxxx\XXXXXXXXXXXXXXXXXXXX_processed_data.h5'
calibrated_calibration_name = r'C:\xxxxx\xxxxx\XXXXXXXXXXXXXXXXXXXX_calibrated_processed_data.h5'

# %% Loading the measurement
proc = PostProcessor()
proc.load_configuration(measurement_name)
proc.load_transmission()
proc.calibrateWNaxisOfMeasurement(calibFilename=calibrated_calibration_name, plotOn=False, debug=False)

# %% Averaging acquisitions
# proc.ASC_phase_drift_correction = True  # default = False
proc.acquisition_average(startIndx=None, stopIndx=None, plotOn=True)
# For ASC (amplitude-sensitive configuration) only: if the phase angle of the complex transmission is significantly
# different from zero, then the attribute proc.ASC_phase_drift_correction should be set to True --> uncomment the
# line above to and re-run this cell.
# See helpdesk article at https://irsweep.atlassian.net/servicedesk/customer/portal/2/topic/e487cc9e-84f8-43bc-833f-57772986eeab/article/3544055809


# %% Spectral averaging
proc.spectral_smoothing(gaussianConvolve=True, gaussianWNsigma=0.6, plotOn=True, threshold=1)
# Alternatively, use Boxcar averaging:
# proc.spectral_smoothing(gaussianConvolve=False, spectralHalfWidth=5, plotOn=True, threshold=1)

# %% plot transient
if proc.is_timeresolved():
    plt.close('all')
    proc.plotSpectra(mode='absorbance')
    proc.plotTransients(logscale=False, mode='absorbance')

#%% export: You can export different data to a CSV file. For example proc.data['transientTrans'], proc.data['transmission'], proc.data['transientTransAvgOfFiles'], proc.data['transmissionAvgOfFiles']
proc.csv_export(proc.data['transmission'], transpose = False)
