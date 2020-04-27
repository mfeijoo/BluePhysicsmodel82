#!/usr/bin/env python3

from PyQt5 import QtCore
import sys
import os
import time
import pyqtgraph as pg
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT,
                                                FigureCanvas)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

import atexit

import serial
import serial.tools.list_ports



colors = ['#C0392B', '#3498DB']


#Read Metadata file and load data in a dictionary
metadatafile = open('metadata.csv', 'r')
listmetadata = [pair.split(',') for pair in metadatafile.readlines()]
metadatafile.close()
dmetadata = {key:value.strip() for [key,value] in listmetadata}
metadatakeylist = [key for [key, value] in listmetadata]


#Global flag to indicate if there are measurements done
measurements_done = False


def clearLayout(layout):
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if isinstance(item, QWidgetItem):
            item.widget().setParent(None)
        else:
            layout.removeItem(item)



class EmulatorThread(QThread):
    
    def __init__(self):
        QThread.__init__(self)
        self.stop = False
        self.ser2 = serial.Serial ('/dev/pts/5', 115200, timeout=1)
        file = open('./rawdata/emulatormeasurementscounts.csv', 'r')
        self.lines =  file.readlines()
        file.close()
        
    def __del__(self):
        self.wait()
        
    def run(self):
        for line in self.lines:
            #print(line)
            self.ser2.write(line.encode())
            if self.stop:
                break
            time.sleep(0.3)
        
        self.ser2.close()
        
    def stopping(self):
        self.stop = True
        self.wait()
        self.quit()


class MeasureThread(QThread):

    info = pyqtSignal (list)

    def __init__(self):
        QThread.__init__(self)
        self.stop = False
        #emulator
        #self.ser = serial.Serial ('/dev/pts/6', 115200, timeout=1)
        self.ser = serial.Serial ('/dev/ttyS0', 115200, timeout=1)

    def __del__(self):
        self.wait()

    def run(self):
        #One reading to discard garbge
        #comment if emulator
        reading0 = self.ser.readline().decode().strip().split(',')

        #second reading to check starting time
        #comment if emulator
        reading1 = self.ser.readline().decode().strip().split(',')
        tstart = int(reading1[0])
        
        while True:
            
            if self.stop:
                break
        
            try:
                reading = self.ser.readline().decode().strip().split(',')
                #print (reading)
                #only if emulator
                #listatosend = [float(i) for i in reading]
                listatosend = [(int(reading[0])-tstart)/1000] + [float(reading[1])] + [int(i) for i  in reading[2:]]
                #print (listatosend)
                self.info.emit(listatosend)
            except:
                pass
 

            
    def stopping(self):
        self.stop = True
        self.ser.close()
        self.wait()
        self.quit()
                   
       
