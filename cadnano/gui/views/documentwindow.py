from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QApplication, QWidget, QAction
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QCheckBox, QCommandLinkButton

from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.QtGui import QColor, QQuaternion, QVector3D
from PyQt5.Qt3DExtras import Qt3DWindow, QCylinderMesh
from PyQt5.Qt3DExtras import QFirstPersonCameraController, QPhongMaterial
from PyQt5.Qt3DInput import QInputAspect

from cadnano import app
from cadnano.gui.views.pathview.colorpanel import ColorPanel
from cadnano.gui.views.pathview.pathrootitem import PathRootItem
from cadnano.gui.views.pathview.tools.pathtoolmanager import PathToolManager
from cadnano.gui.views.sliceview.slicerootitem import SliceRootItem
from cadnano.gui.views.sliceview.tools.slicetoolmanager import SliceToolManager
from cadnano.gui.ui.mainwindow import ui_mainwindow

# from PyQt5.QtOpenGL import QGLWidget
# # check out https://github.com/baoboa/pyqt5/tree/master/examples/opengl
# # for an example of the QOpenGlWidget added in Qt 5.4


# Just copied the entire import block from basicshapes-py
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, QObject, QSize, Qt
from PyQt5.QtGui import QColor, QQuaternion, QVector3D
from PyQt5.QtWidgets import (QApplication, QCheckBox, QCommandLinkButton,
        QHBoxLayout, QVBoxLayout, QWidget, QDockWidget)
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import (Qt3DWindow, QConeMesh, QCuboidMesh,
        QCylinderMesh, QFirstPersonCameraController, QPhongMaterial,
        QPlaneMesh, QSphereMesh, QTorusMesh)
from PyQt5.Qt3DInput import QInputAspect
from PyQt5.Qt3DRender import QCamera


