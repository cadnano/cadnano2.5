from cadnano.cnproxy import UndoCommand
from cadnano.virtualhelix import VirtualHelix

class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self, part, row, col):
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self._part = part
        self._is_parity_even = part.isEvenParity(row, col)
        id_num = part._reserveHelixIDNumber(self._is_parity_even,
                                            requested_id_num=None)
        self._vhelix = VirtualHelix(part, row, col, id_num)
        self._id_num = id_num
        # self._batch = batch
    # end def

    def redo(self):
        vh = self._vhelix
        part = self._part
        id_num = self._id_num
        vh.setPart(part)
        part._addVirtualHelix(vh)
        vh.setNumber(id_num)
        if not vh.number():
            part._reserveHelixIDNumber(self._is_parity_even,
                                        requested_id_num=id_num)
        # end if
        part.partVirtualHelixAddedSignal.emit(part, vh)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        vh = self._vhelix
        part = self._part
        id_num = self._id_num
        part._removeVirtualHelix(vh)
        part._recycleHelixIDNumber(id_num)
        # clear out part references
        vh.setNumber(None)  # must come before setPart(None)
        vh.setPart(None)
        vh.virtualHelixRemovedSignal.emit(vh)
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class