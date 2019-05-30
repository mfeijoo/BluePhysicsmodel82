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


number_of_ch = 2

colors = ['#C0392B', '#3498DB']


#Read Metadata file and load data in a dictionary
metadatakeylist = ['Save File As', 'File Name', 'Test Time',
                   'Show Relative Dose',
                   'Calibration Factor', 'Temperature Correction',
                   'Reference diff Voltage',
                   'Integrator Mode', 'Integration Time', 'Reset Time',
                   'Facility', 'Investigator', 'Source','Brand',
                   'Particles', 'Energy', 'Dose Rate', 'Gantry',
                   'Collimator', 'Couch', 'Field Size X1',
                   'Field Size X2', 'Field Size Y1', 'Field Size Y2',
                   'Ion Chamber', 'Setup', 'Distance', 'MU', 'PS',
                   'Transducer Type', 'Sensor Type',
                   'Sensor Size', 'Fiber Diameter', 'Fiber Length',
                   'Sensor Position X', 'Sensor Position Y',
                   'Sensor Position Z','Reference Fiber Diameter',
                   'Reference Fiber Length', 'Comments']

metadatafile = open('metadata.csv', 'r')
listmetadata = [pair.split(',') for pair in metadatafile.readlines()]
metadatafile.close()
dmetadata = {key:value.strip() for [key,value] in listmetadata}

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
        file = open('./rawdata/emulatormeasurements.csv', 'r')
        self.lines =  file.readlines()
        file.close()
        
    def __del__(self):
        self.wait()
        
    def run(self):
        for line in self.lines:
            self.ser2.write(line.encode())
            #print(line)
            if self.stop:
                break
            time.sleep(0.320)
        
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
        #self.ser = serial.Serial ('/dev/pts/4', 115200, timeout=1)
        self.ser = serial.Serial ('/dev/ttyS0', 115200, timeout=1)

    def __del__(self):
        self.wait()

    def run(self):
        #One reading to discard garbge
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
                listatosend = [(int(reading[0])-tstart)/1000] + [float(i) for i  in reading[1:]]
                print (listatosend)
                self.info.emit(listatosend)
            except:
                pass
 

            
    def stopping(self):
        self.stop = True
        self.ser.close()
        #self.wait()
        #self.quit()
                   
       
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
        windowstitle = 'Blue Physics Model 8 File: %s' %(dmetadata['File Name'])
        self.setWindowTitle(windowstitle)
        self.mymeasure.setWindowTitle(windowstitle)
        self.mymetadata.setWindowTitle(windowstitle)
        self.myanalyze.setWindowTitle('Blue Physics Model 8 Analyze File:')
       
    def signals(self):
        #self.tbvoltage.clicked.connect(self.showvoltage)
        self.tbmeasure.clicked.connect(self.showmeasure)
        self.tboff.clicked.connect(app.quit)
        self.tbsettings.clicked.connect(self.showmetadata)
        #self.tbanalyze.clicked.connect(self.showanalyze)
        
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
        self.plot1buttons = [self.tbviewch0, self.tbviewch1]
        self.signals()
        self.relfileloaded = False
        
    def signals(self):
        self.tbmainmenuanalyze.clicked.connect(self.backtomainmenu)
        self.tbreffile.clicked.connect(self.selectfile)
        for butt in self.plot1buttons:
            butt.clicked.connect(self.plot1)
        self.tbviewraw.clicked.connect(self.plot1)
        self.tbviewint.clicked.connect(self.plot1)
        self.cbsecondplot.currentIndexChanged.connect(self.plot2)
        self.tbrelfile.clicked.connect(self.relfile)

    def relfile(self):
        if self.tbrelfile.isChecked():
            #a funciton to load a second relative file to compare
            #with reference file loaded as self.df
            relfilename = QFileDialog.getOpenFileName(self, 'Open file',
                                                      './rawdata',
                                             'measurements (*measurements.csv)')
            self.dfrel = pd.read_csv(relfilename[0], skiprows=41)
            self.dfrel.columns = ['%srel' %c for c in self.dfrel.columns]
            #loading powers of sencond file
            self.dfrelp = pd.read_csv('%spowers.csv' %relfilename[0][:-16],
                                        skiprows=41)
            self.dfrelp.columns = ['%srel' %c for c in self.dfrelp.columns]
            #print (self.dfrelp.head())
            #flag to inidcate we have a relative file loaded
            self.relfileloaded = True
                
            #list of channels in the relative file, removing time
            self.lchsrel = self.dfrel.columns[1:]
                
            #A routine to calculate the zeros
            for ch in self.lchsrel:
                self.dfrel['%sz' %ch] = self.dfrel[ch]-self.dfrel.loc[:25, ch].mean()

            #A routine to calculate the relative time with the reference
            #measurement under self.df
            self.dfrel['ch1reldiff'] = self.dfrel.ch1rel.diff()
            self.df['ch1diff'] = self.df.ch1.diff()
            t2 = list(self.dfrel.loc[self.dfrel.ch1reldiff <-2, 'timerel'])[0]
            t1 = list(self.df.loc[self.df.ch1diff<-2, 'time'])[0]
            timediff = t2 - t1
            self.dfrel['newtimerel'] = self.dfrel.timerel - timediff
            self.dfrelp['newtimerel'] = self.dfrelp.timerel - timediff

            #plot the relative file
            self.plot1()
 
        else:
            self.relfileloaded = False



    def selectfile(self):
        self.tbrelfile.setEnabled(True)
        #self.ax1.clear()
        #self.ax2.clear()
        filename = QFileDialog.getOpenFileName(self, 'Open file',
                                               './rawdata',
                                    'measurements (*measurements.csv)')
        filename_only = filename[0].split('/')[-1]
        filenamepowers = '%spowers.csv' %filename[0][:-16]
        self.setWindowTitle('Blue Physics Model 8 Analyze File: %s'
                             %filename_only)
        self.dfp = pd.read_csv(filenamepowers, skiprows=41)
        #print (self.dfp.head())
        self.df = pd.read_csv(filename[0], skiprows=41)
        #list of channels in the file, removing time
        self.lchs = self.df.columns[1:]
        
        #A routine to calculate the zeros
        for ch in self.lchs:
            self.df['%sz' %ch] = self.df[ch]-self.df.loc[:25, ch].mean()

        #Plot the selected file running the current functions
        self.plot1()

        for but in self.plot1buttons:
            but.setEnabled(True)
        self.cbsecondplot.setEnabled(True)
        self.tbviewraw.setEnabled(True)
        self.tbviewint.setEnabled(True)


    def plot1(self):

        self.ax1.clear()
        self.ax1.grid(True)
        
        for ch in self.plot1buttons:
            if ch.isChecked():
                if self.tbviewraw.isChecked():
                    self.ax1.plot(self.df.time, self.df[ch.text()],
                                  color=dcolors[ch.text()],
                                  label=ch.text())
                    if self.relfileloaded:
                        self.ax1.plot(self.dfrel.newtimerel, self.dfrel['%srel' %ch.text()],
                                       color = 'r',
                                       alpha = 0.5,
                                       label = '%srel' %ch.text())
                else:
                    self.ax1.plot(self.df.time, self.df['%sz' %ch.text()],
                                  color=dcolors[ch.text()],
                                  label=ch.text())
                    #find x coord for text
                    xcoord = self.df.time.max()/2
                    #find y coord for text
                    ycoord = self.df['%sz' %ch.text()].max()
                    #calculate the integral
                    integral = self.df['%sz' %ch.text()].sum()
                    #Put integral in a text
                    self.ax1.text(xcoord, ycoord, 'int: %s %.3f' 
                                                %(ch.text(), integral),
                                  color=dcolors[ch.text()])

                    if self.relfileloaded:
                        self.ax1.plot(self.dfrel.newtimerel, self.dfrel['%srelz' %ch.text()],
                                      color = dcolors[ch.text()],
                                      alpha = 0.5,
                                      label = '%srel' %ch.text())
                        xcoordrel = self.dfrel.newtimerel.max()/2
                        ycoordrel = self.dfrel['%srelz' %ch.text()].max()
                        integralrel = self.dfrel['%srelz' %ch.text()].sum()
                        self.ax1.text(xcoordrel, ycoordrel,
                                'int: %s %.3f' %(ch.text(), integralrel),
                                color = dcolors[ch.text()],
                                alpha = 0.5)
                                        
                        

        self.ax1.set_ylabel('volts (V)')
        self.ax1.legend()
        self.canvas.draw()
 
        
        
    def plot2(self, index):
        
        self.ax2.clear()
        self.ax2.set_ylabel('Volts (V)')
        
        if index == 1:
            self.dfp.set_index('time').loc[:,'temp'].plot(ax=self.ax2,
                                                        grid=True)
            if self.relfileloaded:
                self.dfrelp.set_index('newtimerel').loc[:, 'temprel'].plot(ax=self.ax2,
                                                                    grid=True,
                                                                    alpha=0.5)
            self.ax2.set_ylabel('Temp (C)')
        elif index == 2:
            self.dfp.set_index('time').loc[:,['PS0', 'PS1']].plot(ax=self.ax2, grid=True)
            if self.relfileloaded:
                self.dfrelp.set_index('newtimerel').loc[:, ['PS0rel', 'PS1rel']].plot(ax=self.ax2,
                                                                        grid = True,
                                                                        alpha=0.5)
        elif index == 3:
            self.dfp.set_index('time').loc[:,'61V':'12V'].plot(ax=self.ax2, grid=True)
            if self.relfileloaded:
                self.dfrelp.set_index('newtimerel').loc[:, '61Vrel':'12Vrel'].plot(ax=self.ax2,
                                                                        grid=True,
                                                                        alpha = 0.5)
        elif index == 4:
            self.dfp.set_index('time').loc[:,'08V'].plot(ax=self.ax2, grid=True)
            if self.relfileloaded:
                self.dfrelp.set_index('newtimerel').loc[:,'08Vrel'].plot(ax=self.ax2,
                                                                grid=True,
                                                                alpha = 0.5)
       

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
        self.metadatadictogui()
        self.signals()
        #self.cbsaveoncurrentmeasurements.setChecked(True)
        
    def metadatadictogui(self):
        if dmetadata['Save File As'] == 'Default':
            self.cbdefault.setChecked(True)
            self.cbdatetime.setChecked(False)
            self.cbcustom.setChecked(False)
            self.lefilename.setText('default')
        elif dmetadata['Save File As'] == 'Date/Time':
            self.cbdefault.setChecked(False)
            self.cbdatetime.setChecked(True)
            self.cbcustom.setChecked(False)
            self.lefilename.setText(dmetadata['File Name'])
        elif dmetadata['Save File As'] == 'Custom':
            self.cbdefault.setChecked(False)
            self.cbdatetime.setChecked(False)
            self.cbcustom.setChecked(True)
            #self.lefilename.setReadOnly(False)
            self.lefilename.setText(dmetadata['File Name'])
        
        self.sbtesttime.setValue(int(dmetadata['Test Time']))

        if dmetadata['Integrator Mode'] == 'TRUE':
            self.tbintmode.setChecked(True)
            self.tbpulsemode.setChecked(False)
        else:
            self.tbintmode.setChecked(False)
            self.tbpulsemode.setChecked(True)
        if dmetadata['Show Relative Dose'] == 'TRUE':
            self.cbrelcalc.setChecked(True)
        else:
            self.cbrelcalc.setChecked(False)
        self.sbcalibfactor.setValue(float(dmetadata['Calibration Factor']))
        self.sbtempcorrec.setValue(float(dmetadata['Temperature Correction']))
        self.sbreferencedose.setValue(float(dmetadata['Reference diff Voltage']))
        self.sbinttime.setValue(int(dmetadata['Integration Time']))
        self.sbresettime.setValue(int(dmetadata['Reset Time']))
        self.lefacility.setText(dmetadata['Facility'])
        self.leinvestigator.setText(dmetadata['Investigator'])
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
        self.sbionchamber.setValue(float(dmetadata['Ion Chamber']))
        self.linacssdsad.setCurrentText(dmetadata['Setup'])
        self.linacssdsaddist.setValue(int(dmetadata['Distance']))
        self.linacmus.setValue(int(dmetadata['MU']))
        self.transducertype.setCurrentText(dmetadata['Transducer Type'])
        self.sensortype.setCurrentText(dmetadata['Sensor Type'])
        self.sensorsize.setCurrentText(dmetadata['Sensor Size'])
        self.sensorfiberdiam.setCurrentText(dmetadata['Fiber Diameter'])
        self.sensorfiberlength.setValue(int(dmetadata['Fiber Length']))
        self.sensorpositionx.setValue(float(dmetadata['Sensor Position X']))
        self.sensorpositiony.setValue(float(dmetadata['Sensor Position Y']))
        self.sensorpositionz.setValue(float(dmetadata['Sensor Position Z']))
        self.referencefiberdiam.setCurrentText(dmetadata['Reference Fiber Diameter'])
        self.referencefiberlength.setValue(int(dmetadata['Reference Fiber Length']))
        self.comments.setText(dmetadata['Comments'])
        
    def signals(self):
        self.tbgeneral.clicked.connect(self.showgeneralpage)
        self.tblinac.clicked.connect(self.showlinacpage)
        self.tbsensor.clicked.connect(self.showsensorpage)
        self.tbcomments.clicked.connect(self.showcommentspage)
        self.tbmainmenumetadata.clicked.connect(self.backtomainmenu)
        self.tbintmode.clicked.connect(self.integratorpulse)
        self.tbpulsemode.clicked.connect(self.integratorpulse)
        self.cbdefault.clicked.connect(self.saveasfilename)
        self.sbinttime.valueChanged.connect(self.tbintmodechange)
        self.sbresettime.valueChanged.connect(self.tbintmodechange)
        self.cbdatetime.clicked.connect(self.saveasfilename)
        self.cbcustom.clicked.connect(self.saveasfilename)
        self.cbsaveoncurrentmeasurements.clicked.connect(self.saveoncurrent)

    def tbintmodechange(self, value):
        self.tbintmode.setChecked(False)
        self.tbpulsemode.setChecked(True)    


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
            elif self.cbdatetime.isChecked():
                self.lefilename.setText(time.strftime ('%d %b %Y %H:%M:%S'))
                self.lefilename.setReadOnly(True)
            elif self.cbcustom.isChecked():
                self.lefilename.setText('')
                self.lefilename.setReadOnly(False)
        
    def integratorpulse(self):
        self.sermode = serial.Serial ('/dev/ttyS0', 115200, timeout=1)
        if self.tbintmode.isChecked():
            inttime = self.sbinttime.value()
            resettime = self.sbresettime.value()
            stringtosend = 'i%s,%s' %(inttime, resettime)
            bytestosend = stringtosend.encode('utf-8')
            self.sermode.write(bytestosend)
            print ('integrator mode set, integratortime: %s, resettime: %s' %(inttime, resettime))
        else:
            self.sermode.write('p'.encode('utf-8'))
            print ('pulse mode')
        
        self.sermode.close()
        
    def metadataguitodic(self):
        if self.cbdefault.isChecked():
            dmetadata['Save File As'] =  'Default'
        if self.cbdatetime.isChecked():
            dmetadata['Save File As'] =  'Date/Time'
        if self.cbcustom.isChecked():
            dmetadata['Save File As'] = 'Custom'
        dmetadata['File Name'] = self.lefilename.text()
        dmetadata['Test Time'] = str(self.sbtesttime.value())
        
        if self.tbintmode.isChecked():
            dmetadata['Integrator Mode'] = 'TRUE'
        else:
            dmetadata['Integrator Mode'] = 'FALSE'
        if self.cbrelcalc.isChecked():
            dmetadata['Show Relative Dose'] = 'TRUE'
        else:
            dmetadata['Show Relative Dose'] = 'FALSE'
        dmetadata['Calibration Factor'] = str(self.sbcalibfactor.value())
        dmetadata['Temperature Correction'] = str(self.sbtempcorrec.value())
        dmetadata['Reference diff Voltage'] = str(self.sbreferencedose.value())
        dmetadata['Integration Time'] = str(self.sbinttime.value())
        dmetadata['Reset Time'] = str(self.sbresettime.value())
        dmetadata['Facility'] = self.lefacility.text()
        dmetadata['Investigator'] = self.leinvestigator.text()
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
        dmetadata['Ion Chamber'] = str(self.sbionchamber.value())
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
        loadUi("measureguim82.ui", self)
        
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
        self.plotitemvoltages = pg.PlotItem(title ='<span style="color: #990099">5V</span> '
                                                    '& <span style="color: #009999">12V</span> '
                                                    '& <span style="color: #990000">10.58V</span> '
                                                    '& <span style="color: #009900">-12V</span> ')
        self.plotitemvoltages.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemvoltages.setLabel('bottom', 'Time', units = 's')
        self.plotitemvoltages.setLabel('left', 'Voltage', units = 'V')
        self.plotitem613 = pg.PlotItem(title ='<span style="color: #990099">61.3V</span>')
        self.plotitem613.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitem613.setLabel('bottom', 'Time', units = 's')
        self.plotitem613.setLabel('left', 'Voltages', units = 'V')
        self.plotitemtemp = pg.PlotItem(title = '<span style="color: #002525">Temp C')
        self.plotitemtemp.showGrid(x = True, y = True, alpha = 0.5)
        self.plotitemtemp.setLabel('bottom', 'Time', units = 's')
        self.plotitemtemp.setLabel('left', 'Temperature', units = 'C')
        
        self.curvech0 = self.plotitemchs.plot(pen=pg.mkPen(color='#C0392B', width=2),
                                              name = 'Ch0',
                                              autoDownsample = False)
                                              
        self.curvech1 = self.plotitemchs.plot(pen=pg.mkPen(color='#3498DB', width=2),
                                              name = 'Ch1',
                                              autoDownsample = False)
                
        self.curvePS = self.plotitemPS.plot(pen=pg.mkPen(color='#000099', width=2),
                                                   autoDownsample = False)

        self.curve613V = self.plotitem613.plot(pen=pg.mkPen(color='#990099', width=2),
                                                   autoDownsample = False)
        self.curve5V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#990099',
                                                                          width=2),
                                                   autoDownsample = False)
        self.curveminus12V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#009900',
                                                                 width=2),
                                                  autoDownsample = False)
        self.curve1058V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#990000',
                                                                             width=2),
                                                   autoDownsample = False)
        self.curve12V = self.plotitemvoltages.plot(pen=pg.mkPen(color='#009999',
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
            self.graphicsView.addItem(self.plotitem613, row=1, col=0)
        elif index == 4:
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
        self.v5Vmeas = []
        self.v12Vmeas = []
        self.v1058Vmeas = []
        self.minus12Vmeas = []
        self.PSmeas = []
        self.v613Vmeas = []    
        

        self.tbstopmeasure.setEnabled(True)
        self.tbstartmeasure.setEnabled(False)
        
        if dmetadata['Save File As'] == 'Date/Time':
            dmetadata['File Name'] = time.strftime ('%d %b %Y %H:%M:%S')

        #only if emulator
        #self.emulator = EmulatorThread()
        #self.emulator.start()
        
        self.measurethread = MeasureThread()
        self.measurethread.start()
        self.measurethread.info.connect(self.update)
        self.tbstopmeasure.clicked.connect(self.stopmeasurement)

      
    def update(self, measurements):
        self.times.append(measurements[0])
        self.tempmeas.append(measurements[1])
        self.ch0meas.append(measurements[2])
        self.ch1meas.append(measurements[3])
        self.v5Vmeas.append(measurements[4])
        self.v1058Vmeas.append(measurements[5])
        self.v12Vmeas.append(measurements[6])
        self.minus12Vmeas.append(measurements[7])
        self.PSmeas.append(measurements[8])
        self.v613Vmeas.append(measurements[9])
        
        
        self.curvetemp.setData(self.times[::3], self.tempmeas[::3])
        self.curvech0.setData(self.times[::3], self.ch0meas[::3])
        self.curvech1.setData(self.times[::3], self.ch1meas[::3])
        self.curve5V.setData(self.times[::3], self.v5Vmeas[::3])
        self.curve12V.setData(self.times[::3], self.v12Vmeas[::3])
        self.curve1058V.setData(self.times[::3], self.v1058Vmeas[::3])
        self.curveminus12V.setData(self.times[::3], self.minus12Vmeas[::3])
        self.curvePS.setData(self.times[::3], self.PSmeas[::3])
        self.curve613V.setData(self.times[::3], self.v613Vmeas[::3])
        
        
        
    def stopmeasurement(self):
        #emulator
        #self.emulator.stopping()
        self.measurethread.stopping()
        self.tbstopmeasure.setEnabled(False)
        self.tbstartmeasure.setEnabled(True)
        
        #Global flag idicating measurements are done
        global measurements_done
        measurements_done = True
        
        #Save data in files and close files
        
        self.filemeas = open ('./rawdata/%smeasurements.csv' %dmetadata['File Name'], 'w')

        for key in metadatakeylist:
            self.filemeas.write('%s,%s\n' %(key,dmetadata[key]))

        self.filemeas.write('time,temp,ch0,ch1,5V,12V,10.38V,-12V,PS,61.3V\n')
        
        for i in range(len(self.times)):
            self.filemeas.write('%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' %(self.times[i],
                                                                self.tempmeas[i],
                                                                self.ch0meas[i],
                                                                self.ch1meas[i],
                                                                self.v5Vmeas[i],
                                                                self.v12Vmeas[i],
                                                                self.v1058Vmeas[i],
                                                                self.minus12Vmeas[i],
                                                                self.PSmeas[i],
                                                                self.v613Vmeas[i]))
        self.filemeas.close()
        
        #Calculate integrals
        #first put in a dataframe
        df = pd.DataFrame({'time': self.times, 'ch0': self.ch0meas, 'ch1':self.ch1meas,
              '5V': self.v5Vmeas, '12V':self.v12Vmeas, '10.58V':self.v1058Vmeas,
              '-12V':self.minus12Vmeas, 'PS':self.PSmeas, '61.3V':self.v613Vmeas})
              
        #Calculate start and end of radiation
        #Assuming ch1 is where the sensor is and it has the largest differences
        df['ch1diff'] = df.ch1.diff()
        ts = df.loc[df.ch1diff == df.ch1diff.max(), 'time'].item()
        tf = df.loc[df.ch1diff == df.ch1diff.min(), 'time'].item()
        
        #calculate the zeros
        df['ch0z'] = df.ch0 - df.loc[(df.time<ts)|(df.time>tf), 'ch0'].mean()
        df['ch1z'] = df.ch1 - df.loc[(df.time<ts)|(df.time>tf), 'ch1'].mean()
        
        #calculate integrals not corrected
        intch0 = df.loc[(df.time>ts)&(df.time<tf), 'ch0z'].sum()
        intch1 = df.loc[(df.time>ts)&(df.time<tf), 'ch1z'].sum()
        
        #Calculate ch0 corrected
        df['ch0zc'] = df.ch0z * float(dmetadata['Calibration Factor'])
        df['ch1zc'] = df.ch1z
        
        #Calculate integrals corrected
        intch0c = df.loc[(df.time>ts)&(df.time<tf), 'ch0zc'].sum()
        intch1c = df.loc[(df.time>ts)&(df.time<tf), 'ch1zc'].sum()
        
        #calculate absolute dose
        absdose = intch1c - intch0c
        
        #calculate relative dose
        reldose = (absdose / float(dmetadata['Reference diff Voltage'])) * 100
        
        #draw the new plots with zeros corrected
        self.curvech0.setData(df.time, df.ch0zc)
        self.curvech1.setData(df.time, df.ch1zc)
        
        
        #Put integrals in the graph
        ch0text = pg.TextItem('Int %s: %.2fV' %('ch0', intch0), color = '#C0392B')
        ch0text.setPos((tf+ts)/2 - 2, df.ch0z.max()+ 0.5)
        self.plotitemchs.addItem(ch0text)
        
        ch1text = pg.TextItem('Int %s: %.2f, Abs. Dose: %.2f, Rel. Dose: %.2f' %('ch1', intch1, absdose, reldose), color = '#3498DB')
        ch1text.setPos((tf+ts)/2 - 5, df.ch1z.max()+ 0.5)
        self.plotitemchs.addItem(ch1text)
        
        
        
        
    def backmainmenu(self):
        self.close()
        mymainmenu.show()


def goodbye():
    print ('bye')
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
