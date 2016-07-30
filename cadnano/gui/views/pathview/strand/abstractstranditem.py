from PyQt5.QtWidgets import QGraphicsPathItem


class AbstractStrandItem(QGraphicsPathItem):
    def __init__(self, parent):
        """The parent should be a VirtualHelixItem."""
        if self.__class__ == AbstractStrandItem:
            raise NotImplementedError("AbstractStrandItem should be subclassed.")
        super(AbstractStrandItem, self).__init__(parent)
        self._strand = None
        self._oligo = None

    ### SIGNALS ###

    ### SLOTS ###
    def oligoAppeareanceChanged(self):
        """docstring for oligoAppeareanceChanged"""
        pass

    def hasNewOligoSlot(self, oligo):
        """docstring for hasNewOligoSlot"""
        self._oligo = oligo
        # redraw

    def strandRemovedSlot(self, strand):
        """docstring for strandRemovedSlot"""
        pass

    ### METHODS ###
    def connectSignals(self):
        self._oligo.appearanceChangedSignal.connect(self.oligoAppeareanceChanged)
        self._strand.strandHasNewOligoSignal.connect(self.hasNewOligoSlot)
        self._strand.destroyedSignal.connect(self.strandRemovedSlot)

    def disconnectSignals(self):
        self._oligo.appearanceChangedSignal.disconnect(self.oligoAppeareanceChanged)
        self._strand.strandHasNewOligoSignal.disconnect(self.hasNewOligoSlot)
        self._strand.destroyedSignal.disconnect(self.strandRemovedSlot)
