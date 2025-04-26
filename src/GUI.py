
import os,glob
import pygame
import copy
import sys
from moviepy.editor import VideoFileClip
from PyQt5.QtCore import Qt, QRectF, QPointF,QTimer,QThread,pyqtSignal,QRect,QPoint,QSize,QEvent,QPropertyAnimation
from PyQt5.QtGui import QFont, QKeyEvent, QPaintEvent, QPen, QColor, QBrush,QTransform,QMouseEvent,QPainterPath,QPixmap, QWheelEvent,QCursor,QImage,QIcon,QKeySequence,QContextMenuEvent,QPainter, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem,QGraphicsItem, QMenu, QAction, QActionGroup,QPushButton,QGraphicsEllipseItem,QWidget,QLabel,QFontDialog,QFileDialog,QMessageBox,QScrollArea,QLayout, QSpacerItem, QSizePolicy,QGraphicsDropShadowEffect,QGraphicsOpacityEffect,QComboBox
from util import *
from graphicItems import *
from GuiStyles import *
from renderer.rendererWithGestureInput import *


app = QApplication(sys.argv)
icon=QIcon("interfaceAssets/interfaceIcons/gesturaIcon.ico")
app.setWindowIcon(icon)
app.setFont(QFont("Arial",10))

class GradientWidget(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent=parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # Create a gradient that goes from top to bottom
        grad1 = QLinearGradient(0, 0, rect.width(), 0)
        grad2 = QLinearGradient(0, 0, 0, rect.height())
        grad1.setColorAt(0, QColor(243, 200, 205, 255))
        grad1.setColorAt(1, QColor(181, 210, 228, 255))

        # Create a gradient that goes from left to right

        grad2 = QLinearGradient(0, 0, 0, rect.height())
        grad2.setColorAt(0, QColor(243,243,243,255))
        grad2.setColorAt(1, QColor(255,255,255,0))

        # Draw the gradients
        painter.fillRect(rect, grad1)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.fillRect(rect, grad2)
class WorkSpace(QGraphicsView):
    def __init__(self,slideScrollZone,mainWindow,parent=None):
        super().__init__(parent)
        self.mainWindow=mainWindow
        self.mouseIsmoving=False
        self.mouseWheelScrolling=False
        self.mouseButtonDown=False
        
        self.setGeometry(320,100, 1600, 850)
        
        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0,0,self.width(),self.height())
        self.setScene(self._scene)
        self.workView=WorkView(self)
        self.workViewBorder=WorkView(self)
        self.workViewBorder.backgroundColor=QColor(0,0,0,0)
        self.workView.setZValue(-100000)
        self.workViewBorder.setZValue(100000)
        self.slideScrollZone=slideScrollZone
        self.workView.setWidth(1000)
        self.workViewBorder.setWidth(1000)
        self.workViewBorder.setheight(1000/getScreenAspectRatio())
        self.workView.setheight(1000/getScreenAspectRatio())
        self.workView.moveCenter(self.rect().center())
        self.workViewBorder.moveCenter(self.rect().center())
        self.scene().addItem(self.workView)
        self.scene().addItem(self.workViewBorder)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        # Enable drag-and-drop
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.versionBufferMaxLength=20
        self.versionIndex=0
        self.versionBuffer=[{}]
        self.buffer=[]
        self.tempAudioDirBuffer=[]
        self.activeVideo=None
        self.insertedItem="empty"
        self.backgroundColor=QColor(150, 150, 150,255)
        self.colorBackground()
        self.background_image = QPixmap('disque.png')  
        self.videoLoadingImage=None
        self.currentVideoPosition=None
        self.currentImagePath=None
        self.zoomRatio=1
        self.waitingDuration=0.1
        self.currentVideoPath=None
    def setBackgroundColor(self,color:QColor):
        self.backgroundColor=QColor(color)
    def colorBackground(self):
        color=self.backgroundColor
        self.setStyleSheet(f"background-color:rgb({color.red()}, {color.green()}, {color.blue()})")
    def getMinZValue(self):
        
        if len(self.buffer)==0:
            return None  # return None if the scene is empty
        return min(item.zValue() for item in self.buffer)

    def getMaxZValue(self):
        if len(self.buffer)==0:
            return None  # return None if the scene is empty
        return max(item.zValue() for item in self.buffer)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background-color:rgb(100, 200, 255);")
            self.setWindowOpacity(0.5)
    def dragMoveEvent(self, event):
        
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        pos=self.mapToScene(event.pos())
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image=Image(self,file_path)
                    image.setPos(pos)
                    self.addComponent(image)
                    event.acceptProposedAction()
                    self.updateVersionBuffer()
                    
                elif file_path.lower().endswith(("mp4","mkv","flv")):
                    
                    
                    tempAudioPath,tempAudioDir=createAudioTempFilePath()
                    self.tempAudioDirBuffer.append(tempAudioDir)
                    self.audioWriter = AudioWriter(self.addVideo,file_path,tempAudioPath)
                    self.currentVideoPosition=pos
                    
                    self.audioWriter.start()
                    self.setVideoLoadingImage(file_path)
                    if self.videoLoadingImage.getAspectRatio() >=1:
                        self.videoLoadingImage.resizeToWidth(500)
                    else:
                        self.videoLoadingImage.resizeToHeight(500)
                    event.acceptProposedAction()
                
                    
                    
                self.colorBackground()
    def dragLeaveEvent(self, event):
        self.colorBackground()

    def addComponent(self, component):
        maxZValue=self.getMaxZValue()
        if maxZValue is not None:
            component.setZValue(maxZValue+1)
      
        self._scene.addItem(component)
        self.buffer.append(component)
    def removeComponent(self,component):
        self._scene.removeItem(component)
        self.buffer.remove(component)
        self.update()
    def mousePressEvent(self,event:QMouseEvent):
        self.update()
        self.mouseButtonDown=True
        pos=self.mapToScene(event.pos())
        match self.insertedItem:
            case "text":
                text_item=Text("Write your text here",self)
                
                text_item.setPos(pos)
                self.addComponent(text_item)
                self.insertedItem="empty"
                self.updateVersionBuffer()
            case "image":
                image = Image(self,self.currentImagePath)
                if image.getAspectRatio()>=1:
                    image.resizeToWidth(500)
                else:
                    image.resizeToHeight(500)
                image.setPos(pos)
                self.addComponent(image)
                self.insertedItem="empty"
                self.updateVersionBuffer()
            case "video":
                tempAudioPath,tempAudioDir=createAudioTempFilePath()
                self.tempAudioDirBuffer.append(tempAudioDir)
                self.audioWriter = AudioWriter(self.addVideo,self.currentVideoPath,tempAudioPath)
                self.currentVideoPosition=pos
                self.audioWriter.start()
                
                self.setVideoLoadingImage(self.currentVideoPath)
                if self.videoLoadingImage.getAspectRatio() >=1:
                    self.videoLoadingImage.resizeToWidth(500)
                else:
                    self.videoLoadingImage.resizeToHeight(500)
                self.insertedItem="empty"
            case "rect":
                rect=Rect(self)
                rect.setPos(pos)
                self.addComponent(rect)
                self.insertedItem="empty"
                self.updateVersionBuffer()
            
            case "roundedRect":
                rRect=RoundedRect(self)
                rRect.setPos(pos)
                self.addComponent(rRect)
                self.insertedItem="empty"
                self.updateVersionBuffer()
            case "circle":
                circle=Circle(self)
                circle.setPos(pos)
                self.addComponent(circle)
                self.insertedItem="empty"
                self.updateVersionBuffer()
        super().mousePressEvent(event)
    def wait(self):
        time.sleep(self.waitingDuration)
    def setWaitingDuration(self,secondes:float):
        self.waitingDuration=secondes
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.mouseIsmoving=True
        
        if self.mouseButtonDown:
           self.update()
        
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event) 
        self.mouseIsmoving=False
        self.mouseButtonDown=False
        self.update()
    def deleteComponent(self,component): 
        if isinstance(component,Video):
            if component==self.activeVideo:
                if not self.activeVideo.play:
                    self.activeVideo.pause()
                self.activeVideo.videoClip.reader.proc.terminate()
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                self.activeVideo=None
 
        self.removeComponent(component)
          
    def keyPressEvent(self, event: QKeyEvent ):
        # Handle deletion
        if event.key() == Qt.Key_Delete:
            deletion=False
            for item in self.buffer:
                if item in self.scene().selectedItems() and item.isRemovable():
                 
                    self.deleteComponent(item)
                    deletion=True
            if deletion:
                
                self.updateVersionBuffer()
               
        # Handle undo 
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            if len(self.slideScrollZone.selectedSlide().versionBuffer ) != 0:
                if self.slideScrollZone.selectedSlide().versionIndex  >0:
                    self.slideScrollZone.selectedSlide().versionIndex -=1
                    
                    self.loadVersion()
                    self.slideScrollZone.selectedSlide().loadFromWorkspace()
        # Handle redo
        if event.key() == Qt.Key_Y and event.modifiers() == Qt.ControlModifier:
            if len(self.slideScrollZone.selectedSlide().versionBuffer ) != 0:
                if self.slideScrollZone.selectedSlide().versionIndex +1 <len(self.slideScrollZone.selectedSlide().versionBuffer ):
                    self.slideScrollZone.selectedSlide().versionIndex +=1
                    
                    self.loadVersion()
                    self.slideScrollZone.selectedSlide().loadFromWorkspace()
        super().keyPressEvent(event)

    def updateVersionBuffer(self):
        
        if len(self.slideScrollZone.selectedSlide().versionBuffer )!=0:
            self.slideScrollZone.selectedSlide().versionBuffer =[copy.copy(self.slideScrollZone.selectedSlide().versionBuffer [i]) for i in range(0,self.slideScrollZone.selectedSlide().versionIndex +1) ]
        if self.slideScrollZone.selectedSlide().versionIndex +1>=self.versionBufferMaxLength:
            self.slideScrollZone.selectedSlide().versionBuffer .pop(0)
            self.slideScrollZone.selectedSlide().versionIndex -=1
        tempList=[]
        for item in self.buffer:
            copyItem=copy.copy(item)
            tempList.append(copyItem)
            copyItem.rotate(item.rotation())

        self.slideScrollZone.selectedSlide().versionBuffer .append({"items":copy.copy(tempList),"workviewPos":self.workView.rect().topLeft(),"workviewWidth":self.workView.width()})
        self.slideScrollZone.selectedSlide().versionIndex +=1
        if self.activeVideo:
            if not self.activeVideo.play:
                self.activeVideo.pause()
        
        self.slideScrollZone.selectedSlide().loadImage()
        self.update()
    def loadVersion(self):

        tempList=[]
        for item in self.scene().items():
            if isinstance(item,(Text,Image,Video,Shape,Thumbnail)):
                self.scene().removeItem(item)
        if len(self.slideScrollZone.selectedSlide().versionBuffer [self.slideScrollZone.selectedSlide().versionIndex ])!=0:
            for item in self.slideScrollZone.selectedSlide().versionBuffer [self.slideScrollZone.selectedSlide().versionIndex ]["items"]:
                copyItem=copy.copy(item)
                ratio=self.workView.width()/self.slideScrollZone.selectedSlide().versionBuffer [self.slideScrollZone.selectedSlide().versionIndex ]["workviewWidth"]
                workviewPos=self.slideScrollZone.selectedSlide().versionBuffer [self.slideScrollZone.selectedSlide().versionIndex ]["workviewPos"]
                copyItem.setPos(ratio*(item.pos()-workviewPos)+self.workView.rect().topLeft())
                copyItem.resizeToRatio(ratio)
                copyItem.rotate(item.rotation())
                tempList.append(copyItem)
        self.buffer=copy.copy(tempList)
        for item in self.buffer:        
            self.scene().addItem(item)  
        if self.activeVideo:
            self.activeVideo.pause()
    def addVideo(self):
        video=Video(self,self.audioWriter.videoPath,self.audioWriter.audioPath)
        video.loadVideoClip()
        video.setVideoTimer()
        video.setPos(self.currentVideoPosition)
        if video.getAspectRatio() >=1:
            video.resizeToWidth(500)
        else:
            video.resizeToHeight(500)
        if self.videoLoadingImage is not None:
            if self.videoLoadingImage in self.scene().items():
                self.removeComponent(self.videoLoadingImage)
                video.setZValue(self.videoLoadingImage.zValue())
                self.addComponent(video)
                if self.activeVideo is not None:
                    if not self.activeVideo.play: 
                        self.activeVideo.pause()
                self.activeVideo=video
                pygame.mixer.music.load(video._audioTempFile)
               
                self.videoLoadingImage=None
                self.currentVideoPosition=None
                self.updateVersionBuffer()
                
        else:
            raise Exception("videoLoadingImage is None")
    def setVideoLoadingImage(self,videoPath):
        if self.currentVideoPosition is not None:
            self.videoLoadingImage=Image(self)
            self.videoLoadingImage.setRemovable(False)# the VideoLoadingImage can not be removed by the user while the video is loading
            videoClip = VideoFileClip(videoPath)
            frame = videoClip.get_frame(0)
            self.videoLoadingImage.setImage(frameToQImage(frame))
            self.videoLoadingImage.setPos(self.currentVideoPosition)
            self.videoLoadingImage.setOpacity(0.6)
            self.videoLoadingImage.blocked=True
            
            self.addComponent(self.videoLoadingImage)
        else:
            raise Exception("currentVideoPosition is None")
    def loadTextureFile(self):
        # Open file dialog for selecting texture file
        texture_file, _ = QFileDialog.getOpenFileName(
            self, 'Open Texture File', '', 'Image Files (*.png)'
        )
        if texture_file:
            QMessageBox.information(self, 'Texture File Loaded', f'Texture file "{texture_file}" loaded.')
            return texture_file
        else:
            return None
    def loadObjFile(self):
        # Open file dialog for selecting OBJ file
        obj_file, _ = QFileDialog.getOpenFileName(
            self, 'Open OBJ File', '', 'OBJ Files (*.obj)'
        )
        if obj_file:
            QMessageBox.information(self, 'OBJ File Loaded', f'OBJ file "{obj_file}" loaded.')
            return obj_file
        else:
            QMessageBox.warning(self, 'No File Selected', 'No OBJ file selected.')
            return None
    
    def insert3DModel(self):
        objFile=self.loadObjFile()
        if not objFile:
            return
        else:
            textureFile=self.loadTextureFile()
            text=self.mainWindow.ui.modelNameLineEdit.text()
            
            validText=False        
            for i in text:
                if i!=" ":
                    validText=True
            if len(text)==0 or not validText:
                text= os.path.basename(objFile)
            thumbnail=Thumbnail(self, resource_path("interfaceAssets/interfaceIcons/modelThumbnail.jpg"), text)
            print(self.mainWindow.ui.modelNameLineEdit.text())
            thumbnail.setShapeToBackground()
            self.addComponent(thumbnail)
            self.slideScrollZone.selectedSlide().loadModel(objFile,textureFile)
            self.updateVersionBuffer()
    def insertRect(self):
        self.insertedItem="rect"
    def insertRoundedRect(self):
        self.insertedItem="roundedRect"
    def insertCircle(self):
        self.insertedItem="circle"
    def insertVideo(self):
        options = QFileDialog.Options()
        self.currentVideoPath, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.avi *.mp4 *.mkv)", options=options)
        print(self.currentVideoPath)
        if self.currentVideoPath:
            self.insertedItem="video"
        else:
            self.insertedItem="empty"
    def insertText(self):
        self.insertedItem="text"
        
    def insertImage(self):
        options = QFileDialog.Options()
        self.currentImagePath, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.ico *.svg)", options=options)
        if self.currentImagePath:
            self.insertedItem="image"
        else:
            self.insertedItem="empty"
        
    def wheelEvent(self, event):
        self.mouseWheelScrolling=True
        # Zoom factor
        
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor

       
        # Scale factor based on wheel direction
        if event.angleDelta().y() > 0:
            self.setZoomRatio(zoom_in_factor)
        else:
            self.setZoomRatio(zoom_out_factor)
        self.Zoom()
    def setZoomRatio(self,ratio:float):
        self.zoomRatio=ratio
    def getZoomRatio(self):
        return self.zoomRatio
    def Zoom(self):
        self.scale(self.getZoomRatio(), self.getZoomRatio())
  
    def centerText(self):
        for item in self.scene().selectedItems():
            if isinstance(item,Text):
                
                item.textPos="center"
                item.setAlignment()
                
    def shiftTextToLeft(self):
        for item in self.scene().selectedItems():
            if isinstance(item,Text):
                item.textPos="left"
                item.setAlignment()
                
    def shiftTextToRight(self):
        for item in self.scene().selectedItems():
            if isinstance(item,Text):
                item.textPos="right"
                item.setAlignment()
    def quit(self):
        for item in self.buffer:
            self.deleteComponent(item)
        if self.activeVideo is not None:
            self.activeVideo.pause()
            self.activeVideo.videoClip.reader.proc.terminate()
        
               
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            pygame.quit()
        
        for dir in self.tempAudioDirBuffer:
            cleanup_temp_dir(dir)
        print("deletion finished succefully")
                 
