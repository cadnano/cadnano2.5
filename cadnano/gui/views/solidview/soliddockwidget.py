from PyQt5.QtCore import pyqtSlot, QObject, Qt  # QSize
from PyQt5.QtGui import QQuaternion, QVector3D
from PyQt5.QtWidgets import (QCheckBox, QSlider,  # QCommandLinkButton
                             QHBoxLayout, QVBoxLayout, QWidget, QDockWidget)
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import (Qt3DWindow, QConeMesh, QCuboidMesh,
                              QCylinderMesh, QOrbitCameraController,
                              QPhongMaterial, QPlaneMesh, QSphereMesh,
                              # QGoochMaterial, QPhongAlphaMaterial,
                              QTorusMesh)
from PyQt5.Qt3DInput import QInputAspect
from PyQt5.Qt3DRender import QDirectionalLight

from cadnano.gui.palette import getColorObj


class SceneModifier(QObject):
    def __init__(self, root_entity):
        super(SceneModifier, self).__init__()
        self.m_root_entity = root_entity

        # Light 1
        self.m_lightEntity = QEntity(self.m_root_entity)
        self.light = light = QDirectionalLight()
        light.setColor(getColorObj('#ffffff'))
        light.setIntensity(1.0)
        light.setWorldDirection(QVector3D(0, 1, -1))
        self.m_lightEntity.addComponent(light)

        # Light 2
        self.m_light2Entity = QEntity(self.m_root_entity)
        self.light2 = light2 = QDirectionalLight()
        light2.setColor(getColorObj('#ffffff'))
        light2.setIntensity(1.0)
        light2.setWorldDirection(QVector3D(0, 0, 1))
        self.m_light2Entity.addComponent(light2)

        # # Cylinder
        # cylinder = QCylinderMesh()
        # cylinder.setRadius(1)
        # cylinder.setLength(5)
        # cylinder.setRings(100)
        # cylinder.setSlices(20)
        # cylinderTransform = QTransform()
        # cylinderTransform.setScale(1.0)
        # cylinderTransform.setRotation(QQuaternion.fromAxisAndAngle(
        #                               QVector3D(1.0, 0.0, 0.0), 90.0))
        # cylinderTransform.setTranslation(QVector3D(-5.0, 4.0, -1.5))
        # # cylinderMaterial = QGoochMaterial()
        # cylinderMaterial = QPhongMaterial()
        # cylinderMaterial.setDiffuse(getColorObj('#cc0000'))
        # # cylinderMaterial.setAlpha(1)
        # self.m_cylinderEntity = QEntity(self.m_root_entity)
        # self.m_cylinderEntity.addComponent(cylinder)
        # self.m_cylinderEntity.addComponent(cylinderMaterial)
        # self.m_cylinderEntity.addComponent(cylinderTransform)

        # # Cone
        # cone = QConeMesh()
        # cone.setTopRadius(0.5)
        # cone.setBottomRadius(1)
        # cone.setLength(3)
        # cone.setRings(50)
        # cone.setSlices(20)
        # coneTransform = QTransform()
        # coneTransform.setScale(1.0)
        # coneTransform.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(1.0, 1.0, -0.5), 45.0))
        # coneTransform.setTranslation(QVector3D(0.0, 4.0, -1.5))
        # coneMaterial = QPhongMaterial()
        # coneMaterial.setDiffuse(getColorObj('#f74308'))
        # self.m_coneEntity = QEntity(self.m_root_entity)
        # self.m_coneEntity.addComponent(cone)
        # self.m_coneEntity.addComponent(coneMaterial)
        # self.m_coneEntity.addComponent(coneTransform)

        # # Torus
        # self.m_torus = QTorusMesh()
        # self.m_torus.setRadius(1.0)
        # self.m_torus.setMinorRadius(0.4)
        # self.m_torus.setRings(100)
        # self.m_torus.setSlices(20)
        # torusTransform = QTransform()
        # torusTransform.setScale(1.5)
        # torusTransform.setRotation(QQuaternion.fromAxisAndAngle(
        #                            QVector3D(0.0, 1.0, 0.0), 25.0))
        # torusTransform.setTranslation(QVector3D(5.0, 4.0, 0.0))
        # torusMaterial = QPhongMaterial()
        # torusMaterial.setDiffuse(getColorObj('#f7931e'))
        # self.m_torusEntity = QEntity(self.m_root_entity)
        # self.m_torusEntity.addComponent(self.m_torus)
        # self.m_torusEntity.addComponent(torusMaterial)
        # self.m_torusEntity.addComponent(torusTransform)

        # # Sphere
        # sphereMesh = QSphereMesh()
        # sphereMesh.setRings(20)
        # sphereMesh.setSlices(20)
        # sphereMesh.setRadius(2)
        # sphereTransform = QTransform()
        # sphereTransform.setScale(0.8)
        # sphereTransform.setTranslation(QVector3D(-5.0, -4.0, 0.0))
        # sphereMaterial = QPhongMaterial()
        # sphereMaterial.setDiffuse(getColorObj('#aaaa00'))
        # self.m_sphereEntity = QEntity(self.m_root_entity)
        # self.m_sphereEntity.addComponent(sphereMesh)
        # self.m_sphereEntity.addComponent(sphereMaterial)
        # self.m_sphereEntity.addComponent(sphereTransform)

        # # Plane
        # planeMesh = QPlaneMesh()
        # planeMesh.setWidth(2)
        # planeMesh.setHeight(2)
        # planeTransform = QTransform()
        # planeTransform.setScale(1.3)
        # planeTransform.setRotation(QQuaternion.fromAxisAndAngle(
        #                            QVector3D(1.0, 0.0, 0.0), 75.0))
        # planeTransform.setTranslation(QVector3D(0.0, -4.0, 0.0))
        # planeMaterial = QPhongMaterial()
        # planeMaterial.setDiffuse(getColorObj('#57bb00'))
        # self.m_planeEntity = QEntity(self.m_root_entity)
        # self.m_planeEntity.addComponent(planeMesh)
        # self.m_planeEntity.addComponent(planeMaterial)
        # self.m_planeEntity.addComponent(planeTransform)

        # # Cuboid
        # cuboid = QCuboidMesh()
        # cuboidTransform = QTransform()
        # cuboidTransform.setScale(2.0)
        # cuboidTransform.setRotation(QQuaternion.fromAxisAndAngle(
        #                             QVector3D(1.0, 1.0, 0.0), 45.0))
        # cuboidTransform.setTranslation(QVector3D(5.0, -4.0, 0.0))
        # cuboidMaterial = QPhongMaterial()
        # cuboidMaterial.setDiffuse(getColorObj('#03b6a2'))
        # # cuboidMaterial.setShininess(1.0)
        # # cuboidMaterial = QPhongAlphaMaterial()
        # # cuboidMaterial.setDiffuse(QColor(0xffffff))
        # # cuboidMaterial.setAlpha(0.2)
        # self.m_cuboidEntity = QEntity(self.m_root_entity)
        # self.m_cuboidEntity.addComponent(cuboid)
        # self.m_cuboidEntity.addComponent(cuboidMaterial)
        # self.m_cuboidEntity.addComponent(cuboidTransform)

    @pyqtSlot(int)
    def enableTorus(self, enabled):
        self.m_torusEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableCone(self, enabled):
        self.m_coneEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableCylinder(self, enabled):
        self.m_cylinderEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableCuboid(self, enabled):
        self.m_cuboidEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enablePlane(self, enabled):
        self.m_planeEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableSphere(self, enabled):
        self.m_sphereEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableLight(self, enabled):
        self.m_lightEntity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def enableLight2(self, enabled):
        self.m_light2Entity.setParent(self.m_root_entity if enabled else None)

    @pyqtSlot(int)
    def changeLightX(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setX(2*(value/100.-1)+1)
        # print(v)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLightY(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setY(2*(value/100.-1)+1)
        # print(v)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLightZ(self, value):
        v = QVector3D(self.light.worldDirection())
        v.setZ(2*(value/100.-1)+1)
        # print(v)
        self.light.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLight2X(self, value):
        v = QVector3D(self.light2.worldDirection())
        v.setX(2*(value/100.-1)+1)
        # print(v)
        self.light2.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLight2Y(self, value):
        v = QVector3D(self.light2.worldDirection())
        v.setY(2*(value/100.-1)+1)
        # print(v)
        self.light2.setWorldDirection(v)

    @pyqtSlot(int)
    def changeLight2Z(self, value):
        v = QVector3D(self.light2.worldDirection())
        v.setZ(2*(value/100.-1)+1)
        # print(v)
        self.light2.setWorldDirection(v)


class SolidDockWidget(QDockWidget):
    """
    SolidDockWidget is the solid view's equivalent of CustomQGraphicsView.
    It gets added to the dock area directly by DocumentWindow, and maintains
    a QWidget container for the Qt3DWindow.

    Attributes:
        root_entity (QEntity): Description
    """
    name = 'solid'

    def __init__(self, root_entity):
        """Instantiates PyQt3D objects for the Solid view.
        Sets up the 2D layout, and then the 3D window.
        """
        super(SolidDockWidget, self).__init__()
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
        """Creates and arranges the GUI inputs. Derived from basicshapes-py.
        Just some checkboxes and sliders at the moment, will certainly change.
        """
        view = self.view
        widget = self.widget
        container = self.container
        modifier = self.modifier

        view.defaultFramegraph().setClearColor(getColorObj('#666666'))
        # screenSize = view.screen().size()
        # container.setMinimumSize(QSize(200, 100))
        # container.setMaximumSize(screenSize)

        hLayout = QHBoxLayout(widget)
        vLayout = QVBoxLayout()
        vLayout.setAlignment(Qt.AlignTop)
        hLayout.addWidget(container, 1)
        hLayout.addLayout(vLayout)

        torusCB = QCheckBox(checked=True, text="Torus")
        coneCB = QCheckBox(checked=True, text="Cone")
        cylinderCB = QCheckBox(checked=True, text="Cylinder")
        cuboidCB = QCheckBox(checked=True, text="Cuboid")
        planeCB = QCheckBox(checked=True, text="Plane")
        sphereCB = QCheckBox(checked=True, text="Sphere")
        lightCB = QCheckBox(checked=True, text="Light")
        lightSliderX = QSlider(Qt.Horizontal)
        lightSliderY = QSlider(Qt.Horizontal)
        lightSliderZ = QSlider(Qt.Horizontal)
        light2CB = QCheckBox(checked=True, text="Light2")
        light2SliderX = QSlider(Qt.Horizontal)
        light2SliderY = QSlider(Qt.Horizontal)
        light2SliderZ = QSlider(Qt.Horizontal)

        # info = QCommandLinkButton(text="Qt3D ready-made meshes")
        # info.setDescription("Qt3D provides several ready-made meshes, like torus, "
        #                     "cylinder, cone, cube, plane and sphere.")
        # info.setIconSize(QSize(0, 0))
        # vLayout.addWidget(info)

        # vLayout.addWidget(torusCB)
        # vLayout.addWidget(coneCB)
        # vLayout.addWidget(cylinderCB)
        # vLayout.addWidget(cuboidCB)
        # vLayout.addWidget(planeCB)
        # vLayout.addWidget(sphereCB)
        vLayout.addWidget(lightCB)
        vLayout.addWidget(lightSliderX)
        vLayout.addWidget(lightSliderY)
        vLayout.addWidget(lightSliderZ)
        vLayout.addWidget(light2CB)
        vLayout.addWidget(light2SliderX)
        vLayout.addWidget(light2SliderY)
        vLayout.addWidget(light2SliderZ)

        # torusCB.stateChanged.connect(modifier.enableTorus)
        # coneCB.stateChanged.connect(modifier.enableCone)
        # cylinderCB.stateChanged.connect(modifier.enableCylinder)
        # cuboidCB.stateChanged.connect(modifier.enableCuboid)
        # planeCB.stateChanged.connect(modifier.enablePlane)
        # sphereCB.stateChanged.connect(modifier.enableSphere)
        lightCB.stateChanged.connect(modifier.enableLight)
        lightSliderX.valueChanged.connect(modifier.changeLightX)
        lightSliderY.valueChanged.connect(modifier.changeLightY)
        lightSliderZ.valueChanged.connect(modifier.changeLightZ)
        light2CB.stateChanged.connect(modifier.enableLight2)
        light2SliderX.valueChanged.connect(modifier.changeLight2X)
        light2SliderY.valueChanged.connect(modifier.changeLight2Y)
        light2SliderZ.valueChanged.connect(modifier.changeLight2Z)

        self.setWindowTitle("3D")

    def _init3D(self):
        """Configure the camera and register the view aspect and root entity."""
        camera_entity = self.camera_entity
        camera_entity.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 1000.0)
        camera_entity.setPosition(QVector3D(0.0, 0.0, 50.0))
        camera_entity.setUpVector(QVector3D(0.0, 1.0, 0.0))
        camera_entity.setViewCenter(QVector3D(0.0, 0.0, 0.0))
        self.cam_controller.setCamera(camera_entity)
        self.view.registerAspect(self.aspect)
        self.view.setRootEntity(self.root_entity)
