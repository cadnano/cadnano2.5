from cadnano.cnproxy import UndoCommand

class ResizePartCommand(UndoCommand):
    """
    set the maximum and mininum base index in the helical direction

    need to adjust all subelements in the event of a change in the
    minimum index
    """
    def __init__(self, part, low_helix_delta, high_helix_delta):
        super(ResizePartCommand, self).__init__("resize part")
        self._part = part
        self._low_idx_delta = low_helix_delta
        self._high_idx_delta = high_helix_delta
        self._old_active_idx = part.activeBaseIndex()
    # end def

    def redo(self):
        part = self._part
        part._min_base += self._low_idx_delta
        part._max_base += self._high_idx_delta
        if self._low_idx_delta != 0:
            self.deltaLowIdx(part, self._low_idx_delta)
        for vh in part._coord_to_virtual_velix.values():
            for ss in vh.getStrandSets():
                ss.resize(self._low_idx_delta, self._high_idx_delta)
            part.partVirtualHelixResizedSignal.emit(part, vh)
        if self._old_active_idx > part._max_base:
            part.setActiveBaseIndex(part._max_base)
        part.partDimensionsChangedSignal.emit(part)
    # end def

    def undo(self):
        part = self._part
        part._min_base -= self._low_idx_delta
        part._max_base -= self._high_idx_delta
        if self._low_idx_delta != 0:
            self.deltaLowIdx(part, self._low_idx_delta)
        for vh in part._coord_to_virtual_velix.values():
            for ss in vh.getStrandSets():
                ss.resize(-self._low_idx_delta, -self._high_idx_delta)
            part.partVirtualHelixResizedSignal.emit(part, vh)
        if self._old_active_idx != part.activeBaseIndex():
            part.setActiveBaseIndex(self._old_active_idx)
        part.partDimensionsChangedSignal.emit(part)
    # end def

    def deltaLowIdx(self, part, low_idx_delta):
        """
        Need to update:
        strands
        insertions
        """
        for vh_dict in part._insertions.values():
            for insertion in vh_dict:
                insertion.updateIdx(low_idx_delta)
            # end for
        # end for
        for vh in part._coord_to_virtual_velix.values():
            for strand in vh.scaffoldStrand().generatorStrand():
                strand.updateIdxs(low_idx_delta)
            for strand in vh.stapleStrand().generatorStrand():
                strand.updateIdxs(low_idx_delta)
        # end for
        part.changeModsDeltaLowIdx(low_idx_delta)
    # end def
# end class
