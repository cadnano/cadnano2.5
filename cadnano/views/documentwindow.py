from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QAction, QApplication, QWidget


from cadnano import app
from cadnano.gui.mainwindow import ui_mainwindow
from cadnano.proxies.cnenum import OrthoViewType
from cadnano.views.gridview.gridrootitem import GridRootItem
from cadnano.views.gridview.tools.gridtoolmanager import GridToolManager
from cadnano.views.pathview.colorpanel import ColorPanel
from cadnano.views.pathview.pathrootitem import PathRootItem
from cadnano.views.pathview.tools.pathtoolmanager import PathToolManager
from cadnano.views.sliceview.slicerootitem import SliceRootItem
from cadnano.views.sliceview.tools.slicetoolmanager import SliceToolManager


# from PyQt5.QtOpenGL import QGLWidget
# # check out https://github.com/baoboa/pyqt5/tree/master/examples/opengl
# # for an example of the QOpenGlWidget added in Qt 5.4


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
        self.settings = QSettings("cadnano.org", "cadnano2.5")
        # Appearance pref
        if not app().prefs.show_icon_labels:
            self.main_toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # Outliner & PropertyEditor setup
        self.outliner_widget.configure(window=self, document=doc)
        self.property_widget.configure(window=self, document=doc)
        self.property_buttonbox.setVisible(False)

        self.tool_managers = None  # initialize

        self._initSliceview(doc)
        self._initGridview(doc)
        self._initPathview(doc)
        self._initPathviewToolbar()
        self._initEditMenu()

        self.path_dock_widget.setTitleBarWidget(QWidget())
        self.grid_dock_widget.setTitleBarWidget(QWidget())
        self.slice_dock_widget.setTitleBarWidget(QWidget())
        self.inspector_dock_widget.setTitleBarWidget(QWidget())

        self.setCentralWidget(None)
        if app().prefs.orthoview_style == OrthoViewType.SLICE:
            self.splitDockWidget(self.slice_dock_widget, self.path_dock_widget, Qt.Horizontal)
        elif app().prefs.orthoview_style == OrthoViewType.GRID:
            self.splitDockWidget(self.grid_dock_widget, self.path_dock_widget, Qt.Horizontal)
        self._restoreGeometryandState()
        self._finishInit()

        doc.setViewNames(['slice', 'path', 'inspector'])
    # end def

    def document(self):
        return self.controller.document()

    def destroyWin(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()
        for mgr in self.tool_managers:
            mgr.destroy()
        self.controller = None

    ### ACCESSORS ###
    def undoStack(self):
        return self.controller.undoStack()

    def selectedInstance(self):
        return self.controller.document().selectedInstance()

    def activateSelection(self, isActive):
        self.path_graphics_view.activateSelection(isActive)
        self.slice_graphics_view.activateSelection(isActive)
        self.grid_graphics_view.activateSelection(isActive)

    ### EVENT HANDLERS ###
    def focusInEvent(self):
        """Handle an OS focus change into cadnano."""
        app().undoGroup.setActiveStack(self.controller.undoStack())

    def moveEvent(self, event):
        """Handle the moving of the cadnano window itself.

        Reimplemented to save state on move.
        """
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

    def resizeEvent(self, event):
        """Handle the resizing of the cadnano window itself.

        Reimplemented to save state on resize.
        """
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("size", self.size())
        self.settings.endGroup()
        QWidget.resizeEvent(self, event)

    def changeEvent(self, event):
        QWidget.changeEvent(self, event)

    # end def

    ### DRAWING RELATED ###

    ### PRIVATE HELPER METHODS ###
    def _restoreGeometryandState(self):
        self.settings.beginGroup("MainWindow")
        geometry = self.settings.value("geometry")
        state = self.settings.value("geometry")
        if geometry is not None:
            result = self.restoreGeometry(geometry)
            if result is False:
                print("MainWindow.restoreGeometry() failed.")
        else:
            print("Setting default MainWindow size: 1100x800")
            self.resize(self.settings.value("size", QSize(1100, 800)))
            self.move(self.settings.value("pos", QPoint(200, 200)))
            self.inspector_dock_widget.close()
            self.action_inspector.setChecked(False)
        state = self.settings.value("state")
        if state is not None:
            result = self.restoreState(state)
            if result is False:
                print("MainWindow.restoreState() failed.")
        self.settings.endGroup()
    # end def

    def _initGridview(self, doc):
        """Initializes Grid View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns: None
        """
        self.grid_scene = QGraphicsScene(parent=self.grid_graphics_view)
        self.grid_root = GridRootItem(rect=self.grid_scene.sceneRect(),
                                      parent=None,
                                      window=self,
                                      document=doc)
        self.grid_root.setFlag(QGraphicsItem.ItemHasNoContents)
        self.grid_scene.addItem(self.grid_root)
        self.grid_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.grid_root.scene() == self.grid_scene
        self.grid_graphics_view.setScene(self.grid_scene)
        self.grid_graphics_view.scene_root_item = self.grid_root
        self.grid_graphics_view.setName("GridView")
        self.grid_tool_manager = GridToolManager(self, self.grid_root)
    # end def

    def _initPathview(self, doc):
        """Initializes Path View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns: None
        """
        self.path_scene = QGraphicsScene(parent=self.path_graphics_view)
        self.path_root = PathRootItem(rect=self.path_scene.sceneRect(),
                                      parent=None,
                                      window=self,
                                      document=doc)
        self.path_root.setFlag(QGraphicsItem.ItemHasNoContents)
        self.path_scene.addItem(self.path_root)
        self.path_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.path_root.scene() == self.path_scene
        self.path_graphics_view.setScene(self.path_scene)
        self.path_graphics_view.scene_root_item = self.path_root
        self.path_graphics_view.setScaleFitFactor(0.7)
        self.path_graphics_view.setName("PathView")
    # end def

    def _initPathviewToolbar(self):
        """Initializes Path View Toolbar.

        Returns: None
        """
        self.path_color_panel = ColorPanel()
        self.path_graphics_view.toolbar = self.path_color_panel  # HACK for customqgraphicsview
        self.path_scene.addItem(self.path_color_panel)
        self.path_tool_manager = PathToolManager(self, self.path_root)

        self.slice_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.slice_tool_manager = self.slice_tool_manager

        self.grid_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.grid_tool_manager = self.grid_tool_manager

        self.tool_managers = (self.path_tool_manager, self.slice_tool_manager, self.grid_tool_manager)

        self.insertToolBarBreak(self.main_toolbar)

        self.path_graphics_view.setupGL()
        self.slice_graphics_view.setupGL()
        self.grid_graphics_view.setupGL()
    # end def

    def _initSliceview(self, doc):
        """Initializes Slice View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns: None
        """
        self.slice_scene = QGraphicsScene(parent=self.slice_graphics_view)
        self.slice_root = SliceRootItem(rect=self.slice_scene.sceneRect(),
                                        parent=None,
                                        window=self,
                                        document=doc)
        self.slice_root.setFlag(QGraphicsItem.ItemHasNoContents)
        self.slice_scene.addItem(self.slice_root)
        self.slice_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.slice_root.scene() == self.slice_scene
        self.slice_graphics_view.setScene(self.slice_scene)
        self.slice_graphics_view.scene_root_item = self.slice_root
        self.slice_graphics_view.setName("SliceView")
        self.slice_graphics_view.setScaleFitFactor(0.7)
        self.slice_tool_manager = SliceToolManager(self, self.slice_root)
    # end def

    def _initEditMenu(self):
        """Initializes the Edit menu

        Returns: None
        """
        self.actionUndo = self.controller.undoStack().createUndoAction(self)
        self.actionRedo = self.controller.undoStack().createRedoAction(self)
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
    # end def

    def _finishInit(self):
        """
        Handle the dockwindow visibility and action checked status.
        The console visibility is explicitly stored in the settings file,
        since it doesn't seem to work if we treat it like a normal dock widget.
        """
        inspector_visible = self.inspector_dock_widget.isVisibleTo(self)
        self.action_inspector.setChecked(inspector_visible)
        path_visible = self.path_dock_widget.isVisibleTo(self)
        self.action_path.setChecked(path_visible)
        slice_visible = self.slice_dock_widget.isVisibleTo(self)
        self.action_slice.setChecked(slice_visible)
    # end def
# end class
