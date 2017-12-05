from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QVector3D
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QDockWidget
from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
from PyQt5.Qt3DInput import QInputAspect

from cadnano.gui.palette import getColorObj

from .virtualhelixitem import Sphere


class SceneModifier(QObject):
    def __init__(self, root_entity):
        super(SceneModifier, self).__init__()
        self.m_root_entity = root_entity


class SimDockWidget(QDockWidget):
    """
    SimDockWidget is the SimView's equivalent of CustomQGraphicsView.
    It gets added to the Dock area directly by DocumentWindow, and maintains
    a QWidget container for the Qt3DWindow.

    Attributes:
        root_entity (QEntity): Description
    """
    name = 'sim'

    def __init__(self, flags):
        """Instantiates PyQt3D objects for the Sim view.
        Sets up the 2D layout, and then the 3D window.
        """
        super(SimDockWidget, self).__init__(flags)

    def setup(self, root_entity):
        self.root_entity = root_entity
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.view = view = Qt3DWindow()
        self.container = QWidget.createWindowContainer(view)
        self.camera_entity = view.camera()
        self.cam_controller = QOrbitCameraController(root_entity)
        self.modifier = SceneModifier(root_entity)
        self.aspect = QInputAspect()
        self._initUI()
        self._init3D()

    def _initUI(self):
        """Creates and arranges the GUI inputs. Derived from basicshapes-py."""
        widget = self.widget
        container = self.container
        hLayout = QHBoxLayout(widget)
        vLayout = QVBoxLayout()
        vLayout.setAlignment(Qt.AlignTop)
        hLayout.addWidget(container, 1)
        hLayout.addLayout(vLayout)
        hLayout.setContentsMargins(0, 1, 0, 1)
        vLayout.setContentsMargins(0, 0, 0, 0)
    # end def

    def _init3D(self):
        """Configure the camera and register the view aspect and root entity."""
        framegraph = self.view.defaultFrameGraph()
        framegraph.setClearColor(getColorObj('#ffffff'))
        cam_entity = self.camera_entity
        cam_entity.lens().setPerspectiveProjection(15.0, 16.0 / 9.0, 0.1, 1000.0)
        # cam_entity.lens().setOrthographicProjection(-20, 20, -20, 20, 0.1, 1000.0)

        cam_entity.setUpVector(QVector3D(0.0, 1.0, 0.0))  # default
        cam_entity.setPosition(QVector3D(0.0, 0.0, 100.0))
        # cam_entity.setViewCenter(QVector3D(0.0, 0.0, 0.0))
        cam_entity.setViewCenter(QVector3D(0.0, 0.0, -6.97))
        self.cam_controller.setCamera(cam_entity)
        self.view.registerAspect(self.aspect)
        self.view.setRootEntity(self.root_entity)

        Sphere(1, 0, 0, '#0000cc', self.root_entity)
        Sphere(2, 0, 0, '#0000cc', self.root_entity)
        Sphere(3, 0, 0, '#0000cc', self.root_entity)
        Sphere(0, 1, 0, '#007200', self.root_entity)
        Sphere(0, 2, 0, '#007200', self.root_entity)
        Sphere(0, 3, 0, '#007200', self.root_entity)
        Sphere(0, 0, 1, '#cc0000', self.root_entity)
        Sphere(0, 0, 2, '#cc0000', self.root_entity)
        Sphere(0, 0, 3, '#cc0000', self.root_entity)
    # end def
