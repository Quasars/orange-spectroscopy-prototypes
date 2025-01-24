# CHANGELOG
All notable changes to heterodyne_postprocessing are documentd in this file. 

## Release 7.1.2 - 2023-03-30

### Fixed
- A spectral averaging bug introduced by the fix in 7.1.1 was patched

## Release 7.1.1 - 2023-03-27

### Changed 
- Changed all np.int() to int() since the former is deprecated. Thanks to Stuart Read (CLS) for alerting us to this change
- Changed export options for IRis-Lens with long-term data. "Unprocessed" now exports one CSV file per acquisition, "Averaged" now exports the average of all acquisitions, "Spectral avg." now exports the spectrally averaged version of all acquisitions.  

### Fixed
- Fixed a bug where the plotting utilities output the wrong array 
- Fixed a bug where IRis-Lens sometimes exports the wrong array
- Removed some unneeded function imports and figures from postProcessorPlottingUtilities and postProcessorCSVSaver
- The function PostProcessorPlotSpectra.plotSpectra used to overwrite spectrally averaged data in PostProcessor.data (proc.data), leading to unexpected results when exporting data after calling this function. The plotSpectra function now does not overwrite any data.

## Release 7.1.0 - 2022-12-08

### Added
- Added the attribute ASC_phase_drift_correction to the class PostProcessorConfigurationMethods to handle the rare instances when the transmittance is computed wrongly in ASC. The attribute is inherited by the class PostProcessor (among others), which is used in the heterodyne_postprocessing/EvaluatePostProcessing.py script. Please consult the Setting phase contributions to zero in postprocessing helpdesk article for more information. 
- IRis-Lens now has the processing option "no averaging"
- IRis-Lens now has data export options of transmission or absorbance (base 10)
- The csv_export() function now takes an optional argument "transpose", allowing time/wavenumber axes to be reversed for export

### Changed 
- The python server communication has been updated:
	- Trigger settings are now changed with the function control.set_trigger()
	- control.start()and control.stop()functions introduced to emulate behavior of GUI
	- control.measureBackground() and control.measureTransfer() now work without external trigger, even when external triggering is selected
	- Any previous trigger setting is reset when the functions finish (e.g. for later use with the control.measureSample() function)
	- These functions now pause python until the acquisition is complete
	- The python communication is extended to transfer, background, and time resolved measurements 
	- Every time one of these measurements finishes,control.seenFinishedSampleis set to True
- IRis-Lens has minor cosmetic and performance improvements
- General performance improvement in computing spectral average
- Improved time resolved spectra and kinetics visualization in the postprocesssing scripts
	- Instead of Time 1 and Time 2, the sliders now show Start time and Integration time
	- Analogous change for kinetic traces
- Improved handling of time information in Long Term mode
	- Export of Long Term data now uses timeAxis instead of timeStamp 
	- timeAxis is usually the same as timeStamp, except when external trigger is used together with pretrigger acquisitions. In this case, timeAxis is adjusted so t = 0 occurs at after the pretrigger acquisitions
	- timeStamp is now a numpy array
- Migrated changelog to .md file

### Fixed
- Fixed bugs causing IRis-Lens crash between opening different files
- IRis-Lens displays the correct timescale label on the plots 
- IRis-Lens data export has the correct dimensions
- IRis-Lens applies the correct complex to real conversion before data export


## Release 7.0.0 - 2022-03-04

### Added
- Added source code for IRis-Lens (post-processing GUI). Please consult the IRis-Lens Helpdesk article for more information.
- New attribute added to the proc.datacontaining spectrally averaged individual acquisition of proc.data['transmission'] 
	- Accessible through : proc.data['transmissionSpectralAvgOfIndividualFiles']
- New attributes added to the proc.data, containing:
	- Standard deviation for each individual acquisition as proc.data['stdPeakAcqs']
	- Standard deviation of the drift calculation for each individual acquisition as proc.data['driftStd']
	- The old array proc.data['stdPeak'] has been removed

### Changed 
- All python post-processing scripts are now open-source (MIT licensed)
- Unnecessary arrays proc.data['peakMeanAmpCalib'], proc.data['stdPeakCalib'], proc.data['transmissionCalib'], proc.data['wnAxisCalib'] are now removed from proc.data after calibration is completed
- The old array proc.data['stdPeak'] has been removed


## Release 6.1.0 - 2021-08-26

