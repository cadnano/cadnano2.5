from cadnano.cnproxy import UndoCommand

class AddModsCommand(UndoCommand):
    def __init__(self, document, strand, idx, mod_id):
        super(AddModsCommand, self).__init__()
        self._strand = strand
        self._id_num = strand.idNum()
        self._idx = idx
        self._mod_id = mod_id
        self.document = document
    # end def

    def redo(self):
        strand = self._strand
        mid = self._mod_id
        part = strand.part()
        idx = self._idx
        part.addModStrandInstance(strand, idx, mid)
        strand.strandModsAddedSignal.emit(strand, self.document, mid, idx)
    # end def

    def undo(self):
        strand = self._strand
        mid = self._mod_id
        part = strand.part()
        idx = self._idx
        part.removeModStrandInstance(strand, idx, mid)
        strand.strandModsRemovedSignal.emit(strand, self.document, mid, idx)
    # end def
# end class

class RemoveModsCommand(UndoCommand):
    def __init__(self, document, strand, idx, mod_id):
        super(RemoveModsCommand, self).__init__()
        self._strand = strand
        self._id_num = strand.idNum()
        self._idx = idx
        self._mod_id = mod_id
        self.document = document
    # end def

    def redo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        idx = self._idx
        part.removeModStrandInstance(strand, idx, mid)
        strand.strandModsRemovedSignal.emit(strand, self.document, mid, idx)
    # end def

    def undo(self):
        strand = self._strand
        isstaple = strand.isStaple()
        mid = self._mod_id
        part = strand.part()
        idx = self._idx
        part.addModStrandInstance(strand, idx, mid)
        strand.strandModsAddedSignal.emit(strand, self.document, mid, idx)
    # end def
# end class
