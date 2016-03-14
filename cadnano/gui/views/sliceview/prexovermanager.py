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
        self.active_neighbor_group = None
        self.groups = {}

        # dictionary of tuple of a
        #    (PreXoverItemGroup, PreXoverItemGroup, List[PreXoverItem])
        # tracks connections between prexovers
        self.prexover_item_map = {}
        self.neighbor_prexover_items = {}   # just a dictionary of neighbors
        self._active_items = []
    # end def

    def clearPreXoverItemGroups(self):
        groups = self.groups
        while groups:
            k, item = groups.popitem()
            item.remove()
        if self.active_group is not None:
            self.active_group.remove()
            self.active_group = None
        self._active_items = []
        self.prexover_item_map = {}
        self.neighbor_prexover_items = {}
    # end def

    def activateVirtualHelix(self, virtual_helix_item, per_neighbor_hits):
        """ Create PreXoverItemGroups for the active virtual_helix_item and it's
        neighbors and connect the neighboring bases
        """
        self.clearPreXoverItemGroups()
        pxis = self.prexover_item_map
        neighbor_pxis_dict = self.neighbor_prexover_items # for avoiding duplicates
        self.virtual_helix_item = virtual_helix_item
        part_item = self.part_item
        groups = self.groups
        self.active_group = agroup = PreXoverItemGroup(_RADIUS, WEDGE_RECT,
                                                    virtual_helix_item, True)
        id_num = virtual_helix_item.idNum()
        fwd_st_type, rev_st_type = True, False  # for clarity in the call to constructors
        for neighbor_id, hits in per_neighbor_hits.items():
            nvhi = part_item.idToVirtualHelixItem(neighbor_id)
            ngroup = PreXoverItemGroup(_RADIUS, WEDGE_RECT, nvhi, False)
            groups[neighbor_id] = ngroup
            fwd_axis_hits, rev_axis_hits = hits
            n_step_size = nvhi.getProperty('bases_per_repeat')
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                neighbor_pxis = []
                # print((id_num, fwd_st_type, idx))
                pxis[(id_num, fwd_st_type, idx)] = (
                                        agroup.getItemIdx(fwd_st_type, idx),
                                        ngroup,
                                        neighbor_pxis
                                        )
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(fwd_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(  npxi  )
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(rev_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )

            for idx, fwd_idxs, rev_idxs in rev_axis_hits:
                neighbor_pxis = []
                # print((id_num, rev_st_type, idx))
                pxis[(id_num, rev_st_type, idx)] = (
                                        agroup.getItemIdx(rev_st_type, idx),
                                        ngroup,
                                        neighbor_pxis
                                        )
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(fwd_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(rev_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )
        # end for per_neighbor_hits
    # end def

    def activateNeighbors(self, id_num, is_fwd, idx):
        # print("ACTIVATING neighbors", id_num, idx)
        if self.active_group is None:
            return
        if id_num != self.active_group.id_num:
            raise ValueError("not active id_num {} != {}".format(id_num,
                                                self.active_group.id_num))

        item = self.prexover_item_map.get((id_num, is_fwd, idx))
        if item is not None:
            apxi, npxig, neighbor_list = item
            self.active_neighbor_group = npxig
            # print("Should have {} neighbors".format(len(neighbor_list)))
            for k, npxi in enumerate(neighbor_list):
                # npxi.activateNeighbor(pxi, shortcut=str(k))
                # self.addKeyPress(k, npxi.getInfo())
                # npxi.updateViewActiveBase(apxi)
                npxi.setActive3p(True)
                npxig.active_wedge_gizmo.showActive(npxi)
                self._active_items.append(npxi)

    # end def

    def deactivateNeighbors(self):
        # self._key_press_dict = {}
        if self.active_neighbor_group is None:
            return
        self.active_neighbor_group.active_wedge_gizmo.hide()
        while self._active_items:
            npxi = self._active_items.pop()
            npxi.setActive3p(False)
            npxi.setActive5p(False)

    # def updateNeighborsNearActiveBase(self, item, is_active):
    #     """Update part prop to reflect VHs near the active (hovered) phos."""
    #     _vh = self._virtual_helix
    #     if not is_active:
    #         _vh.part().setProperty('neighbor_active_angle', '')
    #         return

    #     facing_angle = item.facing_angle()
    #     ret = []
    #     span = self.partCrossoverSpanAngle()/2
    #     neighbors = _vh.getProperty('neighbors').split()
    #     for n in neighbors:
    #         n_name, n_angle = n.split(':')
    #         n_angle = int(n_angle)
    #         d = n_angle-facing_angle
    #         if 180-abs(abs(d)-180)<span:
    #             ret.append('%s:%d' % (n_name, n_angle+d))
    #     _vh.part().setProperty('neighbor_active_angle', ' '.join(ret))

    # def foo():
    #     if new_value:
    #         local_angle = (int(new_value)+180) % 360
    #         fwd_items, rev_items = pxig.getItemsFacingNearAngle(local_angle)
    #         for item in fwd_items + rev_items:
    #             item.updateItemApperance(True, show_3p=False)
    #     else:
    #         pxig.resetAllItemsAppearance()

# end class