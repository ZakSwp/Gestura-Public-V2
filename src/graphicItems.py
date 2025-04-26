
import cv2


import pygame
import vtk
import mediapipe as mp
import numpy as np
import copy
from moviepy.editor import VideoFileClip
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from abc import ABC,abstractmethod
from PyQt5.QtCore import Qt, QRectF, QPointF,QTimer,QThread,pyqtSignal,QRect,QPoint,QSize
from PyQt5.QtGui import QFont, QKeyEvent, QPaintEvent, QPainter, QPen, QColor, QBrush,QTransform,QMouseEvent,QPainterPath,QPixmap, QWheelEvent,QCursor,QImage,QIcon,QFontMetricsF
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem,QGraphicsItem, QMenu, QAction, QActionGroup,QFrame,QPushButton,QGraphicsEllipseItem,QWidget,QLabel,QFontDialog,QFileDialog,QMessageBox,QDesktopWidget,QVBoxLayout
from math import pi,sin,cos,sqrt
from util import *

    





class Lable(QGraphicsTextItem):
    def __init__(self, text,width,view:QGraphicsView, parent=None):
        super().__init__(text, parent)
        self.view=view
        self.fonte = QFont('Comic Sans MS', 10)
        self.setFont(self.fonte)
        self.setDefaultTextColor(QColor(255, 255, 255 , 255))
        self.setOpacity(1)
        self.backBrush = QBrush(QColor(72, 73, 72 , 240))
       
        self.radius=5
        self.setTextWidth(width)
        self.setHtml(f"""
                <div style="text-align: center;">
                    <p>{self.toPlainText()}</p>
                </div>
                """)
    def paint(self, painter, option, widget):
        painter.save()
        painter.setBrush(self.backBrush)
        painter.setPen(Qt.NoPen)
        rect = self.boundingRect()
        painter.drawRoundedRect(rect,self.radius,self.radius)
        painter.restore()
        super().paint(painter, option, widget)
   
    def setPlainText(self, text: str | None) -> None:
        super().setPlainText(text)
        self.setHtml(f"""
                <div style="text-align: center;">
                    <p>{self.toPlainText()}</p>
                </div>
                """)
    def updatePos(self):
        cursorPos=QCursor().pos()-self.view.pos()
        self.setPos(self.view.mapToScene(QPoint(cursorPos.x(),cursorPos.y())))
        if cursorPos.y() <=10:
            self.setPos(self.view.mapToScene(QPoint(cursorPos.x(),10)))
        if  self.view.height()-cursorPos.y()-int(self.boundingRect().height())<=10:
            self.setPos(self.view.mapToScene(QPoint(cursorPos.x(),self.view.height()-int(self.boundingRect().height())-10)))
        if cursorPos.x()<=10:
            self.setPos(self.view.mapToScene(QPoint(10,cursorPos.y())))
        if  self.view.width()-cursorPos.x()-int(self.boundingRect().width())<=10:
            self.setPos(self.view.mapToScene(QPoint(self.view.width()-int(self.boundingRect().width()),cursorPos.y())))
            
