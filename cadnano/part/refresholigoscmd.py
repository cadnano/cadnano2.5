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

    if include_scaffold is specified, the scaffold is refreshed as well

    if colors are specified as a tuple of (scaffold_color, staple_color)
    default colors are also applied to the oligos.

    This command is meant for undoable steps, like file-io and autostaple
    """
    def __init__(self, part, include_scaffold=False, colors=None):
        super(RefreshOligosCommand, self).__init__("refresh oligos")
        self._part = part
        self.include_scaffold = include_scaffold
        self.colors = colors
    # end def

    def redo(self):
        visited = {}
        doc = self._part.document()
        for vh in self._part.getVirtualHelices():
            stap_ss = vh.stapleStrandSet()
            for strand in stap_ss:
                visited[strand] = False
            if self.include_scaffold:
                scap_ss = vh.scaffoldStrandSet()
                for strand in scap_ss:
                    visited[strand] = False

        colors = self.colors
        for strand in list(visited.keys()):
            if visited[strand]:
                continue
            visited[strand] = True
            start_oligo = strand.oligo()

            if colors is not None:
                if strand.isStaple():
                    start_oligo.setColor(colors[1])
                else:
                    start_oligo.setColor(colors[0])

            strand5gen = strand.generator5pStrand()
            # this gets the oligo and burns a strand in the generator
            strand5 = next(strand5gen)
            for strand5 in strand5gen:
                oligo5 = strand5.oligo()
                if oligo5 != start_oligo:
                    oligo5.removeFromPart()
                    Strand.setOligo(strand5, start_oligo)  # emits strandHasNewOligoSignal
                visited[strand5] = True
            # end for
            start_oligo.setStrand5p(strand5)
            # is it a loop?
            if strand.connection3p() == strand5:
                start_oligo.setLoop(True)
            else:
                strand3gen = strand.generator3pStrand()
                strand3 = next(strand3gen)   # burn one
                for strand3 in strand3gen:
                    oligo3 = strand3.oligo()
                    if oligo3 != start_oligo:
                        oligo3.removeFromPart()
                        Strand.setOligo(strand3, start_oligo)  # emits strandHasNewOligoSignal
                    visited[strand3] = True
                # end for
            start_oligo.refreshLength()
        # end for

        for strand in visited.keys():
            strand.strandUpdateSignal.emit(strand)
    # end def

    def undo(self):
        """Doesn't reassign """
        pass
    # end def
# end class