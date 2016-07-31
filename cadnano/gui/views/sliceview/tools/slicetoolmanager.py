"""Summary
"""
from cadnano.gui.views.abstractitems.abstracttoolmanager import AbstractToolManager
from .selectslicetool import SelectSliceTool
from .createslicetool import CreateSliceTool


class SliceToolManager(AbstractToolManager):
    """Manages interactions between the slice widgets/UI and the model.

    Attributes:
        create_tool (CreateSliceTool): Description
        select_tool (SelectSliceTool): Description
        tool_names (tuple): `str` names of tools
    """
    def __init__(self, window, viewroot):
        """
        We store mainWindow because a controller's got to have
        references to both the layer above (UI) and the layer below (model)

        Args:
            window (TYPE): Description
            viewroot (TYPE): Description
        """
        super(SliceToolManager, self).__init__('vhelix', window, viewroot)
        self.tool_names = ('Select', 'Create')
        self.select_tool = SelectSliceTool(self)
        self.create_tool = CreateSliceTool(self)
        self.viewroot.setManager(self)
        self.installTools()
    # end def

    ### SIGNALS ###

    ### SLOTS ###

    def resetTools(self):
        """Calls resetTool on each tool managed by this tool manager.

        Returns:
            TYPE: Description
        """
        self.select_tool.resetTool()
        self.create_tool.resetTool()
    # end def
