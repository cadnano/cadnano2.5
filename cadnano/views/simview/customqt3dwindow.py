# from PyQt5.QtCore import QObject
from PyQt5.QtGui import QVector3D

from PyQt5.Qt3DCore import QTransform
from PyQt5.Qt3DExtras import Qt3DWindow
# from PyQt5.Qt3DExtras import QOrbitCameraController
from PyQt5.Qt3DInput import QAction, QActionInput
from PyQt5.Qt3DInput import QAnalogAxisInput, QAxis
# from PyQt5.Qt3DInput import QInputAspect
from PyQt5.Qt3DInput import QLogicalDevice
from PyQt5.Qt3DInput import QMouseDevice, QMouseEvent
from PyQt5.Qt3DLogic import QFrameAction

from cadnano import util
from cadnano.gui.palette import getColorObj
from .customlines import Line


# class SceneModifier(QObject):
#     def __init__(self, root_entity):
#         super(SceneModifier, self).__init__()
#         self.m_root_entity = root_entity


LOOK_SPEED = 360
MIN_SCALE = 0.25
MAX_SCALE = 10
SCALE_RATE = 0.05


class CustomQt3DWindow(Qt3DWindow):
    def __init__(self, root_entity, screen=None):
        super(CustomQt3DWindow, self).__init__(screen)
        self.root_entity = root_entity
        self.setRootEntity(self.root_entity)

        cam = self.camera()
        # cam_entity.lens().setPerspectiveProjection(15.0, 16.0 / 9.0, 0.1, 1000.0)
        # cam_entity.lens().setOrthographicProjection(-20, 20, -20, 20, 0.1, 1000.0)
        cam.lens().setOrthographicProjection(-16.0, 16.0, -9.0, 9.0, 0.0, 1000.0)
        cam.setPosition(QVector3D(0.0, 0.0, 50.0))
        cam.setViewCenter(QVector3D(0.0, 0.0, 0.0))

        # self.cam_controller.setLinearSpeed(100.0)
        # self.cam_controller.setLookSpeed(360.0)
        # self.cam_controller.setCamera(cam)

        # self.cam_controller = QOrbitCameraController(root_entity)
        # self.modifier = SceneModifier(root_entity)
        # self.aspect = QInputAspect()
        # self.registerAspect(self.aspect)
        self.defaultFrameGraph().setClearColor(getColorObj('#f6f6f6'))

        self.trans = QTransform()
        root_entity.addComponent(self.trans)
        # self.trans.setScale(4)

        self._initMouseControls()
        self._initShapes()
    # end def

    def wheelEvent(self, event):
        # scale_factor = event.angleDelta().y()
        # self.trans.setScale()
        # print("wheee", event.angleDelta(), event.pixelDelta())
        delta = event.pixelDelta().y()
        scale_factor = 1 + delta * SCALE_RATE
        old_scale = self.trans.scale()
        new_scale = util.clamp(old_scale * scale_factor, MIN_SCALE, MAX_SCALE)
        self.trans.setScale(new_scale)
    # end def

    def onFrame(self, dt):
        cam = self.camera()
        cam.panAboutViewCenter((self.rx_axis.value() * LOOK_SPEED) * dt, cam.upVector())
        cam.tiltAboutViewCenter((self.ry_axis.value() * LOOK_SPEED) * dt)

        # if self.left_mouse_button_action.isActive():
        #     cam = self.camera()
        #     cam.panAboutViewCenter((self.rx_axis.value() * LOOK_SPEED) * dt, cam.upVector())
        #     cam.tiltAboutViewCenter((self.ry_axis.value() * LOOK_SPEED) * dt)
        # elif self.right_mouse_button_action.isActive():
        #     print("right mouse", dt, self.rx_axis.value(), self.ry_axis.value())
    # end def

    def _initMouseControls(self):
        self.mouse = m_d = QMouseDevice(self.root_entity)
        # print(m_d.axisCount(), m_d.axisNames(), m_d.buttonCount(), m_d.buttonNames())

        # Left button
        self.left_mouse_button_action = lmba = QAction()
        self.left_mouse_button_input = lmbi = QActionInput()
        lmbi.setButtons([QMouseEvent.LeftButton])
        lmbi.setSourceDevice(m_d)
        lmba.addInput(lmbi)

        # Right button
        self.right_mouse_button_action = rmba = QAction()
        self.right_mouse_button_input = rmbi = QActionInput()
        rmbi.setButtons([QMouseEvent.RightButton])
        rmbi.setSourceDevice(m_d)
        rmba.addInput(rmbi)

        # Mouse X
        self.rx_axis = rx_a = QAxis()
        self.mouse_rx_input = mrxi = QAnalogAxisInput()
        mrxi.setAxis(QMouseDevice.X)
        mrxi.setSourceDevice(m_d)
        rx_a.addInput(mrxi)

        # Mouse Y
        self.ry_axis = ry_a = QAxis()
        self.mouse_ry_input = mryi = QAnalogAxisInput()
        mryi.setAxis(QMouseDevice.Y)
        mryi.setSourceDevice(m_d)
        ry_a.addInput(mryi)

        l_d = QLogicalDevice()
        l_d.addAction(lmba)
        l_d.addAction(rmba)
        l_d.addAxis(rx_a)
        l_d.addAxis(ry_a)
        fa = QFrameAction()
        fa.triggered.connect(self.onFrame)
        self.root_entity.addComponent(l_d)
        self.root_entity.addComponent(fa)
    # end def

    def _initShapes(self):
        Line((0, 0, 0), (1, 0, 0), '#cc0000', self.root_entity)
        Line((0, 0, 0), (0, 1, 0), '#007200', self.root_entity)
        Line((0, 0, 0), (0, 0, 1), '#0000cc', self.root_entity)
        # Line((0, 0, 0), (1, 1, 1), '#cc00cc', self.root_entity)
        # StrandLines(self.root_entity)

        # Light 1
        # self.light = light = QDirectionalLight()
        # light.setColor(getColorObj('#ffffff'))
        # light.setIntensity(1.0)
        # light.setWorldDirection(QVector3D(0, 1, -1))
        # self.root_entity.addComponent(light)
    # end def
# end class
