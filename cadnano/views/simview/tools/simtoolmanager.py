"""Summary
"""
from cadnano.views.abstractitems.abstracttoolmanager import AbstractToolManager
from .selectsimtool import SelectTool
from .paintsimtool import PaintTool


class SimToolManager(AbstractToolManager):
    """
    Manages the interactions between Sim widgets / UI elements and the model.

    Attributes:
        select_tool (SelectTool): Description
    """

    def __init__(self, window, viewroot):
        """Summary

        Args:
            window (TYPE): Description
            viewroot (TYPE): Description
        """
        super(SimToolManager, self).__init__('sim', window, viewroot)
        self.tool_names = ('Select', 'Paint')
        self.select_tool = SelectTool(self, viewroot)
        # self.pencil_tool = PencilTool(self)
        # self.nick_tool = BreakTool(self)
        # self.insertion_tool = InsertionTool(self)
        # self.skip_tool = SkipTool(self)
        self.paint_tool = PaintTool(self)  # (self, win.path_graphics_view.toolbar)
        # self.add_seq_tool = AddSeqTool(self)
        # self.mods_tool = ModsTool(self)
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

        # if self.lastLocation():
        #     new_active_tool.updateLocation(*self.lastLocation())

        if self._active_tool is not None:
            self._active_tool.setActive(False)

        # if str(new_active_tool) == "select_tool":
        #     self.window.activateSelection(True)
            # self.window.filter_toolbar.show()
        # elif str(new_active_tool) == "paint_tool":
        #     self.window.activateSelection(True)
        #     # self.window.filter_toolbar.show()
        # else:
        #     self.window.activateSelection(False)
        #     # self.window.filter_toolbar.hide()
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

    # def lastLocation(self):
    #     """(SimHelix, posInScene) or None, depending on where
    #     the mouse is (basically, pathHelix and position of
    #     the last event seen by the active tool)
    #     """
    #     if self._active_tool is None:
    #         return None
    #     return self._active_tool.lastLocation()
# end class
