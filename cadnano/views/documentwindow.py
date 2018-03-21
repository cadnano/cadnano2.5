from collections import namedtuple

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
from cadnano.views.abstractitems.abstracttoolmanager import AbstractTool

# from PyQt5.QtOpenGL import QGLWidget
# # check out https://github.com/baoboa/pyqt5/tree/master/examples/opengl
# # for an example of the QOpenGlWidget added in Qt 5.4
CNView = namedtuple('CNView', ['view', 'scene', 'root_item'])

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

        self.views = {}
        self.views['slice'] = self._initSliceview(doc)
        self.views['grid']  = self._initGridview(doc)
        self.views['path']  = self._initPathview(doc)

        self._initPathviewToolbar()
        self._initEditMenu()

        self.path_dock_widget.setTitleBarWidget(QWidget())
        self.grid_dock_widget.setTitleBarWidget(QWidget())
        self.slice_dock_widget.setTitleBarWidget(QWidget())
        self.inspector_dock_widget.setTitleBarWidget(QWidget())

        self.setCentralWidget(None)
        if app().prefs.orthoview_idx == OrthoViewType.SLICE:
            self.splitDockWidget(self.slice_dock_widget, self.path_dock_widget, Qt.Horizontal)
        elif app().prefs.orthoview_idx == OrthoViewType.GRID:
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

    def destroyView(self, view_name: str):
        '''
        Args:
            view_name: the name of the view

        Raises:
            ValueError for ``view_name`` not existing
        '''
        cnview = self.views.get(view_name)
        if cnview is not None:
            cnview.root_item
        else:
            raise ValueError("view_name: %s does not exist" % (view_name))


    def _initGridview(self, doc) -> CNView:
        """Initializes Grid View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns: None
        """
        grid_scene = QGraphicsScene(parent=self.grid_graphics_view)
        grid_root = GridRootItem(   rect=grid_scene.sceneRect(),
                                    parent=None,
                                    window=self,
                                    document=doc)
        grid_scene.addItem(grid_root)
        grid_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert grid_root.scene() == grid_scene
        ggv = self.grid_graphics_view
        ggv.setScene(grid_scene)
        ggv.scene_root_item = grid_root
        ggv.setName("GridView")
        self.grid_tool_manager = GridToolManager(self, grid_root)
        return CNView(ggv, grid_scene, grid_root)
    # end def

    def _initPathview(self, doc) -> CNView:
        """Initializes Path View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns:
            CNView namedtuple
        """
        path_scene = QGraphicsScene(parent=self.path_graphics_view)
        path_root = PathRootItem(   rect=path_scene.sceneRect(),
                                    parent=None,
                                    window=self,
                                    document=doc)
        path_scene.addItem(path_root)
        path_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert path_root.scene() == path_scene
        pgv = self.path_graphics_view
        pgv.setScene(path_scene)
        pgv.scene_root_item = path_root
        pgv.setScaleFitFactor(0.7)
        pgv.setName("PathView")
        return CNView(pgv, path_scene, path_root)
    # end def

    def _initPathviewToolbar(self):
        """Initializes Path View Toolbar.

        Returns: None
        """
        self.path_color_panel = ColorPanel()
        self.path_graphics_view.toolbar = self.path_color_panel  # HACK for customqgraphicsview
        path_scene = self.views['path'].scene
        path_scene.addItem(self.path_color_panel)
        self.path_tool_manager = PathToolManager(self, self.views['path'].root_item)

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

    def _initSliceview(self, doc) -> CNView:
        """Initializes Slice View.

        Args:
            doc (cadnano.document.Document): The Document corresponding to
            the design

        Returns:
            CNView namedtuple
        """
        slice_scene = QGraphicsScene(parent=self.slice_graphics_view)
        slice_root = SliceRootItem( rect=slice_scene.sceneRect(),
                                    parent=None,
                                    window=self,
                                    document=doc)
        slice_scene.addItem(slice_root)
        slice_scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert slice_root.scene() == slice_scene
        sgv = self.slice_graphics_view
        sgv.setScene(slice_scene)
        sgv.scene_root_item = slice_root
        sgv.setName("SliceView")
        sgv.setScaleFitFactor(0.7)
        self.slice_tool_manager = SliceToolManager(self, slice_root)
        return CNView(sgv, slice_scene, slice_root)
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
        path_visible = self.slice_dock_widget.widget().isVisibleTo(self)
        self.action_path.setChecked(path_visible)
        slice_visible = self.slice_dock_widget.isVisibleTo(self)
        self.action_slice.setChecked(slice_visible)
    # end def

    def getMouseViewTool(self, tool_type_name: str) -> AbstractTool:
        """Give a tool type, return the tool for the view the mouse is over

        Args:
            tool_type_name: the tool which is active or None

        Returns:
            active tool for the view the tool is in
        """
        return_tool = None
        for item in self.views.values():
            view, scene, root_item = item
            if view.underMouse():
                # print("I am under mouse", view)
                if root_item.manager.isToolActive(tool_type_name):
                    # print("{} is active".format(tool_type_name))
                    return_tool = root_item.manager.activeToolGetter()
                else:
                    # print("no {} HERE!".format(tool_type_name))
                    pass
                break
        return return_tool
# end class
