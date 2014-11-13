from cadnano.cnproxy import UndoCommand

class RemoveOligoCommand(UndoCommand):
    def __init__(self,oligo):
        super(RemoveOligoCommand, self).__init__("remove oligo")
        self._oligo = oligo
        self._part = oligo.part()
        self._strand_idx_list = []
        self._strand3p = None
    # end def

    def redo(self):
        s_i_list = self._strand_idx_list
        o = self._oligo
        s5p = o.strand5p()
        part = self._part

        for strand in list(s5p.generator3pStrand()):
            strandset = strand.strandSet()
            strandset._doc.removeStrandFromSelection(strand)
            is_in_set, overlap, sset_idx = strandset._findIndexOfRangeFor(strand)
            s_i_list.append(sset_idx)
            strandset._strand_list.pop(sset_idx)
            # emit a signal to notify on completion
            strand.strandRemovedSignal.emit(strand)
            # for updating the Slice View displayed helices
            strandset.part().partStrandChangedSignal.emit(strandset.part(), strandset.virtualHelix())
        # end def
        # set the 3p strand for the undo
        self._strand3p = strand

        # remove Oligo from part but don't set parent to None?
        # o.removeFromPart()
        part.removeOligo(o)
    # end def

    def undo(self):
        s_i_list = self._strand_idx_list
        o = self._oligo
        s3p = self._strand3p
        part = self._part

        for strand in list(s3p.generator5pStrand()):
            strandset = strand.strandSet()
            sset_idx = s_i_list.pop(-1)
            strandset._strand_list.insert(sset_idx, strand)
            # Emit a signal to notify on completion
            strandset.strandsetStrandAddedSignal.emit(strandset, strand)
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(strandset.part(), strandset.virtualHelix())
        # end def

        # add Oligo to part but don't set parent to None?
        # o.addToPart(part)
        part.addOligo(o)
    # end def
# end class