class Text(QGraphicsTextItem):
    def __init__(self, text,view:QGraphicsView, parent=None):
        super().__init__(text, parent)
        self.setFlags(
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        
        self.view=view
        self.fonte = QFont('Arial', 20)
        self.opacity_=1
        self.setFont(self.fonte)
        self.setDefaultTextColor(Qt.black)
      
        self.fillColor = QColor(255, 255, 255, 255)
        self.borderColor=QColor(0, 0, 0, 255)
        self.borderThickness=1
        self.setAcceptHoverEvents(True)
        self.rotCursor= QCursor(QPixmap(resource_path("interfaceAssets/interfaceIcons/doubleRot.png")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.handle_color = QColor(8, 184, 240 , 255)
        self.handle_active_color=QColor(241, 106, 7,200)
        self.textAlignement="left"
        self._removable=True # The text can be removed 
        self.blocked=False
        self._resizingLeft=False
        self._resizeLeft=False
        self._resizeRight=False
        self._resizingRight=False
        self._resizeTop=False
        self._resizingTop=False
        self._resizeBottom=False
        self._resizingBottom=False
        self._drag=False
        self._draging=False
        self._rotate=False
        self._rotating=False
        self._startPos = QPointF(0,0)
        self._oldProperties=dict()
        self.selectionItems=None
 
        self._group=dict()
        pos = self.boundingRect().center()
        self.adjustSize()
        self.setTextWidth(self.boundingRect().width())
        rotationLabel = Lable("0°",75,self.view)
        sizeLabel=Lable("Width: \nHeight: ",100,self.view)
        
        height=abs(self.boundingRect().top()-self.boundingRect().bottom())
        rotationLabel.setPlainText(f"{int(self.rotation())}°")
        sizeLabel.setPlainText(f"Width:{int(self.textWidth())} \nHeight:{int(height)} ")


     
        rotationLabel.updatePos()

        sizeLabel.updatePos()
        self._addToGroup(rotationLabel,"rotLabel")
        self._addToGroup(sizeLabel,"sizeLabel")
    def setFontFamily(self,fontName:str):
        self.font().setFamily(fontName)
    def setFontSize(self,a:int):
        font=self.font()
        font.setPointSize(a)
        self.setFont(font)
    def setBold(self,a:bool):
        font=self.font()
        font.setBold(a)
        self.setFont(font)
    def setItalic(self,a:bool):
        font=self.font()
        font.setItalic(a)
        self.setFont(font)
    def setUnderline(self,a:bool):
        font=self.font()
        font.setUnderline(a)
        self.setFont(font)
    def setStrikethrough(self,a:bool):
        font=self.font()
        font.setStrikeOut(a)
        self.setFont(font)
    def setFillColor(self,color:QColor):
        self.fillColor=color
    def setBorderColor(self,color:QColor):
        self.borderColor=color
    def setBorderThickness(self,a:float):
        self.borderThickness=a    
    def getProperties(self):
        return {"pos":self.pos(),"rotation":self.rotation(),"width":self.textWidth(),"font":self.font(),"textColor":self.defaultTextColor(),"text":self.toPlainText(),"zValue":self.zValue()}
    def setTextColor(self,color:QColor):
        self.setDefaultTextColor(color)
    def setWidth(self, width):
        left_edge = self.mapToScene(self.boundingRect().topLeft())
        
        self.setTextWidth(width)
        self.setTransformOriginPoint(self.boundingRect().center())
     
        # Get the new left edge after changing width
        new_left_edge = self.mapToScene(self.boundingRect().topLeft())
        # Adjust the position to keep the left edge constant
        delta = left_edge - new_left_edge
        self.moveBy(delta.x(),delta.y())
    def posFromItem(self,item):
        return self.pos()-item.rect().topLeft()
    def setPosFromItem(self,pos,item):
        self.setPos(pos+item.rect().topLeft())
    def resizeToRatio(self,ratio):
        passe=False
        newHeight=self.boundingRect().height()*ratio
        self.setTextWidth(self.textWidth()*ratio)
        while self.boundingRect().height() < newHeight :
            passe=True
            font=QFont(self.font())
            currentSize = font.pointSizeF()
            
            font.setPointSizeF(currentSize + 1)
            self.setFont(font)

        while self.boundingRect().height() > newHeight and not passe:
            
            font=QFont(self.font())
            currentSize = font.pointSizeF()
            
            if currentSize - 1>0:
                font.setPointSizeF(currentSize - 1)
                self.setFont(font)
                
                
            else:
               
                break
            
    def __copy__(self):
        textCopy=Text(self.toPlainText(),self.view)
        textCopy.setPos(self.pos())
        textCopy.setTextWidth(self.textWidth())
        textCopy.setFont(self.font())
        textCopy.setZValue(self.zValue())
        textCopy.setDefaultTextColor(self.defaultTextColor())
        textCopy.setFillColor(self.fillColor)
        textCopy.setBorderThickness(self.borderThickness)
        textCopy.setBorderColor(self.borderColor)
        textCopy.setHtml(self.toHtml())
        return textCopy
    def setInteraction(self,a:bool):
        self.setFlag(QGraphicsTextItem.ItemIsSelectable, a)
        self.setFlag(QGraphicsTextItem.ItemIsMovable, a)
        self.setFlag(QGraphicsTextItem.ItemIsFocusable, a)  
        self.setAcceptHoverEvents(a)  
        if a:
            self.blocked=False
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
        else:
            self.blocked=True
            self.setTextInteractionFlags(Qt.NoTextInteraction)    

    def setRemovable(self,a:bool):
        self._removable=a
    def isRemovable(self):
        return self._removable 
    def _addToGroup(self,item,name):
        self._group[name]=item
    def _removeFromGroup(self,name):
        self._group.pop(name)
    def sendToBack(self):
        minZvalue=self.view.getMinZValue()
        
        if minZvalue is not None:
            if self.zValue()==minZvalue:
                return
            for item in self.scene().items():
                item.setZValue(item.zValue()+1)
            self.setZValue(minZvalue)
            self.view.updateVersionBuffer()
    def bringToFront(self):
        maxZvalue=self.view.getMaxZValue()
        if maxZvalue is not None:
            if self.zValue()==maxZvalue:
                return
            self.setZValue(maxZvalue+1)
            self.view.updateVersionBuffer()
    def raise_(self):
        scene = self.view.scene()  # Assuming self.view is your QGraphicsView instance
        currentZValue = self.zValue()
        items=[]
        zValues=[]
        for item in scene.items():
            items.append(item)
            zValues.append(item.zValue())

        if len(zValues) == 1 or currentZValue == max(zValues):
            return  # No need to raise if already at the highest or only item

        # Sort zValues in ascending order
        sortedZValues=sorted(zValues)

        # Find the next higher zValue
        nextZValue = None
        for z in sortedZValues:
            if z > currentZValue:
                nextZValue = z
                break

        if nextZValue is not None:
            
            #Set new zValues to items ,the order is important
            items[zValues.index(nextZValue)].setZValue(currentZValue)
            
            self.setZValue(nextZValue)
            self.view.updateVersionBuffer()

    def lower(self):
        scene = self.view.scene()  # Assuming self.view is your QGraphicsView instance
        currentZValue = self.zValue()
        items=[]
        zValues=[]
        for item in scene.items():
            items.append(item)
            zValues.append(item.zValue())

        if len(zValues) == 1 or currentZValue == min(zValues):
            return  # No need to raise if already at the highest or only item
        
        # Sort zValues in descending order
        sortedZValues=sorted(zValues,reverse=True)

        # Find the next higher zValue
        nextZValue = None
        for z in sortedZValues:
            if z < currentZValue:
                nextZValue = z
                break

        if nextZValue is not None:
 
            #Set new zValues to items ,the order is important
            
            items[zValues.index(nextZValue)].setZValue(currentZValue)
            self.setZValue(nextZValue)
            self.view.updateVersionBuffer()

            
    def hoverMoveEvent(self, event:QMouseEvent):
        pos=event.pos()
        self._resizeLeft=False
        self._resizeRight=False
        self._drag=False
        self._rotate=False
        self._resizeTop=False
        self._resizeBottom=False
        if self.selectionItems is not None and self.isSelected():
            for name in self.selectionItems:
                if self.selectionItems[name].contains(pos):
                    if name=="left":
                        
                        self._resizeLeft=True
                      
                        self.setCursor(Qt.SizeHorCursor)
                        break
                    if name=="right":
                        self._resizeRight=True  
                        self.setCursor(Qt.SizeHorCursor)
                        break
                    if name=="top":
                        self._drag=True  
                        self.setCursor(Qt.SizeAllCursor)
                        break
                    if name =="topRight":
                        self._rotate=True
                        self.setCursor(self.rotCursor)
                        break
                else:
                    self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        super().hoverMoveEvent(event)
    def mousePressEvent(self, event:QMouseEvent):
        self.view.update()
        self._oldProperties=self.getProperties()
        pos=self.pos()
        self._startPos = event.pos() #important  
        textCursor=self.textCursor() 
        self._resizingLeft=False
        self._resizingRight = False
        self._draging=False
        self._rotating=False
        self._resizingTop=False
        self._resizingBottom=False  
        if self._resizeRight:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            textCursor.clearSelection()
            self.setTextCursor(textCursor)
            self._resizingRight = True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
         
            
            
        elif self._resizeLeft:
            
            textCursor.clearSelection()
            self.setTextCursor(textCursor)
            self._resizingLeft=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel)
            
  
            
        
        elif self._drag:
            self.setFlag(QGraphicsItem.ItemIsMovable ,True)
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            textCursor.clearSelection()
            self.setTextCursor(textCursor)
            self._draging=True
        
        
        elif self._rotate:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            textCursor.clearSelection()
            self.setTextCursor(textCursor)
            self._rotating=True
            rotationLabel=self._group["rotLabel"]
            rotationLabel.updatePos()
            self.view.scene().addItem(rotationLabel)
        
            
        
        super().mousePressEvent(event)
        


    def mouseMoveEvent(self, event:QMouseEvent):
        super().mouseMoveEvent(event)
        self.view.update()
        delta = event.pos() - self._startPos
        
        if self._resizingRight :
            
            
            
            self.setWidth(max(self.textWidth() + delta.x(),100))  
            
            self._startPos = event.pos()
        elif self._resizingLeft:
            
            if delta.x()>0:
                if self.textWidth()-delta.x()>100:
                    dx=delta.x()*cos(self.rotation()*pi/180)
                    dy=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(self.pos().x()+dx,self.pos().y()+dy)
                    self.setWidth(self.textWidth()-delta.x())
                    
            else:
                dx=delta.x()*cos(self.rotation()*pi/180)
                dy=delta.x()*sin(self.rotation()*pi/180)
                self.setPos(self.pos().x()+dx,self.pos().y()+dy)
                self.setWidth(self.textWidth()-delta.x())
                

                
            
        elif self._rotating:
            
            
            pos = self.pos()
           
            rotationLabel=self._group["rotLabel"]
            rotationLabel.setPlainText(f"{int(self.rotation())}°")
           
           
            rotationLabel.updatePos()
            max_z_value = self.view.getMaxZValue() # Get the highest current Z-value
            rotationLabel.setZValue(max_z_value + 1)
            
            
            dx=delta.x()
            dy=-delta.y()
            pos=event.pos()
            height=abs(self.boundingRect().top()-self.boundingRect().bottom())
            x=pos.x()+self.textWidth()/2
            y=-pos.y()+height/2

            deltaAngle=(-y*dx+x*dy)*180/((x**2+y**2)*pi)
            self.rotate(-1*deltaAngle)
          
        if self._resizingLeft or self._resizeRight:
            height=abs(self.boundingRect().top()-self.boundingRect().bottom())
            pos = self.pos()
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.setPlainText(f"Width:{int(self.textWidth())} \nHeight:{int(height)} ")
            sizeLabel.updatePos()
            max_z_value = self.view.getMaxZValue() # Get the highest current Z-value
            sizeLabel.setZValue(max_z_value + 1)
             
        
        
    def mouseReleaseEvent(self, event):
        self.view.update()
        if self._oldProperties!=self.getProperties():
            self.view.updateVersionBuffer()
        sizeLabel=self._group["sizeLabel"]
        rotationLabel=self._group["rotLabel"]
        if sizeLabel in self.view.scene().items():
            self.view.scene().removeItem(sizeLabel)
            
        if rotationLabel in self.view.scene().items():
            
            self.view.scene().removeItem(rotationLabel)
        self.setFlag(QGraphicsItem.ItemIsMovable ,False)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self._resizingLeft=False
        self._resizeLeft=False
        self._resizeRight=False
        self._resizingRight=False
        self._resizingTop=False
        self._resizingBottom=False
        self._draging=False
        super().mouseReleaseEvent(event)
        

    def setAlignment(self):
        if self.isSelected():
            self.setHtml(f"""
                <div style="text-align: {self.textPos};">
                    <p>{self.toPlainText()}</p>
                </div>
                """)
            self.view.updateVersionBuffer()

    

    def paint(self, painter, option, widget):
       
        painter.save()
        brush = QBrush(self.fillColor)
        pen=QPen(Qt.NoPen)
        if self.borderThickness!=0:
            pen=QPen()
            pen.setColor(self.borderColor)
            pen.setWidthF(self.borderThickness)
        painter.setPen(pen)
        painter.setBrush(brush)
        rect = self.boundingRect()
        painter.drawRect(rect)
        if self.isSelected():
            pen = QPen()
            pen.setColor(self.handle_color)
            pen.setWidth(5)
            painter.setPen(pen)
            
            painter.drawRect(rect)
        
        
      
        
       
        if self.isSelected():
            self.drawSelectionHandles(painter, rect)
        painter.restore()
        super().paint(painter, option, widget)
        
        
    def drawSelectionHandles(self, painter:QPainter, rect:QRectF):
        handle_size = 20
        handle_length=30
        dragHanleSize=40
        radius=5
        
        painter.setBrush(self.handle_color)
        
        
        # Draw rectangles at the corners and midpoints of the edges
        self._points = {
            "topLeft":rect.topLeft(),
            "topRight":rect.topRight(),
            "bottomLeft":rect.bottomLeft(),
            "bottomRight":rect.bottomRight(),
            "top":QPointF(rect.center().x(), rect.top()),
            "bottom":QPointF(rect.center().x(), rect.bottom()),
            "left":QPointF(rect.left(), rect.center().y()),
            "right":QPointF(rect.right(), rect.center().y()),
            
        }
        self.selectionItems=dict()
        for name in self._points:
            handle_rect = QRectF(self._points[name].x() - handle_size / 2,self._points[name].y() - handle_size / 2, handle_size, handle_size)
            
            if name in {"top","left","right"}:
                
                    
                painter.drawRoundedRect(handle_rect, radius, radius)
            
            elif name!="bottom":
            

                painter.drawEllipse(handle_rect)
            self.selectionItems[name]=handle_rect 

            
    def rotate(self,deltaAngle):
        
      
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setRotation(self.rotation() +deltaAngle)
        if abs(self.rotation())>=360:
            self.setRotation(0)
        if abs(self.rotation())<=2:
            self.setRotation(0)
        if abs(self.rotation()-90)<=2:
            self.setRotation(90)
        if abs(self.rotation()+90)<=2:
            self.setRotation(-90)
        if abs(self.rotation()-180)<=2:
            self.setRotation(180)
        if abs(self.rotation()+180)<=2:
            self.setRotation(-180)
        if abs(self.rotation()-270)<=2:
            self.setRotation(270)
        if abs(self.rotation()+270)<=2:
            self.setRotation(-270)
        
    def contextMenuEvent(self, event):
        if not self.blocked:
            menu = QMenu()
            menu.setStyleSheet("""
    QMenu {
        background-color: rgb(240, 240, 240); /* Same as QLineEdit background */
        border: 1px solid rgb(154, 154, 154);
        padding: 5px;
        border-radius: 10px
    }
    QMenu::item {
        padding: 5px 15px;
        background-color: transparent;
        color: rgb(50, 50, 50);
        font-family: "Arial"; /* Set your custom font */
        font-size: 14px; /* Set the font size */
    }
    QMenu::item:hover {
        background-color: rgb(240, 240, 240); /* Slightly darker on hover */
        color: rgb(30, 30, 30); /* Darker text on hover */
        border-radius: 3px; /* Rounded corners */
    }
    QMenu::item:selected {
        background-color: rgb(245, 245, 245); /* Similar to hover but for selected item */
        color: rgb(20, 20, 20); /* Even darker text on selected */
    }
""")

            rotate_action = QAction("Font", menu)
            rotate_action.triggered.connect(self.openFontDialog)
            menu.addAction(rotate_action)
            #send to back action 
            sendToBackAction=QAction("Send to back",menu)
            sendToBackAction.setIcon(QIcon(resource_path("interfaceAssets/interfaceIcons/send-back.ico")))
            sendToBackAction.triggered.connect(self.sendToBack)
            menu.addAction(sendToBackAction)
            #bring to front action
            bringToFrontAction=QAction("Bring to front",menu)
            bringToFrontAction.triggered.connect(self.bringToFront)
            menu.addAction(bringToFrontAction)

            #lower action
            lowerAction=QAction("Depress",menu)
            lowerAction.triggered.connect(self.lower)
            menu.addAction(lowerAction)
            
            #raise action
            raiseAction=QAction("Elevate",menu)
            raiseAction.triggered.connect(self.raise_)
            menu.addAction(raiseAction)
            

            menu.exec(event.screenPos())
        else:
            event.ignore()
    def openFontDialog(self):
        FontDialog = QFontDialog()
        font, ok = FontDialog.getFont(self.fonte, self.view.parent(), "Select Font")
       
        # If the user selected a font, apply it to the text item and close the dialog
        if ok:
            self.setFont(font)
            self.fonte = font
            #self.document().setDefaultFont(font)
            self.prepareGeometryChange()
            
            # Close the font dialog
            FontDialog.done(QFontDialog.Accepted)
            self.view.updateVersionBuffer()

class Shape(QGraphicsRectItem):
    def __init__(self,view,parent=None):
        super().__init__(parent=parent)
        self.view=view
        self.setFlags(
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsFocusable 
                      )
        self.setAcceptHoverEvents(True)
        self.locked=False
        self.image=None
        self._removable=True  
        self.blocked=False        
        self.cursorPos=None
        self.rotCursor= QCursor(QPixmap(resource_path("interfaceAssets/interfaceIcons/doubleRot.png")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.handle_color = QColor(8, 184, 240 , 200)
        self.handle_active_color=QColor(241, 106, 7,200)
        self.fillColor=QColor(162, 217, 206 ,255)
        self.borderColor=QColor(0,0,0,255)
        self.borderThickness=0
        self._resizingLeft=False
        self._resizeLeft=False
        self._resizeTop=False
        self._resizeBottom=False
        self._resizeRight=False
        self._resizingRight=False
        self._resizingBottom=False
        self._resizingTop=False
        self._resizeDiagBottomRight=False
        self._resizingDiagBottomRight=False
        self._resizeDiagTopLeft=False
        self._resizingDiagTopLeft=False
        self._resizingDiagBottomLeft=False
        self._resizeDiagBottomLeft=False
        self._resizeDiagTopRight=False
        self._resizingDiagTopRight=False
        self._drag=False
        self._draging=False
        self._rotate=False
        self._rotating=False
        self._startPos = QPointF(0,0)
        self.selectionItems=None
        self.keepAspectRatio=False
        self._group=dict()
        self.oldProperties=dict()
        pos = self.boundingRect().center()
      
        self.shapeRect = self.boundingRect()
   
        self.opacity_=1
        rotationLabel = Lable("0°",75,self.view)
        sizeLabel=Lable("Width: \nHeight: ",100,self.view)
        
        height=abs(self.boundingRect().top()-self.boundingRect().bottom())
        rotationLabel.setPlainText(f"{int(self.rotation())}°")
        sizeLabel.setPlainText(f"Width:{int(self.rect().width())} \nHeight:{int(height)} ")
        rotationLabel.updatePos()
        sizeLabel.updatePos()

        
        self._addToGroup(rotationLabel,"rotLabel")
        self._addToGroup(sizeLabel,"sizeLabel")
        self.setRect(QRectF(0,0,200,200))
        self.selectionPen=QPen()
        self.selectionPen.setWidthF(5)
        self.selectionPen.setColor(self.handle_color)
    def setFillColor(self,color:QColor):
        self.fillColor=color
    def setBorderColor(self,color:QColor):
        self.borderColor=color
    def setBorderThickness(self,a:float):
        self.borderThickness=a
    def setLocked(self,a:bool):
        self.locked=a
    def isLocked(self):
        return self.locked
    def getProperties(self):
        return {"pos":self.pos(),"rotation":self.rotation(),"width":self.width(),"height":self.height(),"zValue":self.zValue()}
    def posFromItem(self,item):
        return self.pos()-item.rect().topLeft()
    def setPosFromItem(self,pos,item):
        self.setPos(pos+item.rect().topLeft())
    def width(self):
        return self.rect().width()
    def height(self):
        return self.rect().height()
    @abstractmethod
    def __copy__(self):
        pass
        
    def setInteraction(self,a:bool):

        if not a:
            self.blocked=True
            self.setFlag(QGraphicsItem.ItemIsSelectable,False)
            self.setFlag( QGraphicsItem.ItemIsFocusable,False)
            self.setAcceptHoverEvents(False)         
            
    def setRemovable(self,a:bool):
        self._removable=a
    def isRemovable(self):
        return self._removable
    def setImage(self,image:QImage):
        self.image=image.copy()
        self.setRect(0,0,self.image.width(),self.image.height())
        self.shapeRect = self.boundingRect()
        self.shapeRect.moveTopLeft(self.pos())
        self.shapeRect.setWidth(self.rect().width())
        self.shapeRect.setHeight(self.rect().height())
    def getAspectRatio(self):
        if self.image.height()!=0:
            return self.image.width()/self.image.height() 
    def _addToGroup(self,item,name):
        self._group[name]=item
    
    def _removeFromGroup(self,name):
        self._group.pop(name)
    def resize(self,width:float,height:float):
        if width*height !=0:
            left_edge = self.mapToScene(self.boundingRect().topLeft())
            self.setRect(self.rect().x(),self.rect().y(),width,height)
            self.setTransformOriginPoint(self.boundingRect().center())
            # Get the new left edge after changing width
            new_left_edge = self.mapToScene(self.boundingRect().topLeft())
            # Adjust the position to keep the left edge constant
            delta = left_edge - new_left_edge
            self.moveBy(delta.x(),delta.y())
        else:
            print("Can't resize the item.Item with no dimensions")
    def setWidth(self,width:float):
        if width !=0:
            left_edge = self.mapToScene(self.boundingRect().topLeft())
            self.setRect(self.rect().x(),self.rect().y(),width,self.height())
            self.setTransformOriginPoint(self.boundingRect().center())
            # Get the new left edge after changing width
            new_left_edge = self.mapToScene(self.boundingRect().topLeft())
            # Adjust the position to keep the left edge constant
            delta = left_edge - new_left_edge
            self.moveBy(delta.x(),delta.y())
        else:
            print("Can't resize the item.Item with no dimensions")
    def setHeight(self,height:float):
        if height !=0:
            left_edge = self.mapToScene(self.boundingRect().topLeft())
            self.setRect(self.rect().x(),self.rect().y(),self.width(),height)
            self.setTransformOriginPoint(self.boundingRect().center())
            # Get the new left edge after changing width
            new_left_edge = self.mapToScene(self.boundingRect().topLeft())
            # Adjust the position to keep the left edge constant
            delta = left_edge - new_left_edge
            self.moveBy(delta.x(),delta.y())
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToWidth(self,width:float):
        
        if width!=0:
            left_edge = self.mapToScene(self.boundingRect().topLeft())
            self.setRect(self.rect().x(),self.rect().y(),width,width/self.getAspectRatio())
            self.setTransformOriginPoint(self.boundingRect().center())
            # Get the new left edge after changing width
            new_left_edge = self.mapToScene(self.boundingRect().topLeft())
            # Adjust the position to keep the left edge constant
            delta = left_edge - new_left_edge
            self.moveBy(delta.x(),delta.y())
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToHeight(self,height:float):
        if height!=0:
            self.setRect(self.rect().x(),self.rect().y(),height*self.getAspectRatio(),height)
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToRatio(self,ratio:float):
        if ratio!=0:
            self.setRect(self.rect().x(),self.rect().y(),self.width()*ratio,self.height()*ratio)
        else:
            print("Can't resize the item. Ratio musn't be 0 !!")
        
    def hoverMoveEvent(self, event:QMouseEvent):
        pos=event.pos()
        
        self._resizeLeft=False
        self._resizeRight=False
        self._drag=False
        self._rotate=False
        self._resizeTop=False
        self._resizeBottom=False
        self._resizeDiagBottomRight=False
        self._resizeDiagTopLeft=False
       
        if self.selectionItems is not None and self.isSelected() and not self.blocked:
            
            self._drag=True
            self.setCursor(Qt.SizeAllCursor)
            for name in self.selectionItems:
                
                if self.selectionItems[name].contains(pos):
                    if name=="left":
                        
                        self._resizeLeft=True
                        self._drag=False
                        self.setCursor(Qt.SizeHorCursor)
                        break
                    if name=="right":
                        
                        
                        self._resizeRight=True  
                        self._drag=False

                        
                        self.setCursor(Qt.SizeHorCursor)
                        break
                    
                    if name=="top":
                        self._resizeTop=True
                        self._drag=False
                        self.setCursor(Qt.SizeVerCursor)
                        break
                    if name=="bottom":
                        self._resizeBottom=True
                        self._drag=False
                        self.setCursor(Qt.SizeVerCursor)
                        break
                    if name =="center":
                        
                        self._rotate=True
                        self._drag=False
                       
                        self.setCursor(self.rotCursor)
                        
                        break
                    if name=="bottomRight":
                        self._resizeDiagBottomRight=True
                        self._drag=False
                        self.setCursor(Qt.SizeFDiagCursor)
                        break
                    if name=="topLeft":
                        self._resizeDiagTopLeft=True
                        self._drag=False
                        self.setCursor(Qt.SizeFDiagCursor)
                        break
                    if name=="topRight":
                        self._resizeDiagTopRight=True
                        self._drag=False
                        self.setCursor(Qt.SizeBDiagCursor)
                        break
                    if name=="bottomLeft":
                        self._resizeDiagBottomLeft=True
                        self._drag=False
                        self.setCursor(Qt.SizeBDiagCursor)
                        break
        else:
            
            self.setCursor(Qt.ArrowCursor)
        
        super().hoverMoveEvent(event)
    def mousePressEvent(self, event:QMouseEvent):
        super().mousePressEvent(event)
        if self.isLocked():
            return
        self.view.update()
        self.oldProperties=self.getProperties()
        pos=self.pos()
        self._startPos = event.pos() #important
        self._startPos1= self._startPos 
        self.cursorPos=self._startPos        
        self._resizingLeft=False
        self._resizingRight = False
        self._draging=False
        self._rotating=False
        self._resizingTop=False
        self._resizingBottom=False  
        self._resizingDiagBottomRight=False
        self._resizingDiagTopLeft=False
        self._resizingDiagTopRight=False
        self._resizingDiagBottomLeft=False
        if self._resizeRight:
            self._resizingRight = True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel)  
        elif self._resizeLeft:
            self._resizingLeft=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._drag:
            self.setFlag(QGraphicsItem.ItemIsMovable ,True)
            self.setOpacity(0.6)
            self._draging=True
            self._resizeDiagTopRight=False
        elif self._rotate:
            self._rotating=True
            rotationLabel=self._group["rotLabel"]
            rotationLabel.updatePos()
            self.view.scene().addItem(rotationLabel)
            self.setOpacity(0.6)
        elif self._resizeTop:
            self._resizingTop=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._resizeBottom:
            self._resizingBottom=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._resizeDiagBottomRight:
            self._resizingDiagBottomRight=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._resizeDiagTopLeft:
            self._resizingDiagTopLeft=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._resizeDiagBottomLeft:
            self._resizingDiagBottomLeft=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel) 
        elif self._resizeDiagTopRight:
            self._resizingDiagTopRight=True
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.updatePos()
            self.view.scene().addItem(sizeLabel)
        
    def mouseMoveEvent(self, event:QMouseEvent):
        
        super().mouseMoveEvent(event)
        if self.isLocked():
            return
        self.view.update()
        delta = event.pos() - self._startPos
        delta1= event.pos() - self._startPos1
        pos = self.pos()
        self.cursorPos=event.pos()
        
        if self._resizingRight :

            self.setWidth(max(self.rect().width()+ delta.x(),100))
            self._startPos = event.pos()

        elif self._resizingLeft:
            
            if delta.x()>0:
                if self.rect().width()-delta.x()>100:
                    dx=delta.x()*cos(self.rotation()*pi/180)
                    dy=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx,pos.y()+dy)
                    self.setWidth(self.rect().width()- delta.x())
                   
            else:
                dx=delta.x()*cos(self.rotation()*pi/180)
                dy=delta.x()*sin(self.rotation()*pi/180)
                self.setPos(pos.x()+dx,pos.y()+dy)
                self.setWidth(self.rect().width()- delta.x())
        elif self._resizingBottom:
            self.setHeight(max(self.rect().height()+ delta.y(),100))
            self._startPos = event.pos()
        elif self._resizingTop:
            if delta.y()>0:
                if self.rect().height()-delta.y()>100:
                    dx=-delta.y()*sin(self.rotation()*pi/180)
                    dy=delta.y()*cos(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx,pos.y()+dy)
                    self.setHeight(self.rect().height()- delta.y())
                   
            else:
                dx=-delta.y()*sin(self.rotation()*pi/180)
                dy=delta.y()*cos(self.rotation()*pi/180)
                self.setPos(pos.x()+dx,pos.y()+dy)
                self.setHeight(self.rect().height()- delta.y())   

        elif self._resizingDiagBottomRight:
            if  self.keepAspectRatio:
                
                self.resizeToWidth(max(self.rect().width()+ delta.x(),100))
                
            else:
                self.resize(max(self.rect().width()+ delta.x(),100),max(self.rect().height()+ delta.y(),100))
            self._startPos = event.pos()


        elif self._resizingDiagBottomLeft:
            if delta1.x()>0:
                if self.rect().width()-delta.x()>100:
                    dx=delta1.x()*cos(self.rotation()*pi/180)
                    dy=delta1.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx,pos.y()+dy)
                    self.resize(self.rect().width()- delta1.x(),max(self.rect().height()+ delta.y(),100))
                    self._startPos = event.pos()
            else:
                dx=delta1.x()*cos(self.rotation()*pi/180)
                dy=delta1.x()*sin(self.rotation()*pi/180)
                self.setPos(pos.x()+dx,pos.y()+dy)
                self.resize(self.rect().width()- delta1.x(),max(self.rect().height()+ delta.y(),100))
                self._startPos = event.pos()
        elif self._resizeDiagTopRight:
            
            if delta1.y()>0:
                if self.rect().height()-delta1.y()>100:
                    dx=-delta1.y()*sin(self.rotation()*pi/180)
                    dy=delta1.y()*cos(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx,pos.y()+dy)
                    self.resize(max(self.rect().width()+ delta.x(),100),self.rect().height()- delta1.y())
                    self._startPos = event.pos()
            else:
                dx=-delta1.y()*sin(self.rotation()*pi/180)
                dy=delta1.y()*cos(self.rotation()*pi/180)
                self.setPos(pos.x()+dx,pos.y()+dy)
                self.resize(max(self.rect().width()+ delta.x(),100),self.rect().height()- delta1.y())

                self._startPos = event.pos()

        elif self._resizingDiagTopLeft:
            
            if delta.y()>0 and delta.x()>0:
                if self.rect().height()-delta.y()>100 and self.rect().width()-delta.x()>100:
                    dx1=-delta.y()*sin(self.rotation()*pi/180)
                    dy1=delta.y()*cos(self.rotation()*pi/180)
                    dx2=delta.x()*cos(self.rotation()*pi/180)
                    dy2=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx1+dx2,pos.y()+dy1+dy2)
                    
                    self.resize(self.rect().width()- delta.x(),self.rect().height()- delta.y()) 
                elif self.rect().height()-delta.y()>100:
                    dx1=-delta.y()*sin(self.rotation()*pi/180)
                    dy1=delta.y()*cos(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx1,pos.y()+dy1)
                    self.setHeight(self.rect().height()- delta.y())
                    
                elif self.rect().width()-delta.x()>100:
                    dx2=delta.x()*cos(self.rotation()*pi/180)
                    dy2=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx2,pos.y()+dy2)
                    
                    self.setWidth(self.rect().width()- delta.x())    
            elif delta.y()>0:
                if self.rect().height()-delta.y()>100 :
                    dx1=-delta.y()*sin(self.rotation()*pi/180)
                    dy1=delta.y()*cos(self.rotation()*pi/180)
                    dx2=delta.x()*cos(self.rotation()*pi/180)
                    dy2=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx1+dx2,pos.y()+dy1+dy2)
                    self.resize(self.rect().width()- delta.x(),self.rect().height()- delta.y())
                    
                    
                else:
                    dx2=delta.x()*cos(self.rotation()*pi/180)
                    dy2=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx2,pos.y()+dy2) 
                    self.setWidth(self.rect().width()- delta.x())  
                     

            elif delta.x()>0:
                if self.rect().width()-delta.x()>100:
                    dx1=-delta.y()*sin(self.rotation()*pi/180)
                    dy1=delta.y()*cos(self.rotation()*pi/180)
                    dx2=delta.x()*cos(self.rotation()*pi/180)
                    dy2=delta.x()*sin(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx1+dx2,pos.y()+dy1+dy2)
                    self.resize(self.rect().width()- delta.x(),self.rect().height()- delta.y())
                else:
                    dx1=-delta.y()*sin(self.rotation()*pi/180)
                    dy1=delta.y()*cos(self.rotation()*pi/180)
                    self.setPos(pos.x()+dx1,pos.y()+dy1)
                    
                    self.setHeight(self.rect().height()- delta.y())
                
            else:
                dx1=-delta.y()*sin(self.rotation()*pi/180)
                dy1=delta.y()*cos(self.rotation()*pi/180)
                dx2=delta.x()*cos(self.rotation()*pi/180)
                dy2=delta.x()*sin(self.rotation()*pi/180)
                self.setPos(pos.x()+dx1+dx2,pos.y()+dy1+dy2)
                
                self.resize(self.rect().width()- delta.x(),self.rect().height()- delta.y())

            
        elif self._rotating:
            
            
            
           
            rotationLabel=self._group["rotLabel"]
            rotationLabel.setPlainText(f"{int(self.rotation())}°")
            
            rotationLabel.updatePos()
            max_z_value = max(item.zValue() for item in self.view.scene().items())  # Get the highest current Z-value
            rotationLabel.setZValue(max_z_value + 1)
            rotationLabel.show()
            
            dx=delta.x()
            dy=-delta.y()
            pos=event.pos()
            height=abs(self.boundingRect().top()-self.boundingRect().bottom())
            x=pos.x()+self.boundingRect().width()/2
            y=-pos.y()+height/2

            deltaAngle=-(-y*dx+x*dy)*180/((x**2+y**2)*pi)
            self.rotate(deltaAngle)
            
        if self._resizingLeft or self._resizeRight or self._resizingTop or self._resizingBottom or self._resizingDiagBottomRight or self._resizingDiagTopLeft or self._resizingDiagBottomLeft or self._resizingDiagTopRight:
            height=abs(self.boundingRect().top()-self.boundingRect().bottom())
            pos = self.pos()
            sizeLabel=self._group["sizeLabel"]
            sizeLabel.setPlainText(f"Width:{int(self.rect().width())} \nHeight:{int(height)} ")
            sizeLabel.updatePos()
            max_z_value = max(item.zValue() for item in self.view.scene().items())  # Get the highest current Z-value
            sizeLabel.setZValue(max_z_value + 1)
            sizeLabel.show()  
        
        
    def mouseReleaseEvent(self, event:QMouseEvent):
        super().mouseReleaseEvent(event)
        if self.isLocked():
            return 
        self.view.update()
        if self.oldProperties!=self.getProperties():
            self.view.updateVersionBuffer()
        sizeLabel=self._group["sizeLabel"]
        rotationLabel=self._group["rotLabel"]
        if sizeLabel in self.view.scene().items():
            self.view.scene().removeItem(sizeLabel)
            
        if rotationLabel in self.view.scene().items():
            
            self.view.scene().removeItem(rotationLabel)
        self.setFlag(QGraphicsItem.ItemIsMovable ,False)
        
        self._resizingLeft=False
        self._resizeLeft=False
        self._resizeRight=False
        self._resizingRight=False
        self._resizeDiagBottomRight=False
        self._resizeDiagTopLeft=False
        self._resizingDiagBottomRight=False
        self._resizingDiagTopLeft=False
        self._resizingDiagTopRight=False
        self._resizeDiagTopRight=False
        self._resizingDiagBottomLeft=False
        self._resizeDiagBottomLeft=False
        self._drag=False
        self._rotating=False
        self.setOpacity(1)
        
   
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.keepAspectRatio=True
        super().keyPressEvent(event)
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.keepAspectRatio=False
        super().keyReleaseEvent(event)
    def paint(self, painter, option=None, widget=None):

        
        painter.save()
        center=self.mapToScene(self.boundingRect().center())
        centerX=center.x()
        centerY=center.y()
       
        
        
        # Create a QTransform for rotation and scaling
        transform = QTransform()
        transform.translate(centerX,centerY)
        transform.rotate(self.rotation())
        transform.translate(-centerX,-centerY)
        # Set the transform to the painter
        painter.setTransform(transform)
        
        
        
        self.shapeRect.setWidth(self.width())
        self.shapeRect.setHeight(self.height())
        self.shapeRect.moveCenter(center)
        
        painter.restore()
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        brush=QBrush(self.fillColor)
        pen=QPen(Qt.NoPen)
        if self.borderThickness!=0:
            pen=QPen()
            pen.setColor(self.borderColor)
            pen.setWidthF(self.borderThickness)
        painter.setPen(pen)    
        painter.setBrush(brush)
        self.drawContent(painter)
        
    @abstractmethod
    def drawContent(self,painter:QPainter):
        pass
    def drawSelectionHandles(self, painter:QPainter, rect:QRectF):
        handle_size = 20
        handle_length=30
        dragHanleSize=40
        radius=5
        
        painter.setBrush(self.handle_color)
        
        
        # Draw rectangles at the corners and midpoints of the edges
        self._points = {
            "topLeft":rect.topLeft(),
            "topRight":rect.topRight(),
            "bottomLeft":rect.bottomLeft(),
            "bottomRight":rect.bottomRight(),
            "top":QPointF(rect.center().x(), rect.top()),
            "bottom":QPointF(rect.center().x(), rect.bottom()),
            "left":QPointF(rect.left(), rect.center().y()),
            "right":QPointF(rect.right(), rect.center().y()),
            "center":rect.center()
                             
            
        }
        self.selectionItems=dict()
        for name in self._points:
            handle_rect = QRectF(self._points[name].x() - handle_size / 2,self._points[name].y() - handle_size / 2, handle_size, handle_size)
            
            if name in {"top","left","right","bottom"}:
                
                    
                painter.drawRoundedRect(handle_rect, radius, radius)
            
            else:
            

                painter.drawEllipse(handle_rect)
            self.selectionItems[name]=handle_rect 
        if self.cursorPos is not None:

            if self._rotating:
                pen = QPen()
                pen.setColor(QColor(0,0,0,255))
                pen.setWidth(3)
                pen.setStyle(Qt.DashLine)
                painter.setPen(pen)
                painter.drawLine(int(rect.center().x()),int(rect.center().y()),int(self.cursorPos.x()),int(self.cursorPos.y()))
           
    def rotate(self,deltaAngle):

        
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setRotation(self.rotation() +deltaAngle)
        if abs(self.rotation())>=360:
            self.setRotation(0)
        if abs(self.rotation())<=2:
            self.setRotation(0)
        if abs(self.rotation()-90)<=2:
            self.setRotation(90)
        if abs(self.rotation()+90)<=2:
            self.setRotation(-90)
        if abs(self.rotation()-180)<=2:
            self.setRotation(180)
        if abs(self.rotation()+180)<=2:
            self.setRotation(-180)
        if abs(self.rotation()-270)<=2:
            self.setRotation(270)
        if abs(self.rotation()+270)<=2:
            self.setRotation(-270)
    def sendToBack(self):
        minZvalue=self.view.getMinZValue()
        if minZvalue is not None:
            if self.zValue()==minZvalue:
                return
            for item in self.scene().items():
                item.setZValue(item.zValue()+1)
            self.setZValue(minZvalue)
            self.view.updateVersionBuffer()
    def bringToFront(self):
        maxZvalue=self.view.getMaxZValue()
        if maxZvalue is not None:
            if self.zValue()==maxZvalue:
                return
            self.setZValue(maxZvalue+1)
            self.view.updateVersionBuffer()
    def raise_(self):
        buffer=self.view.buffer  
        currentZValue = self.zValue()
        items=[]
        zValues=[]
        for item in buffer:
            items.append(item)
            zValues.append(item.zValue())

        if len(zValues) == 1 or currentZValue == max(zValues):
            return  # No need to raise if already at the highest or only item

        # Sort zValues in ascending order
        sortedZValues=sorted(zValues)

        # Find the next higher zValue
        nextZValue = None
        for z in sortedZValues:
            if z > currentZValue:
                nextZValue = z
                break

        if nextZValue is not None:
            
            #Set new zValues to items ,the order is important
            items[zValues.index(nextZValue)].setZValue(currentZValue)
            
            self.setZValue(nextZValue)
            self.view.updateVersionBuffer()

    def lower(self):
        buffer=self.view.buffer
        currentZValue = self.zValue()
        items=[]
        zValues=[]
        for item in buffer:
            items.append(item)
            zValues.append(item.zValue())

        if len(zValues) == 1 or currentZValue == min(zValues):
            return  # No need to raise if already at the highest or only item
        
        # Sort zValues in descending order
        sortedZValues=sorted(zValues,reverse=True)

        # Find the next higher zValue
        nextZValue = None
        for z in sortedZValues:
            if z < currentZValue:
                nextZValue = z
                break

        if nextZValue is not None:
 
            #Set new zValues to items ,the order is important
            
            items[zValues.index(nextZValue)].setZValue(currentZValue)
            self.setZValue(nextZValue)
            self.view.updateVersionBuffer()
    def setShapeToBackground(self) :
        self.setWidth(self.view.workView.width())
        self.setHeight(self.view.workView.height())
        self.setRotation(0)
        self.setPos(self.view.workView.rect().topLeft())
        self.view.updateVersionBuffer()
    def contextMenuEvent(self, event):
        if not self.blocked:
            menu = QMenu()
     
      
            menu.setStyleSheet("""
    QMenu {
        background-color: rgb(240, 240, 240); /* Same as QLineEdit background */
        border: 1px solid rgb(154, 154, 154);
        padding: 5px;
        
    }
    QMenu::item {
        padding: 5px 15px;
        background-color: transparent;
        color: rgb(50, 50, 50);
        font-family: "Arial"; /* Set your custom font */
        font-size: 14px; /* Set the font size */
    }
    QMenu::item:hover {
        background-color: rgb(240, 240, 240); /* Slightly darker on hover */
        color: rgb(30, 30, 30); /* Darker text on hover */
        border-radius: 3px; /* Rounded corners */
    }
    QMenu::item:selected {
        background-color: rgb(245, 245, 245); /* Similar to hover but for selected item */
        color: rgb(20, 20, 20); /* Even darker text on selected */
    }
""")

            
            #send to back action 
            sendToBackAction=QAction("Send to back",menu)
            sendToBackAction.triggered.connect(self.sendToBack)
           
            icon=QIcon(resource_path("interfaceAssets/interfaceIcons/send-back.ico"))
            sendToBackAction.setIcon(icon)
            
            menu.addAction(sendToBackAction)
            #bring to front action
            bringToFrontAction=QAction("Bring to front",menu)
            bringToFrontAction.triggered.connect(self.bringToFront)
            menu.addAction(bringToFrontAction)

            #lower action
            lowerAction=QAction("Depress",menu)
            lowerAction.triggered.connect(self.lower)
            menu.addAction(lowerAction)
            
            #raise action
            raiseAction=QAction("Elevate",menu)
            raiseAction.triggered.connect(self.raise_)
            menu.addAction(raiseAction)
            #set image to background
            BackgroundImageAction=QAction("set image to background")
            BackgroundImageAction.triggered.connect(self.setShapeToBackground)
            menu.addAction(BackgroundImageAction)
            menu.exec(event.screenPos())
        else:
            event.ignore()
