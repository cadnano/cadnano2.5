# -*- coding: utf-8 -*-
import os
from collections import namedtuple
from typing import (
    List,
    Tuple,
    Union
)
from types import MethodType

from PyQt5.QtCore import (
    Qt,
    QCoreApplication,
    QDir,
    QEvent,
    QFileInfo,
    QPoint,
    QRect,
    QSettings,
    QSize,
    pyqtBoundSignal
)
_translate = QCoreApplication.translate
from PyQt5.QtGui import (
    QMoveEvent,
    QResizeEvent
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QDialog,
    QFileDialog,
    QGraphicsItem,
    QGraphicsScene,
    QMessageBox,
    QMainWindow,
    QStyleOptionGraphicsItem,
    QWidget
)
from PyQt5.QtGui import (
    QKeySequence,
    QPainter,
    QCloseEvent
)
from PyQt5.QtSvg import QSvgGenerator

from cadnano import (
    app,
    setReopen,
    util
)
from cadnano.views import styles
from cadnano.fileio.v3encode import reEmitPart
from cadnano.proxies.cnproxy import UndoStack
from cadnano.gui.mainwindow import ui_mainwindow
from cadnano.gui.dialogs.ui_about import Ui_About
from cadnano.proxies.cnenum import (
    EnumType,
    GridEnum,
    OrthoViewEnum,
    ViewReceiveEnum,
    ViewSendEnum,
)
from cadnano.views.gridview.gridrootitem import GridRootItem
from cadnano.views.gridview.tools.gridtoolmanager import GridToolManager
from cadnano.views.pathview.colorpanel import ColorPanel
from cadnano.views.pathview.pathrootitem import PathRootItem
from cadnano.views.pathview.tools.pathtoolmanager import PathToolManager
from cadnano.views.sliceview.slicerootitem import SliceRootItem
from cadnano.views.sliceview.tools.slicetoolmanager import SliceToolManager
from cadnano.views.abstractitems import (
    AbstractTool,
    AbstractToolManager
)

from cadnano.cntypes import (
    DocT,
    WindowT,
    DocCtrlT,
    GraphicsViewT,
    NucleicAcidPartT
)

IS_TESTING = True

DEFAULT_VHELIX_FILTER = True
ONLY_ONE = True  # bool: Retricts Document to creating only one Part if True.
SAVE_DIALOG_OPTIONS = {'SAVE': 0,
                       'CANCEL': 1,
                       'DISCARD': 2
                       }

# from PyQt5.QtOpenGL import QGLWidget
# # check out https://github.com/baoboa/pyqt5/tree/master/examples/opengl
# # for an example of the QOpenGlWidget added in Qt 5.4

