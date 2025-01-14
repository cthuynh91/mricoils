"""
Code made available for the ISMRM 2015 Sunrise Educational Course

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
    
Alan Kuurstra    
Philip J. Beatty (philip.beatty@gmail.com)
"""
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4 import QtCore,QtGui
import _Core
import _DisplayDefinitions as dd

        
class _MplImage(FigureCanvas):
    from _DisplaySignals import *      
    def __init__(self, complexImage, parent=None, interpolation='bicubic', origin = 'lower', imageType=None, windowLevel=None, location=None, locationLabels=None, colormap=None ):        
        #
        # Qt related initialization
        #
        _Core._create_qApp()        
        self.fig=mpl.figure.Figure()
        FigureCanvas.__init__(self,self.fig)  
        FigureCanvas.setSizePolicy(self,QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        #
        # Event related initialization
        #
        self.mpl_connect('motion_notify_event',self.MoveEvent)        
        self.mpl_connect('button_press_event',self.PressEvent)
        self.mpl_connect('button_release_event',self.ReleaseEvent)
        self.leftMousePress=False
        self.middleMousePress=False
        self.rightMousePress=False
        
        #
        # Internal data model initialization
        #        
        self.complexImageData = complexImage  
        self.location = np.minimum(np.maximum(location, [0,0]), np.subtract(self.complexImageData.shape,1)).astype(np.int)
        
        #
        # Initialize objects visualizing the internal data model
        #
        if colormap is None:
            self.colormap = mpl.cm.Greys_r
        else:
            self.colormap = colormap
        #labels
        currLabels = [{'color': 'r', 'textLabel': "X"},{'color': 'b', 'textLabel': "Y"},{'color': 'g', 'textLabel': "Z Slice"}]
        if locationLabels is not None:
            currLabels = locationLabels
        #image
        self.fig.patch.set_color(currLabels[2]['color'])                
        self.axes=self.fig.add_axes([.1,.05,.8,.8])     
        self.axes.hold(False)
        if origin != 'upper' and origin != 'lower':
            print "origin parameter not understood, defaulting to 'lower'"
            origin='lower'
        self.img=self.axes.imshow(np.zeros(complexImage.shape).T, interpolation=interpolation, origin=origin)
        self._imageType=0
        self.setMplImg()
        self.title=self.axes.text(0.5, 1.08, currLabels[2]['textLabel'],horizontalalignment='center',fontsize=18,transform = self.axes.transAxes)
        self.axes.xaxis.set_visible(False)
        self.axes.yaxis.set_visible(False) 
        self.axes.patch.set_facecolor('black')
        #cursor lines
        self.hline=self.axes.axhline(y=location[1],linewidth=1,color=currLabels[0]['color']) 
        self.htxt=self.axes.text(0,location[1],currLabels[0]['textLabel'],bbox=dict(facecolor='white', alpha=0.7),va='center',ha='right')                 
        self.vline=self.axes.axvline(x=location[0],linewidth=1,color=currLabels[1]['color'])         
        self.vtxt=self.axes.text(location[0],0,currLabels[1]['textLabel'], bbox=dict(facecolor='white', alpha=0.7),va='bottom',ha='center') 
        
        #
        #Initialize internal variables that determine how visualization objects display data model
        #
        self.intensityLevelCache = np.zeros(4)
        self.intensityWindowCache = np.ones(4)
        self.intensityLevel = 0.0
        self.intensityWindow = 1.0
        self._imageType = dd.ImageType.mag
        self.enableWindowLevel = True
        
        self.setWindowLevelToDefault()
        if imageType is None:
            self.showImageTypeChange(dd.ImageType.mag)
        else:
            self.showImageTypeChange(imageType)
     
    def SaveImage(self, fname):
        img=self.img.get_array()
        cmap=cmap=self.img.get_cmap()
        origin=self.img.origin
        vmin,vmax=self.img.get_clim()

        mpl.pyplot.imsave(fname=fname+'.png', arr=img, cmap=cmap, origin=origin, vmin=vmin, vmax=vmax, format="png")
               
    #==================================================================
    #slots to deal with mpl mouse events
    #==================================================================
    def PressEvent(self,event): 
        #with matplotlib event, button 1 is left, 2 is middle, 3 is right        
        if event.button==1:
            self.leftMousePress=True        
        elif event.button==2:            
            self.middleMousePress=True
            img=self.img.get_array()
            cmap=cmap=self.img.get_cmap()
            origin=self.img.origin
            vmin,vmax=self.img.get_clim()
            mpl.pyplot.figure()
            mpl.pyplot.imshow(img,cmap=cmap,origin=origin, vmin=vmin,vmax=vmax)            
            #mpl.pyplot.imsave(fname="temp.png", arr=img, cmap=cmap, origin=origin, vmin=vmin, vmax=vmax, format="png")            
            
        elif event.button==3:            
            self.rightMousePress=True
                
        self.origIntensityWindow=self.intensityWindow            
        self.origIntensityLevel=self.intensityLevel
        self.origPointerLocation = [event.x, event.y]
        self.MoveEvent(event)         
    def ReleaseEvent(self,event): 
        if event.button==1:
            self.leftMousePress=False        
        elif event.button==2:            
            self.middleMousePress=False
        elif event.button==3:            
            self.rightMousePress=False              
    def MoveEvent(self,event):        
        if (self.rightMousePress and self.enableWindowLevel ):
            #"""
            levelScale = 0.001
            windowScale = 0.001
            
            dLevel = levelScale * float(self.origPointerLocation[1] - event.y) * self.dynamicRange
            dWindow = windowScale * float(event.x - self.origPointerLocation[0]) * self.dynamicRange

            newIntensityLevel = self.origIntensityLevel + dLevel
            newIntensityWindow = self.origIntensityWindow + dWindow
            self.signalWindowLevelChange.emit(newIntensityWindow,newIntensityLevel)
            
        if (self.leftMousePress):
            locationDataCoord = self.axes.transData.inverted().transform([event.x, event.y])            
            clippedLocation = np.minimum(np.maximum(locationDataCoord+0.5, [0,0]), np.subtract(self.complexImageData.shape,1))
            #print self.complexImageData.shape, locationDataCoord, clippedLocation
            self._signalCursorChange(clippedLocation)        
    def _signalCursorChange(self,location):
        #this function will be overwritten to use signals when the class is inherited        
        self.signalLocationChange.emit(location[0], location[1])
        
    #==================================================================
    #functions that set internal data
    #==================================================================
    def setComplexImage(self, newComplexImage):
        self.complexImageData = newComplexImage
    def setLocation(self, newLocation):           
        # clip newLocation to valid locations, this is now done in MoveEvent() before the ChangeLocation signal is emitted
        # however, there could still be problems if a control signals a location change that is out of bounds
        #newLocation = np.minimum(np.maximum(newLocation, [0,0]), np.subtract(self.complexImageData.shape,1)).astype(np.int)
        if (int(self.location[0]) != newLocation[0]) or (int(self.location[1]) != newLocation[1]):
            self.location = newLocation
    def setImageType(self, imageType):
        self._imageType = imageType 
        if imageType == dd.ImageType.mag or imageType == dd.ImageType.imag or imageType == dd.ImageType.real: 
            self.setMplImgColorMap(self.colormap)
            self.setWindowLevel(self.intensityWindowCache[imageType],self.intensityLevelCache[imageType])
            self.enableWindowLevel = True
        elif imageType == dd.ImageType.phase: 
            self.setMplImgColorMap(mpl.cm.hsv)                       
            self.setWindowLevel(2*np.pi,0)
            self.enableWindowLevel = False
    def setWindowLevel(self, newIntensityWindow,newIntensityLevel):
        #print 'window: %f, level %f' %(newIntensityWindow, newIntensityLevel)        
        if self.intensityLevel != newIntensityLevel or self.intensityWindow != newIntensityWindow:
            self.intensityLevel = newIntensityLevel
            self.intensityWindow = max(newIntensityWindow, 0)        
            self.intensityLevelCache[self._imageType] = newIntensityLevel
            self.intensityWindowCache[self._imageType] = newIntensityWindow        
            vmin=self.intensityLevel-(self.intensityWindow*0.5)
            vmax=self.intensityLevel+(self.intensityWindow*0.5)
            self.img.set_clim(vmin, vmax)            
    def setWindowLevelToDefault(self):
        
        maxMag = np.max(np.abs(self.complexImageData))

        self.intensityLevelCache[dd.ImageType.imag] = 0.0
        self.intensityWindowCache[dd.ImageType.imag] = 2.0 * maxMag        
    
        self.intensityLevelCache[dd.ImageType.real] = 0.0
        self.intensityWindowCache[dd.ImageType.real] = 2.0 * maxMag        
    
        self.intensityLevelCache[dd.ImageType.phase] = 0.0
        self.intensityWindowCache[dd.ImageType.phase] = 2.0 * np.pi

        self.intensityLevelCache[dd.ImageType.mag] = maxMag * 0.5
        self.intensityWindowCache[dd.ImageType.mag] = maxMag        
                
        self.setWindowLevel(self.intensityWindowCache[self._imageType], self.intensityLevelCache[self._imageType])    

                
    #==================================================================            
    #functions that update objects visualizing internal data
    #==================================================================
    def setMplImgColorMap(self, cmap):   
        self.img.set_cmap(cmap)  
    def setMplImg(self):       
        if self._imageType == dd.ImageType.mag:
            intensityImage = np.abs(self.complexImageData)
        elif self._imageType == dd.ImageType.phase:
            intensityImage = np.angle(self.complexImageData)
        elif self._imageType == dd.ImageType.real:
            intensityImage = np.real(self.complexImageData)
        elif self._imageType == dd.ImageType.imag:
            intensityImage = np.imag(self.complexImageData)
        
        self.dynamicRange = np.max(intensityImage) - np.min(intensityImage)        
        self.img.set_data(intensityImage.T)  
        #reason for transpose: 
        #matplotlib shows 10x20 matrix with height of 10 and width of 20  
        #but in our matrix the 10 refers to width and the 20 to height 
    def setMplLines(self):
        self.hline.set_ydata([self.location[1],self.location[1]])
        self.vline.set_xdata([self.location[0],self.location[0]])
        self.htxt.set_y(self.location[1])
        self.vtxt.set_x(self.location[0]) 
    def BlitImageAndLines(self):
        if self.fig._cachedRenderer is not None:  
           # print "blit!!"
            self.fig.draw_artist(self.fig.patch)
            self.axes.draw_artist(self.title)
            self.axes.draw_artist(self.axes.patch)
            self.axes.draw_artist(self.img)
            self.axes.draw_artist(self.hline)
            self.axes.draw_artist(self.vline) 
            self.axes.draw_artist(self.htxt)
            self.axes.draw_artist(self.vtxt)
          
            #self.blit(self.axes.bbox)        
            self.blit(self.fig.bbox)
            
    #==================================================================        
    #convenience functions to change data and update visualizing objects
    #==================================================================
    def showComplexImageChange(self, newComplexImage):
        self.setComplexImage(newComplexImage)
        self.setMplImg()
        self.BlitImageAndLines()
    def showLocationChange(self, newLocation):           
        self.setLocation(newLocation)
        self.setMplLines()
        self.BlitImageAndLines()
    def showImageTypeChange(self, imageType):        
        self.setImageType(imageType)        
        self.setMplImg()
        self.BlitImageAndLines()      
    def showColorMapChange(self, cmap):   
        self.setMplImgColorMap(cmap)
        self.BlitImageAndLines()     
    def showWindowLevelChange(self, newIntensityWindow,newIntensityLevel):
        self.setWindowLevel(newIntensityWindow,newIntensityLevel) 
        self.BlitImageAndLines() 
    def showSetWindowLevelToDefault(self):
        self.setWindowLevelToDefault()
        self.BlitImageAndLines()  
        
    #==================================================================        
    #functions related to Qt
    #==================================================================
    def sizeHint(self):
        return QtCore.QSize(450,450)               
