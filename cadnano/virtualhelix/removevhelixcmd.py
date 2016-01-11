from cadnano.cnproxy import UndoCommand

class RemoveVirtualHelixCommand(UndoCommand):
    """"""
    def __init__(self, part, id_num):
        super(RemoveVirtualHelixCommand, self).__init__("remove virtual helix")
        self.part = part
        self.id_num = id_num
        vhg = part.virtualHelixGroup()
        _, self.length = vhg.getOffsetAndSize(id_num)
        x, y = vhg.getOrigin(id_num)
        self.origin_pt = (x, y, 0.)
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        vhg = part.virtualHelixGroup()
        # clear out part references
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
        vhg.removeHelix(id_num)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        part = self._part
        id_num = self._id_num
        vhg.createHelix(id_num, self.origin_pt, (1, 0, 0), self.length)
        part.partVirtualHelixAddedSignal.emit(part, id_num)
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class
