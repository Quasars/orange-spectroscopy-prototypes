# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import sys
import os
import h5py

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from heterodyne_postprocessing.configurations.configuration import Configuration


class ConfigurationProcessed(Configuration):
    """
    Configuration for raw data file
    """

    def __init__(self):

        super().__init__()

    def read_from_h5(self):
        f = h5py.File(self.filename, 'r')
        info = f['info']
        self.noLines = info.attrs['NumberOfLines']
        try:
            self.maxPeakNo = int(info.attrs['MaxPeakC'][0])
        except:
            infodatagroup = f['transmission/info']
            self.maxPeakNo = int(infodatagroup.attrs['MaxPeakC'][0])

        self.numSamp = 0
        for g in f['transmission'].values():
            if 'acquisition' in g.name:
                self.numSamp += 1

    def read_from_h5_v3_2_3(self):
        """
        Add the loading of metadata specific to raw data.
        """

        super().read_from_h5_v3_2_3()

        self.read_from_h5()

    def read_from_h5_v3_3_0(self):
        """
        Add the loading of metadata specific to raw data.
        """

        super().read_from_h5_v3_3_0()

        self.read_from_h5()

    def read_from_h5_v4_1_0(self):
        """
        Add the loading of metadata specific to raw data.
        """

        super().read_from_h5_v4_1_0()

        self.read_from_h5()

    def read_from_h5_v5_0_0(self):
        """
        Add the loading of metadata specific to raw data.
        """

        super().read_from_h5_v5_0_0()

        self.read_from_h5()
