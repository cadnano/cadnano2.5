from cadnano.cnproxy import UndoCommand

class RemoveAllStrandsCommand(UndoCommand):
    """
    1. Remove all strands. Emits strandRemovedSignal for each.
    2. Remove all oligos. 
    """
    def __init__(self, part):
        super(RemoveAllStrandsCommand, self).__init__("remove all strands")
        self._part = part
        self._vhs = vhs = part.getVirtualHelices()
        self._strand_sets = []
        for vh in self._vhs:
            x = vh.getStrandSets()
            self._strand_sets.append(x[0])
            self._strand_sets.append(x[1])
        self._strandSetListCopies = \
                    [[y for y in x._strand_list] for x in self._strand_sets]
        self._oligos = set(part.oligos())
    # end def

    def redo(self):
        part = self._part
        # Remove the strand
        for s_set in self.__strand_set:
            s_list = s_set._strand_list
            for strand in s_list:
                s_set.removeStrand(strand)
            # end for
            s_set._strand_list = []
        #end for
        for vh in self._vhs:
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(part, vh)
        # end for
        self._oligos.clear()
    # end def

    def undo(self):
        part = self._part
        # Remove the strand
        sListCopyIterator = iter(self._strandSetListCopies)
        for s_set in self._strand_sets:
            s_list = next(sListCopyIterator)
            for strand in s_list:
                s_set.strandsetStrandAddedSignal.emit(s_set, strand)
            # end for
            s_set._strand_list = s_list
        #end for
        for vh in self._vhs:
            # for updating the Slice View displayed helices
            part.partStrandChangedSignal.emit(part, vh)
        # end for
        for olg in self._oligos:
            part.addOligo(olg)
    # end def
# end class