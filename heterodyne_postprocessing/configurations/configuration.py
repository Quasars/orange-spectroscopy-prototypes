# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import h5py
from heterodyne_postprocessing.misc.hdf5Class import HDF5Class
    
import os

import numpy as np
import warnings


class Configuration(HDF5Class):
    """
    Class holding all the configuration parameter for the evaluation of data 
    from an HDF5 file
    """
    
    def __init__(self):
        
        super().__init__()
        
        
        # General evaluation parameters
        self.dirpath = None
        self.splitName = None
        self.filename = None
        
        self.processor = None
        self.version = None
        self.measureOnTrigger = None
        self.dataProcessing = None
        self.moduleID = None
        
        #Acquisition evaluation parameters
        self.numDaqAcq = None
        self.numAvgBg =None
        self.numAvgTf = None
        self.numAvgSamp = None
        self.preTriggerSamples = None
        self.preTriggerTime = None
        self.backgroundIntegrationSamples = None
        self.backgroundIntegrationTime = None
        self.acqFreq = None
        self.sampleRate = None
        
        # Fourier evaluation parameters
        self.pow2fftLength = None
        self.pow2timeTrace = None
        self.pow2interleave = None
        self.pow2padding = None
        
        self.interleaveTimeStep = None
        
        self.loCut = None
        self.hiCut = None
        
        # Coefficient for beatnote and wavelength calibration
        self.centralWn = None
        
        # Quantitative evaluation parameters
        self.numSamp = None
        
        #Plotting parameters
        self.plot_first_file = True
        self.plot_drift = True
        
        #Processed paramters
        self.noLines = None
        self.maxPeakNo = None
        self.peakStd = None
        self.first_wn_axis = None
            
    def load_configuration(self,filename=None):
        """
        Function to choose between the version to use to load the metadata
        """
        
        #If no filename is given, open a dir tab
        if filename is None or not os.path.exists(str(filename)):
            self.filename = self._get_dir()
        else:
            self.filename = filename
            
        # Get the version to know how to load stuff
        f = h5py.File(self.filename,'r')
        try:
            self.version = np.string_(f['info'].attrs['SoftwareVersion'][0]).decode()
        except:
            try:
                self.version = np.string_(f['info'].attrs['Version'][0]).decode()
            except:
                raise RuntimeError('in Configuration.load_configuration : no version metadata found')
        self.version = tuple(map(int, (self.version.split("."))))
        f.close()

        #Use the function corresponding to the version
        if self.version >=(3,2,3) and self.version<(3,3,0):
            self.read_from_h5_v3_2_3()
        elif self.version>=(3,3,0) and self.version<(4,1,0):
            self.read_from_h5_v3_3_0()
        elif self.version>=(4,1,0) and self.version<(5,0,0):
            self.read_from_h5_v4_1_0()
        elif self.version>=(5,0,0):
            self.read_from_h5_v5_0_0() 
        else:
            raise RuntimeError('in Configuration.load_configuration : software version not compatible.')
            
            
    def read_base_data(self):
        
        f = h5py.File(self.filename,'r')
        
        self.dirpath = os.path.dirname(self.filename)
        self.splitName = os.path.basename(self.filename).replace('_raw.h5','')
        
        info = f['info']
        
        # General evaluation
        self.processor = np.string_(info.attrs['Processor'][0]).decode()
        self.moduleID = np.string_(info.attrs['ModuleID'][0]).decode()
        self.dataProcessing = info.attrs['DataProcessing'][0]
        self.preTriggerSamples = info.attrs['PreTrigSamples'][0]
        
        # Acquisition evaluation parameters
        self.numAvgBg = info.attrs['NumberOfAveragesBackground'][0]
        self.numAvgTf = info.attrs['NumberOfAveragesTransfer'][0]
        self.numAvgSamp = info.attrs['NumberOfAveragesSample'][0]
        self.acqFreq = info.attrs['AcquisitionFrequency'][0]
        self.sampleRate = info.attrs['SampleRate'][0]
        
        # Fourier evaluation parameters
        self.pow2fftLength = int(np.log2(info.attrs['FftLength'][0]))
        self.pow2timeTrace = int(np.log2(info.attrs['Samples'][0]))
        self.pow2interleave = int(info.attrs['Interleaving'][0])
        self.pow2padding = int(info.attrs['ZeroPadding'][0])
        
        self.loCut = 5e7
        self.hiCut = self.sampleRate/2-5e7
        
        self.interleaveTimeStep = 2**self.pow2fftLength/self.sampleRate/2**self.pow2interleave
        
        # Coefficient for wavelength calibration
        self.centralWn = info.attrs['CentralWaveNumber'][0]
                
        f.close()
        
    
    def read_from_h5_v3_2_3(self):
        """
        Read the metadata for the version release 3.2.3 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename,'r')
        
        info = f['info']

        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]        
        self.numDaqAcq = info.attrs['NumberDaqAcquisitions'][0]
        self.useBackgroundIntegrationTime = False
        
        if 2**self.pow2fftLength<2**(self.pow2interleave):
            raise TypeError("in Configuration.read_from_h5_v3_2_3 : the pow2length and interleave parameters must respect 2**pow2length>=2**(interleave-1)")
                
        f.close()
        

    def read_from_h5_v3_3_0(self):
        """
        Read the metadata for the version release 3.3.0 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename,'r')
        
        info = f['info']
        
        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]
        self.driver = info.attrs['Driver'][0]
        self.useBackgroundIntegrationTime = False

        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]
        
        if 2**self.pow2fftLength<2**(self.pow2interleave):
            raise TypeError("in Configuration.read_from_h5_v3_3_0 : the pow2length and interleave parameters must respect 2**pow2length>=2**(interleave-1)")
                
        f.close()
        
        
    def read_from_h5_v4_1_0(self):
        """
        Read the metadata for the version release 4.0.0 of the server
        """
        
        self.read_base_data()
        f = h5py.File(self.filename,'r')
        info = f['info']
        
        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]
        self.measureOnSingleTrigger = info.attrs['MeasureOnSingleTrigger'][0]
        self.driver = info.attrs['Driver'][0]
        
        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]
        
        if 2**self.pow2fftLength<2**(self.pow2interleave):
            raise TypeError("in Configuration.read_from_h5_v4_1_0 : the pow2length and interleave parameters must respect 2**pow2length>=2**(interleave-1)")

        self.model = np.string_(info.attrs['Model'][0]).decode() 
        self.manufacturer = np.string_(info.attrs['Manufacturer'][0]).decode() 
        self.H5Version = info.attrs['H5Version'][0] 
        
        
        self.useBackgroundIntegrationTime = info.attrs['UseBackgroundIntegrationTime'][0]
        self.backgroundIntegrationTime = info.attrs['BackgroundIntegrationTime'][0]*(10**(-3))
        self.backgroundIntegrationSamples = info.attrs['BackgroundIntegrationSamples'][0]
        self.preTriggerTime = info.attrs['PretriggerTime'][0]*(10**(-3))
                
        self.pretriggerAcquisitions = info.attrs['PretriggerAcquisitions'][0]
                        
        f.close()
        
    def read_from_h5_v5_0_0(self):
        """
        Read the metadata for the version release 4.0.0 of the server
        """
        
        self.read_base_data()
        f = h5py.File(self.filename,'r')
        info = f['info']
        
        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]
        
        if 2**self.pow2fftLength<2**(self.pow2interleave):
            raise TypeError("in Configuration.read_from_h5_v4_1_0 : the pow2length and interleave parameters must respect 2**pow2length>=2**(interleave-1)")

        self.model = np.string_(info.attrs['Model'][0]).decode() 
        self.manufacturer = np.string_(info.attrs['Manufacturer'][0]).decode() 
        self.H5Version = info.attrs['H5Version'][0] 
        
        
        self.useBackgroundIntegrationTime = info.attrs['UseBackgroundIntegrationTime'][0]
        self.backgroundIntegrationTime = info.attrs['BackgroundIntegrationTime'][0]*(10**(-3))
        self.backgroundIntegrationSamples = info.attrs['BackgroundIntegrationSamples'][0]
        self.preTriggerTime = info.attrs['PretriggerTime'][0]*(10**(-3))
        self.pretriggerAcquisitions = info.attrs['PretriggerAcquisitions'][0]
                        
        f.close()
                
                
    def require_metadata(self,listNeeded):
        """
        Function that tells you if the requirement in metadata is fullfilled,
        meaning that the metadata specified are initialize and not None
        
        Input   :   listNeeded(list of str) a list of names of metadata
        Output  :   check(bool) a boolean telling if all the required metadata
                    are initialized and not None
        """
        
        for variable in listNeeded:
            if getattr(self,variable) is None:
                return False
            
        return True
    

    def change_config(self,pow2fftLength=None,pow2timeTrace=None,centralWn=None,numAvgBg=None,numAvgTf=None,numAvgSamp=None,preTriggerTime=None, backgroundIntegrationTime=None, useBackgroundIntegrationTime=None, acqFreq=None,pow2interleave=None):
        """
        This function is called if the default configurations want to be changed
        Times should be entered in ms units. 
                    
        """
        if pow2fftLength is not None:
            self.pow2fftLength = pow2fftLength
            
        if pow2interleave is not None:
            self.pow2interleave = pow2interleave
        
        if pow2timeTrace is not None:
            self.pow2timeTrace = pow2timeTrace
        
        if centralWn is not None:
            self.centralWn = centralWn            
  
        if numAvgBg is not None:
            self.numAvgBg = numAvgBg   
            
        if numAvgTf is not None:
            self.numAvgTf = numAvgTf   
            
        if numAvgSamp is not None:
            self.numAvgSamp = numAvgSamp 
            
        if useBackgroundIntegrationTime is not None:
            if self.useBackgroundIntegrationTime == 0 and useBackgroundIntegrationTime == 1 and backgroundIntegrationTime is None:
                warnings.warn("You want to use the BackgroundIntegrationTime feature without indicating the backgroundIntegrationTime. Please indicate a backgroundIntegrationTime.")
            self.useBackgroundIntegrationTime = useBackgroundIntegrationTime
        
        if preTriggerTime is not None:
            self.preTriggerTime = preTriggerTime*(10**(-3))  
            self.preTriggerSamples = self.sampleRate*self.preTriggerTime
        
        if backgroundIntegrationTime is not None: 
            self.backgroundIntegrationTime = backgroundIntegrationTime*(10**(-3))
            self.backgroundIntegrationSamples = self.sampleRate*self.backgroundIntegrationTime
            if self.backgroundIntegrationTime != backgroundIntegrationTime  and self.useBackgroundIntegrationTime == 0:
                warnings.warn("You change the backgroundIntegrationTime, but the BackgroundIntegrationTime feature is off. Please indicate that you want to use the BackgroundIntegrationTime feature.")

        if acqFreq is not None:
            self.acqFreq = acqFreq  

        self.interleaveTimeStep = 2**self.pow2fftLength/self.sampleRate/2**self.pow2interleave


    def read_ASC_PSC_configuration(self):
        """
        this method reads the moduleID and return either "ASC" or "PSC"
        """
        if self.moduleID.find('ASC')>=0:
            name = 'ASC'
        elif self.moduleID.find('PSC')>=0:
            name = 'PSC'
        else:
            raise RuntimeError('It is not possible to read configuration (ASC/PSC)')
            
        return name
        
        
        
if __name__ == '__main__':
    config = Configuration()