class Slide(QGraphicsView):
    def __init__(self,mainWindow,parent=None):
        super().__init__(parent=parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #set a comment to the slide
        self.commentText=""
        #set the removable property
        self.removable=True #initially every slide is removable but if it remained jute one ,the removable attribut will be set to False 
        self.index=0
        # creat a version buffer to hold all the history of the scene
        self.versionBuffer=[{}]
        # version index that indicates the current version that must be displayed
        self.versionIndex=0
        # connect the slide the workspace and the slideContainer
        self.mainWindow=mainWindow
        self.workSpace=mainWindow.workSpace
        self.slideScrollZone=mainWindow.slideScrollZone
        # configure the slide border thickness
        self.defaultBorderThickness=2
        self.clickedBorderThickness=5
        self.hoverBorderThickness=4
        self.borderPadding=5
        # configure the slide border color
        self.defaultBorderColor=QColor(100,100,100,255)
        self.clickedBorderColor=QColor(255,0,0,255)
        self.hoverBorderColor=QColor(200,200,200,255)

        self.aspecRatio=getScreenAspectRatio()
        self.width_=200
        self.setFixedSize(self.width_,int(self.width_/self.aspecRatio))
        scene=QGraphicsScene()
        self.setScene(scene)
        workView=self.workSpace.workView
        self.scene().setSceneRect(workView.rect())
        ratio=self.width_/workView.rect().width()
        self.scale(ratio,ratio)
        
        self.dragging = False
        self.drag=False
        self.last_y= QPoint(0,0)
        self.origineY=self.y()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Set the timer to 1 seconds (1000 ms)
        self.timer.setSingleShot(True)  # The timer will only fire once
        self.timer.timeout.connect(self.setDrag)
        # set animation when moving
         # Timer to change border color
        self.animationTimer = QTimer(self)
        self.animationTimer.timeout.connect(self.blinkBorder)
        self.colorFlag = True
        self.thumbnail=None
        self.actorBuffer=[]
        self.hasModel=False

    def loadModel(self,objFileName,textureFileName=None):
        actor=create3DModel(objFileName,textureFileName)
        self.actorBuffer.append(actor) 
        self.hasModel=True 
    def setCommentText(self,text:str):
        self.commentText=text
    def getCommentText(self):
        return self.commentText
    def blinkBorder(self):
        if self.colorFlag:
            self.clickedBorderColor=QColor(255,0,0,255)
            self.setClickedBorder()
        else:
            self.clickedBorderColor=QColor(0, 0, 0,255)
            self.setClickedBorder()
        self.colorFlag = not self.colorFlag    
    def setDrag(self):
        buttons = app.mouseButtons()
        if self.underMouse() and buttons & Qt.LeftButton:
            self.drag=True
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            self.animationTimer.start(500)  # Change every 500 milliseconds
            
        else:
            self.drag=False   
            self.setCursor(QCursor(Qt.PointingHandCursor)) 

    def setIndex(self,index:int):
        self.index=index
    def setWidth(self,width:float):
        self.width_=width
        self.setFixedSize(self.width_,int(self.width_/self.aspecRatio))
        self.scene().setSceneRect(0,0,self.width_,self.width_/self.aspecRatio)
    def loadImage(self):
        self.scene().clear()
        # Define the size and position of the scene to capture
        if len(self.versionBuffer[self.versionIndex])==0:
            return
        ratio=self.width_/self.versionBuffer[self.versionIndex]["workviewWidth"]
        for item in self.versionBuffer[self.versionIndex]["items"]:
            if isinstance(item,(Text,Video,Image,Shape,Thumbnail)) :
                
                copyItem=copy.copy(item)
                copyItem.setInteraction(False)
                
                
                copyItem.setPos(self.mapToScene(ratio*(copyItem.pos()-QPointF(self.versionBuffer[self.versionIndex]["workviewPos"].x(),self.versionBuffer[self.versionIndex]["workviewPos"].y())).toPoint()))
                
                
                copyItem.rotate(item.rotation())
                
                self.scene().addItem(copyItem)
                
             
        
        
    def connectToWorkspace(self):
        self.workSpace.versionBuffer=self.versionBuffer
        self.workSpace.versionIndex=self.versionIndex
    def loadFromWorkspace(self):
        self.loadImage()
        

    def setDefaultBorder(self):
        self.setWidth(200)
        self.move(self.slideScrollZone.xOffset,self.y())
        r=self.defaultBorderColor.red()
        g=self.defaultBorderColor.green()
        b=self.defaultBorderColor.blue()
        a=self.defaultBorderColor.alpha()
        self.setStyleSheet(f"background-color:rgb(255, 255, 255); border: {self.defaultBorderThickness}px solid rgba({r},{g},{b},{a});border-radius: 15px;padding: {self.borderPadding}px;")

    def setClickedBorder(self):
        self.setWidth(200)
        self.move(self.slideScrollZone.xOffset+30,self.y())
        r=self.clickedBorderColor.red()
        g=self.clickedBorderColor.green()
        b=self.clickedBorderColor.blue()
        a=self.clickedBorderColor.alpha()
        self.setStyleSheet(f"background-color:rgb(255, 255, 255); border: {self.clickedBorderThickness}px solid rgba({r},{g},{b},{a});border-radius: 15px; padding: {self.borderPadding}px;")

    def setHoverBorder(self):
        self.setWidth(200)
        self.move(self.slideScrollZone.xOffset+20,self.y())
        r=self.hoverBorderColor.red()
        g=self.hoverBorderColor.green()
        b=self.hoverBorderColor.blue()
        a=self.hoverBorderColor.alpha()
        self.setStyleSheet(f"background-color:rgba(255, 255, 255,255); border: {self.hoverBorderThickness}px solid rgba({r},{g},{b},{a});border-radius: 15px; padding: {self.borderPadding}px;")
    def setSelected(self):
        
        if self.slideScrollZone.activeSlide:
            self.slideScrollZone.activeSlide.setDefaultBorder()
            self.slideScrollZone.activeSlide.setCommentText(self.mainWindow.ui.textEdit.toHtml())
        self.slideScrollZone.activeSlide=self
        self.setClickedBorder()
        self.connectToWorkspace()
        self.workSpace.loadVersion()
        self.mainWindow.ui.textEdit.setText(self.getCommentText())
        
    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        self.setSelected()
        if event.button() == Qt.LeftButton:
            self.timer.start()
            self.last_y = event.pos()  # Save the initial Y position
            
            self.raise_()
            #self.setMouseTracking(True)
          
            event.accept()
    
    def enterEvent(self, event):
        
        if self!=self.slideScrollZone.selectedSlide():
            self.setHoverBorder()
        super().enterEvent(event)

    def leaveEvent(self, event):
        
        if self!=self.slideScrollZone.selectedSlide():
            self.setDefaultBorder()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.drag :
            new_y = self.mapToParent(event.pos() - self.last_y).y()
          
            if new_y< self.y():
                index=self.parent().buffer.index(self)
                if index==0 and new_y<self.origineY:
                    return
                elif index==0:
                    self.move(self.x(), new_y)  # Move label vertically
                    return 
                prevWidget=self.parent().buffer[index-1]
                if self.y() < prevWidget.y()+prevWidget.height()/2:
                    self.move(self.x(),prevWidget.origineY)
                    prevWidget.move(prevWidget.x(),self.origineY)
                    self.parent().buffer[index],self.parent().buffer[index-1]=self.parent().buffer[index-1],self.parent().buffer[index]
                    self.origineY=self.y()
                    prevWidget.origineY=prevWidget.y()
               
                    self.last_y = event.pos() 
                
                   
                    self.raise_()
            elif new_y> self.y():
                
                index=self.parent().buffer.index(self)
                if index==len(self.parent().buffer)-1 and self.y()> self.origineY:
                    return 
                elif index==len(self.parent().buffer)-1:
                    self.move(self.x(), new_y)  # Move label vertically
                    return
                nextWidget=self.parent().buffer[index+1]
                if self.y()+self.height()/2 > nextWidget.y():
                    
                    self.move(self.x(),nextWidget.origineY)
                    nextWidget.move(nextWidget.x(),self.origineY)
                    self.parent().buffer[index],self.parent().buffer[index+1]=self.parent().buffer[index+1],self.parent().buffer[index]
                    self.origineY=self.y()
                    nextWidget.origineY=nextWidget.y()
                    self.last_y = event.pos() 
                    self.raise_()
            
            self.move(self.x(), new_y)  # Move label vertically
            
            self.dragging = True  # Update last Y position

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
                
            if self.dragging :
                self.move(self.x(),self.origineY)
                
            self.animationTimer.stop()
            self.clickedBorderColor=QColor(255,0,0,255)
            self.setClickedBorder()    
            self.setCursor(QCursor(Qt.PointingHandCursor))
            self.dragging = False
            self.drag=False
    
 
    def delete(self):
        length=len(self.slideScrollZone.buffer())
        
        if not self.removable:
            return 
         
        index=self.slideScrollZone.buffer().index(self)
        if self==self.slideScrollZone.activeSlide:
            
            if index==length-1:
                self.slideScrollZone.buffer()[index-1].setSelected()
            else:
                self.slideScrollZone.buffer()[index+1].setSelected()
            
            self.slideScrollZone.removeSlide(index)
  
        
    def contextMenuEvent(self, event:QContextMenuEvent):
        menu=QMenu()
        deleteAction=QAction("delete",menu)
        length=len(self.slideScrollZone.buffer())
        if length==1:
            self.removable=False # one slide remains ,we must keep it 
        else:
            self.removable=True
        deleteAction.setEnabled(self.removable)
        deleteAction.triggered.connect(self.delete)
        menu.addAction(deleteAction)
        menu.exec_(event.globalPos())


    
class SlideScrollZone(QScrollArea):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.slideSpacing=20
        self.xOffset=20
        self.topMargin=20
        self.setAttribute(Qt.WA_Hover, True)
        self.setWidgetResizable(True)
        #self.setGeometry(0,100,300,900)
        # Create a vertical layout for the image container
        self.verticalContainer=VerticalContainer()
        self.verticalContainer.leftMargin=self.xOffset
        self.verticalContainer.topMargin=self.topMargin
        self.verticalContainer = VerticalContainer()
        self.verticalContainer.setGeometry(QRect(0, 0, 192, 382))
        self.verticalContainer.setStyleSheet("QWidget{\n"
"\n"
"background-color:transparent;\n"
"\n"
"\n"
"}")
        self.verticalContainer.setObjectName("verticalContainer")
        self.setWidget(self.verticalContainer)
        

       
    
        # the activeSlide contains the current selected slide 
        self.activeSlide=None
        # creat a spacer to be used in case of slide movement
        
        
        
    
    def buffer(self):
        return self.verticalContainer.buffer    
    def addSlide(self,slide:Slide,index=None):
        
        
        
        if index==len(self.buffer()) or index==None:
           
            self.verticalContainer.add(slide)
        else:
            
            self.verticalContainer.insertWidget(index,slide)
    def selectedSlide(self)->Slide:
        return self.activeSlide
    def removeSlide(self,index):

        self.verticalContainer.removeAt(index)

class PresenterView(QGraphicsView):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        self.setGeometry(self.parent().rect())
        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0,0,self.width(),self.height())
        self.setScene(self._scene)
    def wheelEvent(self, event: QWheelEvent | None) -> None:
        event.ignore()
    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        event.ignore()
    def keyReleaseEvent(self, event: QKeyEvent | None) -> None:
        event.ignore()
