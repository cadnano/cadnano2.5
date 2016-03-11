from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QColor

from . import slicestyles as styles
from .sliceextras import PreXoverItemGroup, WedgeGizmo, WEDGE_RECT
from cadnano.gui.palette import newPenObj, getNoPen, getPenObj
from cadnano.enum import StrandType

_RADIUS = styles.SLICE_HELIX_RADIUS

class PreXoverManager(QGraphicsRectItem):

    def __init__(self, part_item):
        super(PreXoverManager, self).__init__(part_item)
        self.part_item = part_item
        self.virtual_helix_item = None
        self.active_group = None
        self.groups = []
    # end def

    def clearPreXoverItemGroups(self):
        groups = self.groups
        while groups:
            groups.pop().remove()
        if self.active_group is not None:
            self.active_group.remove()
            self.active_group = None
    # end def

    def activateVirtualHelix(self, virtual_helix_item, per_neighbor_hits):
        self.clearPreXoverItemGroups()
        self.virtual_helix_item = virtual_helix_item
        part_item = self.part_item
        groups = self.groups
        self.active_group = PreXoverItemGroup(_RADIUS, WEDGE_RECT, virtual_helix_item)
        for neighbor_id in per_neighbor_hits:
            nvhi = part_item.idToVirtualHelixItem(neighbor_id)
            ngroup = PreXoverItemGroup(_RADIUS, WEDGE_RECT, nvhi)
            groups.append(ngroup)
    # end def


# end class