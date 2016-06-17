from PyQt5.QtCore import pyqtSignal
from .selectslicetool import SelectSliceTool
from .moveslicetool import MoveSliceTool
from .createslicetool import CreateSliceTool


from cadnano import util
from cadnano.gui.views.abstractitems.abstracttoolmanager import AbstractToolManager

class SliceToolManager(AbstractToolManager):
    """Manages interactions between the slice widgets/UI and the model."""
    def __init__(self, window, viewroot):
        """
        We store mainWindow because a controller's got to have
        references to both the layer above (UI) and the layer below (model)
        """
        super(SliceToolManager, self).__init__('vhelix', window, viewroot)
        self.tool_names = ('Select', 'Create')
        self.select_tool = SelectSliceTool(self)
        self.create_tool = CreateSliceTool(self)
        self.viewroot.setManager(self)
        self.installTools()
        # self._connectWindowSignalsToSelf()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
