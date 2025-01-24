# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorCalibration import PostProcessorCalibration

import matplotlib.pyplot as plt
import numpy as np

class PostProcessorTimeResolved(PostProcessorCalibration):
    def __init__(self):
        super().__init__()
    
    
    def getTransientInWnRange(self,minWn,maxWn,plotOn=False):
        """
        Function that gives you the a transient corresponding to the average
        of all transients in the wavenumber range.
        
        Input   :   minWn(float) the smallest wavenumber in [cm-1]
                    maxWn(float) the highest wavenumber in [cm-1]
                    plotOn(bool) optional param for plotting
                    
        Output  :   transient(ndarray) an array of length time size
        """
        
        if not self.is_timeresolved():
            raise RuntimeError('in PostProcessorTimeResolved.getTransientInWnRange : not available for non time-resolved measurements')
        
        
        min_indx = np.argmin(np.abs(self.data['wnAxis']-minWn))
        max_indx = np.argmin(np.abs(self.data['wnAxis']-maxWn))
#        If the wnAxis was reversed, min_indx>max_indx so we exchange them !
        if min_indx >max_indx:
            (min_indx,max_indx)=(max_indx,min_indx)
            
        # Add 1 to the max index to make sure we take the last point corresponding to maxWn or minWn
        max_indx+=1
        weight = self.weights(min_indx,max_indx)
        
        transient = self.complexToReal(np.mean(self.data[self.data_name+self.last_data_type][:,min_indx:max_indx]*weight*(max_indx-min_indx),axis=-1))
        
        
        if plotOn:
            plt.figure()
            plt.plot(self.data['timeAxis'],transient)
            plt.xlabel('time [s]')
            plt.ylabel('transmission')
        
        return transient
    
    def getTransientWithLinTime(self,minWn,maxWn,averaging,interleave,plotOn=False):
        """
        Function that gives you the transient corresponding to the average
        of all transients in the wavenumber range with a linear time axis
        
        Input   :   minWn(float) the smallest wavenumber in [cm-1]
                    maxWn(float) the highest wavenumber in [cm-1]
                    averaging how many points to use for averaging
                    interleave(int) the amount of overlap. e.g. 2 means each
                    point is used in two averaged log value.
                    plotOn(bool) optional param for plotting
                    
        Ouptut  :   lintrans(ndarray) an array of length noSteps with transients
                    logtrans(ndarray) an array of length no Steps with time
        """
        if not self.is_timeresolved():
            raise RuntimeError('in PostProcessorTimeResolved.getTransientWithLinTime : not available for non time-resolved measurements')
              
        transient = self.getTransientInWnRange(minWn,maxWn)
        time = np.copy(self.data['timeAxis'])
        start_time = np.min(time)
        
        averaging = int(averaging)
        
        
        deltatime = np.abs(np.mean(np.gradient(self.data['timeAxis'])))*averaging
        noSteps = int(np.floor(len(time)/averaging))
        
        lintime = np.zeros(noSteps)
        lintrans = np.zeros(noSteps)
        for i in np.arange(0,noSteps):
            start = np.argmin(np.abs(time-(start_time+i*deltatime-deltatime*(interleave-1))))
            stop = np.argmin(np.abs(time-(time[start+(averaging-1)]+2*deltatime*(interleave-1))))
            lintime[i] = np.mean(time[start:stop+1])
            lintrans[i] = np.mean(transient[start:stop+1])
        
        
        if plotOn:
            plt.figure()
            plt.plot(lintime,lintrans)
            plt.xlabel('time [s]')
            plt.ylabel('transmission')
            
        return lintrans,lintime
            
            
    def getTransientWithLogTime(self,minWn,maxWn,noSteps,interleave,plotOn=False):
        """
        Function that gives you the transient corresponding to the average
        of all transients in the wavenumber range with a logarithmic
        time axis
        
        Input   :   minWn(float) the smallest wavenumber in [cm-1]
                    maxWn(float) the highest wavenumber in [cm-1]
                    noSteps(int) the number of log steps
                    interleave(int) the amount of overlap. e.g. 2 means each
                    point is used in two averaged log value.
                    plotOn(bool) optional param for plotting
                    
        Ouptut  :   logtrans(ndarray) an array of length noSteps with transients
                    logtime(ndarray) an array of length no Steps with time
        """
        
        if not self.is_timeresolved():
            raise RuntimeError('in PostProcessorTimeResolved.getTransientWithLogTime : not available for non time-resolved measurements')
        
        
        transient = self.getTransientInWnRange(minWn,maxWn)
        time = np.copy(self.data['timeAxis'])
        
        
        #Make sure the time axis is increasing
        indx = np.argsort(time)
        time = time[indx]
        transient=transient[indx]
        
        #Make sure we only take the postTrigger samples and times
        transient = transient[time>0]
        time = time[time>0]
        
        logtime = np.logspace(np.log10(time[0]),np.log10(time[-1]),noSteps)
        logtrans = np.zeros(logtime.shape)
        
        noSteps = int(noSteps)
        start=0
        for i in np.arange(0,noSteps):
            stop = np.argmin(np.abs(time-logtime[i]*interleave))
            logtrans[i]=np.mean(transient[start:stop+1])
            logtime[i]=np.sqrt(time[start]*time[stop])
            start = np.argmin(np.abs(time-logtime[i]))
            
