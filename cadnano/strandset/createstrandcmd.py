import random

from cadnano import preferences as prefs
from cadnano.cnproxy import UndoCommand
from cadnano.oligo import Oligo
from cadnano.strand import Strand

class CreateStrandCommand(UndoCommand):
    """
    Create a new Strand based with bounds (base_idx_low, base_idx_high),
    and insert it into the strandset at position strandset_idx. Also,
    create a new Oligo, add it to the Part, and point the new Strand
    at the oligo.
    """
    def __init__(self, strandset, base_idx_low, base_idx_high):
        super(CreateStrandCommand, self).__init__("create strand")
        self._strandset = strandset
        # self._s_set_idx = strandset_idx
        doc = strandset.document()
        self._strand = Strand(strandset, base_idx_low, base_idx_high)
        # if strandset.isStaple():
        #     color_list = prefs.STAP_COLORS
        #     color = random.choice(color_list)
        # else:
        #     #prefs.SCAF_COLORS
        color = strandset.part().getProperty('color')
        self._new_oligo = Oligo(None, color)  # redo will set part
        self._new_oligo.setLength(self._strand.totalLength())
    # end def

    def redo(self):
        # Add the new strand to the StrandSet strand_list
        strand = self._strand
        strandset = self._strandset
        strandset._addToStrandList(strand)
        # Set up the new oligo
        oligo = self._new_oligo
        oligo.setStrand5p(strand)
        oligo.addToPart(strandset.part())
        strand.setOligo(oligo)

        # if strandset.isStaple():
        strand.reapplySequence()
        # Emit a signal to notify on completion
        strandset.strandsetStrandAddedSignal.emit(strandset, strand)
        # for updating the Slice View displayed helices
        strandset.part().partStrandChangedSignal.emit(strandset.part(), strandset.idNum())
    # end def

    def undo(self):
        # Remove the strand from StrandSet strand_list and selectionList
        strand = self._strand
        strandset = self._strandset
        strandset._document.removeStrandFromSelection(strand)
        strandset._removeFromStrandList(strand)
        # Get rid of the new oligo
        oligo = self._new_oligo
        oligo.setStrand5p(None)
        oligo.removeFromPart()
        # Emit a signal to notify on completion
        strand.strandRemovedSignal.emit(strand)
        strand.setOligo(None)
        # for updating the Slice View displayed helices
        strandset.part().partStrandChangedSignal.emit(strandset.part(), strandset.idNum())
    # end def
# end class
