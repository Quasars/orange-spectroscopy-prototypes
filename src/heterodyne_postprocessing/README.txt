The current package called heterodyne_postprocessing is used to post process
the data given by the IRisF1 instrument in an HDF5 file. The file should
be called XXXXXXX_processed_data.h5. 

This version of the script currently works for IRisF1 server version V3.2.3 or 
more recent.

The package contains mutiple classes, organized under submodules, and a general
script, EvalutatePostProcessing.py, which can be copied and modified according
to your needs. The different classes are using inheritence to wrap all the 
function in a single final class that you can use for multiple purposes.

########################
Structure of the package
########################

heterodyne_postprocessing
-> EvaluatePostProcessing.py    (specific script that you can copy-past in you folder and change to do whatever you want)

-> processing
    -> postProcessorHDF5           	(implements functions to load data from hdf5)
    -> postProcessorAvg     		(implements functions to average data)
    -> postProcessorCalibration    	(implements functions to calibrate spectra)
    -> postProcessorTimeResolved   	(implements functions dedicated to time resolved data)
    -> postProcessorPlotSpectra    	(implements function to plot spectra in different time ranges)
    -> postProcessorPlotTransients 	(implements function to plot transient in different wavenumber ranges)
    -> .... other classes adding new functionality ....
    -> .... other classes adding new functionality ....
    -> postProcessor  (inherits from the latest postProcessorXXXX class and is included in every specific script)
   
-> configurations
    -> configuration    (implements the base configuration loading)
    -> configurationprocessed    (implements the additonal loading for processed files)
    
-> misc
    -> hdf5Class    (implements some helping functions for hdf5 reading)
    
    
###############
Data evaluation
###############

-> add the folder containing heterodye_postprocessing to your python path
-> copy/paste the EvaluatePostProcessing.py script in another directory. 
-> change the filenames with absolute path
-> run it, either entirely or section by section

-> perform the manual calibration
-> choose the spectra you want using the interactive plot.
	-> you can also export the saved spectra to a csv file
-> choose the transients you want using the interactive plot.
	-> you can also export the saved transient to a csv file 


###############
Data Extraction 
###############

The data is stored in the main class Processor under the attribute data. It is
a dictonnary containing multiple fields : 

->  'wnAxis' is the wavenumber axis in [cm-1].

->  'timeAxis' is the axis containing the time of each slice in [s]. Only for
    time-resolved measurements.
    
->  'peakMeanAmp' is the average amplitude of the multiheterodyne peaks on the
    reference channel. 
    
->  'stdPeak' is the scaled standard deviation of each line.
 
->  'transmission' or 'transientTrans' the transmission of multiple acquisitions.
    This name is saved under proc.data_name so that you don't have to think about
    it each time you change from time resolved to static measurement.

->   proc.data_name+'AvgOfFiles' is the transmission averaged over multiple acquisitions.

->   proc.data_name+'SpectralAvgOfFiles' is the transmission spectrally averaged.

################################
Extension of the functionalities
################################

All the postProcessingXXX classes are inheriting from each other, in the order shown by the structure of the package : 
postProcessorHDF5 is the base class and PostProcessor is the end class. If you need to add some new functionality,
create a new file that you put in the processing directory. 
Inside, create a new class PostProcessingXXXX which inheritates from the lowest class but no PostProcessor. 
Add your functionality there and the modify the postProcessor file and class to include the current file and make 
PostProcessor inheriting from your new class.
Like that, any previous script using PostProcessor will still work and the class will have additional functionality.

For a more complete description, please refer to https://irsweep.atlassian.net/wiki/spaces/IR1/pages/edit/893517875?draftId=893648946&draftShareId=f733b669-483d-432e-a4b4-5e20f5b12779&

