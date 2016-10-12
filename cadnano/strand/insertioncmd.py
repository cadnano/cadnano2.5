# -*- coding: utf-8 -*-
from cadnano.cnproxy import UndoCommand
from cadnano.decorators.insertion import Insertion

class AddInsertionCommand(UndoCommand):
    def __init__(self, strand, idx, length):
        super(AddInsertionCommand, self).__init__("add insertion")
        self._strand = strand
        id_num = strand.idNum()
        self._insertions = strand.part().insertions()[id_num]
        self._idx = idx
        self._length = length
        self._insertion = Insertion(idx, length)
        self._comp_strand = \
                    strand.strandSet().complementStrandSet().getStrand(idx)
    # end def

    def redo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertion
        self._insertions[self._idx] = inst
        strand.oligo()._incrementLength(inst.length(), emit_signals=True)
        strand.strandInsertionAddedSignal.emit(strand, inst)
        if c_strand:
            c_strand.oligo()._incrementLength(inst.length(), emit_signals=True)
            c_strand.strandInsertionAddedSignal.emit(c_strand, inst)
    # end def

    def undo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertion
        strand.oligo()._decrementLength(inst.length(), emit_signals=True)
        if c_strand:
            c_strand.oligo()._decrementLength(inst.length(), emit_signals=True)
        idx = self._idx
        del self._insertions[idx]
        strand.strandInsertionRemovedSignal.emit(strand, idx)
        if c_strand:
            c_strand.strandInsertionRemovedSignal.emit(c_strand, idx)
    # end def
# end class

class RemoveInsertionCommand(UndoCommand):
    def __init__(self, strand, idx):
        super(RemoveInsertionCommand, self).__init__("remove insertion")
        self._strand = strand
        self._idx = idx
        id_num = strand.idNum()
        self._insertions = strand.part().insertions()[id_num]
        self._insertion = self._insertions[idx]
        self._comp_strand = \
                    strand.strandSet().complementStrandSet().getStrand(idx)
    # end def

    def redo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertion
        strand.oligo()._decrementLength(inst.length(), emit_signals=True)
        if c_strand:
            c_strand.oligo()._decrementLength(inst.length(), emit_signals=True)
        idx = self._idx
        del self._insertions[idx]
        strand.strandInsertionRemovedSignal.emit(strand, idx)
        if c_strand:
            c_strand.strandInsertionRemovedSignal.emit(c_strand, idx)
    # end def

    def undo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertion
        strand.oligo()._incrementLength(inst.length(), emit_signals=True)
        self._insertions[self._idx] = inst
        strand.strandInsertionAddedSignal.emit(strand, inst)
        if c_strand:
            c_strand.oligo()._incrementLength(inst.length(), emit_signals=True)
            c_strand.strandInsertionAddedSignal.emit(c_strand, inst)
    # end def
# end class

class ChangeInsertionCommand(UndoCommand):
    """
    Changes the length of an insertion to a non-zero value
    the caller of this needs to handle the case where a zero length
    is required and call RemoveInsertionCommand
    """
    def __init__(self, strand, idx, new_length):
        super(ChangeInsertionCommand, self).__init__("change insertion")
        self._strand = strand
        id_num = strand.idNum()
        self._insertions = strand.part().insertions()[id_num]
        self._idx = idx
        self._new_length = new_length
        self._old_length = self._insertions[idx].length()
        self._comp_strand = \
                    strand.strandSet().complementStrandSet().getStrand(idx)
    # end def

    def redo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertions[self._idx]
        inst.setLength(self._new_length, emit_signals=True)
        strand.oligo()._incrementLength(self._new_length - self._old_length,
                                        emit_signals=True)
        strand.strandInsertionChangedSignal.emit(strand, inst)
        if c_strand:
            c_strand.oligo()._incrementLength(
                                        self._new_length - self._old_length,
                                        emit_signals=True)
            c_strand.strandInsertionChangedSignal.emit(c_strand, inst)
    # end def

    def undo(self):
        strand = self._strand
        c_strand = self._comp_strand
        inst = self._insertions[self._idx]
        inst.setLength(self._old_length)
        strand.oligo()._decrementLength(self._new_length - self._old_length,
                                        emit_signals=True)
        strand.strandInsertionChangedSignal.emit(strand, inst)
        if c_strand:
            c_strand.oligo()._decrementLength(
                                        self._new_length - self._old_length,
                                        emit_signals=True)
            c_strand.strandInsertionChangedSignal.emit(c_strand, inst)
    # end def
# end class
