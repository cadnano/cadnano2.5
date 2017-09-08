"""Summary
"""
from PyQt5.QtWidgets import QGraphicsRectItem
from . import slicestyles as styles
from .sliceextras import PreXoverItemGroup, WEDGE_RECT

_RADIUS = styles.SLICE_HELIX_RADIUS


class PreXoverManager(QGraphicsRectItem):
    """Summary

    Attributes:
        active_group (TYPE): Description
        active_neighbor_group (TYPE): Description
        groups (dict): Description
        neighbor_pairs (tuple): Description
        neighbor_prexover_items (dict): Description
        part_item (TYPE): Description
        prexover_item_map (dict): Description
        virtual_helix_item (cadnano.gui.views.sliceview.virtualhelixitem.VirtualHelixItem): Description
    """
    def __init__(self, part_item):
        """Summary

        Args:
            part_item (TYPE): Description
        """
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
        self.neighbor_pairs = ()  # accounting for neighbor pairing
        self._active_items = []
    # end def

    def partItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.part_item
    # end def

    def clearPreXoverItemGroups(self):
        """Summary

        Returns:
            TYPE: Description
        """
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
        if self.virtual_helix_item is not None:
            self.virtual_helix_item.setZValue(styles.ZSLICEHELIX)
    # end def

    def hideGroups(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.clearPreXoverItemGroups()
        if self.active_group is not None:
            self.active_group.hide()
        for group in self.groups.values():
            group.hide()
        self.virtual_helix_item = None
    # end def

    def activateVirtualHelix(self, virtual_helix_item, idx, per_neighbor_hits, pairs):
        """Create PreXoverItemGroups for the active virtual_helix_item and it's
        neighbors and connect the neighboring bases

        Args:
            virtual_helix_item (cadnano.gui.views.sliceview.virtualhelixitem.VirtualHelixItem): Description
            idx (int): the base index within the virtual helix
            per_neighbor_hits (TYPE): Description
            pairs (TYPE): Description
        """
        self.clearPreXoverItemGroups()
        pxis = self.prexover_item_map
        neighbor_pxis_dict = self.neighbor_prexover_items  # for avoiding duplicates)
        self.neighbor_pairs = pairs

        self.virtual_helix_item = virtual_helix_item
        part_item = self.part_item
        groups = self.groups
        self.active_group = agroup = PreXoverItemGroup(_RADIUS, WEDGE_RECT,
                                                       virtual_helix_item, True)
        id_num = virtual_helix_item.idNum()
        virtual_helix_item.setZValue(styles.ZSLICEHELIX + 10)

        fwd_st_type, rev_st_type = True, False  # for clarity in the call to constructors
        for neighbor_id, hits in per_neighbor_hits.items():
            nvhi = part_item.idToVirtualHelixItem(neighbor_id)
            ngroup = PreXoverItemGroup(_RADIUS, WEDGE_RECT, nvhi, False)
            groups[neighbor_id] = ngroup

            fwd_axis_hits, rev_axis_hits = hits

            # n_step_size = nvhi.getProperty('bases_per_repeat')
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                neighbor_pxis = []
                # print((id_num, fwd_st_type, idx))
                pxis[(id_num, fwd_st_type, idx)] = (agroup.getItemIdx(fwd_st_type, idx),
                                                    ngroup,
                                                    neighbor_pxis
                                                    )
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(fwd_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(npxi)
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(rev_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(npxi)

            for idx, fwd_idxs, rev_idxs in rev_axis_hits:
                neighbor_pxis = []
                # print((id_num, rev_st_type, idx))
                pxis[(id_num, rev_st_type, idx)] = (agroup.getItemIdx(rev_st_type, idx),
                                                    ngroup,
                                                    neighbor_pxis
                                                    )
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(fwd_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(npxi)
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = ngroup.getItemIdx(rev_st_type, j)
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(npxi)
        # end for per_neighbor_hits
    # end def

    def activateNeighbors(self, id_num, is_fwd, idx):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            is_fwd (TYPE): Description
            idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description

        Raises:
            ValueError: Description
        """
        # print("ACTIVATING neighbors", id_num, idx)
        if self.active_group is None:
            return
        agroup = self.active_group
        if id_num != agroup.id_num:
            raise ValueError("not active id_num {} != {}".format(id_num,
                                                                 agroup.id_num))
        active_items = self._active_items

        item = self.prexover_item_map.get((id_num, is_fwd, idx))
        if item is None:
            apxi = agroup.getItemIdx(is_fwd, idx)
            apxi.setActive5p(True) if is_fwd else apxi.setActive3p(True)
            agroup.active_wedge_gizmo.pointToPreXoverItem(apxi)
            active_items.append(apxi)
        else:
            apxi, npxig, neighbor_list = item
            pairs = self.neighbor_pairs[0] if is_fwd else self.neighbor_pairs[1]
            check_5prime = pairs.get(idx)
            is_5prime_strand = None
            if check_5prime is not None:
                is_5prime_strand = check_5prime[0]
            else:
                if is_fwd and idx == 0:
                    is_5prime_strand = False
                elif not is_5prime_strand and self.virtual_helix_item.getProperty('length') == idx + 1:
                    is_5prime_strand = False
                else:
                    is_5prime_strand = True

            agroup.active_wedge_gizmo.pointToPreXoverItem(apxi)
            active_items.append(apxi)
            self.active_neighbor_group = npxig
            # print("Should have {} neighbors".format(len(neighbor_list)))
            # color = neighbor_list[0].color if neighbor_list else '#aaaaa'
            # angle = 0
            for npxi in neighbor_list:
                npxi.setActive3p(True, apxi) if is_5prime_strand else npxi.setActive5p(True, apxi)
                active_items.append(npxi)

            apxi.setActive5p(True, npxi) if is_5prime_strand else apxi.setActive3p(True, npxi)
    # end def

    def deactivateNeighbors(self):
        """Summary

        Returns:
            TYPE: Description
        """
        while self._active_items:
            npxi = self._active_items.pop()
            npxi.setActive3p(False)
            npxi.setActive5p(False)
        if self.active_neighbor_group is None:
            return
        wg = self.active_neighbor_group.active_wedge_gizmo
        if wg is not None:
            wg.deactivate()
        self.active_neighbor_group = None
    # end def
# end class
