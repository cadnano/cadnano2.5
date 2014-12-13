from cadnano import app

from cadnano.gui.views.pathview.pathtoolbar import PathToolBar
from cadnano.gui.views.pathview.parttoolbar import PartToolBar
from cadnano.gui.views.pathview.colorpanel import ColorPanel

from cadnano.gui.views.pathview.tools.pathtoolmanager import PathToolManager
from cadnano.gui.views.sliceview.slicerootitem import SliceRootItem
from cadnano.gui.views.pathview.pathrootitem import PathRootItem

from cadnano.gui.views.sliceview.tools.slicetoolmanager import SliceToolManager
import cadnano.gui.ui.mainwindow.ui_mainwindow as ui_mainwindow
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtCore import QFileInfo, QSettings
from PyQt5.QtCore import QPoint, QSize

from PyQt5.QtGui import QPaintEngine, QIcon
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsScene
from PyQt5.QtWidgets import QGraphicsView, QMainWindow
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PyQt5.QtWidgets import QApplication, QWidget, QAction
from PyQt5.QtWidgets import QSizePolicy, QFrame

# for OpenGL mode
try:
    from OpenGL import GL
except:
    GL = False

GL = False

class DocumentWindow(QMainWindow, ui_mainwindow.Ui_MainWindow):
    """docstring for DocumentWindow"""
    def __init__(self, parent=None, doc_ctrlr=None):
        super(DocumentWindow, self).__init__(parent)

        self.controller = doc_ctrlr
        doc = doc_ctrlr.document()
        self.setupUi(self)
        self.settings = QSettings()
        self._readSettings()

        # Slice setup
        self.slicescene = QGraphicsScene(parent=self.slice_graphics_view)
        self.sliceroot = SliceRootItem(rect=self.slicescene.sceneRect(),\
                                       parent=None,\
                                       window=self,\
                                       document=doc)
        self.sliceroot.setFlag(QGraphicsItem.ItemHasNoContents)
        self.slicescene.addItem(self.sliceroot)
        self.slicescene.setItemIndexMethod(QGraphicsScene.NoIndex)
        assert self.sliceroot.scene() == self.slicescene
        self.slice_graphics_view.setScene(self.slicescene)
        self.slice_graphics_view.scene_root_item = self.sliceroot
        self.slice_graphics_view.setName("SliceView")
        self.slice_tool_manager = SliceToolManager(self)

        # Part toolbar
        splitter_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        splitter_size_policy.setHorizontalStretch(0)
        splitter_size_policy.setVerticalStretch(0)
        splitter_size_policy.setHeightForWidth(self.main_splitter.sizePolicy().hasHeightForWidth())

        self.slice_splitter.setSizePolicy(splitter_size_policy)
        self.slice_splitter.setFrameShape(QFrame.NoFrame)
        self.slice_splitter.setFrameShadow(QFrame.Plain)
        self.slice_splitter.setLineWidth(0)
        self.slice_splitter.setOrientation(Qt.Horizontal)
        self.slice_splitter.setOpaqueResize(False)
        self.slice_splitter.setHandleWidth(0)

        self.part_toolbar = PartToolBar(doc, self.slice_splitter)
        self.slice_splitter.addWidget(self.slice_graphics_view) # reorder

        # Path setup
        self.pathscene = QGraphicsScene(parent=self.path_graphics_view)
        self.pathroot = PathRootItem(rect=self.pathscene.sceneRect(),\
                                     parent=None,\
                                     window=self,\
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
        self.path_splitter.setSizePolicy(splitter_size_policy)
        self.path_splitter.setFrameShape(QFrame.NoFrame)
        self.path_splitter.setFrameShadow(QFrame.Plain)
        self.path_splitter.setLineWidth(0)
        self.path_splitter.setOrientation(Qt.Horizontal)
        self.path_splitter.setOpaqueResize(False)
        self.path_splitter.setHandleWidth(0)
        self.path_splitter.setObjectName("path_splitter")
        self.path_splitter.setSizes([600,0]) # for path_splitter horizontal
        self.path_splitter.addWidget(self.selectionToolBar)
        self.path_toolbar = PathToolBar(doc, self.path_splitter)
        # self.path_splitter.addWidget(self.path_graphics_view) # reorder
        self.path_color_panel = ColorPanel()
        self.path_graphics_view.toolbar = self.path_color_panel  # HACK for customqgraphicsview
        self.pathscene.addItem(self.path_color_panel)
        self.path_tool_manager = PathToolManager(self, self.path_toolbar)
        self.slice_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.slice_tool_manager = self.slice_tool_manager

        # set the selection filter default
        doc.documentSelectionFilterChangedSignal.emit(["endpoint", "scaffold", "staple", "xover"])

        self.path_graphics_view.setupGL()
        self.slice_graphics_view.setupGL()
        if GL:
            pass
            # self.slicescene.drawBackground = self.drawBackgroundGL
            # self.pathscene.drawBackground = self.drawBackgroundGL

        # Edit menu setup
        self.actionUndo = doc_ctrlr.undoStack().createUndoAction(self)
        self.actionRedo = doc_ctrlr.undoStack().createRedoAction(self)
        self.actionUndo.setText(QApplication.translate(
                                            "MainWindow", "Undo",
                                            None))
        self.actionUndo.setShortcut(QApplication.translate(
                                            "MainWindow", "Ctrl+Z",
                                            None))
        self.actionRedo.setText(QApplication.translate(
                                            "MainWindow", "Redo",
                                            None))
        self.actionRedo.setShortcut(QApplication.translate(
                                            "MainWindow", "Ctrl+Shift+Z",
                                            None))
        self.sep = QAction(self)
        self.sep.setSeparator(True)
        self.menu_edit.insertAction(self.action_modify, self.sep)
        self.menu_edit.insertAction(self.sep, self.actionRedo)
        self.menu_edit.insertAction(self.actionRedo, self.actionUndo)
        self.main_splitter.setSizes([250, 550])  # balance main_splitter size
        self.statusBar().showMessage("")

    ### ACCESSORS ###
    def undoStack(self):
        return self.controller.undoStack()

    def selectedPart(self):
        return self.controller.document().selectedPart()

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
    # def drawBackgroundGL(self, painter, rect):
    #     """
    #     This method is for overloading the QGraphicsScene.
    #     """
    #     if painter.paintEngine().type() != QPaintEngine.OpenGL and \
    #         painter.paintEngine().type() != QPaintEngine.OpenGL2:
    # 
    #         qWarning("OpenGLScene: drawBackground needs a QGLWidget to be set as viewport on the graphics view");
    #         return
    #     # end if
    #     painter.beginNativePainting()
    #     GL.glDisable(GL.GL_DEPTH_TEST) # disable for 2D drawing
    #     GL.glClearColor(1.0, 1.0, 1.0, 1.0)
    #     GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    # 
    #     painter.endNativePainting()
    # # end def
    
    # def drawBackgroundNonGL(self, painter, rect):
    #     """
    #     This method is for overloading the QGraphicsScene.
    #     """
    #     print self
    #     return QGraphicsScene.drawBackground(self, painter, rect)
    # # end def

    ### PRIVATE HELPER METHODS ###
    def _readSettings(self):
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QSize(1100, 800)))
        self.move(self.settings.value("pos", QPoint(200, 200)))
        self.settings.endGroup()

