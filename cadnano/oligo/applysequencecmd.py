from cadnano.cnproxy import UndoCommand
import cadnano.util as util

class ApplySequenceCommand(UndoCommand):
    def __init__(self, oligo, sequence):
        super(ApplySequenceCommand, self).__init__("apply sequence")
        self._oligo = oligo
        self._new_sequence = sequence
        self._old_sequence = oligo.sequence()
        self._strand_type = oligo._strand5p.strandSet().strandType()
    # end def

    def redo(self):
        olg = self._oligo
        n_s = ''.join(self._new_sequence) if self._new_sequence else None
        n_s_original = self._new_sequence
        oligo_list = [olg]
        for strand in olg.strand5p().generator3pStrand():
            used_seq, n_s = strand.setSequence(n_s)
            # get the compliment ahead of time
            used_seq = util.comp(used_seq) if used_seq else None
            comp_ss = strand.strandSet().complementStrandSet()
            for comp_strand in comp_ss._findOverlappingRanges(strand):
                sub_used_seq = comp_strand.setComplementSequence(used_seq, strand)
                oligo_list.append(comp_strand.oligo())
            # end for
            # as long as the new Applied Sequence is not None
            if n_s == None and n_s_original:
                break
        # end for
        for oligo in oligo_list:
            oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def

    def undo(self):
        olg = self._oligo
        o_s = ''.join(self._old_sequence) if self._old_sequence else None

        oligo_list = [olg]

        for strand in olg.strand5p().generator3pStrand():
            used_seq, o_s = strand.setSequence(o_s)

            # get the compliment ahead of time
            used_seq = util.comp(used_seq) if used_seq else None
            comp_ss = strand.strandSet().complementStrandSet()
            for comp_strand in comp_ss._findOverlappingRanges(strand):
                sub_used_seq = comp_strand.setComplementSequence(used_seq, strand)
                oligo_list.append(comp_strand.oligo())
            # end for
        # for

        for oligo in oligo_list:
            oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def
# end class