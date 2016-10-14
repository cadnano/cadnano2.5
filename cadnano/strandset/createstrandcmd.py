# -*- coding: utf-8 -*-
import random

from cadnano import preferences as prefs
from cadnano.cnproxy import UndoCommand
from cadnano.oligo import Oligo
from cadnano.strand import Strand

class CreateStrandCommand(UndoCommand):
    """Create a new `Strand` based with bounds (base_idx_low, base_idx_high),
    and insert it into the strandset at position strandset_idx. Also,
    create a new Oligo, add it to the Part, and point the new Strand
    at the oligo.

    `Strand` explicitly do not create `Oligo` as do to the 1 to many nature of
    Oligos
    """
    def __init__(self,  strandset,
                        base_idx_low, base_idx_high,
                        color,
                        update_segments=True):
        """ TODO: Now that parts have a UUID this could be instantiated via
        a document, uuid, id_num, is_fwd, base_idx_low, ... instead of an object
        to be independent of parts keeping strandsets live
        """
        super(CreateStrandCommand, self).__init__("create strand")
        self._strandset = strandset
        doc = strandset.document()
        self._strand = Strand(strandset, base_idx_low, base_idx_high)
        self._new_oligo = Oligo(None, color, length=self._strand.totalLength())  # redo will set part
        self.update_segments = update_segments
    # end def

    def strand(self):
        return self._strand
    # end def

    def redo(self):
        # Add the new strand to the StrandSet strand_list
        strand = self._strand
        strandset = self._strandset
        strandset._addToStrandList(strand, self.update_segments)
        # Set up the new oligo
        oligo = self._new_oligo
        oligo.setStrand5p(strand)
        strand.setOligo(oligo)

        oligo.addToPart(strandset.part(), emit_signals=True)

        # strand.reapplySequence()
        # Emit a signal to notify on completion
        strandset.strandsetStrandAddedSignal.emit(strandset, strand)
        # for updating the Slice View displayed helices
        strandset.part().partStrandChangedSignal.emit(  strandset.part(),
                                                        strandset.idNum())
    # end def

    def undo(self):
        # Remove the strand from StrandSet strand_list and selectionList
        strand = self._strand
        strandset = self._strandset
        strandset._document.removeStrandFromSelection(strand)
        strandset._removeFromStrandList(strand, self.update_segments)
        # Get rid of the new oligo
        oligo = self._new_oligo
        oligo.setStrand5p(None)
        oligo.removeFromPart(emit_signals=True)
        # Emit a signal to notify on completion
        strand.strandRemovedSignal.emit(strand)
        strand.setOligo(None)
        # for updating the Slice View displayed helices
        strandset.part().partStrandChangedSignal.emit(  strandset.part(),
                                                        strandset.idNum())
    # end def
# end class
