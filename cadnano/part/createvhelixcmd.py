from cadnano.cnproxy import UndoCommand
from cadnano.virtualhelix import VirtualHelixGroup

class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self, part, x, y, length):
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self.part = part
        vhg = part.virtualHelixGroup()
        self.id_num = vhg.getNewIdNum()
        self.origin_pt = (x, y, 0.)
        self.length = length
    # end def

    def redo(self):
        part = self.part
        vhg = part.virtualHelixGroup()
        id_num = self.id_num
        origin_pt = self.origin_pt
        # need to always reserve an id
        vhg.createHelix(id_num, origin_pt, (1, 0, 0), self.length)
        part.partVirtualHelixAddedSignal.emit(part, id_num)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        part = self.part
        vhg = part.virtualHelixGroup()
        id_num = self.id_num
        # since we're hashing on the object in the views do this first
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
        vhg.removeHelix(id_num)
        # clear out part references
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class
