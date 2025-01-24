# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 - present, IRsweep AG
MIT license
"""

import os,sys
import csv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from heterodyne_postprocessing.processing.postProcessorAvg import PostProcessorAvg

import numpy as np

#from PyQt5 import QtCore
from PyQt5 import QtWidgets


class PostProcessorCSVSaver(PostProcessorAvg):
    def __init__(self):
        super().__init__()
        
        
    def avg_to_csv(self):
        
        #Ask for a filename
        filename,_ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File','',"Text files (*.txt)")
            
        data = self.data[self.data_name+'AvgOfFiles']
        header = ''
        
        np.savetxt(filename,np.transpose(data),header=header,delimiter=',')
        
    def csv_export(self,export,ToReal=True, transpose = False):
        '''
        It exports the data "export" in a CSV file in the same directory as the file is.
        Depending on the data, the time axis, WN axis, or TimeSteps axis is added.
    

        Parameters
        ----------
        export : 1d, 2d or 3d array
            An array containing the data to be exported. It could be for 
            example proc.data['transientTrans'], proc.data['transmission'],
            proc.data['transientTransAvgOfFiles'],
            proc.data['transmissionAvgOfFiles']
        ToReal : boolean, optional
            Transforms the data to real values. The default is True.
        transpose : boolean, optional
            Export the transposed data. The default is False.

        Returns
        -------
        None.

        '''
        
        if ToReal:
            data = self.complexToReal(np.array(export))
    
        else:
            data = np.array(export)
     
            
        if data.ndim == 1:
            #insert wnAxis
            try:
                WNAxis=np.squeeze(self.data['wnAxis']) 
                data = np.insert([data],[0],[WNAxis],axis=0)
            except:
                print('wnAxis and data dimentions do not match')        
            
            if transpose == True:
                # transpose data to make the result more readable for some programs
                data = np.transpose(data)
            
            with open(self.config.filename[:-18]+'_export.csv', 'w', newline='') as exptData:
                wr = csv.writer(exptData, dialect='excel', quoting=csv.QUOTE_NONE)
                for v in data:
                    wr.writerow(v)        
        
        elif data.ndim == 2:
            #insert wnAxis
       
            try:
                WNAxis=np.squeeze(self.data['wnAxis'])
                #get shape
                (row,col)=data.shape
                if row == len(WNAxis):
                    data=data.T
                data = np.insert(data,0,WNAxis,0)
            except:
                print('wnAxis and data dimentions do not match')

            try:
                tsi = np.array(np.insert(self.data['timeAxis'], 0,0,0))
            except:
                tsi = np.array(np.insert(self.data['timeStamp'], 0,0,0))
            try:
                data = np.insert(data,0,tsi,1)
            except:
                print('timeAxis and data dimensions do not match')
                
            if transpose == True:
                # transpose data to make the result more readable for some programs
                data = np.transpose(data)

            with open(self.config.filename[:-18]+'_export.csv', 'w', newline='') as exptData:
                wr = csv.writer(exptData, dialect='excel', quoting=csv.QUOTE_NONE)
                for v in data:
                    wr.writerow(v)
                    
        elif data.ndim == 3: #dim=3 time resolved, more files to generate
            for i in range(data.shape[-1]):

                #insert wnAxis
                try:
                    WNAxis=np.squeeze(self.data['wnAxis'])
                    expData = np.insert(data[:,:,i],0,WNAxis,axis=0)
                except:
                    print('wnAxis and data dimensions do not match')
                #insert timeAxis
                tsi = np.array(np.insert(self.data['timeAxis'], 0,0,0))
                try: 
                    expData = np.insert(expData,0,tsi,axis=1)
                except:
                    print('timeAxis and data dimensions do not match')
                
                if transpose == True:
                    # transpose data to make the result more readable for some programs
                    data = np.transpose(data)
                
                with open(self.config.filename[:-18]+'_export_acquisition'+str(i+1)+'.csv', 'w', newline='') as expFile:
                    wr = csv.writer(expFile, dialect='excel', quoting=csv.QUOTE_NONE, escapechar='\\')
                    for v in expData:
                        wr.writerow(v)
        else:
            print('sorry, your data input is not supported')    