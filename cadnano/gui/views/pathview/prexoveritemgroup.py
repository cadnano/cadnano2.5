from PyQt5.QtWidgets import QGraphicsRectItem
from .prexoveritem import PreXoverItem, PHOS_ITEM_WIDTH, BASE_WIDTH
from cadnano.enum import StrandType

class PreXoverItemGroup(QGraphicsRectItem):
    HUE_FACTOR = 1.6

    def __init__(self, virtualhelixitem):
        super(QGraphicsRectItem, self).__init__(virtual_helix_item)
        self._parent = virtual_helix_item
        self.setPen(getNoPen())
        self._colors = []
        # dictionary of tuple of a (PreXoverItem, List[PreXoverItem])
        self.prexover_items = {}
        self._active_items = []
        self.updateBasesPerRepeat()
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._parent.window()

    def virtualHelixItem(self):
        return self.parentItem():
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def updateBasesPerRepeat(self):
        """Recreates colors, all vhi"""
        step_size = self._parent.getProperty('bases_per_repeat')
        hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        # self.removeRepeats()
        # self.addRepeats()
    # end def

    def updateTurnsPerRepeat(self):
        pass
    # end def

    def part(self):
        return self._parent.part()

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

    def setActiveVirtualHelix(self, virtual_helix_item, per_neighbor_hits):
        """ Populate self.prexover_items dictionary which maps a tuple
        of (id_num, is_fwd, idx) to a given PreXoverItem and a List of neighbor PreXoverItems

        Args:
            virtual_helix_item (VirtualHelixItem):
            per_neighbor_hits (Tuple()):
        """
        # 1. clear all PreXoverItems
        self.clearPreXoverItems()
        pxis = self.prexover_items

        colors = self._colors
        this_step_size = virtual_helix_item.getProperty(['bases_per_repeat'])
        self._active_virtual_helix_item = virtual_helix_item
        # the list of neighbots per strand
        id_num = virtual_helix_item.idNum()
        fwd_st, rev_st = True, False
        # 1. Construct PXIs for the active virtual_helix_item
        for neighbor_id, hits in per_neighbor_hits:
            fwd_axis_hits, rev_axis_hits = hits
            nvhi = self._virtual_helix_item_hash[neighbor_id]
            n_step_size = nvhi.getProperty(['bases_per_repeat'])
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                # from_virtual_helix_item, from_index, fwd_st, prexoveritemgroup, color):
                neighbor_pxis = []
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
                pxis[(id_num, idx, rev_st)] = ( PreXoverItem(virtual_helix_item, rev_st, idx,
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

    def setActiveNeighbors(self, id_num, is_fwd, idx):
        pxi, neighbor_list = self.prexover_items[(id_num, is_fwd, idx)]
        neighbor_keys = {}
        for i, npxi in enumerate(neighbor_list):
            npxi.setActiveNeighbor(pxi, shortcut=str(k))
            neighbor_keys[k] = npxi.getInfo()
            self._active_items.append(npxi)
        self._parent.partItem().setKeyPressDict(neighbor_keys)
    # end def

    def deactivateNeighbors(self):
        self._parent.partItem().setKeyPressDict({})
        while self._active_items:
            self._active_items.pop().deactivateNeighbor()

    def setProximalItems(self, prox_groups):
        max_length = self._parent.maxLength()
        inactive_fwd = set(range(max_length))
        inactive_rev = set(range(max_length))
        bpr = self._parent.getProperty('bases_per_repeat')
        step_idxs = range(0, max_length, bpr)
        id_
        for this_idx, neighbor_id, idxs in fwd_hits:
            item = self._fwd_pxo_items[this_idx]
            item.setProximal(True, id_num=neighbor_id)


        for id_num, fwd_idxs, rev_idxs in prox_groups:

            for i, j in product(fwd_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                item.setProximal(True, id_num=id_num, colliding=is_colliding)
                if idx in inactive_fwd:
                    inactive_fwd.remove(idx)
            for i, j in product(rev_idxs, step_idxs):
                idx = i + j
                if not idx in self._rev_pxo_items:
                    continue
                item = self._rev_pxo_items[i + j]
                item.setProximal(True, id_num=id_num, colliding=is_colliding)
                if idx in inactive_rev:
                    inactive_rev.remove(idx)
        for idx in list(inactive_fwd):
            self._fwd_pxo_items[idx].setProximal(False)
        for idx in list(inactive_rev):
            self._rev_pxo_items[idx].setProximal(False)


    def updatePositionsAfterRotation(self, angle):
        bw = BASE_WIDTH
        part = self._parent.part()
        canvas_size = self._parent.maxLength()
        bpr = self._parent.getProperty('bases_per_repeat')
        xdelta = angle / 360. * bw*bpr
        for i, item in self._fwd_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
        for i, item in self._rev_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
    # end def

    def updateModelActiveBase(self, pre_xover_info):
        """Notify model of pre_xover_item hover state.
        Args:
            pre_xover_info (Tuple): from call to getInfo()
        """
        self._part.setProperty('active_base', pre_xover_info)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        while self._active_items:
            self._active_items.pop().setActive(False)
        if new_active_item:
            new_active_item.setActive(True)
            self._active_items.append(new_active_item)
    # end def
# end class