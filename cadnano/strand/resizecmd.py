from cadnano.cnproxy import UndoCommand

class ResizeCommand(UndoCommand):
    def __init__(self, strand, newIdxs):
        super(ResizeCommand, self).__init__("resize strand")
        self.strand = strand
        self.oldIndices = oI = strand.idxs()
        self.newIdxs = newIdxs
        # an increase in length leads to positive delta
        self.delta = (newIdxs[1] - newIdxs[0]) - (oI[1] - oI[0])
        # now handle insertion deltas
        oldInsertions = strand.insertionsOnStrand(*oI)
        newInsertions = strand.insertionsOnStrand(*newIdxs)
        oL = 0
        for i in oldInsertions:
            oL += i.length()
        nL = 0
        for i in newInsertions:
            nL += i.length()
        self.delta += (nL-oL)

        # the strand sequence will need to be regenerated from scratch
        # as there are no guarantees about the entirety of the strand moving
        # thanks to multiple selections
    # end def

    def redo(self):
        std = self.strand
        nI = self.newIdxs
        strandset = self.strand.strandSet()
        part = strandset.part()

        std.oligo().incrementLength(self.delta)
        std.setIdxs(nI)
        if strandset.isStaple():
            
            std.reapplySequence()
        std.strandResizedSignal.emit(std, nI)
        # for updating the Slice View displayed helices
        part.partStrandChangedSignal.emit(part, strandset.virtualHelix())
        std5p = std.connection5p()
        if std5p:
            std5p.strandResizedSignal.emit(std5p, std5p.idxs())
    # end def

    def undo(self):
        std = self.strand
        oI = self.oldIndices
        strandset = self.strand.strandSet()
        part = strandset.part()

        std.oligo().decrementLength(self.delta)
        std.setIdxs(oI)
        if strandset.isStaple():
            std.reapplySequence()
        std.strandResizedSignal.emit(std, oI)
        # for updating the Slice View displayed helices
        part.partStrandChangedSignal.emit(part, strandset.virtualHelix())
        std5p = std.connection5p()
        if std5p:
            std5p.strandResizedSignal.emit(std5p, std5p.idxs())
    # end def
# end class