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
        self.props = part.getAllVirtualHelixProperties(id_num, inject_extras=False)
        self.old_active_base_info = part.active_base_info
        self._vh_order = part.getImportVirtualHelixOrder().copy()  # just copy the whole list
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        # clear out part references
        part.clearActiveVirtualHelix()
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
        part._removeHelix(id_num)
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
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
        vh = part._createHelix(id_num, self.origin_pt, (0, 0, 1), self.length, self.color)
        keys = list(self.props.keys())
        vals = list(self.props.values())
        part.setVirtualHelixProperties( id_num,
                                        keys, vals,
                                        safe=False)
        part.resetCoordinates(id_num)
        part.partVirtualHelixAddedSignal.emit(part, id_num, vh, self.neighbors)
        abi = self.old_active_base_info
        if abi:
            part.setActiveVirtualHelix(*abi[0:3])
        part.setImportedVHelixOrder(self._vh_order)
    # end def
# end class
