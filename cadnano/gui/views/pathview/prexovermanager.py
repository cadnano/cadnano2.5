from collections import deque
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QColor
from .pathextras import (PreXoverItem, #NeighborPreXoverItem, ActivePreXoverItem,
                        PHOS_ITEM_WIDTH, BASE_WIDTH)
from cadnano.gui.palette import newPenObj, getNoPen, getPenObj
from cadnano.enum import StrandType

class PreXoverManager(QGraphicsRectItem):
    HUE_FACTOR = 1.6
    KEYMAP = { i: getattr(Qt, 'Key_%d' % i) for i in range(10) }
    def __init__(self, part_item):
        super(QGraphicsRectItem, self).__init__(part_item)
        self.part_item = part_item
        self.virtual_helix_item = None
        self.setPen(getNoPen())
        self._colors = []

        # dictionary of tuple of a (PreXoverItem, List[PreXoverItem])
        # for activating on hover events
        self.prexover_item_map = {}

        self.neighbor_prexover_items = {}   # just a dictionary of neighbors
        self.active_items = []
        self._key_press_dict = {}

        # for reuse of PreXoverItem objects
        self.pxi_pool = deque()
        self.fwd_pxis = []
        self.rev_pxis = []
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._parent.window()

    def virtualHelixItem(self):
        return self.virtual_helix_item
    # end def

    def addKeyPress(self, key_int, info):
        qtkey = self.KEYMAP[key_int]
        self._key_press_dict[qtkey] = info
    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def updateBasesPerRepeat(self, step_size):
        """Recreates colors, all vhi"""
        hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        # self.removeRepeats()
        # self.addRepeats()
    # end def

    def handlePreXoverKeyPress(self, key):
        print("handling key", key, self.KEYMAP.get(key, None))
        if key not in self._key_press_dict:
            return

        # active item
        part = self.part_item.part()
        active_id_num, a_is_fwd, a_idx, a_to_id = part.active_base_info
        a_strand_type = StrandType.FWD if a_is_fwd else StrandType.REV
        neighbor_id_num, n_is_fwd, n_idx, n_to_id = self._key_press_dict[key]
        n_strand_type = StrandType.FWD if n_is_fwd else StrandType.REV

        if not part.hasStrandAtIdx(active_id_num, a_idx)[a_strand_type]:
            print("no active strand", key)
            return
        if not part.hasStrandAtIdx(neighbor_id_num, n_idx)[n_strand_type]:
            print("no neighbor strand", key)
            return

        a_strandset = part.getStrandSets(active_id_num)[a_strand_type]
        n_strandset = part.getStrandSets(neighbor_id_num)[n_strand_type]
        a_strand = a_strandset.getStrand(a_idx)
        n_strand = n_strandset.getStrand(n_idx)

        if a_strand.hasXoverAt(a_idx): return
        if n_strand.hasXoverAt(n_idx): return

        # SPECIAL CASE: neighbor already has a 3' end, and active has
        # a 5' end, so assume the user wants to install a returning xover
        if a_strand.idx5Prime() == a_idx and n_strand.idx3Prime() == n_idx:
            part.createXover(n_strand, n_idx, a_strand, a_idx)
            return

        # DEFAULT CASE: the active strand acts as strand5p,
        # install a crossover to the neighbor acting as strand3p
        part.createXover(a_strand, a_idx, n_strand, n_idx)
    # end def

    def updateTurnsPerRepeat(self):
        pass
    # end def

    def part(self):
        return self.parentItem().part()

    ### PUBLIC SUPPORT METHODS ###
    def getItem(self, id_num, is_fwd, idx):
        return self.prexover_item_map[(id_num, is_fwd, idx)]
    # end def

    def clearPreXoverItems(self):
        self.active_items = []
        pxi_pool = self.pxi_pool
        # for x, y in self.prexover_item_map.values():
        for x in self.fwd_pxis:
            x.hide()
            pxi_pool.append(x)
        self.fwd_pxis = []
        for x in self.rev_pxis:
            x.hide()
            pxi_pool.append(x)
        self.rev_pxis = []
        self.prexover_item_map = {}
        for x in self.neighbor_prexover_items.values():
            x.hide()
            pxi_pool.append(x)
        self.neighbor_prexover_items = {}
    # end def

    @staticmethod
    def getPoolItem(pool, cls, *args):
        """ grab an item from a pool if there is one and reconfigure it
        otherwise, create a new object of type `cls`
        Useful to avoid issues with deleting animations
        """
        if len(pool) > 0:
            item = pool.pop()
            item.resetItem(*args)
            return item
        else:
            return cls(*args)
    # end def

    def activateVirtualHelix(self, virtual_helix_item, this_idx, per_neighbor_hits):
        """ Populate self.prexover_item_map dictionary which maps a tuple
        of (id_num, is_fwd, idx) to a given PreXoverItem and a List of neighbor PreXoverItems
        This also effectively deactivates the existing VirtualHelix

        Args:
            virtual_helix_item (VirtualHelixItem):
            per_neighbor_hits (Tuple()):
        """
        # print("ACTIVATING VH", virtual_helix_item.idNum())
        # 1. clear all PreXoverItems
        self.clearPreXoverItems()
        pxis = self.prexover_item_map
        neighbor_pxis_dict = self.neighbor_prexover_items # for avoiding duplicates
        part_item = self.part_item
        pxi_pool = self.pxi_pool
        getPoolItem = self.getPoolItem

        bpr = virtual_helix_item.getProperty('bases_per_repeat')

        self.virtual_helix_item = virtual_helix_item
        self.updateBasesPerRepeat(bpr)

        colors = self._colors
        # the list of neighbors per strand
        id_num = virtual_helix_item.idNum()
        fwd_st_type, rev_st_type = True, False  # for clarity in the call to constructors

        start, length = part_item.part().normalizedRange(id_num, this_idx)
        self.fwd_pxis = fpxis = []
        self.rev_pxis = rpxis = []
        for idx in range(start, start + length):
            apxi = getPoolItem(     pxi_pool,
                                    PreXoverItem,
                                    virtual_helix_item, fwd_st_type, idx,
                                    None, self, colors[idx % bpr]
                                )
            apxi.enableActive(True, None)
            fpxis.append(apxi)
            apxi = getPoolItem(     pxi_pool,
                                    PreXoverItem,
                                    virtual_helix_item, rev_st_type, idx,
                                    None, self, colors[-1 - (idx % bpr)]
                        )
            apxi.enableActive(True, None)
            rpxis.append(apxi)

        # 1. Construct PXIs for the active virtual_helix_item
        for neighbor_id, hits in per_neighbor_hits.items():
            fwd_axis_hits, rev_axis_hits = hits
            nvhi = part_item.idToVirtualHelixItem(neighbor_id)
            n_step_size = nvhi.getProperty('bases_per_repeat')
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                # from_virtual_helix_item, from_index, fwd_st_type, prexoveritemgroup, color):
                neighbor_pxis = []
                # print((id_num, fwd_st_type, idx))
                apxi = fpxis[idx - start]
                # apxi = getPoolItem(     pxi_pool,
                #                         PreXoverItem,
                #                         virtual_helix_item, fwd_st_type, idx,
                #                         neighbor_id, self, colors[idx % bpr]
                #                         )
                apxi.enableActive(True, to_vh_id_num=neighbor_id)
                pxis[(id_num, fwd_st_type, idx)] = (apxi, neighbor_pxis)
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = getPoolItem( pxi_pool,
                                            PreXoverItem,
                                            nvhi, fwd_st_type, j,
                                            id_num, self, colors[j % n_step_size]
                                            )
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append(  npxi  )
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = getPoolItem(     pxi_pool,
                                                PreXoverItem,
                                                nvhi, rev_st_type, j,
                                                id_num, self, colors[-1 - (j % n_step_size)]
                                                )
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )

            for idx, fwd_idxs, rev_idxs in rev_axis_hits:
                neighbor_pxis = []
                # print((id_num, rev_st_type, idx))
                # apxi = getPoolItem(     pxi_pool,
                #                         PreXoverItem,
                #                         virtual_helix_item, rev_st_type, idx,
                #                         neighbor_id, self, colors[-1 - (idx % bpr)]
                #                         )
                apxi = rpxis[idx - start]
                apxi.enableActive(True, to_vh_id_num=neighbor_id)
                pxis[(id_num, rev_st_type, idx)] = ( apxi, neighbor_pxis )
                for j in fwd_idxs:
                    nkey = (neighbor_id, fwd_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = getPoolItem( pxi_pool,
                                            PreXoverItem,
                                            nvhi, fwd_st_type, j,
                                            id_num, self, colors[j % n_step_size]
                                            )
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )
                for j in rev_idxs:
                    nkey = (neighbor_id, rev_st_type, j)
                    npxi = neighbor_pxis_dict.get(nkey)
                    if npxi is None:
                        npxi = getPoolItem( pxi_pool,
                                            PreXoverItem,
                                            nvhi, rev_st_type, j,
                                            id_num, self, colors[-1 - (j % n_step_size)]
                                            )
                        neighbor_pxis_dict[nkey] = npxi
                    neighbor_pxis.append( npxi )
        # end for per_neighbor_hits
    # end def

    def activateNeighbors(self, id_num, is_fwd, idx):
        # print("ACTIVATING neighbors", id_num, idx)
        item = self.prexover_item_map.get((id_num, is_fwd, idx))
        if item is not None:
            pxi, neighbor_list = item
            # print("Should have {} neighbors".format(len(neighbor_list)))
            for k, npxi in enumerate(neighbor_list):
                npxi.activateNeighbor(pxi, shortcut=str(k))
                self.addKeyPress(k, npxi.getInfo())
                self.active_items.append(npxi)
    # end def

    def deactivateNeighbors(self):
        self._key_press_dict = {}
        while self.active_items:
            self.active_items.pop().deactivateNeighbor()

    def updateModelActiveBaseInfo(self, pre_xover_info):
        """Notify model of pre_xover_item hover state.
        Args:
            pre_xover_info (Tuple): from call to getInfo()
        """
        self.part_item.part().setActiveBaseInfo(pre_xover_info)
    # end def

    def isVirtualHelixActive(self, id_num):
        return self.part_item.part().isVirtualHelixActive(id_num)
    # end def
# end class