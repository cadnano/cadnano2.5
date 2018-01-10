from cadnano.controllers.stranditemcontroller import StrandItemController
from cadnano.views.abstractitems.abstractstranditem import AbstractStrandItem


class StrandItem(AbstractStrandItem):
    def __init__(self, model_strand, virtual_helix_item):
        AbstractStrandItem.__init__(self, model_strand, virtual_helix_item)
        self._model_strand = model_strand
        self._vh_item = virtual_helix_item
        self._controller = StrandItemController(model_strand, self)
    # end def

    def strandResizedSlot(self, strand, indices):
        self._vh_item.resizeStrand3D(strand, indices)
    # end def

    def strandRemovedSlot(self, strand):
        self._controller.disconnectSignals()
        self._controller = None
        self._model_strand = None
        self._vh_item.removeStrand3D(self)
        self._vh_item = None
    # end def

    def strandConnectionChangedSlot(self, strand):
        # print("[simview] strandConnectionChangedSlot")
        self._vh_item.updateStrandConnections3D(strand)
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        # print("[simview] oligoPropertyChangedSlot", key, new_value)
        pass
    # end def

    def strandHasNewOligoSlot(self, strand):
        self._controller.reconnectOligoSignals()
        # strand = self._model_strand
        # self._updateColor(strand)
        # if strand.connection3p():
        #     self.xover_3p_end._updateColor(strand)
        # for insertion in self.insertionItems().values():
        #     insertion.updateItem()
        pass
    # end def

    def strandInsertionAddedSlot(self, strand, insertion):
        print("[simview] strandInsertionAddedSlot", strand, insertion)
    # end def

    def strandInsertionChangedSlot(self, strand, insertion):
        print("[simview] strandInsertionChangedSlot", strand, insertion)
    # end def

    def strandInsertionRemovedSlot(self, strand, index):
        print("[simview] strandInsertionRemovedSlot", strand, index)
    # end def

    def strandSelectedChangedSlot(self, strand, indices):
        # print("[simview] strandSelectedChangedSlot", strand, indices)
        pass
    # end def
