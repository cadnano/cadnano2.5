import cadnano.util as util
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QActionGroup

class SliceToolManager(QObject):
    """Manages interactions between the slice widgets/UI and the model."""
    def __init__(self, win):
        """
        We store mainWindow because a controller's got to have
        references to both the layer above (UI) and the layer below (model)
        """
        super(SliceToolManager, self).__init__()
        self._window = win
        self._connectWindowSignalsToSelf()

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
        part = self._window.selectedPart()
        if part != None:
            part.setActiveBaseIndex(0)

    def activeSliceLastSlot(self):
        part = self._window.selectedPart()
        if part != None:
            part.setActiveBaseIndex(part.maxBaseIdx()-1)

    ### METHODS ###
    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by SliceToolManager"""
        self._window.action_slice_first.triggered.connect(self.activeSliceFirstSlot)
        self._window.action_slice_last.triggered.connect(self.activeSliceLastSlot)
