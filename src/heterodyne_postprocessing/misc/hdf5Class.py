# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

try:
    from PyQt5 import QtWidgets

    _qt = True
except:
    _qt = False
    print('Could not import PyQt5')

import sys
import os
import re
import numpy as np


class HDF5Class:
    """
    Class implementing some function for HDF5 classes
    """

    def __init__(self):
        pass

    def _get_dir(self):
        """
        Function that asks for a path.
        
        :return : the path chosen
        :rtype : str
        """
        if _qt:
            app = QtWidgets.QApplication.instance()
            if app is None:
                app = QtWidgets.QApplication(sys.argv)

            path = QtWidgets.QFileDialog.getOpenFileName(None, 'Test Dialog', os.getcwd(), 'All Files(*.*)')[0]

            app.exec_()
        else:
            path = input('Insert the path : ')

        return path

    def get_name_from_index(self, group, acq_num):
        """
        From the number of the acquisition, we can deduce the real name of the
        acquisition by sorting them with them name
        Input   :   group(HDF5Group) an hdf5 group 
                    acq_num(int) the number of the acquisition starting from 0
                    to the total number of acquisitions
        Output  :   index(int) the index in the name of the corresponding acquisition
        """
        index = []
        for name in group.keys():
            tmp = re.search('\d+', name)
            if tmp is not None:
                index.append(int(tmp.group(0)))

        index = np.sort(index)

        if index.size == 0:
            return 0
        else:
            return int(index[int(acq_num)])

    def get_entries(self, group):
        """
        This defenition returnes the length of the index array as retrived from get_name_from_index.
        It says how many entries are in the grounp
        Input   :   group(HDF5Group) an hdf5 group 
        Output  :   entryNo(int) how many entries are in group
        """
        index = []
        for name in group.keys():
            tmp = re.search('\d+', name)
            if tmp is not None:
                index.append(int(tmp.group(0)))

        if len(index) == 0:
            return 0
        else:
            return int(len(index))
