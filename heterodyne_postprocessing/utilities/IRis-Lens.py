# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

###

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (QApplication,QDialog, QGridLayout, QGroupBox, QHBoxLayout,QCheckBox,QMessageBox,QComboBox,QFileDialog,
                             QLabel, QLineEdit,QPushButton, QRadioButton,QVBoxLayout)
from PyQt5.QtCore import QCoreApplication, Qt

###

import matplotlib

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

###

import numpy as np

###
import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from heterodyne_postprocessing.processing.postProcessor import PostProcessor
import glob as glob
import csv
from threading import Thread

###

#The class that is used to embed figures
class MplCanvas(FigureCanvasQTAgg):
    """
        Class to declare a widget figure, allows to embed it in a window
    """
    def __init__(self):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
    
###

#The main widget doing all the work making the main window appear
class WidgetGallery(QDialog):
    """
        The class defining the main window
    """
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)
        
        ### In this section generic properties are defined
        self.setWindowTitle('IRis-Lens')
        self.setWindowIcon(QtGui.QIcon(os.path.join(sys.path[0],'heterodyne_postprocessing/utilities/Logo_IR.png')))
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        #self.showMaximized()
        
        ### Initial attributes declaration
        self.loaded_file = False #is a file loaded?
        self.loaded_calib = False
        self.old_plot_spectra_at_time = [[]]
        self.old_plot_kin_at_wn = [[]]
        self.start_acq = None
        self.stop_acq = None
        self.color_scheme_list = matplotlib.pyplot.colormaps()
        self.color_scheme_list.insert(0,'IRsweep')
        self.nbr_exported_plots = 0
        self.spec_popupPlot = []
        self.kin_popupPlot = []
        self.set_time_resolution_spec = 0
        self.set_time_resolution_kin = 0
        irsweep_pixmap = QtGui.QPixmap(os.path.join(sys.path[0],'heterodyne_postprocessing/utilities/Logo.png'))
        self.irsweepLogo = QLabel(self)
        self.irsweepLogo.setPixmap(irsweep_pixmap.scaled(125, 500, QtCore.Qt.KeepAspectRatio))
        
        
        #Create the main layouts
        self.createTopPanel()
        self.createBottomPanel('spectra')
        self.createBottomPanel('kinetics')
        
        ### Piece the layouts together in a grid
        mainLayout = QGridLayout()
        subTopGrid = QGridLayout()
        # subTopGrid.setColumnStretch(column, stretch)
        subTopGrid.addWidget(self.loadGroupBox, 1, 0, 1, 3)
        subTopGrid.addWidget(self.irsweepLogo, 0, 0)
        subTopGrid.addWidget(self.calibrateGroupBox, 0, 1)
        subTopGrid.addWidget(self.infoGroupBox, 0, 2)
        subTopGrid.addWidget(self.acqAveragingTopGroupBox, 0, 3, 2, 1)
        subTopGrid.addWidget(self.specAveragingTopGroupBox, 0, 4, 2, 1)
        subTopGrid.addWidget(self.optionsTopGroupBox, 0, 5, 2, 1)
        # subTopGrid.setColumnStretch(0,1)
        subTopGrid.setColumnStretch(4,3)
        
        mainLayout.addLayout(subTopGrid, 0, 0, 1, 2)
        mainLayout.addWidget(self.bottomSpecPlotGroupBox, 1, 0)
        mainLayout.addWidget(self.bottomKinPlotGroupBox, 1, 1)
        self.setLayout(mainLayout)
        
    ############################################################################################################################################################
    ############################################################################################################################################################
    ### PANELS
    ############################################################################################################################################################
    ############################################################################################################################################################
    
    def createTopPanel(self):
        """
            Method to create the top panel layout of the GUI 
        """
        ### Define the top layer panel
        
        #Create a calibrated file
        calibration_PushButton = QPushButton("Generate calibration")
        calibration_PushButton.setFixedWidth(125)
        calibration_PushButton.setToolTip('Create a calibration file. First select the calibration measurement, then select the reference file')
        
        #Loading folder containing the files
        folder_PushButton = QPushButton("Load folder")
        folder_PushButton.setFixedWidth(125)
        folder_PushButton.setToolTip('Load the folder containing measurement files')
        
        #List the files in the loaded folder
        self.file_path_cb = QComboBox()
        self.file_path_cb.setToolTip('Select the measurement file to load')
        
        #Load a calibrated file
        self.calib_PushButton = QPushButton("Apply calibration")
        self.calib_PushButton.setEnabled(False)
        self.calib_PushButton.setFixedWidth(125)
        self.calib_PushButton.setToolTip('Load a calibrated file to calibrate the current measurement')
        
        #Labels and textboxes for the acquisition averaging
        self.no_avg_tickbox = QCheckBox("No averaging")
        self.no_avg_tickbox.setChecked(False)
        self.no_avg_tickbox.setToolTip("Do not average long term measurements. For time resolved measurements, instead select the start/stop value you want to keep")
        label1 = QLabel("Start")
        self.textbox_start_idx = QLineEdit()
        self.textbox_start_idx.setFixedWidth(45)
        self.textbox_start_idx.setToolTip('Enter the start of the acquisition averaging range')
        self.textbox_start_idx.setEnabled(True)
        #
        label2 = QLabel("Stop")
        self.textbox_stop_idx = QLineEdit()
        self.textbox_stop_idx.setFixedWidth(45)
        self.textbox_stop_idx.setToolTip('Enter the end of the acquisition averaging range')
        self.textbox_stop_idx.setEnabled(True)
        
        #Labels and textboxes for the smoothing
        label3 = QLabel("Sigma ["+self.term('cm','-1')+"]")
        self.textbox_sigma = QLineEdit("0.6")
        self.textbox_sigma.setFixedWidth(30)
        self.textbox_sigma.setToolTip('Enter the sigma value to use for Gaussian averaging')
        self.textbox_sigma.setEnabled(False)
        #
        label4 = QLabel("Halfwidth [lines]")
        self.textbox_halfwidth = QLineEdit("7")
        self.textbox_halfwidth.setFixedWidth(30)
        self.textbox_halfwidth.setToolTip('Enter the halfwidth value to use for boxcar averaging')
        self.textbox_halfwidth.setEnabled(False)
        #
        #Radiobuttons to decide on the type of averaging
        self.radiobutton_gaussian = QRadioButton("Gaussian")
        self.radiobutton_gaussian.setToolTip('Use Gaussian spectral averaging')
        self.radiobutton_gaussian.setEnabled(False)
        #
        self.radiobutton_box = QRadioButton("Boxcar")
        self.radiobutton_box.setToolTip('Use boxcar spectral averaging')
        self.radiobutton_box.setEnabled(False)
        
        #Send the entered data to the back-end script
        self.update_PushButton = QPushButton("Update data")
        # self.update_PushButton.setFixedWidth(125)
        self.update_PushButton.setEnabled(False)
        self.update_PushButton.setToolTip('Update the data with the current parameters')
        self.update_PushButton.setStyleSheet("color:rgb(237, 33,36)")
        
        #Exit the instance in which the GUI is created
        quit_PushButton  = QPushButton("Quit") #rough fix to quit
        # quit_PushButton.setFixedWidth(125)
        quit_PushButton.setToolTip('Quit the program')
        
        #Display all metadata infos
        self.infos_PushButton = QPushButton("Metadata")
        self.infos_PushButton.setToolTip('Display metadata of the loaded file')
        self.infos_PushButton.setEnabled(False)
        
        #Plot the standard deviation peaks
        self.infos_std_PushButton = QPushButton("Standard deviation")
        self.infos_std_PushButton.setToolTip('Display the standard deviation as a function of wavenumber')
        self.infos_std_PushButton.setEnabled(False)
        
        #List the possible exports to a csv file
        self.export_label = QLabel("Export data")
        #
        self.export_cb = QComboBox()
        # self.export_cb.setFixedWidth(250)
        self.export_cb.setToolTip('Select whether to export averaged or unprocessed data')
        self.export_cb.setEnabled(False)
		#Export the selected array to csv
        self.export_data_PushButton = QPushButton("Export")
        # self.export_data_PushButton.setFixedWidth(125)
        self.export_data_PushButton.setToolTip('Export the selected data to a csv file')
        self.export_data_PushButton.setEnabled(False)
        
        ### Connect widgets to their functions
        calibration_PushButton.clicked.connect(self.calibrate_a_file)
        folder_PushButton.clicked.connect(self.load_folder)
        self.calib_PushButton.clicked.connect(self.load_calib)
        self.radiobutton_gaussian.clicked.connect(self.set_gaussian_average)
        self.radiobutton_box.clicked.connect(self.set_boxcar_average)
        self.update_PushButton.clicked.connect(lambda : self.post_proc_thread('averaging'))
        quit_PushButton.clicked.connect(QCoreApplication.instance().quit) #rough fix to quit
        self.export_data_PushButton.clicked.connect(self.export_data_to_csv)
        self.file_path_cb.currentIndexChanged.connect(lambda : self.post_proc_thread('load_file'))
        self.infos_PushButton.clicked.connect(self.display_metadata)
        self.infos_std_PushButton.clicked.connect(self.display_stdPeaks)
        self.no_avg_tickbox.clicked.connect(self.no_avg_change_state)
        
        ### Organize the layout
        
        self.loadGroupBox = QGroupBox("Load")
        self.calibrateGroupBox = QGroupBox("Calibrate")
        self.acqAveragingTopGroupBox = QGroupBox("Acquisition averaging")
        self.specAveragingTopGroupBox = QGroupBox("Spectral averaging")
        self.optionsTopGroupBox = QGroupBox("Options")
        self.infoGroupBox = QGroupBox("Info")
        
        #Layout for the loading and averaging top part
        main_layout_load = QHBoxLayout() #define an horizontal box to embed the widgets
        main_layout_calib = QHBoxLayout()
        main_layout_acq_averaging = QHBoxLayout()
        main_layout_spec_averaging = QHBoxLayout() #define an horizontal box to embed the widgets
        main_layout_options = QHBoxLayout()
        main_layout_info = QHBoxLayout()
        
        #Use a grid layout
        grid10 = QGridLayout()
        grid11 = QGridLayout()
        grid2 = QGridLayout()
        grid3 = QGridLayout()
        grid4 = QGridLayout()
        grid5 = QGridLayout()
        
        #Fill the two grids with the buttons
        grid10.addWidget(self.file_path_cb, 0, 1, 1, 2)
        grid10.addWidget(folder_PushButton, 0, 0)
        grid11.addWidget(calibration_PushButton, 0, 0)
        grid11.addWidget(self.calib_PushButton, 0, 1)
        
        grid2.addWidget(self.no_avg_tickbox,0,0)
        grid2.addWidget(label1, 1, 0)
        grid2.addWidget(self.textbox_start_idx, 1, 1)
        grid2.addWidget(label2, 2, 0)
        grid2.addWidget(self.textbox_stop_idx, 2, 1)
        
        grid3.addWidget(self.radiobutton_gaussian, 0, 5)
        grid3.addWidget(self.radiobutton_box, 1, 5)
        grid3.addWidget(label3, 0, 6)
        grid3.addWidget(self.textbox_sigma, 0, 7)
        grid3.addWidget(label4, 1, 6)
        grid3.addWidget(self.textbox_halfwidth, 1, 7)
        
        grid4.addWidget(self.update_PushButton, 0, 1)
        grid4.addWidget(self.export_label, 1, 0)
        grid4.addWidget(self.export_cb, 2, 0, 1, 2)
        grid4.addWidget(quit_PushButton, 0, 2)
        grid4.addWidget(self.export_data_PushButton, 2, 2)
        
        grid5.addWidget(self.infos_PushButton, 0, 2)
        grid5.addWidget(self.infos_std_PushButton, 0, 3)
        
        main_layout_load.addLayout(grid10)
        main_layout_calib.addLayout(grid11)
        main_layout_acq_averaging.addLayout(grid2)
        main_layout_spec_averaging.addLayout(grid3)
        main_layout_options.addLayout(grid4)
        main_layout_info.addLayout(grid5)
        
        self.loadGroupBox.setLayout(main_layout_load) 
        self.calibrateGroupBox.setLayout(main_layout_calib) 
        self.acqAveragingTopGroupBox.setLayout(main_layout_acq_averaging)
        self.specAveragingTopGroupBox.setLayout(main_layout_spec_averaging)
        self.optionsTopGroupBox.setLayout(main_layout_options)
        self.infoGroupBox.setLayout(main_layout_info)
        
    ###
    
    def createBottomPanel(self,panel_type):
        """
            Method to define the bottom panels of the GUI that are in charge of the plotting widgets
        """
        
        #Update the entered parameters of the plot
        plot_update_PushButton = QPushButton('Update')
        plot_update_PushButton.setMaximumWidth(75)
        plot_update_PushButton.setToolTip('Plot with the current parameters.')
        color_scheme_label = QLabel("Color scheme")
        
        if panel_type=='spectra':
            self.times_to_plot_spec_lb = QLabel()
            self.times_to_plot_spec_lb.setText("Select times")
            self.bottomSpecPlotGroupBox = QGroupBox("Plot spectra")
            self.spectra_canvas = MplCanvas()
            self.spectra_toolbar = NavigationToolbar(self.spectra_canvas, self)
            self.textbox_plotspec_times = QLineEdit()
            self.textbox_plotspec_times.setToolTip('Select time points to plot')
            self.textbox_plotspec_times.setPlaceholderText("0, 0.1, 1, ...")
            self.radiobutton_plotspec_absorbance = QRadioButton("absorbance")
            self.radiobutton_plotspec_absorbance.setToolTip('Plot absorbance (base 10)')
            self.radiobutton_plotspec_absorbance.setChecked(True)
            self.radiobutton_plotspec_absorbtion = QRadioButton("absorption")
            self.radiobutton_plotspec_absorbtion.setToolTip('Plot absorption')
            self.radiobutton_plotspec_transmission = QRadioButton("transmission")
            self.radiobutton_plotspec_transmission.setToolTip('Plot transmission')
            self.checkbox_plotspec_legend = QCheckBox("Legend")
            self.checkbox_plotspec_legend.setToolTip('Include a legend. This option is automatically disabled when too many spectra are plotted')
            self.time_resol_spec_label = QLabel("Time resolution")
            self.spec_textbox_time_resolution = QLineEdit()
            self.spec_textbox_time_resolution.setFixedWidth(65)
            self.spec_textbox_time_resolution.setToolTip('Enter the desired time resolution for integrating in the time domain (time resolved measurements only)')
            self.spec_textbox_time_resolution.setEnabled(False)
            self.spec_color_scheme_cb = QComboBox()
            self.spec_color_scheme_cb.addItems(self.color_scheme_list)
            self.spec_color_scheme_cb.setToolTip('Change the color scheme of the plot. See the matplotlib documentation on colormaps for an overview')
            self.plotspec_export_PushButton = QPushButton('Export')
            self.plotspec_export_PushButton.setToolTip('Export the currently plotted trace(s) to a csv file')
            
            #Make a popup copy of the actual plot in the figure
            self.pop_spectra_plot_PushButton = QPushButton("Pop out")
            self.pop_spectra_plot_PushButton.setToolTip('Open the figure in a separate window')
            
        elif panel_type=='kinetics':
            self.wn_to_plot_kin_lb = QLabel("Select wavenumbers ["+self.term('cm','-1')+"]")
            self.bottomKinPlotGroupBox = QGroupBox("Plot kinetics")
            self.kin_canvas = MplCanvas()
            self.kin_toolbar = NavigationToolbar(self.kin_canvas, self)
            self.textbox_kinplot_wn = QLineEdit()
            self.textbox_kinplot_wn.setToolTip('Select wavenumbers at which to plot')
            self.textbox_kinplot_wn.setPlaceholderText("1650, 1500, ...")
            self.radiobutton_kinplot_absorbance = QRadioButton("absorbance")
            self.radiobutton_kinplot_absorbance.setToolTip('Plot absorbance (base 10).')
            self.radiobutton_kinplot_absorbance.setChecked(True)
            self.radiobutton_kinplot_absorbtion = QRadioButton("absorption")
            self.radiobutton_kinplot_absorbtion.setToolTip('Plot absorption.')
            self.radiobutton_kinplot_transmission = QRadioButton("transmission")
            self.radiobutton_kinplot_transmission.setToolTip('Plot transmission.')
            self.checkbox_kinplot_legend = QCheckBox("Legend")
            self.checkbox_kinplot_legend.setToolTip('Include a legend. This option is automatically disabled when too many spectra are plotted.')
            self.time_resol_kin_label = QLabel("Time resolution")
            self.kin_textbox_time_resolution = QLineEdit()
            self.kin_textbox_time_resolution.setFixedWidth(65)
            self.kin_textbox_time_resolution.setToolTip('Enter the desired time resolution for integrating in the time domain (time resolved measurements only).')
            self.kin_textbox_time_resolution.setEnabled(False)
            self.kin_color_scheme_cb = QComboBox()
            self.kin_color_scheme_cb.addItems(self.color_scheme_list)
            self.kin_color_scheme_cb.setToolTip('Change the color scheme of the plot. See the matplotlib documentation on colormaps for an overview.')
            self.kinplot_export_PushButton = QPushButton('Export')
            
            #Make a popup copy of the actual plot in the figure
            self.pop_kin_plot_PushButton = QPushButton("Pop out")
            self.pop_kin_plot_PushButton.setToolTip('Open the figure in a separate window.')
            
        ### Connect the widgets to their functions
        
        if panel_type=='spectra':
            plot_update_PushButton.clicked.connect(lambda: self.update_plot(panel_type))
            self.pop_spectra_plot_PushButton.clicked.connect(self.pop_plot_spectra_out)
            self.plotspec_export_PushButton.clicked.connect(lambda: self.export_current_plot(panel_type))
            
        elif panel_type=='kinetics':
            plot_update_PushButton.clicked.connect(lambda: self.update_plot(panel_type))
            self.pop_kin_plot_PushButton.clicked.connect(self.pop_plot_kin_out)
            self.kinplot_export_PushButton.clicked.connect(lambda: self.export_current_plot(panel_type))
            
        ### Organize the layout
        
        main_layout = QVBoxLayout()
        grid = QGridLayout()
        grid.addWidget(color_scheme_label, 2, 0)
        
        if panel_type=='spectra':
            grid.addWidget(self.times_to_plot_spec_lb, 0, 0)
            main_layout.addWidget(self.spectra_toolbar)
            main_layout.addWidget(self.spectra_canvas)
            grid.addWidget(self.textbox_plotspec_times, 0, 1)
            grid.addWidget(self.time_resol_spec_label, 1, 0)
            grid.addWidget(self.spec_textbox_time_resolution, 1, 1)
            grid.addWidget(self.radiobutton_plotspec_absorbance, 0, 2)
            grid.addWidget(self.radiobutton_plotspec_absorbtion, 1, 2)
            grid.addWidget(self.radiobutton_plotspec_transmission, 2, 2)
            grid.addWidget(self.spec_color_scheme_cb, 2, 1)
            grid.addWidget(self.checkbox_plotspec_legend, 0, 4)
            grid.addWidget(self.pop_spectra_plot_PushButton, 2, 4)
            grid.addWidget(self.plotspec_export_PushButton, 3, 4)
            
        elif panel_type=='kinetics':
            grid.addWidget(self.wn_to_plot_kin_lb, 0, 0)
            main_layout.addWidget(self.kin_toolbar)
            main_layout.addWidget(self.kin_canvas)
            grid.addWidget(self.textbox_kinplot_wn, 0, 1)
            grid.addWidget(self.time_resol_kin_label, 1, 0)
            grid.addWidget(self.kin_textbox_time_resolution, 1, 1)
            grid.addWidget(self.radiobutton_kinplot_absorbance, 0, 2)
            grid.addWidget(self.radiobutton_kinplot_absorbtion, 1, 2)
            grid.addWidget(self.radiobutton_kinplot_transmission, 2, 2)
            grid.addWidget(self.kin_color_scheme_cb, 2, 1)
            grid.addWidget(self.checkbox_kinplot_legend, 0, 4)
            grid.addWidget(self.pop_kin_plot_PushButton, 2, 4)
            grid.addWidget(self.kinplot_export_PushButton, 3,4)
        
        grid.addWidget(plot_update_PushButton, 3, 0)
        grid.setColumnStretch(3, 1)
        #
        
        main_layout.addLayout(grid)
        
        #Initialize
        main_layout.addStretch(1)
        if panel_type=='spectra':
            self.bottomSpecPlotGroupBox.setLayout(main_layout) 
        elif panel_type=='kinetics':
            self.bottomKinPlotGroupBox.setLayout(main_layout) 
    
    ############################################################################################################################################################
    ############################################################################################################################################################
    ### THREADS
    ############################################################################################################################################################
    ############################################################################################################################################################
    
    ###
    
    def post_proc_thread(self,thread_type):
        if thread_type=='load_file':
           t1=Thread(target=self.load_proc)
           t1.start()
        elif thread_type=='averaging':
            t1=Thread(target=self.average_proc())
            t1.start()
    
    ############################################################################################################################################################
    ############################################################################################################################################################
    ### METHODS
    ############################################################################################################################################################
    ############################################################################################################################################################
    
    ###
    
    def average_proc(self):
            """
                Method to run through the proc averging methods
            """
            #Get the parameters
            if not(self.textbox_start_idx.text() == ""):
                self.start_acq = int(self.textbox_start_idx.text())
            if not(self.textbox_stop_idx.text() == ""):
                self.stop_acq = int(self.textbox_stop_idx.text())
                
            try:
                if self.radiobutton_gaussian.isChecked():
                    self.gaussianWNsigma = float(self.textbox_sigma.text())
                elif self.radiobutton_box.isChecked():
                    self.spectralHalfWidth = float(self.textbox_halfwidth.text())
                
                ### Averaging and smoothing
                self.proc.acquisition_average(startIndx = self.start_acq, stopIndx = self.stop_acq,plotOn=False)
                #
                if self.radiobutton_gaussian.isChecked():
                    self.proc.spectral_smoothing(gaussianConvolve=self.gaussianConvolve, gaussianWNsigma=self.gaussianWNsigma, plotOn=False, threshold=1)
                elif self.radiobutton_box.isChecked():
                    self.proc.spectral_smoothing(gaussianConvolve=self.gaussianConvolve, spectralHalfWidth=self.spectralHalfWidth, plotOn=False, threshold=1)
                
            except ValueError:
                msg2 = QMessageBox()
                msg2.setIcon(QMessageBox.Information)
                msg2.setText("One of the fields was not entered properly.")
                msg2.setWindowTitle("Info")
                msg2.setStandardButtons(QMessageBox.Ok)
                msg2.exec_()
            
            self.export_cb.clear()
            if self.proc.is_timeintegrated():
                self.export_cb.addItems(["Spectrally averaged data","Averaged data","Unprocessed data"])
            elif self.proc.is_timeresolved():
                self.export_cb.addItems(["Averaged data","Unprocessed data"])
            self.export_cb.setEnabled(True)
            self.export_data_PushButton.setEnabled(True)
            
    ###
    
    def calibrate_a_file(self):
        """
            Method to create a calibrated file from a reference matrice
        """
        file1, state1 = QFileDialog.getOpenFileName(self, "h5 files (*.h5)")
        if state1 and file1[-3:]==".h5":
            calibration_name = file1
            
        file2, state2 = QFileDialog.getOpenFileName(self, "h5 files (*.h5)")
        if state2 and file2[-4:]==".mat":
            reference_name = file2
            calibProc = PostProcessor()
            calibProc.load_configuration(calibration_name)
            calibProc.load_transmission()
            calibProc.calibrateWNaxisOfCalibration(calibFilename=calibration_name, refFilename=reference_name, plotOn=False)
        
    ###
    
    def char_to_float(self,word):
        """
            Function to convert a string to a list of floats
            
            Input   : word - string to convert
            
            Output  : a list of floats of all numbers in word
        """
        w_numbers = []
        w_number = ''
        for index in range(len(word)):
            if word[index] != ',':
                w_number = w_number + word[index]
            else:
                w_numbers.append(w_number)
                w_number = ''
        w_numbers.append(w_number)
        return [float(i) for i in w_numbers]
    
    
    ###
    
    def check_format_float_list(self,string):
        """
            Function verifing that the format entered is that of numbers, comas, points, and spacing only
            
            Input   :   string to verify
            
            Output  :   boolean to verify the format of the entered string
            """
        char_list = ["0","1","2","3","4","5","6","7","8","9",".",","," "]
        matched_list = [char in char_list for char in string]
        return all(matched_list)
        
    ###
    
    def display_metadata(self):
        """
            Method to display the metadatas infos
        """
        self.infosPopup = QDialog()
        grid = QGridLayout()
        
        metadatas = self.proc.config.__dict__
        row, col = 0, 0
        for name,dict_ in metadatas.items():
            if not name=='filename':
                temp = QLabel(name+': '+str(dict_), self.infosPopup)
                grid.addWidget(temp, row, col)
                row = row+1
                if row==15:
                    row=0
                    col=col+1
        
        self.infosPopup.setLayout(grid)
        self.infosPopup.show()
        
    ###
    
    def display_stdPeaks(self):
        """
            Method to plot the standard deviation peaks
        """
        #self.stdGraphPopup = stdGraph(self.proc)
        self.stdGraph = QDialog()
        layout = QVBoxLayout()
        stdPeaksGraph = MplCanvas()
        toolbar = NavigationToolbar(stdPeaksGraph, self)
        layout.addWidget(stdPeaksGraph)
        layout.addWidget(toolbar)
        self.stdGraph.setLayout(layout)
        stdPeaksGraph.axes.clear()
        if 'stdPeakAcqs' in self.proc.data.keys():
            for i in range(int(self.proc.config.numSamp)):
                stdPeaksGraph.axes.plot(self.proc.data['wnAxis'],self.proc.data['stdPeakAcqs'][:,i],label=('acq. '+ str(i)),linewidth=1)
        try:        
            stdPeaksGraph.axes.plot(self.proc.data['wnAxis'],self.proc.getStdAxis(),label=('std average'),linewidth=2,color='red')
        except: #this ugly fix is only used for old files not having stdPeak for each acquisition
            stdPeaksGraph.axes.plot(self.proc.data['wnAxis'],self.proc.data['stdPeak'],label=('std average'),linewidth=2,color='red')
        stdPeaksGraph.axes.set_xlabel('Wavenumbers')
        stdPeaksGraph.axes.set_ylabel('Standard deviation')
        stdPeaksGraph.axes.legend()
        stdPeaksGraph.fig.tight_layout()
        stdPeaksGraph.draw()
        self.stdGraph.show()
    
    ###
    
    def export_current_plot(self, panel_type):
        """
        Method to export the data currently plotted on the panel type that is selected

        """
        if panel_type=='spectra':
            if self.spectra_canvas.axes.lines:
                with open(self.proc.config.filename[:-18]+'_spectra_export_'+str(self.nbr_exported_plots)+'.csv', 'w', newline='') as exptData:
                    wr = csv.writer(exptData, dialect='excel', quoting=csv.QUOTE_NONE)
                    wnAxis=np.squeeze(np.array((self.spectra_canvas.axes.lines[0].get_xdata())))
                    wr.writerow(wnAxis)
                    for i,line in enumerate(self.spectra_canvas.axes.lines):
                        to_export = np.array(line.get_ydata())
                        to_export = np.insert(to_export,0,self.plot_spectra_at_time[i])
                        wr.writerow(to_export)
                        
                self.nbr_exported_plots = self.nbr_exported_plots+1
            
        elif panel_type=='kinetics':
            if self.kin_canvas.axes.lines:
                with open(self.proc.config.filename[:-18]+'_kinetics_export_'+str(self.nbr_exported_plots)+'.csv', 'w', newline='') as exptData:
                    wr = csv.writer(exptData, dialect='excel', quoting=csv.QUOTE_NONE)
                    timeAxis=np.squeeze(np.array((self.kin_canvas.axes.lines[0].get_xdata())))
                    wr.writerow(timeAxis)
                    for i,line in enumerate(self.kin_canvas.axes.lines):
                        to_export = np.array(line.get_ydata())
                        to_export = np.insert(to_export,0,self.plot_kin_at_wn[i])
                        wr.writerow(to_export)
                        
                self.nbr_exported_plots = self.nbr_exported_plots+1
                
    
    ###
    
    def export_data_to_csv(self):
        """
            Method to export the selected data to csv
        """
        if self.proc.is_timeintegrated():
            if self.export_cb.currentText()=="Unprocessed data":
                self.data_to_csv_export=self.proc.data['transmission']
            elif self.export_cb.currentText()=="Averaged data":
                self.data_to_csv_export=self.proc.data['transmissionSpectralAvgOfFiles']
            elif self.export_cb.currentText()=="Spectrally averaged data":
                self.data_to_csv_export=self.proc.data['transmissionSpectralAvgOfIndividualFiles']
                
        elif self.proc.is_timeresolved():
            if self.export_cb.currentText()=="Unprocessed data":
                self.data_to_csv_export=self.proc.data['transientTrans']
            elif self.export_cb.currentText()=="Averaged data":
                self.data_to_csv_export=self.proc.data['transientTransSpectralAvgOfFiles']
        
        print(self.data_to_csv_export)
        self.proc.csv_export(self.data_to_csv_export)

    ###
    
    def load_calib(self):
        """
            Method to load the calibrated file of interest
        """
        file, state = QFileDialog.getOpenFileName(self, "h5 files (*.h5)")
        if state and file[-3:]==".h5":
            self.calibrated_calibration_name = file
            self.loaded_calib = True
            self.proc.calibrateWNaxisOfMeasurement(calibFilename=self.calibrated_calibration_name, plotOn=False, debug=False)   
        else:
            self.calibrated_calibration_name = None
            self.loaded_calib = False
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Something went wrong.")
            msg.setInformativeText("Check that the file extension is .h5 and try again.")
            msg.setWindowTitle("Info")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    ###
    
    def load_folder(self):
        """
            Method to load the folder containing the files of interest
        """
        dialog = QFileDialog()
        self.folder_path = dialog.getExistingDirectory(None, "Select Folder")
        self.list_of_file_path = glob.glob(self.folder_path+'/*.h5')
        list_of_file_names = [item[len(self.folder_path+'/'):] for item in self.list_of_file_path]
        list_of_file_names.insert(0,'')
        self.file_path_cb.clear() #needs to be fixed to avoid error
        self.file_path_cb.addItems(list_of_file_names)
     
    ###
    
    def load_proc(self):
        """
        Method to load the file and create the PostProcessor object

        """
        
        if not self.file_path_cb.currentText()=='':
            self.measurement_name = self.folder_path+'//'+self.file_path_cb.currentText()
            self.proc = PostProcessor()
            self.proc.load_configuration(self.measurement_name)
            self.proc.load_transmission()
            if self.proc.is_timeresolved():
                self.textbox_start_idx.setEnabled(True)
                self.textbox_stop_idx.setEnabled(True)
                self.textbox_start_idx.setText(str(0))
                self.textbox_stop_idx.setText(str(self.proc.config.numSamp-1))
                self.no_avg_tickbox.setEnabled(False) 
                self.spec_textbox_time_resolution.setEnabled(True)
                self.kin_textbox_time_resolution.setEnabled(True)
                self.times_to_plot_spec_lb.setText("Select times [ms]")
                self.time_resol_spec_label.setText("Time resolution [ms]")
                self.time_resol_kin_label.setText("Time resolution [ms]")
                self.spec_textbox_time_resolution.setText(str(round(self.proc.config.interleaveTimeStep*1e3,3)))
                self.kin_textbox_time_resolution.setText(str(round(self.proc.config.interleaveTimeStep*1e3,3)))
                self.textbox_plotspec_times.setText(str(round(self.proc.data['timeAxis'][0]*1e3,3))+','+str(round(self.proc.data['timeAxis'][-1]*1e3,3)))
            elif self.proc.is_timeintegrated():
                self.times_to_plot_spec_lb.setText("Select times [s]")
                self.time_resol_spec_label.setText("Time resolution [s]")
                self.time_resol_kin_label.setText("Time resolution [s]")
                self.no_avg_tickbox.setEnabled(True) 
                self.no_avg_tickbox.setChecked(True)
                self.textbox_start_idx.setEnabled(False)
                self.textbox_stop_idx.setEnabled(False)
                self.textbox_plotspec_times.setText(str(round(self.proc.data['timeAxis'][0],5))+','+str(round(self.proc.data['timeAxis'][-1],5)))
            self.radiobutton_gaussian.setEnabled(True)
            self.radiobutton_box.setEnabled(True)
            self.infos_PushButton.setEnabled(True)
            self.infos_std_PushButton.setEnabled(True)
            self.textbox_kinplot_wn.setText(str(round(self.proc.data['wnAxis'][self.proc.config.maxPeakNo],1)))
            self.calib_PushButton.setEnabled(True)
            
    
    ###
    
    def no_avg_change_state(self):
        """
        Changes the state of wether to average the data or not (need to update the data to apply)

        """
        if self.no_avg_tickbox.isChecked():
            self.textbox_start_idx.setEnabled(False)
            self.textbox_stop_idx.setEnabled(False)
            self.textbox_start_idx.setText("")
            self.textbox_stop_idx.setText("")
            # self.radiobutton_gaussian.setEnabled(True)
            # self.textbox_sigma.setEnabled(True)
            # self.radiobutton_box.setChecked(True)
            # self.textbox_halfwidth.setEnabled(True)
            # self.textbox_halfwidth.setText("7")
            
        if not self.no_avg_tickbox.isChecked():
            self.textbox_start_idx.setEnabled(True)
            self.textbox_stop_idx.setEnabled(True)
            self.textbox_start_idx.setText("0")
            self.textbox_stop_idx.setText(str(self.proc.config.numSamp-1))
            # self.radiobutton_gaussian.setEnabled(True)
            # self.radiobutton_box.setEnabled(True)
            # self.textbox_halfwidth.setText("7")

    ###
    
    def pop_plot_spectra_out(self):
        """
            Method to make a copy window of the current spectra plot
        """
        self.spec_popupPlot.append(QDialog())
        layout = QVBoxLayout()
        fig = MplCanvas()
        toolbar = NavigationToolbar(fig, self.spec_popupPlot[-1])
        layout.addWidget(toolbar)
        layout.addWidget(fig)
        self.spec_popupPlot[-1].setLayout(layout)
        
        for line in self.spectra_canvas.axes.lines:
            fig.axes.plot(line.get_xdata(),line.get_ydata(),color=line.get_color())
        
        
        handles, labels = self.spectra_canvas.axes.get_legend_handles_labels()
        fig.axes.legend(handles, labels)
        fig.axes.set_xlabel(self.spectra_canvas.axes.get_xlabel())
        fig.axes.set_ylabel(self.spectra_canvas.axes.get_ylabel())
        fig.draw()
            
        self.spec_popupPlot[-1].show()
        
    ###
    
    def pop_plot_kin_out(self):
        """
            Method to make a copy window of the current kinetics plot
        """
        self.kin_popupPlot.append(QDialog())
        layout = QVBoxLayout()
        fig = MplCanvas()
        toolbar = NavigationToolbar(fig, self.kin_popupPlot[-1])
        layout.addWidget(toolbar)
        layout.addWidget(fig)
        self.kin_popupPlot[-1].setLayout(layout)
        
        for line in self.kin_canvas.axes.lines:
            fig.axes.plot(line.get_xdata(),line.get_ydata(),color=line.get_color())
        
        
        handles, labels = self.kin_canvas.axes.get_legend_handles_labels()
        fig.axes.legend(handles,labels)
        fig.axes.set_xlabel(self.kin_canvas.axes.get_xlabel())
        fig.axes.set_ylabel(self.kin_canvas.axes.get_ylabel())
        fig.draw()
            
        self.kin_popupPlot[-1].show()
        
    ###
    
    def term(self,base, exponent):
        return u'{}<sup>{}</sup>'.format(base, exponent)
    
    ###
    
    def set_boxcar_average(self):
        """
            Method to set the smoothing to boxcar averaging
        """
        if self.radiobutton_box.isChecked():
            self.gaussianConvolve = False
            self.textbox_halfwidth.setEnabled(True)
            self.textbox_sigma.setEnabled(False)
            self.update_PushButton.setEnabled(True)
            
    ###
    
    def set_gaussian_average(self):
        """
            Method to set the smoothing to gaussian averaging
        """
        if self.radiobutton_gaussian.isChecked():
            self.gaussianConvolve = True
            self.textbox_sigma.setEnabled(True)
            self.textbox_halfwidth.setEnabled(False)
            self.update_PushButton.setEnabled(True)
            
    ###
    
    def update_plot(self, plotting_type):
        """
            Method in charge of updating the plot in the figure according to the entered parameters
            Input   :   plotting_type a string determining the figure to update
        """
        if plotting_type=='spectra':
            self.spectra_canvas.axes.clear()  # Clear the canvas.
            self.plot_spectra_at_time = self.char_to_float(self.textbox_plotspec_times.text())
            if not self.spec_textbox_time_resolution.text()=='':
                self.set_time_resolution_spec = float(self.spec_textbox_time_resolution.text())
            self.old_plot_spectra_at_time.append(self.plot_spectra_at_time)
                
            if(self.radiobutton_plotspec_absorbance.isChecked()):
                plot_type = self.radiobutton_plotspec_absorbance.text()
                self.spectra_canvas.axes.set_ylabel('Absorbance')
            elif(self.radiobutton_plotspec_absorbtion.isChecked()):
                plot_type = self.radiobutton_plotspec_absorbtion.text()
                self.spectra_canvas.axes.set_ylabel('Absorption')
            elif(self.radiobutton_plotspec_transmission.isChecked()):
                plot_type = self.radiobutton_plotspec_transmission.text()
                self.spectra_canvas.axes.set_ylabel('Transmission')
            
            self.spectra, spectra_gca = self.proc.acquisition_plotter(plot_at_time=self.plot_spectra_at_time, time_resolution=self.set_time_resolution_spec, plot_type=plot_type, color_scheme=self.spec_color_scheme_cb.currentText())
            
            #The drawing magic
                
            for line in spectra_gca.lines:
                self.spectra_canvas.axes.plot(line.get_xdata(),line.get_ydata(),color=line.get_color())
                #self.spectra_canvas.axes.plot.tight_layout()
            if self.checkbox_plotspec_legend.isChecked():
                handles, labels = spectra_gca.get_legend_handles_labels()
                self.spectra_canvas.axes.legend(handles,labels)
            self.spectra_canvas.axes.set_xlabel('Wavenumber [cm$^{-1}$]')
            self.spectra_canvas.draw()
            self.spectra_canvas.fig.tight_layout()
            spectra_gca.cla() #super important, delete this object
            
        elif plotting_type=='kinetics':
            
            self.kin_canvas.axes.clear()  # Clear the canvas.
            self.plot_kin_at_wn = self.char_to_float(self.textbox_kinplot_wn.text())
            if not self.kin_textbox_time_resolution.text()=='':
                self.set_time_resolution_kin = float(self.kin_textbox_time_resolution.text())
            self.old_plot_kin_at_wn.append(self.plot_kin_at_wn)
            
            if(self.radiobutton_kinplot_absorbance.isChecked()):
                plot_type = self.radiobutton_kinplot_absorbance.text()
                self.kin_canvas.axes.set_ylabel('Absorbance')
            elif(self.radiobutton_kinplot_absorbtion.isChecked()):
                plot_type = self.radiobutton_kinplot_absorbtion.text()
                self.kin_canvas.axes.set_ylabel('Absorption')
            elif(self.radiobutton_kinplot_transmission.isChecked()):
                plot_type = self.radiobutton_kinplot_transmission.text()
                self.kin_canvas.axes.set_ylabel('Transmission')
            
            self.kinetics, kin_gca = self.proc.transient_plotter(plot_at_wn=self.plot_kin_at_wn, time_resolution=self.set_time_resolution_kin, plot_type=plot_type, color_scheme=self.kin_color_scheme_cb.currentText())
            
            #The drawing magic
                
            for line in kin_gca.lines:
                self.kin_canvas.axes.plot(line.get_xdata(),line.get_ydata(),color=line.get_color())
                #self.kin_canvas.axes.plot.tight_layout()
            if self.checkbox_kinplot_legend.isChecked():
                handles, labels = kin_gca.get_legend_handles_labels()
                self.kin_canvas.axes.legend(handles,labels)
            self.kin_canvas.axes.set_xlabel('Time [ms]')
            self.kin_canvas.fig.tight_layout()
            self.kin_canvas.draw()
            kin_gca.cla() #super important, delete this object
            
        
############################################################################################################################################################
############################################################################################################################################################
### MAIN FUNCTION
############################################################################################################################################################
############################################################################################################################################################

###

def main():
   import sys

   app = QApplication(sys.argv)
   gallery = WidgetGallery()
   gallery.show()
   sys.exit(app.exec_()) 

if __name__ == '__main__':
   main()
    
        