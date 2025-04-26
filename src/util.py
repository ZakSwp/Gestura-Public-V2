import time
import os,glob
import shutil
import tempfile
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import QDesktopWidget,QWidget,QScrollArea,QMessageBox,QGroupBox,QGridLayout,QPushButton
from PyQt5.QtCore import Qt, QRectF, QPointF,QTimer,QThread,pyqtSignal
from moviepy.editor import VideoFileClip
import sys,re
import numpy as np

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def distance(point1,point2):
   return np.linalg.norm(np.array(point1) - np.array(point2))

def getScreenRect():
    rect = QDesktopWidget().screenGeometry()
    return rect

def getScreenAspectRatio():
    screenRect=getScreenRect()
    return screenRect.width()/screenRect.height()

def createAudioTempFilePath()->str:
    """Creates a path to save the temp audio file of a video given by its videoPath"""
    temp_dir = tempfile.mkdtemp()  # Creates a temporary directory
    temp_file_path = os.path.join(temp_dir, "temp.mp3")  # Creates a temp file path
    return temp_file_path,temp_dir



def cleanup_temp_dir(dir_path: str):
    """Removes the temporary directory and all its contents"""
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)


def frameToQImage(frame):
    """ convert a moviePy videoClip frame to a QImage"""
    height, width, channel = frame.shape
    bytes_per_line = 3 * width
    image=QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return  image

def formatDuration(s):
    hours = s // 3600
    minutes = (s // 60) % 60
    seconds = s % 60
    
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

def countObjectType(type:type,iterable):
    s=0
    for element in iterable:
        if isinstance(element,type):
            s+=1
    return s

def subListOfType(type:type,list:list):
    tempList=[]
    for element in list:
        if isinstance(element,type):
            tempList.append(element)
    return tempList 
def saveAudioFromVideo(video_path, output_audio_path, log_file='output.log'):
    with open(log_file, 'w') as f:
        sys.stdout = f
        sys.stderr = f
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_audio_path)
        video.audio.close()
        video.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
def loadAnimationImages(directory):
    # List to store QPixmap objects
    pixmap_list = []

    # Regular expression to extract numbers from filenames
    def extract_number(file_name):
        match = re.search(r'\d+', file_name)
        return int(match.group()) if match else float('inf')

    # Get list of image files, sorted by their numeric part
    files = sorted(os.listdir(directory), key=extract_number)

    for file_name in files:
        # Construct the full file path
        file_path = os.path.join(directory, file_name)

        # Load the image and add it to the list
        pixmap = QPixmap(file_path)
        pixmap_list.append(pixmap)

    return pixmap_list
class Timer():
    def __init__(self,minValue,maxValue):
        self.minValue=minValue
        self.maxValue=maxValue
        self.currentValue=minValue
        self.isPaused=False
        self.timeOut=False
        self.settingTime=False
        self.started=False
        self.pauseDuration=0
        self.offset=0
        self.givenTime=0
        self.looping=False
    def setLoop(self,a:bool):
        self.looping=a
    def start(self):
        self.started=True
        self.origineValue=time.time()
    def getTime(self):
        if not self.isPaused:
            self.timeOut=False
            if self.looping and self.currentValue>=self.maxValue:
                
                self.setTime(self.minValue)
            if self.currentValue>=self.maxValue:
                self.timeOut=True
            if self.settingTime:
                self.settingTime=False
                self.origineValue=time.time()
                self.pauseDuration=0
                self.offset=self.givenTime-self.minValue
            self.currentValue=time.time()-self.pauseDuration-self.origineValue+self.minValue+self.offset
        return self.currentValue
    def pause(self):
        if not self.isPaused:
            self.pauseStartTime=time.time()
            self.isPaused=True
    def unpause(self):
        if self.isPaused:
            self.isPaused=False
            self.pauseDuration+=time.time()-self.pauseStartTime
        
    def setTime(self,time:float):
        if self.minValue<= time <= self.maxValue:
            self.givenTime=time
            self.settingTime=True
    def reset(self):
        self.setTime(self.minValue)
    def addDuration(self,duration:float):
        actualTime=self.getTime()
        newTime=actualTime+duration
        if self.minValue<=newTime <=self.maxValue:
            
            self.setTime(actualTime+duration)
        elif self.minValue>newTime:
            self.setTime(self.minValue)
        elif self.maxValue<newTime:
            self.setTime(self.maxValue)


