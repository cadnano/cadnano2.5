from ast import literal_eval
import bisect
from cadnano.cnproxy import UndoCommand
from cadnano.virtualhelix import VirtualHelixGroup

class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self, part, x, y, length, id_num=None):
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self.part = part
        if id_num is None:
            self.id_num = part.getNewIdNum()
        else:
            part.reserveIdNum(id_num)
            self.id_num = id_num
        self.origin_pt = (x, y, 0.)
        self.length = length
        self.color = part.getColor()
        self.neighbors = []
        self.threshold = 2.1*part.radius()
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        origin_pt = self.origin_pt
        # need to always reserve an id
        part.createHelix(id_num, origin_pt, (0, 0, 1), self.length, self.color)

        if not self.neighbors:
            self.neighbors = part.getVirtualHelixOriginNeighbors(id_num, self.threshold)

        neighbors = self.neighbors
        part.vh_properties.loc[id_num, 'neighbors'] = str(list(neighbors))
        for neighbor_id in neighbors:
            nneighbors = literal_eval(
                part.getVirtualHelixProperties(neighbor_id, 'neighbors')
            )
            bisect.insort_left(nneighbors, id_num)
            part.vh_properties.loc[neighbor_id, 'neighbors'] =str(list(nneighbors))

        part.partVirtualHelixAddedSignal.emit(part, id_num, neighbors)
        part.partActiveSliceResizeSignal.emit(part)
    # end def

    def undo(self):
        part = self.part
        id_num = self.id_num
        # since we're hashing on the object in the views do this first
        for neighbor_id in self.neighbors:
            nneighbors = literal_eval(
                            part.getVirtualHelixProperties(neighbor_id, 'neighbors')
                        )
            nneighbors.remove(id_num)
            part.vh_properties.loc[neighbor_id, 'neighbors'] = str(list(nneighbors))

        part.partVirtualHelixRemovedSignal.emit(part, id_num, self.neighbors)
        part.removeHelix(id_num)
        # clear out part references
        part.partActiveSliceResizeSignal.emit(part)
    # end def
# end class
