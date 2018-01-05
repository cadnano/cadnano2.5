from PyQt5.QtGui import QVector3D
from PyQt5.Qt3DCore import QTransform
from PyQt5.Qt3DExtras import Qt3DWindow
from PyQt5.Qt3DInput import QAction, QActionInput
from PyQt5.Qt3DInput import QAnalogAxisInput, QAxis
from PyQt5.Qt3DInput import QLogicalDevice
from PyQt5.Qt3DInput import QMouseDevice, QMouseEvent
from PyQt5.Qt3DLogic import QFrameAction

from cadnano import util
from cadnano.gui.palette import getColorObj
from cadnano.views import styles

LOOK_SPEED = 360
MIN_SCALE = 0.2
MAX_SCALE = 10
SCALE_RATE = 0.005
NEAR_PLANE = 0.0
FAR_PLANE = 1000.0


class CustomQt3DWindow(Qt3DWindow):
    def __init__(self, root_entity, screen=None):
        super(CustomQt3DWindow, self).__init__(screen)
        self.root_entity = root_entity
        self.setRootEntity(self.root_entity)

        self.defaultFrameGraph().setClearColor(getColorObj(styles.VIEW_BG_COLOR))
        self.camera().setPosition(QVector3D(0.0, 0.0, 100.0))
        self.camera().setViewCenter(QVector3D(0.0, 0.0, 0.0))

        self.mouse = QMouseDevice(root_entity)
        self._initMouseControls()

        frame_action = QFrameAction()
        frame_action.triggered.connect(self.onFrame)
        root_entity.addComponent(frame_action)

        self.trans = QTransform()
        root_entity.addComponent(self.trans)
    # end def

    def _initMouseControls(self):
        # Left button
        self.left_mouse_button_action = lmba = QAction()
        self.left_mouse_button_input = lmbi = QActionInput()
        lmbi.setButtons([QMouseEvent.LeftButton])
        lmbi.setSourceDevice(self.mouse)
        lmba.addInput(lmbi)
        # Right button
        self.right_mouse_button_action = rmba = QAction()
        self.right_mouse_button_input = rmbi = QActionInput()
        rmbi.setButtons([QMouseEvent.RightButton])
        rmbi.setSourceDevice(self.mouse)
        rmba.addInput(rmbi)
        # Mouse X
        self.rx_axis = rx_a = QAxis()
        self.mouse_rx_input = mrxi = QAnalogAxisInput()
        mrxi.setAxis(QMouseDevice.X)
        mrxi.setSourceDevice(self.mouse)
        rx_a.addInput(mrxi)
        # Mouse Y
        self.ry_axis = ry_a = QAxis()
        self.mouse_ry_input = mryi = QAnalogAxisInput()
        mryi.setAxis(QMouseDevice.Y)
        mryi.setSourceDevice(self.mouse)
        ry_a.addInput(mryi)
        # Device
        l_d = QLogicalDevice()
        l_d.addAction(lmba)
        l_d.addAction(rmba)
        l_d.addAxis(rx_a)
        l_d.addAxis(ry_a)
        self.root_entity.addComponent(l_d)
    # end def

    ### SLOTS ###
    def onFrame(self, dt):
        if self.left_mouse_button_action.isActive() or self.right_mouse_button_action.isActive():
            cam = self.camera()
            cam.panAboutViewCenter((self.rx_axis.value() * LOOK_SPEED) * dt, cam.upVector())
            cam.tiltAboutViewCenter((self.ry_axis.value() * LOOK_SPEED) * dt)
    # end def

    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        aspect_ratio = w/h
        # https://stackoverflow.com/questions/39048746/
        if w > h:
            top = 16.0
            bottom = -top
            right = top*aspect_ratio
            left = -right
        else:
            right = 16.0
            left = -right
            top = right/aspect_ratio
            bottom = -top
        self.camera().lens().setOrthographicProjection(left, right, bottom, top, NEAR_PLANE, FAR_PLANE)
    # end def

    def wheelEvent(self, event):
        delta = event.pixelDelta().y()
        scale_factor = 1 + delta * SCALE_RATE
        old_scale = self.trans.scale()
        new_scale = util.clamp(old_scale * scale_factor, MIN_SCALE, MAX_SCALE)
        self.trans.setScale(new_scale)
    # end def
# end class
