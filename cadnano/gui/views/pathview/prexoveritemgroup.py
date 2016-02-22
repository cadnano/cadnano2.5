from PyQt5.QtWidgets import QGraphicsRectItem
from .prexoveritem import PreXoverItem, PHOS_ITEM_WIDTH, BASE_WIDTH

class PreXoverItemGroup(QGraphicsRectItem):
    HUE_FACTOR = 1.6

    def __init__(self, virtualhelixitem):
        super(QGraphicsRectItem, self).__init__(virtual_helix_item)
        self._parent = virtual_helix_item
        self.setPen(getNoPen())
        self._colors = []
        self._fwd_pxo_items = {}
        self._rev_pxo_items = {}
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
    def addRepeats(self, n=None):
        """
        Adds n*bases_per_repeat PreXoverItems to fwd and rev groups.
        If n is None, get the value from the parent VHI.
        """
        step_size, num_repeats = self._parent.getProperty(['bases_per_repeat', 'repeats'])
        if n is None:
            n = num_repeats
            start_idx = 0
        else:
            start_idx = len(self._fwd_pxo_items)
        end_idx = start_idx + n*step_size

        iw, half_iw = PHOS_ITEM_WIDTH, 0.5*PHOS_ITEM_WIDTH
        bw, half_bw, bw2 = BASE_WIDTH, 0.5*BASE_WIDTH, 2*BASE_WIDTH
        for i in range(start_idx, end_idx, step_size):
            for j in range(step_size):
                fwd = PreXoverItem(i, j, self._colors[j], is_fwd=True, parent=self)
                rev = PreXoverItem(i, j, self._colors[-1 - j], is_fwd=False, parent=self)
                fwd.setPos((i + j)*bw, -bw)
                rev.setPos((i + j)*bw, bw2)
                self._fwd_pxo_items[i + j] = fwd
                self._rev_pxo_items[i + j] = rev
            # end for
        # end for
        canvas_size = self._parent.maxLength()
        self.setRect(0, 0, bw*canvas_size, bw2)
    # end def

    def removeRepeats(self):
        """
        remove all PreXoverItems from fwd and rev groups.
        """
        for i in range(len(self._fwd_pxo_items)):
            self.scene().removeItem(self._fwd_pxo_items.pop())
            self.scene().removeItem(self._rev_pxo_items.pop())
    # end def

    def updateBasesPerRepeat(self):
        """Recreates colors, all vhi"""
        step_size = self._parent.getProperty('bases_per_repeat')
        hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        self.removeRepeats()
        self.addRepeats()
    # end def

    def updateTurnsPerRepeat(self):
        pass
    # end def

    def part(self):
        return self._parent.part()

    ### PUBLIC SUPPORT METHODS ###
    def getItem(self, is_fwd, idx):
        if is_fwd:
            if idx in self._fwd_pxo_items:
                return self._fwd_pxo_items[idx]
        else:
            if idx in self._rev_pxo_items:
                return self._rev_pxo_items[idx]
        return None
    # end def

    def resize(self):
        old_max = len(self._fwd_pxo_items)
        new_max = self._parent.maxLength()
        if new_max == old_max:
            return
        elif new_max > old_max:
            bpr = self._parent.getProperty('bases_per_repeat')
            self._add_pxitems(old_max + 1, new_max, bpr)
        else:
            self._rm_pxitems_after(new_max)
        self._max_base = new_max
    # end def

    def clear(self):
        for x in self._pre_xover_items: PreXoverItem.remove(x)
        self._pre_xover_items = {}
    # end def

    def setActiveVirtualHelix(self, virtual_helix_item, per_neighbor_hits):
        """
        Args:
            virtual_helix_item (VirtualHelixItem):
            per_neighbor_hits (Tuple()):
        """
        # 1. clear all PreXoverItems
        for x in self._pre_xover_items: PreXoverItem.remove(x)
        self._pre_xover_items = {}
        pxis = self._pre_xover_items
        colors = self._colors
        this_step_size = virtual_helix_item.getProperty(['bases_per_repeat'])
        self._active_virtual_helix_item = virtual_helix_item
        # the list of neighbots per strand
        id_num = virtual_helix_item.idNum()
        # 1. Construct PXIs for the active virtual_helix_item
        for neighbor_id, hits in per_neighbor_hits:
            fwd_axis_hits, rev_axis_hits = hits
            nvhi = self._virtual_helix_item_hash[neighbor_id]
            n_step_size = nvhi.getProperty(['bases_per_repeat'])
            for idx, fwd_idxs, rev_idxs in fwd_axis_hits:
                # from_virtual_helix_item, from_index, is_fwd, prexoveritemgroup, color):
                pxis[(id_num, idx, True)] = PreXoverItem(virtual_helix_item, idx, True,
                                                        neighbor_id, self, colors[idx % this_step_size])
                for j in fwd_idxs:
                    pxis[(neighbor_id, j, True)] = PreXoverItem(nvhi, j, True,
                                                        id_num, self, colors[j % n_step_size])
                for j in rev_idxs:
                    pxis[(neighbor_id, j, False)] = PreXoverItem(nvhi, j, False,
                                                        id_num, self, colors[(-1-(j % n_step_size)])
            for idx, fwd_idxs, rev_idxs in rev_axis_hits:
                pxis[(id_num, idx, False)] = PreXoverItem(virtual_helix_item, idx, False,
                                                        neighbor_id, self, colors[-1 - (idx % this_step_size)])
                for j in fwd_idxs:
                    pxis[(neighbor_id, j, True)] = PreXoverItem(nvhi, j, True,
                                                        id_num, self, colors[j % n_step_size])
                for j in rev_idxs:
                    pxis[(neighbor_id, j, False)] = PreXoverItem(nvhi, j, False,
                                                        id_num, self, colors[(-1-(j % n_step_size)])
        # end for per_neighbor_hits
    # end def

    def setActiveNeighbors(self, active_item, fwd_idxs, rev_idxs):
        # active_item is a PreXoverItem
        if active_item:
            active_absolute_idx = active_item.absoluteIdx()
            bpr = self._parent.getProperty('bases_per_repeat')
            cutoff = bpr / 2
            active_idx = active_item.baseIdx()
            step_idxs = range(0, self._parent.maxLength(), bpr)
            k = 0
            pre_xovers = {}
            for i, j in product(fwd_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                delta = item.absoluteIdx() - active_absolute_idx
                if abs(delta) < cutoff and k < 10:
                    item.setActiveNeighbor(active_item, shortcut=str(k))
                    pre_xovers[k] = item.name()
                    k += 1
                    self._active_items.append(item)
            for i, j in product(rev_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._rev_pxo_items[i+j]
                delta = item.absoluteIdx() - active_absolute_idx
                if abs(delta) < cutoff and k < 10:
                    item.setActiveNeighbor(active_item, shortcut=str(k))
                    pre_xovers[k] = item.name()
                    k += 1
                    self._active_items.append(item)
            self._parent.partItem().setKeyPressDict(pre_xovers)
        else:
            self._parent.partItem().setKeyPressDict({})
            while self._active_items:
                self._active_items.pop().setActiveNeighbor(None)
    # end def

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

    def updateModelActivePhos(self, pre_xover_item):
        """Notify model of pre_xover_item hover state."""
        vhi = self._parent
        model_part = vhi.part()
        id_num = self._parent.idNum()
        if pre_xover_item is None:
            model_part.setProperty('active_phos', None)
            return
        vh_name, vh_angle  = vhi.getProperty(['name', 'eulerZ'])
        idx = pre_xover_item.baseIdx() # (f|r).step_idx
        is_fwd = 'fwd' if pre_xover_item.isFwd() else 'rev'
        value = '%s.%s.%d' % (vh_name, is_fwd, idx)
        model_part.setProperty('active_phos', value)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        while self._active_items:
            self._active_items.pop().setActive(False)
        if new_active_item:
            new_active_item.setActive(True)
            self._active_items.append(new_active_item)
    # end def
# end class