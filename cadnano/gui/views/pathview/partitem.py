from __future__ import division
from collections import defaultdict
from math import ceil

from .activesliceitem import ActiveSliceItem
from cadnano.gui.controllers.itemcontrollers.partitemcontroller import PartItemController
from .prexoveritem import PreXoverItem
from .strand.xoveritem import XoverNode3
from cadnano.gui.ui.mainwindow.svgbutton import SVGButton
from . import pathstyles as styles
from .virtualhelixitem import VirtualHelixItem
import cadnano.util as util

from cadnano import app, getBatch

from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSlot

from PyQt5.QtGui import QBrush,  QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem, QInputDialog

_BASE_WIDTH = _BW = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_MOD_PEN = QPen(styles.BLUE_STROKE)

class ProxyParentItem(QGraphicsRectItem):
    """an invisible container that allows one to play with Z-ordering"""
    findChild = util.findChild  # for debug


class PartItem(QGraphicsRectItem):
    findChild = util.findChild  # for debug

    def __init__(self, model_part, viewroot, active_tool_getter, parent):
        """parent should always be pathrootitem"""
        super(PartItem, self).__init__(parent)
        self._model_part = m_p = model_part
        self._viewroot = viewroot
        self._getActiveTool = active_tool_getter
        self._activeSliceItem = ActiveSliceItem(self, m_p.activeBaseIndex())
        self._active_virtual_helix_item = None
        self._controller = PartItemController(self, m_p)
        self._pre_xover_items = []  # crossover-related
        self._virtual_helix_hash = {}
        self._virtual_helix_item_list = []
        self._vh_rect = QRectF()
        self.setAcceptHoverEvents(True)
        self._initModifierRect()
        self._initResizeButtons()
        self._proxy_parent = ProxyParentItem(self)
        self._proxy_parent.setFlag(QGraphicsItem.ItemHasNoContents)
    # end def
    
    def proxy(self):
        return self._proxy_parent
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
    def partParentChangedSlot(self, sender):
        """docstring for partParentChangedSlot"""
        # print "PartItem.partParentChangedSlot"
        pass
    # end def

    def partHideSlot(self, sender):
        self.hide()
    # end def

    def partActiveVirtualHelixChangedSlot(self, part, virtual_helix):
        self.updatePreXoverItems()
    #end def

    def partDimensionsChangedSlot(self, part):
        if len(self._virtual_helix_item_list) > 0:
            vhi = self._virtual_helix_item_list[0]
            vhi_rect = vhi.boundingRect()
            vhi_h_rect = vhi.handle().boundingRect()
            self._vh_rect.setLeft(vhi_h_rect.left())
            self._vh_rect.setRight(vhi_rect.right())
        self.scene().views()[0].zoomToFit()
        self._activeSliceItem.resetBounds()
        self._updateBoundingRect()
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot"""
        self._activeSliceItem.removed()
        self.parentItem().removePartItem(self)
        scene = self.scene()
        scene.removeItem(self)
        self._model_part = None
        self._virtual_helix_hash = None
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
        # print("PartItem.partVirtualHelixAddedSlot")
        vh = model_virtual_helix
        vhi = VirtualHelixItem(self, model_virtual_helix, self._viewroot)
        self._virtual_helix_hash[vh.coord()] = vhi
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

    def partVirtualHelicesReorderedSlot(self, sender, ordered_coord_list):
        """docstring for partVirtualHelicesReorderedSlot"""
        new_list = self._virtual_helix_item_list
        decorated = [(ordered_coord_list.index(vhi.coord()), vhi)\
                        for vhi in self._virtual_helix_item_list]
        decorated.sort()
        new_list = [vhi for idx, vhi in decorated]
        ztf = not getBatch()
        self._setVirtualHelixItemList(new_list, zoom_to_fit=ztf)
    # end def

    def updatePreXoverItemsSlot(self, sender, virtual_helix):
        part = self.part()
        if virtual_helix == None:
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
        ztf = not getBatch()
        self._setVirtualHelixItemList(self._virtual_helix_item_list, 
            zoom_to_fit=ztf)
        self._updateBoundingRect()

    # end def

    def itemForVirtualHelix(self, virtual_helix):
        return self._virtual_helix_hash[virtual_helix.coord()]
    # end def

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
        # if app().isInMaya():
        #     import maya.cmds as cmds
        #     cmds.select(clear=True)
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
            # if app().isInMaya():
            #     import maya.cmds as cmds
            #     cmds.select(clear=True)
    # end def

    def _setVirtualHelixItemList(self, new_list, zoom_to_fit=True):
        """
        Give me a list of VirtualHelixItems and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.
        """
        y = 0  # How far down from the top the next PH should be
        leftmost_extent = 0
        rightmost_extent = 0

        scene = self.scene()
        vhi_rect = None
        vhi_h_rect = None

        for vhi in new_list:
            vhi.setPos(0, y)
            if vhi_rect is None:
                vhi_rect = vhi.boundingRect()
                step = vhi_rect.height() + styles.PATH_HELIX_PADDING
            # end if

            # get the VirtualHelixHandleItem
            vhi_h = vhi.handle()
            if vhi_h.parentItem() != self._viewroot._vhi_h_selection_group:
                vhi_h.setParentItem(self)

            if vhi_h_rect is None:
                vhi_h_rect = vhi_h.boundingRect()

            vhi_h.setPos(-2 * vhi_h_rect.width(), y + (vhi_rect.height() - vhi_h_rect.height()) / 2)

            leftmost_extent = min(leftmost_extent, -2 * vhi_h_rect.width())
            rightmost_extent = max(rightmost_extent, vhi_rect.width())
            y += step
            self.updateXoverItems(vhi)
        # end for
        self._vh_rect = QRectF(leftmost_extent, -40, -leftmost_extent + rightmost_extent, y + 40)
        self._virtual_helix_item_list = new_list
        if zoom_to_fit:
            self.scene().views()[0].zoomToFit()
    # end def

    def _updateBoundingRect(self):
        """
        Updates the bounding rect to the size of the childrenBoundingRect,
        and refreshes the addBases and removeBases buttons accordingly.

        Called by partVirtualHelixAddedSlot, partDimensionsChangedSlot, or
        removeVirtualHelixItem.
        """
        self.setPen(QPen(Qt.NoPen))
        self.setRect(self.childrenBoundingRect())
        # move and show or hide the buttons if necessary
        add_button = self._add_bases_button
        rm_button = self._remove_bases_button
        if len(self._virtual_helix_item_list) > 0:
            addRect = add_button.boundingRect()
            rmRect = rm_button.boundingRect()
            x = self._vh_rect.right()
            y = -styles.PATH_HELIX_PADDING
            add_button.setPos(x, y)
            rm_button.setPos(x-rmRect.width(), y)
            add_button.show()
            rm_button.show()
        else:
            add_button.hide()
            rm_button.hide()
    # end def

    ### PUBLIC METHODS ###
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
        self._setVirtualHelixItemList(new_list, zoom_to_fit=False)
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

        if vhi == None:
            if self._pre_xover_items:
                # clear all PreXoverItems
                list(map(PreXoverItem.remove, self._pre_xover_items))
                self._pre_xover_items = []
            return

        vh = vhi.virtualHelix()
        part_item = self
        part = self.part()
        idx = part.activeVirtualHelixIdx()

        # clear all PreXoverItems
        list(map(PreXoverItem.remove, self._pre_xover_items))
        self._pre_xover_items = []

        potential_xovers = part.potentialCrossoverList(vh, idx)
        for neighbor, index, strand_type, is_low_idx in potential_xovers:
            # create one half
            neighbor_vhi = self.itemForVirtualHelix(neighbor)
            pxi = PreXoverItem(vhi, neighbor_vhi, index, strand_type, is_low_idx)
            # add to list
            self._pre_xover_items.append(pxi)
            # create the complement
            pxi = PreXoverItem(neighbor_vhi, vhi, index, strand_type, is_low_idx)
            # add to list
            self._pre_xover_items.append(pxi)
        # end for
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
        part_item = self
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromPartItem(self, pt)
    # end def
