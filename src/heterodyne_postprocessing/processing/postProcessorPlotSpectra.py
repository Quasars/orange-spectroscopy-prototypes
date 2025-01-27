# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorTimeResolved import PostProcessorTimeResolved

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider,Button
import matplotlib.gridspec as gridspec

from PyQt5 import QtWidgets
import numpy as np
import copy

class PostProcessorPlotSpectra(PostProcessorTimeResolved):
    def __init__(self):
        super().__init__()
        
        
        self.plot_hidden=False
        
        
    def plotSpectra(self,mode='transmission'):
        """
        Function producing an interactive window allowing the plot of different
        spectra averaged over different time periods. You can also change the 
        thresholding, meaning removing noisy peaks, and adjust the spectral
        smoothing according to you needs.
        
        Input   :   mode(str) the type of data to display.
        
        Output  :   final_plots(list) a list of dictionaries containing the 
                    saved spectra
        """
        
        fig = plt.figure(figsize=(12,7))
        plt.subplots_adjust(left = 0.175)
        gs = gridspec.GridSpec(20,10)
        
        #Definition of the different axes
        ax_main = plt.subplot(gs[0:14,:])
        ax_timemin = plt.subplot(gs[16,0:7])
        ax_timemax = plt.subplot(gs[17,0:7])
        ax_thr = plt.subplot(gs[18,0:7])
        ax_smooth = plt.subplot(gs[19,0:7])
        ax_hidebutton = plt.subplot(gs[16,8:])
        ax_savebutton = plt.subplot(gs[17,8:])
        ax_export = plt.subplot(gs[18,8:])
        ax_quit = plt.subplot(gs[19,8:])

        if mode == 'absorbance':
            y_ax = 'Absorbance'
        if mode == 'transmission':
            y_ax = 'Transmission'
        elif mode == 'absorption':
            y_ax = 'Absorption'
        
        ax_main.set_ylabel(y_ax)
        ax_main.set_xlabel('Wavenumber [$\mathrm{cm^{-1}}$]')
        
        
        
        init_res = np.mean(np.abs(np.gradient(self.data['wnAxis'], axis=0)))
        
        #Definition of the different objects
        slider_time = Slider(ax_timemin,'Start Time [ms]',np.min(self.data['timeAxis'])*1e3,np.max(self.data['timeAxis'])*1e3,valinit=0,valstep=1e-3,valfmt='%3.3f ms')
        slider_inttime = Slider(ax_timemax,'Integration Time [$\mu$s]',np.gradient(self.data['timeAxis'])[0]*1e6,(max(self.data['timeAxis']))*1e6/4,valinit=4*np.gradient(self.data['timeAxis'])[0]*1e6,valstep=1e-3,valfmt='%3.0f $\mu$s')
        slider_thr = Slider(ax_thr,'Threshold',0,1,valinit=1)
        slider_smooth = Slider(ax_smooth,'Spectral resolution',init_res,40*init_res,valstep=2*init_res,valinit=10*init_res,valfmt='%1.4f $\mathrm{cm^{-1}}$')
        
        button_save = Button(ax_savebutton,'Save spectrum',hovercolor='0.975')
        button_hide = Button(ax_hidebutton,'Hide spectra',hovercolor='0.975')
        button_quit = Button(ax_quit,'Quit',hovercolor='0.975')
        button_export = Button(ax_export,'Export to CSV',hovercolor='0.975')
        
        
        #Definition of the plots
        self.spectral_smoothing(spectralHalfWidth=np.floor(slider_smooth.val/init_res/2),gaussianConvolve=False, plotOn=False,writeParameters=False)
        init_spec = self.getSpectrumWithNoiseThreshold(slider_time.val,slider_time.val+slider_inttime.val*1e-3,slider_thr.val)
        init_spec = self.getOutputInType(init_spec,mode_out=mode)
        plots = []
        cur_plot = ax_main.plot(self.data['wnAxis'],init_spec,linestyle='-',marker='.')
        plots.append(cur_plot)
        
        
        
        #List of dictionnary where to store the end results
        final_plots = []
        
        def update(val):
            #Get values
            startval = slider_time.val
            stopval = startval+slider_inttime.val*1e-3
            thrs = slider_thr.val
            #Get the spectrum and update value
            spectrum = self.getSpectrumWithNoiseThreshold(startTime=startval*1e-3,stopTime=stopval*1e-3,threshold=thrs)
            spectrum = self.getOutputInType(spectrum,mode_out=mode)

            plots[-1][0].set_ydata(spectrum)
            
            fig.canvas.draw_idle()
            
        slider_time.on_changed(update)
        slider_inttime.on_changed(update)
        slider_thr.on_changed(update)
        
        def save(val):
            
            #Store the current spectrum in the dictionnary
            tmp = {}
            tmp['data'] = plots[-1][0].get_ydata()
            tmp['time'] = slider_time.val*1e-3
            tmp['intTime'] = slider_inttime.val*1e-6
            tmp['specRes'] = slider_smooth.val
            tmp['threshold'] = slider_thr.val
            
            final_plots.append(tmp)
            
            init_spec = self.getSpectrumWithNoiseThreshold(slider_time.val*1e-3,slider_time.val*1e-3+slider_inttime.val*1e-6,slider_thr.val)
            init_spec = self.getOutputInType(init_spec,mode_out=mode)
            new_plot = ax_main.plot(self.data['wnAxis'],init_spec,linestyle='-',marker='.')
            plots.append(new_plot)
            
        button_save.on_clicked(save)
        
        def smooth(val):
            self.spectral_smoothing(spectralHalfWidth=np.floor(slider_smooth.val/init_res/2),gaussianConvolve=False, plotOn=False,writeParameters=False)
            update(val)
            
        slider_smooth.on_changed(smooth)
        
        
        def hide(val):
            self.plot_hidden= not self.plot_hidden
            
            
            for p in plots[:-1]:
                if self.plot_hidden:
                    p[0].set_alpha(0)
                else:
                    p[0].set_alpha(1)
                    
                    
        button_hide.on_clicked(hide)
                    
            
        def export_csv(event):
                    
            #Ask for a filename
            filename,_ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File','',"Text files (*.txt)")
            
            
            #Start building header and data
            header = ''
            title = '{:<24}'.format('Wavenumber [cm-1]')
            data = np.squeeze(np.array([self.data['wnAxis']]))
            counter = 1
            for dic in final_plots:
                header += 'Transient {:3.0f} -> time 1: {:1.9e}s - time 2: {:1.9e}s - spectral resolution: {:3.3f}cm-1 - threshold: {:2.3f}\n'.format(counter,dic['time'],dic['intTime'],dic['specRes'],dic['threshold'])
                title += '{:<24}'.format(mode+' '+str(counter))
                data = np.vstack((data,dic['data']))
                counter+=1
            
            header +=title
            np.savetxt(filename,np.transpose(data),header=header,delimiter=',')
                
            
                    
        
        button_export.on_clicked(export_csv)     
            
            
        def handle_close(event):
            self.spectral_smoothing(spectralHalfWidth=self.spectralHalfWidth,gaussianConvolve=self.gaussianConvolve,gaussianWNsigma=self.gaussianWNsigma,plotOn=False,writeParameters=False)
            self.running = False
            plt.close(fig.number)
            
            
        closeid = fig.canvas.mpl_connect('close_event',handle_close)
        button_quit.on_clicked(handle_close)
        
        
        self.running = True
        while self.running:
            plt.pause(0.001)   
        fig.canvas.mpl_disconnect(closeid)
        
        
        
        fig = plt.figure()
        ax = plt.subplot(1,1,1)
        ax.set_xlabel('Wavenumber [$\mathrm{cm^{-1}}$]')
        ax.set_ylabel(y_ax)
        
        for plot in final_plots:
            ax.plot(self.data['wnAxis'],plot['data'],label='{:3.3f} ms to {:3.3f} ms'.format(plot['time']*1e3,plot['time']*1e3+plot['intTime']*1e3))
        ax.legend()

        # return final_plots
            
if __name__=='__main__':
    plt.close('all')
    proc = PostProcessorPlotSpectra()
    proc.load_configuration(r'C:\Users\QuentinSaudan\Documents\measurements\TestPython\TestTR-2018-11-23-08-59-29_processed_data.h5')
    proc.load_transmission()
    proc.acquisition_average(plotOn=False)
    proc.spectral_smoothing(5,plotOn=False) 
    proc.plotSpectra(mode='transmission')