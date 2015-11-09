from cadnano.cnproxy import UndoCommand

class TransformVirtualHelixCommand(UndoCommand):
    """Inserts strandToAdd into strandList at index idx."""
    def __init__(self, part, virtual_helix, transform):
        super(TransformVirtualHelixCommand, self).__init__("transform virtual helix")
        self._part = part
        self._virtual_helix = virtual_helix
        self._transform = transform
        self._old_transform = virtual_helix.transform()
    # end def

    def redo(self):
        vh = self._virtual_helix
        part = self._part
        tr = self._transform
        vh.virtualHelixPropertyChangedSignal.emit(vh, tr)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        vh = self._virtual_helix
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
