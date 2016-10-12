# -*- coding: utf-8 -*-
import random

from cadnano import preferences as prefs
from cadnano.cnproxy import UndoCommand
from cadnano.strand import Strand

class SplitCommand(UndoCommand):
    """ The SplitCommand takes as input a strand and "splits" the strand in
    two, such that one new strand 3' end is at base_idx, and the other
    new strand 5' end is at base_idx +/- 1 (depending on the direction
    of the strands).

    Under the hood:
    On redo, this command actually is creates two new copies of the
    original strand, resizes each and modifies their connections.
    On undo, the new copies are removed and the original is restored.
    """
    def __init__(self, strand, base_idx, update_sequence=True):
        super(SplitCommand, self).__init__("split strand")
        # Store inputs
        self._old_strand = strand
        old_sequence  = strand._sequence
        is5to3 = strand.isForward()

        self._s_set = s_set = strand.strandSet()
        self._old_oligo = oligo = strand.oligo()
        # Create copies
        self.strand_low = strand_low = strand.shallowCopy()
        self.strand_high = strand_high = strand.shallowCopy()

        if oligo.isLoop():
            self._l_oligo = self._h_oligo = l_oligo = h_oligo = oligo.shallowCopy()
        else:
            self._l_oligo = l_oligo = oligo.shallowCopy()
            self._h_oligo = h_oligo = oligo.shallowCopy()

        color_list = prefs.STAP_COLORS


        # Determine oligo retention based on strand priority
        if is5to3:  # strand_low has priority
            i_new_low = base_idx
            color_low = oligo.getColor()
            color_high = random.choice(color_list)
            olg5p, olg3p = l_oligo, h_oligo
            std5p, std3p = strand_low, strand_high
        else:  # strand_high has priority
            i_new_low = base_idx - 1
            color_low = random.choice(color_list)
            color_high = oligo.getColor()
            olg5p, olg3p = h_oligo, l_oligo
            std5p, std3p = strand_high, strand_low
        # this is for updating a connected xover view object
        # there is only ever one xover a strand is in charge of
        self._strand3p = std3p
        self._strand5p = std5p

        # Update strand connectivity
        strand_low.setConnectionHigh(None)
        strand_high.setConnectionLow(None)

        # Resize strands and update decorators
        strand_low.setIdxs((strand.lowIdx(), i_new_low))
        strand_high.setIdxs((i_new_low + 1, strand.highIdx()))

        # Update the oligo for things like its 5prime end and isLoop
        olg5p._strandSplitUpdate(std5p, std3p, olg3p, strand)

        if not oligo.isLoop():
            # Update the oligo color if necessary
            l_oligo._setColor(color_low)
            h_oligo._setColor(color_high)
            # settle the oligo length
            length = 0
            for strand in std3p.generator3pStrand():
                length += strand.totalLength()
            # end for
            olg5p._setLength(olg5p.length() - length, emit_signals=True)
            olg3p._setLength(length, emit_signals=True)
        # end if

        if update_sequence and old_sequence:
            if is5to3:  # strand_low has priority
                tL = strand_low.totalLength()
                strand_low._sequence = old_sequence[0:tL]
                strand_high._sequence = old_sequence[tL:]
            else:
                tH = strand_high.totalLength()
                strand_high._sequence = old_sequence[0:tH]
                strand_low._sequence = old_sequence[tH:]

    # end def

    def redo(self):
        ss = self._s_set
        s_low = self.strand_low
        s_high = self.strand_high
        o_strand = self._old_strand
        # idx = self._s_set_idx
        olg = self._old_oligo
        doc = ss.document()
        l_olg = self._l_oligo
        h_olg = self._h_oligo
        was_not_loop = l_olg != h_olg

        # Remove old Strand from the s_set
        ss._removeFromStrandList(o_strand, update_segments=False)

        # Add new strands to the s_set (reusing idx, so order matters)
        ss._addToStrandList(s_high, update_segments=False)
        ss._addToStrandList(s_low)

        # update connectivity of strands
        sLcL = s_low.connectionLow()
        if sLcL:
            if ( (o_strand.isForward() and sLcL.isForward()) or
                (not o_strand.isForward() and not sLcL.isForward()) ):
                sLcL.setConnectionHigh(s_low)
            else:
                sLcL.setConnectionLow(s_low)
        sHcH = s_high.connectionHigh()
        if sHcH:
            if ( (o_strand.isForward() and sHcH.isForward()) or
                (not o_strand.isForward() and not sHcH.isForward()) ):
                sHcH.setConnectionLow(s_high)
            else:
                sHcH.setConnectionHigh(s_high)

        # Traverse the strands via 3'conns to assign the new oligos
        fSetOligo = Strand.setOligo
        for strand in l_olg.strand5p().generator3pStrand():
            fSetOligo(strand, l_olg)  # emits strandHasNewOligoSignal
        if was_not_loop:  # do the second oligo which is different
            for strand in h_olg.strand5p().generator3pStrand():
                # emits strandHasNewOligoSignal
                fSetOligo(strand, h_olg)

        # Add new oligo and remove old oligos from the part
        olg.removeFromPart(emit_signals=True)
        l_olg.addToPart(s_low.part(), emit_signals=True)
        if was_not_loop:
            h_olg.addToPart(s_high.part(), emit_signals=True)

        # Emit Signals related to destruction and addition
        o_strand.strandRemovedSignal.emit(o_strand)
        ss.strandsetStrandAddedSignal.emit(ss, s_high)
        ss.strandsetStrandAddedSignal.emit(ss, s_low)
    # end def

    def undo(self):
        ss = self._s_set
        s_low = self.strand_low
        s_high = self.strand_high
        o_strand = self._old_strand
        # idx = self._s_set_idx
        olg = self._old_oligo
        doc = ss.document()
        l_olg = self._l_oligo
        h_olg = self._h_oligo
        was_not_loop = l_olg != h_olg

        # Remove new strands from the s_set (reusing idx, so order matters)
        ss._removeFromStrandList(s_low, update_segments=False)
        ss._removeFromStrandList(s_high, update_segments=False)
        # Add the old strand to the s_set
        ss._addToStrandList(o_strand)

        # update connectivity of strands
        oScL = o_strand.connectionLow()
        if oScL:
            if ( (o_strand.isForward() and oScL.isForward()) or
                (not o_strand.isForward() and not oScL.isForward()) ):
                oScL.setConnectionHigh(o_strand)
            else:
                oScL.setConnectionLow(o_strand)
        oScH = o_strand.connectionHigh()
        if oScH:
            if ( (o_strand.isForward() and oScH.isForward()) or
                (not o_strand.isForward() and not oScH.isForward()) ):
                oScH.setConnectionLow(o_strand)
            else:
                oScH.setConnectionHigh(o_strand)

        # Traverse the strands via 3'conns to assign the old oligo
        fSetOligo = Strand.setOligo
        for strand in olg.strand5p().generator3pStrand():
            fSetOligo(strand, olg)
        # Add old oligo and remove new oligos from the part
        olg.addToPart(ss.part(), emit_signals=True)
        l_olg.removeFromPart(emit_signals=True)
        if was_not_loop:
            h_olg.removeFromPart(emit_signals=True)

        # Emit Signals related to destruction and addition
        s_low.strandRemovedSignal.emit(s_low)
        s_high.strandRemovedSignal.emit(s_high)
        ss.strandsetStrandAddedSignal.emit(ss, o_strand)
    # end def
# end class
