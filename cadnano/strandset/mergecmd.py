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
    def __init__(self, strand_low, strand_high, low_strandset_idx, priority_strand):
        super(MergeCommand, self).__init__("merge strands")
        # Store strands
        self._strand_low = strand_low
        self._strand_high = strand_high
        pS = priority_strand
        self._s_set = s_set = pS.strandSet()
        # Store oligos
        self._new_oligo = pS.oligo().shallowCopy()
        self._s_low_oligo = sLOlg = strand_low.oligo()
        self._s_high_oligo = sHOlg = strand_high.oligo()

        self._s_set_idx = low_strandset_idx

        # update the new oligo length if it's not a loop
        if sLOlg != sHOlg:
            self._new_oligo.setLength(sLOlg.length() + sHOlg.length())

        # Create the new_strand by copying the priority strand to
        # preserve its properties
        new_idxs = strand_low.lowIdx(), strand_high.highIdx()
        new_strand = strand_low.shallowCopy()
        new_strand.setIdxs(new_idxs)
        new_strand.setConnectionHigh(strand_high.connectionHigh())
        # Merging any decorators
        new_strand.addDecorators(strand_high.decorators())
        self._new_strand = new_strand
        # Update the oligo for things like its 5prime end and isLoop
        self._new_oligo.strandMergeUpdate(strand_low, strand_high, new_strand)
        
        # set the new sequence by concatenating the sequence properly
        if strand_low._sequence or strand_high._sequence:
            tL = strand_low.totalLength()
            tH = strand_high.totalLength()
            seqL = strand_low._sequence if strand_low._sequence else "".join([" " for i in range(tL)])
            seqH = strand_high._sequence if strand_high._sequence else "".join([" " for i in range(tH)])    
            if new_strand.isDrawn5to3():
                new_strand._sequence = seqL + seqH
            else:
                new_strand._sequence = seqH + seqL
    # end def

    def redo(self):
        ss = self._s_set
        doc = ss._doc
        sL = self._strand_low
        sH = self._strand_high
        nS = self._new_strand
        idx = self._s_set_idx
        olg = self._new_oligo
        l_olg = sL.oligo()
        h_olg = sH.oligo()

        # Remove old strands from the s_set (reusing idx, so order matters)
        ss._removeFromStrandList(sL)
        ss._removeFromStrandList(sH)
        # Add the new_strand to the s_set
        ss._addToStrandList(nS, idx)

        # update connectivity of strands
        nScL = nS.connectionLow()
        if nScL:
            if (nS.isDrawn5to3() and nScL.isDrawn5to3()) or \
                (not nS.isDrawn5to3() and not nScL.isDrawn5to3()):
                nScL.setConnectionHigh(nS)
            else:
                nScL.setConnectionLow(nS)
        nScH = nS.connectionHigh()
        if nScH:
            if (nS.isDrawn5to3() and nScH.isDrawn5to3()) or \
                (not nS.isDrawn5to3() and not nScH.isDrawn5to3()):
                nScH.setConnectionLow(nS)
            else:
                nScH.setConnectionHigh(nS)

        # Traverse the strands via 3'conns to assign the new oligo
        for strand in olg.strand5p().generator3pStrand():
            Strand.setOligo(strand, olg)  # emits strandHasNewOligoSignal

        # Add new oligo and remove old oligos
        olg.addToPart(ss.part())
        l_olg.removeFromPart()
        if h_olg != l_olg:  # check if a loop was created
            h_olg.removeFromPart()

        # Emit Signals related to destruction and addition
        sL.strandRemovedSignal.emit(sL)
        sH.strandRemovedSignal.emit(sH)
        ss.strandsetStrandAddedSignal.emit(ss, nS)
    # end def

    def undo(self):
        ss = self._s_set
        doc = ss._doc
        sL = self._strand_low
        sH = self._strand_high
        nS = self._new_strand
        idx = self._s_set_idx
        olg = self._new_oligo
        l_olg = self._s_low_oligo
        h_olg = self._s_high_oligo
        # Remove the new_strand from the s_set
        ss._removeFromStrandList(nS)
        # Add old strands to the s_set (reusing idx, so order matters)
        ss._addToStrandList(sH, idx)
        ss._addToStrandList(sL, idx)

        # update connectivity of strands
        sLcL = sL.connectionLow()
        if sLcL:
            if (sL.isDrawn5to3() and sLcL.isDrawn5to3()) or \
                (not sL.isDrawn5to3() and not sLcL.isDrawn5to3()):
                sLcL.setConnectionHigh(sL)
            else:
                sLcL.setConnectionLow(sL)
        sHcH = sH.connectionHigh()
        if sHcH:
            if (sH.isDrawn5to3() and sHcH.isDrawn5to3()) or \
                (not sH.isDrawn5to3() and not sHcH.isDrawn5to3()):
                sHcH.setConnectionLow(sH)
            else:
                sHcH.setConnectionHigh(sH)

        # Traverse the strands via 3'conns to assign the old oligo
        for strand in l_olg.strand5p().generator3pStrand():
            Strand.setOligo(strand, l_olg)  # emits strandHasNewOligoSignal
        for strand in h_olg.strand5p().generator3pStrand():
            Strand.setOligo(strand, h_olg)  # emits strandHasNewOligoSignal

        # Remove new oligo and add old oligos
        olg.removeFromPart()
        l_olg.addToPart(sL.part())
        if h_olg != l_olg:
            h_olg.addToPart(sH.part())

        # Emit Signals related to destruction and addition
        nS.strandRemovedSignal.emit(nS)
        ss.strandsetStrandAddedSignal.emit(ss, sL)
        ss.strandsetStrandAddedSignal.emit(ss, sH)
    # end def
# end class