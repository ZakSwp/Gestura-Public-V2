from PyQt5.QtWidgets import QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import mediapipe as mp
import cv2
import numpy as np


import time
from src.renderer import globalVariables as gv
import csv
import itertools

import copy
from src.renderer.model.keypoint_classifier.keypoint_classifier import KeyPointClassifier

previousTime = 0
# Mathematical operators
def distance(pt1, pt2):
    return np.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)
def distance3D(pt1, pt2):
    return np.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2 + (pt1[2] - pt2[2]) ** 2)
def cartesienToSpherical(coords, focalPoint):
    '''
    Converts cartesien coordinates into azimuth and elevation angles (phi and theta)
    :param coords: Cartesien coordinates to convert
    :param focalPoint: Origin of the cartesien coordinates system (for camera orbit set it to the current focal point)
    :return: phi for azimuth, theta for elevation. Should be in angles?  '''

    distance = distance3D(focalPoint, coords)
    phi = np.arctan(coords[2] / distance)
    if coords[0]:
        theta = np.arctan(coords[1] / coords[0])
    else:
        theta = 0
    return (phi, theta)
def isColinear(vector1, vector2):
    return not (np.cross(vector1, vector2))
def GetVector(pos1, pos2):
    return (pos1[0] - pos2[0], pos1[1] - pos2[1], pos1[2] - pos2[2])

import vtk

class CustomVTKOutputWindow(vtk.vtkOutputWindow):
    def DisplayText(self, text):
        with open("vtk_errors.log", "a") as log_file:
            log_file.write(text)

# Create an instance of the custom output window
output_window = CustomVTKOutputWindow()

# Set it as the default output window for VTK
vtk.vtkOutputWindow.SetInstance(output_window)
class vtkGesturaActor(vtk.vtkActor):
    def __init__(self, texturePath, status = False, modelPath="renderer/presentation assets/Presentation 3D Models/Porsche/GesturaReady/MeshSplit/Body.obj"):
        super().__init__()
        self.modelPath=modelPath
        self.texturePath=texturePath
        self.isStatic=status
        self.initialPos = self.GetPosition()
    def getPath(self):
        return self.modelPath
    def getTexture(self):
        return self.texturePath
    def resetTransform(self):
        self.SetPosition(self.initialPos)




class VirtualCamera(vtk.vtkCamera):
    def __init__(self):
        super().__init__()
        self.SetFocalPoint(0, 0, 0)
        self.SetFreezeFocalPoint(True)
        self.freezeRoll = True
        self.initialRoll = self.GetRoll()
        self.clippingPos = (0, 0, 5)
        self.SetPosition(2.9144, 2.1682, 3.4357)

        # boolean flags for smooth movement methods
        self.rotateSmoothly = False
        self.moveSmoothly = False
        self.targetPos = self.GetPosition()
        self.trajectory = None

        # trajectory settings for smooth movement methods
        self.stepCount = 50
        self.currentStep = 0
        self.speed = 5  # units per second
        self.posList = []

    # calculating right vector
    def GetRightVectorNormalized(self):
        '''
        Returns the normalized Right Vector of the virtual camera
        :return: 3D vector
        '''
        position = self.GetPosition()
        focalPoint = self.GetFocalPoint()

        viewDirection = [focalPoint[i] - position[i] for i in range(3)]
        vtk.vtkMath.Normalize(viewDirection)

        upVector = self.GetViewUp()
        upVectorNormalized = [upVector[i] for i in range(3)]
        vtk.vtkMath.Normalize(upVectorNormalized)

        rightVector = [0, 0, 0]
        vtk.vtkMath.Cross(viewDirection, upVectorNormalized, rightVector)
        return rightVector

    def GetUpVectorNormalized(self):
        '''
        Returns the normalized Up Vector of the virtual camera
        :return: 3D vector
        '''
        upVector = self.GetViewUp()
        upVectorNormalized = [upVector[i] for i in range(3)]
        vtk.vtkMath.Normalize(upVectorNormalized)
        return upVectorNormalized

    def lookAt(self, pt):
        self.SetFocalPoint(pt)
        return

    def SetFreezeRoll(self, state):
        self.freezeRoll = state
        return


    def smoothMoveForward(self):
        if not self.moveSmoothly:
            return
        if(self.currentStep < self.stepCount):
            self.SetPosition(self.trajectory[self.currentStep])
            self.currentStep+=1
        else:
            self.moveSmoothly = False
            self.currentStep=0
    def moveForward(self, step):
        forwardVector = list(self.GetDirectionOfProjection())
        vtk.vtkMath.Normalize(forwardVector)
        newPosition = [self.GetPosition()[i] + step*forwardVector[i] for i in range(3)]
        self.SetPosition(newPosition)
        return
    def getTrajectory(self, forwardDistance):
        forwardVector = list(self.GetDirectionOfProjection())
        vtk.vtkMath.Normalize(forwardVector)
        newPosition = [self.GetPosition()[i] + forwardDistance*forwardVector[i] for i in range(3)]
        grad = np.linspace(0,1,self.stepCount)
        trajectory = [(1-t)*self.GetPosition() + t*newPosition for t in grad]
        self.moveSmoothly = True
        return trajectory


