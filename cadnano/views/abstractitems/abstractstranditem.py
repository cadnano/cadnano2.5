

class AbstractStrandItem(object):
    def __init__(self, model_strand=None, virtual_helix_item=None):
        """The parent should be a VirtualHelixItem."""
        if self.__class__ == AbstractStrandItem:
            raise NotImplementedError("AbstractStrandItem should be subclassed.")
        self._model_strand = None
        self._model_vh = None
        self._model_oligo = None

    ### SIGNALS ###

    def strandHasNewOligoSlot(self, strand):
        pass
    # end def

    def strandRemovedSlot(self, strand):
        pass
    # end def

    def strandResizedSlot(self, strand, indices):
        pass
    # end def

    def strandXover5pRemovedSlot(self, strand3p, strand5p):
        pass
    # end def

    def strandConnectionChangedSlot(self, strand):
        pass
    # end def

    def strandInsertionAddedSlot(self, strand, insertion):
        pass
    # end def

    def strandInsertionChangedSlot(self, strand, insertion):
        pass
    # end def

    def strandInsertionRemovedSlot(self, strand, index):
        pass
    # end def

    def strandModsAddedSlot(self, strand, document, mod_id, idx):
        pass
    # end def

    def strandModsChangedSlot(self, strand, document, mod_id, idx):
        pass
    # end def

    def strandModsRemovedSlot(self, strand, document, mod_id, idx):
        pass
    # end def

    def strandSelectedChangedSlot(self, strand, indices):
        pass
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        pass
    # end def

    def oligoSequenceAddedSlot(self, oligo):
        pass
    # end def

    def oligoSequenceClearedSlot(self, oligo):
        pass
    # end def

    def oligoSelectedChangedSlot(self, oligo, new_value):
        pass
    # end def
