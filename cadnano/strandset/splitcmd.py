import random

from cadnano import preferences as prefs
from cadnano.cnproxy import UndoCommand
from cadnano.strand import Strand

class SplitCommand(UndoCommand):
    """
    The SplitCommand takes as input a strand and "splits" the strand in
    two, such that one new strand 3' end is at base_idx, and the other
    new strand 5' end is at base_idx +/- 1 (depending on the direction
    of the strands).

    Under the hood:
    On redo, this command actually is creates two new copies of the
    original strand, resizes each and modifies their connections.
    On undo, the new copies are removed and the original is restored.
    """
    # def __init__(self, strand, base_idx, strandset_idx, update_sequence=True):
    def __init__(self, strand, base_idx, update_sequence=True):
        super(SplitCommand, self).__init__("split strand")
        # Store inputs
        self._old_strand = strand
        old_sequence  = strand._sequence
        is5to3 = strand.isDrawn5to3()
        
        # self._s_set_idx = strandset_idx
        self._s_set = s_set = strand.strandSet()
        self._old_oligo = oligo = strand.oligo()
        # Create copies
        self._strand_low = strand_low = strand.shallowCopy()
        self._strand_high = strand_high = strand.shallowCopy()

        if oligo.isLoop():
            self._l_oligo = self._h_oligo = l_oligo = h_oligo = oligo.shallowCopy()
        else:
            self._l_oligo = l_oligo = oligo.shallowCopy()
            self._h_oligo = h_oligo = oligo.shallowCopy()
        colorList = prefs.STAP_COLORS if s_set.isStaple() \
                                        else prefs.SCAF_COLORS
        # end

        # Determine oligo retention based on strand priority
        if is5to3:  # strand_low has priority
            i_new_low = base_idx
            color_low = oligo.color()
            color_high = random.choice(colorList).name()
            olg5p, olg3p = l_oligo, h_oligo
            std5p, std3p = strand_low, strand_high
        else:  # strand_high has priority
            i_new_low = base_idx - 1
            color_low = random.choice(colorList).name()
            color_high = oligo.color()
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
        olg5p.strandSplitUpdate(std5p, std3p, olg3p, strand)

        if not oligo.isLoop():
            # Update the oligo color if necessary
            l_oligo.setColor(color_low)
            h_oligo.setColor(color_high)
            # settle the oligo length
            length = 0
            for strand in std3p.generator3pStrand():
                length += strand.totalLength()
            # end for
            olg5p.setLength(olg5p.length() - length)
            olg3p.setLength(length)
        # end if

        if update_sequence and old_sequence:
            if is5to3:  # strand_low has priority
                tL = strand_low.totalLength()
                strand_low._sequence = old_sequence[0:tL]
                strand_high._sequence = old_sequence[tL:]
                # print "lenght match 5 to 3", strand_high.totalLength()+tL == len(old_sequence)
                # assert (strand_high.totalLength()+tL == len(old_sequence))
            else:
                tH = strand_high.totalLength()
                strand_high._sequence = old_sequence[0:tH]
                strand_low._sequence = old_sequence[tH:]
                # print "lenght match 3 to 5", strand_low.totalLength()+tH == len(old_sequence)
                # assert (strand_low.totalLength()+tH == len(old_sequence))

    # end def

    def redo(self):
        ss = self._s_set
        s_low = self._strand_low
        s_high = self._strand_high
        o_strand = self._old_strand
        # idx = self._s_set_idx
        olg = self._old_oligo
        doc = ss.document()
        l_olg = self._l_oligo
        h_olg = self._h_oligo
        was_not_loop = l_olg != h_olg

        # Remove old Strand from the s_set
        ss._removeFromStrandList(o_strand)

        # Add new strands to the s_set (reusing idx, so order matters)
        ss._addToStrandList(s_high)
        ss._addToStrandList(s_low)

        # update connectivity of strands
        sLcL = s_low.connectionLow()
        if sLcL:
            if (o_strand.isDrawn5to3() and sLcL.isDrawn5to3()) or \
                (not o_strand.isDrawn5to3() and not sLcL.isDrawn5to3()):
                sLcL.setConnectionHigh(s_low)
            else:
                sLcL.setConnectionLow(s_low)
        sHcH = s_high.connectionHigh()
        if sHcH:
            if (o_strand.isDrawn5to3() and sHcH.isDrawn5to3()) or \
                (not o_strand.isDrawn5to3() and not sHcH.isDrawn5to3()):
                sHcH.setConnectionLow(s_high)
            else:
                sHcH.setConnectionHigh(s_high)

        # Traverse the strands via 3'conns to assign the new oligos
        for strand in l_olg.strand5p().generator3pStrand():
            Strand.setOligo(strand, l_olg)  # emits strandHasNewOligoSignal
        if was_not_loop:  # do the second oligo which is different
            for strand in h_olg.strand5p().generator3pStrand():
                # emits strandHasNewOligoSignal
                Strand.setOligo(strand, h_olg)

        # Add new oligo and remove old oligos from the part
        olg.removeFromPart()
        l_olg.addToPart(s_low.part())
        if was_not_loop:
            h_olg.addToPart(s_high.part())

        # Emit Signals related to destruction and addition
        o_strand.strandRemovedSignal.emit(o_strand)
        ss.strandsetStrandAddedSignal.emit(ss, s_high)
        ss.strandsetStrandAddedSignal.emit(ss, s_low)
    # end def

    def undo(self):
        ss = self._s_set
        s_low = self._strand_low
        s_high = self._strand_high
        o_strand = self._old_strand
        # idx = self._s_set_idx
        olg = self._old_oligo
        doc = ss.document()
        l_olg = self._l_oligo
        h_olg = self._h_oligo
        was_not_loop = l_olg != h_olg

        # Remove new strands from the s_set (reusing idx, so order matters)
        ss._removeFromStrandList(s_low)
        ss._removeFromStrandList(s_high)
        # Add the old strand to the s_set
        ss._addToStrandList(o_strand)

        # update connectivity of strands
        oScL = o_strand.connectionLow()
        if oScL:
            if (o_strand.isDrawn5to3() and oScL.isDrawn5to3()) or \
                (not o_strand.isDrawn5to3() and not oScL.isDrawn5to3()):
                oScL.setConnectionHigh(o_strand)
            else:
                oScL.setConnectionLow(o_strand)
        oScH = o_strand.connectionHigh()
        if oScH:
            if (o_strand.isDrawn5to3() and oScH.isDrawn5to3()) or \
                (not o_strand.isDrawn5to3() and not oScH.isDrawn5to3()):
                oScH.setConnectionLow(o_strand)
            else:
                oScH.setConnectionHigh(o_strand)

        # Traverse the strands via 3'conns to assign the old oligo
        for strand in olg.strand5p().generator3pStrand():
            Strand.setOligo(strand, olg)
        # Add old oligo and remove new oligos from the part
        olg.addToPart(ss.part())
        l_olg.removeFromPart()
        if was_not_loop:
            h_olg.removeFromPart()

        # Emit Signals related to destruction and addition
        s_low.strandRemovedSignal.emit(s_low)
        s_high.strandRemovedSignal.emit(s_high)
        ss.strandsetStrandAddedSignal.emit(ss, o_strand)
    # end def
# end class
