"""Summary
"""
from cadnano.gui.views.abstractitems.abstracttoolmanager import AbstractToolManager

from .selecttool import SelectTool
from .penciltool import PencilTool
from .breaktool import BreakTool
from .insertiontool import InsertionTool
from .skiptool import SkipTool
from .painttool import PaintTool
from .addseqtool import AddSeqTool
from .modstool import ModsTool


class PathToolManager(AbstractToolManager):
    """
    Manages the interactions between Path widgets / UI elements and the model.

    Attributes:
        add_seq_tool (AddSeqTool): Description
        insertion_tool (InsertionTool): Description
        mods_tool (ModsTool): Description
        nick_tool (BreakTool): Description
        paint_tool (PaintTool): Description
        pencil_tool (PencilTool): Description
        select_tool (SelectTool): Description
        skip_tool (SkipTool): Description
        tool_names (tuple): Description
    """
    def __init__(self, window, viewroot):
        """Summary

        Args:
            window (TYPE): Description
            viewroot (TYPE): Description
        """
        super(PathToolManager, self).__init__('path', window, viewroot)
        self.tool_names = ('Select', 'Pencil', 'Nick', 'Insertion', 'Skip', 'Paint', 'Add_Seq', 'Mods')
        self.select_tool = SelectTool(self, viewroot)
        self.pencil_tool = PencilTool(self)
        self.nick_tool = BreakTool(self)
        self.insertion_tool = InsertionTool(self)
        self.skip_tool = SkipTool(self)
        self.paint_tool = PaintTool(self)  # (self, win.path_graphics_view.toolbar)
        self.add_seq_tool = AddSeqTool(self)
        self.mods_tool = ModsTool(self)
        self.viewroot.setManager(self)
        self.installTools()
    # end def

    ### SIGNALS ###

    ### SLOTS ###

    ### METHODS ###
    def activePart(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._active_part

    def setActivePart(self, part):
        """Summary

        Args:
            part (TYPE): Description

        Returns:
            TYPE: Description
        """
        self._active_part = part

    def setActiveTool(self, new_active_tool):
        """Summary

        Args:
            new_active_tool (TYPE): Description

        Returns:
            TYPE: Description
        """
        if new_active_tool == self._active_tool:
            return

        if self.lastLocation():
            new_active_tool.updateLocation(*self.lastLocation())

        if self._active_tool is not None:
            self._active_tool.setActive(False)

        if str(new_active_tool) == "select_tool":
            self.window.activateSelection(True)
            # self.window.selection_toolbar.show()
        elif str(new_active_tool) == "paint_tool":
            self.window.activateSelection(True)
            # self.window.selection_toolbar.show()
        else:
            self.window.activateSelection(False)
            # self.window.selection_toolbar.hide()
        self._active_tool = new_active_tool
        self._active_tool.setActive(True)
        self.activeToolChangedSignal.emit(self._active_tool.action_name)

    def isSelectToolActive(self):
        """Summary

        Returns:
            TYPE: Description
        """
        if self._active_tool == self.select_tool:
            return True
        return False

    def lastLocation(self):
        """(PathHelix, posInScene) or None, depending on where
        the mouse is (basically, pathHelix and position of
        the last event seen by the active tool)
        """
        if self._active_tool is None:
            return None
        return self._active_tool.lastLocation()
# end class