class Presenter(QMainWindow):
    def __init__(self,mainWindow:QMainWindow):
        super().__init__()
        self.setWindowTitle("Gestura Presenter")
        self.setGeometry(0, 0, 800, 600)
        self.setCentralWidget(QWidget())
        layout=QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.centralWidget().setLayout(layout)
        self.mainWindow=mainWindow
        color=QColor(255,255,255,255)
        self.setStyleSheet(f"background-color:rgb({color.red()}, {color.green()}, {color.blue()})")
        self.view=PresenterView(self)
        
        self.currentWidget=self.view
        layout.addWidget(self.currentWidget)
        workView=self.mainWindow.workSpace.workView
        self.view.scene().setSceneRect(workView.rect())
        ratio=getScreenRect().width()/workView.rect().width()
        self.view.scale(ratio,ratio) 
        #self.timer=QTimer()
        #self.timer.start(100)
        #self.timer.timeout.connect(self.update)
        self.setWindowIcon(QIcon(resource_path('interfaceAssets/interfaceIcons/gesturaIcon.ico')))
        # set the currentPageIndex to the first page
        self.currentPageIndex=0
        self.slideNumber=len(self.mainWindow.slideScrollZone.buffer())
        self.modelView=None
        for slide in self.mainWindow.slideScrollZone.buffer():
            if slide.hasModel:
                self.modelView=ModelView(screenshotMode=True)
        """if self.modelView:
            for slide in self.mainWindow.slideScrollZone.buffer():
                if len(slide.actorBuffer)!=0:
                    for index,actor in enumerate(slide.actorBuffer):
                        self.modelView.addActorToRendrer(actor)
                        self.modelView.actorList.append((actor,index+1))"""


    def setCurrentPageIndex(self,index:int):
        self.currentPageIndex=index
    def incrementPageIndex(self):
        if self.currentPageIndex>=self.slideNumber-1:
            return
        else:
            self.currentPageIndex+=1
    def decrementPageIndex(self):
        if self.currentPageIndex<=0:
            return
        else:
            self.currentPageIndex-=1
    def present(self):
        slide=self.mainWindow.slideScrollZone.buffer()[self.currentPageIndex]
        self.currentWidget=self.centralWidget().layout().itemAt(0).widget()

        if slide.hasModel:
            if len(self.modelView.actorList)!=0:
                self.modelView.clearRendrer()
                
            for index,actor in enumerate(slide.actorBuffer):
                        self.modelView.addActorToRendrer(actor)
                       
                        self.modelView.actorList.append((actor,index+1))
                        
                        
       
            self.view.hide()
            self.modelView.setHidden(False)
            self.centralWidget().layout().removeWidget(self.currentWidget)
            self.centralWidget().layout().addWidget(self.modelView)
            self.modelView.startCv()
        else:
            if isinstance(self.currentWidget,ModelView):
                self.currentWidget.stopCv()
                self.currentWidget.hide()

                self.view.setHidden(False)
                self.centralWidget().layout().removeWidget(self.currentWidget)
                self.centralWidget().layout().addWidget(self.view)

            version=slide.versionBuffer[slide.versionIndex]
            self.setItems(version)
        
    def closeEvent(self,event):
        self.mainWindow.showMaximized()
        if self.mainWindow.workSpace.activeVideo is not None:
            self.mainWindow.workSpace.activeVideo.pause()
            pygame.mixer.music.stop()
        if self.modelView:
            self.modelView.stopCv()
            self.modelView.vtk_widget.GetRenderWindow().RemoveRenderer(self.modelView.ren)  # Remove the renderer
            self.modelView.vtk_widget.GetRenderWindow().Finalize()  # Finalize the render window to release resources
            self.modelView.vtk_widget.TerminateApp()  # Terminate VTK interactor
            self.modelView.vtk_widget.deleteLater()  # Ensure the widget is properly deleted in PyQt
        
        event.accept() 
         
    def keyPressEvent(self, event):
       
        if event.key() == Qt.Key_Escape:
            self.mainWindow.showMaximized()
            if isinstance(self.currentWidget,ModelView):
                self.currentWidget.stopCv()
            self.showNormal()
        elif event.key() in {Qt.Key_Space ,Qt.Key_Enter}:
            if self.mainWindow.workSpace.activeVideo is not None:
                self.mainWindow.workSpace.activeVideo.pause()
            self.incrementPageIndex()
            self.present()
        elif event.key()==Qt.Key_Backspace:
            if self.mainWindow.workSpace.activeVideo is not None:
                self.mainWindow.workSpace.activeVideo.pause()
            self.decrementPageIndex()
            self.present()
        else:
            super().keyPressEvent(event)
            
    def setItems(self,version):
        self.view.scene().clear()
        if len(version)==0:
            itemBuffer=[]

        else:
            itemBuffer=version["items"]
            workViewPos=version["workviewPos"] 
            workViewWidth=version["workviewWidth"] 
            ratio=getScreenRect().width()/workViewWidth
        for item in itemBuffer:
            if isinstance(item,(Text,Shape)) :
                copyItem=copy.copy(item)
                copyItem.setInteraction(False)
                copyItem.setPos(self.view.mapToScene(ratio*(copyItem.pos()-workViewPos).toPoint()))
                copyItem.rotate(item.rotation())
                self.view.scene().addItem(copyItem)
              
    
        
      
        
