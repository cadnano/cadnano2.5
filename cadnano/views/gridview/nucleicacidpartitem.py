# -*- coding: utf-8 -*-
from ast import literal_eval
from typing import (
    Tuple,
    List,
    Set
)

from PyQt5.QtCore import (
    QPointF,
    Qt,
    QRectF
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent
)

from cadnano.objectinstance import ObjectInstance
from cadnano.controllers import NucleicAcidPartItemController
from cadnano.gui.palette import getPenObj, getNoPen  # , getBrushObj
from cadnano.views.abstractitems import QAbstractPartItem
from cadnano.views.grabcorneritem import GrabCornerItem
from cadnano.cntypes import (
    RectT,
    Vec2T,
    NucleicAcidPartT,
    VirtualHelixT,
    ABInfoT
)

from .virtualhelixitem import GridVirtualHelixItem
from .prexovermanager import PreXoverManager
from .griditem import GridItem
from . import gridstyles as styles
from . import GridRootItemT, AbstractGridToolT

_DEFAULT_WIDTH:  int = styles.DEFAULT_PEN_WIDTH
_DEFAULT_ALPHA:  int = styles.DEFAULT_ALPHA
_SELECTED_COLOR: str = styles.SELECTED_COLOR
_SELECTED_WIDTH: int = styles.SELECTED_PEN_WIDTH
_SELECTED_ALPHA: int = styles.SELECTED_ALPHA


