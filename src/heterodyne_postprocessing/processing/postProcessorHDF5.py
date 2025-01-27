# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os
import sys
import numpy as np
import h5py

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from heterodyne_postprocessing.configurations.configurationprocessed import ConfigurationProcessed
from heterodyne_postprocessing.misc.hdf5Class import HDF5Class


class PostProcessorHDF5Loader:
    def __init__(self):
        """
        Constructor of the processor.
        """
        self.config = None

        # Variable containing all the different values
        self.data = None

        self.data_name = None
        self.last_data_type = None

        self.hdf5Help = HDF5Class()

    def load_configuration(self, filename=None):
        self.config = ConfigurationProcessed()
        self.config.load_configuration(filename)

    def load_transmission(self):
        if self.config is None:
            raise RuntimeError('in PostProcessor.load_transmission : config not yet loaded.')

        f = h5py.File(self.config.filename, 'r')
        transInfoKeys = f['transmission/info'].keys()
        self.data = {}
        self.data.update({'wnAxis': f['info/first_wn_axis'][()]})

        if 'peakstd' in transInfoKeys:
            self.data.update({'stdPeak': f['transmission/info/peakstd'][()]})

        if self.is_timeresolved():
            self.data_name = 'transientTrans'
            first_acq = 'acquisition' + str(self.hdf5Help.get_name_from_index(f['transmission'], 0))
            self.data.update({'timeAxis': f['transmission/' + first_acq + '/time'][()]})
        elif self.is_timeintegrated():
            self.data_name = 'transmission'

        self.last_data_type = ''

        acq_order = []

        # first define the order in which the acquisitions were acquired
        for g in f['transmission'].values():
            if 'acquisition' in g.name:
                acq_order.append(int(''.join(filter(str.isdigit,
                                                    g.name))))  # this can break if acquisitions are re-named at some point in the future
        self._acq_order = acq_order

        tmp_transmission = [0] * len(acq_order)
        time_stamp = [0] * len(acq_order)

        self._initiateArraysInPostProcH5()

        # use the above-found order to loop through and index correctly
        for i, v, in enumerate(acq_order):
            if i == 0:
                self.data.update({'peakMeanAmp': f['transmission/acquisition' + str(v)]['peakmeanamp'][()]})

            self._fillArraysInPostProcH5(f, v)
            if self.is_timeresolved():
                tmp_transmission[v] = (f['transmission/acquisition' + str(v)]['amp'][()][:, :, 0] +
                                       f['transmission/acquisition' + str(v)]['amp'][()][:, :, 1] * 1j)

            elif self.is_timeintegrated():
                transmission = f['transmission/acquisition' + str(v)]['y'][()]
                # old python processor saves transmission as a complex array,
                # old server processor saves transmission as real array but
                # both have dimension 1
                if transmission.ndim == 1:
                    tmp_transmission[v] = transmission.astype(np.complex128)
                # new python and new server processor save transmission as a 3D matrix
                # containing real and imaginary part separetely
                elif transmission.ndim == 3:
                    tmp_transmission[v] = (transmission[:, 0, 0] + transmission[:, 0, 1] * 1j)

            try:
                f['transmission/acquisition' + str(v)]['info'].attrs['TimeStamp']
            except:  # maybe an exception is not the best solution here; consider hasattr if revised
                pass
            else:
                time_stamp[v] = (f['transmission/acquisition' + str(v)]['info'].attrs['TimeStamp'][0])

        time_stamp = np.divide(time_stamp, 1e6)  # convert to seconds
        time_stamp_diff = np.array([v - time_stamp[0] for v in time_stamp])  # shift t = 0 to the first acquisition
        tmp_transmission = np.transpose(tmp_transmission)

        self.data.update({self.data_name: tmp_transmission})
        self.data.update({'numAcq': len(acq_order)})
        self.data.update({'timeStamp': time_stamp_diff})
        self.data.update({'time_UTC': time_stamp})

        if self.is_timeintegrated():
            try:
                offset = self.data['timeStamp'][self.config.pretriggerAcquisitions]
            except:
                offset = 0
                print(
                    'No pretrigger acquisitions or too many pretrigger acquisitions found. The first value of timeAxis may not start at the correct time.')
            self.data.update({'timeAxis': time_stamp_diff - offset})

        self.load_normalization(f, acq_order)
        self.load_peakStd(f, acq_order)
        self.load_driftStd(f, acq_order)

        f.close()

    def _initiateArraysInPostProcH5(self):
        pass

    def _fillArraysInPostProcH5(self, f, v):
        pass

    def load_normalization(self, f, acq_order):
        '''
        Method to load the normalization vector of time resolved data.
        '''

        if (self.config.version >= (4, 1, 0) and self.is_timeresolved()) or (self.config.version >= (5, 0, 0)):
            tmp_normalization = [0] * len(acq_order)
            for i, v, in enumerate(acq_order):
                tmp_normalization[v] = f['transmission/acquisition' + str(v)]['NormalizationVector'][()][:, 0, 0] + \
                                       f['transmission/acquisition' + str(v)]['NormalizationVector'][()][:, 0, 1] * 1j

            tmp_normalization = np.array(tmp_normalization)
            tmp_normalization = np.transpose(tmp_normalization)
            self.data.update({'normalizationVector': tmp_normalization})

    def load_peakStd(self, f, acq_order):
        '''
        Method to load the stdPeak vector of long term and stepsweep data.
        '''

        if 'peakstd' in f['transmission/acquisition0'].keys():
            tmp_stdPeak = [0] * len(acq_order)
            for i, v, in enumerate(acq_order):
                tmp_stdPeak[v] = f['transmission/acquisition' + str(v)]['peakstd'][()]

            tmp_stdPeak = np.array(tmp_stdPeak).T
            self.data.update({'stdPeakAcqs': tmp_stdPeak})

    def load_driftStd(self, f, acq_order):
        '''
        Method to load the driftStd vector of long term and stepsweep data.
        '''

        if 'driftStd' in f['transmission/acquisition0/info'].attrs.keys():
            tmp_driftStd = [0] * len(acq_order)
            for i, v, in enumerate(acq_order):
                tmp_driftStd[v] = (f['transmission/acquisition' + str(v)]['info'].attrs['driftStd'])

            tmp_driftStd = np.array(tmp_driftStd)
            self.data.update({'driftStd': tmp_driftStd})

    def data_type(self):
        if self.data is not None:
            return self.data.keys()
        else:
            return None

    def is_timeresolved(self):
        if self.config.processor == 'TimeResolved' or self.config.processor == 'OptimizedTimeResolved':
            return True
        else:
            return False

    def is_timeintegrated(self):
        if self.config.processor == 'TimeIntegrated' or self.config.processor == 'LongTerm' or self.config.processor == 'StepSweep' or self.config.processor == 'OptimizedLongTerm' or self.config.processor == 'OptimizedStepSweep':
            return True
        else:
            return False


if __name__ == '__main__':
    proc = PostProcessorHDF5Loader()
    proc.load_configuration()
    proc.load_transmission()
