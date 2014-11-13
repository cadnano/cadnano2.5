from cadnano.cnproxy import UndoCommand

class RemoveVirtualHelixCommand(UndoCommand):
    """Inserts strandToAdd into strandList at index idx."""
    def __init__(self, part, virtual_helix):
        super(RemoveVirtualHelixCommand, self).__init__("remove virtual helix")
        self._part = part
        self._vhelix = virtual_helix
        self._id_num = virtual_helix.number()
        # is the number even or odd?  Assumes a valid id_num, row,col combo
        self._is_parity_even = (self._id_num % 2) == 0
        
    # end def

    def redo(self):
        vh = self._vhelix
        part = self._part
        id_num = self._id_num
        
        part._removeVirtualHelix(vh)
        part._recycleHelixIDNumber(id_num)
        # clear out part references
        vh.virtualHelixRemovedSignal.emit(vh)
        part.partActiveSliceResizeSignal.emit(part)
        # vh.setPart(None)
        # vh.setNumber(None)
    # end def

    def undo(self):
        vh = self._vhelix
        part = self._part
        id_num = self._id_num
        
        vh.setPart(part)
        part._addVirtualHelix(vh)
        # vh.setNumber(id_num)
        if not vh.number():
            part._reserveHelixIDNumber(self._is_parity_even, requested_id_num=id_num)
        part.partVirtualHelixAddedSignal.emit(part, vh)
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class