class MainMenu (QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("mainmenugui.ui", self)
        self.mymeasure = Measure()
        self.mymetadata = Metadata()
        self.myanalyze = Analyze()
        self.signals()
        self.setwindowstitle()
        
    def setwindowstitle(self):
        windowstitle = 'Blue Physics Model 8.2.1 File: %s' %(dmetadata['File Name'])
        self.setWindowTitle(windowstitle)
        self.mymeasure.setWindowTitle(windowstitle)
        self.mymetadata.setWindowTitle(windowstitle)
        self.myanalyze.setWindowTitle('Blue Physics Model 8.2.1 Analyze File:')
       
    def signals(self):
        self.tbmeasure.clicked.connect(self.showmeasure)
        self.tboff.clicked.connect(app.quit)
        self.tbsettings.clicked.connect(self.showmetadata)
        self.tbanalyze.clicked.connect(self.showanalyze)
        
    def showanalyze(self):
        self.close()
        self.myanalyze.show()
        
    def showmetadata(self):
        self.close()
        self.mymetadata.show()
        
    def showtemp(self):
        self.close()
        self.mytemp.show()
    
    def showvoltage(self):
        self.close()
        self.myvoltage.show()
   
    def showmeasure(self):
        self.close()
        self.mymeasure.show()
        


class Analyze (QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("analyzegui.ui", self)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        #self.canvas.figure.set_tight_layout(True)
        self.addToolBar(NavigationToolbar2QT(self.canvas, self))
        self.ax1, self.ax2 = self.figure.subplots(2, 1, sharex=True)
        #self.ax1.grid(True)
        #self.ax2.grid(True)
        #self.ax1.legend()
        #self.ax2.legend()
        self.figure.set_tight_layout(True)
        self.ax2.set_xlabel('time (s)')
        self.horizontalLayout.insertWidget(0, self.canvas)
        self.signals()
        self.relfileloaded = False
        self.plot1buttons = [self.tbviewch0, self.tbviewch1]
        
        
    def signals(self):
        self.tbmainmenuanalyze.clicked.connect(self.backtomainmenu)
        self.tbreffile.clicked.connect(self.selectfile)
        self.tbviewch0.clicked.connect(self.plot1)
        self.tbviewch1.clicked.connect(self.plot1)
        self.tbviewraw.clicked.connect(self.plot1)
        self.tbintegral.clicked.connect(self.plot1)
        self.tbtempcorrec.clicked.connect(self.plot1)
        self.tbcalibration.clicked.connect(self.plot1)
        self.cbsecondplot.currentIndexChanged.connect(self.plot2)
        self.tbrelfile.clicked.connect(self.relfile)

    def relfile(self):
        if self.tbrelfile.isChecked():
            #a funciton to load a second relative file to compare
            #with reference file loaded as self.df
            relfilename = QFileDialog.getOpenFileName(self, 'Open file',
                                                      './rawdata')
            self.dfrel = pd.read_csv(relfilename[0], skiprows=34)
            
            #flag to inidcate we have a relative file loaded
            self.relfileloaded = True

            #A routine to calculate the relative time with the reference
            #measurement under self.df
            self.dfrel['ch1reldiff'] = self.dfrel.ch1.diff()
            self.trs = self.dfrel.loc[self.dfrel.ch1reldiff == self.dfrel.ch1reldiff.max(), 'time'].item()
            timediff = self.trs - self.ts
            self.dfrel['newtimerel'] = self.dfrel.time - timediff
            
            #Calculate start and end of radiation
            #Assuming ch1 is where the sensor is and it has the largest differences
            self.trf = self.dfrel.loc[self.dfrel.ch1reldiff == self.dfrel.ch1reldiff.min(), 'time'].item()
             
            #calculate correction to temperature
            self.dfrel['ch0tc'] = self.dfrel.ch0
            self.dfrel['ch1tc'] = self.dfrel.ch1
            self.dfrel.loc[self.dfrel.ch0<6.26, 'ch0tc'] = self.dfrel.ch0 - (-0.012 * self.dfrel.ch0 + 0.075) * (self.dfrel.temp - 26.8)
            self.dfrel.loc[self.dfrel.ch1<6.26, 'ch1tc'] = self.dfrel.ch1 - (-0.012 * self.dfrel.ch1 + 0.075) * (self.dfrel.temp - 26.8)
                
            #calculate the zeros
            #print ('mean zero ch0tc: %.3f' %(self.dfa.loc[(self.dfa.time<ts)|(self.dfa.time>tf), 'ch0tc'].mean()))
            self.dfrel['ch0ztc'] = self.dfrel.ch0tc - self.dfrel.loc[(self.dfrel.time<self.trs)|(self.dfrel.time>self.trf), 'ch0tc'].mean()
            self.dfrel['ch1ztc'] = self.dfrel.ch1tc - self.dfrel.loc[(self.dfrel.time<self.trs)|(self.dfrel.time>self.trf), 'ch1tc'].mean()
            
            self.dfrel['ch0z'] = self.dfrel.ch0 - self.dfrel.loc[(self.dfrel.time<self.trs)|(self.dfrel.time>self.trf), 'ch0'].mean()
            self.dfrel['ch1z'] = self.dfrel.ch1 - self.dfrel.loc[(self.dfrel.time<self.trs)|(self.dfrel.time>self.trf), 'ch1'].mean()
                
            #calculate integrals not corrected
            self.relintch0tc = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch0ztc'].sum()
            self.relintch1tc = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch1ztc'].sum()
            
            self.absdosenocalibtcrel = self.relintch1tc - self.relintch0tc
            self.reldosenocalibtcrel = (self.absdosenocalibtcrel / float(dmetadata['Reference diff Voltage'])) * 100 
            
            self.relintch0 = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch0z'].sum()
            self.relintch1 = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch1z'].sum()
            
            self.absdosenocalibrel = self.relintch1 - self.relintch0
            self.reldosenocalibrel = (self.absdosenocalibrel / float(dmetadata['Reference diff Voltage'])) * 100
                
            #Calculate ch0 corrected
            self.dfrel['ch0zc'] = self.dfrel.ch0z * float(dmetadata['Calibration Factor'])
            self.dfrel['ch1zc'] = self.dfrel.ch1z
            
            self.dfrel['ch0zctc'] = self.dfrel.ch0ztc * float(dmetadata['Calibration Factor'])
            self.dfrel['ch1zctc'] = self.dfrel.ch1ztc
             
            #Calculate integrals corrected
            self.relintch0c = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch0zc'].sum()
            self.relintch1c = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch1zc'].sum()
            
            self.relintch0ctc = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch0zctc'].sum()
            self.relintch1ctc = self.dfrel.loc[(self.dfrel.time>self.trs)&(self.dfrel.time<self.trf), 'ch1zctc'].sum()
             
            #calculate absolute dose
            self.relrelabsdose = self.relintch1c - self.relintch0c
            
            self.relrelabsdosetc = self.relintch1ctc - self.relintch0ctc
                
            #calculate relative dose
            self.relreldose = (self.relrelabsdose / float(dmetadata['Reference diff Voltage'])) * 100
            
            self.relreldosetc = (self.relrelabsdosetc / float(dmetadata['Reference diff Voltage'])) * 100

            #plot the relative file
            self.plot1()
 
        else:
            self.relfileloaded = False



    def selectfile(self):
        self.tbrelfile.setEnabled(True)
        #self.ax1.clear()
        #self.ax2.clear()
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                               './rawdata')
        filename_only = filename[0].split('/')[-1]
        self.setWindowTitle('Blue Physics Model 8.2 Analyze File: %s'
                             %filename_only)
        self.dfa = pd.read_csv(filename[0], skiprows=34)
        
        #Calculate start and end of radiation
        #Assuming ch1 is where the sensor is and it has the largest differences
        self.dfa['ch1diff'] = self.dfa.ch1.diff()
        self.ts = self.dfa.loc[self.dfa.ch1diff == self.dfa.ch1diff.max(), 'time'].item()
        self.tf = self.dfa.loc[self.dfa.ch1diff == self.dfa.ch1diff.min(), 'time'].item()
        print ('Start time: %.2f Finish time: %.2f' %(self.ts, self.tf))
        
        #calculate correction to temperature
        self.dfa['ch0tc'] = self.dfa.ch0
        self.dfa['ch1tc'] = self.dfa.ch1
        self.dfa.loc[self.dfa.ch0<6.25, 'ch0tc'] = self.dfa.ch0 - (-0.012 * self.dfa.ch0 + 0.075) * (self.dfa.temp - 26.8)
        self.dfa.loc[self.dfa.ch1<6.25, 'ch1tc'] = self.dfa.ch1 - (-0.012 * self.dfa.ch1 + 0.075) * (self.dfa.temp - 26.8)
        
        #calculate the zeros
        #print ('mean zero ch0tc: %.3f' %(self.dfa.loc[(self.dfa.time<ts)|(self.dfa.time>tf), 'ch0tc'].mean()))
        self.dfa['ch0ztc'] = self.dfa.ch0tc - self.dfa.loc[(self.dfa.time<self.ts)|(self.dfa.time>self.tf), 'ch0tc'].mean()
        self.dfa['ch1ztc'] = self.dfa.ch1tc - self.dfa.loc[(self.dfa.time<self.ts)|(self.dfa.time>self.tf), 'ch1tc'].mean()
        
        self.dfa['ch0z'] = self.dfa.ch0 - self.dfa.loc[(self.dfa.time<self.ts)|(self.dfa.time>self.tf), 'ch0'].mean()
        self.dfa['ch1z'] = self.dfa.ch1 - self.dfa.loc[(self.dfa.time<self.ts)|(self.dfa.time>self.tf), 'ch1'].mean()
        
        #calculate integrals not corrected
        self.intch0tc = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch0ztc'].sum()
        self.intch1tc = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch1ztc'].sum()
        
        self.absdosenocalibtc = self.intch1tc - self.intch0tc
        self.reldosenocalibtc = (self.absdosenocalibtc / float(dmetadata['Reference diff Voltage'])) * 100 
        
        self.intch0 = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch0z'].sum()
        self.intch1 = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch1z'].sum()
        
        self.absdosenocalib = self.intch1 - self.intch0
        self.reldosenocalib = (self.absdosenocalib / float(dmetadata['Reference diff Voltage'])) * 100
        
        #Calculate ch0 corrected
        self.dfa['ch0zctc'] = self.dfa.ch0ztc * float(dmetadata['Calibration Factor'])
        self.dfa['ch1zctc'] = self.dfa.ch1ztc
        
        self.dfa['ch0zc'] = self.dfa.ch0z * float(dmetadata['Calibration Factor'])
        self.dfa['ch1zc'] = self.dfa.ch1z
        
        #Calculate integrals corrected
        self.intch0ctc = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch0zctc'].sum()
        self.intch1ctc = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch1zctc'].sum()
        
        self.intch0c = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch0zc'].sum()
        self.intch1c = self.dfa.loc[(self.dfa.time>self.ts)&(self.dfa.time<self.tf), 'ch1zc'].sum()
        
        #calculate absolute dose
        self.absdosetc = self.intch1ctc - self.intch0ctc
        
        self.absdose = self.intch1c - self.intch0c
        
        #calculate relative dose
        self.reldosetc = (self.absdosetc / float(dmetadata['Reference diff Voltage'])) * 100
        
        self.reldose = (self.absdose / float(dmetadata['Reference diff Voltage'])) * 100
        
        #Plot the selected file running the current functions
        self.plot1()

        self.tbviewch0.setEnabled(True)
        self.tbviewch1.setEnabled(True)
        self.cbsecondplot.setEnabled(True)
        self.tbviewraw.setEnabled(True)
        self.tbintegral.setEnabled(True)
        self.tbtempcorrec.setEnabled(True)
        self.tbcalibration.setEnabled(True)


    def plot1(self):

        self.ax1.clear()
        self.ax1.grid(True)

        if self.tbviewch0.isChecked():
            if (self.tbviewraw.isChecked() and (not self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbviewraw.isChecked() and (self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0tc,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0tc,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbintegral.isChecked() and (not self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0z,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0z,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch0z.max()
                self.ax1.text(coordx, coordy, 'int: %.2f' %(self.intch0), color=colors[0])
            elif (self.tbintegral.isChecked() and (self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0ztc,
                              color = colors[0], label = 'ch0')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch0ztc.max()
                self.ax1.text(coordx, coordy, 'int: %.2f' %(self.intch0tc), color=colors[0])
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0ztc,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbintegral.isChecked() and (not self.tbtempcorrec.isChecked() and self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0zc,
                              color = colors[0], label = 'ch0')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch0zc.max()
                self.ax1.text(coordx, coordy, 'int: %.2f' %self.intch0c, color=colors[0])
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0zc,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbintegral.isChecked() and (self.tbtempcorrec.isChecked() and self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch0zctc,
                              color = colors[0], label = 'ch0')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch0zctc.max()
                self.ax1.text(coordx, coordy, 'int: %.2f' %self.intch0ctc, color=colors[0])
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0zctc,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')

                
        if self.tbviewch1.isChecked():
            if (self.tbviewraw.isChecked() and (not self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1,
                              color = colors[1], label = 'ch1')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
            elif (self.tbviewraw.isChecked() and (self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1tc,
                              color = colors[1], label = 'ch1')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1tc,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
            elif (self.tbintegral.isChecked() and (not self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1z,
                              color = colors[1], label = 'ch1')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch1z.max()
                self.ax1.text(coordx, coordy, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.intch1, self.absdosenocalib, self.reldosenocalib), color=colors[1])
                self.ax1.text(coordx, coordy-1, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.intch1, self.absdosenocalib, self.reldosenocalib), color=colors[1], alpha=0.5)
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1z,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
            elif (self.tbintegral.isChecked() and (self.tbtempcorrec.isChecked() and not self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1ztc,
                              color = colors[1], label = 'ch1')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1ztc,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch1ztc.max()
                self.ax1.text(coordx, coordy-1, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.relintch1tc, self.absdosenocalibtcrel, self.reldosenocalibtcrel), color=colors[1], alpha=0.5)
                self.ax1.text(coordx, coordy, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.intch1tc, self.absdosenocalibtc, self.reldosenocalibtc), color=colors[1])
            elif (self.tbintegral.isChecked() and (not self.tbtempcorrec.isChecked() and self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1zc,
                              color = colors[1], label = 'ch1')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1zc,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch1zc.max()
                self.ax1.text(coordx, coordy, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.intch1c, self.absdose, self.reldose), color=colors[1])
            elif (self.tbintegral.isChecked() and (self.tbtempcorrec.isChecked() and self.tbcalibration.isChecked())):
                self.ax1.plot(self.dfa.time, self.dfa.ch1zctc,
                              color = colors[1], label = 'ch1')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch1zctc,
                                  color = colors[1], alpha = 0.5, label = 'ch1rel')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch1zctc.max()
                self.ax1.text(coordx, coordy, 'int: %.2f abs dose: %.2f rel dose: %.2f' %(self.intch1ctc, self.absdosetc, self.reldosetc), color=colors[1])
                
       
        self.ax1.set_ylabel('volts (V)')
        self.ax1.legend()
        self.canvas.draw()
 
        
        
    def plot2(self, index):
        
        self.ax2.clear()
        self.ax2.set_ylabel('Volts (V)')
        
        if index == 1:
            self.dfa.set_index('time').loc[:,'temp'].plot(ax=self.ax2,
                                                          color='#002525',
                                                          grid=True)

            self.ax2.set_ylabel('Temp (C)')
            if self.relfileloaded:
                self.dfrel.set_index('newtimerel').loc[:,'temp'].plot(ax=self.ax2,
                                                                      color = '#002525',
                                                                      alpha=0.5,
                                                                      grid=True)
        elif index == 2:
            self.dfa.set_index('time').loc[:,'PS'].plot(ax=self.ax2,
                                                        grid=True,
                                                        color='#000099')
            if self.relfileloaded:
                self.dfrel.set_index('newtimerel').loc[:,'PS'].plot(ax=self.ax2,
                                                                    color = '#002525',
                                                                    alpha=0.5,
                                                                    grid=True)

        elif index == 3:
            self.dfa.set_index('time').loc[:,'-12V':'10.58V'].plot(ax=self.ax2, grid=True)
            if self.relfileloaded:
                self.dfrel.set_index('newtimerel').loc[:,'-12V':'10.58V'].plot(ax=self.ax2,
                                                                               alpha=0.5,
                                                                               grid=True)

       

        self.ax2.set_xlabel('time (s)')
        #self.ax2.legend(True)
        self.canvas.draw()
    
    
    def backtomainmenu(self):
        self.close()
        mymainmenu.show()


class Metadata (QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("metadatagui.ui", self)
        self.metadatadictogui()
        self.signals()
        #self.cbsaveoncurrentmeasurements.setChecked(True)
        
    def metadatadictogui(self):
        
        if dmetadata['Save File As'] == 'Default':
            self.cbdefault.setChecked(True)
            self.cbcustom.setChecked(False)
            self.lefilename.setText('default')
        elif dmetadata['Save File As'] == 'Custom':
            self.cbdefault.setChecked(False)
            self.cbcustom.setChecked(True)
            self.lefilename.setText(dmetadata['File Name'])
        
        self.sbncr.setValue(float(dmetadata['Neighbour Channel Ratio']))
        self.sbreferencecharge.setValue(float(dmetadata['Reference Charge']))
        self.sbcalibrationfactor.setValue(float(dmetadata['Calibration Factor']))
        self.lefacility.setText(dmetadata['Facility'])
        self.leinvestigator.setText(dmetadata['Investigator'])
        self.sbintegrationtime.setValue(int(dmetadata['Integration Time']))
        self.cbopmode.setCurrentText(dmetadata['Operational Mode'])
        self.cbsource.setCurrentText(dmetadata['Source'])
        self.linacbrand.setCurrentText(dmetadata['Brand'])
        self.linacparticles.setCurrentText(dmetadata['Particles'])
        self.linacenergy.setCurrentText(dmetadata['Energy'])
        self.linacdoserate.setValue(int(dmetadata['Dose Rate']))
        self.linacgantry.setValue(int(dmetadata['Gantry']))
        self.linaccollimator.setValue(int(dmetadata['Collimator']))
        self.linaccouch.setValue(int(dmetadata['Couch']))
        self.x1coord.setValue(float(dmetadata['Field Size X1']))
        self.x2coord.setValue(float(dmetadata['Field Size X2']))
        self.y1coord.setValue(float(dmetadata['Field Size Y1']))
        self.y2coord.setValue(float(dmetadata['Field Size Y2']))
        self.linacssdsad.setCurrentText(dmetadata['Setup'])
        self.linacssdsaddist.setValue(int(dmetadata['Distance']))
        self.linacmus.setValue(int(dmetadata['MU']))
        self.transducertype.setCurrentText(dmetadata['Transducer Type'])
        self.sensortype.setCurrentText(dmetadata['Sensor Type'])
        self.sensorsize.setCurrentText(dmetadata['Sensor Size'])
        self.sensorfiberlength.setValue(int(dmetadata['Fiber Length']))
        self.sensorpositionx.setValue(float(dmetadata['Sensor Position X']))
        self.sensorpositiony.setValue(float(dmetadata['Sensor Position Y']))
        self.sensorpositionz.setValue(float(dmetadata['Sensor Position Z']))
        self.referencefiberlength.setValue(int(dmetadata['Reference Fiber Length']))
        self.comments.setText(dmetadata['Comments'])
        

    def signals(self):
        self.tbgeneral.clicked.connect(self.showgeneralpage)
        self.tblinac.clicked.connect(self.showlinacpage)
        self.tbsensor.clicked.connect(self.showsensorpage)
        self.tbcomments.clicked.connect(self.showcommentspage)
        self.tbmainmenumetadata.clicked.connect(self.backtomainmenu)
        self.cbdefault.clicked.connect(self.saveasfilename)
        self.cbcustom.clicked.connect(self.saveasfilename)
        self.cbsaveoncurrentmeasurements.clicked.connect(self.saveoncurrent)
        self.cbsymetric.clicked.connect(self.symetry)
        self.y1coord.valueChanged.connect(self.symy1ch)
        self.pbsendtocontroller.clicked.connect(self.sendtocontroller)
        
    def sendtocontroller(self):
        device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
        self.serc = serial.Serial(device, 115200, timeout=1)
        texttosend = 'c%s,%s' %(self.sbintegrationtime.value(), self.cbopmode.currentText()[0])
        print (texttosend.encode())
        self.serc.write(texttosend.encode())
        self.serc.close()
        
    def symy1ch(self, value):
        if self.cbsymetric.isChecked():
            self.x1coord.setValue(value)
            self.x2coord.setValue(value)
            self.y2coord.setValue(value)

    def symetry(self):
        if self.cbsymetric.isChecked():
            self.x1coord.setEnabled(False)
            self.x2coord.setEnabled(False)
            self.y2coord.setEnabled(False)
        else:
            self.x1coord.setEnabled(True)
            self.x2coord.setEnabled(True)
            self.y2coord.setEnabled(True)
        

    def saveoncurrent(self):
        if self.cbsaveoncurrentmeasurements.isChecked():
            self.lefilename.setReadOnly(True)
        else:
            self.lefilename.setReadOnly(False)
        
    def saveasfilename(self):
        if not(self.cbsaveoncurrentmeasurements.isChecked()):
            if self.cbdefault.isChecked():
                self.lefilename.setText('default')
                self.lefilename.setReadOnly(True)
            elif self.cbcustom.isChecked():
                self.lefilename.setText('')
                self.lefilename.setReadOnly(False)
        
    def metadataguitodic(self):
        if self.cbdefault.isChecked():
            dmetadata['Save File As'] =  'Default'
        if self.cbcustom.isChecked():
            dmetadata['Save File As'] = 'Custom'
        dmetadata['File Name'] = self.lefilename.text()
        dmetadata['Neightbour Channel Ratio'] = str(self.sbncr.value())
        dmetadata['Calibration Factor'] = str(self.sbcalibrationfactor.value())
        dmetadata['Facility'] = self.lefacility.text()
        dmetadata['Investigator'] = self.leinvestigator.text()
        dmetadata['Integration Time'] = str(self.sbintegrationtime.value())
        dmetadata['Operational Mode'] = self.cbopmode.currentText()
        dmetadata['Source'] = self.cbsource.currentText()
        dmetadata['Brand'] = self.linacbrand.currentText()
        dmetadata['Particles'] = self.linacparticles.currentText()
        dmetadata['Energy'] = self.linacenergy.currentText()
        dmetadata['Dose Rate'] = str(self.linacdoserate.value())
        dmetadata['Gantry'] = str(self.linacgantry.value())
        dmetadata['Collimator'] = str(self.linaccollimator.value())
        dmetadata['Couch'] = str(self.linaccouch.value())
        dmetadata['Field Size X1'] =  str(self.x1coord.value())
        dmetadata['Field Size X2'] =  str(self.x2coord.value())
        dmetadata['Field Size Y1'] =  str(self.y1coord.value())
        dmetadata['Field Size Y2'] =  str(self.y2coord.value())
        dmetadata['Setup'] = self.linacssdsad.currentText()
        dmetadata['Distance'] =  str(self.linacssdsaddist.value())
        dmetadata['MU'] = str(self.linacmus.value())
        dmetadata['Transducer Type'] =  self.transducertype.currentText()
        dmetadata['Sensor Type'] = self.sensortype.currentText()
        dmetadata['Sensor Size'] = self.sensorsize.currentText()
        dmetadata['Fiber Length'] =  str(self.sensorfiberlength.value())
        dmetadata['Sensor Position X'] = str(self.sensorpositionx.value())
        dmetadata['Sensor Position Y'] = str(self.sensorpositiony.value())
        dmetadata['Sensor Position Z'] = str(self.sensorpositionz.value())
        dmetadata['Reference Fiber Length'] = str(self.referencefiberlength.value())
        dmetadata['Comments'] =  self.comments.toPlainText()
        
    def backtomainmenu(self):
        self.close()
        self.metadataguitodic()
        
        #If there is already a measument done add the changes to the header file
        #First check if there are measurements
        #global measurements_done
        if measurements_done and self.cbsaveoncurrentmeasurements.isChecked():
            #read the current files
            filepow = open('./rawdata/%spowers.csv' %dmetadata['File Name'], 'r')
            filemeas = open('./rawdata/%smeasurements.csv' %dmetadata['File Name'], 'r')
            #read lines
            filepowlines = filepow.readlines()
            filemeaslines = filemeas.readlines()
            filepow.close()
            filemeas.close()
            #find the number of lines of metadata
            nlinesmeta = len(metadatakeylist)
            #Create the new list of lines
            #first add the new metadata
            newfilepowlines = ['%s,%s\n' %(key,dmetadata[key]) for key in metadatakeylist]
            newfilemeaslines = ['%s,%s\n' %(key,dmetadata[key]) for key in metadatakeylist]
            #then add the current measurements
            for line in filepowlines[nlinesmeta:]:
                newfilepowlines.append(line)
            for line in filemeaslines[nlinesmeta:]:
                newfilemeaslines.append(line)
            #Save the new changes and overwrite the old files
            newfilepow = open('./rawdata/%spowers.csv' %dmetadata['File Name'], 'w')
            newfilemeas = open('./rawdata/%smeasurements.csv' %dmetadata['File Name'], 'w')
            newfilepow.writelines(newfilepowlines)
            newfilemeas.writelines(newfilemeaslines)
            newfilepow.close()
            newfilemeas.close()
            
        mymainmenu.setwindowstitle()
        
        mymainmenu.show()
        
    def showcommentspage(self):
        self.swmetadata.setCurrentIndex(3)
        
    def showsensorpage(self):
        self.swmetadata.setCurrentIndex(2)
        
    def showlinacpage(self):
        self.swmetadata.setCurrentIndex(1)
        
    def showgeneralpage(self):
        self.swmetadata.setCurrentIndex(0)
        

class Measure(QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("measuregui.ui", self)
        
        #Creat the plot for measuring
        #Source https://htmlcolorcodes.com
        self.plotitemchs = pg.PlotItem()
        self.plotitemchs.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemchs.setLabel('bottom', 'Time', units='s')
        self.plotitemchs.setLabel('left', 'Voltage', units='V')
        self.legend = self.plotitemchs.addLegend()
        self.plotitemPS = pg.PlotItem(title= '<span style="color: #000099">PS</span>')
        self.plotitemPS.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemPS.setLabel('bottom', 'Time', units ='s')
        self.plotitemPS.setLabel('left', 'Voltage', units = 'V')
        self.plotitem5v = pg.PlotItem(title ='<span style="color: #009999">5V</span> ')
        self.plotitemminus12v = pg.PlotItem(title = '<span style="color: #990099">-12V</span>')
        self.plotitemvref = pg.PlotItem(title = '<span style="color: #990000">Vref</span>')
        self.plotitem5v.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitem5v.setLabel('bottom', 'Time', units = 's')
        self.plotitem5v.setLabel('left', 'Voltage', units = 'V')
        self.plotitemminus12v.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemminus12v.setLabel('bottom', 'Time', units = 's')
        self.plotitemminus12v.setLabel('left', 'Voltage', units = 'V')
        self.plotitemvref.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemvref.setLabel('bottom', 'Time', units = 's')
        self.plotitemvref.setLabel('left', 'Voltage', units = 'V')
        self.plotitemtemp = pg.PlotItem(title = '<span style="color: #002525">Temp C')
        self.plotitemtemp.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemtemp.setLabel('bottom', 'Time', units = 's')
        self.plotitemtemp.setLabel('left', 'Temperature', units = 'C')        
        self.curvech0 = self.plotitemchs.plot(pen=pg.mkPen(color='#C0392B', width=2),
                                              name = 'Ch0')                                              
        self.curvech1 = self.plotitemchs.plot(pen=pg.mkPen(color='#3498DB', width=2),
                                              name = 'Ch1')                
        self.curvePS = self.plotitemPS.plot(pen=pg.mkPen(color='#000099', width=2))
        self.curve5v = self.plotitem5v.plot(pen=pg.mkPen(color='#009999',width=2))
        self.curveminus12v = self.plotitemminus12v.plot(pen=pg.mkPen(color='#990099',width=2))
        self.curvevref = self.plotitemvref.plot(pen=pg.mkPen(color='#990000',width=2))
        self.curvetemp = self.plotitemtemp.plot(pen=pg.mkPen(color='#002525', width=2))
        
        self.signals()
        
        self.graphicsView.addItem(self.plotitemchs)
        #self.viewplots()

       
    def signals(self):
        self.tbmainmenu.clicked.connect(self.backmainmenu)
        self.tbstartmeasure.clicked.connect(self.startmeasuring)
        self.tbviewch0.clicked.connect(self.viewplots)
        self.tbviewch1.clicked.connect(self.viewplots)
        self.cbsecondplot.currentIndexChanged.connect(self.secondplot)
        self.tbstopmeasure.clicked.connect(self.stopmeasurement)
        self.tbsdc.clicked.connect(self.sdc)
        self.tbregulate.clicked.connect(self.regulate)
        
    def regulate(self):
        self.tbstartmeasure.setEnabled(False)
        //device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
        self.serreg = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        self.serreg.write('r'.encode())
        print ('r'.encode())
        for i in range(10):
            line = self.serreg.readline().decode().strip()
            print (line)
        while len(line) == 9:
            line = self.serreg.readline().decode().strip()
            print (line)
        self.serreg.close()
        self.tbstartmeasure.setEnabled(True)
        
    def sdc(self):
        self.tbstartmeasure.setEnabled(False)
        //device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
        self.ser = serial.Serial('/dev/ttyS0', 115200, timeout = 1)
        self.ser.write('s'.encode())
        for i in range (10):
            line = self.ser.readline().decode().strip().split(',')
            print(line)
        while len(line) == 9:
            print(line)
            line = self.ser.readline().decode().strip().split(',')
        self.ser.close()
        self.tbstartmeasure.setEnabled(True)

        
    def secondplot(self, index):
        #clearLayout(self.gridmeasure)
        #self.gridmeasure.addWidget(self.plotitemchs)
        itemtoremove = self.graphicsView.getItem(1, 0)
        if itemtoremove:
            self.graphicsView.removeItem(itemtoremove)
        if index == 1:
            self.graphicsView.addItem(self.plotitemtemp,row=1,col=0)
        elif index == 2:
            self.graphicsView.addItem(self.plotitemPS, row=1, col=0)
        elif index == 3:
            self.graphicsView.addItem(self.plotitem5v, row=1, col=0)
        elif index == 4:
            self.graphicsView.addItem(self.plotitemminus12v, row = 1, col = 0)
        elif index == 5:
            self.graphicsView.addItem(self.plotitemvref, row = 1, col = 0)
    
    
    def viewplots(self):
        currentcurves = self.plotitemchs.listDataItems()
        for curve in currentcurves:
            self.plotitemchs.removeItem(curve)
        self.legend.scene().removeItem(self.legend)
        self.legend = self.plotitemchs.addLegend()
        if self.tbviewch0.isChecked():
            self.plotitemchs.addItem(self.curvech0)
        if self.tbviewch1.isChecked():
            self.plotitemchs.addItem(self.curvech1)

        
    
    def startmeasuring(self):
        mymainmenu.setwindowstitle()
        #Check if the file already exist, to prevent overwritting
        filesnow = os.listdir('rawdata')
        if ('%s.csv' %dmetadata['File Name'] in filesnow) and (dmetadata['File Name'] != 'default'):
            filename = dmetadata['File Name']
            #check if file names ends with -num
            if '-' in filename:
                pos = filename.find('-')
                current_num = int(filename[pos+1:])
                new_num = current_num + 1
                new_name = '%s-%s' %(filename[:pos], new_num)
                
            else:
                new_name = '%s-2' %filename
                
            buttonreply = QMessageBox.question(self, 'File exists',
                                  "Change to %s?" %new_name,
                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                  
            if buttonreply == QMessageBox.Yes:
                dmetadata['File Name'] = new_name
                mymainmenu.setwindowstitle()
                self.startmeasuringforgood()
            else:
                self.close()
                mymainmenu.mymetadata.show()
        else:
            self.startmeasuringforgood()
                   
            
    def startmeasuringforgood(self):
            
        #Refresh screen and reset buttons
        #clearLayout (self.gridmeasure)
        global measurements_done
        measurements_done = False
        
        self.plotitemchs.clear()
        self.viewplots()
        #self.legend.scene().removeItem(self.legend)
        #self.legend = self.plotitemchs.addLegend()
        self.times = []
        self.tempmeas = []
        self.ch0meas = []
        self.ch1meas = []
        self.PSmeas = []
        self.minus12Vmeas = []
        self.v5Vmeas = []
        self.v1058Vmeas = []


        self.tbstopmeasure.setEnabled(True)
        self.tbstartmeasure.setEnabled(False)
        self.tbsdc.setEnabled(False)
        self.tbregulate.setEnabled(False)
        
        if dmetadata['Save File As'] == 'Date/Time':
            dmetadata['File Name'] = time.strftime ('%d %b %Y %H:%M:%S')
            
        dmetadata['Date Time'] = time.strftime('%d %b %Y %H:%M:%S')

        #only if emulator
        #self.emulator = EmulatorThread()
        #self.emulator.start()
        
        self.measurethread = MeasureThread()
        self.measurethread.start()
        self.measurethread.info.connect(self.update)
        

      
    def update(self, measurements):
        self.times.append(measurements[0])
        self.tempmeas.append(measurements[1])
        self.ch0meas.append(-(measurements[2]) * 0.000375 + 12.288)
        self.ch1meas.append(-(measurements[3]) * 0.000375 + 12.288)
        self.PSmeas.append(measurements[4] * 0.1875 / 1000 * 12.914)
        self.minus12Vmeas.append(measurements[5] * 0.1875 / 1000 * 2.2)
        self.v5Vmeas.append(measurements[6] * 0.1875 / 1000)
        self.v1058Vmeas.append(measurements[7] * 0.1875 / 1000 * 2)   
        
        DS = 1 #Downsampling
        self.curvetemp.setData(self.times[::DS], self.tempmeas[::DS])
        self.curvech0.setData(self.times[::DS], self.ch0meas[::DS])
        self.curvech1.setData(self.times[::DS], self.ch1meas[::DS])
        self.curve5v.setData(self.times[::DS], self.v5Vmeas[::DS])
        self.curvevref.setData(self.times[::DS], self.v1058Vmeas[::DS])
        self.curveminus12v.setData(self.times[::DS], self.minus12Vmeas[::DS])
        self.curvePS.setData(self.times[::DS], self.PSmeas[::DS])

        
        
        
    def stopmeasurement(self):
        #emulator
        #self.emulator.stopping()
        self.measurethread.stopping()
        self.tbstopmeasure.setEnabled(False)
        self.tbstartmeasure.setEnabled(True)
        self.tbsdc.setEnabled(True)
        self.tbregulate.setEnabled(True)
        
        #Global flag idicating measurements are done
        global measurements_done
        measurements_done = True
        
        #Save data in files and close files
        
        self.filemeas = open ('./rawdata/%s.csv' %dmetadata['File Name'], 'w')

        for key in metadatakeylist:
            self.filemeas.write('%s,%s\n' %(key,dmetadata[key]))

        self.filemeas.write('time,temp,ch0,ch1,PS,-12V,5V,10.58V\n')
        
        for i in range(len(self.times)):
            self.filemeas.write('%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' %(self.times[i],
                                                                self.tempmeas[i],
                                                                self.ch0meas[i],
                                                                self.ch1meas[i],
                                                                self.PSmeas[i],
                                                                self.minus12Vmeas[i],
                                                                self.v5Vmeas[i],
                                                                self.v1058Vmeas[i]))
        self.filemeas.close()
        self.afterstopping()
        
        
    def afterstopping(self):
        #Calculate integrals
        #first put in a dataframe
        df = pd.DataFrame({'time': self.times, 'temp':self.tempmeas,
                           'ch0': self.ch0meas, 'ch1':self.ch1meas,
                           '5V': self.v5Vmeas, '10.58V':self.v1058Vmeas,
                           '-12V':self.minus12Vmeas, 'PS':self.PSmeas})
              
        #Calculate start and end of radiation
        #Assuming ch1 is where the sensor is and it has the largest differences
        df['ch1diff'] = df.ch1.diff()
        dfchanges =  df.loc[df.ch1diff.abs() > 0.5, :].copy()
        #print (dfchanges.head())
        dfchanges['timediff'] = dfchanges.time.diff()
        dfchanges.fillna(1, inplace=True)
        dftimes =  dfchanges[dfchanges.timediff > 0.5].copy()
        #print (dftimes.head())
        starttimes = dftimes.loc[dftimes.ch1diff > 0, 'time'].values
        print (starttimes)
        finishtimes = dftimes.loc[dftimes.ch1diff < 0, 'time'].values
        #print (finishtimes)
        ts = starttimes[0]
        tf = finishtimes[-1]
        #print ('Start time: %.2f Finish time: %.2f' %(ts, tf))
  
        #calculate the zeros
        #print ('mean zero ch0: %.3f' %(df.loc[(df.time<(ts-2))|(df.time>(tf+2)), 'ch0'].mean()))
        df['ch0z'] = df.ch0 - df.loc[(df.time<(ts-2))|(df.time>(tf+2)), 'ch0'].mean()
        df['ch1z'] = df.ch1 - df.loc[(df.time<(ts-2))|(df.time>(tf+2)), 'ch1'].mean()
        
        #calculate integrals not corrected
        self.intch0 = df.loc[:, 'ch0z'].sum()
        self.intch1 = df.loc[:, 'ch1z'].sum()
        
        self.plotitemchs.clear()
        #draw the new plots with zeros corrected
        self.curvech0.setData(df.time, df.ch0z)
        self.curvech1.setData(df.time, df.ch1z)
        self.legend.scene().removeItem(self.legend)
        self.legend = self.plotitemchs.addLegend()
        self.plotitemchs.addItem(self.curvech0)
        self.plotitemchs.addItem(self.curvech1)
        #print ('zero ch0zc: %.3f' %(df.loc[(df.time<ts)|(df.time>tf), 'ch0zc'].mean()))
        
        self.linearregions = []
        for (st, ft) in zip(starttimes, finishtimes):
            self.linearregions.append(pg.LinearRegionItem(values=(st-2, ft+2), movable=False))
            
        for lr in self.linearregions:
            self.plotitemchs.addItem(lr)
                
        self.listaintch0 = []
        self.listaintch1 = []
        for (st, ft) in zip(starttimes, finishtimes):
            intch0beamn = df.loc[(df.time>(st-2))&(df.time<(ft+2)), 'ch0z'].sum()
            intch1beamn = df.loc[(df.time>(st-2))&(df.time<(ft+2)), 'ch1z'].sum()
            self.listaintch0.append(intch0beamn)
            self.listaintch1.append(intch1beamn)
            
        self.listadoses = [s - c * float(dmetadata['Neighbour Channel Ratio']) for (c, s) in zip(self.listaintch0, self.listaintch1)]
        self.listadosesrel = [d/float(dmetadata['Reference Charge'])*100 for d in self.listadoses]
        
        self.ch0text = pg.TextItem('Tot. int. ch0: %.2f V' %(self.intch0), color = colors[0])
        self.ch0text.setPos((df.time.max())/2, df.ch0z.max())
        self.ch1text = pg.TextItem('Tot. int. ch1: %.2f V' %(self.intch1), color = colors[1])
        self.ch1text.setPos((df.time.max())/2, df.ch1z.max())
        self.plotitemchs.addItem(self.ch0text)
        self.plotitemchs.addItem(self.ch1text)

        self.plotitemchs.scene().sigMouseMoved.connect(self.mouseMoved)


    def mouseMoved(self, evt):
        listaindex = [lr.sceneBoundingRect().contains(evt) for lr in self.linearregions]
        if (sum(listaindex)) > 0:
            #find the index where the True value is
            gi = listaindex.index(True)
            self.ch0text.setText('IntCh0: %.2f V' %(self.listaintch0[gi]))
            self.ch1text.setText('IntCh1: %.2f V\nVDose: %.2f V\n%%Dose: %.2f %%' %(self.listaintch1[gi],
                                                                                    self.listadoses[gi],
                                                                                    self.listadosesrel[gi]))
        else:
            self.ch0text.setText('Tot. Int. ch0: %.2f V' %(self.intch0))
            self.ch1text.setText('Tot. Int. ch1: %.2f V' %(self.intch1))


    def backmainmenu(self):
        self.close()
        mymainmenu.show()


def goodbye():
    print ('bye')
    print (dmetadata['Date Time'])
    metadatafile = open('metadata.csv', 'w')
    for key in metadatakeylist:
        metadatafile.write('%s,%s\n' %(key, dmetadata[key]))
        print ('%s,%s\n' %(key, dmetadata[key]))
    metadatafile.close()
    #mymainmenu.mymeasure.measurepowerthread.stopping()
    
    
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    mymainmenu = MainMenu()
    atexit.register(goodbye)
    mymainmenu.show()
    sys.exit(app.exec_())
