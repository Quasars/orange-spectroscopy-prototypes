# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os
import sys
import h5py
import numpy as np
import re
import warnings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from heterodyne_postprocessing.misc.hdf5Class import HDF5Class


class Configuration(HDF5Class):
    """
    Class holding all the configuration parameter for the evaluation of data 
    from an HDF5 file
    """

    def __init__(self):

        super().__init__()

        # General evaluation parameters
        self.dirpath = None
        self.splitName = None
        self.filename = None

        self.processor = None
        self.version = None
        self.measureOnTrigger = None
        self.dataProcessing = None
        self.moduleID = None

        self.model = None
        self.manufacturer = None
        self.H5Version = None

        self.measureOnSingleTrigger = None
        self.driver = None
        self.numDaqAcq = None
        self.totalSampleAcquisitions = None
        self.pretriggerAcquisitions = None

        # Acquisition evaluation parameters; attributes starting with an _ have a getter and setter method below
        self.numDaqAcq = None
        self.numAvgBg = None
        self.numAvgTf = None  # None or -1 means all acquisitions
        self.numAvgSamp = None
        self._preTriggerSamples = 0  # depends on sampleRate and preTriggerTime
        self._preTriggerTime = 0  # updates preTriggerSamples
        self._backgroundIntegrationSamples = 0  # depends on sampleRate and backgroundIntegrationTime
        self._backgroundIntegrationTime = 0  # updates backgroundIntegrationSamples
        self._useBackgroundIntegrationTime = False
        self.acqFreq = None
        self._sampleRate = None  # updates df, backgroundIntegrationSamples, preTriggerSamples
        self._df = None
        self._interleaveTimeStep = None  # depends on pow2fftLength, sampleRate and pow2interleave

        # Fourier evaluation parameters
        self._pow2fftLength = 15  # updates interleaveTimeStep
        self.pow2timeTrace = None
        self._pow2interleave = 2  # updates interleaveTimeStep
        self._pow2padding = 1  # updates df

        self.loCut = None
        self.hiCut = None

        # Coefficient for beatnote and wavelength calibration
        self.centralWn = None

        # Quantitative evaluation parameters
        self.numSamp = None

        # Plotting parameters
        self.plot_first_file = True
        self.plot_drift = True

        # Processed parameters
        self.noLines = None
        self.maxPeakNo = None
        self.peakStd = None
        self.first_wn_axis = None

    # Getters ---------------------
    @property
    def preTriggerSamples(self):
        return self._preTriggerSamples

    @property
    def preTriggerTime(self):
        return self._preTriggerTime

    @property
    def backgroundIntegrationSamples(self):
        return self._backgroundIntegrationSamples

    @property
    def useBackgroundIntegrationTime(self):
        return self._useBackgroundIntegrationTime

    @property
    def backgroundIntegrationTime(self):
        return self._backgroundIntegrationTime

    @property
    def sampleRate(self):
        return self._sampleRate

    @property
    def pow2fftLength(self):
        return self._pow2fftLength

    @property
    def pow2interleave(self):
        return self._pow2interleave

    @property
    def pow2padding(self):
        return self._pow2padding

    @property
    def interleaveTimeStep(self):
        return self._interleaveTimeStep

    @property
    def df(self):
        return self._df

    # Setters ---------------------
    @preTriggerSamples.setter
    def preTriggerSamples(self, value):
        warnings.warn("preTriggerSamples should not be set directly. It is computed from sampleRate and "
                      "preTriggerTime.")

    @preTriggerTime.setter
    def preTriggerTime(self, value):
        """
        Set the pre-trigger time.
        :param value: pre-trigger time in ms
        """
        self._preTriggerTime = value * (10 ** (-3))
        self._update_preTriggerSamples()

    @backgroundIntegrationSamples.setter
    def backgroundIntegrationSamples(self, value):
        warnings.warn("backgroundIntegrationSamples should not be set directly. It is computed from sampleRate and \
                       backgroundIntegrationTime.")

    @useBackgroundIntegrationTime.setter
    def useBackgroundIntegrationTime(self, value):
        if self.useBackgroundIntegrationTime == 0 and value == 1 and self.backgroundIntegrationTime == 0:
            print(
                "You want to use the BackgroundIntegrationTime feature without indicating the "
                "backgroundIntegrationTime."
                " Please indicate a backgroundIntegrationTime.")
        self._useBackgroundIntegrationTime = value

    @backgroundIntegrationTime.setter
    def backgroundIntegrationTime(self, value):
        """
        Set the background integration time.
        :param value: background integration time in ms
        """
        if self.backgroundIntegrationTime != value and self.useBackgroundIntegrationTime == 0:
            print(
                "You changed the backgroundIntegrationTime, but the BackgroundIntegrationTime feature is off. Please "
                "indicate that you want to use the BackgroundIntegrationTime feature.")
        self._backgroundIntegrationTime = value * (10 ** (-3))
        self._update_backgroundIntegrationSamples()

    @sampleRate.setter
    def sampleRate(self, value):
        """
        Set sampling rate.
        :param value: sampling rate in samples/s
        """
        self._sampleRate = value
        self._update_preTriggerSamples()
        self._update_backgroundIntegrationSamples()
        self._update_df()

    @pow2fftLength.setter
    def pow2fftLength(self, value):
        """
        Length of the slices (= FFT length).
        :param value: log2 of the FFT length (usually 15)
        """
        self._pow2fftLength = value
        self._update_df()
        self._update_interleaveTimeStep()

    @pow2interleave.setter
    def pow2interleave(self, value):
        """
        The slices of length 2**(pow2fftLength) can be chosen to be overlapping, to avoid losing data due to windowing.
        This increases the number of slices to be processed by a factor of 2**(pow2interleave).
        :param value: log2 of the increase factor in the number of slices to be processed (example: with
        pow2interleave = 2 there are 2**2 = 4 times more slices --> the second slice overlaps by 3/4 with the first,
        the third overlaps by 2/4 with the first etc.)
        """
        self._pow2interleave = value
        self._update_interleaveTimeStep()

    @pow2padding.setter
    def pow2padding(self, value):
        """
        How much zero-padding should be applied to the time-domain data.
        :param value: log2 of the increase factor in the length of the slices (example: with pow2padding = 1 the
        length of each slice is doubled (2**pow2padding = 2) by appending zeroes).
        """
        self._pow2padding = value
        self._update_df()

    @df.setter
    def df(self, value):
        warnings.warn("df should not be set directly. It depends on sampleRate, pow2fftLength and pow2padding.")

    @interleaveTimeStep.setter
    def interleaveTimeStep(self, value):
        warnings.warn("interleaveTimeStep should not be set directly. It is computed from pow2fftLength, sampleRate "
                      "and pow2interleave.")

    # Functions that update attributes ---------------------
    def _update_preTriggerSamples(self):
        """
        Update the preTriggerSamples attribute. To be called whenever either the sampling rate or the preTriggerTime
        are changed.
        """
        self._preTriggerSamples = self._sampleRate * self._preTriggerTime

    def _update_df(self):
        """
        Update the df attribute. To be called whenever the sampling rate, the FFT length or the zero-padding length are
        changed.
        """
        self._df = self.sampleRate / (2 ** (self.pow2fftLength + self.pow2padding))

    def _update_interleaveTimeStep(self):
        """
        Update the interleaveTimeStep attribute. To be called whenever the FFT length, the sampling rate or the
        interleave factor are changed.
        """
        self._interleaveTimeStep = 2 ** self.pow2fftLength / self.sampleRate / 2 ** self.pow2interleave

    def _update_backgroundIntegrationSamples(self):
        """
        Update the backgroundIntegrationSamples attribute. To be called whenever the sampling rate or the
        backgroundIntegrationTime are changed.
        """
        self._backgroundIntegrationSamples = self._sampleRate * self._backgroundIntegrationTime

    def load_configuration(self, filename=None):
        """
        Load the information from measurement file.
        :param filename: file name
        """

        # If no filename is given, open a dir tab
        if filename is None or not os.path.exists(str(filename)):
            self.filename = self._get_dir()
        else:
            self.filename = filename

        # Test file name extension
        if re.search(r"\.h5\Z", self.filename):  # it's a HDF5 file
            with h5py.File(self.filename, 'r') as f:
                # Get the version to know how to load stuff
                try:
                    self.version = np.bytes_(f['info'].attrs['SoftwareVersion'][0]).decode()
                except:
                    try:
                        self.version = np.bytes_(f['info'].attrs['Version'][0]).decode()
                    except:
                        raise RuntimeError('in Configuration.load_configuration : no version metadata found')
                self.version = tuple(map(int, (self.version.split("."))))

                # Use the function corresponding to the version
                if (3, 2, 3) <= self.version < (3, 3, 0):
                    self.read_from_h5_v3_2_3()
                elif (3, 3, 0) <= self.version < (4, 1, 0):
                    self.read_from_h5_v3_3_0()
                elif (4, 1, 0) <= self.version < (5, 0, 0):
                    self.read_from_h5_v4_1_0()
                elif self.version >= (5, 0, 0):
                    self.read_from_h5_v5_0_0()
                else:
                    raise RuntimeError('in Configuration.load_configuration : software version not compatible.')

    def read_base_data(self):

        with h5py.File(self.filename, 'r') as f:
            self.dirpath = os.path.dirname(self.filename)
            if re.search(r"-_processed_data\.h5", self.filename):
                self.splitName = os.path.basename(re.sub(r"-_processed_data\.h5", "", self.filename))
            elif re.search(r"-_raw\.h5", self.filename):
                self.splitName = os.path.basename(re.sub(r"-_raw\.h5", "", self.filename))
            elif re.search(r"\.h5", self.filename):
                self.splitName = os.path.basename(re.sub(r"\.h5", "", self.filename))

            info = f['info']

            # General evaluation
            self.processor = np.bytes_(info.attrs['Processor'][0]).decode()
            self.moduleID = np.bytes_(info.attrs['ModuleID'][0]).decode()
            self.dataProcessing = info.attrs['DataProcessing'][0]

            # Acquisition evaluation parameters
            self.numAvgBg = info.attrs['NumberOfAveragesBackground'][0]
            self.numAvgTf = info.attrs['NumberOfAveragesTransfer'][0]
            self.numAvgSamp = info.attrs['NumberOfAveragesSample'][0]
            self.acqFreq = info.attrs['AcquisitionFrequency'][0]
            self.sampleRate = info.attrs['SampleRate'][0]
            self._preTriggerSamples = info.attrs['PreTrigSamples'][0]

            # Fourier evaluation parameters
            self.pow2fftLength = int(np.log2(info.attrs['FftLength'][0]))
            self.pow2timeTrace = int(np.log2(info.attrs['Samples'][0]))
            self.pow2interleave = int(info.attrs['Interleaving'][0])
            self.pow2padding = int(info.attrs['ZeroPadding'][0])

            try:
                self.loCut = np.float(info.attrs['loCut'][0])
                self.hiCut = np.float(info.attrs['hiCut'][0])
            except:
                print('hiCut and loCut values not found. Falling back to default.')
                self.loCut = 5E7
                self.hiCut = self.sampleRate / 2 - 5E7

            # Coefficient for wavelength calibration
            self.centralWn = info.attrs['CentralWaveNumber'][0]

    def read_from_h5_v3_2_3(self):
        """
        Read the metadata for the version release 3.2.3 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename, 'r')

        info = f['info']

        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]
        self.numDaqAcq = info.attrs['NumberDaqAcquisitions'][0]

        if 2 ** self.pow2fftLength < 2 ** self.pow2interleave:
            raise TypeError(
                "in Configuration.read_from_h5_v3_2_3 : the pow2length and interleave parameters must respect "
                "2**pow2length>=2**(interleave-1)")

        f.close()

    def read_from_h5_v3_3_0(self):
        """
        Read the metadata for the version release 3.3.0 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename, 'r')

        info = f['info']

        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]
        self.driver = info.attrs['Driver'][0]

        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]

        if 2 ** self.pow2fftLength < 2 ** self.pow2interleave:
            raise TypeError(
                "in Configuration.read_from_h5_v3_3_0 : the pow2length and interleave parameters must respect "
                "2**pow2length>=2**(interleave-1)")

        f.close()

    def read_from_h5_v4_1_0(self):
        """
        Read the metadata for the version release 4.0.0 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename, 'r')
        info = f['info']

        self.measureOnTrigger = info.attrs['MeasureOnTrigger'][0]
        self.measureOnSingleTrigger = info.attrs['MeasureOnSingleTrigger'][0]
        self.driver = info.attrs['Driver'][0]

        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]

        if 2 ** self.pow2fftLength < 2 ** self.pow2interleave:
            raise TypeError(
                "in Configuration.read_from_h5_v4_1_0 : the pow2length and interleave parameters must respect "
                "2**pow2length>=2**(interleave-1)")

        self.model = np.bytes_(info.attrs['Model'][0]).decode()
        self.manufacturer = np.bytes_(info.attrs['Manufacturer'][0]).decode()
        self.H5Version = info.attrs['H5Version'][0]

        self._useBackgroundIntegrationTime = info.attrs['UseBackgroundIntegrationTime'][0]
        self._backgroundIntegrationTime = info.attrs['BackgroundIntegrationTime'][0]
        self._preTriggerTime = info.attrs['PretriggerTime'][0]
        self.pretriggerAcquisitions = info.attrs['PretriggerAcquisitions'][0]

        f.close()

    def read_from_h5_v5_0_0(self):
        """
        Read the metadata for the version release 4.0.0 of the server
        """

        self.read_base_data()
        f = h5py.File(self.filename, 'r')
        info = f['info']

        self.numDaqAcq = info.attrs['NumberOfMeasurementsSample'][0]
        self.totalSampleAcquisitions = info.attrs['TotalSampleAcquisitions'][0]

        if 2 ** self.pow2fftLength < 2 ** self.pow2interleave:
            raise TypeError(
                "in Configuration.read_from_h5_v4_1_0 : the pow2length and interleave parameters must respect "
                "2**pow2length>=2**(interleave-1)")

        self.model = np.bytes_(info.attrs['Model'][0]).decode()
        self.manufacturer = np.bytes_(info.attrs['Manufacturer'][0]).decode()
        self.H5Version = info.attrs['H5Version'][0]

        self._useBackgroundIntegrationTime = info.attrs['UseBackgroundIntegrationTime'][0]
        self._backgroundIntegrationTime = info.attrs['BackgroundIntegrationTime'][0]
        self._preTriggerTime = info.attrs['PretriggerTime'][0]
        self.pretriggerAcquisitions = info.attrs['PretriggerAcquisitions'][0]

        f.close()

    def require_metadata(self, list_needed):
        """
        Function that tells you if the requirement in metadata is fullfilled,
        meaning that the metadata specified are initialize and not None

        Input   :   listNeeded(list of str) a list of names of metadata
        Output  :   check(bool) a boolean telling if all the required metadata
                    are initialized and not None
        """

        for variable in list_needed:
            if getattr(self, variable) is None:
                return False

        return True

    def change_config(self, **kwargs):
        """
        Obsolete: all the attributes can now be set directly, e.g.:
            config.pow2fftLength = 16
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                warnings.warn(f"Attribute {key} does not exist in {__name__}")

    def read_ASC_PSC_configuration(self):
        """
        this method reads the moduleID and return either "ASC" or "PSC"
        """
        if self.moduleID.find('ASC') >= 0:
            name = 'ASC'
        elif self.moduleID.find('PSC') >= 0:
            name = 'PSC'
        else:
            raise RuntimeError('It is not possible to read configuration (ASC/PSC)')

        return name


if __name__ == '__main__':
    config = Configuration()
