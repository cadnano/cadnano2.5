# -*- coding: utf-8 -*-
from cadnano.cntypes import (
    ValueT,
    DocT,
    OligoT,
    StrandT,
    SegmentT,
    InsertionT
)
class AbstractStrandItem(object):
    def __init__(self, strand=None, virtual_helix_item=None):
        """The parent should be a VirtualHelixItem."""
        if self.__class__ == AbstractStrandItem:
            raise NotImplementedError("AbstractStrandItem should be subclassed.")
        self._model_strand = None
        self._model_oligo = None
    # end def

    def strand(self) -> StrandT:
        return self._model_strand
    # end def

    def setProperty(self, key: str, value: ValueT):
        self._model_strand.setProperty(key, value)
    # end def

    def getProperty(self, key: str) -> ValueT:
        self._model_strand.getProperty(key)
    # end def

    ### SIGNALS ###

    def strandHasNewOligoSlot(self, strand: StrandT):
        pass
    # end def

    def strandRemovedSlot(self, strand: StrandT):
        pass
    # end def

    def strandResizedSlot(self, strand: StrandT, indices: SegmentT):
        pass
    # end def

    def strandXover5pRemovedSlot(self, strand3p: StrandT, strand5p: StrandT):
        pass
    # end def

    def strandConnectionChangedSlot(self, strand: StrandT):
        pass
    # end def

    def strandInsertionAddedSlot(self, strand: StrandT, insertion: InsertionT):
        pass
    # end def

    def strandInsertionChangedSlot(self, strand: StrandT, insertion: InsertionT):
        pass
    # end def

    def strandInsertionRemovedSlot(self, strand: StrandT, idx: int):
        pass
    # end def

    def strandModsAddedSlot(self, strand: StrandT, document: DocT, mod_id: str, idx: int):
        pass
    # end def

    def strandModsChangedSlot(self, strand: StrandT, document: DocT, mod_id: str, idx: int):
        pass
    # end def

    def strandModsRemovedSlot(self, strand: StrandT, document: DocT, mod_id: str, idx: int):
        pass
    # end def

    def strandSelectedChangedSlot(self, strand: StrandT, indices: SegmentT):
        pass
    # end def

    def oligoPropertyChangedSlot(self, oligo: OligoT, key: str, new_value: ValueT):
        pass
    # end def

    def oligoSequenceAddedSlot(self, oligo: OligoT):
        pass
    # end def

    def oligoSequenceClearedSlot(self, oligo: OligoT):
        pass
    # end def

    def oligoSelectedChangedSlot(self, oligo: OligoT, new_value: ValueT):
        pass
    # end def
