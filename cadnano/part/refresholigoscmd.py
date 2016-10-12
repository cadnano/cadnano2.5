from cadnano.cnproxy import UndoCommand
from cadnano.strand import Strand

class RefreshOligosCommand(UndoCommand):
    """
    RefreshOligosCommand is a post-processing step for AutoStaple.

    Normally when an xover is created, all strands in the 3' direction are
    assigned the oligo of the 5' strand. This becomes very expensive
    during autoStaple, because the Nth xover requires updating up to N-1
    strands.

    Hence, we disable oligo assignment during the xover creation step,
    and then do it all in one pass at the end with this command.

    This command is meant for non-undoable steps, like file-io.
    """
    def __init__(self, part):
        super(RefreshOligosCommand, self).__init__("refresh oligos")
        self._part = part
    # end def

    def redo(self):
        visited = {}
        part = self._part
        for id_num in part.getIdNums():
            fwd_ss, rev_ss = part.getStrandSets(id_num)
            for strand in rev_ss:
                visited[strand] = False
            for strand in fwd_ss:
                visited[strand] = False

        fSetOligo = Strand.setOligo
        for strand in list(visited.keys()):
            if visited[strand]:
                continue
            visited[strand] = True
            start_oligo = strand.oligo()

            strand5gen = strand.generator5pStrand()
            # this gets the oligo and burns a strand in the generator
            strand5 = next(strand5gen)
            for strand5 in strand5gen:
                oligo5 = strand5.oligo()
                if oligo5 != start_oligo:
                    oligo5.removeFromPart(emit_signals=True)
                    fSetOligo(strand5, start_oligo, emit_signals=True)  # emits strandHasNewOligoSignal
                visited[strand5] = True
            # end for
            start_oligo.setStrand5p(strand5)
            # is it a loop?
            if strand.connection3p() == strand5:
                start_oligo._setLoop(True)
            else:
                strand3gen = strand.generator3pStrand()
                strand3 = next(strand3gen)   # burn one
                for strand3 in strand3gen:
                    oligo3 = strand3.oligo()
                    if oligo3 != start_oligo:
                        oligo3.removeFromPart(emit_signals=True)
                        fSetOligo(strand3, start_oligo, emit_signals=True)  # emits strandHasNewOligoSignal
                    visited[strand3] = True
                # end for
            start_oligo.refreshLength(emit_signals=True)
        # end for

        for strand in visited.keys():
            strand.strandUpdateSignal.emit(strand)
    # end def

    def undo(self):
        """Doesn't reassign """
        pass
    # end def
# end class
