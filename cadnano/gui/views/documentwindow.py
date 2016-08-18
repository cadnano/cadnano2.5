from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QApplication, QWidget, QAction

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

        # Path toolbar
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
        self.main_splitter.setSizes([400, 400, 180])  # balance main_splitter size
        self.statusBar().showMessage("")

        doc.setViewNames(['slice', 'path'])
    # end def

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