class SceneModifier(QObject):
    def __init__(self, rootEntity):
        super(SceneModifier, self).__init__()

        self.m_rootEntity = rootEntity

        # Torus shape data.
        self.m_torus = QTorusMesh()
        self.m_torus.setRadius(1.0)
        self.m_torus.setMinorRadius(0.4)
        self.m_torus.setRings(100)
        self.m_torus.setSlices(20)

        # TorusMesh transform.
        torusTransform = QTransform()
        torusTransform.setScale(2.0)
        torusTransform.setRotation(
                QQuaternion.fromAxisAndAngle(QVector3D(0.0, 1.0, 0.0), 25.0))
        torusTransform.setTranslation(QVector3D(5.0, 4.0, 0.0))

        torusMaterial = QPhongMaterial()
        torusMaterial.setDiffuse(QColor(0xbeb32b))

        # Torus.
        self.m_torusEntity = QEntity(self.m_rootEntity)
        self.m_torusEntity.addComponent(self.m_torus)
        self.m_torusEntity.addComponent(torusMaterial)
        self.m_torusEntity.addComponent(torusTransform)

        # Cone shape data.
        cone = QConeMesh()
        cone.setTopRadius(0.5)
        cone.setBottomRadius(1)
        cone.setLength(3)
        cone.setRings(50)
        cone.setSlices(20)

        # ConeMesh transform.
        coneTransform = QTransform()
        coneTransform.setScale(1.5)
        coneTransform.setRotation(
                QQuaternion.fromAxisAndAngle(QVector3D(1.0, 0.0, 0.0), 45.0))
        coneTransform.setTranslation(QVector3D(0.0, 4.0, -1.5))

        coneMaterial = QPhongMaterial()
        coneMaterial.setDiffuse(QColor(0x928327))

        # Cone.
        self.m_coneEntity = QEntity(self.m_rootEntity)
        self.m_coneEntity.addComponent(cone)
        self.m_coneEntity.addComponent(coneMaterial)
        self.m_coneEntity.addComponent(coneTransform)

        # Cylinder shape data.
        cylinder = QCylinderMesh()
        cylinder.setRadius(1)
        cylinder.setLength(3)
        cylinder.setRings(100)
        cylinder.setSlices(20)

        # CylinderMesh transform.
        cylinderTransform = QTransform()
        cylinderTransform.setScale(1.5)
        cylinderTransform.setRotation(
                QQuaternion.fromAxisAndAngle(QVector3D(1.0, 0.0, 0.0), 45.0))
        cylinderTransform.setTranslation(QVector3D(-5.0, 4.0, -1.5))

        cylinderMaterial = QPhongMaterial()
        cylinderMaterial.setDiffuse(QColor(0x928327))

        # Cylinder.
        self.m_cylinderEntity = QEntity(self.m_rootEntity)
        self.m_cylinderEntity.addComponent(cylinder)
        self.m_cylinderEntity.addComponent(cylinderMaterial)
        self.m_cylinderEntity.addComponent(cylinderTransform)

        # Cuboid shape data.
        cuboid = QCuboidMesh()

        # CuboidMesh transform.
        cuboidTransform = QTransform()
        cuboidTransform.setScale(4.0)
        cuboidTransform.setTranslation(QVector3D(5.0, -4.0, 0.0))

        cuboidMaterial = QPhongMaterial()
        cuboidMaterial.setDiffuse(QColor(0x665423))

        # Cuboid.
        self.m_cuboidEntity = QEntity(self.m_rootEntity)
        self.m_cuboidEntity.addComponent(cuboid)
        self.m_cuboidEntity.addComponent(cuboidMaterial)
        self.m_cuboidEntity.addComponent(cuboidTransform)

        # Plane shape data.
        planeMesh = QPlaneMesh()
        planeMesh.setWidth(2)
        planeMesh.setHeight(2)

        # Plane mesh transform.
        planeTransform = QTransform()
        planeTransform.setScale(1.3)
        planeTransform.setRotation(
                QQuaternion.fromAxisAndAngle(QVector3D(1.0, 0.0, 0.0), 45.0))
        planeTransform.setTranslation(QVector3D(0.0, -4.0, 0.0))

        planeMaterial = QPhongMaterial()
        planeMaterial.setDiffuse(QColor(0xa69929))

        # Plane.
        self.m_planeEntity = QEntity(self.m_rootEntity)
        self.m_planeEntity.addComponent(planeMesh)
        self.m_planeEntity.addComponent(planeMaterial)
        self.m_planeEntity.addComponent(planeTransform)

        # Sphere shape data.
        sphereMesh = QSphereMesh()
        sphereMesh.setRings(20)
        sphereMesh.setSlices(20)
        sphereMesh.setRadius(2)

        # Sphere mesh transform.
        sphereTransform = QTransform()
        sphereTransform.setScale(1.3)
        sphereTransform.setTranslation(QVector3D(-5.0, -4.0, 0.0))

        sphereMaterial = QPhongMaterial()
        sphereMaterial.setDiffuse(QColor(0xa69929))

        # Sphere.
        self.m_sphereEntity = QEntity(self.m_rootEntity)
        self.m_sphereEntity.addComponent(sphereMesh)
        self.m_sphereEntity.addComponent(sphereMaterial)
        self.m_sphereEntity.addComponent(sphereTransform)

    @pyqtSlot(int)
    def enableTorus(self, enabled):
        self.m_torusEntity.setParent(self.m_rootEntity if enabled else None)

    @pyqtSlot(int)
    def enableCone(self, enabled):
        self.m_coneEntity.setParent(self.m_rootEntity if enabled else None)

    @pyqtSlot(int)
    def enableCylinder(self, enabled):
        self.m_cylinderEntity.setParent(self.m_rootEntity if enabled else None)

    @pyqtSlot(int)
    def enableCuboid(self, enabled):
        self.m_cuboidEntity.setParent(self.m_rootEntity if enabled else None)

    @pyqtSlot(int)
    def enablePlane(self, enabled):
        self.m_planeEntity.setParent(self.m_rootEntity if enabled else None)

    @pyqtSlot(int)
    def enableSphere(self, enabled):
        self.m_sphereEntity.setParent(self.m_rootEntity if enabled else None)


