"""Summary
"""
from __future__ import division

from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem

from cadnano import getBatch, util
from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.views.abstractitems.abstractpartitem import QAbstractPartItem
from cadnano.gui.views.grabcorneritem import GrabCornerItem

from . import pathstyles as styles
from .prexovermanager import PreXoverManager
from .strand.xoveritem import XoverNode3
from .virtualhelixitem import VirtualHelixItem

_BASE_WIDTH = _BW = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_MOD_PEN = getPenObj(styles.BLUE_STROKE, 0)
_BOUNDING_RECT_PADDING = 20
_VH_XOFFSET = styles.VH_XOFFSET


class ProxyParentItem(QGraphicsRectItem):
    """an invisible container that allows one to play with Z-ordering

    Attributes:
        findChild (TYPE): Description
    """
    findChild = util.findChild  # for debug


class NucleicAcidPartItem(QAbstractPartItem):
    """Summary

    Attributes:
        active_virtual_helix_item (TYPE): Description
        findChild (TYPE): Description
        grab_corner (TYPE): Description
        prexover_manager (TYPE): Description
    """
    findChild = util.findChild  # for debug

    def __init__(self, model_part_instance, viewroot, parent):
        """parent should always be pathrootitem

        Args:
            model_part_instance (TYPE): Description
            viewroot (TYPE): Description
            parent (TYPE): Description
        """
        super(NucleicAcidPartItem, self).__init__(model_part_instance, viewroot, parent)
        self._getActiveTool = viewroot.manager.activeToolGetter
        self.active_virtual_helix_item = None
        m_p = self._model_part
        self._controller = NucleicAcidPartItemController(self, m_p)
        self.prexover_manager = PreXoverManager(self)
        self._virtual_helix_item_list = []
        self._vh_rect = QRectF()
        self.setAcceptHoverEvents(True)
        self._initModifierRect()
        self._proxy_parent = ProxyParentItem(self)
        self._proxy_parent.setFlag(QGraphicsItem.ItemHasNoContents)
        self._scale_2_model = m_p.baseWidth()/_BASE_WIDTH
        self._scale_2_Qt = _BASE_WIDTH / m_p.baseWidth()
        GC_SIZE = 20
        self.grab_corner = GrabCornerItem(GC_SIZE, m_p.getColor(), False, self)
    # end def

    def proxy(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._proxy_parent
    # end def

    def modelColor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._model_part.getProperty('color')
    # end def

    def convertToModelZ(self, z):
        """scale Z-axis coordinate to the model

        Args:
            z (TYPE): Description
        """
        return z * self._scale_2_model
    # end def

    def convertToQtZ(self, z):
        """Summary

        Args:
            z (TYPE): Description

        Returns:
            TYPE: Description
        """
        return z * self._scale_2_Qt
    # end def

    def _initModifierRect(self):
        """docstring for _initModifierRect
        """
        self._can_show_mod_rect = False
        self._mod_rect = m_r = QGraphicsRectItem(_DEFAULT_RECT, self)
        m_r.setPen(_MOD_PEN)
        m_r.hide()
    # end def

    def vhItemForIdNum(self, id_num):
        """Returns the pathview VirtualHelixItem corresponding to id_num

        Args:
            id_num (TYPE): Description
        """
        return self._virtual_helix_item_hash.get(id_num)

    ### SIGNALS ###

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part, id_num):
        """Summary

        Args:
            part (TYPE): Description
            id_num (TYPE): Description

        Returns:
            TYPE: Description
        """
        vhi = self._virtual_helix_item_hash.get(id_num, None)
        self.setActiveVirtualHelixItem(vhi)
        self.setPreXoverItemsVisible(vhi)
    # end def

    def partActiveBaseInfoSlot(self, part, info):
        """Summary

        Args:
            part (TYPE): Description
            info (TYPE): Description

        Returns:
            TYPE: Description
        """
        pxoig = self.prexover_manager
        pxoig.deactivateNeighbors()
        if info and info is not None:
            id_num, is_fwd, idx, to_vh_id_num = info
            pxoig.activateNeighbors(id_num, is_fwd, idx)
    # end def

    def partZDimensionsChangedSlot(self, model_part, min_id_num, max_id_num, ztf=False):
        """Summary

        Args:
            model_part (TYPE): Description
            min_id_num (TYPE): Description
            max_id_num (TYPE): Description
            ztf (bool, optional): Description

        Returns:
            TYPE: Description
        """
        if len(self._virtual_helix_item_list) > 0:
            vhi_hash = self._virtual_helix_item_hash
            vhi_max = vhi_hash[max_id_num]
            vhi_rect_max = vhi_max.boundingRect()
            self._vh_rect.setRight(vhi_rect_max.right() + vhi_max.x())

            vhi_min = vhi_hash[min_id_num]
            vhi_h_rect = vhi_min.handle().boundingRect()
            self._vh_rect.setLeft((vhi_h_rect.left() -
                                   styles.VH_XOFFSET +
                                   vhi_min.x()))
        if ztf:
            self.scene().views()[0].zoomToFit()
        self._updateBoundingRect()
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        """Summary

        Args:
            model_part (TYPE): Description
            is_selected (TYPE): Description

        Returns:
            TYPE: Description
        """
        print("partSelectedChangedSlot", is_selected)
        if is_selected:
            self.resetPen(styles.SELECTED_COLOR, styles.SELECTED_PEN_WIDTH)
            self.resetBrush(styles.SELECTED_BRUSH_COLOR, styles.SELECTED_ALPHA)
        else:
            self.resetPen(self.modelColor())
            self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        """Summary

        Args:
            model_part (TYPE): Description
            property_key (TYPE): Description
            new_value (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self._model_part == model_part:
            self._model_props[property_key] = new_value
            if property_key == 'color':
                self._updateBoundingRect()
                for vhi in self._virtual_helix_item_list:
                    vhi.handle().refreshColor()
                self.grab_corner.setBrush(getBrushObj(new_value))
    # end def

    def partVirtualHelicesTranslatedSlot(self, sender,
                                         vh_set, left_overs,
                                         do_deselect):
        """Summary

        Args:
            sender (TYPE): Description
            vh_set (TYPE): Description
            left_overs (TYPE): Description
            do_deselect (TYPE): Description

        Returns:
            TYPE: Description
        """
        # self.prexover_manager.clearPreXoverItems()
        # if self.active_virtual_helix_item is not None:
        #     self.active_virtual_helix_item.deactivate()
        #     self.active_virtual_helix_item = None

        # if self.active_virtual_helix_item is not None:
        #     self.setPreXoverItemsVisible(self.active_virtual_helix_item)
        pass
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot

        Args:
            sender (TYPE): Description
        """
        self.parentItem().removePartItem(self)
        scene = self.scene()
        scene.removeItem(self)
        self._model_part = None
        self._virtual_helix_item_hash = None
        self._virtual_helix_item_list = None
        self._controller.disconnectSignals()
        self._controller = None
        self.grab_corner = None
    # end def

    def partVirtualHelixAddedSlot(self, model_part, id_num):
        """
        When a virtual helix is added to the model, this slot handles
        the instantiation of a virtualhelix item.

        Args:
            model_part (TYPE): Description
            id_num (TYPE): Description
        """
        # print("NucleicAcidPartItem.partVirtualHelixAddedSlot")
        vhi = VirtualHelixItem(id_num, self, self._viewroot)
        self._virtual_helix_item_hash[id_num] = vhi
        vhi_list = self._virtual_helix_item_list
        # reposition when first VH is added
        if len(vhi_list) == 0:
            view = self.window().path_graphics_view
            p = view.scene_root_item.childrenBoundingRect().bottomLeft()
            _p = _BOUNDING_RECT_PADDING
            self.setPos(p.x() + _p*6 + styles.VIRTUALHELIXHANDLEITEM_RADIUS, p.y() + _p*3)
            # self.setPos(p.x() + _VH_XOFFSET, p.y() + _p*3)

        vhi_list.append(vhi)
        ztf = not getBatch()
        self._setVirtualHelixItemList(vhi_list, zoom_to_fit=ztf)
        self._updateBoundingRect()
    # end def

    def partVirtualHelixResizedSlot(self, sender, id_num):
        """Notifies the virtualhelix at coord to resize.

        Args:
            sender (TYPE): Description
            id_num (TYPE): Description
        """
        vhi = self._virtual_helix_item_hash[id_num]
        vhi.resize()
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, ordered_id_list, check_batch):
        """docstring for partVirtualHelicesReorderedSlot

        Args:
            sender (TYPE): Description
            ordered_id_list (TYPE): Description
            check_batch (TYPE): Description
        """
        vhi_dict = self._virtual_helix_item_hash
        new_list = [vhi_dict[id_num] for id_num in ordered_id_list]
        ztf = not getBatch() if check_batch == True else False
        self._setVirtualHelixItemList(new_list, zoom_to_fit=ztf)
    # end def

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        """Summary

        Args:
            sender (TYPE): Description
            id_num (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.removeVirtualHelixItem(id_num)
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, keys, values):
        """Summary

        Args:
            sender (TYPE): Description
            id_num (TYPE): Description
            keys (TYPE): Description
            values (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self._model_part == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            vh_i.virtualHelixPropertyChangedSlot(keys, values)
    # end def

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        """is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)

        Args:
            sender (TYPE): Description
            vh_set (TYPE): Description
            is_adding (TYPE): Description
        """
        vhhi_group = self._viewroot.vhiHandleSelectionGroup()
        vh_hash = self._virtual_helix_item_hash
        doc = self._viewroot.document()
        if is_adding:
            # print("got the adding slot in path")
            for id_num in vh_set:
                vhi = vh_hash[id_num]
                vhhi = vhi.handle()
                vhhi.modelSelect(doc)
            # end for
            vhhi_group.processPendingToAddList()
        else:
            # print("got the removing slot in path")
            for id_num in vh_set:
                vhi = vh_hash[id_num]
                vhhi = vhi.handle()
                vhhi.modelDeselect(doc)
            # end for
            vhhi_group.processPendingToAddList()
    # end def

    ### ACCESSORS ###
    def removeVirtualHelixItem(self, id_num):
        """Summary

        Args:
            id_num (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.setActiveVirtualHelixItem(None)
        vhi = self._virtual_helix_item_hash[id_num]
        vhi.virtualHelixRemovedSlot()
        self._virtual_helix_item_list.remove(vhi)
        del self._virtual_helix_item_hash[id_num]
        ztf = not getBatch()
        self._setVirtualHelixItemList(self._virtual_helix_item_list,
                                      zoom_to_fit=ztf)
        self._updateBoundingRect()
    # end def

    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.parentItem().window()
    # end def

    ### PRIVATE METHODS ###
    def _setVirtualHelixItemList(self, new_list, zoom_to_fit=True):
        """
        Give me a list of VirtualHelixItems and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.

        Args:
            new_list (TYPE): Description
            zoom_to_fit (bool, optional): Description
        """
        y = 0  # How far down from the top the next PH should be
        leftmost_extent = 0
        rightmost_extent = 0
        vhi_rect = None
        vhi_h_rect = None
        vhi_h_selection_group = self._viewroot.vhiHandleSelectionGroup()
        for vhi in new_list:
            _, _, _z = vhi.getAxisPoint(0)
            _z *= self._scale_2_Qt
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

            # vhi_h.setPos(-2 * vhi_h_rect.width(), y + (vhi_rect.height() - vhi_h_rect.height()) / 2)
            vhi_h_x = _z - _VH_XOFFSET
            vhi_h_y = y + (vhi_rect.height() - vhi_h_rect.height()) / 2
            vhi_h.setPos(vhi_h_x, vhi_h_y)

            # leftmost_extent = min(leftmost_extent, vhi_h_x)
            leftmost_extent = min(leftmost_extent, -1.5*vhi_h_rect.width())
            rightmost_extent = max(rightmost_extent, vhi_rect.width())
            y += step
            self.updateXoverItems(vhi)
            if do_reselect:
                vhi_h_selection_group.addToGroup(vhi_h)
        # end for
        self._vh_rect = QRectF(leftmost_extent, -10, -leftmost_extent + rightmost_extent, y)
        self._virtual_helix_item_list = new_list
        if zoom_to_fit:
            self.scene().views()[0].zoomToFit()
    # end def

    def resetPen(self, color, width=0):
        """Summary

        Args:
            color (TYPE): Description
            width (int, optional): Description

        Returns:
            TYPE: Description
        """
        pen = getPenObj(color, width)
        self.setPen(pen)
    # end def

    def resetBrush(self, color, alpha):
        """Summary

        Args:
            color (TYPE): Description
            alpha (TYPE): Description

        Returns:
            TYPE: Description
        """
        brush = getBrushObj(color, alpha=alpha)
        self.setBrush(brush)
    # end def

    def _updateBoundingRect(self):
        """
        Updates the bounding rect to the size of the childrenBoundingRect,
        and refreshes the addBases and removeBases buttons accordingly.
        
        Called by partVirtualHelixAddedSlot, partZDimensionsChangedSlot, or
        removeVirtualHelixItem.
        """
        self.setPen(getPenObj(self.modelColor(), 0))
        self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)

        # self.setRect(self.childrenBoundingRect())
        _p = _BOUNDING_RECT_PADDING
        temp_rect = self._vh_rect.adjusted(-_p/2, -_p, _p, -_p/2)
        self.grab_corner.setTopLeft(temp_rect.topLeft())
        self.setRect(temp_rect)
    # end def

    ### PUBLIC METHODS ###
    def setModifyState(self, bool):
        """Hides the modRect when modify state disabled.

        Args:
            bool (TYPE): Description
        """
        self._can_show_mod_rect = bool
        if bool is False:
            self._mod_rect.hide()

    def getOrderedVirtualHelixList(self):
        """Used for encoding.
        """
        ret = []
        for vhi in self._virtual_helix_item_list:
            ret.append(vhi.coord())
        return ret
    # end def

    def reorderHelices(self, first, last, index_delta):
        """
        Reorder helices by moving helices _pathHelixList[first:last]
        by a distance delta in the list. Notify each PathHelix and
        PathHelixHandle of its new location.

        Args:
            first (TYPE): Description
            last (TYPE): Description
            index_delta (TYPE): Description
        """
        vhi_list = self._virtual_helix_item_list
        helix_numbers = [vhi.idNum() for vhi in vhi_list]
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
        self.part().setImportedVHelixOrder([vhi.idNum() for vhi in new_list], check_batch=False)
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi):
        """Summary

        Args:
            new_active_vhi (TYPE): Description

        Returns:
            TYPE: Description
        """
        current_vhi = self.active_virtual_helix_item
        if new_active_vhi != current_vhi:
            if current_vhi is not None:
                current_vhi.deactivate()
            if new_active_vhi is not None:
                new_active_vhi.activate()
            self.active_virtual_helix_item = new_active_vhi
    # end def

    def setPreXoverItemsVisible(self, virtual_helix_item):
        """
        self._pre_xover_items list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers

        Args:
            virtual_helix_item (TYPE): Description
        """
        vhi = virtual_helix_item

        if vhi is None:
            return

        # print("path.setPreXoverItemsVisible", virtual_helix_item.idNum())
        part = self.part()
        info = part.active_base_info
        if info and virtual_helix_item is not None:
            id_num, is_fwd, idx, to_vh_id_num = info
            per_neighbor_hits, pairs = part.potentialCrossoverMap(id_num, idx)
            self.prexover_manager.activateVirtualHelix(virtual_helix_item, idx, per_neighbor_hits)
        else:
            self.prexover_manager.reset()
    # end def

    def updateXoverItems(self, virtual_helix_item):
        """Summary

        Args:
            virtual_helix_item (TYPE): Description

        Returns:
            TYPE: Description
        """
        for item in virtual_helix_item.childItems():
            if isinstance(item, XoverNode3):
                item.refreshXover()
    # end def

    def updateStatusBar(self, status_string):
        """Shows status_string in the MainWindow's status bar.

        Args:
            status_string (TYPE): Description
        """
        self.window().statusBar().showMessage(status_string)

    ### COORDINATE METHODS ###
    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)
        """
        vhs = self._virtual_helix_item_list
        return vhs[0].keyPanDeltaX() if vhs else 5
    # end def

    def keyPanDeltaY(self):
        """How far an an arrow key should move the scene (in scene space)
        for a single press
        """
        vhs = self._virtual_helix_item_list
        if not len(vhs) > 1:
            return 5
        dy = vhs[0].pos().y() - vhs[1].pos().y()
        dummyRect = QRectF(0, 0, 1, dy)
        return self.mapToScene(dummyRect).boundingRect().height()
    # end def

    ### TOOL METHODS ###
    def mousePressEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        self._viewroot.clearSelectionsIfActiveTool()
        return QGraphicsItem.mousePressEvent(self, event)

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event (TYPE): Description
        """
        active_tool = self._getActiveTool()
        tool_method_name = active_tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event.pos())
    # end def

    def pencilToolHoverMove(self, pt):
        """Pencil the strand is possible.

        Args:
            pt (TYPE): Description
        """
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromPartItem(self, pt)
    # end def
