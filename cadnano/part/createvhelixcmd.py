from ast import literal_eval
import bisect
from cadnano.cnproxy import UndoCommand


class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self, part, x, y, z, length,
                 id_num=None, properties=None,
                 safe=True):
        """
        Args:
            safe (bool): safe must be True to update neighbors
            otherwise, neighbors need to be explicitly updated
        """
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self.part = part
        if id_num is None:
            self.id_num = part._getNewIdNum()
        else:
            part._reserveIdNum(id_num)
            self.id_num = id_num
        self.origin_pt = (x, y, z)
        self.length = length
        self.color = part.getColor()
        self.keys = None
        if properties is not None:
            if isinstance(properties, tuple):  # usually for unsafe
                self.keys, self.values = properties
            else:
                self.keys = list(properties.keys())
                self.values = list(properties.values())
        if safe:
            self.neighbors = []
        else:
            self.neighbors = literal_eval(self.values[self.keys.index('neighbors')])

        self.threshold = 2.1*part.radius()
        self.safe = safe
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        origin_pt = self.origin_pt
        # need to always reserve an id
        vh = part._createHelix(id_num, origin_pt, (0, 0, 1), self.length, self.color)

        if self.safe:   # update all neighbors
            if not self.neighbors:
                self.neighbors = part._getVirtualHelixOriginNeighbors(id_num, self.threshold)

            neighbors = self.neighbors
            part.vh_properties.loc[id_num, 'neighbors'] = str(list(neighbors))
            for neighbor_id in neighbors:
                nneighbors = literal_eval(
                    part.getVirtualHelixProperties(neighbor_id, 'neighbors')
                )
                bisect.insort_left(nneighbors, id_num)
                part.vh_properties.loc[neighbor_id, 'neighbors'] = str(list(nneighbors))
        else:
            neighbors = self.neighbors
        if self.keys is not None:
            part.setVirtualHelixProperties(id_num,
                                           self.keys, self.values,
                                           safe=False)
            part.resetCoordinates(id_num)
        part.partVirtualHelixAddedSignal.emit(part, id_num, vh, neighbors)
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

        # signaling the view is two parts to clean up signals properly
        # and then allow the views to refresh
        part.partVirtualHelixRemovingSignal.emit(
            part, id_num, part.getVirtualHelix(id_num), self.neighbors)
        # clear out part references
        part._removeHelix(id_num)
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
    # end def
# end class