def create3DModel(objFilename, textureFilename=None, position=(0, 0, 0),actorScale=[1, 1, 1]):
       
    reader = vtk.vtkOBJReader()
    reader.SetFileName(objFilename)
   
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtkGesturaActor(textureFilename, False, objFilename)
    actor.SetMapper(mapper)
    if textureFilename:
        texture = vtk.vtkTexture()
        texture_reader = vtk.vtkPNGReader()
        texture_reader.SetFileName(textureFilename)
 
        texture.SetInputConnection(texture_reader.GetOutputPort())
        actor.SetTexture(texture)
    actor.SetPosition(position[0], position[1], position[2])
    actor.SetScale(actorScale[0], actorScale[1], actorScale[2])
    
    return actor
# Inherit model class
class ModelView(QWidget):
    def __init__(self, parent=None, screenshotMode = False):
        super().__init__(parent=parent)
        self.setWindowTitle("VTK with Hand Gesture Control")
        self.setGeometry(100, 100, 800, 600)
        self.use_brect = True
        self.screenshotMode = screenshotMode
        # Set up the layout for VTK and camera feed
        layout = QVBoxLayout()  # a layout class that lines up widgets vertically
        self.vtk_widget = QVTKRenderWindowInteractor(self)  # QVTKRenderWindowInteractor is a powerful&simple vtk widget class
        self.vtk_widget.keyPressEvent=self.keyPressEvent
        self.vtk_widget.keyReleaseEvent=self.keyReleaseEvent
        layout.addWidget(self.vtk_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)  # sets the layout as the one just created

        # VTK initialization
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

        self.ren = vtk.vtkRenderer()
     
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        # Add environment to the scene
        self.add_environment(self.ren)
        

        # Add two 3D models with different positions

        
        self.actorList = []
        

        camera = VirtualCamera()
        camera.SetPosition(2.9144, 2.1682, 3.4357)
        camera.SetFreezeRoll(True)
        self.ren.SetActiveCamera(camera)
        self.load_classifier_labels()
        # Interactor initialization
        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        interactor.Initialize()
        self.zoomFactor=0
        # Assign the classifier to `self`
        self.keypoint_classifier = KeyPointClassifier()  # This makes it accessible as an instance attribute

        # Initialize Mediapipe Hand model
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.7,
                                            min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
    
        # Start the camera feed
            # Start a timer to update every 10 ms
        self.loopCounter = 0
        self.maxFrame = 1  # maximum length of cursorPositionHistory, corresponds to the number of frames across which the movement will be averaged

    
        # Initialize the 2D disc actor for the model center
        self.modelRadius = 100
        self.disc_actor = self.create_2d_disc_actor(self.modelRadius, [1, 0, 0])  # Red disc for model center
        self.ren.AddActor(self.disc_actor)
        self.hoveredActor = None
        self.updateHover = True

        # Initialize the 2D disc actor for the cursor (index finger)
        self.cursorPosition = (0, 0)
        self.oldCursorPosition = (0, 0)
        self.cursorRadius = 10
        self.cursor_actor = self.create_2d_disc_actor(self.cursorRadius, [0, 1, 0])  # Green disc for the cursor
        self.ren.AddActor(self.cursor_actor)
        self.cursorPositionHistory = []  # Cursor position history for smooth cursor movement

        # Normalized cursor positions for orbit logic
        self.normalizedCursorPosition = (0.5, 0.5)
        self.oldNormalizedCursorPosition = (0.5, 0.5)

        # Model selection flag
        self.selectedActor = None

        # Button states initialization
        self.pinched = False
        self.actorCameraDistance = 1
        self.right_hand_sign_id = -1
        self.left_hand_sign_id = -1
        self.newHandToHandDistance = None
        self.handToHandDistance = None
        self.rightHandOrigin = (0,0)
        self.leftHandOrigin = (0,0)
        self.leftHandPresent = False
        self.rightHandPresent = False

            
    def startCv(self):
        self.cap = cv2.VideoCapture(0)
        self.timer = self.startTimer(10)
        self.screenshotMode=False
    def stopCv(self):
        self.screenshotMode=True

        self.cap.release()
        cv2.destroyAllWindows()
    def keyPressEvent(self, event):
        # Ignore key press events
        event.ignore()

    def keyReleaseEvent(self, event):
        # Ignore key release events
        event.ignore()
    def load_classifier_labels(self):
        # Load keypoint classifier labels
        with open('renderer/model/keypoint_classifier/keypoint.csv',
                  encoding='utf-8-sig') as f:
            self.keypoint_classifier_labels = [row[0] for row in csv.reader(f)]



    def timerEvent(self, event):
        if self.screenshotMode:
            self.vtk_widget.GetRenderWindow().Render()
            return
        global previousTime
        self.lockCameraRoll()
        ret, frame = self.cap.read()
        if not ret:
            return
        if self.updateHover:
            self.hoveredActor = self.getHoveredActor()


        # Flip the frame horizontally for a mirrored view
        frame = cv2.flip(frame, 1)
        frameRgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frameRgb)
        self.rightHandPresent = False
        self.leftHandPresent = False


        # Set the frame as writable to draw on it later
        frame.flags.writeable = True
        if results.multi_hand_landmarks:
            # Loop through each hand detected
            self.loopCounter += 1
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):

                # Get image dimensions
                h, w, _ = frame.shape
                tipList = self.GetTipList(hand_landmarks)
                posList, missingFingers = self.GetPosList(tipList, h, w)
                self.drawTips(posList, missingFingers, frame)

                # Calculate the bounding rectangle around the hand
                brect = self.calc_bounding_rect(frame, hand_landmarks)
                # Calculate landmark positions
                landmark_list = self.calc_landmark_list(frame, hand_landmarks)
                pre_processed_landmark_list = self.pre_process_landmark(landmark_list)
                hand_sign_id = self.keypoint_classifier(pre_processed_landmark_list)

                if handedness.classification[0].label == 'Right':
                    self.rightHandPresent = True
                    self.right_hand_sign_id = hand_sign_id
                    self.rightHandOrigin = (hand_landmarks.landmark[0].x,hand_landmarks.landmark[0].y)
                if handedness.classification[0].label == 'Left':
                    self.leftHandPresent = True
                    self.left_hand_sign_id = hand_sign_id
                    self.leftHandOrigin = (hand_landmarks.landmark[0].x,hand_landmarks.landmark[0].y)
                # Convert Mediapipe coordinates to VTK window coordinates
                self.cursorPosition, self.normalizedCursorPosition = self.landmarkToVtkWindowCoordinates(posList[5])
                self.appendCurrentCursorPosition()
                if self.loopCounter == self.maxFrame:
                    self.cursorPosition = self.averageCursorPos(self.cursorPositionHistory)
                    # Update the position of the cursor (index finger)
                    self.update_cursor_position(self.cursorPosition)
                    targetCursorPosition = self.cursorPosition
                    targetNormalizedCursorPosition = self.normalizedCursorPosition
                    self.processClick(posList, targetNormalizedCursorPosition, targetCursorPosition)
                    self.oldCursorPosition = targetCursorPosition
                    self.oldNormalizedCursorPosition = targetNormalizedCursorPosition
                    self.clearCursorPositionHistory()
                    self.loopCounter = 0

                # Draw hand landmarks on the frame
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                if not self.leftHandPresent:
                    self.right_hand_sign_id = -1
                if not self.rightHandPresent:
                    self.left_hand_sign_id = -1

        # Update disc size based on zoom level
        self.update_disc_size_based_on_zoom()

        # Render the VTK window
        self.vtk_widget.GetRenderWindow().Render()

        # Framerate calculation and display
        currentTime = time.time()
        fps = 1 / (currentTime - previousTime)
        previousTime = currentTime
        cv2.putText(frame, "FPS=" + str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (0, 200, 0), 3)

        # Show the camera feed with hand landmarks
        cv2.imshow("Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            self.killTimer(self.timer)
            self.cap.release()
            cv2.destroyAllWindows()





    def calc_bounding_rect(self, image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_array = np.empty((0, 2), int)

        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)

            landmark_point = [np.array((landmark_x, landmark_y))]

            landmark_array = np.append(landmark_array, landmark_point, axis=0)

        x, y, w, h = cv2.boundingRect(landmark_array)
        return [x, y, x + w, y + h]
    def calc_landmark_list(self, image, landmarks):
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_point = []

        # Keypoint
        for _, landmark in enumerate(landmarks.landmark):
            landmark_x = min(int(landmark.x * image_width), image_width - 1)
            landmark_y = min(int(landmark.y * image_height), image_height - 1)
            # landmark_z = landmark.z

            landmark_point.append([landmark_x, landmark_y])

        return landmark_point
    def pre_process_landmark(self, landmark_list):
        temp_landmark_list = copy.deepcopy(landmark_list)
        # Convert to relative coordinates
        base_x, base_y = 0, 0
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:
                base_x, base_y = landmark_point[0], landmark_point[1]

            temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
            temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

        # Convert to a one-dimensional list
        temp_landmark_list = list(
            itertools.chain.from_iterable(temp_landmark_list))

        # Normalization
        max_value = max(list(map(abs, temp_landmark_list)))

        def normalize_(n):
            return n / max_value

        temp_landmark_list = list(map(normalize_, temp_landmark_list))

        return temp_landmark_list
    def draw_info_text(self, image, brect, handedness, hand_sign_text, finger_gesture_text = ""):
        cv2.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22),
                      (0, 0, 0), -1)

        info_text = handedness.classification[0].label[0:]
        if hand_sign_text != "":
            info_text = info_text + ':' + hand_sign_text
        cv2.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        if finger_gesture_text != "":
            cv2.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2,
                        cv2.LINE_AA)

        return image
    def draw_info(self, image, mode, number):

        mode_string = ['Logging Key Point', 'Logging Point History']
        if 1 <= mode <= 2:
            cv2.putText(image, "MODE:" + mode_string[mode - 1], (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                        cv2.LINE_AA)
        if 0 <= number <= 9:
            cv2.putText(image, "NUM:" + str(number), (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                        cv2.LINE_AA)
        return image
    def draw_landmarks(self, image, landmark_point):
        if len(landmark_point) > 0:
            # Thumb
            cv2.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                     (255, 255, 255), 2)

            # Index finger
            cv2.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                     (255, 255, 255), 2)

            # Middle finger
            cv2.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                     (255, 255, 255), 2)

            # Ring finger
            cv2.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                     (255, 255, 255), 2)

            # Little finger
            cv2.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                     (255, 255, 255), 2)

            # Palm
            cv2.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                     (255, 255, 255), 2)
            cv2.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                     (0, 0, 0), 6)
            cv2.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                     (255, 255, 255), 2)

        # Key Points
        for index, landmark in enumerate(landmark_point):
            if index == 0:  # 手首1
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 1:  # 手首2
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 2:  # 親指：付け根
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 3:  # 親指：第1関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 4:  # 親指：指先
                cv2.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 5:  # 人差指：付け根
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 6:  # 人差指：第2関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 7:  # 人差指：第1関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 8:  # 人差指：指先
                cv2.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 9:  # 中指：付け根
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 10:  # 中指：第2関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 11:  # 中指：第1関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 12:  # 中指：指先
                cv2.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 13:  # 薬指：付け根
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 14:  # 薬指：第2関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 15:  # 薬指：第1関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 16:  # 薬指：指先
                cv2.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
            if index == 17:  # 小指：付け根
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 18:  # 小指：第2関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 19:  # 小指：第1関節
                cv2.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
            if index == 20:  # 小指：指先
                cv2.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                           -1)
                cv2.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

        return image
    def draw_bounding_rect(self, use_brect, image, brect):
        if use_brect:
            # Outer rectangle
            cv2.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                          (0, 0, 0), 1)

        return image
    def processClick(self, posList, targetNormalizedCursorPosition, targetCursorPos):

        actor = self.hoveredActor
        if(self.left_hand_sign_id == 2 and self.right_hand_sign_id == 2):

            self.newHandToHandDistance = distance(self.rightHandOrigin,self.leftHandOrigin)
            if self.handToHandDistance == None:
                self.handToHandDistance = self.newHandToHandDistance
                pass
            self.zoomFactor = (self.newHandToHandDistance-self.handToHandDistance)*200
            self.handToHandDistance = self.newHandToHandDistance
            print("Zoom factor = {}".format(self.zoomFactor), end='\r')
            if vtk.vtkMath.Distance2BetweenPoints(self.ren.GetActiveCamera().GetPosition(), self.ren.GetActiveCamera().GetFocalPoint())> 40 or self.zoomFactor <0:
                self.ren.GetActiveCamera().moveForward(self.zoomFactor)
        else:
            self.handToHandDistance = None
        if (self.left_hand_sign_id == 0 and self.right_hand_sign_id == 0):
            for actors in self.actorList:
                actors[0].resetTransform()

        if(self.right_hand_sign_id==3):
            pass
            # self.updateHover = False
            # if actor:
            #     self.selectedActor = actor
            #     self.selectActor(self.selectedActor)
            #     self.rotateActorGimball(self.selectedActor, self.oldCursorPosition, self.cursorPosition)
            #     print("EXECUTED GIMBALL ROTATE")
            # self.update_2d_disc_position(self.cursorPosition)
        if (self.left_hand_sign_id == 1):
            self.rotateCameraOrbit(self.oldNormalizedCursorPosition, targetNormalizedCursorPosition)

            pass
        if (self.right_hand_sign_id == 1):
            # Pinch detected - move the selected model
            self.updateHover = False
            if actor and not self.pinched:
                self.selectedActor = actor
                self.selectActor(self.selectedActor)
                self.pinched = True
                self.moveActorAcrossPlane(self.selectedActor, self.oldCursorPosition, targetCursorPos, updateDistance=True)
            elif actor and self.pinched:
                self.moveActorAcrossPlane(self.selectedActor, self.oldCursorPosition, targetCursorPos, updateDistance=False)
            self.update_2d_disc_position(self.cursorPosition)
        elif self.pinched:
            self.pinched = False
            # No pinch detected - deselect the model
            if self.selectedActor:
                self.selectActor(self.selectedActor, "Up")
            self.updateHover = True
        else:
            self.updateHover = True
        return





    # Virtual Camera Movement Methods
    def lockCameraRoll(self):
        '''
        Locks camera roll and prevents the camera from zooming out too far
        :return:
        '''
        camera = self.ren.GetActiveCamera()
        p = camera.GetPosition()
        newPos = [1, 1, 1]
        for i in range(3):
            if p[i] >= 10:
                newPos[i] = p[i] - p[i] / abs(p[i]) * 2
        if camera.freezeRoll:
            camera.SetRoll(camera.initialRoll)
        distance = vtk.vtkMath.Distance2BetweenPoints(camera.GetPosition(), camera.GetFocalPoint())
        if (distance > 2000):
            camera.SetPosition(newPos)
        return



    def rotateCameraOrbit(self, currentCursorPos, targetCursorPos):
        '''
        :param currentCursorPos: Normalized current cursor position [0,1]
        :param targetCursorPos: Normalized target cursor position [0,1]
        '''
        camera = self.ren.GetActiveCamera()
        roll = camera.GetRoll()
        targetCursorPos = (targetCursorPos[0] - currentCursorPos[0], targetCursorPos[1] - currentCursorPos[1])
        targetAlt = targetCursorPos[1] * 180
        targetAzm = 360 - targetCursorPos[0] * 360
        (currentAlt, currentAzm) = cartesienToSpherical(camera.GetPosition(), camera.GetFocalPoint())
        camera.Elevation(targetAlt + currentAlt)
        camera.Azimuth(targetAzm + currentAzm)
        if camera.freezeRoll:
            camera.SetRoll(roll)
        return
    def rotateActorGimball(self, actor, currentCursorPos, targetCursorPos):
        '''
        :param currentCursorPos: Normalized current cursor position [0,1]
        :param targetCursorPos: Normalized target cursor position [0,1]
        '''
        targetCursorPos = (targetCursorPos[0] - currentCursorPos[0], targetCursorPos[1] - currentCursorPos[1])
        targetAlt = targetCursorPos[1] * 180
        targetAzm = 360 - targetCursorPos[0] * 360
        actor.RotateX(targetAzm)
        return



    # Attribute update methods
    def appendCurrentCursorPosition(self):
        try:
            self.cursorPositionHistory.append(self.cursorPosition)
            return 1
        except:
            print("CAN NOT UPDATE CURSOR POSITION")
            return 0
    def clearCursorPositionHistory(self):
        self.cursorPositionHistory = []
        return
    # Computer vision  methods
    def GetTipList(self, hand_landmarks):
        '''
        Returns fingertip landmark list with an additional wrist landmark.
        :param hand_landmarks: what the name says
        :return: list of landmarks (could be described as a list of nodes each containing an index and x,y,z normalized coordinates)
        '''
        tipList = []
        for i in range(1, 6):
            tipList.append(hand_landmarks.landmark[i * 4])
        tipList.append(hand_landmarks.landmark[0])
        return (tipList)
    def GetPosList(self, tipList, h, w):
        '''
        Returns fingertip positions list posList in webcam coordinates space
        :param tipList: list of finger tip landmarks
        :param h: cv camera window height
        :param w: cv camera window width
        :return: fingertip positions list plus number of misssing fingers
        '''
        # extracts finger tip positions list and checks for missing fingers
        posList = []
        missingFingers = 0
        for i in range(len(tipList)):
            posList.append((int(tipList[i].x * w), int(tipList[i].y * h)))  # check for isInFrameRange
            if not self.isInFrameRange(posList[i], w, h):
                missingFingers += 1
        return (posList, missingFingers)
    def isInFrameRange(self, position, w, h):
        if position is None: return False
        return ((position[0] in range(w)) and (position[1] in range(h)))
    def drawTips(self, posList, missingFingers, frame):
        for i in range(len(posList)):
            cv2.circle(frame, posList[i], 10, gv.fingerColorList[i], -1)
        if (missingFingers != 0):
            cv2.putText(frame, "MISSING {} FINGERS".format((missingFingers)), (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 2)
            missingFingers = 0
        return
    def landmarkToVtkWindowCoordinates(self, coordinates):
        '''
        Converts landmark nodes (the colored ones) coordinates from cv camera coordinates space to vtkwindow coordinates space
        :param coordinates: Coordinates in cv camera coordinates space
        :return: vtkwindow coordinates and normalized coordinates in cv camera coordinates space
        '''
        window_width, window_height = self.vtk_widget.GetRenderWindow().GetSize()
        cvWidth, cvHeight = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        vtk_x = coordinates[0] * (window_width / cvWidth)
        vtk_y = (1 - coordinates[1] / cvHeight) * window_height
        normalizedX = coordinates[0] / cvWidth
        normalizedY = coordinates[1] / cvHeight
        return (int(vtk_x), int(vtk_y)), (normalizedX, normalizedY)
    # Virtual cursor methods
    def update_disc_size_based_on_zoom(self):
        camera = self.ren.GetActiveCamera()
        zoom_factor = camera.GetDistance()

        self.modelRadius = max(10, 400000 / zoom_factor)
        disk_source = self.disc_actor.GetMapper().GetInputConnection(0, 0).GetProducer()
        disk_source.SetInnerRadius(self.modelRadius - 2)
        disk_source.SetOuterRadius(self.modelRadius)
        disk_source.Modified()
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
        self.cursor_actor.SetPosition(position_2d[0], position_2d[1])
    def moveActorAcrossPlane(self, selectedActor, vtkWindowOgCoords, vtkWindowTargetCoords, updateDistance=True):

        # get camera and actor parameters
        camera = self.ren.GetActiveCamera()
        cameraPosition = camera.GetPosition()
        actorPosition = selectedActor.GetPosition()

        # Get landmark 0's translation vector (calculate how much it moved on the screen)
        sizeList = list(self.vtk_widget.GetRenderWindow().GetSize())
        translationVector = [(vtkWindowTargetCoords[i] - vtkWindowOgCoords[i]) / sizeList[i] for i in
                             range(2)]  # the distance is normalized

        # calculate right and up vectors
        upVectorNormalized = camera.GetUpVectorNormalized()
        rightVector = camera.GetRightVectorNormalized()

        # calculate actor movement vector
        translationRight = [translationVector[0] * rightVector[i] for i in range(3)]
        translationUp = [translationVector[1] * upVectorNormalized[i] for i in range(3)]
        newActorPos = [0, 0, 0]

        if updateDistance:
            distance = vtk.vtkMath.Distance2BetweenPoints(actorPosition, cameraPosition)
            self.actorCameraDistance = distance

        # update new actor position vector, scaled to world scale
        for i in range(3):
            newActorPos[i] = actorPosition[i] + int(self.actorCameraDistance*0.1) * (
                    translationRight[i] + translationUp[i])
        selectedActor.SetPosition(newActorPos)
        return

    def project_3d_to_2d(self, point_3d):  #FIXME:
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToWorld()
        coordinate.SetValue(point_3d)
        screen_coordinates = coordinate.GetComputedDisplayValue(self.ren)
        return screen_coordinates
    
    # Scene generation methods
    def addActorToRendrer(self,actor):
        vtkRenderer=self.ren
        vtkRenderer.AddActor(actor)
        vtkRenderer.SetBackground(0.5,0.5,0.5)
        vtkRenderer.GetRenderWindow().Render()

    def clearRendrer(self):
        for i in range(len(self.actorList)):
            self.ren.RemoveActor(self.actorList[i][0])

        self.actorList.clear()   

    def appendto3DBuffer(self,objFilename, textureFilename=None):
        model = self.create3DModel(objFilename, textureFilename)
        self.actorList.append(model)

    def RemoveFrom3DBuffer(self, model):
        self.actorList.remove(model)

    def add_environment(self, vtk_renderer, resolutionX=1000, resolutionY=1000):
        # Add a base plane (floor)
        plane = vtk.vtkPlaneSource()
        plane.SetOrigin(-1000, 0, -1000)  # Set the origin of the plane
        plane.SetPoint1(1000, 0, -1000)  # Set the first corner of the plane
        plane.SetPoint2(-1000, 0, 1000)  # Set the second corner of the plane
        plane.SetXResolution(resolutionX)  # Set the resolution along X-axis
        plane.SetYResolution(resolutionY)  # Set the resolution along Y-axis
        plane_mapper = vtk.vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane.GetOutputPort())
        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(plane_mapper)
        # plane_actor.GetProperty().SetColor(0.5, 0.5, 0.5)  # Set the color of the plane
        plane_actor.GetProperty().SetOpacity(0.1)  # Set the opacity of the plane
        plane_actor.GetProperty().EdgeVisibilityOn()
        plane_actor.GetProperty().SetEdgeColor(1, 1, 1)

        self.ren.AddActor(plane_actor)
        # Create axes
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(10, 10, 10)
        axes.SetConeRadius(0.0)
        axes.GetXAxisCaptionActor2D().SetWidth(0.02)
        axes.GetYAxisCaptionActor2D().SetWidth(0.02)
        axes.GetZAxisCaptionActor2D().SetWidth(0.02)
        vtk_renderer.AddActor(axes)

    def initializeSkybox(self, textureFilePath):
        # texture = vtk.vtkTexture()
        # reader = vtk.vtkJPEGReader()  # Replace with appropriate reader for your HDRI format (e.g., vtkTIFFReader)
        # reader.SetFileName(textureFilePath)
        # texture.SetInputConnection(reader.GetOutputPort())
        # texture.MipmapOn()
        # texture.InterpolateOn()
        #
        # # Create a skybox and set the HDRI texture
        # skybox = vtk.vtkSkybox()
        # skybox.SetProjection(2)
        # skybox.SetTexture(texture)
        # # Add the skybox to the renderer
        # self.ren.AddActor(skybox)
        self.ren.SetBackground(0.3, 0.3, 0.3)

        return

    def getHoveredActor(self, radius=100):
        '''
        In this context actor represents a tuple of actor and actorID
        :param radius:
        :return:
        '''
        actors = self.actorList
        cursorPos = self.cursor_actor.GetPosition()
        distanceList = []
        for actor in actors:
            actorPosition = actor[0].GetPosition()
            projectedActorPosition = self.project_3d_to_2d(actorPosition)
            distanceList.append(distance(projectedActorPosition, cursorPos))
        try:
            min_dist = min(distanceList)
        except:
            print("Empty actorList")
            return
        selectedActor = None

        for actor in actors:
            actorPosition = actor[0].GetPosition()  # Corrected this line
            projectedActorPosition = self.project_3d_to_2d(actorPosition)
            if distance(projectedActorPosition, cursorPos) < radius + self.cursorRadius and distance(projectedActorPosition, cursorPos) == min_dist:
                selectedActor = actor[0]
                break  # Break after selecting the closest model
        if selectedActor:
            selectedActor.GetProperty().SetEdgeVisibility(1)
            return selectedActor
        else:
            for actor in self.actorList:
                actor[0].GetProperty().SetEdgeVisibility(0)
            return None
    def selectActor(self, actor, mode = "down"):
        if mode == "up":
            actor.GetProperty().SetEdgeVisibility(0)
        else:
            actor.GetProperty().SetEdgeVisibility(1)
            actor.GetProperty().SetEdgeColor(0.53, 0.81, 0.98)
            actor.GetProperty().SetLineWidth(2.0)

    # Miscellaneous

    def averageCursorPos(self, posList):
        '''
        Returns the average of posList coordinates to be used as a target position.
        :param posList: history of cursor positions for the past n frames
        :return: averaged cursor position across n frames
        '''
        X = []
        Y = []
        for i in range(len(posList)):
            X.append(posList[i][0])
            Y.append(posList[i][1])
        x = sum(X) / len(posList)
        y = sum(Y) / len(posList)
        return ((x, y))





