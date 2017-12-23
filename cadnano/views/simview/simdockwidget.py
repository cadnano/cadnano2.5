from PyQt5.QtCore import QObject, Qt
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QVector3D
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QDockWidget
from PyQt5.QtWidgets import QLabel, QSpinBox
from PyQt5.QtWidgets import QCheckBox, QSlider
from PyQt5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
from PyQt5.Qt3DInput import QInputAspect
from PyQt5.Qt3DRender import QDirectionalLight

from cadnano.gui.palette import getColorObj

from .customshapes import Line
# from .customshapes import TriStrip
from .customshapes import Sphere
# from .customshapes import LineSegment
# from .customshapes import TetrahedronMesh


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
        self.shapes = []
        self.spinboxes = []
        self._initUI()
        self._init3D()
        self._initControls()

    @pyqtSlot(int)
    def setPosVertexSize(self, value):
        for s in self.shapes:
            s.setPosVertexSize(value)

    @pyqtSlot(int)
    def setPosByteOffset(self, value):
        for s in self.shapes:
            s.setPosByteOffset(value)

    @pyqtSlot(int)
    def setPosByteStride(self, value):
        for s in self.shapes:
            s.setPosByteStride(value)

    @pyqtSlot(int)
    def setPosCount(self, value):
        for s in self.shapes:
            s.setPosCount(value)

    @pyqtSlot(int)
    def setColVertexSize(self, value):
        for s in self.shapes:
            s.setColVertexSize(value)

    @pyqtSlot(int)
    def setColByteOffset(self, value):
        for s in self.shapes:
            s.setColByteOffset(value)

    @pyqtSlot(int)
    def setColByteStride(self, value):
        for s in self.shapes:
            s.setColByteStride(value)

    @pyqtSlot(int)
    def setColCount(self, value):
        for s in self.shapes:
            s.setColCount(value)

    # @pyqtSlot(int)
    # def setByteStride(self, value):
    #     self.posbytestride_spinbox.setValue(value)
    #     self.colbytestride_spinbox.setValue(value)

    @pyqtSlot(int)
    def setCount(self, count):
        self.poscount_spinbox.setValue(count)
        self.colcount_spinbox.setValue(count)
    # end def

    @pyqtSlot(int)
    def setStride(self, stride):
        for s in self.shapes:
            s.setByteStride(stride)
    # end def

    @pyqtSlot(int)
    def enableLight(self, enabled):
        self.m_lightEntity.setParent(self.root_entity if enabled else None)

    @pyqtSlot(int)
    def changeLightX(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setX(2*(value/100.-1)+1)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLightY(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setY(2*(value/100.-1)+1)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLightZ(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setZ(2*(value/100.-1)+1)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def setStep(self, size):
        self.posvertexsize_spinbox.setSingleStep(size)
        self.posbyteoffset_spinbox.setSingleStep(size)
        # self.posbytestride_spinbox.setSingleStep(size)
        self.colvertexsize_spinbox.setSingleStep(size)
        self.colbyteoffset_spinbox.setSingleStep(size)
        # self.colbytestride_spinbox.setSingleStep(size)
        self.poscount_spinbox.setSingleStep(size)
        self.colcount_spinbox.setSingleStep(size)
        self.stride_spinbox.setSingleStep(size)

    # end def

    def _initControls(self):
        v_layout = self._v_layout
        v_layout.setContentsMargins(2, 10, 10, 2)

        # Positions
        self.posvertexsize_spinbox = posvertexsize_spinbox = QSpinBox()
        self.posbyteoffset_spinbox = posbyteoffset_spinbox = QSpinBox()
        self.poscount_spinbox = poscount_spinbox = QSpinBox()
        for sb in [posvertexsize_spinbox, posbyteoffset_spinbox, poscount_spinbox]:
            sb.setRange(0, 1000)
            sb.setSingleStep(1)
        posvertexsize_label = QLabel("Pos VertexSize")
        posbyteoffset_label = QLabel("Pos ByteOffset")
        poscount_label = QLabel("Pos Count")

        v_layout.addWidget(posvertexsize_label)
        v_layout.addWidget(posvertexsize_spinbox)
        v_layout.addWidget(posbyteoffset_label)
        v_layout.addWidget(posbyteoffset_spinbox)
        v_layout.addWidget(poscount_label)
        v_layout.addWidget(poscount_spinbox)
        posvertexsize_spinbox.valueChanged.connect(self.setPosVertexSize)
        posbyteoffset_spinbox.valueChanged.connect(self.setPosByteOffset)
        poscount_spinbox.valueChanged.connect(self.setColCount)

        s = self.shapes[0]
        posvertexsize_spinbox.setValue(s._pos_attr.vertexSize())
        posbyteoffset_spinbox.setValue(s._pos_attr.byteOffset())
        poscount_spinbox.setValue(s._pos_attr.count())

        # Colors
        self.colvertexsize_spinbox = colvertexsize_spinbox = QSpinBox()
        self.colbyteoffset_spinbox = colbyteoffset_spinbox = QSpinBox()
        self.colcount_spinbox = colcount_spinbox = QSpinBox()
        for sb in [colvertexsize_spinbox, colbyteoffset_spinbox, colcount_spinbox]:
            sb.setRange(0, 1000)
            sb.setSingleStep(1)
        colvertexsize_label = QLabel("Col VertexSize")
        colbyteoffset_label = QLabel("Col ByteOffset")
        colcount_label = QLabel("Col Count")
        v_layout.addWidget(colvertexsize_label)
        v_layout.addWidget(colvertexsize_spinbox)
        v_layout.addWidget(colbyteoffset_label)
        v_layout.addWidget(colbyteoffset_spinbox)
        v_layout.addWidget(colcount_label)
        v_layout.addWidget(colcount_spinbox)
        colvertexsize_spinbox.valueChanged.connect(self.setColVertexSize)
        colbyteoffset_spinbox.valueChanged.connect(self.setColByteOffset)
        colcount_spinbox.valueChanged.connect(self.setColCount)

        colvertexsize_spinbox.setValue(s._col_attr.vertexSize())
        colbyteoffset_spinbox.setValue(s._col_attr.byteOffset())
        colcount_spinbox.setValue(s._col_attr.count())

        stride_label = QLabel("Stride")
        self.stride_spinbox = stride_spinbox = QSpinBox()
        v_layout.addWidget(stride_label)
        v_layout.addWidget(stride_spinbox)
        stride_spinbox.valueChanged.connect(self.setStride)

        # floatsize_label = QLabel("Float size")
        # self.floatsize_spinbox = floatsize_spinbox = QSpinBox()
        # v_layout.addWidget(floatsize_label)
        # v_layout.addWidget(floatsize_spinbox)
        # floatsize_spinbox.valueChanged.connect(self.setFloatsize)
        for sb in [stride_spinbox]:
            sb.setRange(0, 1000)
            sb.setSingleStep(1)
        stride_spinbox.setValue(s._col_attr.byteStride())

        count_label = QLabel("Count")
        count_spinbox = QSpinBox()
        count_spinbox.setRange(1, 1000)
        v_layout.addWidget(count_label)
        v_layout.addWidget(count_spinbox)
        count_spinbox.valueChanged.connect(self.setCount)

        stepsize_label = QLabel("Step size")
        stepsize_spinbox = QSpinBox()
        stepsize_spinbox.setRange(1, 1000)
        v_layout.addWidget(stepsize_label)
        v_layout.addWidget(stepsize_spinbox)
        stepsize_spinbox.valueChanged.connect(self.setStep)

        lightCB = QCheckBox(checked=True, text="Light")
        lightSliderX = QSlider(Qt.Horizontal)
        lightSliderY = QSlider(Qt.Horizontal)
        lightSliderZ = QSlider(Qt.Horizontal)
        v_layout.addWidget(lightCB)
        v_layout.addWidget(lightSliderX)
        v_layout.addWidget(lightSliderY)
        v_layout.addWidget(lightSliderZ)
        lightCB.stateChanged.connect(self.enableLight)
        lightSliderX.valueChanged.connect(self.changeLightX)
        lightSliderY.valueChanged.connect(self.changeLightY)
        lightSliderZ.valueChanged.connect(self.changeLightZ)
    # end def

    def _initUI(self):
        """Creates and arranges the GUI inputs. Derived from basicshapes-py."""
        widget = self.widget
        container = self.container
        self._h_layout = h_layout = QHBoxLayout(widget)
        self._v_layout = v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignTop)
        h_layout.addWidget(container, 1)
        h_layout.addLayout(v_layout)
        h_layout.setContentsMargins(0, 1, 0, 1)
        v_layout.setContentsMargins(0, 0, 0, 0)
    # end def

    def _init3D(self):
        """Configure the camera and register the view aspect and root entity."""
        framegraph = self.view.defaultFrameGraph()
        framegraph.setClearColor(getColorObj('#ffffff'))
        cam_entity = self.camera_entity
        cam_entity.lens().setPerspectiveProjection(15.0, 16.0 / 9.0, 0.1, 1000.0)
        # cam_entity.lens().setOrthographicProjection(-20, 20, -20, 20, 0.1, 1000.0)
        # cam_entity.setUpVector(QVector3D(0.0, 1.0, 0.0))  # default
        cam_entity.setPosition(QVector3D(0.0, 0.0, 30.0))
        # cam_entity.setViewCenter(QVector3D(0.0, 0.0, 0.0))
        cam_entity.setViewCenter(QVector3D(0.0, 0.0, -6.97))
        self.cam_controller.setLinearSpeed(100.0)
        self.cam_controller.setLookSpeed(360.0)
        self.cam_controller.setCamera(cam_entity)
        self.view.registerAspect(self.aspect)
        self.view.setRootEntity(self.root_entity)

        line = Line(self.root_entity)
        self.shapes.append(line)
        # ts = TriStrip(self.root_entity)
        # self.shapes.append(ts)

        # Sphere(0, 0, 0, '#cccccc', self.root_entity, radius=0.1)
        # Sphere(2, 0, 0, '#0000cc', self.root_entity, radius=0.2)
        # Sphere(0, 2, 0, '#007200', self.root_entity, radius=0.2)
        # Sphere(0, 0, 2, '#cc0000', self.root_entity, radius=0.2)

        Sphere(2, 2, 2, '#cccc00', self.root_entity, radius=0.1)

        # LineSegment(self.root_entity)
        # TetrahedronMesh(0, 0, 0, self.root_entity)
        # c = Cube(0, 0, 0, 1, 1, 1, '#cc00cc', self.root_entity)

        # Sphere(1.0, 0.0, -1.0, '#00ff00', self.root_entity)
        # Sphere(0.0, 1.0, 0.0, '#0000ff', self.root_entity)
        # Sphere(0.0, 0.0, 1.0, '#ffffff', self.root_entity)

        # Sphere(1, 0, 0, '#0000cc', self.root_entity)
        # Sphere(2, 0, 0, '#0000cc', self.root_entity)
        # Sphere(3, 0, 0, '#0000cc', self.root_entity)
        # Sphere(0, 1, 0, '#007200', self.root_entity)
        # Sphere(0, 2, 0, '#007200', self.root_entity)
        # Sphere(0, 3, 0, '#007200', self.root_entity)
        # Sphere(0, 0, 1, '#cc0000', self.root_entity)
        # Sphere(0, 0, 2, '#cc0000', self.root_entity)
        # Sphere(0, 0, 3, '#cc0000', self.root_entity)

        # Light 1
        self.light = light = QDirectionalLight()
        light.setColor(getColorObj('#ffffff'))
        light.setIntensity(1.0)
        light.setWorldDirection(QVector3D(0, 1, -1))
        self.root_entity.addComponent(light)


    # end def
