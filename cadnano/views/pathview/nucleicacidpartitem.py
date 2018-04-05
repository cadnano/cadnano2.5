# -*- coding: utf-8 -*-
from __future__ import division
from typing import (
    Set,
    List,
    Tuple
)

from PyQt5.QtCore import (
    QPointF,
    QRectF
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent
)

from cadnano.objectinstance import ObjectInstance
from cadnano import getBatch, util
from cadnano.proxies.cnenum import HandleEnum
from cadnano.gui.palette import (
    getBrushObj,
    getPenObj,
    getNoPen,
    # newPenObj
)
from cadnano.controllers import NucleicAcidPartItemController
from cadnano.views.abstractitems import QAbstractPartItem
from cadnano.views.resizehandles import ResizeHandleGroup

from . import pathstyles as styles
from .pathextras import PathWorkplaneItem
from .prexovermanager import PreXoverManager
from .strand.xoveritem import XoverNode3
from .virtualhelixitem import PathVirtualHelixItem
from . import (
    PathRootItemT,
    AbstractPathToolT
)

from cadnano.cntypes import (
    RectT,
    Vec2T,
    NucleicAcidPartT,
    VirtualHelixT,
    ABInfoT,
    WindowT
)

_DEFAULT_WIDTH = styles.DEFAULT_PEN_WIDTH
_DEFAULT_ALPHA = styles.DEFAULT_ALPHA
_SELECTED_COLOR = styles.SELECTED_COLOR
_SELECTED_WIDTH = styles.SELECTED_PEN_WIDTH
_SELECTED_ALPHA = styles.SELECTED_ALPHA

_BASE_WIDTH = _BW = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_MOD_PEN = getPenObj(styles.BLUE_STROKE, 0)

_VH_XOFFSET = styles.VH_XOFFSET
_HANDLE_SIZE = 8


class ProxyParentItem(QGraphicsRectItem):
    """an invisible container that allows one to play with Z-ordering

    Attributes:
        findChild (TYPE): Description
    """
    findChild = util.findChild  # for debug


class PathRectItem(QGraphicsRectItem):
    """The rectangle corresponding to the outline of the workable area in the
    Path View.

    This class overrides :meth:`mousePressEvent` so that clicking anywhere in the
    rectangle will result in the active VHI being deselected.
    """

    def __init__(self, parent):
        super(PathRectItem, self).__init__(parent)
        self.parent = parent

    def destroyItem(self):
        self.parent = None
        self.scene().removeItem(self)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.parent.unsetActiveVirtualHelixItem()