class RoundedRect(Shape):
    def __init__(self,view,parent=None):
        super().__init__(view=view,parent=parent)
      
        self.radius=20
    def setRadius(self,radius:float):
        self.radius=radius
    

    def drawContent(self, painter: QPainter):
  
        
        painter.drawRoundedRect(self.boundingRect(),self.radius,self.radius)
        if self.isSelected() and not self.blocked:
            painter.setPen(self.selectionPen)
            painter.setBrush(Qt.NoBrush)  # No brush, no fill
            painter.drawRect(self.boundingRect())
            self.drawSelectionHandles(painter, self.boundingRect())
    def __copy__(self):
        
        shapeCopy=RoundedRect(self.view)
        shapeCopy.setPos(self.pos())
        shapeCopy.resize(self.width(),self.height())
        shapeCopy.setOpacity(self.opacity_)
        shapeCopy.setZValue(self.zValue())
        shapeCopy.setFillColor(self.fillColor)
        shapeCopy.setBorderColor(self.borderColor)
        shapeCopy.setBorderThickness(self.borderThickness)
        shapeCopy.setRadius(self.radius)
        
        return shapeCopy
class Rect(RoundedRect):
    def __init__(self,view,parent=None):
        super().__init__(view=view,parent=parent)
        self.setRadius(0)
    def __copy__(self):
        
        shapeCopy=Rect(self.view)
        shapeCopy.setPos(self.pos())
        shapeCopy.resize(self.width(),self.height())
        shapeCopy.setOpacity(self.opacity_)
        shapeCopy.setZValue(self.zValue())
        shapeCopy.setFillColor(self.fillColor)
        shapeCopy.setBorderColor(self.borderColor)
        shapeCopy.setBorderThickness(self.borderThickness)
       
       
        return shapeCopy
    

