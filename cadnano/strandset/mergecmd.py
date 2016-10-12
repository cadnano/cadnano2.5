# -*- coding: utf-8 -*-
from cadnano.cnproxy import UndoCommand
from cadnano.strand import Strand

class MergeCommand(UndoCommand):
    """
    This class takes two Strands and merges them.  This Class should be
    private to StrandSet as knowledge of a strandsetIndex outside of this
    of the StrandSet class implies knowledge of the StrandSet
    implementation

    Must pass this two different strands, and nominally one of the strands
    again which is the priority_strand.  The resulting "merged" strand has
    the properties of the priority_strand's oligo.  Decorators are preserved

    the strand_low and strand_high must be presorted such that strand_low
    has a lower range than strand_high

    low_strandset_idx should be known ahead of time as a result of selection
    """
    # def __init__(self, strand_low, strand_high, low_strandset_idx, priority_strand):
    def __init__(self, strand_low, strand_high, priority_strand):
        super(MergeCommand, self).__init__("merge strands")
        # Store strands
        self._strand_low = strand_low
        self._strand_high = strand_high

        self._s_set = s_set = priority_strand.strandSet()
        # Store oligos
        self._new_oligo = priority_strand.oligo().shallowCopy()
        self._s_low_oligo = s_low_olg = strand_low.oligo()
        self._s_high_oligo = s_high_olg = strand_high.oligo()

        # self._s_set_idx = low_strandset_idx

        # update the new oligo length if it's not a loop
        if s_low_olg != s_high_olg:
            self._new_oligo._setLength(s_low_olg.length() + s_high_olg.length(),
                                        emit_signals=True)

        # Create the new_strand by copying the priority strand to
        # preserve its properties
        new_idxs = strand_low.lowIdx(), strand_high.highIdx()
        new_strand = strand_low.shallowCopy()
        new_strand.setIdxs(new_idxs)
        new_strand.setConnectionHigh(strand_high.connectionHigh())

        self._new_strand = new_strand
        # Update the oligo for things like its 5prime end and isLoop
        self._new_oligo._strandMergeUpdate(strand_low, strand_high, new_strand)

        # set the new sequence by concatenating the sequence properly
        if strand_low._sequence or strand_high._sequence:
            tL = strand_low.totalLength()
            tH = strand_high.totalLength()
            seqL = strand_low._sequence if strand_low._sequence else "".join([" " for i in range(tL)])
            seqH = strand_high._sequence if strand_high._sequence else "".join([" " for i in range(tH)])
            if new_strand.isForward():
                new_strand._sequence = seqL + seqH
            else:
                new_strand._sequence = seqH + seqL
    # end def

    def redo(self):
        ss = self._s_set
        doc = ss._document
        s_low = self._strand_low
        s_high = self._strand_high
        new_strand = self._new_strand
        # idx = self._s_set_idx
        olg = self._new_oligo
        l_olg = s_low.oligo()
        h_olg = s_high.oligo()

        fSetOligo = Strand.setOligo

        # Remove old strands from the s_set (reusing idx, so order matters)
        ss._removeFromStrandList(s_low, update_segments=False)
        ss._removeFromStrandList(s_high, update_segments=False)
        # Add the new_strand to the s_set
        ss._addToStrandList(new_strand)

        # update connectivity of strands
        nScL = new_strand.connectionLow()
        if nScL:
            if (new_strand.isForward() and nScL.isForward()) or \
                (not new_strand.isForward() and not nScL.isForward()):
                nScL.setConnectionHigh(new_strand)
            else:
                nScL.setConnectionLow(new_strand)
        nScH = new_strand.connectionHigh()
        if nScH:
            if (new_strand.isForward() and nScH.isForward()) or \
                (not new_strand.isForward() and not nScH.isForward()):
                nScH.setConnectionLow(new_strand)
            else:
                nScH.setConnectionHigh(new_strand)

        # Traverse the strands via 3'conns to assign the new oligo
        for strand in olg.strand5p().generator3pStrand():
            fSetOligo(strand, olg, emit_signals=True)  # emits strandHasNewOligoSignal

        # Add new oligo and remove old oligos
        olg.addToPart(ss.part(), emit_signals=True)
        l_olg.removeFromPart(emit_signals=True)
        if h_olg != l_olg:  # check if a loop was created
            h_olg.removeFromPart(emit_signals=True)

        # Emit Signals related to destruction and addition
        s_low.strandRemovedSignal.emit(s_low)
        s_high.strandRemovedSignal.emit(s_high)
        ss.strandsetStrandAddedSignal.emit(ss, new_strand)
    # end def

    def undo(self):
        ss = self._s_set
        doc = ss._document
        s_low = self._strand_low
        s_high = self._strand_high
        new_strand = self._new_strand

        fSetOligo = Strand.setOligo

        olg = self._new_oligo
        l_olg = self._s_low_oligo
        h_olg = self._s_high_oligo
        # Remove the new_strand from the s_set
        ss._removeFromStrandList(new_strand, update_segments=False)
        # Add old strands to the s_set (reusing idx, so order matters)
        ss._addToStrandList(s_high, update_segments=False)
        ss._addToStrandList(s_low)

        # update connectivity of strands
        sLcL = s_low.connectionLow()
        if sLcL:
            if (s_low.isForward() and sLcL.isForward()) or \
                (not s_low.isForward() and not sLcL.isForward()):
                sLcL.setConnectionHigh(s_low)
            else:
                sLcL.setConnectionLow(s_low)
        sHcH = s_high.connectionHigh()
        if sHcH:
            if (s_high.isForward() and sHcH.isForward()) or \
                (not s_high.isForward() and not sHcH.isForward()):
                sHcH.setConnectionLow(s_high)
            else:
                sHcH.setConnectionHigh(s_high)

        # Traverse the strands via 3'conns to assign the old oligo
        for strand in l_olg.strand5p().generator3pStrand():
            fSetOligo(strand, l_olg, emit_signals=True)  # emits strandHasNewOligoSignal
        for strand in h_olg.strand5p().generator3pStrand():
            fSetOligo(strand, h_olg, emit_signals=True)  # emits strandHasNewOligoSignal

        # Remove new oligo and add old oligos
        olg.removeFromPart(emit_signals=True)
        l_olg.addToPart(s_low.part(), emit_signals=True)
        if h_olg != l_olg:
            h_olg.addToPart(s_high.part(), emit_signals=True)

        # Emit Signals related to destruction and addition
        new_strand.strandRemovedSignal.emit(new_strand)
        ss.strandsetStrandAddedSignal.emit(ss, s_low)
        ss.strandsetStrandAddedSignal.emit(ss, s_high)
    # end def
# end class