class CNMainWindow(QMainWindow, ui_mainwindow.Ui_MainWindow):
    """:class`CNMainWindow` subclasses :class`QMainWindow` and
    :class`Ui_MainWindow`. It performs some initialization operations that
    must be done in code rather than using Qt Creator.

    Attributes:
        _document
    """
    filter_list = ["strand", "endpoint", "xover", "virtual_helix"]

    def __init__(self, document: DocT, parent=None):
        super(CNMainWindow, self).__init__(parent)
        self._document: DocT = document
        document.setAppWindow(self)
        self.setupUi(self)
        self.docwin_signal_and_slots: List[Tuple[pyqtBoundSignal, MethodType]] = []
        self.defineWindowSignals()
        self.connectSelfSignals()

        self.fileopendialog: QFileDialog = None
        self.filesavedialog: QFileDialog = None
        self._file_open_path: str = None  # will be set in _readSettings
        self._has_no_associated_file: bool = True

        # self.settings = QSettings("cadnano.org", "cadnano2.5")
        self.settings: QSettings = QSettings(   "69bfae41ee5e33c689fded70c89cc64c",
                                                "69bfae41ee5e33c689fded70c89cc64c")
        self._readSettings()

        self._tool_hints_visible:   bool = False
        self._filter_hints_visible: bool = False
        self.slice_view_showing:    bool = False

        # Appearance pref
        if not app().prefs.show_icon_labels:
            self.main_toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # Outliner & PropertyEditor setup
        self.outliner_widget.configure(window=self, document=document)
        self.property_widget.configure(window=self, document=document)

        self.property_buttonbox.setVisible(False)

        self.tool_managers: List[AbstractToolManager] = []  # initialize

        self.views: Dict[EnumType, GraphicsViewT] = {
            # ViewSendEnum.SLICE: self._initSliceview(document)
            # ViewSendEnum.GRID:  self._initGridview(document)
            # ViewSendEnum.PATH:  self._initPathview(document)
        }
        self.views[ViewSendEnum.SLICE] = self._initSliceview(document)
        self.views[ViewSendEnum.GRID] = self._initGridview(document)
        self.views[ViewSendEnum.PATH] =  self._initPathview(document)

        self._initToolbar()
        self._initEditMenu()

        self.path_dock_widget.setTitleBarWidget(QWidget())
        self.grid_dock_widget.setTitleBarWidget(QWidget())
        self.slice_dock_widget.setTitleBarWidget(QWidget())
        self.inspector_dock_widget.setTitleBarWidget(QWidget())

        self.setCentralWidget(None)
        if app().prefs.orthoview_style_idx == OrthoViewEnum.SLICE:
            self.splitDockWidget(self.slice_dock_widget, self.path_dock_widget, Qt.Horizontal)
        elif app().prefs.orthoview_style_idx == OrthoViewEnum.GRID:
            self.splitDockWidget(self.grid_dock_widget, self.path_dock_widget, Qt.Horizontal)
        self._restoreGeometryandState()
        self._finishInit()

        document.setViewNames(['slice', 'path', 'inspector'])

        # Set Default Filter
        if DEFAULT_VHELIX_FILTER:
            self.actionFilterVirtualHelixSlot()
        else:
            self.actionFilterEndpointSlot()
            self.actionFilterXoverSlot()

                # setup tool exclusivity
        self.actiongroup: QActionGroup = QActionGroup(self)
        ag = self.actiongroup
        action_group_list: List[str] = [
            'action_global_select',
            'action_global_create',
            'action_path_break',
            'action_path_paint',
            'action_path_insertion',
            'action_path_skip',
            'action_path_add_seq',
            'action_path_mods'
        ]
        for action_name in action_group_list:
            ag.addAction(getattr(self, action_name))

        if IS_TESTING:
            # ADDED SPECIAL NC for testing with keyboard shortcut:
            action_special = QAction(self)
            action_special.setObjectName("action_special")
            action_special.setText(_translate("MainWindow", "Special"))
            action_special.setShortcut(_translate("MainWindow", "Ctrl+J"))
            self.action_special = action_special
            self.menu_edit.addAction(action_special)
            action_special.triggered.connect(self.actionSpecialSlot)

        # set up tool & filter hinting
        # filters that display alt icon when disabled
        self._hintable_tools: List[QAction] = [
            self.action_global_create,
            self.action_global_select
        ]
        self._hintable_filters: List[QAction] = [
            self.action_filter_helix,
            self.action_filter_strand,
            self.action_filter_endpoint,
            self.action_filter_xover
        ]
        # what buttons to hint for each filter
        self._hintable_tool_action_map: Dict[str, QAction] = {
            'create': [self.action_global_create],
            'select': [self.action_global_select]
        }

        self._hintable_filter_action_map: Dict[str, QAction] = {
            'virtual_helix': [self.action_filter_helix],
            'strand': [self.action_filter_strand],
            'endpoint': [self.action_filter_endpoint],
            'xover': [self.action_filter_xover]
        }

        self.action_global_select.trigger()
        # self.inspector_dock_widget.hide()

        self.exit_when_done: bool = False
        self.closeEvent: MethodType = self.windowCloseEventHandler
        self.show()
        app().documentWindowWasCreatedSignal.emit(document, self)
    # end def

    def document(self) -> DocT:
        return self._document

    def destroyWin(self):
        '''Save window state and destroy the tool managers.  Also destroy
        :class`DocumentController` object
        '''
        self.settings.beginGroup("MainWindow")
        # Saves the current state of this mainwindow's toolbars and dockwidgets
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()
        for mgr in self.tool_managers:
            mgr.destroyItem()
        self.tool_managers = []

    ### ACCESSORS ###
    def undoStack(self) -> UndoStack:
        return self._document.undoStack()

    def activateSelection(self, is_active: bool):
        self.path_graphics_view.activateSelection(is_active)
        self.slice_graphics_view.activateSelection(is_active)
        self.grid_graphics_view.activateSelection(is_active)

    ### EVENT HANDLERS ###
    def focusInEvent(self):
        """Handle an OS focus change into cadnano."""
        app().undoGroup.setActiveStack(self.undoStack())

    def moveEvent(self, event: QMoveEvent):
        """Handle the moving of the cadnano window itself.

        Reimplemented to save state on move.
        """
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()

    def resizeEvent(self, event: QResizeEvent):
        """Handle the resizing of the cadnano window itself.

        Reimplemented to save state on resize.
        """
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("size", self.size())
        self.settings.endGroup()
        QWidget.resizeEvent(self, event)

    def changeEvent(self, event: QEvent):
        QWidget.changeEvent(self, event)

    # end def

    ### DRAWING RELATED ###

    ### PRIVATE HELPER METHODS ###
    def _restoreGeometryandState(self):
        settings = self.settings
        settings.beginGroup("MainWindow")
        geometry = settings.value("geometry")
        if geometry is not None:
            result = self.restoreGeometry(geometry)
            if result is False:
                print("MainWindow.restoreGeometry() failed.")
        else:
            print("Setting default MainWindow size: 1100x800")
            self.resize(settings.value("size", QSize(1100, 800)))
            self.move(settings.value("pos", QPoint(200, 200)))
            self.inspector_dock_widget.close()
            self.action_inspector.setChecked(False)

        # Restore the current state of this mainwindow's toolbars and dockwidgets
        window_state = settings.value("windowState")
        if window_state is not None:
            result = self.restoreState(window_state)
            if result is False:
                print("MainWindow.restoreState() failed.")
        settings.endGroup()
    # end def

    def destroyView(self, view_type: EnumType):
        '''
        Args:
            view_type: the name of the view

        Raises:
            ValueError for :obj:`view_type` not existing
        '''
        cnview = self.views.get(view_type)
        if cnview is not None:
            root_item = cnview.rootItem()
            root_item.destroyViewItems()
        else:
            raise ValueError("view_type: %s does not exist" % (view_type))

    def rebuildView(self, view_type: EnumType):
        '''Rebuild views which match view_type ORed argument.
        Only allows SLICE or GRID view to be active.  Not both at the same time

        Args:
            view_type: one or more O
        '''
        doc: DocT = self.document()

        # turn OFF all but the views we care about
        doc.changeViewSignaling(view_type)

        delta: EnumType = 0
        if view_type & ViewSendEnum.SLICE:
            delta = ViewSendEnum.GRID
            self.destroyView(delta)
        elif view_type & ViewSendEnum.GRID:
            delta = ViewSendEnum.GRID
            self.destroyView(delta)

        for part in doc.getParts():
            reEmitPart(part)

        # turn ON all but the views we care about
        doc.changeViewSignaling(ViewSendEnum.ALL - delta)
    # end def

    def _initGridview(self, doc: DocT) -> GraphicsViewT:
        """Initializes Grid View.

        Args:
            doc: The :class:`Document` corresponding to the design

        Returns:
            :class:`CNGraphicsView`
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
        return ggv
    # end def

    def _initPathview(self, doc: DocT) -> GraphicsViewT:
        """Initializes Path View.

        Args:
            doc: The :class:`Document` corresponding to the design

        Returns:
            :class:`CNGraphicsView`
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
        return pgv
    # end def

    def _initToolbar(self):
        """Initializes the Toolbar and the manager.
        """
        self.path_color_panel = ColorPanel()
        self.path_graphics_view.toolbar = self.path_color_panel  # HACK for cngraphicsview
        path_view = self.views[ViewSendEnum.PATH]
        path_scene = path_view.cnScene()
        path_scene.addItem(self.path_color_panel)
        self.path_tool_manager = PathToolManager(self, path_view.rootItem())

        self.slice_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.slice_tool_manager = self.slice_tool_manager

        self.grid_tool_manager.path_tool_manager = self.path_tool_manager
        self.path_tool_manager.grid_tool_manager = self.grid_tool_manager

        self.tool_managers = [self.path_tool_manager, self.slice_tool_manager, self.grid_tool_manager]

        self.insertToolBarBreak(self.main_toolbar)

        self.path_graphics_view.setupGL()
        self.slice_graphics_view.setupGL()
        self.grid_graphics_view.setupGL()
    # end def

    def _initSliceview(self, doc: DocT) -> GraphicsViewT:
        """Initializes Slice View.

        Args:
            doc: The :class:`Document` corresponding to the design

        Returns:
            :class:`CNGraphicsView`
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
        return sgv
    # end def

    def _initEditMenu(self):
        """Initializes the Edit menu
        """
        us = self.undoStack()
        qatrans = QApplication.translate

        action_undo = us.createUndoAction(self)
        action_undo.setText( qatrans("MainWindow", "Undo", None) )
        action_undo.setShortcut( qatrans("MainWindow", "Ctrl+Z", None) )
        self.actionUndo = action_undo

        action_redo = us.createRedoAction(self)
        action_redo.setText( qatrans("MainWindow", "Redo", None) )
        action_redo.setShortcut( qatrans("MainWindow", "Ctrl+Shift+Z", None) )
        self.actionRedo = action_redo

        self.sep = sep = QAction(self)
        sep.setSeparator(True)

        self.menu_edit.insertAction(sep, action_redo)
        self.menu_edit.insertAction(action_redo, action_undo)
        # print([x.text() for x in self.menu_edit.actions()])

        # self.main_splitter.setSizes([400, 400, 180])  # balance main_splitter size
        self.statusBar().showMessage("")
    # end def

    def _finishInit(self):
        """Handle the dockwindow visibility and action checked status.
        The console visibility is explicitly stored in the settings file,
        since it doesn't seem to work if we treat it like a normal dock widget.
        """
        inspector_visible = self.inspector_dock_widget.isVisibleTo(self)
        self.action_inspector.setChecked(inspector_visible)
        path_visible = self.path_dock_widget.isVisibleTo(self)
        self.action_path.setChecked(path_visible)
        slice_visible = self.slice_dock_widget.isVisibleTo(self)

        # NOTE THIS IS ALWAYS FALSE FOR  SOME REASON
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
        for view in self.views.values():
            if view.underMouse():
                root_item = view.rootItem()
                # print("I am under mouse", view)
                if root_item.manager.isToolActive(tool_type_name):
                    # print("{} is active".format(tool_type_name))
                    return_tool = root_item.manager.activeToolGetter()
                else:
                    # print("no {} HERE!".format(tool_type_name))
                    pass
                break
        return return_tool
    # end def

    def doMouseViewDestroy(self):
        """Destroy the view the mouse is over
        """
        return_tool = None
        for name, view in self.views.items():
            if view.underMouse():
                self.destroyView(name)
    # end def

    ##### SLOTS
    def actionSpecialSlot(self):
        self.doMouseViewDestroy()
    # end def

    def actionSelectForkSlot(self):
        self.action_path_select.trigger()
        self.action_vhelix_select.trigger()
    # end def

    def actionCreateForkSlot(self):
        self._document.clearAllSelected()
        self.action_vhelix_create.trigger()
        self.action_path_create.trigger()
    # end def

    def actionVhelixSnapSlot(self, state: bool):
        for item in self.sliceroot.instance_items.values():
            item.griditem.allow_snap = state
    # end def

    def undoStackCleanChangedSlot(self):
        '''The title changes to include [*] on modification.
        Use this when clearing out undostack to set the modified status of
        the document
        '''
        self.setWindowModified(not self.undoStack().isClean())
        self.setWindowTitle(self.documentTitle())
    # end def

    def actionAboutSlot(self):
        '''Displays the about cadnano dialog.'''
        dialog = QDialog()
        dialog_about = Ui_About()  # reusing this dialog, should rename
        dialog.setStyleSheet(
            "QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
        dialog_about.setupUi(dialog)
        dialog.exec_()

    def showFilterHints(self, show_hints: bool, filter_name: str = None):
        '''Changes the appearance of filter buttons in the toolbar to help user
        realize they may not have the correct filters selected to perform a
        desired action. Meant to avoid the case where user clicks and nothing
        happens.

        Buttons (:class:`QAction`s) can automatically display different icons
        depending on state. We use "enabled" state, temporarily disabling the
        :class:`QAction` to toggle its appearance.

        View items should call this method once from a :meth:`mousePressEvent`
        with ``show_hints=True``, and again on :meth:`mouseReleaseEvent` with
        ``show_hints=False``.

        Args:
            show_hints: ``True to show hints, ``False`` to hide hints.
            filter_name: What filter to hint from ``self._hintable_filter_action_map``
        '''
        if filter_name:
            try:
                for f in self._hintable_filter_action_map[filter_name]:
                    if not f.isChecked():  # no need to hint when already checked
                        f.setEnabled(False)  # disable to show hint icon
                        self._filter_hints_visible = True
            except KeyError:
                pass
        elif self._filter_hints_visible:
            for f in self._hintable_filters:
                if f.isEnabled() is False:
                    f.setEnabled(True)  # enable to hide hint icon
            self._filter_hints_visible = False

    def showToolHints(self, show_hints: bool, tool_name: str = None):
        if tool_name:
            try:
                for t in self._hintable_tool_action_map[tool_name]:
                    if not t.isChecked():  # no need to hint when already checked
                        t.setEnabled(False)  # disable to show hint icon
                        self._tool_hints_visible = True
            except KeyError:
                pass
        elif self._tool_hints_visible:
            for t in self._hintable_tools:
                if t.isEnabled() is False:
                    t.setEnabled(True)  # enable to hide hint icon
            self._tool_hints_visible = False
    # end def

    def actionFilterVirtualHelixSlot(self):
        '''Disables all other selection filters when active.'''
        fH = self.action_filter_helix
        fE = self.action_filter_endpoint
        fS = self.action_filter_strand
        fX = self.action_filter_xover
        fH.setChecked(True)
        if fE.isChecked():
            fE.setChecked(False)
        if fS.isChecked():
            fS.setChecked(False)
        if fX.isChecked():
            fX.setChecked(False)
        types = ["virtual_helix"]
        self._document.setFilterSet(types)
    # end def

    def actionFilterEndpointSlot(self):
        '''Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        '''
        fH = self.action_filter_helix
        fE = self.action_filter_endpoint
        fS = self.action_filter_strand
        fX = self.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fS.isChecked() and not fX.isChecked():
            fE.setChecked(True)
            fS.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterStrandSlot(self):
        '''Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        '''
        fH = self.action_filter_helix
        fE = self.action_filter_endpoint
        fS = self.action_filter_strand
        fX = self.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fX.isChecked():
            fS.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterXoverSlot(self):
        '''Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        '''
        fH = self.action_filter_helix
        fE = self.action_filter_endpoint
        fS = self.action_filter_strand
        fX = self.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fS.isChecked():
            fX.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterScafSlot(self):
        '''Remains checked if no other strand-type filter is active.'''
        f_scaf = self.action_filter_scaf
        f_stap = self.action_filter_stap
        if not f_scaf.isChecked() and not f_stap.isChecked():
            f_scaf.setChecked(True)
        self._strandFilterUpdate()

    def actionFilterStapSlot(self):
        '''Remains checked if no other strand-type filter is active.'''
        f_scaf = self.action_filter_scaf
        f_stap = self.action_filter_stap
        if not f_scaf.isChecked() and not f_stap.isChecked():
            f_stap.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionCopySlot(self):
        select_tool = self.getMouseViewTool('select')
        if select_tool is not None and hasattr(select_tool, 'copySelection'):
            print("select_tool is rolling")
            select_tool.copySelection()
    # end def

    def actionPasteSlot(self):
        select_tool = self.getMouseViewTool('select')
        if select_tool is not None and hasattr(select_tool, 'pasteClipboard'):
            select_tool.pasteClipboard()
    # end def

    def actionFilterFwdSlot(self):
        '''Remains checked if no other strand-type filter is active.'''
        f_fwd = self.action_filter_fwd
        f_rev = self.action_filter_rev
        if not f_fwd.isChecked() and not f_rev.isChecked():
            f_fwd.setChecked(True)
        self._strandFilterUpdate()

    def actionFilterRevSlot(self):
        '''Remains checked if no other strand-type filter is active.'''
        f_fwd = self.action_filter_fwd
        f_rev = self.action_filter_rev
        if not f_fwd.isChecked() and not f_rev.isChecked():
            f_rev.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def _strandFilterUpdate(self):
        if self.action_filter_helix.isChecked():
            self._document.setFilterSet(["virtual_helix"])
            return

        filter_list = []
        add_oligo = False
        if self.action_filter_endpoint.isChecked():
            filter_list.append("endpoint")
            add_oligo = True
        if self.action_filter_strand.isChecked():
            filter_list.append("strand")
            add_oligo = True
        if self.action_filter_xover.isChecked():
            filter_list.append("xover")
            add_oligo = True
        if self.action_filter_fwd.isChecked():
            filter_list.append("forward")
            add_oligo = True
        if self.action_filter_rev.isChecked():
            filter_list.append("reverse")
            add_oligo = True
        if self.action_filter_scaf.isChecked():
            filter_list.append("scaffold")
            add_oligo = True
        if self.action_filter_stap.isChecked():
            filter_list.append("staple")
            add_oligo = True
        if add_oligo:
            filter_list.append("oligo")
        self._document.setFilterSet(filter_list)
    # end def

    def actionNewSlot(self):
        '''1. If document is has no parts, do nothing.
        2. If document is dirty, call promptSaveDialog and continue if it succeeds.
        3. Create a new document and swap it into the existing ctrlr/window.
        '''
        # clear/reset the view!

        if len(self._document.children()) == 0:
            return  # no parts
        elif self.promptSaveDialog() is SAVE_DIALOG_OPTIONS['CANCEL']:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if self.filesavedialog is not None:
                self.filesavedialog.finished.connect(self.newClickedCallback)
            else:  # user did not save
                self.newClickedCallback()  # finalize new

    def actionOpenSlot(self):
        '''1. If document is untouched, proceed to open dialog.
        2. If document is dirty, call maybesave and continue if it succeeds.
        3. Downstream, the file is selected in openAfterMaybeSave, and the selected
           file is actually opened in openAfterMaybeSaveCallback.
        '''
        if self.promptSaveDialog() is SAVE_DIALOG_OPTIONS['CANCEL']:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if hasattr(self, "filesavedialog"):  # user did save
                if self.filesavedialog is not None:
                    self.filesavedialog.finished.connect(self.openAfterMaybeSave)
                else:
                    self.openAfterMaybeSave()  # windows
            else:  # user did not save
                self.openAfterMaybeSave()  # finalize new

    def actionCloseSlot(self):
        '''Called when CNMainWindow is closed.

        This method does not do anything as its functionality is implemented by
        windowCloseEventHandler.  windowCloseEventHandler captures all close
        events (including quit signals) while this method captures only close
        window events (i.e. a strict subset of the events that the
        windowCloseEventHandler captures.
        '''
        pass

    def actionSaveSlot(self):
        '''SaveAs if necessary, otherwise overwrite existing file.'''
        if self._has_no_associated_file:
            self.saveFileDialog()
            return
        self.writeDocumentToFile()

    def actionSaveAsSlot(self):
        '''Open a save file dialog so user can choose a name.'''
        self.saveFileDialog()

    def actionSVGSlot(self):
        ''''''
        fname = os.path.basename(str(self.fileName()))
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()

        fdialog = QFileDialog(self,
                              "%s - Save As" % QApplication.applicationName(),
                              directory,
                              "%s (*.svg)" % QApplication.applicationName())
        fdialog.setAcceptMode(QFileDialog.AcceptSave)
        fdialog.setWindowFlags(Qt.Sheet)
        fdialog.setWindowModality(Qt.WindowModal)
        self.svgsavedialog = fdialog
        self.svgsavedialog.filesSelected.connect(self.saveSVGDialogCallback)
        fdialog.open()

    class DummyChild(QGraphicsItem):
        def boundingRect(self):
            return QRect(200, 200)  # self.parentObject().boundingRect()

        def paint(self, painter, option, widget=None):
            pass

    def saveSVGDialogCallback(self, selected: Union[str, list, tuple]):
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".svg"):
            fname += ".svg"
        if self.svgsavedialog is not None:
            self.svgsavedialog.filesSelected.disconnect(self.saveSVGDialogCallback)
            del self.svgsavedialog  # prevents hang
            self.svgsavedialog = None

        generator = QSvgGenerator()
        generator.setFileName(fname)
        generator.setSize(QSize(200, 330))
        generator.setViewBox(QRect(0, 0, 2000, 2000))
        painter = QPainter()

        # Render through scene
        # painter.begin(generator)
        # self.pathscene.render(painter)
        # painter.end()

        # Render item-by-item
        painter = QPainter()
        style_option = QStyleOptionGraphicsItem()
        q = [self.pathroot]
        painter.begin(generator)
        while q:
            graphics_item = q.pop()
            transform = graphics_item.itemTransform(self.sliceroot)[0]
            painter.setTransform(transform)
            if graphics_item.isVisible():
                graphics_item.paint(painter, style_option, None)
                q.extend(graphics_item.childItems())
        painter.end()

    def actionExportSequencesSlot(self):
        '''Triggered by clicking Export Staples button. Opens a file dialog to
        determine where the staples should be saved. The callback is
        exportStaplesCallback which collects the staple sequences and exports
        the file.
        '''
        # Validate that no staple oligos are circular.
        part = self._document.activePart()
        if part is None:
            return
        circ_olgs = part.getCircularOligos()
        if circ_olgs:
            from cadnano.gui.dialogs.ui_warning import Ui_Warning
            dialog = QDialog()
            dialogWarning = Ui_Warning()  # reusing this dialog, should rename
            dialog.setStyleSheet(
                "QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
            dialogWarning.setupUi(dialog)

            locs = ", ".join([o.locString() for o in circ_olgs])
            msg = "Part contains staple loop(s) at %s.\n\nUse the break tool to introduce 5' & 3' ends before exporting. Loops have been colored red; use undo to revert." % locs  # noqa
            dialogWarning.title.setText("Staple validation failed")
            dialogWarning.message.setText(msg)
            for o in circ_olgs:
                o.applyColor(styles.stapColors[0])
            dialog.exec_()
            return

        # Proceed with staple export.
        fname = self.fileName()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(self,
                                                "%s - Export As" % QApplication.applicationName(),
                                                directory,
                                                "(*.txt)")
            self.saveStaplesDialog = None
            self.exportStaplesCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self,
                                  "%s - Export As" % QApplication.applicationName(),
                                  directory,
                                  "(*.txt)")
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.saveStaplesDialog = fdialog
            self.saveStaplesDialog.filesSelected.connect(self.exportStaplesCallback)
            fdialog.open()
    # end def

    def actionPathAddSeqSlot(self):
        pass
        # print("triggered seqslot")
        # ap = self._document.activePart()
        # if ap is not None:
        #     self._document.activePart().setAbstractSequences(emit_signals=True)
    # end def

    def actionPrefsSlot(self):
        app().prefsClicked()
    # end def

    def actionModifySlot(self):
        '''Notifies that part root items that parts should respond to modifier
        selection signals.
        '''

    def actionCreateNucleicAcidPartHoneycomb(self):
        # TODO[NF]:  Docstring
        self.actionCreateNucleicAcidPart(grid_type=GridEnum.HONEYCOMB)

    def actionCreateNucleicAcidPartSquare(self):
        # TODO[NF]:  Docstring
        self.actionCreateNucleicAcidPart(grid_type=GridEnum.SQUARE)

    def actionCreateNucleicAcidPart(self, grid_type: EnumType) -> NucleicAcidPartT:
        # TODO[NF]:  Docstring
        if ONLY_ONE:
            if len(self._document.children()) is not 0:
                if self.promptSaveDialog() is SAVE_DIALOG_OPTIONS['CANCEL']:
                    return
            self.newDocument()
        doc = self._document
        part = doc.createNucleicAcidPart(use_undostack=True, grid_type=grid_type)
        active_part = doc.activePart()
        if active_part is not None:
            active_part.setActive(False)
            doc.deactivateActivePart()
        part.setActive(True)
        doc.setActivePart(part)
        return part
    # end def

    def actionToggleSliceViewSlot(self):
        '''Handle the action_slice button being clicked.

        If either the slice or grid view are visible hide them.  Else, revert
        to showing whichever view(s) are showing.
        '''
        if self.action_slice.isChecked():
        # if not (self.slice_dock_widget.isVisible() or self.grid_dock_widget.isVisible()):
            self.action_slice.setChecked(True)
            if self.slice_view_showing:
                self.toggleSliceView(True)
                self.toggleGridView(False)
            else:
                self.toggleGridView(True)
                self.toggleSliceView(False)
        else:
            self.action_slice.setChecked(False)
            self.toggleSliceView(False)
            self.toggleGridView(False)

    # end def

    def actionTogglePathViewSlot(self):
        dock_window = self.path_dock_widget
        if dock_window.isVisible():
            dock_window.hide()
        else:
            dock_window.show()
    # end def

    def actionToggleInspectorViewSlot(self):
        dock_window = self.inspector_dock_widget
        if dock_window.isVisible():
            dock_window.hide()
        else:
            dock_window.show()
    # end def

    def toggleNewPartButtons(self, is_enabled: bool):
        '''Toggle the AddPart buttons when the active part changes.

        Args:
            is_enabled:
        '''
        self.action_new_dnapart_honeycomb.setEnabled(is_enabled)
        self.action_new_dnapart_square.setEnabled(is_enabled)
    # end def

    def setSliceOrGridViewVisible(self, view_type: EnumType):
        '''
        Args:
            view_type: type of view enum

        Raises:
            ValueError for unknown ``view_type``.
        '''
        if view_type == OrthoViewEnum.SLICE:
            self.slice_view_showing = True
        elif view_type == OrthoViewEnum.GRID:
            self.slice_view_showing = False
        else:
            raise ValueError('Invalid orthoview value: %s' % value)
        self.actionToggleSliceViewSlot()
    # end def

    def toggleSliceView(self, show: bool):
        '''Hide or show the slice view based on the given parameter `show`.

        Since calling this method where show=True will cause the SliceView to
        show, ensure that the action_slice button is checked if applicable.

        Args:
            show: Whether the slice view should be hidden or shown

        '''
        assert isinstance(show, bool)

        slice_view_widget = self.slice_dock_widget
        path_view_widget = self.path_dock_widget
        views = self.views
        sgv = views[ViewSendEnum.SLICE]
        if show:
            self.splitDockWidget(slice_view_widget, path_view_widget, Qt.Horizontal)
            # self.splitDockWidget(slice_view_widget, path_view_widget, Qt.Vertical)
            slice_view_widget.show()
            sgv.zoomToFit() # NOTE ZTF for now rather than copying the scale factor
        else:
            slice_view_widget.hide()
    # end def

    def toggleGridView(self, show: bool):
        '''Hide or show the grid view based on the given parameter `show`

        Since calling this method where show=True will cause the SliceView to
        show, ensure that the action_slice button is checked if applicable.

        Args:
            show: Whether the grid view should be hidden or shown
        '''
        assert isinstance(show, bool)
        grid_view_widget = self.grid_dock_widget
        path_view_widget = self.path_dock_widget
        views = self.views
        ggv = views[ViewSendEnum.GRID]
        if show:
            self.splitDockWidget(grid_view_widget, path_view_widget, Qt.Horizontal)
            # self.splitDockWidget(grid_view_widget, path_view_widget, Qt.Vertical)
            grid_view_widget.show()
            ggv.zoomToFit() # NOTE ZTF for now rather than copying the scale factor
        else:
            grid_view_widget.hide()
    # end def

    ### ACCESSORS ###
    def document(self) -> DocT:
        return self._document
    # end def

    def undoStack(self) -> UndoStack:
        return self._document.undoStack()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def newDocument(self, fname: str = None):
        '''Creates a new Document, reusing the DocumentController.
        Tells all of the views to reset and removes all items from
        them
        '''
        if fname is not None and self.fileName() == fname:
            setReopen(True)
        self._document.makeNew()
        self._has_no_associated_file = fname is None
        self.setWindowTitle(self.documentTitle() + '[*]')
    # end def

    def saveFileDialog(self):
        fname = self.fileName()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(self,
                                                "%s - Save As" % QApplication.applicationName(),
                                                directory,
                                                "%s (*.json)" % QApplication.applicationName())
            if isinstance(fname, (list, tuple)):
                fname = fname[0]
            self.writeDocumentToFile(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self,
                                  "%s - Save As" % QApplication.applicationName(),
                                  directory,
                                  "%s (*.json)" % QApplication.applicationName())
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.filesavedialog = fdialog
            self.filesavedialog.filesSelected.connect(self.saveFileDialogCallback)
            fdialog.open()
    # end def

    def _readSettings(self):
        self.settings.beginGroup("FileSystem")
        self._file_open_path = self.settings.value("openpath", QDir().homePath())
        self.settings.endGroup()

    def _writeFileOpenPath(self, path):
        ''''''
        self._file_open_path = path
        self.settings.beginGroup("FileSystem")
        self.settings.setValue("openpath", path)
        self.settings.endGroup()

    ### SLOT CALLBACKS ###
    def actionNewSlotCallback(self):
        '''Gets called on completion of filesavedialog after newClicked's
        promptSaveDialog. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        '''
        if self.filesavedialog is not None:
            self.filesavedialog.finished.disconnect(self.actionNewSlotCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def exportStaplesCallback(self, selected: Union[str, list, tuple]):
        '''Export all staple sequences to selected CSV file.

        Args:
            selected (Tuple, List or str): if a List or Tuple, the filename should
            be the first element
        '''
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        # Return if fname is '', None, or a directory path
        if not fname or fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".txt"):
            fname += ".txt"
        if self.saveStaplesDialog is not None:
            self.saveStaplesDialog.filesSelected.disconnect(self.exportStaplesCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.saveStaplesDialog
            self.saveStaplesDialog = None
        # write the file
        ap = self._document.activePart()
        if ap is not None:
            output = ap.getSequences()
            with open(fname, 'w') as f:
                f.write(output)
    # end def

    def newClickedCallback(self):
        '''Gets called on completion of filesavedialog after newClicked's
        promptSaveDialog. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        '''

        if self.filesavedialog is not None:
            self.filesavedialog.finished.disconnect(self.newClickedCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def openAfterMaybeSaveCallback(self, selected: Union[str, list, tuple]):
        '''Receives file selection info from the dialog created by
        openAfterMaybeSave, following user input.

        Extracts the file name and passes it to the decode method, which
        returns a new document doc, which is then set as the open document
        by newDocument. Calls finalizeImport and disconnects dialog signaling.
        '''
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or fname == '' or os.path.isdir(fname):
            return False
        if not os.path.exists(fname):
            return False
        self._writeFileOpenPath(os.path.dirname(fname))

        self.path_graphics_view.setViewportUpdateOn(False)
        self.slice_graphics_view.setViewportUpdateOn(False)
        self.grid_graphics_view.setViewportUpdateOn(False)

        if ONLY_ONE:
            self.newDocument(fname=fname)

        self._document.readFile(fname)

        self.path_graphics_view.setViewportUpdateOn(True)
        self.slice_graphics_view.setViewportUpdateOn(True)
        self.grid_graphics_view.setViewportUpdateOn(True)

        self.path_graphics_view.update()
        self.slice_graphics_view.update()
        self.grid_graphics_view.update()

        if hasattr(self, "filesavedialog"):  # user did save
            if self.fileopendialog is not None:
                self.fileopendialog.filesSelected.disconnect(self.openAfterMaybeSaveCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.fileopendialog
            self.fileopendialog = None
        self.setFileName(fname)

    def saveFileDialogCallback(self, selected: Union[str, list, tuple]):
        '''If the user chose to save, write to that file.'''
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".json"):
            fname += ".json"
        if self.filesavedialog is not None:
            self.filesavedialog.filesSelected.disconnect(self.saveFileDialogCallback)
            del self.filesavedialog  # prevents hang
            self.filesavedialog = None
        self.writeDocumentToFile(fname)
        self._writeFileOpenPath(os.path.dirname(fname))

        if self.exit_when_done:
            the_app = app()
            # self.destroyDC()
            self.destroyWin()
            if the_app.cnmain_windows:
                the_app.destroyApp()

    ### EVENT HANDLERS ###
    def windowCloseEventHandler(self, event: QCloseEvent = None):
        '''Intercept close events when user attempts to close the window.'''
        dialog_result = self.promptSaveDialog(exit_when_done=True)
        if dialog_result == SAVE_DIALOG_OPTIONS['DISCARD']:
            if event is not None:
                event.accept()
            the_app = app()
            # self.destroyDC()
            self.destroyWin()
            if len(the_app.cnmain_windows) > 0:
                the_app.destroyApp()
        elif event is not None:
            event.ignore()
    # end def

    ### FILE INPUT ##
    def documentTitle(self) -> str:
        fname = os.path.basename(str(self.fileName()))
        if not self.undoStack().isClean():
            fname += '[*]'
        return fname

    def fileName(self) -> str:
        return self._document.fileName()

    def setFileName(self, proposed_fname: str) -> bool:
        if self.fileName() == proposed_fname:
            return True
        self._document.setFileName(proposed_fname)
        self._has_no_associated_file = False
        self.setWindowTitle(self.documentTitle())
        return True

    def openAfterMaybeSave(self):
        '''This is the method that initiates file opening. It is called by
        actionOpenSlot to spawn a QFileDialog and connect it to a callback
        method.
        '''
        path = self._file_open_path
        if util.isWindows():  # required for native looking file window#"/",
            fname = QFileDialog.getOpenFileName(None,
                                                "Open Document", path,
                                                "cadnano1 / cadnano2 Files (*.nno *.json *.c25)")
            self.filesavedialog = None
            self.openAfterMaybeSaveCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self,
                                  "Open Document",
                                  path,
                                  "cadnano1 / cadnano2 Files (*.nno *.json *.c25)")
            fdialog.setAcceptMode(QFileDialog.AcceptOpen)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.fileopendialog = fdialog
            self.fileopendialog.filesSelected.connect(self.openAfterMaybeSaveCallback)
            fdialog.open()
    # end def

    ### FILE OUTPUT ###
    def promptSaveDialog(self, exit_when_done: bool = False):
        '''Save on quit, check if document changes have occurred.

        Returns:
            SAVE_DIALOG_OPTIONS['CANCEL'] or
            SAVE_DIALOG_OPTIONS['DISCARD'] or
            SAVE_DIALOG_OPTIONS['SAVE']
        '''
        if app().dontAskAndJustDiscardUnsavedChanges:
            return SAVE_DIALOG_OPTIONS['DISCARD']
        if not self.undoStack().isClean():    # document dirty?
            savebox = QMessageBox(QMessageBox.Warning, "Application",
                                  "The document has been modified.\nDo you want to save your changes?",
                                  QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                  self,
                                  Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.Sheet)
            savebox.setWindowModality(Qt.WindowModal)
            save = savebox.button(QMessageBox.Save)
            discard = savebox.button(QMessageBox.Discard)
            cancel = savebox.button(QMessageBox.Cancel)
            savebox.setDefaultButton(save)
            savebox.setEscapeButton(cancel)
            save.setShortcut("Ctrl+S")
            discard.setShortcut(QKeySequence("D,Ctrl+D"))
            cancel.setShortcut(QKeySequence("C,Ctrl+C,.,Ctrl+."))
            ret = savebox.exec_()
            del savebox  # manual garbage collection to prevent hang (in osx)
            if ret == QMessageBox.Save:
                self.exit_when_done = exit_when_done
                self.actionSaveAsSlot()
                return SAVE_DIALOG_OPTIONS['SAVE']
            elif ret == QMessageBox.Cancel:
                return SAVE_DIALOG_OPTIONS['CANCEL']
        return SAVE_DIALOG_OPTIONS['DISCARD']

    def writeDocumentToFile(self, filename: str = None):
        if filename is None or filename == '':
            if self._has_no_associated_file:
                return False
            filename = self.fileName()
        try:
            self._document.writeToFile(filename)
        except Exception:
            flags = Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.Sheet
            errorbox = QMessageBox(QMessageBox.Critical,
                                   "cadnano",
                                   "Could not write to '%s'." % filename,
                                   QMessageBox.Ok,
                                   self,
                                   flags)
            errorbox.setWindowModality(Qt.WindowModal)
            errorbox.open()
            raise
            return False
        self.undoStack().setClean()
        self.setFileName(filename)
        return True

    def actionCadnanoWebsiteSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/")

    def actionFeedbackSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/feedback")

    def globalCreateSlot(self):
        self.action_global_create.trigger()

    def defineWindowSignals(self):
        self.docwin_signal_and_slots = [
            (self.action_new.triggered, self.actionNewSlot),
            (self.action_open.triggered, self.actionOpenSlot),
            (self.action_close.triggered, self.actionCloseSlot),
            (self.action_save.triggered, self.actionSaveSlot),
            (self.action_save_as.triggered, self.actionSaveAsSlot),
            (self.action_SVG.triggered, self.actionSVGSlot),
            (self.action_export_staples.triggered, self.actionExportSequencesSlot),
            (self.action_preferences.triggered, self.actionPrefsSlot),
            (self.action_new_dnapart_honeycomb.triggered, self.actionCreateNucleicAcidPartHoneycomb),
            (self.action_new_dnapart_honeycomb.triggered, self.globalCreateSlot),
            (self.action_new_dnapart_square.triggered, self.actionCreateNucleicAcidPartSquare),
            (self.action_new_dnapart_square.triggered, self.globalCreateSlot),
            (self.action_about.triggered, self.actionAboutSlot),
            (self.action_cadnano_website.triggered, self.actionCadnanoWebsiteSlot),
            (self.action_feedback.triggered, self.actionFeedbackSlot),

            # make it so select tool in slice view activation turns on vh filter
            (self.action_global_select.triggered, self.actionSelectForkSlot),
            (self.action_global_create.triggered, self.actionCreateForkSlot),

            (self.action_filter_helix.triggered, self.actionFilterVirtualHelixSlot),
            (self.action_filter_endpoint.triggered, self.actionFilterEndpointSlot),
            (self.action_filter_strand.triggered, self.actionFilterStrandSlot),
            (self.action_filter_xover.triggered, self.actionFilterXoverSlot),
            (self.action_filter_fwd.triggered, self.actionFilterFwdSlot),
            (self.action_filter_rev.triggered, self.actionFilterRevSlot),
            (self.action_filter_scaf.triggered, self.actionFilterScafSlot),
            (self.action_filter_stap.triggered, self.actionFilterStapSlot),
            (self.action_copy.triggered, self.actionCopySlot),
            (self.action_paste.triggered, self.actionPasteSlot),

            (self.action_inspector.triggered, self.actionToggleInspectorViewSlot),
            (self.action_path.triggered, self.actionTogglePathViewSlot),
            (self.action_slice.triggered, self.actionToggleSliceViewSlot),

            (self.action_path_add_seq.triggered, self.actionPathAddSeqSlot),

            (self.action_vhelix_snap.triggered, self.actionVhelixSnapSlot)
        ]
    # end def

    def connectSelfSignals(self):
        for signal, slot in self.docwin_signal_and_slots:
            signal.connect(slot)
        o = self.outliner_widget
        p_e = self.property_widget
        o.itemSelectionChanged.connect(p_e.outlinerItemSelectionChanged)
    # end def

    def disconnectSelfSignals(self):
        for signal, slot in self.docwin_signal_and_slots:
            signal.disconnect(slot)
        o = self.outliner_widget
        p_e = self.property_widget
        o.itemSelectionChanged.disconnect(p_e.outlinerItemSelectionChanged)
    # end def
# end class
