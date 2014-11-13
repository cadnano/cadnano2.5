from cadnano.cnproxy import UndoCommand

class ResizePartCommand(UndoCommand):
    """
    set the maximum and mininum base index in the helical direction

    need to adjust all subelements in the event of a change in the
    minimum index
    """
    def __init__(self, part, min_helix_delta, max_helix_delta):
        super(ResizePartCommand, self).__init__("resize part")
        self._part = part
        self._min_delta = min_helix_delta
        self._max_delta = max_helix_delta
        self._old_active_idx = part.activeBaseIndex()
    # end def

    def redo(self):
        part = self._part
        part._min_base += self._min_delta
        part._max_base += self._max_delta
        if self._min_delta != 0:
            self.deltaMinDimension(part, self._min_delta)
        for vh in part._coord_to_virtual_velix.values():
            part.partVirtualHelixResizedSignal.emit(part, vh.coord())
        if self._old_active_idx > part._max_base:
            part.setActiveBaseIndex(part._max_base)
        part.partDimensionsChangedSignal.emit(part)
    # end def

    def undo(self):
        part = self._part
        part._min_base -= self._min_delta
        part._max_base -= self._max_delta
        if self._min_delta != 0:
            self.deltaMinDimension(part, self._min_delta)
        for vh in part._coord_to_virtual_velix.values():
            part.partVirtualHelixResizedSignal.emit(part, vh.coord())
        if self._old_active_idx != part.activeBaseIndex():
            part.setActiveBaseIndex(self._old_active_idx)
        part.partDimensionsChangedSignal.emit(part)
    # end def

    def deltaMinDimension(self, part, minDimensionDelta):
        """
        Need to update:
        strands
        insertions
        """
        for vh_dict in part._insertions.values():
            for insertion in vh_dict:
                insertion.updateIdx(minDimensionDelta)
            # end for
        # end for
        for vh in part._coord_to_virtual_velix.values():
            for strand in vh.scaffoldStrand().generatorStrand():
                strand.updateIdxs(minDimensionDelta)
            for strand in vh.stapleStrand().generatorStrand():
                strand.updateIdxs(minDimensionDelta)
        # end for
    # end def
# end class