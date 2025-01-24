# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
from matplotlib.colors import LinearSegmentedColormap 
from heterodyne_postprocessing.processing.postProcessorPlotTransients import PostProcessorPlotTransient


class PostProcessorPlottingUtilities(PostProcessorPlotTransient):
    def __init__(self, time_resolution = 0, calibrated_calibration_name = None, calibrate = False, startIndx = None, stopIndx = None, spectralHalfWidth = 0, gaussianConvolve = False, gaussianWNsigma = 0, plotOn = False, title = '', yaxis = '', plot_range = False, legend = True, plot_type = 'absorbance', color_scheme = 'IRsweep'):
        super().__init__()
        # self.measurement_name = measurement_name
        # self.plot_data = plot_data
        # self.plot_at_time = plot_at_time
        self.time_resolution = time_resolution
        self.calibrated_calibration_name = calibrated_calibration_name
        self.calibrate = calibrate
        self.startIndx = startIndx
        self.stopIndx = stopIndx
        self.spectralHalfWidth = spectralHalfWidth
        self.gaussianConvolve = gaussianConvolve
        self.gaussianWNsigma = gaussianWNsigma
        self.plotOn = plotOn
        self.title = title
        self.yaxis = yaxis
        self.plot_range = plot_range
        self.legend = legend
        self.plot_type = plot_type 
        self.color_scheme = color_scheme
        

    # global plotting settings
    plt.rc('font', family = 'Arial', size = 10)  # controls default text sizes
    plt.rc('axes', labelsize = 12)               # fontsize of the x and y labels
    plt.rc('xtick', labelsize = 10)              # fontsize of the tick labels
    plt.rc('ytick', labelsize = 10)              # fontsize of the tick labels
    plt.rc('legend', fontsize = 10)              # legend fontsize
    
    
    def plot_colors(self, color_scheme, plotList):
        """
        Returns a color map based on the number of plots to make and a color scheme.  
                
        Input
        ------
            color_scheme - str                   - name of the color scheme to be used 
            plotList     - int or array or list  - can be a list of plots or number of plots 
            
        Returns
        -------
            scalarMap - color map object
        
        """
        if color_scheme == 'IRsweep':
            # IRsweep style colors
            cmap = LinearSegmentedColormap.from_list('IRsweep', [
                                                            (128/255,128/255,129/255),
                                                            (0,0,0),
                                                            (237/255, 33/255,36/255)]
                                                )
        else:
            cmap = plt.get_cmap(color_scheme)
            
        if isinstance(plotList, int):
            number_of_plots = plotList
        else:
            number_of_plots = len(plotList)-1
       
        cNorm  = colors.Normalize(vmin=0, vmax=number_of_plots) 
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cmap)
        return scalarMap


    def load_proc(self, measurement_name, calibrated_calibration_name = None, calibrate = False):
        """
        Loads the data and calibrates the spectra.  
                
        Input
        ------
            measurement_name            - int  - name of the measurement 
            calibrated_calibration_name - str  - name of the calibrated calibration file 
            calibrate                   - bool - whether or not to run the calibration
            
        Returns
        -------
            none
        
        """
        if calibrated_calibration_name == None and calibrate == True:
            raise Exception("Enter a calibrated calibration name or set calibrate to False.")
        self.load_configuration(measurement_name)
        self.load_transmission()
        if calibrate == True:
            self.calibrateWNaxisOfMeasurement(calibFilename=calibrated_calibration_name, plotOn=False)  


    def find_idx(self, entries, axis): 
        """
        Finds the index of the nearest-value element in an array.
        
        Input
        ------
            entries - list of int or float     - values whose indices should be returned
            axis    - np array of int or float - array in which the entries should be found
            
        Returns
        -------
            indecies - list of int - indecies of closest elements to ones provided
        
        """

        indecies = [list(axis).index(min(axis, key=lambda x:abs(x-v))) for i, v in enumerate(entries)]
        
        return indecies


    def acquisition_plotter(self, plot_at_time, custom_data = None, time_resolution = 0, title = '', yaxis = '', plot_range = False, legend = True, plot_type = 'absorbance', color_scheme = 'IRsweep', plotOn = False, static = False):
        """
        Sends the correct data (custom input or within post processor) to either 
        the time resolved or long term plotting functions. 
        
        Input
        ------
            custom_data     - np array      - data input 
            plot_at_time    - list of float - time points at which to plot 
            time_resolution - float         - time resolution of the output
            title           - str           - label for plot
            yaxis           - str           - label for y axis
            plot_range      - bool          - whether to plot a range or individual spectra
            legend          - bool          - whether to plot the legend
            plot_type       - str           - determines the output
            plotOn          - bool          - whether to output a plot
            static          - bool          - whether to plot averaged or unaveraged data
            
        Returns
        -------
            transient      - np array      - array of all kinetic traces plotted
        
        """

        # first figure out if anything has to be done with custom plotting data
        if custom_data is None:
            if self.is_timeresolved() == False: # for TR measurements, do nothing
                if static == True:
                    custom_data = self.data['transmissionSpectralAvgOfFiles']
                else:
                    custom_data = self.data['transmissionSpectralAvgOfIndividualFiles']
        else:
            if self.is_timeresolved() == False: #for LT measurements
                if np.shape(custom_data)[1] != len(self.data['wnAxis']): 
                    raise Exception('Please make sure the input has the correct format.')
            else: #for TR measurements 
                if np.shape(custom_data)[0] != len(self.data['timeAxis']) and np.shape(custom_data)[1] != len(self.data['wnAxis']):
                    raise Exception('Please make sure the input has the correct format.')
                else: 
                    self.data.update({'transientTransSpectralAvgOfFiles':np.array(custom_data)})        
        
        if plot_type == 'unchanged':
            plot_type = 'transmission'
        
        # call the correct plotter 
        if self.is_timeresolved() == True:
            spectra,gcas = self.plot_TR(plot_at_time, time_resolution, title, yaxis, plot_range, legend, plot_type, color_scheme, plotOn)
        else: 
            if static == True:
                spectra, gcas = self.plot_static(custom_data, title, yaxis, plot_type, color_scheme, plotOn)
            else:
                spectra,gcas = self.plot_LT(custom_data, plot_at_time, title, yaxis, plot_range, legend, plot_type, color_scheme, plotOn)
            
        return spectra, gcas


    def plot_TR(self, startTime, integrationTime, title, ylabel, plot_range, legend, plot_type, color_scheme, plotOn):
        """
        Plots individual TR acquisitions based on input parameters
        
        Input
        ------
            plot_at_time    - list of float - time points at which to plot (in ms)
            integrationTime - float         - time resolution for plotted lines
            title           - str           - label for plot
            yaxis           - str           - label for y axis
            plot_range      - bool          - whether to plot a range or individual spectra
            legend          - bool          - whether to plot the legend
            plot_type       - str           - whether to and return plot 'absorbance', 'transmission', 'absorption'
            plotOn          - str           - whether to show a plot 
            
        Returns
        -------
            array of spectra plotted
        
        """
        # make sure the data getting function uses the averaged array
        self.last_data_type = 'SpectralAvgOfFiles' 
        
        # convert times to seconds
        integrationTime = integrationTime*1e-3
        startTime = np.multiply(startTime,1e-3)
        
        # ensure that integration times are at a minimum the time resolution of the measurement
        if integrationTime < self.config.interleaveTimeStep: 
            integrationTime = self.config.interleaveTimeStep 
        
        # generate range if plot_range is needed
        if plot_range == True:
            time_span = abs(max(startTime)-min(startTime)) 
            num_spec = int(np.floor(time_span/integrationTime)+1) 
            startTime = [integrationTime * (i+min(startTime)) for i in range(num_spec)] 
        
        # obtain data for plotting and convert to the appropriate format
        spectra = [self.getSpectrumWithNoiseThreshold((v),(v+integrationTime),threshold=100,plotOn=False) for v in startTime]
        spectra = self.complexToReal(self.getOutputInType(np.array(spectra), plot_type))
        
        # make sure no crazy-long legends are made
        if len(spectra) > 24:
            legend = False
            print('No legend is printed because the number of plots is too high.')
                
        color_map = self.plot_colors(color_scheme, startTime)
        plt.ioff()
        if plotOn == True:
            plt.figure()
            plt.show()
            
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel(ylabel)
        plt.title(title)
        for i, v in enumerate(spectra):
            plt.plot(self.data['wnAxis'], v, label = str('%.3f'%(np.multiply(startTime[i],1e3)))+' ms to '+str('%.3f'%(np.multiply(startTime[i]+integrationTime,1e3)))+' ms',linewidth=2,color=color_map.to_rgba(i))
            if legend == True:
                plt.legend()
        
        plt.ion()
        
        return np.array(spectra),plt.gca()
    
    
    def plot_LT(self, data, plot_at_time, title, yaxis, plot_range, legend, plot_type, color_scheme, plotOn): 
        """
        Plots individual LT acquisitions based on input parameters
        
        Input
        ------
            data         - np array      - (optional) data input
            plot_at_time - list of float - time points at which to plot
            title        - str           - label for plot
            yaxis        - str           - label for y axis
            plot_range   - bool          - whether to plot a range or individual spectra
            legend       - bool          - whether to plot the legend
            plot_type    - str           - whether to and return plot 'absorbance', 'transmission', 'absorption'
            plotOn       - str           - whether to show a plot 
            
        Returns
        -------
            array of spectra plotted
        
        """
        
        data = self.getOutputInType(data, plot_type)
        specIdx = self.find_idx(plot_at_time, self.data['timeAxis'])
        
        if plot_range == True:
            specIdx = list(range(min(specIdx), max(specIdx))) 
        
        to_plot = [data[v] for v in specIdx]
        to_plot = self.complexToReal(to_plot)
        
        # make sure no crazy-long legends are made
        if len(specIdx) > 24:
             legend = False
             print('No legend is printed because the number of plots is too high.')
                    
        color_map = self.plot_colors(color_scheme, specIdx)
        plt.ioff()
        if plotOn == True:
            plt.figure()
            plt.show()
            
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel(yaxis)  
        plt.title(title)
        for i, v in enumerate(to_plot):
            plt.plot(self.data['wnAxis'], v, label = str('%.2f'%(self.data['timeAxis'][specIdx[i]]))+' s', color=color_map.to_rgba(i))
        if legend == True:plt.legend()
        
        plt.ion()
        
        return np.array(to_plot),plt.gca()


    def plot_static(self, data, title, yaxis, plot_type, color_scheme, plotOn): 
        """
        Plots fully averaged static spectrum from transmissionSpectralAvgOfFiles
        
        Input
        ------
            data         - np array      - data input
            title        - str           - label for plot
            yaxis        - str           - label for y axis
            plot_type    - str           - whether to and return plot 'absorbance', 'transmission', 'absorption'
            plotOn       - str           - whether to show a plot 
            
        Returns
        -------
            array of spectra plotted
        
        """
        
        data = self.getOutputInType(data, plot_type)
        
        color_map = self.plot_colors(color_scheme, [0])
        plt.ioff()
        if plotOn == True:
            plt.figure()
            plt.show()
            
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel(yaxis)  
        plt.title(title)
        plt.plot(self.data['wnAxis'], data, color=color_map.to_rgba(0))
        
        plt.ion()
        
        return np.array(data),plt.gca()
    

    def transient_plotter(self, plot_at_wn, custom_input = None, time_resolution = 0, title = '', yaxis = '', offset = 0, plot_type = 'absorbance', color_scheme = 'IRsweep', plotOn = False):
        """
        Sends the correct data (custom input or within post processor) to either 
        the time resolved or long term plotting functions. 
        
        Input
        ------
            plot_data       - np array      - data input 
            plot_at_wn      - list of float - wavenumber points at which to plot
            time_resolution - float         - time resolution of the output
            title           - str           - label for plot
            yaxis           - str           - label for y axis
            offset          - float         - time offset to change timeAxis
            plot_type       - str           - determines the output
            plotOn          - bool          - whether to output a plot
            
        Returns
        -------
            transient      - np array      - array of all kinetic traces plotted
        
        """
        
        # first figure out if anything has to be done with custom plotting data
        if custom_input is None:
            if self.is_timeresolved() == False: # for TR measurements, do nothing
                custom_input = self.data['transmissionSpectralAvgOfIndividualFiles']
        else:
            if self.is_timeresolved() == False:
                if np.shape(custom_input)[1] != len(self.data['wnAxis']): 
                    raise Exception('Please make sure the input has the correct format.')
            else: #for TR measurements 
                if np.shape(custom_input)[0] != len(self.data['timeAxis']) and np.shape(custom_input)[1] != len(self.data['wnAxis']):
                    raise Exception('Please make sure the input has the correct format.')
                else: 
                    self.data.update({'transientTransSpectralAvgOfFiles':np.array(custom_input)})
                    
        if plot_type == 'unchanged':
            plot_type = 'transmission'

        # call the correct plotter, depending on the type of measurement
        if self.is_timeresolved() == True:
            transient, gcas = self.transient_plotter_TR(plot_at_wn, time_resolution, title, yaxis, offset, plot_type, color_scheme, plotOn)
        else: 
            transient, gcas = self.transient_plotter_LT(custom_input, plot_at_wn, title, yaxis, offset, plot_type, color_scheme, plotOn)
            
        return transient, gcas


    def transient_plotter_TR(self, centerWn, timeResolution, title, yaxis, offset, plot_type, color_scheme, plotOn):
        """
        Plots kinetic transients of TR measurement based on input parameters.
        Also updates timeAxis based on offset.
        
        Input
        ------
            centerWn       - list of float - wavenumber points at which to plot
            timeResolution - float         - time resolution of the output
            title          - str           - label for plot
            yaxis          - str           - label for y axis
            offset         - float         - time offset to change timeAxis
            plot_type      - str           - determines the output
            plotOn         - bool          - whether to output a plot
            
        Returns
        -------
            transient      - np array      - array of all kinetic traces plotted
        
        """
        self.last_data_type = 'SpectralAvgOfFiles' 
        
        # convert to seconds
        timeResolution = timeResolution*1e-3
        offset = offset*1e-3
        
        # ensure that integration times are at a minimum the time resolution of the measurement
        if timeResolution < self.config.interleaveTimeStep: 
            timeResolution = self.config.interleaveTimeStep 

        TimeMovingAverage = int(round(timeResolution/self.config.interleaveTimeStep))  
        
        # apply offset to time axis and ensure that it can be done repeatedly
        self.time_axis_offset = np.array(np.subtract(self.data['timeAxis'], offset)) 
        
        # generate transient data
        transient = [self.getTransientWithLinTime(v,v,averaging=1,interleave=TimeMovingAverage,plotOn=False)[0] for v in centerWn]
        
        # get output in correct type
        transient = self.getOutputInType(transient, plot_type) 
        transient = self.complexToReal(transient)
        
        color_map = self.plot_colors(color_scheme, centerWn)
        plt.ioff()
        if plotOn == True:
            plt.figure()
            plt.show()
            
        plt.xlabel('Time [ms]')
        plt.ylabel(yaxis)
        plt.title(title)
        for i, v in enumerate(transient):
            plt.plot(self.time_axis_offset*1e3, v, label = str(round((centerWn[i]), 1))+' cm$^{-1}$', linewidth=2, color=color_map.to_rgba(i))
            plt.legend()
        
        plt.ion()
        
        return transient,plt.gca()
    
    
    def transient_plotter_LT(self, plot_data, plot_at_wn, title, yaxis, offset, plot_type, color_scheme, plotOn):
        """
        Plots kinetic transients of LT measurement based on input parameters.
        Also updates timeAxis based on offset.
        
        Input
        ------
            plot_data  - np array      - data input 
            plot_at_wn - list of float - wavenumber points at which to plot
            title      - str           - label for plot
            yaxis      - str           - label for y axis
            offset     - float         - time offset to change timeAxis
            plot_type  - str           - determines the output
            plotOn     - bool          - whether to output a plot
            
        Returns
        -------
            kin        - np array      - array of all kinetic traces plotted
        
        """
        # update timeAxis
        try:
            self.time_axis_offset = np.subtract(self.data['timeAxis'], offset)
        except:
            self.time_axis_offset = np.subtract(self.data['timeStamp'], offset)
        
        plot_data = self.getOutputInType(plot_data, plot_type)
        peakIdx = self.find_idx(plot_at_wn, self.data['wnAxis'])
        
        kin = np.transpose(plot_data[:,peakIdx])
        kin = self.complexToReal(kin)
        
        plt.ioff()
        if plotOn == True:
            plt.figure()
            plt.show()
            
        plt.xlabel('Time [s]')
        plt.ylabel(yaxis)
        plt.title(title)
        color_map = self.plot_colors(color_scheme, kin)
        for i, v in enumerate(kin):
            plt.plot(self.time_axis_offset, v, label = str(round(self.data['wnAxis'][peakIdx[i]],1))+' cm$^{-1}$', color=color_map.to_rgba(i)) 
            plt.legend()
        
        plt.ion()
        
        return np.array(kin),plt.gca()



        