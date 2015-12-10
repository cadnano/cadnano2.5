import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QActionGroup

from cadnano import app
from cadnano import util

from .selecttool import SelectTool
from .penciltool import PencilTool
from .breaktool import BreakTool
from .insertiontool import InsertionTool
from .skiptool import SkipTool
from .painttool import PaintTool
from .addseqtool import AddSeqTool
from .modstool import ModsTool


class PathToolManager(QObject):
    """
    Manages the interactions between Path widgets / UI elements and the model.
    """
    def __init__(self, win):
        super(PathToolManager, self).__init__()
        self.window = win
        self._active_tool = None
        self._active_part = None
        self.select_tool = SelectTool(self)
        self.pencil_tool = PencilTool(self)
        self.nick_tool = BreakTool(self)
        self.insertion_tool = InsertionTool(self)
        self.skip_tool = SkipTool(self)
        self.paint_tool = PaintTool(self) # (self, win.path_graphics_view.toolbar)
        self.add_seq_tool = AddSeqTool(self)
        self.mods_tool = ModsTool(self)

        def installTool(tool_name, window):
            l_tool_name = tool_name.lower()
            tool_widget = getattr(window, 'action_path_' + l_tool_name)
            tool = getattr(self, l_tool_name + '_tool')
            tool.action_name = 'action_path_' + tool_name

            def clickHandler(self):
                tool_widget.setChecked(True)
                self.setActiveTool(tool)
                if hasattr(tool, 'widgetClicked'):
                    tool.widgetClicked()
            # end def

            select_tool_method_name = 'choose' + tool_name + 'Tool'
            setattr(self.__class__, select_tool_method_name, clickHandler)
            handler = getattr(self, select_tool_method_name)
            tool_widget.triggered.connect(handler)
            return tool_widget
        # end def
        tools = ('Select', 'Pencil', 'Nick', 'Insertion', 'Skip', 'Paint', 'Add_Seq', 'Mods')
        self.ag = QActionGroup(win)
        # Call installTool on every tool
        list(map((lambda tool_name: self.ag.addAction(installTool(tool_name, win))), tools))
        self.ag.setExclusive(True)
        # Select the preferred Startup tool
        startup_tool_name = app().prefs.getStartupToolName()
        getattr(self, 'choose' + startup_tool_name + 'Tool')()

    ### SIGNALS ###
    activeToolChangedSignal = pyqtSignal(str)

    ### SLOTS ###

    ### METHODS ###
    def activePart(self):
        return self._active_part

    def setActivePart(self, part):
        self._active_part = part

    def activeToolGetter(self):
        return self._active_tool

    def setActiveTool(self, new_active_tool):
        if new_active_tool == self._active_tool:
            return

        if self.lastLocation():
            new_active_tool.updateLocation(*self.lastLocation())

        if self._active_tool is not None:
            self._active_tool.setActive(False)

        if str(new_active_tool) == "select_tool":
            self.window.activateSelection(True)
            self.window.selection_toolbar.show()
        elif str(new_active_tool) == "paint_tool":
            self.window.activateSelection(True)
            self.window.selection_toolbar.show()
        else:
            self.window.activateSelection(False)
            self.window.selection_toolbar.hide()
        self._active_tool = new_active_tool
        self._active_tool.setActive(True)
        self.activeToolChangedSignal.emit(self._active_tool.action_name)

    def isSelectToolActive(self):
        if self._active_tool == self.select_tool:
            return True
        return False

    def lastLocation(self):
        """(PathHelix, posInScene) or None, depending on where
        the mouse is (basically, pathHelix and position of
        the last event seen by the active tool)"""
        if self._active_tool is None:
            return None
        return self._active_tool.lastLocation()
# end class