#        logtime = logtime[logtrans != np.nan]
#        logtrans = logtrans[logtrans != np.nan]
        
        
        if plotOn:
            plt.figure()
            plt.semilogx(logtime,logtrans)
            plt.xlabel('time [s]')
            plt.ylabel('transmission')
            
        return logtrans,logtime
    
    def getStartStop(self,startTime,stopTime):
        """
        This method get the start and stop index from the start and stop time

        Args:
            startTime ([float]): selected start time to look up
            stopTime ([float]): selected stop time to look up

        Returns:
            start [int]: start index
            stop  [int]: stop index
        """


        if not self.is_timeresolved():
            raise RuntimeError('in PostProcessorTimeResolved.getSpectrumWithNoiseThreshold : not available for non time-resolved measurements')
        
        start = np.argmin(np.abs(self.data['timeAxis']-startTime))
        stop = np.argmin(np.abs(self.data['timeAxis']-stopTime))
    
        
        #Inver the start - stop if necessary because the axis might have be flipped
        if start > stop:
            (start,stop)=(stop,start)      
            
        #Add 1 to stop to make sure we take all the time steps
        stop+=1

        return start, stop

    def getComplexSpectrum(self,startTime,stopTime):
        """
        Function that gives you the spectrum corresponding to the average of 
        all spectra in the time range.
        
        Input   :   startTime(float) the starting time in [s]
                    stopTime(float) the last time in [s]
                    
        Output  :   transmission(float) a transmission spectrum
        """
        start,stop=self.getStartStop(startTime=startTime,stopTime=stopTime)
        
        complexTransmission = np.mean(self.data[self.data_name+self.last_data_type][start:stop,:],axis=0)
        
        return complexTransmission


    def getSpectrumStd(self,startTime,stopTime):
        """
        Function that gives you the standard deviation of the average of 
        all spectra in the time range.
        
        Input   :   startTime(float) the starting time in [s]
                    stopTime(float) the last time in [s]
                    
        Output  :   std(float) of transmission spectrum
        """
        start,stop=self.getStartStop(startTime=startTime,stopTime=stopTime) 
        
        std = np.std(self.complexToReal(self.data[self.data_name+self.last_data_type][start:stop,:]),axis=0)/np.sqrt(stop-start)
        
        return std

    
    def getSpectrumWithNoiseThreshold(self,startTime,stopTime,threshold,plotOn=False):
        """
        Function that gives you the spectrum corresponding to the average of 
        all spectra in the time range with a noise threshold. All the noisy
        points are set to np.nan.
        
        Input   :   startTime(float) the starting time in [s]
                    stopTime(float) the last time in [s]
                    threshold(float) a threshold for the noise
                    
        Output  :   transmission(float) a transmission spectrum
        """


        transmission = self.complexToReal(self.getComplexSpectrum(startTime,stopTime))
        std = self.getStdAxis()
        transmission[std>threshold]=np.nan
        
        
        if plotOn:
            plt.figure()
            plt.plot(self.data['wnAxis'],transmission)
            plt.xlabel('Wavenumber $[\mathrm{cm^{-1}}]$')
            plt.ylabel('Transmission')
            
        return transmission   
    
 
        
        
        
        
        
    
    
        
        