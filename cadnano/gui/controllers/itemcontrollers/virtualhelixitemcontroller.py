class VirtualHelixItemController():
    def __init__(self, virtualhelix_item, model_virtual_helix):
        self._virtual_helix_item = virtualhelix_item
        self._model_virtual_helix = model_virtual_helix
        self.connectSignals()
    # end def

    def connectSignals(self):
        vh_item = self._virtual_helix_item
        mvh = self._model_virtual_helix

        mvh.virtualHelixNumberChangedSignal.connect(vh_item.virtualHelixNumberChangedSlot)
        mvh.virtualHelixRemovedSignal.connect(vh_item.virtualHelixRemovedSlot)
        
        for strandSet in mvh.getStrandSets():
            strandSet.strandsetStrandAddedSignal.connect(vh_item.strandAddedSlot)
            # strandSet.decoratorAddedSignal.connect(vh_item.decoratorAddedSlot)
    # end def

    def disconnectSignals(self):
        vh_item = self._virtual_helix_item
        mvh = self._model_virtual_helix

        mvh.virtualHelixNumberChangedSignal.disconnect(vh_item.virtualHelixNumberChangedSlot)
        mvh.virtualHelixRemovedSignal.disconnect(vh_item.virtualHelixRemovedSlot)

        for strandSet in mvh.getStrandSets():
            strandSet.strandsetStrandAddedSignal.disconnect(vh_item.strandAddedSlot)
            # strandSet.decoratorAddedSignal.disconnect(vh_item.decoratorAddedSlot)