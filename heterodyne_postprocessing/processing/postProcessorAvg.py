# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorConfigurationMethods import PostProcessorConfigurationMethods

import numpy as np
import copy as copy
import matplotlib.pyplot as plt


class PostProcessorAvg(PostProcessorConfigurationMethods):
    def __init__(self):
        super().__init__()
        
        
        
    def acquisition_average(self,startIndx=None,stopIndx=None,plotOn=False):
        """
        Function to average acquisitions together. Saves the data under 
        proc.data_name+'AvgOfFiles'.
        
        Input   :   startIndx(int) the first acqusition to take
                    stopIndx(int) the last acquisition to take
                    plotOnt(bool) boolean to plot or not data before/after
        """
        if startIndx is None:
            startIndx = 0
        if stopIndx is None:
            stopIndx = self.data['numAcq']
        else:
            stopIndx = stopIndx+1
            
        tmp_avg = self.averageConfiguration(startIndx, stopIndx)
        
        std_mean, stdIsAbsolute = self.std_average(startIndx=startIndx,stopIndx=stopIndx)
        
        if stdIsAbsolute:
            std_mean = std_mean/self.complexToReal(tmp_avg)

        self.data.update({'stdAvgOfFiles':std_mean})
        self.data.update({self.data_name+'AvgOfFiles':tmp_avg})
        self.last_data_type = 'AvgOfFiles'
        
        if plotOn:
            fig,ax = plt.subplots()
            if self.is_timeresolved():
                ax.plot(self.data['timeAxis']*1e3,self.complexToReal(self.data[self.data_name][:,self.config.maxPeakNo,startIndx]),label='First acquisition')
                ax.plot(self.data['timeAxis']*1e3,self.complexToReal(self.data[self.data_name+'AvgOfFiles'][:,self.config.maxPeakNo]),label='Average of '+str(stopIndx-startIndx)+' files')
                ax.set_xlabel('Time [ms]')
                ax.set_ylabel('Transmission')
            elif self.is_timeintegrated():
                ax.plot(self.data['wnAxis'],self.complexToReal(self.data[self.data_name][:,startIndx]),label='First acquisition')
                ax.plot(self.data['wnAxis'],self.complexToReal(self.data[self.data_name+'AvgOfFiles'][:]),label='Average of '+str(stopIndx-startIndx)+' files')
                ax.set_xlabel('Wavenumber [cm$^{-1}$]')
                ax.set_ylabel('Transmission')    
            ax.legend()
    
    def std_average(self,startIndx,stopIndx):
        '''
        Method to average the standard deviation via squared sums. As the standard deviation saved in stdPeakAcqs is normalized by its mean value,
        it must first multiplied with its value. Carful, the return is not anymore a relative standard deviation.
        '''
        temp=0
        
        #checks if the standard deviation for each acquisition is in the dic data. If not (old procsessor) the stdpeak is returnd
        if 'stdPeakAcqs' in self.data.keys():            
            if self.is_timeintegrated(): 
                for i in range(startIndx,stopIndx):
                    temp+=np.power(self.data['stdPeakAcqs'][:,i]*self.complexToReal(self.data[self.data_name][:,i]),2)    
                std_mean = np.sqrt(temp)/(stopIndx-startIndx)
                stdIsAbsolute = True
                
            if self.is_timeresolved(): #in the time resolved case the transient trans over the background is 1, so no transformation from rel to absolute is required.
                for i in range(startIndx,stopIndx):
                    temp+=np.power(self.data['stdPeakAcqs'][:,i],2)    
                std_mean = np.sqrt(temp)/(stopIndx-startIndx)
                stdIsAbsolute = False
                
        else:
            std_mean = self.data['stdPeak']
            stdIsAbsolute = False
            
        return std_mean, stdIsAbsolute
        
    
    def gaussian(self,x, mu, sig):
        return (1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2))
    
    def spectral_smoothing(self,spectralHalfWidth=0,plotOn=False, gaussianConvolve=True, gaussianWNsigma=0.6,threshold=1):
        """
        Function to spectrally average the transmission. The smoothing is done by applying a filter on the spectra which
        is weighted by the inverse of the standard deviation of each peaks (i-spectralHalfWidth:i+spectralHalfWidth+1 -> i)
         The filter is (by default) gaussian if the gaussianConvolve is set to True or by a window (box).
        In the former case the spectralHalfwidth is ignored and the gaussianWNsigma has to be defined.
        The data is saved under proc.data_name+'SpectralAvgOfFiles'
        
        Input   :   spectralHalfWidth(int) half of the size of the window to 
                    average points together. Usually set to 5.
                    plotOn(bool) boolean to plot or not the data before/after
                    gaussianConvolve(bool) loolean to add a gaussian concolution on top
                    gaussianWNsigma sets the sigma in cm^-1
                    treshold filters the standqrd deviation peaks above it's value
                    
        """
        old_avg = np.copy(self.data[self.data_name+'AvgOfFiles'])
        new_avg = np.copy(self.data[self.data_name+'AvgOfFiles'])
        
        
        if self.is_timeintegrated():
            old_avg_indiv= np.copy(self.data[self.data_name])
            new_avg_indiv = np.copy(self.data[self.data_name])
        
        if gaussianConvolve is False:
            spectralHalfWidth = int(spectralHalfWidth)
            for i in np.arange(0,old_avg.shape[-1]):
                start = np.max([0,i-spectralHalfWidth])
                stop = np.min([i+spectralHalfWidth+1,old_avg.shape[-1]])
                if self.is_timeresolved():
                        new_avg[:,i] = self.smoothingAvg(old_avg, start, stop, self.weights(start,stop,threshold))
                elif self.is_timeintegrated():
                        new_avg[i] = self.smoothingAvg(old_avg, start, stop,self.weights(start,stop,threshold))
                        new_avg_indiv[i,:] = self.smoothingAvgIndiv(old_avg_indiv, start, stop, self.weights(start,stop,threshold,individual=True))  
        elif gaussianConvolve is True: 
             gaussianWNsigma=abs(gaussianWNsigma/(self.data['wnAxis'][1]-self.data['wnAxis'][0])) #calculate from cm^-1 to line numbers
             spectralHalfWidth = int(np.ceil(gaussianWNsigma))*3 #calculates the considered points
             for i in np.arange(0,old_avg.shape[-1]):
                start = np.max([0,i-spectralHalfWidth])
                stop = np.min([i+spectralHalfWidth+1,old_avg.shape[-1]])
                if self.is_timeresolved():
                        new_avg[:,i] = self.smoothingAvg(old_avg, start, stop, self.weights(start,stop,i,gaussianWNsigma,threshold)) 
                elif self.is_timeintegrated():
                        new_avg[i] = self.smoothingAvg(old_avg, start, stop,self.weights(start,stop,i,gaussianWNsigma,threshold))      
                        new_avg_indiv[i,:] = self.smoothingAvgIndiv(old_avg_indiv, start, stop,self.weights(start,stop,i,gaussianWNsigma,threshold,individual=True))  
                    
                    
        self.data.update({self.data_name+'SpectralAvgOfFiles':new_avg})
        self.last_data_type = 'SpectralAvgOfFiles'
        
        if self.is_timeintegrated():
            new_avg_indiv = np.transpose(new_avg_indiv) # create dimension consistency with time-resolved
            self.data.update({self.data_name+'SpectralAvgOfIndividualFiles':new_avg_indiv})
        
        
        if plotOn:
            fig,ax = plt.subplots()
            if self.is_timeresolved():
                ax.plot(self.data['timeAxis']*1e3,self.complexToReal(self.data[self.data_name+'AvgOfFiles'][:,self.config.maxPeakNo]),label='No spectral averaging')
                ax.plot(self.data['timeAxis']*1e3,self.complexToReal(self.data[self.data_name+'SpectralAvgOfFiles'][:,self.config.maxPeakNo]),label='Spectral averaged')
                ax.set_xlabel('Time [ms]')
                ax.set_ylabel('Transmission')
            elif self.is_timeintegrated():
                ax.plot(self.data['wnAxis'],self.complexToReal(self.data[self.data_name+'AvgOfFiles'][:]),label='No spectral averaging')
                ax.plot(self.data['wnAxis'],self.complexToReal(self.data[self.data_name+'SpectralAvgOfFiles'][:]),label='Spectral averaged')
                ax.set_xlabel('Wavenumber [cm$^{-1}$]')
                ax.set_ylabel('Transmission') 
            ax.legend()
            
    def weights(self,start,stop,index=0,gaussianWNsigma=None,threshold=1,individual=False):
        """
        Function to generate the weights either from stdPeak or from the
        pretrigger slices in a time-resolved measurement (only with the server version <7.0.0). If selected, a Gaussian convolution is calcuated.
        
        Input   :   start(int) the first peak where to compute the weight
                    stop(int) the last peak where tocompute the weight
                    index(int) the index defining the expectation vaule of the gaussian distribution
                    gaussianWNsigma(float) The Gaussian sigma in wavemunbers. When None, no Gaussian convolution is performed
                    treshold(int) the std tresholding value to give no weight to peaks with a higher std value
                    individual (boolen) If false, the weight is based on an averaged std if true, each individual std from each acquistion is considred.  
        """
        
        #normalization function for Gaussian convolution
        norm=[]
        if gaussianWNsigma is not None:
            for i in range(stop-start):
                norm.append(self.gaussian(i,index-start,gaussianWNsigma))
        else:
            for i in range(stop-start):
                norm.append(1)
        
        
        if individual: #if individual is used, then the weight is calcuated for each individual acquisition
            if 'stdPeakAcqs' in self.data.keys():
                stdPeak= copy.copy(self.data['stdPeakAcqs'][start:stop,:].T)
            else: #in case there is no std for each acq. in the processed files
                stdPeak= self.getStdAxis(start,stop)
        else:
            stdPeak= self.getStdAxis(start,stop)
            
        weight = 1/stdPeak**2
        if 0<threshold<1:
            weight[stdPeak>threshold] = 0
               
        if weight.ndim == 1: 
            if (np.all(weight==0)):
                halfwidth=int(np.round(np.size(stdPeak)/2))
                weight[halfwidth] = 1/stdPeak[halfwidth]**2
            weight = weight*norm    
            weight = weight/np.sum(weight)  
        
        if weight.ndim == 2: 
            for i,weightSingleAcq in enumerate(weight):
                if (np.all(weightSingleAcq==0)):
                    halfwidth=int(np.round(np.size(weightSingleAcq)/2))
                    weight[i][halfwidth] = 1
                weight[i] = weight[i]*norm     
                weight[i] = weight[i]/np.sum(weight[i])
                
        if individual and weight.ndim ==1:
           weight = np.tile((weight), (self.config.numSamp, 1))

        return weight
    

    def getStdAxis(self,start=0,stop=None,plotOn=False):
        """
        Function that gives you the correct standard deviation depending of the version of the processor.
        """
        #from version 7.0.0 is the standard deviation calculated for each acquisition and given by the processor.
        if 'stdPeakAcqs' in self.data.keys():
            if not 'stdAvgOfFiles' in self.data.keys():
                self.acquisition_average()
                
            if stop is None: return self.data['stdAvgOfFiles'][start:]
            else: return self.data['stdAvgOfFiles'][start:stop]
        
        
        #if the stadard deviation was not calculated for each acquisition
        else:
        
            if self.is_timeintegrated():
                if stop is None: return self.data['stdPeak'][start:]
                else: return self.data['stdPeak'][start:stop]
            else:
                if self.config.useBackgroundIntegrationTime: 
                    backgroundSlices = np.int(np.floor(self.config.backgroundIntegrationSamples/self.config.sampleRate/self.config.interleaveTimeStep))
                else:
                    backgroundSlices = np.int(np.floor(self.config.preTriggerSamples/self.config.sampleRate/self.config.interleaveTimeStep))
                    
                if backgroundSlices < 2:
                    return self.data['stdPeak'][start:stop]
                
                if stop is None:
                    std = np.std(np.real(self.data[self.data_name+'AvgOfFiles'][0:backgroundSlices,start:]),axis=0)
                else:
                    std = np.std(np.real(self.data[self.data_name+'AvgOfFiles'][0:backgroundSlices,start:stop]),axis=0)
                return std   
  
    
    
    def getOutputInType(self,data_in,mode_out,mode_in='transmission'):
        """
        Function that generates a real ouptut in one of the following format : 
            transmission
            absorbance
            absorption
            
        Input   :   data_in(ndarray) an array with data of type mode_in
                    mode_out(str) the type of data to output
                    mode_int(str) the type of data in input
        
        Output  :   data(ndarray) an array of same size as input but with the
                    good physical meaning. Values are real.
        """
        
        #Transform everything to transmission first
        if mode_in == 'transmission':
            data = data_in
        elif mode_in == 'absorption':
            data = 1-data_in
        elif mode_in == 'absorbance':
            data = np.power(10,-data_in)
        else:
            raise RuntimeError('in postProcessorAvg.getOutputInType : input type not recognized.')
            
        
        if mode_out =='transmission':
            data_out = data
        elif mode_out == 'absorption':
            data_out = 1-data
        elif mode_out == 'absorbance':
            data_out = -np.log10(np.abs(data))
        else:
            raise RuntimeError('in postProcessorAvg.getOutputInType : input type not recognized.')
            
        return data_out
    
    
if __name__ == '__main__':
    proc = PostProcessorAvg()
    proc.load_configuration()
    proc.load_transmission()
    proc.acquisition_average(plotOn=True)
    proc.spectral_smoothing(5,plotOn=True)