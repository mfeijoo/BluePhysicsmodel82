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



colors = ['#01dfa5', '#a5df00']


#Read Metadata file and load data in a dictionary
metadatafile = open('metadata.csv', 'r')
listmetadata = [pair.split(',') for pair in metadatafile.readlines()]
metadatakeylist = [key for [key, value] in listmetadata]
metadatafile.close()
global dmetadata
dmetadata = {key:value.strip() for [key,value] in listmetadata}
#print(metadatakeylist)


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
        self.ser2 = serial.Serial ('/dev/pts/3', 115200, timeout=1)
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
        self.ser = serial.Serial ('/dev/pts/4', 115200, timeout=1)
        #self.ser = serial.Serial ('/dev/ttyS0', 115200, timeout=1)

    def __del__(self):
        self.wait()

    def run(self):
        #One reading to discard garbge
        #comment if emulator
        #reading0 = self.ser.readline().decode().strip().split(',')

        #second reading to check starting time
        #comment if emulator
        #reading1 = self.ser.readline().decode().strip().split(',')
        #tstart = int(reading1[0])
        
        while True:
            
            if self.stop:
                break
        
            try:
                reading = self.ser.readline().decode().strip().split(',')
                #print (reading)
                #only if emulator
                listatosend = [float(i) for i in reading]
                #listatosend = [(int(reading[0])-tstart)/1000] + [float(i) for i  in reading[1:]]
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
        self.mymetadata = Metadata()
        self.mymeasure = Measure()
        self.metadatadictogui()
        #self.myanalyze = Analyze()
        self.signals()
        self.setwindowstitle()
        
    def metadatadictogui(self):
        
        if dmetadata['Save File As'] == 'Default':
            self.mymetadata.cbdefault.setChecked(True)
            self.mymetadata.cbcustom.setChecked(False)
            self.mymetadata.lefilename.setText('default')
            self.mymetadata.lefilename.setText(dmetadata['File Name'])
        elif dmetadata['Save File As'] == 'Custom':
            self.mymetadata.cbdefault.setChecked(False)
            self.mymetadata.cbcustom.setChecked(True)
            #self.lefilename.setReadOnly(False)
            self.mymetadata.lefilename.setText(dmetadata['File Name'])
        
        self.mymetadata.sbacr.setValue(float(dmetadata['Adjacent Channels Ratio']))
        self.mymetadata.sbreferenceV.setValue(float(dmetadata['Reference Charge']))
        self.mymetadata.sbcalibrationfactor.setValue(float(dmetadata['Calibration Factor']))
        self.mymetadata.lefacility.setText(dmetadata['Facility'])
        self.mymetadata.leinvestigator.setText(dmetadata['Investigator'])
        self.mymetadata.sbintegrationtime.setValue(int(dmetadata['Integration Time']))
        self.mymetadata.cbopmode.setCurrentText(dmetadata['Operational Mode'])
        self.mymetadata.cbsource.setCurrentText(dmetadata['Source'])
        self.mymetadata.linacbrand.setCurrentText(dmetadata['Brand'])
        self.mymetadata.linacparticles.setCurrentText(dmetadata['Particles'])
        self.mymetadata.linacenergy.setCurrentText(dmetadata['Energy'])
        self.mymetadata.linacdoserate.setValue(int(dmetadata['Dose Rate']))
        self.mymetadata.linacgantry.setValue(int(dmetadata['Gantry']))
        self.mymetadata.linaccollimator.setValue(int(dmetadata['Collimator']))
        self.mymetadata.linaccouch.setValue(int(dmetadata['Couch']))
        self.mymetadata.x1coord.setValue(float(dmetadata['Field Size X1']))
        self.mymetadata.x2coord.setValue(float(dmetadata['Field Size X2']))
        self.mymetadata.y1coord.setValue(float(dmetadata['Field Size Y1']))
        self.mymetadata.y2coord.setValue(float(dmetadata['Field Size Y2']))
        self.mymeasure.sbicmeas.setValue(float(dmetadata['IC Measure']))
        self.mymeasure.sbictemp.setValue(float(dmetadata['IC Temperature']))
        self.mymeasure.sbicpress.setValue(float(dmetadata['IC Pressure']))
        self.mymetadata.linacssdsad.setCurrentText(dmetadata['Setup'])
        self.mymetadata.linacssdsaddist.setValue(int(dmetadata['Distance']))
        self.mymetadata.linacmus.setValue(int(dmetadata['MU']))
        self.mymetadata.transducertype.setCurrentText(dmetadata['Transducer Type'])
        self.mymetadata.sensortype.setCurrentText(dmetadata['Sensor Type'])
        self.mymetadata.sensorsize.setCurrentText(dmetadata['Sensor Size'])
        self.mymetadata.sensorfiberdiam.setCurrentText(dmetadata['Fiber Diameter'])
        self.mymetadata.sensorfiberlength.setValue(int(dmetadata['Fiber Length']))
        self.mymetadata.sensorpositionx.setValue(float(dmetadata['Sensor Position X']))
        self.mymetadata.sensorpositiony.setValue(float(dmetadata['Sensor Position Y']))
        self.mymetadata.sensorpositionz.setValue(float(dmetadata['Sensor Position Z']))
        self.mymetadata.referencefiberdiam.setCurrentText(dmetadata['Reference Fiber Diameter'])
        self.mymetadata.referencefiberlength.setValue(int(dmetadata['Reference Fiber Length']))
        self.mymetadata.comments.setText(dmetadata['Comments'])
        
    def setwindowstitle(self):
        windowstitle = 'Blue Physics Model 8.2.5 File: %s' %(dmetadata['File Name'])
        self.setWindowTitle(windowstitle)
        self.mymeasure.setWindowTitle(windowstitle)
        self.mymetadata.setWindowTitle(windowstitle)
        #self.myanalyze.setWindowTitle('Blue Physics Model 8.2 Analyze File:')
       
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
        self.tbcalibration.clicked.connect(self.plot1)
        #self.cbsecondplot.currentIndexChanged.connect(self.plot2)
        self.tbrelfile.clicked.connect(self.relfile)

    def relfile(self):
        if self.tbrelfile.isChecked():
            #a funciton to load a second relative file to compare
            #with reference file loaded as self.df
            relfilename = QFileDialog.getOpenFileName(self, 'Open file',
                                                      './rawdata')
            self.dfrel = pd.read_csv(relfilename[0], skiprows=35, skipfooter=4)
            
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
        self.setWindowTitle('Blue Physics Model 8.2.5 Analyze File: %s'
                             %filename_only)
        self.dfa = pd.read_csv(filename[0], skiprows=35, skipfooter=4)
        
        #Calculate start and end of radiation
        #Assuming ch1 is where the sensor is and it has the largest differences
        self.dfa['ch1diff'] = self.dfa.ch1.diff()
        self.ts = self.dfa.loc[self.dfa.ch1diff == self.dfa.ch1diff.max(), 'time'].item()
        self.tf = self.dfa.loc[self.dfa.ch1diff == self.dfa.ch1diff.min(), 'time'].item()
        #print ('Start time: %.2f Finish time: %.2f' %(self.ts, self.tf))
        
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
        self.tbcalibration.setEnabled(True)


    def plot1(self):

        self.ax1.clear()
        self.ax1.grid(True)

        if self.tbviewch0.isChecked():
            if (self.tbviewraw.isChecked() and  not self.tbcalibration.isChecked()):
                self.ax1.plot(self.dfa.time, self.dfa.ch0,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbviewraw.isChecked() and not self.tbcalibration.isChecked()):
                self.ax1.plot(self.dfa.time, self.dfa.ch0tc,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0tc,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
            elif (self.tbintegral.isChecked() and not self.tbcalibration.isChecked()):
                self.ax1.plot(self.dfa.time, self.dfa.ch0z,
                              color = colors[0], label = 'ch0')
                if self.relfileloaded:
                    self.ax1.plot(self.dfrel.newtimerel, self.dfrel.ch0z,
                                  color = colors[0], alpha = 0.5, label = 'ch0rel')
                coordx = self.dfa.time.max() / 2
                coordy = self.dfa.ch0z.max()
                self.ax1.text(coordx, coordy, 'int: %.2f' %(self.intch0), color=colors[0])
            elif (self.tbintegral.isChecked() and not self.tbcalibration.isChecked()):
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
        loadUi("metadatagui2.ui", self)
        self.signals()
        

    def signals(self):
        self.tbgeneral.clicked.connect(self.showgeneralpage)
        self.tblinac.clicked.connect(self.showlinacpage)
        self.tbsensor.clicked.connect(self.showsensorpage)
        self.tbcomments.clicked.connect(self.showcommentspage)
        self.tbmainmenumetadata.clicked.connect(self.backtomainmenu)
        self.cbdefault.clicked.connect(self.saveasfilename)
        self.cbcustom.clicked.connect(self.saveasfilename)
        self.cbsaveoncurrentmeasurements.clicked.connect(self.saveoncurrent)
        #self.cbbatchfile.clicked.connect(self.batchfile)
        self.cbsymetric.clicked.connect(self.symetry)
        self.y1coord.valueChanged.connect(self.symy1ch)
        self.pbsendtocontroller.clicked.connect(self.sendtocontroller)
        
        
    def sendtocontroller(self):
        self.ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        self.ser.write('c%s,%s\n' %(self.sbintegrationtime.value(),
                                   self.cbopmode.currentText()).encode())
        self.ser.close()
        
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
        dmetadata['Adjacent Channels Ratio'] = str(self.sbacr.value())
        dmetadata['Reference Charge'] = str(self.sbreferenceV.value())
        dmetadata['Calibration Factor'] = str(self.sbcalibrationfactor.value())
        dmetadata['Facility'] = self.lefacility.text()
        dmetadata['Investigator'] = self.leinvestigator.text()
        dmetadata['Integration Time'] = str(self.sbintegrationtime.value())
        dmetadata['Operational Mode'] = str(self.cbopmode.currentText())
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
        dmetadata['IC Measure'] = str(mymainmenu.mymeasure.sbicmeas.value())
        dmetadata['IC Temperature'] = str(mymainmenu.mymeasure.sbictemp.value())
        dmetadata['IC Pressure'] = str(mymainmenu.mymeasure.sbicpress.value())
        dmetadata['Setup'] = self.linacssdsad.currentText()
        dmetadata['Distance'] =  str(self.linacssdsaddist.value())
        dmetadata['MU'] = str(self.linacmus.value())
        dmetadata['Transducer Type'] =  self.transducertype.currentText()
        dmetadata['Sensor Type'] = self.sensortype.currentText()
        dmetadata['Sensor Size'] = self.sensorsize.currentText()
        dmetadata['Fiber Diameter'] =  self.sensorfiberdiam.currentText()
        dmetadata['Fiber Length'] =  str(self.sensorfiberlength.value())
        dmetadata['Sensor Position X'] = str(self.sensorpositionx.value())
        dmetadata['Sensor Position Y'] = str(self.sensorpositiony.value())
        dmetadata['Sensor Position Z'] = str(self.sensorpositionz.value())
        dmetadata['Reference Fiber Diameter'] = self.referencefiberdiam.currentText()
        dmetadata['Reference Fiber Length'] = str(self.referencefiberlength.value())
        dmetadata['Comments'] =  self.comments.toPlainText()
        
    def backtomainmenu(self):
        self.close()
        self.metadataguitodic()
        #print(dmetadata)
        
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
        loadUi("measureguim82sdc.ui", self)
        
        #Creat the plot for measuring
        #Source https://htmlcolorcodes.com
        self.plotitemchs = pg.PlotItem()
        self.plotitemchs.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemchs.setLabel('bottom', 'Time', units='s')
        self.plotitemchs.setLabel('left', 'Current', units='A')
        self.legend = self.plotitemchs.addLegend()
        self.plotitemPS = pg.PlotItem(title= '<span style="color: #000099">PS</span>')
        self.plotitemPS.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemPS.setLabel('bottom', 'Time', units ='s')
        self.plotitemPS.setLabel('left', 'Voltage', units = 'V')
        self.plotitemvoltages = pg.PlotItem(title ='<span style="color: #990099">-12V</span> '
                                                    '& <span style="color: #009999">5V</span> '
                                                    '& <span style="color: #990000">10.58V</span>')
        self.plotitemvoltages.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemvoltages.setLabel('bottom', 'Time', units = 's')
        self.plotitemvoltages.setLabel('left', 'Voltage', units = 'V')
        self.plotitemtemp = pg.PlotItem(title = '<span style="color: #002525">Temp C')
        self.plotitemtemp.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemtemp.setLabel('bottom', 'Time', units = 's')
        self.plotitemtemp.setLabel('left', 'Temperature', units = 'C')
        
        self.curvech0 = self.plotitemchs.plot(pen=pg.mkPen(color='#ff0000', width=2),
                                              name = 'Ch0',
                                              autoDownsample = False)
                                              
        self.curvech1 = self.plotitemchs.plot(pen=pg.mkPen(color='#0000ff', width=2),
                                              name = 'Ch1',
                                              autoDownsample = False)
                
        self.curvePS = self.plotitemPS.plot(pen=pg.mkPen(color='#000099', width=2),
                                                   autoDownsample = False)

        self.curve5V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#009999',
                                                                          width=2),
                                                   autoDownsample = False)
        self.curveminus12V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#990099',
                                                                 width=2),
                                                  autoDownsample = False)
        self.curve1058V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#990000',
                                                                             width=2),
                                                   autoDownsample = False)


        self.curvetemp = self.plotitemtemp.plot(pen=pg.mkPen(color='#002525', width=2),
                                                   autoDownsample = False)
        
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
        #self.tbtempcorrec.clicked.connect(self.afterstopping)
        self.tbdarkcurrent.clicked.connect(self.rmdarkcurrent)
        self.sbicmeas.valueChanged.connect(self.updatemetadata)
        self.sbictemp.valueChanged.connect(self.updatemetadata)
        self.sbicpress.valueChanged.connect(self.updatemetadata)
        
    def updatemetadata(self):
        #first update dictionary
        dmetadata['IC Measure'] = str(self.sbicmeas.value())
        dmetadata['IC Temperature'] = str(self.sbictemp.value())
        dmetadata['IC Pressure'] = str(self.sbicpress.value())
        #secondly if measurements have been done and the save on current file
        #checbox is checked, update the current file
        if (self.cbsaveincurrent.isChecked() and measurements_done):
            currentfile = open('rawdata/%s.csv' %dmetadata['File Name'], 'r+')
            currentlines = currentfile.readlines()
            currentlines[22] = 'IC Measure,%s\n' %(self.sbicmeas.value())
            currentlines[23] = 'IC Temperature,%s\n' %(self.sbictemp.value())
            currentlines[24] = 'IC Pressure,%s\n' %(self.sbicpress.value())
            currentfile.seek(0)
            currentfile.truncate()
            for line in currentlines:
                currentfile.write(line)
            currentfile.close()
            
            

    def rmdarkcurrent(self):
        self.tbstartmeasure.setEnabled(False)
        self.ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        self.ser.write('s'.encode())
        for i in range(20):
            line = self.ser.readline().decode().strip().split(',')
            print (line)
        while len(line) == 2:
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
            self.graphicsView.addItem(self.plotitemvoltages, row=1, col=0)
    
    
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
        self.ch0meastoplot = []
        self.ch1meas = []
        self.ch1meastoplot = []
        self.PScmeas = []
        self.PSVmeastoplot = []
        self.minus12Vcmeas = []
        self.minus12Vmeastoplot = []
        self.cV5meas = []
        self.V5meastoplot = []
        self.cV1058meas = []
        self.V1058meastoplot = []


        self.tbstopmeasure.setEnabled(True)
        self.tbstartmeasure.setEnabled(False)
        self.tbdarkcurrent.setEnabled(False)
        
        #if dmetadata['Save File As'] == 'Date/Time':
            #dmetadata['File Name'] = time.strftime ('%d %b %Y %H:%M:%S')
            
        dmetadata['Date Time'] = time.strftime('%d %b %Y %H:%M:%S')

        #only if emulator
        self.emulator = EmulatorThread()
        self.emulator.start()
        
        self.measurethread = MeasureThread()
        self.measurethread.start()
        self.measurethread.info.connect(self.update)
        

      
    def update(self, measurements):
        self.times.append(measurements[0])
        self.tempmeas.append(measurements[1])
        #ch measure in nC multiplying V titmes 1.8 nF as capacitance
        self.ch0meas.append(measurements[2])
        self.ch0meastoplot.append((-measurements[2] * 375e-6 + 12.288) * 1.8e-9 / (int(dmetadata['Integration Time']) * 1e-3))
        self.ch1meas.append(measurements[3])
        self.ch1meastoplot.append((-measurements[3] * 375e-6 + 12.288) * 1.8e-9 / (int(dmetadata['Integration Time']) * 1e-3))
        self.PScmeas.append(measurements[4])
        self.PSVmeastoplot.append(measurements[4] * 0.1875 / 1000 * 12.914)
        self.minus12Vcmeas.append(measurements[5])
        self.minus12Vmeastoplot.append(measurements[5] * 0.1875 / 1000 * 2.2)
        self.cV5meas.append(measurements[6])
        self.V5meastoplot.append(measurements[6] * 0.1875 / 1000)
        self.cV1058meas.append(measurements[7])
        self.V1058meastoplot.append(measurements[7] * 0.1875 / 1000 * 2)  
        
        DS = 1 #Downsampling
        self.curvetemp.setData(self.times[::DS], self.tempmeas[::DS])
        self.curvech0.setData(self.times[::DS], self.ch0meastoplot[::DS])
        self.curvech1.setData(self.times[::DS], self.ch1meastoplot[::DS])
        self.curve5V.setData(self.times[::DS], self.V5meastoplot[::DS])
        self.curve1058V.setData(self.times[::DS], self.V1058meastoplot[::DS])
        self.curveminus12V.setData(self.times[::DS], self.minus12Vmeastoplot[::DS])
        self.curvePS.setData(self.times[::DS], self.PSVmeastoplot[::DS])

        
        
        
    def stopmeasurement(self):
        self.measurethread.stopping()
        #emulator
        self.emulator.stopping()
        self.tbstopmeasure.setEnabled(False)
        self.tbstartmeasure.setEnabled(True)
        self.tbdarkcurrent.setEnabled(True)
        
        #Global flag idicating measurements are done
        global measurements_done
        measurements_done = True
        
        #Calculate integrals
        #first put in a dataframe
        df = pd.DataFrame({'time': self.times, 'temp':self.tempmeas,
                           'ch0': self.ch0meastoplot, 'ch1':self.ch1meastoplot,
                           '5V': self.V5meastoplot, '10.58V':self.V1058meastoplot,
                           '-12V':self.minus12Vmeastoplot, 'PS':self.PSVmeastoplot})
              
        #print (df.head())
        #Calculate start and end of radiation
        #Assuming ch1 is where the sensor is and it has the largest differences
        df['ch1diff'] = df.ch1.diff()
        #ts is the time of the first big increase
        ts = df.loc[df.ch1diff > 1e-9, 'time'].values[0]
        tsm = ts - 2
        #tf is the time of the last big fall
        tf = df.loc[df.ch1diff < -1e-9 , 'time'].values[-1]
        tfm = tf + 2
        #print ('Start time: %.2f Finish time: %.2f' %(ts, tf))
        
        #calculate correction to temperature
        df['ch0tc'] = df.ch0
        df['ch1tc'] = df.ch1
        #if self.tbtempcorrec.isChecked():
            #df.loc[df.ch0<6.25, 'ch0tc'] = df.ch0 - (-0.012 * df.ch0 + 0.075) * (df.temp - 26.8)
            #df.loc[df.ch1<6.25, 'ch1tc'] = df.ch1 - (-0.012 * df.ch1 + 0.075) * (df.temp - 26.8)
        
        #calculate dark currents
        ch0dc = df.loc[(df.time < tsm)|(df.time > tfm), 'ch0tc'].mean()
        ch1dc = df.loc[(df.time < tsm)|(df.time > tfm), 'ch1tc'].mean()
        
        #calculate the zeros
        #print ('mean zero ch0: %.3f' %(df.loc[(df.time<(ts-1))|(df.time>(tf+1)), 'ch0tc'].mean()))
        df['ch0z'] = df.ch0tc - ch0dc
        df['ch1z'] = df.ch1tc - ch1dc
        
        #Calculate ch0 corrected
        df['ch0zc'] = df.ch0z * float(dmetadata['Adjacent Channels Ratio'])
        df['ch1zc'] = df.ch1z
        
        #Calculate integrals corrected
        self.totalintch0nc = df.loc[(df.time>tsm)&(df.time<tfm), 'ch0zc'].sum()*1e9
        self.totalintch1nc = df.loc[(df.time>tsm)&(df.time<tfm), 'ch1zc'].sum()*1e9
        #print(self.totalintch0c)
        #print(self.totalintch1c)
        
        #calculate charge proportional to dose
        self.totalchargedosenc = self.totalintch1nc - self.totalintch0nc
        #print(self.totalchargedose)
        
        #calculate relative dose
        self.totalreldose = (self.totalchargedosenc / float(dmetadata['Reference Charge'])) * 100
        
        #calculate absolute dose
        self.totalabsdosecG = self.totalchargedosenc * float(dmetadata['Calibration Factor'])
        
        #Do the calculatios for the individual beams in the file
        #First we find the times when individual beams start and finish
        dfchanges =  df.loc[df.ch1diff.abs() > 1e-9, ['ch1diff', 'time']].copy()
        dfchanges['timediff'] = dfchanges.time.diff()
        dfchanges.fillna(2, inplace=True)
        dftimes =  dfchanges[dfchanges.timediff > 0.5].copy()
        self.starttimes = dftimes.loc[dftimes.ch1diff > 0, 'time']
        #print (self.starttimes)
        self.finishtimes = dftimes.loc[dftimes.ch1diff < 0, 'time']
        #print (self.finishtimes)
        
        #Now we calculate the integrals of each beam and put it in a list
        self.listaintch0nc = []
        self.listaintch1nc = []
        self.linearregions = []
        self.listachargedosenc = []
        self.listareldose = []
        self.listaabsdosecG = []
        self.listalrscenes = []
        for (nu, (st, ft)) in enumerate(zip(self.starttimes, self.finishtimes)):
                self.linearregions.append(pg.LinearRegionItem(values=(st-2, ft+2), movable=False))
                intch0beamnnc = df.loc[(df.time>(st-2))&(df.time<(ft+2)), 'ch0zc'].sum()*1e9
                intch1beamnnc = df.loc[(df.time>(st-2))&(df.time<(ft+2)), 'ch1zc'].sum()*1e9
                self.listaintch0nc.append(intch0beamnnc)
                self.listaintch1nc.append(intch1beamnnc)
                chargedosebeamnnc = intch1beamnnc - intch0beamnnc
                self.listachargedosenc.append(chargedosebeamnnc)
                reldosebeamn = chargedosebeamnnc / float(dmetadata['Reference Charge']) * 100
                self.listareldose.append(reldosebeamn)
                absdosebeamncG = chargedosebeamnnc * float(dmetadata['Calibration Factor'])
                self.listaabsdosecG.append(absdosebeamncG)
                #print ('Charge prop. to dose of beam %s: %.3f nC' %(nu+1, chargedosebeamn))
        
        self.listalrscenes = [lr.scene() for lr in self.linearregions]
        self.plotitemchs.clear()
        #draw the new plots with zeros corrected
        self.curvech0.setData(df.time, df.ch0zc)
        self.curvech1.setData(df.time, df.ch1zc)
        self.legend.scene().removeItem(self.legend)
        self.legend = self.plotitemchs.addLegend()
        self.plotitemchs.addItem(self.curvech0)
        self.plotitemchs.addItem(self.curvech1)
        
        for lr in self.linearregions:
                self.plotitemchs.addItem(lr)
        
        self.plotitemchs.scene().sigMouseMoved.connect(self.mouseMoved)          
        
        #Put integrals in the graph
        self.ch0text = pg.TextItem('Charge: %.2f nC' %(self.totalintch0nc), color = '#ff0000')
        self.ch0text.setPos((tf+ts)/2 - 2, df.ch0z.max()+ 0.5e-9)
        self.plotitemchs.addItem(self.ch0text)
        
        self.ch1text = pg.TextItem('Charge: %.2f nC Char. prop. to dose: %.2f nC\n'
                                   'Rel. Dose: %.2f %% Abs. dose: %.2f cGy' %(self.totalintch1nc,
                                                                              self.totalchargedosenc,
                                                                              self.totalreldose,
                                                                              self.totalabsdosecG),
                                                                              color ='#0000ff')
        self.ch1text.setPos((tf+ts)/2 - 5, df.ch1z.max()+ 0.5e-9)
        self.plotitemchs.addItem(self.ch1text)
        
        #If batch file is selected, load the next line in the file in the dmetadata
        #and in metadata gui
        """if mymainmenu.mymetadata.cbbatchfile.isChecked():
            self.batchlinenumbnow = mymainmenu.mymetadata.batchfilelinenumb.value()
            dfbatch = pd.read_csv('batchfile.csv').astype(str)
            self.batchlinenumbnext = self.batchlinenumbnow + 1
            if self.batchlinenumbnext < len(dfbatch):
                mymainmenu.mymetadata.batchfilelinenumb.setValue(self.batchlinenumbnext)
                global dmetadata
                dmetadata = dfbatch.iloc[self.batchlinenumbnext,:].to_dict()
                mymainmenu.mymetadata.metadatadictogui()
                
        #Now ready for the next measurement"""
        
        #Save data in files and close files
        
        self.filemeas = open ('./rawdata/%s.csv' %dmetadata['File Name'], 'w')

        for key in metadatakeylist:
            self.filemeas.write('%s,%s\n' %(key,dmetadata[key]))

        self.filemeas.write('time,temp,ch0,ch1,PS,-12V,5V,10.58V\n')
        
        for i in range(len(self.times)):
            self.filemeas.write('%s,%s,%s,%s,%s,%s,%s,%s\n' %(self.times[i],
                                                              self.tempmeas[i],
                                                              self.ch0meas[i],
                                                              self.ch1meas[i],
                                                              self.PScmeas[i],
                                                              self.minus12Vcmeas[i],
                                                              self.cV5meas[i],
                                                              self.cV1058meas[i]))
        self.filemeas.write('Total Charge ch0 (nC),%.4f\n' %self.totalintch0nc)
        self.filemeas.write('Total Charge ch1 (nC),%.4f\n' %self.totalintch1nc)
        self.filemeas.write('Charge proportional to absolute dose (nC),%.4f\n' %self.totalchargedosenc)
        self.filemeas.write('Relative dose (%%),%.4f\n' %self.totalreldose)
        self.filemeas.write('Absolute dose (cGy),%.4f' %self.totalabsdosecG)
        self.filemeas.close()
        #self.afterstopping()
        


    def mouseMoved(self, evt):
        listaindex = [lr.sceneBoundingRect().contains(evt) for lr in self.linearregions]
        if (sum(listaindex)) > 0:
            #find the index where the True value is
            gi = listaindex.index(True)
            self.ch0text.setText('Charge: %.2fnC' %(self.listaintch0nc[gi]))
            self.ch1text.setText('Charge: %.2f nC Char. prop. to dose: %.2f nC\n'
                                 'Rel. Dose: %.2f %% Abs. dose: %.2f cGy' %(self.listaintch1nc[gi],
                                                                            self.listachargedosenc[gi],
                                                                            self.listareldose[gi],
                                                                            self.listaabsdosecG[gi]))
                
        else:
            self.ch0text.setText('Charge: %.2fnC' %(self.totalintch0nc))
            self.ch1text.setText('Charge: %.2f nC Char. prop. to dose: %.2f nC\n'
                                 'Rel. Dose: %.2f %% Abs. dose: %.2f cGy' %(self.totalintch1nc,
                                                                            self.totalchargedosenc,
                                                                            self.totalreldose,
                                                                            self.totalabsdosecG))
        

    
    def backmainmenu(self):
        self.close()
        mymainmenu.show()


def goodbye():
    #print ('bye')
    #print (dmetadata['Date Time'])
    metadatafile = open('metadata.csv', 'w')
    for key in metadatakeylist:
        metadatafile.write('%s,%s\n' %(key, dmetadata[key]))
        #print ('%s,%s\n' %(key, dmetadata[key]))
    metadatafile.close()
    #mymainmenu.mymeasure.measurepowerthread.stopping()
    
    
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    mymainmenu = MainMenu()
    atexit.register(goodbye)
    mymainmenu.show()
    sys.exit(app.exec_())
