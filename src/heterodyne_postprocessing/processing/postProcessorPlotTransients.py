# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorPlotSpectra import PostProcessorPlotSpectra

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider,Button
import matplotlib.gridspec as gridspec

from PyQt5 import QtWidgets
import numpy as np


class PostProcessorPlotTransient(PostProcessorPlotSpectra):
    def __init__(self):
        super().__init__()
        
        
    def plotTransients(self,logscale=False,mode='transmission'):
        """
        Function to plot an interactive figure allowing to plot multiple
        transient with different time scale and spectral regions.
        
        Input   :   mode(str) the type of data to plot
                    logscale(bool) the type of time scale for your plot
                    
        Output  :   final_plots(list) a list of dictionaries containing the 
                    different transients
        """
        
        fig = plt.figure(figsize=(12,7))
        plt.subplots_adjust(left = 0.175)
        gs = gridspec.GridSpec(20,10)
        
        #Definition of the different axes
        ax_main = plt.subplot(gs[0:14,:])
        ax_wnmin = plt.subplot(gs[16,0:7])
        ax_wnmax = plt.subplot(gs[17,0:7])
        ax_interleave = plt.subplot(gs[19,0:7])
        ax_smooth = plt.subplot(gs[18,0:7])
        ax_hidebutton = plt.subplot(gs[16,8:])
        ax_savebutton = plt.subplot(gs[17,8:])
        ax_export = plt.subplot(gs[18,8:])
        ax_quit = plt.subplot(gs[19,8:])
        
        
        ax_main.set_ylabel(mode)
        ax_main.set_xlabel('Time [ms]')
        
        
        init_wn_res = np.mean(np.abs(np.gradient(self.data['wnAxis'], axis=0)))
        init_time_res = np.mean(np.abs(np.gradient(self.data['timeAxis'])))
        
        #Definition of the different objects
        # slider_wnmin = Slider(ax_wnmin,'Wavenumber 1 [$\mathrm{cm^{-1}}$]',np.min(self.data['wnAxis']),np.max(self.data['wnAxis']),valinit=1/3*np.max(self.data['wnAxis']),valstep=init_wn_res/10,valfmt='%3.3f$\mathrm{cm^{-1}}$')
        # slider_wnmax = Slider(ax_wnmax,'Wavenumber 2 [$\mathrm{cm^{-1}}$]',np.min(self.data['wnAxis']),np.max(self.data['wnAxis']),valinit=2/3*np.max(self.data['wnAxis']),valstep=init_wn_res/10,valfmt='%3.3f$\mathrm{cm^{-1}}$')

        slider_wnstart = Slider(ax_wnmin,'Wavenumber start [$\mathrm{cm^{-1}}$]',np.min(self.data['wnAxis']),np.max(self.data['wnAxis']),valinit=(np.max(self.data['wnAxis'])+np.min(self.data['wnAxis']))/2,valstep=init_wn_res/10,valfmt='%3.0f $\mathrm{cm^{-1}}$')
        slider_wnint = Slider(ax_wnmax,'WN integration [$\mathrm{cm^{-1}}$]',0, 20, valinit = 2,valstep=init_wn_res/10,valfmt='%3.0f $\mathrm{cm^{-1}}$')
 
        slider_interleave= Slider(ax_interleave,'Smoothing',1,8,valinit=1,valstep=1)
        if logscale:
            slider_timestep = Slider(ax_smooth,'TimeSteps',0,100,valstep=1,valinit=40,valfmt='%3.0f')
        else:
            slider_timestep = Slider(ax_smooth,'Averaging',1,10,valstep=1,valinit=0,valfmt='%2.0f')
        
        button_save = Button(ax_savebutton,'Save transient',hovercolor='0.975')
        button_hide = Button(ax_hidebutton,'Hide transient',hovercolor='0.975')
        button_quit = Button(ax_quit,'Quit',hovercolor='0.975')
        button_export = Button(ax_export,'Export to CSV',hovercolor='0.975')
        
        
        plots = []
        
        #Definition of the plots
        if logscale:
            init_spec,time = self.getTransientWithLogTime(slider_wnstart.val,slider_wnstart.val+slider_wnint.val,slider_timestep.val,slider_interleave.val)
            init_spec = self.getOutputInType(init_spec,mode_out=mode)
            cur_plot = ax_main.semilogx(time*1e3,init_spec,linestyle='-',marker='.')
            plots.append(cur_plot)
        else:
            init_spec,time = self.getTransientWithLinTime(slider_wnstart.val,slider_wnstart.val+slider_wnint.val,slider_timestep.val,slider_interleave.val)#,slider_timestep.val,slider_interleave.val)
            init_spec = self.getOutputInType(init_spec,mode_out=mode)
            cur_plot = ax_main.plot(time*1e3,init_spec,linestyle='-',marker='.')
            plots.append(cur_plot)
            act_time_res = np.abs(np.mean(np.gradient(time*1e6)))*np.max([1,(slider_interleave.val-1)*2])
            text_resolution = ax_main.text(0,1.1,'Time resolution : '+'{:4.3f}'.format(act_time_res)+'$\mathrm{\mu s}$',transform=ax_main.transAxes)
        
        
        
        #List of dictionnary where to store the end results
        final_plots = []
        
        def update(val):
            #Get values
            minwn = slider_wnstart.val
            maxwn = slider_wnstart.val+slider_wnint.val
            step = int(slider_timestep.val)
            interleave = int(slider_interleave.val)
            #Get the spectrum and update value
            if logscale:
                 transient,time = self.getTransientWithLogTime(minwn,maxwn,step,interleave)
                 transient = self.getOutputInType(transient,mode_out=mode)
                 plots[-1][0].set_ydata(transient)
                 plots[-1][0].set_xdata(time*1e3)
            else:
                transient,time = self.getTransientWithLinTime(minwn,maxwn,step,interleave)
                transient = self.getOutputInType(transient,mode_out=mode)
                plots[-1][0].set_ydata(transient)
                plots[-1][0].set_xdata(time*1e3)
                act_time_res = np.abs(np.mean(np.gradient(time*1e6)))*np.max([1,(slider_interleave.val-1)*2])
                text_resolution.set_text('Time resolution : '+'{:4.3f}'.format(act_time_res)+'$\mathrm{\mu s}$')
            
            fig.canvas.draw_idle()
            
        slider_wnstart.on_changed(update)
        slider_wnint.on_changed(update)
        slider_timestep.on_changed(update)
        slider_interleave.on_changed(update)
        
        def save(val):
            
            #Store the current spectrum in the dictionnary
            tmp = {}
            tmp['data'] = plots[-1][0].get_ydata()
            tmp['minWn'] = slider_wnstart.val
            tmp['maxWn'] = slider_wnint.val
            tmp['time'] = plots[-1][0].get_xdata()/1e3
            tmp['timeRes'] = np.abs(np.mean(np.gradient(tmp['time'])))*slider_interleave.val
            
            final_plots.append(tmp)
            
            if logscale:
                init_spec,time = self.getTransientWithLogTime(slider_wnstart.val,slider_wnstart.val+slider_wnint.val,slider_timestep.val,slider_interleave.val)
                init_spec = self.getOutputInType(init_spec,mode_out=mode)
                cur_plot = ax_main.semilogx(time*1e3,init_spec,linestyle='-',marker='.')
                plots.append(cur_plot)
            else:
                init_spec,time = self.getTransientWithLinTime(slider_wnstart.val,slider_wnstart.val+slider_wnint.val,slider_timestep.val,slider_interleave.val)#,slider_timestep.val,slider_interleave.val)
                init_spec = self.getOutputInType(init_spec,mode_out=mode)
                new_plot = ax_main.plot(time*1e3,init_spec,linestyle='-',marker='.')
                plots.append(new_plot)
            
        button_save.on_clicked(save)
        
                        
        
        def hide(val):
            self.plot_hidden= not self.plot_hidden
            
            
            for p in plots[:-1]:
                if self.plot_hidden:
                    p[0].set_alpha(0)
                else:
                    p[0].set_alpha(1)
                    
                    
        button_hide.on_clicked(hide)
                    
            
        def export_csv(event):
            
            
            
            size = None
            #Check if all the data sets are of the same size
            for dic in final_plots:
                if size is None:
                    size = dic['time'].shape
                if dic['time'].shape != size:
                    raise RuntimeError('cannot export data with different amount of timestep in the same file.')
                    
            #Ask for a filename
            filename,_ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File','',"Text files (*.txt)")
            
            
            #Start building header and data
            header = ''
            title = '{:<24}'.format('Time [s]')
            data = np.array([final_plots[0]['time']])
            counter = 1
            for dic in final_plots:
                header += 'Transient {:3.0f} -> wavenubmer 1: {:4.2f}cm-1 - wavenumber 2: {:4.2f}cm-1 - time resolution: {:1.4e}\n'.format(counter,dic['minWn'],dic['maxWn'],dic['timeRes'])
                title += '{:<24}'.format(mode+' '+str(counter))
                data = np.vstack((data,dic['data']))
                counter +=1
            
            header +=title
            np.savetxt(filename,np.transpose(data),header=header,delimiter=',')
                
            
                    
        
        button_export.on_clicked(export_csv)
            
            
        def handle_close(event):
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
        ax.set_xlabel('Time [ms]')
        ax.set_ylabel(mode)
        
        for plot in final_plots:
            if logscale:
                ax.semilogx(plot['time']*1e3,plot['data'],label='{:4.1f}cm-1 to {:4.1f}cm-1'.format(plot['minWn'],plot['maxWn']))
            else:
                ax.plot(plot['time']*1e3,plot['data'],label='{:4.1f}cm-1 to {:4.1f}cm-1'.format(plot['minWn'],plot['maxWn']))
        ax.legend()
        
        return final_plots
        
if __name__=='__main__':
    plt.close('all')
    proc = PostProcessorPlotTransient()
    proc.load_configuration(r'C:\Users\QuentinSaudan\Documents\measurements\BR7Meas12-2018-12-07-08-53-07_processed_data.h5')
    proc.load_transmission()
    proc.acquisition_average(plotOn=False)
    proc.spectral_smoothing(5,plotOn=False) 
    proc.plotTransients(logscale=False,mode='absorbance')