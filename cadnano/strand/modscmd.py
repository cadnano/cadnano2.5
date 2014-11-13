from cadnano.cnproxy import UndoCommand

class AddModsCommand(UndoCommand):
    def __init__(self, strand, idx, mod_id):
        super(AddModsCommand, self).__init__()
        self._strand = strand
        self._coord = strand.virtualHelix().coord()
        self._idx = idx
        self._mod_id = mod_id
    # end def

    def redo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        part.addModInstance(self._coord, self._idx, 
            isstaple, False, mid)
        strand.strandModsAddedSignal.emit(strand, mid, self._idx)
    # end def

    def undo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        part.removeModInstance(self._coord, self._idx, 
            isstaple, False, self._mod_id)
        strand.strandModsRemovedSignal.emit(strand, mid, self._idx)
    # end def
# end class

class RemoveModsCommand(UndoCommand):
    def __init__(self, strand, idx, mod_id):
        super(RemoveModsCommand, self).__init__()
        self._strand = strand
        self._coord = strand.virtualHelix().coord()
        self._idx = idx
        self._mod_id = mod_id
    # end def

    def redo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        part.removeModInstance(self._coord, self._idx, 
            isstaple, False, mid)
        strand.strandModsRemovedSignal.emit(strand, mid, self._idx)
    # end def

    def undo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        part.addModInstance(self._coord, self._idx, 
            isstaple, False, mid)
        strand.strandModsAddedSignal.emit(strand, mid, self._idx)
    # end def
# end class