class AudioWriter(QThread):
    finishSignal=pyqtSignal(str)
    def __init__(self,OnFinishSlot,videoInPutPath:str,outPutAudioPath:str):
        super().__init__()
    
        self.videoPath=videoInPutPath
        self.audioPath=outPutAudioPath
        
        self.finishSignal.connect(OnFinishSlot)

        
    def run(self):
        try:
            

            saveAudioFromVideo(self.videoPath, self.audioPath, resource_path("interfaceAssets/output.log"))
            
            self.finishSignal.emit("Audio export finished!")
        except Exception as e:
            self.finishSignal.emit(f"Error: {e}")
            ErrorHandler.show_error_message(str(e))

class ErrorHandler:
    """Class to handle and display errors"""

    @staticmethod
    def show_error_message(error_message: str):
        """Displays an error message in a QMessageBox"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("An error occurred")
        msg.setInformativeText(error_message)
        msg.setWindowTitle("Error")
        msg.exec_()

class VerticalContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.buffer = []
        
        self.spacing = 10
        self.leftMargin = 10
        self.topMargin = 10
        self.currentY = self.topMargin
        
        

    def add(self, widget:QWidget):
        widget.setParent(self)
        widget.move(self.leftMargin, self.currentY)
        widget.origineY=self.currentY
        widget.setHidden(False)
        self.buffer.append(widget)
        # Update the current Y coordinate
        self.currentY += widget.height() + self.spacing
        self.setMinimumHeight(self.currentY)

    def insertSpace(self, index:int,space:int):
        spacer=QWidget(self)
        spacer.setHidden(True)
        spacer.move(self.leftMargin,0)
        self.insertWidget(index,spacer)
    def insertWidget(self, index, widget:QWidget):
        length = len(self.buffer)
        if index >=0  and index <= length-1:
            widget.setParent(self)
            y_pos = self.buffer[index].y() 
            
            
            # Shift all the widgets located after the index
            for i in range(index, length):
                item = self.buffer[i]
                newYpos = item.y() + self.spacing + widget.height()
                item.origineY=newYpos
                item.move(self.leftMargin, newYpos)
            widget.move(self.leftMargin, y_pos)
            widget.origineY=y_pos
            widget.setHidden(False)
            self.buffer.insert(index, widget)
            # Update the current Y coordinate
            self.currentY += widget.height() + self.spacing
            self.setMinimumHeight(self.currentY)
            
        elif index== length or length==0:
            self.add(widget)   
        else:
            print("insertWidget: index out of range!!")
    def removeAt(self,index):
        length = len(self.buffer)
        if 0 <= index <= length-1:
            widget=self.buffer[index]
            widget.setHidden(True)
            offset=self.spacing+widget.height()
            self.currentY-=offset
            if index==length-1:
                self.buffer.pop()
                return
            for i in range(index+1,length):
                item=self.buffer[i]
                item.origineY=item.y()-offset
                item.move(self.leftMargin,item.y()-offset)
                
            self.buffer.pop(index)
        else:
            print("removeAt: index out of range!!")
    def setWidgetAt(self,index,widget:QWidget):
        length = len(self.buffer)
        if 0 <= index <= length-1:
            lastWidget=self.buffer.pop(index)
            lastWidget.setHidden(True)
            widget.setParent(self)
            widget.move(self.leftMargin,lastWidget.y())
            widget.origineY=lastWidget.y()
            widget.setHidden(False)
            self.buffer.insert(index,widget)
            offset=widget.height()-lastWidget.height()
            self.currentY+=offset
            for i in range(index+1,length):
                item=self.buffer[i]
                item.origineY=item.y()+offset
                item.move(self.leftMargin,item.y()+offset)
            self.setMinimumHeight(self.currentY)
        else:
            print("setWidgetAt: index out of range!!")
    def setSpaceAt(self,index:int,space:int):
        spacer=QWidget(self)
        
        spacer.setGeometry(self.leftMargin,0,self.width(),space)
        self.setWidgetAt(index,spacer)
        spacer.setHidden(True)

class ActionBox(QGroupBox):
    def __init__(self,name,parent=None):
        super().__init__(parent=parent)
        self.grid=QGridLayout()
        self.setLayout(self.grid)
        self.setTitle(name)
    def addAction(self,name,slot,row,column):
        button=QPushButton(name)
        button.clicked.connect(slot)
        self.grid.addWidget(button,row,column)
        self.adjustSize()










