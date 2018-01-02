
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
        print("[simview] strandResizedSlot")
        self._vh_item.strandResized(strand, indices)
    # end def

    def strandRemovedSlot(self, strand):
        print("[simview] strandRemovedSlot")
        self._vh_item.strandRemoved(strand)
    # end def

    def strandUpdateSlot(self, strand):
        print("[simview] strandUpdateSlot")
        self._vh_item.strandUpdate(strand)
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        print("[simview] oligoPropertyChangedSlot", key, new_value)
    # end def

    def strandHasNewOligoSlot(self, strand):
        strand = self._model_strand
        self._controller.reconnectOligoSignals()
        # self._updateColor(strand)
        print("[simview] strandHasNewOligoSlot", strand)
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
        print("[simview] strandSelectedChangedSlot", strand, indices)
    # end def
