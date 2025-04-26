from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
environ['TF_ENABLE_ONEDNN_OPTS'] = '0' #Tensorflow and pygame startup prompts removal
from GUI import *
import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow,QToolButton,QWidgetAction,QColorDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from util import *
from app import *
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(" ")
     
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.setGeometry(0, 0, 800, 600)
        self.slideScrollZone=self.ui.slideScrollZone
        self.workSpace = self.ui.workSpace
        self.ui.commentButton.clicked.connect(self.showHideComment)
        self.ui.textEdit.hide()
        self.addNewSlide()
        self.presenter=None
        self.align_group=None
        self.toolbar=None
        self.ui.presentButton.clicked.connect(self.present)
        self.ui.insertSlideButton.clicked.connect(self.addNewSlide)
        self.ui.insertImageButton.clicked.connect(self.workSpace.insertImage)
        self.ui.insertVideoButton.clicked.connect(self.workSpace.insertVideo)
        self.ui.insertTextButton.clicked.connect(self.workSpace.insertText)
    
        #comboBoxs connection
        self.ui.toolButton.setPopupMode(QToolButton.InstantPopup)  # Show the dropdown instantly

        # Create a QMenu to act as the dropdown list
        self.dropdown_menu = QMenu(self)
        self.insertRectButton = QPushButton("Rectangle",self)
        self.insertRoundedRectButton = QPushButton("Rounded rectangle",self)
        self.insertCircleButton = QPushButton("Circle",self)
        # Adding buttons as actions into the QMenu
        insertRectAction = QWidgetAction(self)
        insertRoundedRectAction = QWidgetAction(self)
        insertCircleAction = QWidgetAction(self)
        insertRectAction.setDefaultWidget(self.insertRectButton)
        insertRoundedRectAction.setDefaultWidget(self.insertRoundedRectButton)
        insertCircleAction.setDefaultWidget(self.insertCircleButton)

        self.dropdown_menu.addAction(insertRectAction)
        self.dropdown_menu.addAction(insertRoundedRectAction)
        self.dropdown_menu.addAction(insertCircleAction)
       
        self.insertRectButton.clicked.connect(self.workSpace.insertRect)
        self.insertRoundedRectButton.clicked.connect(self.workSpace.insertRoundedRect)
        self.insertCircleButton.clicked.connect(self.workSpace.insertCircle)
        
        # Assign the QMenu to the tool button
        self.ui.toolButton.setMenu(self.dropdown_menu)
        #self.ui.shapesComboBox.currentIndexChanged.connect(self.onShapeComboBoxChanged)

        # set the text font using the fontComboBox
        self.ui.fontComboBox.currentFontChanged.connect(self.changeFont)
        # set the text font size using the spinBox
        self.ui.fontSizeSpinBox.valueChanged.connect(self.onFontSizeSpinBoxValueChange)
        # set the text style
        self.ui.boldButton.clicked.connect(self.setTextBold)
        self.ui.italicButton.clicked.connect(self.setTextItalic)
        self.ui.underlineButton.clicked.connect(self.setTextUnderline)
        self.ui.strikeButton.clicked.connect(self.setTextStrikethrough)
        #set text color
        self.ui.textColorButton.clicked.connect(self.setTextColor)
        #Dont forget to update the copy methode of the text to make change to the slide view 
        # add 3d model
        self.ui.insertModelButton.clicked.connect(self.workSpace.insert3DModel)
        #set shape fillButton
        self.ui.fillShapeButton.clicked.connect(self.setShapeFillColor)
        #set drawings border color 
        self.ui.borderColorButton.clicked.connect(self.setDrawingsBorderColor)
        # set drawings border thickness
        self.ui.borderThicknessSpinBox.valueChanged.connect(self.onBorderThicknessSpinBoxValueChange)
        # set present from current button
        self.ui.presentFromCurrentButton.clicked.connect(self.presentFromCurrent)
        # set align buttons
        self.ui.alignCenterButton.clicked.connect(lambda:self.alignText("center"))
        self.ui.alignLeftButton.clicked.connect(lambda:self.alignText("left"))
        self.ui.alignRightButton.clicked.connect(lambda:self.alignText("right"))
       
    def alignText(self,pos):
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                
                item.setHtml(f"""
                <div style="text-align: {pos};">
                    <p>{item.toPlainText()}</p>
                </div>
                """)
                self.workSpace.updateVersionBuffer() 
                self.workSpace.update()
    def onBorderThicknessSpinBoxValueChange(self,value):
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,(Shape,Text)):
                item.setBorderThickness(value)
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
           
    def setShapeFillColor(self):
        # Open color dialog and get the  selected color
        color = QColorDialog.getColor()

        # If a valid color is selected, apply it to the label's background
        if color.isValid():
            self.ui.shapeBackgroundColorFrame.setStyleSheet(f"background-color: rgb({color.red()},{color.green()},{color.blue()});")
            buffer=self.workSpace.scene().selectedItems()
            for item in buffer:
                if  isinstance(item,(Shape,Text)) and not isinstance(item,(Video,Image)) :
                    item.setFillColor(color)
                    self.workSpace.update()
                    self.workSpace.updateVersionBuffer()
    def setDrawingsBorderColor(self):
        # Open color dialog and get the selected color
        color = QColorDialog.getColor()

        # If a valid color is selected, apply it to the label's background
        if color.isValid():
            self.ui.borderColorFrame.setStyleSheet(f"background-color: rgb({color.red()},{color.green()},{color.blue()});")
            buffer=self.workSpace.scene().selectedItems()
            for item in buffer:
                if  isinstance(item,(Shape,Text) ) :
                    item.setBorderColor(color)
                    self.workSpace.update()
                    self.workSpace.updateVersionBuffer()     
    def setTextColor(self):
       
        # Open color dialog and get the selected color
        color = QColorDialog.getColor()

        # If a valid color is selected, apply it to the label's background
        if color.isValid():
            self.ui.textColorFrame.setStyleSheet(f"background-color: rgb({color.red()},{color.green()},{color.blue()});")
            buffer=self.workSpace.scene().selectedItems()
            for item in buffer:
                if isinstance(item,Text):
                    item.setDefaultTextColor(color)
            self.workSpace.update()
            self.workSpace.updateVersionBuffer() 
    def setTextBold(self):
       
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setBold(self.ui.boldButton.isChecked() )
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()   
    def setTextItalic(self):
       
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setItalic(self.ui.italicButton.isChecked() )
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
    def setTextUnderline(self):
       
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setUnderline(self.ui.underlineButton.isChecked() )
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
    def setTextStrikethrough(self):
       
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setStrikethrough(self.ui.strikeButton.isChecked() )
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
    def onFontSizeSpinBoxValueChange(self, value):       
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setFontSize(value)
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
    def changeFont(self, font):
        buffer=self.workSpace.scene().selectedItems()
        for item in buffer:
            if isinstance(item,Text):
                item.setFont(font)
        self.workSpace.updateVersionBuffer() 
        self.workSpace.update()
    def showHideComment(self):
        if self.ui.textEdit.isVisible():
            self.ui.textEdit.hide()
        else:
            self.ui.textEdit.show() 
    def present(self):
        self.presenter=Presenter(self)
        
        self.presenter.present()
        
        if self.workSpace.activeVideo is not None:
            if not self.workSpace.activeVideo.play:
                self.workSpace.activeVideo.pause()
        self.presenter.showFullScreen()
        self.showMinimized()
    
    def presentFromCurrent(self):
        self.presenter=Presenter(self)
        self.presenter.currentPageIndex=self.slideScrollZone.buffer().index(self.slideScrollZone.selectedSlide())
        self.presenter.present()
        if self.workSpace.activeVideo is not None:
            if not self.workSpace.activeVideo.play:
                self.workSpace.activeVideo.pause()
        self.presenter.showFullScreen()
        self.showMinimized()   
    def addNewSlide(self):
        slide=Slide(self)
        
        if self.slideScrollZone.selectedSlide():
            self.slideScrollZone.selectedSlide().setDefaultBorder()
        slide.setSelected()
        
        self.slideScrollZone.activeSlide=slide
        self.slideScrollZone.addSlide(slide)
    def openFile(self):
        print("File opened")
    def saveFile(self):
        print("saved")
    def newFile(self):
        print("new file")
    
        

        

    
    
       
    def closeEvent(self,event):
        reply = QMessageBox.question(
            self, 'Quit Gestura ?', 'Are you sure you want to quit?', 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.workSpace.quit()
            if self.presenter is not None:
                if self.presenter.isVisible():
                    self.presenter.destroy(True,True)
            event.accept()
        else:
            event.ignore()
class SplashScreen(QSplashScreen):
    def __init__(self, images, interval, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images = images
        self.interval = interval
        self.current_image_index = 0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_image)
        self.update_timer.start(self.interval)  # Interval in milliseconds
        self.update_image()  # Set initial image

    def update_image(self):
        pixmap = self.images[self.current_image_index]
        scaled_pixmap = pixmap.scaledToWidth(1200, Qt.SmoothTransformation)  # Scale the pixmap to 400px width
        self.setPixmap(scaled_pixmap)
        if self.current_image_index+1<len(self.images):
            self.current_image_index +=1
def runApp():
    image_files=loadAnimationImages(resource_path("interfaceAssets/startAnimation"))
    pygame.mixer.init()
    window = MainWindow()
    # Create the splash screen with the scaled pixmap
    splash = SplashScreen(image_files, 50)  # 1000 ms interval for updating images
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
    splash.setAttribute(Qt.WA_TranslucentBackground)
    splash.show()
    def show_main_window():
        splash.close()
        window.showMaximized()
    
    QTimer.singleShot(3000, show_main_window)
 
    
    
    
    app.exec_()
   
        



runApp()
sys.exit()