class PathNucleicAcidPartItem(QAbstractPartItem):
    """
    Attributes:
        active_virtual_helix_item: Description
        resize_handle_group: Description
        prexover_manager: Description
    """
    findChild = util.findChild  # for debug
    _BOUNDING_RECT_PADDING = 20
    _GC_SIZE = 10

    def __init__(self,  part_instance: ObjectInstance,
                        viewroot: PathRootItemT):
        """parent should always be ``PathRootItem``

        Args:
            part_instance:  ``ObjectInstance`` of the ``Part``
            viewroot: ``PathRootItem`` and parent object
        """
        super(PathNucleicAcidPartItem, self).__init__(part_instance, viewroot)
        self.setAcceptHoverEvents(True)

        self._getActiveTool = viewroot.manager.activeToolGetter
        self.active_virtual_helix_item: PathVirtualHelixItem = None
        m_p = self._model_part
        self._controller = NucleicAcidPartItemController(self, m_p)
        self.prexover_manager: PreXoverManager = PreXoverManager(self)
        self._virtual_helix_item_list = []
        self._initModifierRect()
        self._proxy_parent = ProxyParentItem(self)
        self._proxy_parent.setFlag(QGraphicsItem.ItemHasNoContents)
        self._scale_2_model: float = m_p.baseWidth()/_BASE_WIDTH
        self._scale_2_Qt: float = _BASE_WIDTH / m_p.baseWidth()

        self._vh_rect: QRectF = QRectF()
        self.setPen(getNoPen())

        self.outline: PathRectItem = PathRectItem(self)
        outline = self.outline
        outline.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setZValue(styles.ZPART)
        self._proxy_parent.setZValue(styles.ZPART)
        outline.setZValue(styles.ZDESELECTOR)
        self.outline.setPen(getPenObj(m_p.getColor(), _DEFAULT_WIDTH))
        o_rect = self._configureOutline(outline)
        model_color = m_p.getColor()

        self.resize_handle_group: ResizeHandleGroup = ResizeHandleGroup(
                                                        o_rect, _HANDLE_SIZE,
                                                        model_color, True,
                                                        # HandleEnum.LEFT |
                                                        HandleEnum.RIGHT,
                                                        self)

        self.model_bounds_hint = m_b_h = QGraphicsRectItem(self)
        m_b_h.setBrush(getBrushObj(styles.BLUE_FILL, alpha=32))
        m_b_h.setPen(getNoPen())
        m_b_h.hide()

        self.hide()  # show on adding first vh
    # end def

    def proxy(self) -> ProxyParentItem:
        """
        Returns:
            :class:`ProxyParentItem`
        """
        return self._proxy_parent
    # end def

    def modelColor(self) -> str:
        """
        Returns:
            color hex string
        """
        return self._model_part.getProperty('color')
    # end def

    def convertToModelZ(self, z: float) -> float:
        """scale Z-axis coordinate to the model

        Args:
            z: in view distance units

        Returns:
            z in the model distance units
        """
        return z * self._scale_2_model
    # end def

    def convertToQtZ(self, z: float) -> float:
        """
        Args:
            z: in model distance units

        Returns:
            z in the view distance units
        """
        return z * self._scale_2_Qt
    # end def

    def _initModifierRect(self):
        """
        """
        self._can_show_mod_rect = False
        self._mod_rect = m_r = QGraphicsRectItem(_DEFAULT_RECT, self)
        m_r.setPen(_MOD_PEN)
        m_r.hide()
    # end def

    def vhItemForIdNum(self, id_num: int) -> PathVirtualHelixItem:
        """Returns the pathview ``PathVirtualHelixItem`` corresponding to ``id_num``

        Args:
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.
        """
        return self._virtual_helix_item_hash.get(id_num)

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part: NucleicAcidPartT, id_num: int):
        """
        Args:
            part: Description
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.
        """
        vhi = self._virtual_helix_item_hash.get(id_num, None)
        self.setActiveVirtualHelixItem(vhi)
        self.setPreXoverItemsVisible(vhi)
    # end def

    def partActiveBaseInfoSlot(self, part: NucleicAcidPartT, info: ABInfoT):
        """
        Args:
            part: Description
            info: Description
        """
        pxi_m = self.prexover_manager
        pxi_m.deactivateNeighbors()
        if info and info is not None:
            id_num, is_fwd, idx, to_vh_id_num = info
            pxi_m.activateNeighbors(id_num, is_fwd, idx)
    # end def

    def partZDimensionsChangedSlot(self,    part: NucleicAcidPartT,
                                            min_id_num: int,
                                            max_id_num: int,
                                            ztf: bool = False):
        """
        Args:
            part: The model part
            min_id_num: Description
            max_id_num: Description
            ztf: Default is False for zoom to fit
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

        TLx, TLy, BRx, BRy = self._getVHRectCorners()
        self.reconfigureRect((TLx, TLy), (BRx, BRy))
    # end def

    def partSelectedChangedSlot(self, part: NucleicAcidPartT, is_selected: bool):
        """
        Args:
            part: The model part
            is_selected: Descriptions
        """
        # print("partSelectedChangedSlot", is_selected)
        if is_selected:
            self.resetPen(styles.SELECTED_COLOR, styles.SELECTED_PEN_WIDTH)
            self.resetBrush(styles.SELECTED_BRUSH_COLOR, styles.SELECTED_ALPHA)
        else:
            self.resetPen(self.modelColor())
            self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)

    def partPropertyChangedSlot(self,   part: NucleicAcidPartT,
                                        property_key: str,
                                        new_value):
        """
        Args:
            part: The model part
            property_key (TYPE): Description
            new_value (TYPE): Description
        """
        if self._model_part == part:
            self._model_props[property_key] = new_value
            if property_key == 'color':
                for vhi in self._virtual_helix_item_list:
                    vhi.handle().refreshColor()
                TLx, TLy, BRx, BRy = self._getVHRectCorners()
                self.reconfigureRect((TLx, TLy), (BRx, BRy))
            elif property_key == 'is_visible':
                if new_value:
                    self.show()
                else:
                    self.hide()
            elif property_key == 'virtual_helix_order':
                vhi_dict = self._virtual_helix_item_hash
                new_list = [vhi_dict[id_num] for id_num in new_value]
                ztf = False
                self._setVirtualHelixItemList(new_list, zoom_to_fit=ztf)
    # end def

    def partVirtualHelicesTranslatedSlot(self, sender: NucleicAcidPartT,
                                         vh_set: Set[int], left_overs: Set[int],
                                         do_deselect: bool):
        """
        Args:
            sender: Model object that emitted the signal.
            vh_set: Description
            left_overs: Description
            do_deselect: Description
        """
        # self.prexover_manager.clearPreXoverItems()
        # if self.active_virtual_helix_item is not None:
        #     self.active_virtual_helix_item.deactivate()
        #     self.active_virtual_helix_item = None

        # if self.active_virtual_helix_item is not None:
        #     self.setPreXoverItemsVisible(self.active_virtual_helix_item)
        pass
    # end def

    def partRemovedSlot(self, sender: NucleicAcidPartT):
        """Slot wrapper for ``destroyItem()``

        Args:
            sender: Model object that emitted the signal.
        """
        return self.destroyItem()
    # end def

    def destroyItem(self):
        print("destroying PathNucleicAcidPartItem")
        for item in list(self._virtual_helix_item_hash.values()):
            item.destroyItem()

        self.prexover_manager.destroyItem()
        self.prexover_manager = None

        self.resize_handle_group.destroyItem()
        self.resize_handle_group = None

        self.outline.destroyItem()
        self.outline = None

        scene = self.scene()
        scene.removeItem(self.model_bounds_hint)
        self.model_bounds_hint = None

        scene.removeItem(self._proxy_parent)
        self._proxy_parent = None

        return super(PathNucleicAcidPartItem, self).destroyItem()
    # end def

    def partVirtualHelixAddedSlot(self, sender: NucleicAcidPartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT,
                                        neighbors: List[int]):
        """When a virtual helix is added to the model, this slot handles
        the instantiation of a virtualhelix item.

        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.
            virtual_helix:
            neighbors: Description
        """
        # print("NucleicAcidPartItem.partVirtualHelixAddedSlot")
        if self._viewroot.are_signals_on:
            vhi = PathVirtualHelixItem(id_num, self)
            self._virtual_helix_item_hash[id_num] = vhi
            vhi_list = self._virtual_helix_item_list
            vhi_list.append(vhi)
            ztf = not getBatch()
            self._setVirtualHelixItemList(vhi_list, zoom_to_fit=ztf)
            if not self.isVisible():
                self.show()
    # end def

    def partVirtualHelixResizedSlot(self,   sender: NucleicAcidPartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT):
        """Notifies the virtualhelix at coord to resize.

        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for
                description and related methods.
            virtual_helix: The model object
        """
        vhi = self._virtual_helix_item_hash[id_num]
        # print("resize:", id_num, virtual_helix.getSize())
        vhi.resize()
    # end def

    def partVirtualHelixRemovingSlot(self, sender: NucleicAcidPartT,
                                        id_num: int,
                                        virtual_helix: VirtualHelixT,
                                        neighbors: List[int]):
        """
        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.
            virtual_helix:
            neighbors: Description
        """
        self.removeVirtualHelixItem(id_num)
    # end def

    def partVirtualHelixRemovedSlot(self, sender: NucleicAcidPartT, id_num: int):
        """Step 2 of removing a VHI
        """
        ztf = not getBatch()
        self._setVirtualHelixItemList(self._virtual_helix_item_list, zoom_to_fit=ztf)
        if len(self._virtual_helix_item_list) == 0:
            self.hide()
        self.reconfigureRect((), ())
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender: NucleicAcidPartT,
                                                    id_num: int,
                                                    virtual_helix: VirtualHelixT,
                                                    keys: Tuple,
                                                    values: Tuple):
        """
        Args:
            sender (Part): Model object that emitted the signal.
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for
                description and related methods.
            keys: keys that changed
            values: new values for each key that changed
        """
        if self._model_part == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            vh_i.virtualHelixPropertyChangedSlot(keys, values)
    # end def

    def partVirtualHelicesSelectedSlot(self, sender: NucleicAcidPartT,
                                            vh_set: Set[int],
                                            is_adding: bool):
        """
        Args:
            sender: Model object that emitted the signal.
            vh_set: Description
            is_adding: ``True`` adding virtual helices to a selection
                    or removing ``False`
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
    def removeVirtualHelixItem(self, id_num: int):
        """
        Args:
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for
                description and related methods.
        """
        self.setActiveVirtualHelixItem(None)
        vhi = self._virtual_helix_item_hash[id_num]
        vhi.virtualHelixRemovedSlot()
        self._virtual_helix_item_list.remove(vhi)
        del self._virtual_helix_item_hash[id_num]
    # end def

    def window(self) -> WindowT:
        """
        Returns:
            :obj:`DocumentWindow`
        """
        return self.parentItem().window()
    # end def

    ### PRIVATE METHODS ###
    def _configureOutline(self, outline: QGraphicsRectItem) -> QRectF:
        """Adjusts `outline` size with default padding.

        Args:
            outline: Description

        Returns:
            o_rect: `outline` QRectF adjusted by _BOUNDING_RECT_PADDING
        """
        _p = self._BOUNDING_RECT_PADDING
        o_rect = self.rect().adjusted(-_p, -_p, _p, _p)
        outline.setRect(o_rect)
        return o_rect
    # end def

    def _getVHRectCorners(self) -> RectT:
        vhTL = self._vh_rect.topLeft()
        vhBR = self._vh_rect.bottomRight()
        # vhTLx, vhTLy = vhTL.x(), vhTL.y()
        # vhBRx, vhBRy = vhBR.x(), vhBR.y()
        return vhTL.x(), vhTL.y(), vhBR.x(), vhBR.y()
    # end def

    def _setVirtualHelixItemList(self,  new_list: List[PathVirtualHelixItem],
                                        zoom_to_fit: bool = True):
        """Give me a list of VirtualHelixItems and I'll parent them to myself if
        necessary, position them in a column, adopt their handles, and
        position them as well.

        Args:
            new_list: list of :class:`PathVirtualHelixItem`s
            zoom_to_fit: Default is ``True``
        """
        y = 0  # How far down from the top the next PH should be
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

            vhi_h_x = _z - _VH_XOFFSET
            vhi_h_y = y + (vhi_rect.height() - vhi_h_rect.height()) / 2
            vhi_h.setPos(vhi_h_x, vhi_h_y)

            y += step
            self.updateXoverItems(vhi)
            if do_reselect:
                vhi_h_selection_group.addToGroup(vhi_h)
        # end for
        # this need only adjust top and bottom edges of the bounding rectangle
        # self._vh_rect.setTop()
        self._vh_rect.setBottom(y)
        self._virtual_helix_item_list = new_list

        # now update Z dimension (X in Qt space in the Path view)
        part = self.part()
        self.partZDimensionsChangedSlot(part, *part.zBoundsIds(), ztf=zoom_to_fit)
    # end def

    def resetPen(self, color: str, width: int = 0):
        """
        Args:
            color: color string
            width: Default is 0
        """
        pen = getPenObj(color, width)
        self.outline.setPen(pen)
        # self.setPen(pen)
    # end def

    def resetBrush(self, color: str, alpha: int):
        """
        Args:
            color: color string
            alpha: transparency
        """
        brush = getBrushObj(color, alpha=alpha)
        self.setBrush(brush)
    # end def

    def reconfigureRect(self, top_left: Vec2T, bottom_right: Vec2T,
                                finish: bool = False,
                                padding: int = 80):
        """Updates the bounding rect to the size of the childrenBoundingRect.
        Refreshes the outline and grab_corner locations.

        Called by ``partZDimensionsChangedSlot`` and ``partPropertyChangedSlot``.
        """
        outline = self.outline

        hasTL = True if top_left else False
        hasBR = True if bottom_right else False

        if hasTL ^ hasBR:  # called via resizeHandle mouseMove?
            ptTL = QPointF(*top_left) if top_left else outline.rect().topLeft()
            ptBR = QPointF(*bottom_right) if bottom_right else outline.rect().bottomRight()
            o_rect = QRectF(ptTL, ptBR)
            pad_xoffset = self._BOUNDING_RECT_PADDING*2
            new_size = int((o_rect.width()-_VH_XOFFSET-pad_xoffset)/_BASE_WIDTH)
            substep = self._model_part.subStepSize()
            snap_size = new_size - new_size % substep
            snap_offset = -(new_size % substep)*_BASE_WIDTH
            self.resize_handle_group.updateText(HandleEnum.RIGHT, snap_size)
            if finish:
                self._model_part.setAllVirtualHelixSizes(snap_size)
                o_rect = o_rect.adjusted(0, 0, snap_offset, 0)
                # print("finish", vh_size, new_size, substep, snap_size)
            self.outline.setRect(o_rect)
        else:
            # 1. Temporarily remove children that shouldn't affect size
            outline.setParentItem(None)
            self.model_bounds_hint.setParentItem(None)
            self.resize_handle_group.setParentItemAll(None)
            self.prexover_manager.setParentItem(None)
            # 2. Get the tight bounding rect
            self.setRect(self.childrenBoundingRect())  # vh_items only
            # 3. Restore children like nothing happened
            outline.setParentItem(self)
            self.model_bounds_hint.setParentItem(self)
            self.resize_handle_group.setParentItemAll(self)
            self.prexover_manager.setParentItem(self)
            self._configureOutline(outline)

        self.resetPen(self.modelColor(), 0)  # cosmetic
        self.resetBrush(styles.DEFAULT_BRUSH_COLOR, styles.DEFAULT_ALPHA)
        self.resize_handle_group.alignHandles(outline.rect())
        return outline.rect()
    # end def

    ### PUBLIC METHODS ###
    def getModelMinBounds(self, handle_type=None) -> RectT:
        """Bounds in form of Qt scaled from model
        Absolute min should be 2*stepsize.
        Round up from indexOfRightmostNonemptyBase to nearest substep.

        Returns:
            of form::

                    (xTL, yTL, xBR, yBR)
        """
        _p = self._BOUNDING_RECT_PADDING
        default_idx = self._model_part.stepSize()*2
        nonempty_idx = self._model_part.indexOfRightmostNonemptyBase()
        right_bound_idx = max(default_idx, nonempty_idx)
        substep = self._model_part.subStepSize()
        snap_idx = (right_bound_idx/substep)*substep
        xTL = 0
        xBR = snap_idx*_BASE_WIDTH + _p
        min_rect = self.rect().adjusted(-_p, -_p, _p, _p)
        yTL = min_rect.top()
        yBR = min_rect.bottom()
        return xTL, yTL, xBR, yBR
    # end def

    def showModelMinBoundsHint(self, handle_type, show: bool = True):
        """Shows QGraphicsRectItem reflecting current model bounds.
        ResizeHandleGroup should toggle this when resizing.

        Args:
            handle_type:
            show: show ``True`` or hide ``False``
        """
        m_b_h = self.model_bounds_hint
        if show:
            xTL, yTL, xBR, yBR = self.getModelMinBounds()
            m_b_h.setRect(QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR)))
            m_b_h.show()
        else:
            m_b_h.hide()
    # end def

    def setModifyState(self, is_on: bool):
        """Hides the modRect when modify state disabled.

        Args:
            is_on: is in a modify state
        """
        self._can_show_mod_rect = is_on
        if is_on is False:
            self._mod_rect.hide()

    def getOrderedVirtualHelixList(self):
        """Used for encoding.
        """
        ret = []
        for vhi in self._virtual_helix_item_list:
            ret.append(vhi.coord())
        return ret
    # end def

    def reorderHelices(self, id_nums: List[int], index_delta: int):
        """Reorder helices by moving helices _pathHelixList[first:last]
        by a distance delta in the list. Notify each PathHelix and
        PathHelixHandle of its new location.

        Args:
            id_nums: Description
            index_delta: Description
        """
        vhi_list = self._virtual_helix_item_list
        helix_numbers = [vhi.idNum() for vhi in vhi_list]

        first_index = helix_numbers.index(id_nums[0])
        last_index = helix_numbers.index(id_nums[-1]) + 1

        for id_num in id_nums:
            helix_numbers.remove(id_num)

        if index_delta < 0:  # move group earlier in the list
            new_index = max(0, index_delta + first_index) - len(id_nums)
        else:  # move group later in list
            new_index = min(len(vhi_list), index_delta + last_index) - len(id_nums)
        new_list = helix_numbers[:new_index] + id_nums + helix_numbers[new_index:]
        # call the method to move the items and store the list
        self._model_part.setImportedVHelixOrder(new_list, check_batch=False)
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi: PathVirtualHelixItem):
        """
        Args:
            new_active_vhi: Description
        """
        current_vhi = self.active_virtual_helix_item
        if new_active_vhi != current_vhi:
            if current_vhi is not None:
                current_vhi.deactivate()
            if new_active_vhi is not None:
                new_active_vhi.activate()
            self.active_virtual_helix_item = new_active_vhi
    # end def

    def unsetActiveVirtualHelixItem(self):
        if self.active_virtual_helix_item is not None:
            self.active_virtual_helix_item.deactivate()
            self.active_virtual_helix_item = None
        self.prexover_manager.reset()

    def setPreXoverItemsVisible(self, virtual_helix_item):
        """
        self._pre_xover_items list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers

        Args:
            virtual_helix_item (cadnano.views.pathview.virtualhelixitem.VirtualHelixItem): Description
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

    def updateXoverItems(self, virtual_helix_item: PathVirtualHelixItem):
        """
        Args:
            virtual_helix_item: Description
        """
        for item in virtual_helix_item.childItems():
            if isinstance(item, XoverNode3):
                item.refreshXover()
    # end def

    def updateStatusBar(self, status_string: str):
        """Shows status_string in the MainWindow's status bar.

        Args:
            status_string: The text to be displayed.
        """
        self.window().statusBar().showMessage(status_string)

    ### COORDINATE METHODS ###
    def keyPanDeltaX(self) -> int:
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)
        """
        vhs = self._virtual_helix_item_list
        return vhs[0].keyPanDeltaX() if vhs else 5
    # end def

    def keyPanDeltaY(self) -> int:
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
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen coordinates of the event,
                and previous event.
        """
        self._viewroot.clearSelectionsIfActiveTool()
        self.unsetActiveVirtualHelixItem()

        return QGraphicsItem.mousePressEvent(self, event)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event: Description
        """
        active_tool = self._getActiveTool()
        tool_method_name = active_tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event.pos())
    # end def

    def createToolHoverMove(self, pt: QPointF):
        """Create the strand is possible.

        Args:
            pt: mouse cursor location of create tool hover.
        """
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromPartItem(self, pt)
    # end def
