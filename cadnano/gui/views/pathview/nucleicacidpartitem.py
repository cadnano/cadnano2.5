from __future__ import division

from collections import defaultdict
from math import ceil

from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSlot, QSignalMapper
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem, QInputDialog

from cadnano import app, getBatch, util
from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.ui.mainwindow.svgbutton import SVGButton
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from . import pathstyles as styles
from .activesliceitem import ActiveSliceItem
from .prexoveritem import PreXoverItem
from .strand.xoveritem import XoverNode3
from .virtualhelixitem import VirtualHelixItem


_BASE_WIDTH = _BW = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_MOD_PEN = getPenObj(styles.BLUE_STROKE, 0)
_BOUNDING_RECT_PADDING = 20

_VH_XOFFSET = styles.VH_XOFFSET

class ProxyParentItem(QGraphicsRectItem):
    """an invisible container that allows one to play with Z-ordering"""
    findChild = util.findChild  # for debug


class NucleicAcidPartItem(QGraphicsRectItem, AbstractPartItem):
    findChild = util.findChild  # for debug

    def __init__(self, model_part_instance, viewroot, active_tool_getter, parent):
        """parent should always be pathrootitem"""
        super(NucleicAcidPartItem, self).__init__(parent)
        self._model_instance = model_part_instance
        self._model_part = m_p = model_part_instance.reference()
        self._model_props = m_props = m_p.getPropertyDict()
        self._viewroot = viewroot
        self._getActiveTool = active_tool_getter
        self._active_slice_item = ActiveSliceItem(self, m_p.activeBaseIndex())
        self._active_virtual_helix_item = None
        self._controller = NucleicAcidPartItemController(self, m_p)
        self._pre_xover_items = []  # crossover-related
        self._virtual_helix_hash = {}
        self._virtual_helix_name_hash = {}
        self._virtual_helix_item_list = []
        self._vh_rect = QRectF()
        self.setAcceptHoverEvents(True)
        self._initModifierRect()
        self._proxy_parent = ProxyParentItem(self)
        self._proxy_parent.setFlag(QGraphicsItem.ItemHasNoContents)

        self._sm = sm = QSignalMapper()
        for shortcut, action in self.window().keyActions.items():
            action.triggered.connect(sm.map)
            sm.setMapping(action, shortcut)
        sm.mapped.connect(self._handleKeyPress)
    # end def

    def proxy(self):
        return self._proxy_parent
    # end def

    def modelColor(self):
        return self._model_props['color']
    # end def

    def _initModifierRect(self):
        """docstring for _initModifierRect"""
        self._can_show_mod_rect = False
        self._mod_rect = m_r = QGraphicsRectItem(_DEFAULT_RECT, self)
        m_r.setPen(_MOD_PEN)
        m_r.hide()
    # end def

    def _initResizeButtons(self):
        """Instantiate the buttons used to change the canvas size."""
        self._add_bases_button = SVGButton(":/pathtools/add-bases", self)
        self._add_bases_button.clicked.connect(self._addBasesClicked)
        self._add_bases_button.hide()
        self._remove_bases_button = SVGButton(":/pathtools/remove-bases", self)
        self._remove_bases_button.clicked.connect(self._removeBasesClicked)
        self._remove_bases_button.hide()
    # end def

    def vhItemForVH(self, vhref):
        """Returns the pathview VirtualHelixItem corresponding to vhref"""
        vh = self._model_part.virtualHelix(vhref)
        return self._virtual_helix_hash.get(vh.coord())

    ### SIGNALS ###

    ### SLOTS ###
    def partOligoAddedSlot(self, part, oligo):
        pass
    # end def

    def partParentChangedSlot(self, sender):
        """docstring for partParentChangedSlot"""
        pass
    # end def

    def partActiveVirtualHelixChangedSlot(self, part, virtual_helix):
        self.updatePreXoverItems()
    #end def

    def partDimensionsChangedSlot(self, part, zoom_to_fit):
        if zoom_to_fit:
            self.scene().views()[0].zoomToFit()
        self._active_slice_item.resetBounds()
        self._updateBoundingRect()
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        if is_selected:
            self.resetPen(styles.SELECTED_COLOR, styles.SELECTED_PEN_WIDTH)
            self.resetBrush(styles.SELECTED_BRUSH_COLOR, styles.SELECTED_ALPHA)
            # self.setZValue(styles.ZPARTITEM+1)
        else:
            self.resetPen(self.modelColor())
            self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)
            # self.setZValue(styles.ZPARTITEM)


    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            self._model_props[property_key] = new_value
            if property_key == 'color':
                self._updateBoundingRect()
                for vhi in self._virtual_helix_item_list:
                    vhi.handle().refreshColor()
            elif property_key == 'max_vhelix_length':
                vhis = self._virtual_helix_item_list
                if vhis:
                    old_value = vhis[0]._max_base+1
                    delta = int(new_value)-old_value
                    self.part().resizeVirtualHelices(0, delta)
                    for vhi in vhis:
                        vhi.resize()
                self._updateBoundingRect()
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot"""
        self._active_slice_item.removed()
        self.parentItem().removePartItem(self)
        scene = self.scene()
        scene.removeItem(self)
        self._model_part = None
        self._virtual_helix_hash = None
        self._virtual_helix_name_hash = None
        self._virtual_helix_item_list = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPreDecoratorSelectedSlot(self, sender, row, col, base_idx):
        """docstring for partPreDecoratorSelectedSlot"""
        part = self._model_part
        vh = part.virtualHelixAtCoord((row,col))
        vhi = self.itemForVirtualHelix(vh)
        y_offset = _BW if vh.isEvenParity() else 0
        p = QPointF(base_idx*_BW, vhi.y() + y_offset)
        view = self.window().path_graphics_view
        view.scene_root_item.resetTransform()
        view.centerOn(p)
        view.zoomIn()
        self._mod_rect.setPos(p)
        if self._can_show_mod_rect:
            self._mod_rect.show()
    # end def

    def partVirtualHelixAddedSlot(self, sender, model_virtual_helix):
        """
        When a virtual helix is added to the model, this slot handles
        the instantiation of a virtualhelix item.
        """
        vh = model_virtual_helix
        vhi = VirtualHelixItem(self, model_virtual_helix, self._viewroot)
        self._virtual_helix_hash[vh.coord()] = vhi
        self._virtual_helix_name_hash[vh.getName()] = vhi
        # reposition when first VH is added
        if len(self._virtual_helix_item_list) == 0:
            view = self.window().path_graphics_view
            p = view.scene_root_item.childrenBoundingRect().bottomLeft()
            _p = _BOUNDING_RECT_PADDING
            self.setPos(p.x() + _VH_XOFFSET, p.y() + _p*3)

        self._virtual_helix_item_list.append(vhi)
        ztf = not getBatch()
        self._setVirtualHelixItemList(self._virtual_helix_item_list, zoom_to_fit=ztf)
        self._updateBoundingRect()

    # end def

    def partVirtualHelixRenumberedSlot(self, sender, coord):
        """Notifies the virtualhelix at coord to change its number"""
        vh = self._virtual_helix_hash[coord]
        # check for new number
        # notify VirtualHelixHandleItem to update its label
        # notify VirtualHelix to update its xovers
        # if the VirtualHelix is active, refresh prexovers
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender, coord):
        """Notifies the virtualhelix at coord to resize."""
        vh = self._virtual_helix_hash[coord]
        vh.resize()
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, ordered_coord_list, check_batch):
        """docstring for partVirtualHelicesReorderedSlot"""
        new_list = self._virtual_helix_item_list
        decorated = [(ordered_coord_list.index(vhi.coord()), vhi)\
                        for vhi in self._virtual_helix_item_list]
        decorated.sort()
        new_list = [vhi for idx, vhi in decorated]

        ztf = not getBatch() if check_batch == True else False
        self._setVirtualHelixItemList(new_list, zoom_to_fit=ztf)
    # end def

    def updatePreXoverItemsSlot(self, sender, virtual_helix):
        part = self.part()
        if virtual_helix is None:
            self.setPreXoverItemsVisible(None)
        elif part.areSameOrNeighbors(part.activeVirtualHelix(), virtual_helix):
            vhi = self.itemForVirtualHelix(virtual_helix)
            self.setActiveVirtualHelixItem(vhi)
            self.setPreXoverItemsVisible(self.activeVirtualHelixItem())
    # end def

    ### ACCESSORS ###

    def activeVirtualHelixItem(self):
        return self._active_virtual_helix_item
    # end def

    def part(self):
        """Return a reference to the model's part object"""
        return self._model_part
    # end def

    def document(self):
        """Return a reference to the model's document object"""
        return self._model_part.document()
    # end def

    def removeVirtualHelixItem(self, virtual_helix_item):
        vh = virtual_helix_item.virtualHelix()
        self._virtual_helix_item_list.remove(virtual_helix_item)
        del self._virtual_helix_hash[vh.coord()]
        del self._virtual_helix_name_hash[vh.getName()]
        ztf = not getBatch()
        self._setVirtualHelixItemList(self._virtual_helix_item_list,
            zoom_to_fit=ztf)
        self._updateBoundingRect()

    # end def

    def itemForVirtualHelix(self, virtual_helix):
        return self._virtual_helix_hash[virtual_helix.coord()]
    # end def

    def getVHItemByName(self, vh_name):
        return self._virtual_helix_name_hash[vh_name]

    def virtualHelixBoundingRect(self):
        return self._vh_rect
    # end def

    def window(self):
        return self.parentItem().window()
    # end def

    ### PRIVATE METHODS ###
    def _addBasesClicked(self):
        part = self._model_part
        step = part.stepSize()
        self._addBasesDialog = dlg = QInputDialog(self.window())
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntMinimum(0)
        dlg.setIntValue(step)
        dlg.setIntMaximum(100000)
        dlg.setIntStep(step)
        dlg.setLabelText(( "Number of bases to add to the existing"\
                         + " %i bases\n(must be a multiple of %i)")\
                         % (part.maxBaseIdx(), step))
        dlg.intValueSelected.connect(self._addBasesCallback)
        dlg.open()
    # end def

    @pyqtSlot(int)
    def _addBasesCallback(self, n):
        """
        Given a user-chosen number of bases to add, snap it to an index
        where index modulo stepsize is 0 and calls resizeVirtualHelices to
        adjust to that size.
        """
        part = self._model_part
        self._addBasesDialog.intValueSelected.disconnect(self._addBasesCallback)
        del self._addBasesDialog
        maxDelta = n // part.stepSize() * part.stepSize()
        part.resizeVirtualHelices(0, maxDelta)
    # end def

    def _removeBasesClicked(self):
        """
        Determines the minimum maxBase index where index modulo stepsize == 0
        and is to the right of the rightmost nonempty base, and then resize
        each calls the resizeVirtualHelices to adjust to that size.
        """
        part = self._model_part
        step_size = part.stepSize()
        # first find out the right edge of the part
        idx = part.indexOfRightmostNonemptyBase()
        # next snap to a multiple of stepsize
        idx = ceil((idx + 1) / step_size)*step_size
        # finally, make sure we're a minimum of step_size bases
        idx = util.clamp(idx, step_size, 10000)
        delta = idx - (part.maxBaseIdx() + 1)
        if delta < 0:
            part.resizeVirtualHelices(0, delta)
    # end def

    def _setVirtualHelixItemList(self, new_list, zoom_to_fit=True):
        """
        Give me a list of VirtualHelixItems and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.
        """
        y = 0  # How far down from the top the next PH should be
        _z = 0
        leftmost_extent = 0
        rightmost_extent = 0

        scene = self.scene()
        vhi_rect = None
        vhi_h_rect = None
        vhi_h_selection_group = self._viewroot._vhi_h_selection_group
        for vhi in new_list:
            vh = vhi.virtualHelix()
            _z = vh.getProperty('z')
            vhi.setPos(_z, y)
            if vhi_rect is None:
                vhi_rect = vhi.boundingRect()
                step = vhi_rect.height() + styles.PATH_HELIX_PADDING
            # end if

            # get the VirtualHelixHandleItem
            vhi_h = vhi.handle()
            do_reselect = False
            if vhi_h.parentItem() == vhi_h_selection_group:
                do_reselect = True

            vhi_h.tempReparent()    # so positioning works

            if vhi_h_rect is None:
                vhi_h_rect = vhi_h.boundingRect()

            vhi_h_x = _z-_VH_XOFFSET
            vhi_h_y = y+(vhi_rect.height() - vhi_h_rect.height()) / 2
            vhi_h.setPos(vhi_h_x, vhi_h_y)

            leftmost_extent = min(leftmost_extent, vhi_h_x)
            rightmost_extent = max(rightmost_extent, vhi_rect.width())
            y += step
            self.updateXoverItems(vhi)
            if do_reselect:
                vhi_h_selection_group.addToGroup(vhi_h)
        # end for

        self._virtual_helix_item_list = new_list
        if zoom_to_fit:
            self.scene().views()[0].zoomToFit()
    # end def

    def resetPen(self, color, width=0):
        pen = getPenObj(color, width)
        self.setPen(pen)
    # end def

    def resetBrush(self, color, alpha):
        brush = getBrushObj(color, alpha=alpha)
        self.setBrush(brush)
    # end def

    def _updateBoundingRect(self):
        """
        Updates the bounding rect to the size of the childrenBoundingRect,
        and refreshes the addBases and removeBases buttons accordingly.

        Called by partVirtualHelixAddedSlot, partDimensionsChangedSlot, or
        removeVirtualHelixItem.
        """
        self.setPen(getPenObj(self.modelColor(), 0))
        self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)
        self._vh_rect = self.childrenBoundingRect()
        _p = _BOUNDING_RECT_PADDING
        self.setRect(self._vh_rect.adjusted(-_p,-_p,_p,_p))
    # end def

    def _handleKeyPress(self, key):
        if key not in self._keyPressDict:
            return

        # active item
        active = self._model_part.getProperty('active_phos')
        a_vh_name, a_fwd_str, a_base_idx, a_facing_angle = active.split('.')
        a_strand_idx = 0 if a_fwd_str == 'fwd' else 1
        a_idx = int(a_base_idx)
        a_vhi = self.getVHItemByName(a_vh_name)
        a_vh = a_vhi.virtualHelix()


        neighbor = self._keyPressDict[key]
        n_vh_name, n_fwd_str, n_base_idx, n_facing_angle = neighbor.split('.')
        n_strand_idx = 0 if n_fwd_str == 'fwd' else 1
        n_idx = int(n_base_idx)
        n_vhi = self.getVHItemByName(n_vh_name)
        n_vh = n_vhi.virtualHelix()

        if not a_vh.hasStrandAtIdx(a_idx)[a_strand_idx]: return
        if not n_vh.hasStrandAtIdx(n_idx)[n_strand_idx]: return

        a_strandset = a_vh.getStrandSetByIdx(a_strand_idx)
        n_strandset = n_vh.getStrandSetByIdx(n_strand_idx)

        strand5p = a_strandset.getStrand(a_idx)
        strand3p = n_strandset.getStrand(n_idx)
        # print("createXover", strand5p, a_idx, strand3p, n_idx)
        if not strand5p.connection3p():
            self.part().createXover(strand5p, a_idx, strand3p, n_idx)
    # end def

    ### PUBLIC METHODS ###
    def setKeyPressDict(self, shortcut_item_dict):
        self._keyPressDict = shortcut_item_dict


    def setModifyState(self, bool):
        """Hides the modRect when modify state disabled."""
        self._can_show_mod_rect = bool
        if bool == False:
            self._mod_rect.hide()

    def getOrderedVirtualHelixList(self):
        """Used for encoding."""
        ret = []
        for vhi in self._virtual_helix_item_list:
            ret.append(vhi.coord())
        return ret
    # end def

    def numberOfVirtualHelices(self):
        return len(self._virtual_helix_item_list)
    # end def

    def reorderHelices(self, first, last, index_delta):
        """
        Reorder helices by moving helices _pathHelixList[first:last]
        by a distance delta in the list. Notify each PathHelix and
        PathHelixHandle of its new location.
        """
        vhi_list = self._virtual_helix_item_list
        helix_numbers = [vhi.number() for vhi in vhi_list]
        first_index = helix_numbers.index(first)
        last_index = helix_numbers.index(last) + 1

        if index_delta < 0:  # move group earlier in the list
            new_index = max(0, index_delta + first_index)
            new_list = vhi_list[0:new_index] +\
                                vhi_list[first_index:last_index] +\
                                vhi_list[new_index:first_index] +\
                                vhi_list[last_index:]
        # end if
        else:  # move group later in list
            new_index = min(len(vhi_list), index_delta + last_index)
            new_list = vhi_list[:first_index] +\
                                 vhi_list[last_index:new_index] +\
                                 vhi_list[first_index:last_index] +\
                                 vhi_list[new_index:]
        # end else

        # call the method to move the items and store the list
        self.part().setImportedVHelixOrder([vhi.coord() for vhi in new_list], check_batch=False)
        # self._setVirtualHelixItemList(new_list, zoom_to_fit=False)
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi):
        if new_active_vhi != self._active_virtual_helix_item:
            self._active_virtual_helix_item = new_active_vhi
            # self._model_part.setActiveVirtualHelix(new_active_vhi.virtualHelix())
    # end def

    def setPreXoverItemsVisible(self, virtual_helix_item):
        """
        self._pre_xover_items list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers
        """
        vhi = virtual_helix_item

        if vhi is None:
            if self._pre_xover_items:
                # clear all PreXoverItems
                list(map(PreXoverItem.remove, self._pre_xover_items))
                self._pre_xover_items = []
            return

        vh = vhi.virtualHelix()
        Dna_part_item = self
        part = self.part()
        idx = part.activeVirtualHelixIdx()

        # clear all PreXoverItems
        list(map(PreXoverItem.remove, self._pre_xover_items))
        self._pre_xover_items = []

        _PXI = PreXoverItem
        potential_xovers = part.potentialCrossoverList(vh, idx)

        # for neighbor, index, strand_type, is_low_idx in potential_xovers:
        #     # create one half
        #     neighbor_vhi = self.itemForVirtualHelix(neighbor)
        #     pxi = _PXI(vhi, neighbor_vhi, index, strand_type, is_low_idx)
        #     # add to list
        #     self._pre_xover_items.append(pxi)
        #     # create the complement
        #     pxi = _PXI(neighbor_vhi, vhi, index, strand_type, is_low_idx)
        #     # add to list
        #     self._pre_xover_items.append(pxi)
        # # end for
    # end def

    def updatePreXoverItems(self):
        self.setPreXoverItemsVisible(self.activeVirtualHelixItem())
    # end def

    def updateXoverItems(self, virtual_helix_item):
        for item in virtual_helix_item.childItems():
            if isinstance(item, XoverNode3):
                item.refreshXover()
     # end def

    def updateStatusBar(self, status_string):
        """Shows status_string in the MainWindow's status bar."""
        self.window().statusBar().showMessage(status_string)

    ### COORDINATE METHODS ###
    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)"""
        vhs = self._virtual_helix_item_list
        return vhs[0].keyPanDeltaX() if vhs else 5
    # end def

    def keyPanDeltaY(self):
        """How far an an arrow key should move the scene (in scene space)
        for a single press"""
        vhs = self._virtual_helix_item_list
        if not len(vhs) > 1:
            return 5
        dy = vhs[0].pos().y() - vhs[1].pos().y()
        dummyRect = QRectF(0, 0, 1, dy)
        return self.mapToScene(dummyRect).boundingRect().height()
    # end def

    ### TOOL METHODS ###
    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event.pos())
    # end def

    def pencilToolHoverMove(self, pt):
        """Pencil the strand is possible."""
        Dna_part_item = self
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromPartItem(self, pt)
    # end def
