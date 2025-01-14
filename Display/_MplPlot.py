"""
Code made available for the ISMRM 2015 Sunrise Educational Course

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
    
Alan Kuurstra    
Philip J. Beatty (philip.beatty@gmail.com)
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import _DisplayDefinitions as dd
from PyQt4 import QtCore,QtGui
import numpy as np
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

class _MplPlot(FigureCanvas):
    def __init__(self, complexData, parent=None,dataType=None,initMarkerPosn=None, colors=None, title=None):        
        #
        # Qt related initialization
        #        
        self.fig=mpl.figure.Figure() 
        FigureCanvas.__init__(self,self.fig)
        self.setParent(parent) #the FigureCanvas class doesn't have the option to pass the parent to the __init__() constructer, must set it manually
        FigureCanvas.setSizePolicy(self,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)        
        self.setMinimumSize(200,200)
        FigureCanvas.updateGeometry(self)
        
        #
        # Event related initialization
        #        
        self.mpl_connect('button_press_event',self.PressEvent)           
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)        
        #self.mpl_connect('key_press_event',self.keyPressEventsdd) 
        
        #
        # Internal data model initialization
        #         
        self.setComplexData(complexData)
        if dataType is None:
            self.setDataType(dd.ImageType.mag)
        else:
            self.setDataType(dataType)
        self.setMarkerPosn(initMarkerPosn)
        
        #
        #Initialize internal variables that determine how visualization objects display data model
        #
        self.colors=colors
        if self.colors==None:
            self.colors=dd.PlotColours.colours 
                        
        #
        # Initialize objects visualizing the internal data model
        #
        #1d plot
        self.axes=self.fig.add_subplot(111)
        if title is not None:
            self.axes.set_title(title) 
        #zoom functionality
        self.toolbar=NavigationToolbar2QTAgg(self,self)
        self.toolbar.hide()
        self.toolbar.zoom()        
        #initialization of lines and markers        
        self.createLines()  
        self.createMarkers()
        
    #==================================================================
    #slots to deal with mpl mouse events
    #==================================================================        
    def PressEvent(self,event): 
        #with matplotlib event, button 1 is left, 2 is middle, 3 is right
        if event.button==3:            
            self.toolbar.home()
        if event.button==2:
            plt.figure()             
            for line in range(self.complexData.shape[1]):                                      
                plt.plot(self.applyDataType(self.complexData[:,line]),self.colors[line])            

    #==================================================================
    #functions that set internal data
    #==================================================================
    def setComplexData(self,newComplexData):
        self.complexData=newComplexData 
        if self.complexData.ndim == 1:
            self.complexData = self.complexData[:,np.newaxis]  
    def setDataType(self, dataType):
        self._dataType = dataType
    def setMarkerPosn(self,newMarkerPosn):
        if newMarkerPosn is None:
            self.markerPosn=newMarkerPosn
        else:
            self.markerPosn = np.minimum(np.maximum(newMarkerPosn,0),self.complexData.shape[0]-1)
        
    #==================================================================            
    #functions that update objects visualizing internal data
    #==================================================================        
    def setLines(self):
        for line in range(self.complexData.shape[1]):                           
            self.lines[line][0].set_ydata(self.applyDataType(self.complexData[:,line]))          
        if self._dataType == dd.ImageType.phase:
            self.axes.set_ylim(-np.pi,np.pi)
        else: 
            self.axes.set_ylim(auto=True)                   
            self.axes.relim()        
            self.axes.autoscale_view(scalex=False)        
    def setMarkers(self): 
        if self.markerPosn is not None:
            for plotNum in range(self.complexData.shape[1]):            
                self.markers[plotNum][0].set_data(self.markerPosn,self.applyDataType(self.complexData[self.markerPosn,plotNum]))
    def createLines(self):
        self.lines=[]
        for line in range(self.complexData.shape[1]):                       
            self.lines.append(self.axes.plot(self.applyDataType(self.complexData[:,line]),self.colors[line]))        
        self.axes.set_xlim(0,self.complexData.shape[0]-1)
    def createMarkers(self):
        if self.markerPosn is not None:
            self.markers=[]
            for plotNum in range(self.complexData.shape[1]):            
                self.markers.append(self.axes.plot(self.markerPosn,self.applyDataType(self.complexData[self.markerPosn,plotNum]),'kx'))
    def drawLinesAndMarkers(self):
        self.draw()
    #==================================================================        
    #helper functions
    #==================================================================    
    def applyDataType(self,complexData):
        if self._dataType == dd.ImageType.mag:
            data = np.abs(complexData)
        elif self._dataType == dd.ImageType.phase:
            data = np.angle(complexData)
        elif self._dataType == dd.ImageType.real:
            data = np.real(complexData)
        elif self._dataType == dd.ImageType.imag:
            data = np.imag(complexData)
        else:
            print "Data type not recognized"
            return
        return data
        
    #==================================================================        
    #convenience functions to change data and update visualizing objects
    #==================================================================        
    def showDataTypeChange(self,index):
        self.setDataType(index)
        self.setLines()
        self.setMarkers()
        self.drawLinesAndMarkers()
    def showComplexDataChange(self,newComplexData):
        self.setComplexData(newComplexData)   
        self.setLines()
        self.setMarkers()
        self.drawLinesAndMarkers()
    def showComplexDataAndMarkersChange(self,newComplexData,newMarkerPosn):
        self.setComplexData(newComplexData)
        self.setMarkerPosn(newMarkerPosn)
        self.setLines()
        self.setMarkers()
        self.drawLinesAndMarkers()
        
    #==================================================================        
    #functions related to Qt
    #==================================================================        
    def sizeHint(self):
        return QtCore.QSize(300,183)
        