class DocumentWindow(QMainWindow, ui_mainwindow.Ui_MainWindow):
    """DocumentWindow subclasses QMainWindow and Ui_MainWindow. It performs
    some initialization operations that must be done in code rather than
    using Qt Creator.

    Attributes:
        controller (DocumentController):
    """
    def __init__(self, parent=None, doc_ctrlr=None):
        super(DocumentWindow, self).__init__(parent)
        self.controller = doc_ctrlr
        doc = doc_ctrlr.document()
        self.setupUi(self)
        self.settings = QSettings()
        self._readSettings()
        # self.setCentralWidget(self.slice_graphics_view)
        # Appearance pref
        if not app().prefs.show_icon_labels:
            self.main_toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # Outliner & PropertyEditor setup
        self.outliner_widget.configure(window=self, document=doc)
        self.property_widget.configure(window=self, document=doc)
        self.property_buttonbox.setVisible(False)

        self.tool_managers = None  # initialize

        # Slice setup
        self.slicescene = QGraphicsScene(parent=self.slice_graphics_view)
        self.sliceroot = SliceRootItem(rect=self.slicescene.sceneRect(),
                                       parent=None,
                                       window=self,
                                       document=doc)
        self.sliceroot.setFlag(QGraphicsItem.ItemHasNoContents)
        self.slicescene.addItem(self.sliceroot)
        self.slicescene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.sliceroot.scene() == self.slicescene
        self.slice_graphics_view.setScene(self.slicescene)
        self.slice_graphics_view.scene_root_item = self.sliceroot
        self.slice_graphics_view.setName("SliceView")
        self.slice_tool_manager = SliceToolManager(self, self.sliceroot)
        # Path setup
        self.pathscene = QGraphicsScene(parent=self.path_graphics_view)
        self.pathroot = PathRootItem(rect=self.pathscene.sceneRect(),
                                     parent=None,
                                     window=self,
                                     document=doc)
        self.pathroot.setFlag(QGraphicsItem.ItemHasNoContents)
        self.pathscene.addItem(self.pathroot)
        self.pathscene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.pathroot.scene() == self.pathscene
        self.path_graphics_view.setScene(self.pathscene)
        self.path_graphics_view.scene_root_item = self.pathroot
        self.path_graphics_view.setScaleFitFactor(0.9)
        self.path_graphics_view.setName("PathView")

        # Toolbar
        self.path_color_panel = ColorPanel()
        self.path_graphics_view.toolbar = self.path_color_panel  # HACK for customqgraphicsview
        self.pathscene.addItem(self.path_color_panel)
        self.path_tool_manager = PathToolManager(self, self.pathroot)
        self.slice_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.slice_tool_manager = self.slice_tool_manager
        self.tool_managers = (self.path_tool_manager, self.slice_tool_manager)

        self.insertToolBarBreak(self.main_toolbar)

        self.path_graphics_view.setupGL()
        self.slice_graphics_view.setupGL()

        # Edit menu setup
        self.actionUndo = doc_ctrlr.undoStack().createUndoAction(self)
        self.actionRedo = doc_ctrlr.undoStack().createRedoAction(self)
        self.actionUndo.setText(QApplication.translate("MainWindow", "Undo", None))
        self.actionUndo.setShortcut(QApplication.translate("MainWindow", "Ctrl+Z", None))
        self.actionRedo.setText(QApplication.translate("MainWindow", "Redo", None))
        self.actionRedo.setShortcut(QApplication.translate("MainWindow", "Ctrl+Shift+Z", None))
        self.sep = QAction(self)
        self.sep.setSeparator(True)
        self.menu_edit.insertAction(self.sep, self.actionRedo)
        self.menu_edit.insertAction(self.actionRedo, self.actionUndo)
        # self.main_splitter.setSizes([400, 400, 180])  # balance main_splitter size
        self.statusBar().showMessage("")

        doc.setViewNames(['slice', 'path'])

        self._solidSetup()
    # end def

    def _solidSetup(self):

        # view = Qt3DWindow()
        # view.defaultFramegraph().setClearColor(QColor(0x4d4d4f))

        # container = QWidget.createWindowContainer(view)
        # screenSize = view.screen().size()
        # container.setMinimumSize(QSize(200, 100))
        # container.setMaximumSize(screenSize)

        # self.widget = widget = QWidget()
        # self.setCentralWidget(widget)
        # # widget.show()
        # hLayout = QHBoxLayout(widget)
        # hLayout.addWidget(container, 1)
        # # layout = self.centralWidget().layout()
        # # layout.addWidget(container, 1)

        view = Qt3DWindow()
        view.defaultFramegraph().setClearColor(QColor(0x4d4d4f))
        container = QWidget.createWindowContainer(view)
        screenSize = view.screen().size()
        container.setMinimumSize(QSize(200, 100))
        container.setMaximumSize(screenSize)

        # from PyQt5.QtWidgets import QMainWindow
        # mainwindow = QMainWindow()

        widget = QWidget()
        # mainwindow.setCentralWidget(widget)
        dockwidget = QDockWidget()
        dockwidget.setWidget(widget)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(1), dockwidget)

        hLayout = QHBoxLayout(widget)
        vLayout = QVBoxLayout()
        vLayout.setAlignment(Qt.AlignTop)
        hLayout.addWidget(container, 1)
        hLayout.addLayout(vLayout)

        self.setWindowTitle("Basic shapes")

        aspect = QInputAspect()
        view.registerAspect(aspect)

        # Root entity.
        rootEntity = QEntity()

        # Camera.
        cameraEntity = view.camera()

        cameraEntity.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 1000.0)
        cameraEntity.setPosition(QVector3D(0.0, 0.0, 20.0))
        cameraEntity.setUpVector(QVector3D(0.0, 1.0, 0.0))
        cameraEntity.setViewCenter(QVector3D(0.0, 0.0, 0.0))

        # For camera controls.
        camController = QFirstPersonCameraController(rootEntity)
        camController.setCamera(cameraEntity)

        # Scene modifier.
        modifier = SceneModifier(rootEntity)

        # Set root object of the scene.
        # view.setRootEntity(rootEntity)

        # Create control widgets.
        info = QCommandLinkButton(text="Qt3D ready-made meshes")
        info.setDescription("Qt3D provides several ready-made meshes, like torus, "
                "cylinder, cone, cube, plane and sphere.")
        info.setIconSize(QSize(0,0))

        torusCB = QCheckBox(checked=True, text="Torus")
        coneCB = QCheckBox(checked=True, text="Cone")
        cylinderCB = QCheckBox(checked=True, text="Cylinder")
        cuboidCB = QCheckBox(checked=True, text="Cuboid")
        planeCB = QCheckBox(checked=True, text="Plane")
        sphereCB = QCheckBox(checked=True, text="Sphere")

        vLayout.addWidget(info)
        vLayout.addWidget(torusCB)
        vLayout.addWidget(coneCB)
        vLayout.addWidget(cylinderCB)
        vLayout.addWidget(cuboidCB)
        vLayout.addWidget(planeCB)
        vLayout.addWidget(sphereCB)

        torusCB.stateChanged.connect(modifier.enableTorus)
        coneCB.stateChanged.connect(modifier.enableCone)
        cylinderCB.stateChanged.connect(modifier.enableCylinder)
        cuboidCB.stateChanged.connect(modifier.enableCuboid)
        planeCB.stateChanged.connect(modifier.enablePlane)
        sphereCB.stateChanged.connect(modifier.enableSphere)


        # widget.resize(200, 200)

    def document(self):
        return self.controller.document()
    # end def

    def destroyWin(self):
        for mgr in self.tool_managers:
            mgr.destroy()
        self.controller = None
    # end def

    ### ACCESSORS ###
    def undoStack(self):
        return self.controller.undoStack()

    def selectedInstance(self):
        return self.controller.document().selectedInstance()

    def activateSelection(self, isActive):
        self.path_graphics_view.activateSelection(isActive)
        self.slice_graphics_view.activateSelection(isActive)
    # end def

    ### EVENT HANDLERS ###
    def focusInEvent(self):
        app().undoGroup.setActiveStack(self.controller.undoStack())

    def moveEvent(self, event):
        """Reimplemented to save state on move."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

    def resizeEvent(self, event):
        """Reimplemented to save state on resize."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.endGroup()
        QWidget.resizeEvent(self, event)

    def changeEvent(self, event):
        QWidget.changeEvent(self, event)
    # end def

    ### DRAWING RELATED ###

    ### PRIVATE HELPER METHODS ###
    def _readSettings(self):
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QSize(1100, 800)))
        self.move(self.settings.value("pos", QPoint(200, 200)))
        self.settings.endGroup()
# end class