class Circle(Shape):
    def __init__(self,view,parent=None):
        super().__init__(view=view,parent=parent)

        self.xRadius=100
        self.yRadius=100
    def setXRadius(self,radius:float):
        self.xRadius=radius
    def setYRadius(self,radius:float):
        self.yRadius=radius
    
    def resize(self,width:float,height:float):
        super().resize(width,height)
        if width*height!=0:
            self.setXRadius(width/2)
            self.setYRadius(height/2)
            
    def setWidth(self,width:float):
        super().setWidth(width)
        if width !=0:
            self.setXRadius(width/2)
            
            
        else:
            print("Can't resize the item.Item with no dimensions")
            
    def setHeight(self,height:float):
        super().setHeight(height)
        if height !=0:
            self.setYRadius(height/2)
            
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToWidth(self,width:float):
        super().resizeToWidth(width)
        if width!=0:
            self.setXRadius(width/2)
            self.setYRadius(self.height()/2)
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToHeight(self,height:float):
        super().resizeToHeight(height)
        if height!=0:
            self.setXRadius(self.width()/2)
            self.setYRadius(height/2)
        else:
            print("Can't resize the item.Item with no dimensions")
    def resizeToRatio(self,ratio:float):
        super().resizeToRatio(ratio)
        if ratio!=0:
            self.setXRadius(self.width()/2)
            self.setYRadius(self.height()/2)
            
        else:
            print("Can't resize the item. Ratio musn't be 0 !!")
    def drawContent(self, painter: QPainter):
     
        
        painter.drawEllipse(self.boundingRect().center(),self.xRadius,self.yRadius)
        if self.isSelected() and not self.blocked:
            painter.setPen(self.selectionPen)
            painter.setBrush(Qt.NoBrush)  # No brush, no fill
            painter.drawRect(self.boundingRect())
            self.drawSelectionHandles(painter, self.boundingRect())
    def __copy__(self):
        
        shapeCopy=Circle(self.view)
        shapeCopy.setPos(self.pos())
        shapeCopy.resize(self.width(),self.height())
        shapeCopy.setOpacity(self.opacity_)
        shapeCopy.setZValue(self.zValue())
        shapeCopy.setFillColor(self.fillColor)
        shapeCopy.setBorderColor(self.borderColor)
        shapeCopy.setBorderThickness(self.borderThickness)
        shapeCopy.setXRadius(self.xRadius)
        shapeCopy.setYRadius(self.yRadius)
        return shapeCopy
