from ast import literal_eval
import bisect
from typing import (
    Union,
    List,
    Tuple
)

from cadnano.proxies.cnproxy import UndoCommand
from cadnano.cntypes import (
    NucleicAcidPartT,
    RectT
)

class CreateVirtualHelixCommand(UndoCommand):
    def __init__(self,
                part: NucleicAcidPartT,
                x: float,
                y: float,
                z: float,
                length: int,
                id_num: int = None,
                properties: Union[tuple, dict] = None,
                safe: bool = True,
                parity: int = None):
        '''``UndoCommand`` to create a virtual helix in a ``NucleicAcidPart``

        Args:
            part: The parent ``NucleicAcidPart``
            x: ``x`` coordinate of the 0 - index base
            y: ``y`` coordinate of the 0 - index base
            z: ``z`` coordinate of the 0 - index base
            length: Length of the virtual helix in bases
            id_num: the ID number of the helix in the ``part``
            properties: the initial or inherited properties of the ``part``
            safe: Default is ``True``. safe must be ``True`` to update neighbors.
                otherwise, neighbors need to be explicitly updated.  Set to
                ``False`` to speed up creation of many virtual helices
            parity: even == 0, odd == 1, None == doesn't matter.  Legacy from
                scaffold based design
        '''
        super(CreateVirtualHelixCommand, self).__init__("create virtual helix")
        self.part: NucleicAcidPartT = part
        if id_num is None:
            id_num = part._getNewIdNum(parity=parity)
        else:
            part._reserveIdNum(id_num)
        self.id_num: int = id_num
        self.origin_pt: Tuple[float, float, float] = (x, y, z)
        self.length: int = length
        self.color: str = part.getColor()
        self.keys: List[str] = None
        if properties is not None:
            if isinstance(properties, tuple):  # usually for unsafe
                self.keys, self.values = properties
            else:
                self.keys = list(properties.keys())
                self.values = list(properties.values())

        self.neighbors: List[int] = []
        if not safe:
            self.neighbors = literal_eval(self.values[self.keys.index('neighbors')])

        self.threshold: float = 2.1*part.radius()
        self.safe: bool = safe
        self.old_limits: RectT = None
    # end def

    def redo(self):
        part = self.part
        id_num = self.id_num
        origin_pt = self.origin_pt
        self.old_limits = part.getVirtualHelixOriginLimits()
        # Set direction to (0, 0, 1) for now
        vh = part._createHelix(id_num, origin_pt, (0, 0, 1), self.length, self.color)

        if self.safe:   # update all neighbors
            if not self.neighbors:
                self.neighbors = list(
                    part._getVirtualHelixOriginNeighbors(id_num, self.threshold))

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
            '''NOTE: DON'T bother UndoCommand-ing this because the helix is
            deleted on the undo.  Causes a segfault on MacOS if you do
            '''
            part._setVirtualHelixProperties(id_num,
                                           self.keys, self.values,
                                           emit_signals=False)
            part.resetCoordinates(id_num)
        part.partVirtualHelixAddedSignal.emit(part, id_num, vh, neighbors)
        print('Done redoing create of %s' % self.id_num)
    # end def

    def undo(self):
        part = self.part
        id_num = self.id_num
        # since we're hashing on the object in the views do this first
        for neighbor_id in self.neighbors:
            nneighbors = literal_eval(part.getVirtualHelixProperties(neighbor_id, 'neighbors'))
            try:
                nneighbors.remove(id_num)
                part.vh_properties.loc[neighbor_id, 'neighbors'] = str(list(nneighbors))
            except:
                print("id_num %d not there in neighbor %d" % (id_num, neighbor_id))
                pass

        # signaling the view is two parts to clean up signals properly
        # and then allow the views to refresh
        part.partVirtualHelixRemovingSignal.emit(
            part, id_num, part.getVirtualHelix(id_num), self.neighbors)
        # clear out part references
        part._removeHelix(id_num)
        part.setVirtualHelixOriginLimits(self.old_limits)
        part.partVirtualHelixRemovedSignal.emit(part, id_num)
    # end def
# end class
