import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene, \
    QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QFont, QKeyEvent, QPaintEvent, QPainter
from PyQt5.QtCore import Qt
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np
import globalVariables as gv


def distance(pt1, pt2):
    return np.sqrt((pt1[0] - pt2[0])** 2 + (pt1[1]-pt2[1])** 2)


class ModelView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("VTK with Hand Gesture Control")
        self.setGeometry(100, 100, 800, 600)

        # Set up the layout for VTK and camera feed
        layout = QVBoxLayout() #a layout class that lines up widgets vertically
        self.vtk_widget = QVTKRenderWindowInteractor(self) #QVTKRenderWindowInteractor is a powerful&simple vtk widget class

        layout.addWidget(self.vtk_widget)
        self.setLayout(layout) #sets the layout as the one just created
        # creat a buffer of actors ,each actor represents a model
        self.buffer = []
        # VTK initialization
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackgroundAlpha(0.1)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        # Add environment to the scene
        self.add_environment(self.ren)
        # Add two 3D models with different positions
        self.actor1=self.createOBJActor("TestingHeartGestura.obj")
        self.ren.AddActor(self.actor1)
        # self.actor1 = self.add_3d_model(self.ren, "TestingHeartGestura.obj", "MissingFingers.png", position=(0, 0, 0),textureMode=1)
        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        interactor.Initialize()
        self.ren.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.ren.GetActiveCamera().SetFreezeFocalPoint(True)



        # Initialize rotation parameters
        self.rotation_direction = None
        self.rotation_speed = 2  # Amount of rotation per frame
        self.continue_rotation = False

        self.timer = self.startTimer(10)  # Start a timer to update every 10 ms

        # Initialize the 2D disc actor for the model center
        self.modelRadius = 100
        self.disc_actor = self.create_2d_disc_actor(self.modelRadius, [1, 0, 0])  # Red disc for model center
        self.ren.AddActor(self.disc_actor)

        # Initialize the 2D disc actor for the cursor (index finger)
        self.cursorPosition = (0, 0)
        self.lastCursorPosition = (0, 0)
        self.cursorRadius = 10
        self.cursor_actor = self.create_2d_disc_actor(self.cursorRadius, [0, 1, 0])  # Green disc for the cursor
        self.ren.AddActor(self.cursor_actor)


        # Variable to track the selected model
        self.model_selected = None


    def timerEvent(self, event):

        # Update disc size based on the zoom level
        self.update_disc_size_based_on_zoom()

        # Render the VTK window
        self.vtk_widget.GetRenderWindow().Render()
        print("UPDATED VTK WINDOW RENDERER")



    def update_disc_size_based_on_zoom(self):
        camera = self.ren.GetActiveCamera()
        zoom_factor = camera.GetDistance()

        self.modelRadius = max(10, 400000 / zoom_factor)
        disk_source = self.disc_actor.GetMapper().GetInputConnection(0, 0).GetProducer()
        disk_source.SetInnerRadius(self.modelRadius - 2)
        disk_source.SetOuterRadius(self.modelRadius)
        disk_source.Modified()

    def move_selected_model(self, vtk_window_coords_index):
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToDisplay()
        coordinate.SetValue(vtk_window_coords_index[0], vtk_window_coords_index[1], 0)
        world_coords = coordinate.GetComputedWorldValue(self.ren)
        self.model_selected.SetPosition(world_coords)

    def create_2d_disc_actor(self, radius, color):
        disk_source = vtk.vtkDiskSource()
        disk_source.SetInnerRadius(radius - 2)
        disk_source.SetOuterRadius(radius)
        disk_source.SetCircumferentialResolution(100)
        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputConnection(disk_source.GetOutputPort())
        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        return actor

    def update_2d_disc_position(self, position_2d):
        self.disc_actor.SetPosition(position_2d[0], position_2d[1])

    def update_cursor_position(self, position_2d):
        print("Latest Cursor Position: {}".format(position_2d))
        self.cursor_actor.SetPosition(position_2d[0], position_2d[1])


    def project_3d_to_2d(self, point_3d): #FIXME:
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToWorld()
        coordinate.SetValue(point_3d)
        screen_coordinates = coordinate.GetComputedDisplayValue(self.ren)
        return screen_coordinates

    def createOBJActor(self, objFilename, pos = (0,0,0)):
        reader = vtk.vtkOBJReader()
        reader.SetFileName(objFilename)
        reader.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(pos[0], pos[1], pos[2])
        actor.SetScale(40.0, 40.0, 40.0)

        return actor



    def add_3d_model(self, vtk_renderer, obj_filename, texture_filename, position=(0, 0, 0), textureMode=0):
        reader = vtk.vtkOBJReader()
        reader.SetFileName(obj_filename)
        reader.Update()


        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        if(textureMode):
            texture = vtk.vtkTexture()
            texture_reader = vtk.vtkPNGReader()
            texture_reader.SetFileName(texture_filename)
            texture.SetInputConnection(texture_reader.GetOutputPort())
            actor.SetTexture(texture)
        actor.SetPosition(position[0], position[1], position[2])
        # mapper.Update()
        vtk_renderer.AddActor(actor)
        vtk_renderer.SetBackground(0.5, 0.5, 0.4)
        vtk_renderer.ResetCamera()
        vtk_renderer.GetRenderWindow().Render()
        print("ACTOR ADDED")
        return actor

    def select_model(self, actor, selected):
        if selected:
            actor.GetProperty().SetEdgeVisibility(1)
            actor.GetProperty().SetEdgeColor(0.53, 0.81, 0.98)
            actor.GetProperty().SetLineWidth(2.0)
        else:
            actor.GetProperty().SetEdgeVisibility(0)

    def select_closest_model(self, cursor_position):
        return self.actor1


    def add_environment(self, vtk_renderer):
        # Add a base plane (floor)
        plane = vtk.vtkPlaneSource()
        plane.SetOrigin(-1000, -1000, 0)  # Set the origin of the plane
        plane.SetPoint1(1000, -1000, 0)  # Set the first corner of the plane
        plane.SetPoint2(-1000, 1000, 0)  # Set the second corner of the plane
        plane.SetXResolution(100)  # Set the resolution along X-axis
        plane.SetYResolution(100)  # Set the resolution along Y-axis

        plane_mapper = vtk.vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane.GetOutputPort())

        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(plane_mapper)
        plane_actor.GetProperty().SetColor(0.5, 0.5, 0.5)  # Set the color of the plane
        plane_actor.GetProperty().SetOpacity(0.5)  # Set the opacity of the plane

        self.ren.AddActor(plane_actor)

        # Create axes
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(1000, 1000, 1000)
        axes.GetXAxisCaptionActor2D().SetWidth(0.02)
        axes.GetYAxisCaptionActor2D().SetWidth(0.02)
        axes.GetZAxisCaptionActor2D().SetWidth(0.02)
        vtk_renderer.AddActor(axes)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestura version ALPHA")
        self.setGeometry(100, 100, 800, 600)
        self.view = QGraphicsView(self)
        self._scene = QGraphicsScene()
        self.view.setScene(self._scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        # Enable drag-and-drop
        self.view.setAcceptDrops(True)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setGeometry(50, 50, 1000, 800)
        self.vtk_widget = ModelView(self)
        self.vtk_widget.setGeometry(100, 100, 800, 600)  # Set position and size of the VTKWidget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())