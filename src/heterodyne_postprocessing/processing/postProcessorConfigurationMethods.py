# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorHDF5 import PostProcessorHDF5Loader

import numpy as np

class PostProcessorConfigurationMethods(PostProcessorHDF5Loader):
    
    def __init__(self):
        super().__init__()
        self.ASC_phase_drift_correction = False
        
    def complexToReal(self, transmission):
        """
        Convert the complex transmission to the real value in the correct way, depending on the measurement
        configuration.
        For phase-sensitive configuration (PSC) measurements, the phase of the complex transmission encodes the
        dispersion of the sample and is therefore non-zero (in general). The real transmission is the magnitude
        squared of the complex transmission; the square is because only the interrogating comb is attenuated by the
        sample and transmission is a measure of power (not amplitude) attenuation.
        For ASC measurements, the phase of the complex transmission is often very close to zero. For the real
        transmission, one can take the real part (of the complex transmission). The advantage is that if the
        transmission is close to zero, taking the real part will yield a value that averages to zero.
        However, if the phase of the complex transmission is non-zero (e.g., because one of the beam path lengths
        changed between the measurement of the background and sample), then taking the real part of the complex
        transmission will not yield the correct real transmission. In this case, the magnitude should be taken (
        not squared, because both combs asre atteunated by the sample).

        The ASC_phase_drift_correction attribute should be set to True in cases where the phase of the complex
        transmission is significantly different from zero.

        input: complex transmission
        output: real transmission
        """
        ASC_phase_drift_correction = self.ASC_phase_drift_correction
        if self.config.read_ASC_PSC_configuration() == 'ASC':
            if ASC_phase_drift_correction:
                realTransmission = np.abs(transmission)
            else:
                realTransmission = np.real(transmission)
        elif self.config.read_ASC_PSC_configuration() == 'PSC':
            realTransmission = np.square(np.abs(transmission))
           
        return realTransmission
    
    def averageConfiguration(self, startIndx, stopIndx):
        """
        compute the average over the different acquisition in the correct way, depending on the measurement configuration.
        The different averaging algorithms are described in SPEC-2279
        input: starting and stopping index of the averaged acquisitions
        output: averaged transmission
        """
        if self.config.read_ASC_PSC_configuration() == 'ASC':
            if self.is_timeresolved():
                # complex average
                tmp_avg = np.mean(self.data[self.data_name][:, :, startIndx:stopIndx], axis=-1)
            elif self.is_timeintegrated():
                # complex average
                tmp_avg = np.mean(self.data[self.data_name][:,startIndx:stopIndx],axis=-1)
                
        elif self.config.read_ASC_PSC_configuration() == 'PSC':
          
            if self.is_timeresolved():
                #complex average
                tmp_avg = np.mean(self.data[self.data_name][:,:,startIndx:stopIndx],axis=-1) 
            elif self.is_timeintegrated():
                #averaging magnitude and phase separately
                tmp_avg_mag = np.mean(np.abs(self.data[self.data_name][:,startIndx:stopIndx]),axis=-1)
                tmp_avg_angle = np.angle(np.mean(self.data[self.data_name][:,startIndx:stopIndx],axis=-1))
                tmp_avg = tmp_avg_mag*np.exp(1j*tmp_avg_angle)
                
        return tmp_avg
    
    def smoothingAvg(self, old_avg, start, stop, weight):
        """
        This method compute the correct average for spectral smoothing, depending on the measurement configuration.
        Input: -acquisition average
               -starting wn index
               -stop wn index
               -weight
        Output: spectrally averaged data
        """
        
        if self.config.read_ASC_PSC_configuration() == 'ASC':
            if self.is_timeresolved():
                #average complex
                tmp_avg = np.mean(old_avg[:,start:stop]*weight*(stop-start),axis=-1)
            elif self.is_timeintegrated():
                #average complex
                tmp_avg = np.mean(old_avg[start:stop]*weight*(stop-start),axis=-1)
                
        elif self.config.read_ASC_PSC_configuration() == 'PSC':
            if self.is_timeresolved():
                #average complex
                tmp_avg = np.mean(old_avg[:,start:stop]*weight*(stop-start),axis=-1)
            elif self.is_timeintegrated():
                #averaging magnitude and phase separately
                tmp_avg_mag = np.mean(np.abs(old_avg[start:stop])*weight*(stop-start),axis=-1)
                tmp_avg_angle = np.angle(np.mean(old_avg[start:stop]*weight*(stop-start),axis=-1))
                tmp_avg = tmp_avg_mag*np.exp(1j*tmp_avg_angle)
                
        return tmp_avg
    
    def smoothingAvgIndiv(self, old_avg_indiv, start, stop, weight):
        """
        This method compute the correct average for spectral smoothing, depending on the measurement configuration.
        Input: -acquisitions
               -starting wn index
               -stop wn index
               -weight
        Output: spectrally averaged data for each individual acquisitions
        """
        
        if self.config.read_ASC_PSC_configuration() == 'ASC':
                tmp_avg_indiv = np.mean(old_avg_indiv[start:stop,:].T*weight*(stop-start),axis=1)
                
        elif self.config.read_ASC_PSC_configuration() == 'PSC':
                tmp_avg_indiv_mag = np.mean(np.abs(old_avg_indiv[start:stop,:].T)*weight*(stop-start),axis=1)
                tmp_avg_indiv_angle = np.angle(np.mean(old_avg_indiv[start:stop,:].T*weight*(stop-start),axis=1))
                tmp_avg_indiv = tmp_avg_indiv_mag*np.exp(1j*tmp_avg_indiv_angle)
                
        return tmp_avg_indiv