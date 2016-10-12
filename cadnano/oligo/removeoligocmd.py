from cadnano.cnproxy import UndoCommand

class RemoveOligoCommand(UndoCommand):
    def __init__(self, oligo):
        super(RemoveOligoCommand, self).__init__("remove oligo")
        self._oligo = oligo
        self._part = oligo.part()
        self._strand3p = None
    # end def

    def redo(self):
        o = self._oligo
        s5p = o.strand5p()
        part = self._part
        doc = part.document()

        for strand in list(s5p.generator3pStrand()):
            strandset = strand.strandSet()
            doc.removeStrandFromSelection(strand)

            strandset._removeFromStrandList(strand)

            # emit a signal to notify on completion
            strand.strandRemovedSignal.emit(strand)
            # for updating the Slice View displayed helices
            strandset.part().partStrandChangedSignal.emit(strandset.part(), strandset.idNum())
        # end def
        # set the 3p strand for the undo
        self._strand3p = strand
        # o.setPart(None)
        # remove Oligo from part but don't set parent to None?
        part._removeOligoFromSet(o, emit_signals=True)
    # end def

    def undo(self):
        o = self._oligo
        s3p = self._strand3p
        part = self._part

        for strand in list(s3p.generator5pStrand()):
            strandset = strand.strandSet()
            strandset._addToStrandList(strand)

            # Emit a signal to notify on completion
            strandset.strandsetStrandAddedSignal.emit(strandset, strand)
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(strandset.part(),  strandset.idNum())
        # end def

        # add Oligo to part but don't set parent to None?
        # o.setPart(part)
        part._addOligoToSet(o, emit_signals=True)
    # end def
# end class