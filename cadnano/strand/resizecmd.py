# -*- coding: utf-8 -*-
from cadnano.cnproxy import UndoCommand

class ResizeCommand(UndoCommand):
    def __init__(self, strand, new_idxs, update_segments=True):
        super(ResizeCommand, self).__init__("resize strand")
        self.strand = strand
        self.old_indices = o_i = strand.idxs()
        self.new_idxs = new_idxs
        # an increase in length leads to positive delta
        self.delta = (new_idxs[1] - new_idxs[0]) - (o_i[1] - o_i[0])
        # now handle insertion deltas
        oldInsertions = strand.insertionsOnStrand(*o_i)
        newInsertions = strand.insertionsOnStrand(*new_idxs)
        o_l = 0
        for i in oldInsertions:
            o_l += i.length()
        n_l = 0
        for i in newInsertions:
            n_l += i.length()
        self.delta += (n_l - o_l)

        self.update_segments = update_segments
        # the strand sequence will need to be regenerated from scratch
        # as there are no guarantees about the entirety of the strand moving
        # thanks to multiple selections
    # end def

    def redo(self):
        std = self.strand
        n_i = self.new_idxs
        o_i = self.old_indices
        strandset = self.strand.strandSet()
        part = strandset.part()

        std.oligo()._incrementLength(self.delta, emit_signals=True)
        std.setIdxs(n_i)
        strandset._updateStrandIdxs(std, o_i, n_i)
        if self.update_segments:
            part.refreshSegments(strandset.idNum())

        std.strandResizedSignal.emit(std, n_i)
        # for updating the Slice View displayed helices
        part.partStrandChangedSignal.emit(part, strandset.idNum())
        std5p = std.connection5p()
        if std5p:
            std5p.strandResizedSignal.emit(std5p, std5p.idxs())
    # end def

    def undo(self):
        std = self.strand
        n_i = self.new_idxs
        o_i = self.old_indices
        strandset = self.strand.strandSet()
        part = strandset.part()

        std.oligo()._decrementLength(self.delta, emit_signals=True)
        std.setIdxs(o_i)
        strandset._updateStrandIdxs(std, n_i, o_i)
        if self.update_segments:
            part.refreshSegments(strandset.idNum())

        std.strandResizedSignal.emit(std, o_i)
        # for updating the Slice View displayed helices
        part.partStrandChangedSignal.emit(part, strandset.idNum())
        std5p = std.connection5p()
        if std5p:
            std5p.strandResizedSignal.emit(std5p, std5p.idxs())
    # end def
# end class
