from PyQt5.QtCore import pyqtSignal
from .selectslicetool import SelectSliceTool
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
        self.tool_names = ('Create', 'Select')
        self.create_tool = CreateSliceTool(self)
        self.select_tool = SelectSliceTool(self)
        self.viewroot.setManager(self)
        self.installTools()
        self._connectWindowSignalsToSelf()
    # end def

    ### SIGNALS ###
    activeSliceSetToFirstIndexSignal = pyqtSignal()
    activeSliceSetToLastIndexSignal = pyqtSignal()
    activePartRenumber = pyqtSignal()

    ### SLOTS ###
    def activeSliceFirstSlot(self):
        """
        Use a signal to notify the ActiveSliceHandle to move. A signal is used
        because the SliceToolManager must be instantiated first, and the
        ActiveSliceHandle can later subscribe.
        """
        part = self.window.selectedInstance()
        if part is not None:
            part.setActiveBaseIndex(0)

    def activeSliceLastSlot(self):
        part = self.window.selectedInstance()
        if part is not None:
            part.setActiveBaseIndex(part.maxBaseIdx(0)-1)   # TODO fix this

    ### METHODS ###
    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by SliceToolManager"""
        self.window.action_slice_first.triggered.connect(self.activeSliceFirstSlot)
        self.window.action_slice_last.triggered.connect(self.activeSliceLastSlot)
