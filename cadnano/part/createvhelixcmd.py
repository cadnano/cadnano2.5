from cadnano.cnproxy import UndoCommand
from cadnano.virtualhelix import VirtualHelix
from cadnano.virtualhelixgroup import VirtualHelixGroup

class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self, part, x, y, length):
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self.part = part
        id_num = part._reserveHelixIDNumber(requested_id_num=None))
        self.id_num = id_num
        self.origin_pt = x, y, 0.
        self.length = length
        # self._batch = batch
    # end def

    def redo(self):
        part = self.part
        vhg = part.virtualhelixgroup
        id_num = self.id_num
        origin_pt = self.origin_pt
        # need to always reserve an id
        part._reserveHelixIDNumber(requested_id_num=id_num)
        vhg.createLabel(id_num, origin_pt, (1,0,0), self.length)
        part.partVirtualHelixAddedSignal.emit(part, id_num)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        part = self.part
        vhg = part.virtualhelixgroup
        id_num = self.id_num

        # since we're hashing on the object in the views do this first
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
        vhg.removeLabel(id_num)
        part._recycleHelixIDNumber(id_num)
        # clear out part references
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class
