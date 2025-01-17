import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider,Button
import matplotlib.gridspec as gridspec

from orangecontrib.spectroscopy.data import getx, build_spec_table

# data['wnAxisCalib'] is Iris PP Calibration wavenumber axis
# data['transmissionCalib'] is Iris PP Calibration transmission data (co-added)
# data['wnAxisReference'] is FTIR PP reference wavenumber axis
# data['transmissionReference'] is FTIR PP reference transmission


def manual_calibration(calib, reference, plotOn=False):
    """
    Generate a figure where you can slide the measurement so that it fits
    the reference measurement.

    Input   :   plotOn(bool) boolean to plot or not the calibrate measurements
    """
    flipped = False
    running = False
    final_wnAxisCalib = None


    wnAxisCalib = getx(calib)
    wnSpacing = np.mean(np.gradient(wnAxisCalib))

    #Tunable range fixed to +-50wn due to actual performance of the lasers
    minWn = np.mean(wnAxisCalib)-50
    maxWn = np.mean(wnAxisCalib)+50

    # TODO check we only have one spectrum here (i.e. already averaged)
    # or maybe just move the averaging into this "widget" to simplify the workflow
    init_transmission = calib.X[0]
    init_wn = wnAxisCalib

    last_indx = 14
    fig = plt.figure()
    gs = gridspec.GridSpec(last_indx+7,10)
    ax1 = plt.subplot(gs[0:last_indx,:])
    ax_wnslider = plt.subplot(gs[last_indx+3,:7])
    ax_spaceslider = plt.subplot(gs[last_indx+4,:7])
    ax_offslider = plt.subplot(gs[last_indx+5,:7])
    ax_ampslider = plt.subplot(gs[last_indx+6,:7])
    ax_button_reset = plt.subplot(gs[last_indx+5,8:])
    ax_button_save = plt.subplot(gs[last_indx+6,8:])
    ax_button_flip = plt.subplot(gs[last_indx+3:last_indx+5,8:])

    ax1.set_xlabel('Wavenumber [$\mathrm{cm}^{-1}$]')
    ax1.set_ylabel('Transmission')
    ax1.plot(getx(reference),reference.X[0],'b-')
    p = ax1.plot(init_wn,init_transmission,'r-')
    ax1.set_ylim([-0.05,1.05])

    wn_slider = Slider(ax_wnslider,'Center wavenumber',minWn,maxWn,valinit=np.mean(wnAxisCalib),valstep=wnSpacing/10,valfmt='%4.1f$\mathrm{cm}^{-1}$')
    spacing_slider = Slider(ax_spaceslider,'Spacing wavenumber',wnSpacing*0.75,wnSpacing*1.5,valinit=wnSpacing,valfmt='%1.3f$\mathrm{cm}^{-1}$',valstep=0.0001)
    offset_slider = Slider(ax_offslider,'Offset transmission',-0.5,0.5,valinit=0)
    amp_slider = Slider(ax_ampslider,'Amplitude transformation',0,4,valinit=1)

    button_reset = Button(ax_button_reset,'Reset',hovercolor='0.975')
    button_save = Button(ax_button_save,'Save axis')

    button_flip = Button(ax_button_flip,'Flip',hovercolor='0.975')




    def update(val):
        nonlocal flipped
        wn_center = wn_slider.val
        spacing = spacing_slider.val
        offset = offset_slider.val
        amp = amp_slider.val
        diff = init_transmission-np.mean(init_transmission)
        diff = diff*amp
        transmission = diff+np.mean(init_transmission)
        p[0].set_ydata(transmission+offset)
        wn = (np.arange(0,len(init_wn))-np.round(len(init_wn))/2)*spacing+wn_center
        if flipped:
            wn = np.flip(wn,axis=0)
        p[0].set_xdata(wn)
        fig.canvas.draw_idle()

    wn_slider.on_changed(update)
    spacing_slider.on_changed(update)
    offset_slider.on_changed(update)
    amp_slider.on_changed(update)

    def reset(event):
        wn_slider.reset()
        spacing_slider.reset()
        offset_slider.reset()
        amp_slider.reset()

    def flip(val):
        nonlocal flipped
        wn = p[0].get_xdata()
        wn = np.flip(wn,axis=0)
        p[0].set_xdata(wn)
        flipped = not flipped

    def save(event):
        nonlocal running
        nonlocal final_wnAxisCalib
        print('Wavenumber axis saved !')
        final_wnAxisCalib = p[0].get_xdata()
        running = False

    def handle_close(event):
        nonlocal running
        print('Figure closed without saving wavenumber axis!')
        running = False


    closeid = fig.canvas.mpl_connect('close_event',handle_close)

    button_reset.on_clicked(reset)
    button_save.on_clicked(save)
    button_flip.on_clicked(flip)

    running = True
    while running:
        plt.pause(0.001)

    fig.canvas.mpl_disconnect(closeid)
    plt.close(fig.number)
    return final_wnAxisCalib, flipped

if in_data and in_object:
    calib = in_data
    reference = in_object
    calibrated_wn, flipped = manual_calibration(calib, reference, plotOn=True)
else:
    print("Connect data to input / calibration data to object.")
    calibrated_wn = None

if calibrated_wn is not None:
    peakMeanAmpCalib = np.array([v.attributes['peakMeanAmp'] for v in calib.domain.attributes], ndmin=2)
    calibrated_table = build_spec_table(calibrated_wn, peakMeanAmpCalib, in_data)
    # TODO get rid of flipped attribute (results in 2 files saved instead of one)
    calibrated_table.attributes['flipped'] = flipped
    out_data = calibrated_table
else:
    out_data = None