class GridNucleicAcidPartItem(QAbstractPartItem):
    """Parent should be either a GridRootItem, or an AssemblyItem.

    Invariant: keys in _empty_helix_hash = range(_nrows) x range(_ncols)
    where x is the cartesian product.

    Attributes:
        active_virtual_helix_item: Description
        grab_cornerBR: bottom right bounding box handle
        grab_cornerTL: top left bounding box handle
        griditem: Description
        outline: Description
        prexover_manager (TYPE): Description
        scale_factor: Description
    """
    _RADIUS = styles.GRID_HELIX_RADIUS
    _BOUNDING_RECT_PADDING = 80

    def __init__(self,  part_instance: ObjectInstance,
                        viewroot: GridRootItemT):
        """Summary

        Args:
            part_instance: ``ObjectInstance`` of the ``Part``
            viewroot: ``GridRootItem``
            parent: Default is ``None``
        """
        super(GridNucleicAcidPartItem, self).__init__(  part_instance,
                                                        viewroot)

        self._getActiveTool = viewroot.manager.activeToolGetter
        m_p = self._model_part
        self._controller = NucleicAcidPartItemController(self, m_p)
        self.scale_factor: float = self._RADIUS / m_p.radius()
        self.active_virtual_helix_item: GridVirtualHelixItem = None
        self.prexover_manager = PreXoverManager(self)
        self.hide()  # hide while until after attemptResize() to avoid flicker

        # set this to a token value
        self._rect: QRectF = QRectF(0., 0., 1000., 1000.)
        self.boundRectToModel()
        self.setPen(getNoPen())
        self.setRect(self._rect)

        self.setAcceptHoverEvents(True)

        # Cache of VHs that were active as of last call to activeGridChanged
        # If None, all grids will be redrawn and the cache will be filled.
        # Connect destructor. This is for removing a part from scenes.

        # initialize the NucleicAcidPartItem with an empty set of old coords
        self.setZValue(styles.ZPARTITEM)
        outline = QGraphicsRectItem(self)
        self.outline: QGraphicsRectItem = outline
        o_rect = self._configureOutline(outline)
        outline.setFlag(QGraphicsItem.ItemStacksBehindParent)
        outline.setZValue(styles.ZDESELECTOR)
        model_color = m_p.getColor()
        outline.setPen(getPenObj(model_color, _DEFAULT_WIDTH))

        GC_SIZE = 10
        self.grab_cornerTL: GrabCornerItem = GrabCornerItem(GC_SIZE,
                                                            model_color,
                                                            True,
                                                            self)
        self.grab_cornerTL.setTopLeft(o_rect.topLeft())
        self.grab_cornerBR: GrabCornerItem = GrabCornerItem(GC_SIZE,
                                                            model_color,
                                                            True,
                                                            self)
        self.grab_cornerBR.setBottomRight(o_rect.bottomRight())
        self.griditem: GridItem = GridItem(self, self._model_props['grid_type'])
        self.griditem.setZValue(1)
        self.grab_cornerTL.setZValue(2)
        self.grab_cornerBR.setZValue(2)

        # select upon creation
        for part in m_p.document().children():
            if part is m_p:
                part.setSelected(True)
            else:
                part.setSelected(False)
        self.show()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part: NucleicAcidPartT, id_num: int):
        """Slot

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
        """Summary

        Args:
            part: Description
            info: Description

            (id_num, is_fwd, idx, -1)
        """
        pxom = self.prexover_manager
        pxom.deactivateNeighbors()
        if info and info is not None:
            id_num, is_fwd, idx, _ = info
            pxom.activateNeighbors(id_num, is_fwd, idx)
    # end def

    def partPropertyChangedSlot(self, part: NucleicAcidPartT, key: str, new_value):
        """Slot

        Args:
            part: The model part
            key: Description
            new_value: Description
        """
        if self._model_part == part:
            self._model_props[key] = new_value
            if key == 'color':
                self.outline.setPen(getPenObj(new_value, _DEFAULT_WIDTH))
                for vhi in self._virtual_helix_item_hash.values():
                    vhi.updateAppearance()
                self.grab_cornerTL.setPen(getPenObj(new_value, 0))
                self.grab_cornerBR.setPen(getPenObj(new_value, 0))
            elif key == 'is_visible':
                if new_value:
                    self.show()
                else:
                    self.hide()
            elif key == 'grid_type':
                self.griditem.setGridType(new_value)
    # end def

    def partRemovedSlot(self, sender: NucleicAcidPartT):
        """Slot wrapper for ``destroyItem()``

        Args:
            sender: Model object that emitted the signal.
        """
        return self.destroyItem()
    # end def

    def destroyItem(self):
        '''Remove this object and references to it from the view
        '''
        print("destroying GridNucleicAcidPartItem")
        for id_num in list(self._virtual_helix_item_hash.keys()):
            self.removeVirtualHelixItem(id_num)
        self.prexover_manager.destroyItem()
        self.prexover_manager = None

        scene = self.scene()

        scene.removeItem(self.outline)
        self.outline = None

        self.grab_cornerTL.destroyItem()
        self.grab_cornerTL = None

        self.grab_cornerBR.destroyItem()
        self.grab_cornerBR = None

        self.griditem.destroyItem()
        self.griditem = None

        super(GridNucleicAcidPartItem, self).destroyItem()
    # end def

    def partVirtualHelicesTranslatedSlot(self, sender: NucleicAcidPartT,
                                                vh_set: Set[int],
                                                left_overs:  Set[int],
                                                do_deselect: bool):
        """left_overs are neighbors that need updating due to changes

        Args:
            sender: Model object that emitted the signal.
            vh_set: Description
            left_overs: Description
            do_deselect: Description
        """
        if do_deselect:
            tool = self._getActiveTool()
            if tool.methodPrefix() == "selectTool":
                if tool.isSelectionActive():
                    # tool.deselectItems()
                    tool.modelClearSelected()

        # 1. move everything that moved
        for id_num in vh_set:
            vhi = self._virtual_helix_item_hash[id_num]
            vhi.updatePosition()
        # 2. now redraw what makes sense to be redrawn
        for id_num in vh_set:
            vhi = self._virtual_helix_item_hash[id_num]
            self._refreshVirtualHelixItemGizmos(id_num, vhi)
        for id_num in left_overs:
            vhi = self._virtual_helix_item_hash[id_num]
            self._refreshVirtualHelixItemGizmos(id_num, vhi)

        # 0. clear PreXovers:
        # self.prexover_manager.hideGroups()
        # if self.active_virtual_helix_item is not None:
        #     self.active_virtual_helix_item.deactivate()
        #     self.active_virtual_helix_item = None
        avhi = self.active_virtual_helix_item
        self.setPreXoverItemsVisible(avhi)
        self.enlargeRectToFit()
    # end def

    def _refreshVirtualHelixItemGizmos(self, id_num: int, vhi: GridVirtualHelixItem):
        """Update props and appearance of self & recent neighbors. Ultimately
        triggered by a partVirtualHelicesTranslatedSignal.

        Args:
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            vhi: the item associated with id_num
        """
        neighbors = vhi.getProperty('neighbors')
        neighbors = literal_eval(neighbors)
        vhi.beginAddWedgeGizmos()
        for nvh in neighbors:
            nvhi = self._virtual_helix_item_hash.get(nvh, False)
            if nvhi:
                vhi.setWedgeGizmo(nvh, nvhi)
        # end for
        vhi.endAddWedgeGizmos()
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender: NucleicAcidPartT,
                                                    id_num: int,
                                                    virtual_helix: VirtualHelixT,
                                                    keys: Tuple,
                                                    values: Tuple):
        """Args:
            sender (Part): Model object that emitted the signal.
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            keys: keys that changed
            values: new values for each key that changed
        """
        if self._model_part == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            vh_i.virtualHelixPropertyChangedSlot(keys, values)
    # end def

    def partVirtualHelixAddedSlot(self, sender: NucleicAcidPartT,
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
        if self._viewroot.are_signals_on:
            vhi = GridVirtualHelixItem(id_num, self)
            self._virtual_helix_item_hash[id_num] = vhi
            self._refreshVirtualHelixItemGizmos(id_num, vhi)
            for neighbor_id in neighbors:
                nvhi = self._virtual_helix_item_hash.get(neighbor_id, False)
                if nvhi:
                    self._refreshVirtualHelixItemGizmos(neighbor_id, nvhi)
            self.enlargeRectToFit()
    # end def

    def partVirtualHelixRemovingSlot(self,  sender: NucleicAcidPartT,
                                            id_num: int,
                                            virtual_helix: VirtualHelixT,
                                            neighbors: List[int]):
        """Slot

        Args:
            sender: Model object that emitted the signal.
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.
            virtual_helix:
            neighbors: Description
        """
        tm = self._viewroot.manager
        tm.resetTools()
        self.removeVirtualHelixItem(id_num)
        for neighbor_id in neighbors:
            nvhi = self._virtual_helix_item_hash[neighbor_id]
            self._refreshVirtualHelixItemGizmos(neighbor_id, nvhi)
    # end def

    def partSelectedChangedSlot(self,   model_part: NucleicAcidPartT,
                                        is_selected: bool):
        """Set this Z to front, and return other Zs to default.

        Args:
            model_part: The model part
            is_selected: Description
        """
        if is_selected:
            # self._drag_handle.resetAppearance(_SELECTED_COLOR, _SELECTED_WIDTH, _SELECTED_ALPHA)
            self.setZValue(styles.ZPARTITEM + 1)
        else:
            # self._drag_handle.resetAppearance(self.modelColor(), _DEFAULT_WIDTH, _DEFAULT_ALPHA)
            self.setZValue(styles.ZPARTITEM)
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
        select_tool = self._viewroot.select_tool
        if is_adding:
            # print("got the adding slot in path")
            select_tool.selection_set.update(vh_set)
            select_tool.setPartItem(self)
            select_tool.getSelectionBoundingRect()
        else:
            select_tool.deselectSet(vh_set)
    # end def

    def partDocumentSettingChangedSlot(self, part: NucleicAcidPartT,
                                            key: str,
                                            value):
        """Summary

        Args:
            part: Description
            key: Description
            value: Description

        Raises:
            ValueError: unknown grid styling string in ``key``
        """
        if key == 'grid':
            print("grid change", value)
            if value == 'lines and points':
                self.griditem.setGridAppearance(True)
            elif value == 'points':
                self.griditem.setGridAppearance(False)
            elif value == 'circles':
                pass  # self.griditem.setGridAppearance(False)
            else:
                raise ValueError("unknown grid styling")
    # end def

    ### ACCESSORS ###
    def boundingRect(self) -> QRectF:
        """
        """
        return self._rect
    # end def

    def modelColor(self):
        """
        """
        return self._model_props['color']
    # end def

    def window(self):
        """
        Returns:
            CNMainWindow
        """
        return self.parentItem().window()
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi: GridVirtualHelixItem):
        """Summary

        Args:
            new_active_vhi: Description
        """
        current_vhi = self.active_virtual_helix_item
        # print(current_vhi, new_active_vhi)
        if new_active_vhi != current_vhi:
            if current_vhi is not None:
                current_vhi.deactivate()
            if new_active_vhi is not None:
                new_active_vhi.activate()
            self.active_virtual_helix_item = new_active_vhi
    # end def

    def setPreXoverItemsVisible(self, virtual_helix_item: GridVirtualHelixItem):
        """``self._pre_xover_items`` list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers

        Args:
            virtual_helix_item: Description
        """
        vhi = virtual_helix_item
        pxom = self.prexover_manager
        if vhi is None:
            pxom.hideGroups()
            return

        # print("grid.setPreXoverItemsVisible", virtual_helix_item.idNum())
        part = self.part()
        info = part.active_base_info
        if info:
            id_num, is_fwd, idx, to_vh_id_num = info
            per_neighbor_hits, pairs = part.potentialCrossoverMap(id_num, idx)
            pxom.activateVirtualHelix(virtual_helix_item, idx,
                                      per_neighbor_hits, pairs)
    # end def

    def removeVirtualHelixItem(self, id_num: int):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
        """
        vhi = self._virtual_helix_item_hash[id_num]
        if vhi == self.active_virtual_helix_item:
            self.active_virtual_helix_item = None
        vhi.virtualHelixRemovedSlot()
        del self._virtual_helix_item_hash[id_num]
    # end def

    def reconfigureRect(self,   top_left: Vec2T,
                                bottom_right: Vec2T,
                                padding: int = 80
                                ) -> Tuple[Vec2T, Vec2T]:
        """Summary

        Args:
            top_left: top left corner point
            bottom_right: bottom right corner point
            padding: padding of the rectagle in pixels points

        Returns:
            tuple of point tuples representing the ``top_left`` and
                ``bottom_right`` as reconfigured with ``padding``
        """
        rect = self._rect
        ptTL = QPointF(*self._padTL(padding, *top_left)) if top_left else rect.topLeft()
        ptBR = QPointF(*self._padBR(padding, *bottom_right)) if bottom_right else rect.bottomRight()
        self._rect = new_rect = QRectF(ptTL, ptBR)
        self.setRect(new_rect)
        self._configureOutline(self.outline)
        self.griditem.updateGrid()
        return (ptTL.x(), ptTL.y()), (ptBR.x(), ptBR.y())
    # end def

    def _padTL(self, padding: float, xTL: float, yTL: float) -> Vec2T:
        return xTL + padding, yTL + padding
    # end def

    def _padBR(self, padding: float, xBR: float, yBR: float) -> Vec2T:
        return xBR - padding, yBR - padding
    # end def

    def enlargeRectToFit(self):
        """Enlarges Part Rectangle to fit the model bounds.  Call this
        when adding a GridVirtualHelixItem.
        """
        p = self._BOUNDING_RECT_PADDING
        xTL, yTL, xBR, yBR = self.getModelMinBounds()
        xTL = xTL - p
        yTL = yTL - p
        xBR = xBR + p
        yBR = yBR + p
        tl, br = self.reconfigureRect((xTL, yTL), (xBR, yBR))
        self.grab_cornerTL.alignPos(*tl)
        self.grab_cornerBR.alignPos(*br)
    # end def

    ### PRIVATE SUPPORT METHODS ###
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

    def boundRectToModel(self):
        """update the boundaries to what's in the model with a minimum
        size
        """
        xTL, yTL, xBR, yBR = self.getModelMinBounds()
        self._rect = QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR))
    # end def

    def getModelMinBounds(self, handle_type=None) -> RectT:
        """Bounds in form of Qt scaled from model

        Returns:
            top_left + bottom_right tuple concatenated.
        """
        xLL, yLL, xUR, yUR = self.part().boundDimensions(self.scale_factor)
        return xLL, -yUR, xUR, -yLL
    # end def

    def bounds(self) -> RectT:
        """x_low, x_high, y_low, y_high
        """
        rect = self._rect
        return rect.left(), rect.right(), rect.bottom(), rect.top()

    ### PUBLIC SUPPORT METHODS ###
    def setModifyState(self, bool_val: bool):
        """Hides the mod_rect when modify state disabled.

        Args:
            bool_val (TYPE): what the modifystate should be set to.
        """
        # self._can_show_mod_circ = bool_val
        # if not bool_val:
        #     self._mod_circ.hide()
        pass
    # end def

    def updateStatusBar(self, status_str: str):
        """Shows status_str in the MainWindow's status bar.
        Not implemented

        Args:
            status_str: Description
        """
        # self.window().statusBar().showMessage(status_str, timeout)
    # end def

    def zoomToFit(self):
        """Ask the view to zoom to fit this object
        """
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen
            coordinates of the the event, and previous event.
        """
        if event.button() == Qt.RightButton:
            return
        part = self._model_part
        part.setSelected(True)
        if self.isMovable():
            return QGraphicsItem.mousePressEvent(self, event)
        tool = self._getActiveTool()
        if tool.FILTER_NAME not in part.document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, event)
        else:
            event.setAccepted(False)
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Summary

        Args:
            event: Description
        """

        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, event)
        else:
            event.setAccepted(False)
            QGraphicsItem.hoverMoveEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        tool = self._getActiveTool()
        tool.hideLineItem()

    def getModelPos(self, pos: QPointF) -> Vec2T:
        """Y-axis is inverted in Qt +y === DOWN

        Args:
            pos: a position in this scene

        Returns:
            position in model coordinates
        """
        sf = self.scale_factor
        x, y = pos.x()/sf, -1.0*pos.y()/sf
        return x, y
    # end def

    def getVirtualHelixItem(self, id_num: int) -> GridVirtualHelixItem:
        """Summary

        Args:
            id_num: VirtualHelix ID number. See ``NucleicAcidPart`` for
                description and related methods.

        Returns:
            GridVirtualHelixItem
        """
        return self._virtual_helix_item_hash.get(id_num)
    # end def

    def createToolMousePress(self, tool: AbstractGridToolT,
                                event: QGraphicsSceneMouseEvent,
                                alt_event=None):
        """Summary

        Args:
            tool: Description
            event: Description
            alt_event (None, optional): Description
        """
        # 1. get point in model coordinates:
        part = self._model_part
        if alt_event is None:
            pt = tool.eventToPosition(self, event)
        else:
            pt = alt_event.pos()

        if pt is None:
            tool.deactivate()
            return QGraphicsItem.mousePressEvent(self, event)

        part_pt_tuple = self.getModelPos(pt)

        mod = Qt.MetaModifier
        if not (event.modifiers() & mod):
            pass

        # don't create a new VirtualHelix if the click overlaps with existing
        # VirtualHelix
        current_id_num = tool.idNum()
        check = part.isVirtualHelixNearPoint(part_pt_tuple, current_id_num)
        # print("current_id_num", current_id_num, check)
        # print(part_pt_tuple)
        tool.setPartItem(self)
        if check:
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            # print("got a check", id_num)
            if id_num >= 0:
                # print("restart", id_num)
                vhi = self._virtual_helix_item_hash[id_num]
                tool.setVirtualHelixItem(vhi)
                tool.startCreation()
        else:
            # print("creating", part_pt_tuple)
            part.createVirtualHelix(*part_pt_tuple)
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            vhi = self._virtual_helix_item_hash[id_num]
            tool.setVirtualHelixItem(vhi)
            tool.startCreation()
    # end def

    def createToolHoverMove(self, tool: AbstractGridToolT,
                                event: QGraphicsSceneHoverEvent):
        """Summary

        Args:
            tool: Description
            event: Description
        """
        tool.hoverMoveEvent(self, event)
        return QGraphicsItem.hoverMoveEvent(self, event)
    # end def

    def selectToolMousePress(self,  tool: AbstractGridToolT,
                                    event: QGraphicsSceneMouseEvent):
        """
        Args:
            tool: Description
            event: Description
        """
        tool.setPartItem(self)
        pt = tool.eventToPosition(self, event)
        part_pt_tuple = self.getModelPos(pt)
        part = self._model_part
        if part.isVirtualHelixNearPoint(part_pt_tuple):
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            if id_num >= 0:
                print(id_num)
                loc = part.getCoordinate(id_num, 0)
                print("VirtualHelix #{} at ({:.3f}, {:.3f})".format(id_num, loc[0], loc[1]))
            else:
                # tool.deselectItems()
                tool.modelClearSelected()
        else:
            # tool.deselectItems()
            tool.modelClearSelected()
        return QGraphicsItem.mousePressEvent(self, event)
    # end def
# end class
