from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QColor
from .pathextras import PreXoverItem, PHOS_ITEM_WIDTH, BASE_WIDTH
from cadnano.gui.palette import newPenObj, getNoPen, getPenObj
from cadnano.enum import StrandType

class PreXoverItemGroup(QGraphicsRectItem):
    HUE_FACTOR = 1.6
    KEYMAP = { i: getattr(Qt, 'Key_%d' % i) for i in range(10) }
    def __init__(self, part_item):
        super(QGraphicsRectItem, self).__init__(part_item)
        self.part_item = part_item
        self.virtual_helix_item = None
        self.setPen(getNoPen())
        self._colors = []
        # dictionary of tuple of a (PreXoverItem, List[PreXoverItem])
        self.prexover_items = {}
        self._active_items = []
        self._key_press_dict = {}
        # self.updateBasesPerRepeat()
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
        return self.prexover_items[(id_num, is_fwd, idx)]
    # end def

    def clearPreXoverItems(self):
        for x, y in self.prexover_items.values():
            PreXoverItem.remove(x)
            for z in y:
                PreXoverItem.remove(z)
        self.prexover_items = {}
    # end def

    def activateVirtualHelix(self, virtual_helix_item, per_neighbor_hits):
        """ Populate self.prexover_items dictionary which maps a tuple
        of (id_num, is_fwd, idx) to a given PreXoverItem and a List of neighbor PreXoverItems
        This also effectively deactivates the existing VirtualHelix

        Args:
            virtual_helix_item (VirtualHelixItem):
            per_neighbor_hits (Tuple()):
        """
        # print("ACTIVATING VH", virtual_helix_item.idNum())
        # 1. clear all PreXoverItems
        self.clearPreXoverItems()
        pxis = self.prexover_items
        partitem = self.parentItem()
        this_step_size = virtual_helix_item.getProperty('bases_per_repeat')
        self.virtual_helix_item = virtual_helix_item
        self.updateBasesPerRepeat(this_step_size)
        colors = self._colors
        # the list of neighbors per strand
        id_num = virtual_helix_item.idNum()
        fwd_st, rev_st = True, False
        # 1. Construct PXIs for the active virtual_helix_item
        for neighbor_id, hits in per_neighbor_hits.items():
            fwd_axis_hits, rev_axis_hits = hits
            nvhi = partitem.idToVirtualHelixItem(neighbor_id)
            n_step_size = nvhi.getProperty('bases_per_repeat')
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                # from_virtual_helix_item, from_index, fwd_st, prexoveritemgroup, color):
                neighbor_pxis = []
                # print((id_num, fwd_st, idx))
                pxis[(id_num, fwd_st, idx)] = (PreXoverItem(virtual_helix_item, fwd_st, idx,
                                                        neighbor_id, self, colors[idx % this_step_size]),
                                                neighbor_pxis)
                for j in fwd_idxs:
                    neighbor_pxis.append(   PreXoverItem(nvhi, fwd_st, j,
                                            id_num, self, colors[j % n_step_size]) )
                for j in rev_idxs:
                    neighbor_pxis.append( PreXoverItem(nvhi, rev_st, j,
                                                        id_num, self, colors[-1 - (j % n_step_size)] ))
            for idx, fwd_idxs, rev_idxs in rev_axis_hits:
                neighbor_pxis = []
                # print((id_num, rev_st, idx))
                pxis[(id_num, rev_st, idx)] = ( PreXoverItem(virtual_helix_item, rev_st, idx,
                                                        neighbor_id, self, colors[-1 - (idx % this_step_size)]),
                                                neighbor_pxis)
                for j in fwd_idxs:
                    neighbor_pxis.append(  PreXoverItem(nvhi, fwd_st, j,
                                                        id_num, self, colors[j % n_step_size]))
                for j in rev_idxs:
                    neighbor_pxis.append( PreXoverItem(nvhi, rev_st, j,
                                                        id_num, self, colors[-1 - (j % n_step_size)]))
        # end for per_neighbor_hits
    # end def

    def activateNeighbors(self, id_num, is_fwd, idx):
        print("ACTIVATING neighbors", id_num, idx)
        item = self.prexover_items.get((id_num, is_fwd, idx))
        if item is not None:
            pxi, neighbor_list = item
            print("Should have {} neighbors".format(len(neighbor_list)))
            for k, npxi in enumerate(neighbor_list):
                npxi.activateNeighbor(pxi, shortcut=str(k))
                self.addKeyPress(k, npxi.getInfo())
                self._active_items.append(npxi)
    # end def

    def deactivateNeighbors(self):
        self._key_press_dict = {}
        while self._active_items:
            self._active_items.pop().deactivateNeighbor()

    def updateModelActiveBaseInfo(self, pre_xover_info):
        """Notify model of pre_xover_item hover state.
        Args:
            pre_xover_info (Tuple): from call to getInfo()
        """
        self.part_item.part().setActiveBaseInfo(pre_xover_info)
    # end def
# end class