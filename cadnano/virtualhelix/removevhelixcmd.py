from ast import literal_eval
import bisect

from cadnano.cnproxy import UndoCommand

class RemoveVirtualHelixCommand(UndoCommand):
    """"""
    def __init__(self, part, id_num):
        super(RemoveVirtualHelixCommand, self).__init__("remove virtual helix")
        self.part = part
        self.id_num = id_num
        _, self.length = part.getOffsetAndSize(id_num)
        x, y = part.getVirtualHelixOrigin(id_num)
        self.origin_pt = (x, y, 0.)
        neighbors = part.getVirtualHelixProperties(id_num, 'neighbors')
        self.neighbors = literal_eval(neighbors)
        self.color = part.getVirtualHelixProperties(id_num, 'color')
        self.props = part.getAllVirtualHelixProperties(inject_extras=False)
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        # clear out part references
        for neighbor_id in self.neighbors:
            nneighbors = literal_eval(
                            part.getVirtualHelixProperties(neighbor_id, 'neighbors')
                        )
            nneighbors.remove(id_num)
            part.vh_properties.loc[neighbor_id, 'neighbors'] = str(list(nneighbors))

        part.partVirtualHelixRemovedSignal.emit(part, id_num, self.neighbors)
        part.removeHelix(id_num)
    # end def

    def undo(self):
        part = self.part
        id_num = self.id_num
        for neighbor_id in self.neighbors:
            nneighbors = literal_eval(
                            part.getVirtualHelixProperties(neighbor_id, 'neighbors')
                        )
            bisect.insort_left(nneighbors, id_num)
            part.vh_properties.loc[neighbor_id, 'neighbors'] = str(list(nneighbors))
        part.createHelix(id_num, self.origin_pt, (0, 0, 1), self.length, self.color)
        keys = list(self.props.keys())
        vals = list(self.props.val())
        part.setVirtualHelixProperties( id_num,
                                        keys, vals,
                                        safe=False)
        part.resetCoordinates(id_num)
        part.partVirtualHelixAddedSignal.emit(part, id_num, self.neighbors)
    # end def
# end class
