# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorCSVSaver import PostProcessorCSVSaver

import numpy as np
import h5py
import warnings
import copy 

import scipy.io
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider,Button,TextBox
import matplotlib.gridspec as gridspec

#import absorptionSpectra.hapi as hapi

from shutil import copy2


class PostProcessorCalibration(PostProcessorCSVSaver):
    def __init__(self):
        super().__init__()
        
        self.running = False
        self.flipped = False
        
        self.calibMeasurementName = None
        self.calibReferenceName = None
        
                
    def read_calibMeasurement(self,measurement=None,specHalfWidth=0,start=None,stop=None,plotOn=False):
        """
        Function to load the calibration measurement acquired with an IRisF1 on
        a calibration sample. It is saved under 'transmissionCalib'.
        
        Input   :   measurement(str) the absolute path of the HDF5 file
                    specHalfWidth(int) the parameter for spectral averaging, 
                    which can just be set to 0 for no spectral averaging.
                    start(int) the first acquisition to average
                    stop(int) the last acqusition to average
                    plotOn(bool) a boolean to plot or not the averaging of the
                    calibaraiton data.
        """
        
        proc = PostProcessorCSVSaver()
        proc.load_configuration(measurement)
        proc.load_transmission()
        proc.acquisition_average(start,stop,plotOn=plotOn)
        proc.spectral_smoothing(specHalfWidth,plotOn=plotOn,gaussianConvolve=False)
        self.data.update({'transmissionCalib':proc.data[proc.data_name+proc.last_data_type],'wnAxisCalib':proc.data['wnAxis']})
        self.data.update({'peakMeanAmpCalib':proc.data['peakMeanAmp']})
        
        self.calibMeasurementName = proc.config.filename
    
    def read_preCalibratedMeasurement(self,measurement=None,specHalfWidth=0,start=None,stop=None,plotOn=False):
        '''
        Method to read a calibration measurement which had already been calibrated
        Input   :   measurement(str) the absolute path of the HDF5 file
                    specHalfWidth(int) the parameter for spectral averaging, 
                    which can just be set to 0 for no spectral averaging.
                    start(int) the first acquisition to average
                    stop(int) the last acqusition to average
                    plotOn(bool) a boolean to plot or not the averaging of the
                    calibaraiton data.
        '''
        self.read_calibMeasurement(measurement, specHalfWidth, start, stop, plotOn)
        
        f = h5py.File(self.calibMeasurementName,'r')
        try:
            self.flipped = f['info/calibrationFlipped'][()]
        except:
            raise AttributeError('The calibration measurement needs calibration before use')
        f.close()
        
    
    def read_calibReference(self,reference=None):
        """
        Function to load the reference measurement to perform the calibration.
        It must be at the moment a .mat file from matlab containins two fields
        calibTr, the transission, and calibWn the wavenumbers. The data is saved
        under 'transmissionReference' and 'wnAxisReference'.
        
        Input   :   reference(str) the absolute path of the reference measurement
        """
        if reference is None or not os.path.exists(reference):
            reference = self.hdf5Help._get_dir()
        calib = scipy.io.loadmat(reference)
        self.data.update({'transmissionReference':calib['calibTr'],'wnAxisReference':calib['calibWn']})
        
        self.calibReferenceName = reference
                   
        

    def calibration(self, plotOn=False):
        """
        Performs a calibration of the static measurement with respect to the 
        reference one if manualCalib is True. Otherwise loads the precalibrated static measurements.
        Then modifies the actual measurement(TR or static) with the correct wavenumber axis.
        Inputs:
            manualCalib: boolean saying, if manual calibration should be performed.
            plotOn: boolean saying, if the calibrated measurement is to be plotted.
        """
        
        self.manual_calibration()
        
        self.save_new_calibration()
        
        self.add_lag_measurement(plotOn)
        
    def calibrateWNaxisOfCalibration(self, calibFilename=None, refFilename=None, specHalfWidth=0, start=None, stop=None, plotOn=False):
        '''
        Method that let's the user manually calibrate the wavenumber axis of a calibration measurement and saves the calibrated measurement with the new wn axis.
        Inputs:
            - calibFilename: full address and filename of the calibration measurement (xxxx.h5)
            - refFilename: full address and filename of the reference spectrum (xxxx.mat)
            - specHalfWidth: smoothing width applied to the calibration measurement
            - start: start index from where to average calibration measurements
            - stop: stop index up to where to average calibration measurements
            - plotOn: whether or not to plot the calibrated data
        '''
        
        self.read_calibReference(reference = refFilename)
        self.read_calibMeasurement(measurement=calibFilename, specHalfWidth=specHalfWidth, start=start, stop=stop, plotOn=plotOn)
        self.manual_calibration()
        self.save_new_calibration()

    def calibrateWNaxisOfMeasurement(self, calibFilename=None, specHalfWidth=0, start=None, stop=None, plotOn=False, debug = False):
        '''
        Method that calibrates the wn-axis of a measurement using a previously manually calibrated calibration measurement.

        Inputs:
            - calibFilename: full address and filename of the calibration measurement
            - specHalfWidth: smoothing width applied to the calibration measurement
            - start: start index from where to average calibration measurements
            - stop: stop index up to where to average calibration measurements
            - plotOn: whether or not to plot the cross-correlated peak amplitudes
        '''
        
        self.read_preCalibratedMeasurement(measurement=calibFilename, specHalfWidth=specHalfWidth, start=start, stop=stop, plotOn=False)
        self.add_lag_measurement(plotOn=plotOn)
            
        if debug == False:
            # remove no-longer-necessary arrays to avoid confusion of user
            del self.data['peakMeanAmpCalib']
            del self.data['transmissionCalib']
            del self.data['wnAxisCalib']

            
    def add_lag_measurement(self,plotOn):
        """
        Compares the peak mean amp of the current measurement with the calibration
        one and deduce a lag which is introduced in the wnAxisCalib to create
        the correct wnAxis
        """
        
        first_wn = self.data['wnAxisCalib'][0]
        wn_spacing_calibrated = np.mean(np.gradient(np.squeeze(self.data['wnAxisCalib'])))
        corr = np.correlate(self.data['peakMeanAmpCalib'],self.data['peakMeanAmp'],'full')        
        lag = np.float(np.argmax(corr))-self.config.noLines+1
        
        new_wn = np.arange(0,self.config.noLines)*wn_spacing_calibrated
        new_wn = new_wn + first_wn
        new_wn = new_wn + lag*wn_spacing_calibrated
        
        self.data['wnAxis']=new_wn
        
        if plotOn:
            fig,ax = plt.subplots()
            ax.plot(self.data['wnAxis'], self.data['peakMeanAmp'], label='Measurement')
            ax.plot(self.data['wnAxisCalib'], self.data['peakMeanAmpCalib'], label='Calibration')
            ax.set_xlabel('Wavenumber [$\mathrm{cm}^{-1}$]')
            ax.set_ylabel('Peak Amplitude (arb.u.)')    
            ax.legend()
            ax.set_title('X-correlated peak amplitudes.')
            
    def save_new_calibration(self):
        """
        Generates a copy of the hdf5 file of the calibration measurement, in 
        which the wnAxis is modified to be the calibrated one !
        """
        if 'calibrated_processed_data.h5' not in self.calibMeasurementName:
            new_name = self.calibMeasurementName.replace('processed_data.h5','calibrated_processed_data.h5')
            copy2(self.calibMeasurementName,new_name)
        else:
            new_name = self.calibMeasurementName
            
        
        f = h5py.File(new_name,'a')
        
        del f['info/first_wn_axis'] # delete and recreate dataset to cope with axis dimension of old versions
        f.create_dataset('info/first_wn_axis', self.data['wnAxisCalib'].shape,'f8')
        f['info/first_wn_axis'][...] = self.data['wnAxisCalib']
        f['info/calibrationFlipped'] = self.flipped
        f.close()
        
        
        
    def manual_calibration(self):
        """
        Generate a figure where you can slide the measurement so that it fits
        the reference measurement.
        
        Input   :   plotOn(bool) boolean to plot or not the calibrate measurements
        """
        
        wnSpacing = np.mean(np.gradient(np.squeeze(self.data['wnAxisCalib'])))
        
        #Tunable range fixed to +-50wn due to actual performance of the lasers
        minWn = np.mean(self.data['wnAxisCalib'])-50
        maxWn = np.mean(self.data['wnAxisCalib'])+50
        
        init_transmission = self.complexToReal(self.data['transmissionCalib'])
        init_wn = self.data['wnAxisCalib']
        
        last_indx = 14
        fig = plt.figure('IRsweep - Manual Calibration',figsize=(12,7))
        plt.subplots_adjust(left = 0.175)
        gs = gridspec.GridSpec(last_indx+9,10)
        ax1 = plt.subplot(gs[0:last_indx,:])
        ax_wnslider = plt.subplot(gs[last_indx+3,:7])
        ax_box = plt.subplot(gs[last_indx+4,:7])
        ax_spaceslider = plt.subplot(gs[last_indx+5,:7])
        ax_box2 = plt.subplot(gs[last_indx+6,:7])
        ax_offslider = plt.subplot(gs[last_indx+7,:7])
        ax_ampslider = plt.subplot(gs[last_indx+8,:7])
        ax_button_reset = plt.subplot(gs[last_indx+6,8:])
        ax_button_save = plt.subplot(gs[last_indx+7,8:])
        ax_button_flip = plt.subplot(gs[last_indx+3:last_indx+4,8:])
        ax_button_text = plt.subplot(gs[last_indx+4:last_indx+6,8:])
        
        ax1.set_xlabel(r'Wavenumber [$\mathrm{cm}^{-1}$]')
        ax1.set_ylabel('Transmission')
        ax1.plot(self.data['wnAxisReference'],self.data['transmissionReference'],'#808282')
        p, = ax1.plot(init_wn,init_transmission,'#EE2125')
        ax1.set_ylim([-0.05,1.1])

        init_center_wn=np.mean(self.data['wnAxisCalib'])
        
        wn_slider = Slider(ax_wnslider,'Fine-tune WN',-0.5,+0.5,valinit=0.,valstep=1E-4,color='#808282')
        spacing_slider = Slider(ax_spaceslider,'Fine-tune Spacing',-0.05,+0.05,valinit=0.,valstep=1E-5,color='#808282')

        self.offset_text = init_center_wn
        self.offset_text2 = wnSpacing

        text_box = TextBox(ax_box, 'WN Manual Input',initial=str(np.format_float_positional(np.float(init_center_wn),3)))
        text_box2 = TextBox(ax_box2, 'Spacing Manual Input',initial=str(self.offset_text2))
        offset_slider = Slider(ax_offslider,'Amplitude Offset',-1,1,valinit=0,color='#808282')
        amp_slider = Slider(ax_ampslider,'Amplitude Scale',0.,4.,valinit=1,color='#808282')
        
        button_reset = Button(ax_button_reset,'Reset',hovercolor='0.975')
        button_save = Button(ax_button_save,'Save axis')
                
        button_flip = Button(ax_button_flip,'Flip',hovercolor='0.975')
        button_text = Button(ax_button_text,'Apply values',hovercolor='0.975')

        def update_it(event=None):  #update textbox
            self.offset_text=np.float(text_box.text)
            wn_center = copy.copy(self.offset_text)

            self.offset_text2=np.float(text_box2.text)
            spacing = self.offset_text2

            wn = (np.arange(0,len(init_wn))-np.round(len(init_wn))/2)*spacing+wn_center
            
            if self.flipped:
                wn = np.flip(wn,axis=0)
            p.set_xdata(wn)
    
        def update(val,axis): #update slider
            if axis==0:
                slider_wn_center = np.float(wn_slider.val)
                display_wn_center = np.format_float_positional(np.float(self.offset_text+slider_wn_center), 3)
                text_box.set_val(display_wn_center)
                wn_center = self.offset_text + slider_wn_center

                slider_spacing = np.float(spacing_slider.val)
                display_spacing = np.format_float_positional(np.float(self.offset_text2+slider_spacing), 3)
                text_box2.set_val(display_spacing)
                spacing = self.offset_text2 + slider_spacing

                wn = (np.arange(0,len(init_wn))-np.round(len(init_wn))/2)*spacing+wn_center
                
                if self.flipped:
                    wn = np.flip(wn,axis=0)
                p.set_xdata(wn)

            elif axis==1:

                slider_yoffset = np.float(offset_slider.val)
                amp = np.float(amp_slider.val)
                diff = init_transmission-np.nanmean(init_transmission)
                diff = diff*amp
                transmission = diff+np.nanmean(init_transmission)
                p.set_ydata(transmission+slider_yoffset)

            
            fig.canvas.draw_idle()

        wn_slider.on_changed(lambda x: update(x,0))
        spacing_slider.on_changed(lambda x: update(x,0))
        offset_slider.on_changed(lambda x: update(x,1))
        amp_slider.on_changed(lambda x: update(x,1))
        
        def reset(event):
            wn_slider.reset()
            spacing_slider.reset()
            offset_slider.reset()
            amp_slider.reset()
            text_box.set_val(np.format_float_positional(np.float(init_center_wn),3))
            text_box2.set_val(np.format_float_positional(np.float(wnSpacing),3))
            update_it()
            
        def flip(val):
            wn = p.get_xdata()
            wn = np.flip(wn,axis=0)
            p.set_xdata(wn)
            self.flipped = not self.flipped
            
        def save(event):
            print('Wavenumber axis saved !')
            self.data['wnAxisCalib'] = p.get_xdata()
            self.running = False
            
        def handle_close(event):
            print('Figure closed without saving wavenumber axis!')
            self.running = False


        closeid = fig.canvas.mpl_connect('close_event',handle_close)
        
        button_reset.on_clicked(reset)
        button_save.on_clicked(save)
        button_flip.on_clicked(flip)
        button_text.on_clicked(update_it)
        
        self.running = True
        while self.running:
            plt.pause(0.001)
            
        fig.canvas.mpl_disconnect(closeid)
        plt.close(fig.number)
        

        

            

    
if __name__ == '__main__':
    plt.close('all')
    proc = PostProcessorCalibration()
    proc.load_configuration()
    proc.load_transmission()
    proc.acquisition_average(plotOn=False)
    proc.spectral_smoothing(5,plotOn=False) 
    proc.read_calibMeasurement(specHalfWidth=0,start=None,stop=1,plotOn=False)
    proc.read_calibReference()
    proc.manual_calibration(plotOn=True)
        
        