class Image(Shape):
    def __init__(self, view,imagePath=None,parent=None):
    
        super().__init__(view, parent)
        self.imagePath=imagePath
        self.image=None
        if imagePath: 
            self.image=QImage(imagePath)   
            self.setImage(self.image)
       
    
    def getAspectRatio(self):
        if self.image:
            if self.image.height()!=0:
                return self.image.width()/self.image.height() 
    def __copy__(self):
        imageCopy=Image(self.view)
        imageCopy.setImage(self.image)
        imageCopy.setPos(self.pos())
        imageCopy.resize(self.width(),self.height())
        imageCopy.setOpacity(self.opacity_)
        imageCopy.setZValue(self.zValue())
        imageCopy.setBorderColor(self.borderColor)
        imageCopy.setBorderThickness(self.borderThickness)
        imageCopy.setFillColor(self.fillColor)

        return imageCopy
    
    def drawContent(self, painter: QPainter):
        if self.image:
            painter.setBrush(Qt.NoBrush)  # No brush, no fill
            painter.drawRect(self.boundingRect())
            painter.drawImage(self.boundingRect(),self.image)
        if self.isSelected() and not self.blocked:
            painter.setPen(self.selectionPen)
            painter.setBrush(Qt.NoBrush)  # No brush, no fill
            painter.drawRect(self.boundingRect())
            self.drawSelectionHandles(painter, self.boundingRect())
