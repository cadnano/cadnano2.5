from cadnano.cnproxy import UndoCommand

class ResizeVirtualHelixCommand(UndoCommand):
    """
    set the maximum and mininum base index in the helical direction

    need to adjust all subelements in the event of a change in the
    minimum index
    """
    def __init__(self, part, virtual_helix, high_helix_delta):
        super(ResizeVirtualHelixCommand, self).__init__("Resize vhelix")
        self._part = part
        self._vhelix = virtual_helix
        self._id_num = virtual_helix.number()
        self._high_idx_delta = high_helix_delta
        print ("ResizeVirtualHelixCommand", part, virtual_helix, high_helix_delta)
    # end def

    def redo(self):
        part = self._part
        vh = self._vhelix
        vh._max_base += self._high_idx_delta
        for ss in vh.getStrandSets():
            print("resizing ss", self._high_idx_delta)
            ss.resize(0, self._high_idx_delta)
        part.partVirtualHelixResizedSignal.emit(part, vh.coord())
        part.partDimensionsChangedSignal.emit(part, True)
    # end def

    def undo(self):
        part = self._part
        vh = self._vhelix
        vh._max_base -= self._high_idx_delta
        for ss in vh.getStrandSets():
            ss.resize(0, -self._high_idx_delta)
        part.partVirtualHelixResizedSignal.emit(part, vh.coord())
        part.partDimensionsChangedSignal.emit(part, True)
    # end def
# end class