### Added
- Release of python_client.py and PyToServer libraries, which allow for remote control of IRis-F1 from a Python console
	- PyToServer.py implements the low level commands for communication with the IRis control unit
	- python_client.py implements higher level commands which emulate the functions normally available via the GUI
	- Please refer to the documentation within the libraries and the IRis-F1 manual for details on available commands
- postProcessorPlottingUtilities introduced into loading chain of postProcessor
	- It implements several methods for plotting IRis-F1 data
	- All its functionality can be used by normally instantiating the postProcessor 
	- Please refer to the documentation within the library for details on available methods
- Implemented correct use of new processor metadata in postProcessor
	- All occurrences of the processor metadata work correctly with the new values ‘LongTerm’ and ‘StepSweep’

### Fixed
- postProcessorCSVSaver.py now works correctly with 3-dimensional datasets of shape (timeAxis x wnAxis x acquisitions)


## Release 5.0.0 - 2020-10-30

### Added
- Implementation of CSV export in post-processor
	- Different data can be exported as a CSV file with the call proc.csv_export(xxx) with xxx being for example 'transientTrans', 'transmission', 'transientTransAvgOfFiles', 'transmissionAvgOfFiles', …
	- In the case of a time resolved measurement, the CSV file contains the time and wavenumber axis
	- If multiple acquisitions are exported (i.e 'transientTrans'), one CSV file is made for each acquisition
	- In the case of a long term measurement, the CSV file contains the time stamp and wavenumber axis
- BackgroundIntegrationTime can be used to decouple the trigger from the background
	- If the useBackgroundIntegrationTime bool is True, the backgroundIntegrationTime is used to determine the part of the transient to calculate the standard deviation of the measurement
	
### Changed 
- Manual calibration has fine-tuning option for center wavenumber and spacing on interactive plot.
- The Gaussian averager is now prioritized over Boxcar averager in the proc.spectral_smoothing method in the PostProcessorAvg



## Release 4.1.0 - 2020-04-09

### Added
- Implementation of the new backgroundIntegrationTime feature
	- backgroundIntegrationTime, backgroundIntegrationSamples and useIndependentBackgroundIntegrationTime are directly loaded from the raw file. The same applies to pretriggerTime and pretriggerSamples
	- useIndependentBackgroundIntegrationTime is the boolean which indicates whether this new backgroundIntegrationTime feature is used or not

- Normalization vector is loaded from processed data files
	- The normalization vector contains for each wavenumber and each acquisition the value with which time-resolved data was normalized
	- The normalization vector can be used to revert normalization
- New version selector compatible with 4.0.0 and 4.1.0 was created
- Version specific reading (configuration.py) methods were created for version 4.1.0

### Changed 
Deprecated use of dataset.value removed from the code



## Release 4.0.0 - 2019-12-04

### Added


### Changed 
- Wavelength calibration separated into two steps (see EvaluatePostProcessing.py for example usage):
	- (1) manual calibration of calibration measurement
		- run with proc.calibrateWNaxisOfCalibration()
		- lets user manually change wavelength offset and spacing to fit calibration measurement to reference data in an interactive plot
		- saves the calibrated calibration measurement in a new hdf5-file with “_calibrated” keyword in the filename
	- (2) wavelength calibration of sample measurement
		- run with proc.calibrateWNaxisOfMeasurement()
		- only works with previously manually calibrated calibration measurements
		- corrects the wavenumber axis (proc.data['wnAxis']) according to the manually calibrated measurement
		- if run with plotOn=True, it plots the cross-correlated peak amplitudes for visual verification of cross-correlation.

- Python scripts adapted to correctly load the new representation of static measurements
	- The scripts correctly load the new 3 dimensional representation of static measurements
	- After loading, the data is represented as 2 dimensional array of complex numbers
		- Dimensions: [spectral lines; acquisitions]
		- Spectral lines: Size equal to number of spectral points (proc.config.noLines)
		- Acquisitions: Size equal to number of sample measurements (proc.config.numSamp)
- Post-processing of phase sensitive configuration (PSC) data implemented
- Post-processor detects configuration from module ID (proc.config.moduleID)
- Post-processor uses appropriate averaging methods for ASC and PSC data
- Post-processor takes into account underestimation of absorption caused by only one beam passing through sample in PSC
	- Use the proc.complexToReal() method for correctly transferring complex transmissions to real transmissions taking into account the measurement configuration
- Time stamps for multiple acquisitions are now extracted and can be accessed with proc.data['timeStamp']. This gives an array with each entry corresponding to an acquisition, in the order in which they were acquired

## Release 3.3.1 - 2019-07-19

### Added
Changelog established.