class Video(Image):
    def __init__(self, view,videoPath,audioTempPath):
        
        super().__init__(view)
     
        

        self.videoPath=videoPath
        self._audioTempFile=audioTempPath
        
        self._scroll=False
        self._scrolling=False
        self.sliderBaseColor=QColor(213, 216, 220 ,255)
        self.sliderColor=QColor(255,0,0,255)
        self.sliderCursorColor=QColor(255,0,0,255)
        self.borderColor=QColor(0,0,0,150)
        self.durationFont=QFont("arial",10)
        self.opacity_=1
       
  
  
      
        self.play=True
        self.playing=True
        self.blocked=False
        self.sliderOffset=QPointF(0,-30)
        self.sliderRect=QRectF(0,0,0,10)
        self.sliderRect.moveBottomLeft(self.rect().bottomLeft()+self.sliderOffset)
        self.sliderBaseRect=QRectF(0,0,self.width(),6)
        self.sliderBaseRect.moveBottomLeft(self.rect().bottomLeft()+self.sliderOffset)
        self.sliderCursorRect=QRectF(0,0,20,20)
        self.borderRect=QRectF(0,0,self.width(),50)
        self.borderRect.moveBottomLeft(self.rect().bottomLeft())
        self.playRect=QRectF(0,0,50,50)
        self.playRect.moveCenter(self.rect().center())
        self.durationRect=QRectF(0,0,130,30)
        self.timer = QTimer()
        self.fps=None
        self.videoTimer=None
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.updateFrame)
        
        self.passedTime=0
        self.offsetTime=0
        self.scrollingDuration=0
        self._inEditMode=True
        self._overPlayButton=False
        self.EditTimer=QTimer()
        self.EditTimer.timeout.connect(self.exitEditMode)
        self.EditTimer.start(5000)
    def setVideoTimer(self):
        self.videoTimer=Timer(0,self.videoClip.duration)
    def loadVideoClip(self):
        self.videoClip = VideoFileClip(self.videoPath)
        frame = self.videoClip.get_frame(0)
        self.setImage(frameToQImage(frame).scaledToWidth(int(self.rect().width()), Qt.SmoothTransformation))
        self.fps=self.videoClip.fps
    def __copy__(self):
        videoCopy=Video(self.view,self.videoPath,self._audioTempFile)
        videoCopy.fps=self.fps
        videoCopy.videoClip=self.videoClip
        frame = self.videoClip.get_frame(0)
        videoCopy.setImage(frameToQImage(frame).scaledToWidth(int(self.rect().width()), Qt.SmoothTransformation))
        videoCopy.setVideoTimer()
        videoCopy.resize(self.width(),self.height())
        videoCopy.setPos(self.pos())
        videoCopy.setOpacity(self.opacity_)
        videoCopy.setZValue(self.zValue())
        videoCopy.setBorderColor(self.borderColor)
        videoCopy.setBorderThickness(self.borderThickness)
        videoCopy.setFillColor(self.fillColor)
        return videoCopy
    
    def setInteraction(self,a:bool):
        if not a:
            self.blocked=True
    def exitEditMode(self):
        if not self.isUnderMouse():
            self._inEditMode=False
    def hoverMoveEvent(self,event):
        
        pos=event.pos()
        self._scroll=False
        self._overPlayButton=False
        super().hoverMoveEvent(event)
        if self.isSelected() and self.sliderCursorRect.contains(pos) and self._inEditMode:
            self._scroll=True
            
            self.setFlag(QGraphicsItem.ItemIsMovable ,False)
            self._drag=False
            self.setCursor(Qt.PointingHandCursor)
            
        elif self.isSelected() and self.sliderBaseRect.contains(pos) and self._inEditMode:
            self.setFlag(QGraphicsItem.ItemIsMovable ,False)
            self._drag=False
            self.setCursor(Qt.ArrowCursor)
        if self.isSelected() and self.playRect.contains(pos) and self._inEditMode:
            self._overPlayButton=True
            self.setCursor(Qt.PointingHandCursor)
            self._drag=False
    def mouseMoveEvent(self, event:QMouseEvent):
        delta = event.pos() - self._sliderStartPos
        if self._scrolling:
            
            
            dx=delta.x()*cos(self.rotation()*pi/180)
            dy=delta.x()*sin(self.rotation()*pi/180)
            self.sliderRect.setWidth(min(self.width(),max(self.sliderRect.width()+ delta.x(),0)))
            self.sliderCursorRect.moveTopLeft(self.sliderCursorRect.topLeft()+QPointF(dx,dy))
            self.videoTimer.setTime(self.videoClip.duration*self.sliderRect.width()/self.width())
            
            
            self._sliderStartPos = event.pos()    
        super().mouseMoveEvent(event)
    def mousePressEvent(self, event: QMouseEvent):
        try:
            self._inEditMode=True
            self._sliderStartPos=event.pos()
            self._scrolling=False
            if self.view.activeVideo is None:
                self.view.activeVideo=self
                pygame.mixer.music.load(resource_path(self._audioTempFile))
            if self._scroll and self.view.activeVideo !=self:
                if not self.view.activeVideo.play: 
                    self.view.activeVideo.pause()
                pygame.mixer.music.load(resource_path(self._audioTempFile))
            if self._scroll:
                self._scrolling=True
                self.pause()
            if self._overPlayButton and self.view.activeVideo !=self:
                if not self.view.activeVideo.play: 
                    self.view.activeVideo.pause()
                self.view.activeVideo=self    
                pygame.mixer.music.load(resource_path(self._audioTempFile))
            if self._overPlayButton:
                
                if self.play:
                    self.StartPlay()   
                elif self.playing:
                    self.pause() 
                else:
                    self.unpause()  
                self.play=False
            
                
            super().mousePressEvent(event) 
           
        except Exception as e:
            # Catch any exception and display it
            ErrorHandler.show_error_message(str(e))    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._scrolling:
            
            self.unpause()
        self._scroll=False
        self._scrolling=False
    def drawContent(self, painter:QPainter):
        
        painter.setRenderHints(QPainter.SmoothPixmapTransform|QPainter.Antialiasing)
        if self.image:
            painter.drawImage(self.boundingRect(),self.image)
        if self.isSelected() :
            if not self.blocked:
                painter.setPen(self.selectionPen)
                painter.setBrush(Qt.NoBrush)  # No brush, no fill
                painter.drawRect(self.boundingRect())
                self.drawSelectionHandles(painter, self.boundingRect())
            if self._inEditMode:
                self.paintBorder(painter)
                self.paintDuration(painter)
                self.paintSlider(painter)
                self.paintPlayPause(painter)
            
        
    def paintDuration(self,painter:QPainter):
        painter.save()
        
        painter.setFont(self.durationFont)
        
        self.durationRect.moveBottomLeft(self.borderRect.bottomLeft()+QPointF(0,3))
        pen=QPen()
        
        pen.setColor(QColor(255,255,255,255))
        painter.setPen(pen)
        if self.videoTimer.started:
            
            painter.drawText(self.durationRect,Qt.AlignCenter,f"{formatDuration(int(self.videoTimer.getTime()))}/{formatDuration(int(self.videoTimer.maxValue))}")
        else:
            painter.drawText(self.durationRect,Qt.AlignCenter,f"{formatDuration(0)}/{formatDuration(int(self.videoTimer.maxValue))}")
        painter.restore()
    def paintPlayPause(self,painter:QPainter):
        painter.save()
        painter.setOpacity(0.5)
        self.playRect=QRectF(0,0,50,50)
        if self._overPlayButton:
            self.playRect=QRectF(0,0,60,60)
            painter.setOpacity(1)
        self.playRect.moveCenter(self.rect().center())
        if self.playing:
            self.playImage=QPixmap(resource_path("interfaceAssets/interfaceIcons/pause.png")).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation).toImage()
             
        else:
            self.playImage=QPixmap(resource_path("interfaceAssets/interfaceIcons/play.png")).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation).toImage()
        if self.play:
            self.playImage=QPixmap(resource_path("interfaceAssets/interfaceIcons/play.png")).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation).toImage()
        painter.drawImage(self.playRect,self.playImage)
        painter.restore()
    def paintBorder(self,painter:QPainter):
        painter.save()
        self.borderRect.setWidth(self.width())
        self.borderRect.moveBottomLeft(self.rect().bottomLeft())
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.borderColor)
        painter.drawRect(self.borderRect)
        painter.restore()
    def paintSlider(self,painter:QPainter):
        self.sliderBaseRect.setWidth(self.width())
        self.sliderBaseRect.moveBottomLeft(self.rect().bottomLeft()+self.sliderOffset)
        if not self.playing and not self._scrolling:
            self.sliderRect.setWidth(self.width()*self.videoTimer.getTime()/self.videoClip.duration)
        self.sliderRect.moveBottomLeft(self.rect().bottomLeft()+QPointF(0,(self.sliderRect.height()-self.sliderBaseRect.height())/2)+self.sliderOffset)
        

        self.sliderCursorRect.moveCenter(QPointF(self.sliderRect.right(),self.sliderRect.topRight().y()+self.sliderRect.height()/2))
        
        
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.sliderBaseColor)
        painter.drawRoundedRect(self.sliderBaseRect,5,5)

        painter.setBrush(self.sliderColor)
        painter.drawRoundedRect(self.sliderRect,5,5)
        cursorPen=QPen()
        cursorPen.setColor(QColor(255,255,255,255))
        cursorPen.setWidthF(2)
        
        if self._scroll:
            
            cursorPen.setWidthF(4)
        painter.setPen(cursorPen)
        painter.setBrush(self.sliderCursorColor)
        painter.drawEllipse(self.sliderCursorRect)

        painter.restore()   
    def pause(self):
        if self.videoClip and self.playing:
            self.videoTimer.pause()
            pygame.mixer.music.stop()
            self.playing=False
    def unpause(self):
        if self.videoClip and not self.playing:
            self.videoTimer.unpause()
            pygame.mixer.music.play() 
            pygame.mixer.music.set_pos(self.videoTimer.getTime())
            self.playing=True  
    def StartPlay(self):
        if self.videoClip:
            self.videoTimer.start()
            self.timer.start(1000 // int(self.fps))
            
            pygame.mixer.music.play()         

        
    def updateFrame(self):
        
        if self.playing and self.videoClip:
            
            self.update()
            if not self._scrolling:
                
                self.sliderRect.setWidth(min(self.rect().width(),max(self.videoTimer.getTime()*self.rect().width()/self.videoClip.duration,0)))
            
            
            if self.videoTimer.getTime() <= self.videoClip.duration:
                frame = self.videoClip.get_frame(self.videoTimer.getTime())
                
                self.setImage(frameToQImage(frame).scaledToWidth(int(self.rect().width()), Qt.SmoothTransformation))
            elif self.videoTimer.getTime() >=self.videoTimer.maxValue:
                self.videoTimer.reset()
                pygame.mixer.music.stop()
                pygame.mixer.music.load(resource_path(self._audioTempFile))
                pygame.mixer.music.play()
                pygame.mixer.music.set_pos(0)
class Thumbnail(Image):
    def __init__(self,view,path,name):
        super().__init__(view,path)
        self.textRect=QRectF(0,0,100,100)
        self.text=name
        self.TextFont = QFont("Arial", 20)  # Font name and size
        self.setLocked(True)
    def drawContent(self, painter: QPainter):
        if self.image:
            painter.drawImage(self.boundingRect(),self.image)
        self.textRect.moveCenter(self.boundingRect().center())
        self.textRect.setWidth(self.boundingRect().width())
        self.textRect.setHeight(self.boundingRect().height())
       
        painter.setFont(self.TextFont)
        painter.drawText(self.textRect,self.text)
        if self.isSelected() and not self.blocked:
            painter.setPen(self.selectionPen)
            painter.setBrush(Qt.NoBrush)  # No brush, no fill
            painter.drawRect(self.boundingRect())
            self.drawSelectionHandles(painter, self.boundingRect())
    def __copy__(self):
        copyThumbnail=super().__copy__()
        copyThumbnail.text=self.text 
        return copyThumbnail      

        

      
    
class WorkView(QGraphicsRectItem):
    def __init__(self,workspace):
        super().__init__()
        self.worspace=workspace
        self.image=None
        self.color=QColor(255,255,255,255)
        self.borderWidth=2
        self.borderColor=QColor(0,0,0,255)
        self.backgroundColor=QColor(255,255,255,255)
        self.setAcceptHoverEvents(False)
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
    def width(self):
        return self.rect().width() 
    def height(self):
        return self.rect().height()       
    def setWidth(self,width:float):
        rect=self.rect()
        self.setRect(rect.x(),rect.y(),width,rect.height())
    def setheight(self,height:float):
        rect=self.rect()
        self.setRect(rect.x(),rect.y(),rect.width(),height)
    def resizeToRatio(self,ratio):
        self.setWidth(self.width()*ratio)
        self.setheight(self.height()*ratio)
    def moveCenter(self,point):
        rect=QRectF(0,0,self.width(),self.height())
        rect.moveCenter(point)
        self.setRect(rect)
    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()
    def setBackgroundImage(self,image:QImage):
        self.image=image
    def paint(self,painter:QPainter,widget,option):
        super().paint(painter,widget,option)
        
        painter.save()
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        painter.restore()
        
        if self.image:
            painter.drawImage(self.boundingRect(), self.image)
        else:
            painter.fillRect(self.boundingRect(), self.backgroundColor)
        self.paintBorder(painter)
    def paintBorder(self,painter:QPainter):
        painter.save()
        pen=QPen()
        
        pen.setColor(self.borderColor)
        pen.setWidthF(self.borderWidth)
        painter.setPen(pen)
        
        painter.drawRect(self.boundingRect())   
        painter.restore() 
        



        
        

