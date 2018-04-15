# -*- coding: utf-8 -*-
"""Summary
"""
from typing import (
    Tuple,
    Union,
    Set
)

from PyQt5.QtCore import (
    QPointF,
    QPoint,
    QRect,
    Qt
)
from PyQt5.QtWidgets import (
    QGraphicsItemGroup,
    QGraphicsRectItem,
    QGraphicsItem,
    QMenu,
    QAction,
    QGraphicsSceneMouseEvent
)
from PyQt5.QtGui import (
    QCursor,
    QKeyEvent
)

from cadnano.views.gridview.virtualhelixitem import GridVirtualHelixItem
from cadnano.gui.palette import getPenObj
from cadnano.fileio import (
    v3encode,
    v3decode
)
from cadnano.views.gridview import gridstyles as styles
from .abstractgridtool import AbstractGridTool
from cadnano.views.gridview.griditem import GridEvent
from cadnano.views.gridview import (
    GridToolManagerT,
    GridNucleicAcidPartItemT
)
from cadnano.cntypes import (
    RectT
)

def normalizeRect(rect: RectT) -> RectT:
    """
    Args:
        rect: rectangle tuple

    Returns:
        Tuple of form::

            (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = rect
    if x1 > x2:
        # swap
        x1, x2 = x2, x1
    if y1 > y2:
        # swap
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


_SELECT_PEN_WIDTH = 2
_SELECT_COLOR = "#ff0000"
_TEST_COLOR = "#00ff00"


class SelectGridTool(AbstractGridTool):
    """Handles Select Tool operations in the Grid view

    Attributes:
        clip_board (dict): Description
        group (GridSelectionGroup): Description
        individual_pick (bool): Description
        is_selection_active (bool): Description
        last_rubberband_vals (tuple): Description
        part_item (GridNucleicAcidPartItemT): Description
        selection_set (TYPE): Description
        snap_origin_item (TYPE): Description
    """

    def __init__(self, manager: GridToolManagerT):
        """
        Args:
            manager: the grid view tool manager
        """
        super(SelectGridTool, self).__init__(manager)
        self.last_rubberband_vals = (None, None, None)
        self.selection_set = set()
        self.part_item = None
        self.group = GridSelectionGroup(self, parent=None)
        self.group.hide()
        self.is_selection_active = False
        self.individual_pick = False
        self.snap_origin_item = None
        self.clip_board = None
    # end def

    def __repr__(self) -> str:
        """
        Returns:
            tool name string
        """
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self) -> str:
        """
        Returns:
            prefix string
        """
        return "selectTool"  # first letter should be lowercase

    def isSelectionActive(self) -> bool:
        """
        Returns:
            is the selection active?
        """
        return self.is_selection_active
    # end def

    def resetSelections(self):
        """Clear all model selections
        This is redundant with modelClearSelected()
        """
        # print("resetSelections")
        doc = self.manager.document
        doc.clearAllSelected()

    def modelClearSelected(self):
        """Clear all model selections
        """
        # print("modelClearSelected")
        doc = self.manager.document
        doc.clearAllSelected()
        self.deselectSet(self.selection_set)
        self.is_started = False
        self._vhi = None
        self.hideLineItem()
    # end def

    def setPartItem(self, part_item: GridNucleicAcidPartItemT):
        """
        Args:
            part_item: Description
        """
        self.group.resetTransform()
        if part_item is not self.part_item:
            if self.slice_graphics_view is not None:
                # attempt to enforce good housekeeping, not required
                try:
                    self.slice_graphics_view.rubberBandChanged.disconnect(self.selectRubberband)
                except TypeError:
                    pass
            if self.part_item is not None:
                self.modelClearSelected()
            self.part_item = part_item

            # In the event that the old part_item was deleted (and garbage
            # collected), self.group (whose parent was the old part_item) is
            # also garbage collected.  Therefore, create a new
            # GridSelectionGroup when this is the case
            try:
                self.group.setParentItem(part_item)
            except RuntimeError:
                self.group = GridSelectionGroup(self, parent=part_item)

            # required for whatever reason to re-enable QGraphicsView.RubberBandDrag
            self.slice_graphics_view.activateSelection(True)

            self.slice_graphics_view.rubberBandChanged.connect(self.selectRubberband)
    # end def

    def selectRubberband(self, rect: QRect, from_pt: QPointF, to_point: QPointF):
        """
        Args:
            rect: Description
            from_pt: Description
            to_point: Description
        """
        fset = self.manager.document.filter_set
        if self.FILTER_NAME not in fset:
            return
        rbr_last, fp_last, tp_last = self.last_rubberband_vals
        if rect.isNull() and rbr_last.isValid():
            part_item = self.part_item
            part = part_item.part()

            # convert and normalize the drag rectangle
            from_pt_part_item = part_item.mapFromScene(fp_last)
            to_pt_part_item = part_item.mapFromScene(tp_last)

            # note QRectF.normalized doesn't seem to actually normalize a
            # rectangle near as I can tell no we have normaliz
            from_model_point = part_item.getModelPos(from_pt_part_item)
            to_model_point = part_item.getModelPos(to_pt_part_item)
            query_rect = (from_model_point[0], from_model_point[1],
                          to_model_point[0], to_model_point[1])
            query_rect = normalizeRect(query_rect)
            # print("Query rect", query_rect,
            #     query_rect[0] < query_rect[2], query_rect[1] < query_rect[3])
            res = part.getVirtualHelicesInArea(query_rect)

            doc = self.manager.document
            doc.clearAllSelected()
            doc.addVirtualHelicesToSelection(part, res)
        else:
            self.last_rubberband_vals = (rect, from_pt, to_point)
    # end def

    def getSelectionBoundingRect(self):
        """Show the bounding rect
        """
        part_item = self.part_item
        group = self.group
        # self.deselectItems()
        for id_num in self.selection_set:
            vhi = part_item.getVirtualHelixItem(id_num)
            group.addToGroup(vhi)

        self.is_selection_active = True
        if len(group.childItems()) > 0:
            group.setSelectionRect()
            # print("showing")
            group.show()
        else:
            print("Nothing in selection_set")
    # end def

    def deselectItems(self):
        """
        Returns:
            ``True`` if selection cleared ``False`` if no selection active
        """
        # print("deselecting")
        group = self.group
        if self.snap_origin_item is not None:
            self.snap_origin_item.setSnapOrigin(False)
            self.snap_origin_item = None
        if self.is_selection_active:
            part_item = self.part_item
            for id_num in self.selection_set:
                vhi = part_item.getVirtualHelixItem(id_num)
                if vhi is not None:
                    group.removeFromGroup(vhi)
            self.selection_set.clear()
            group.clearSelectionRect()
            group.hide()
            self.is_selection_active = False
            return True
        group.clearSelectionRect()
        return False
    # end def

    def deselectSet(self, vh_set: Set[int]) -> bool:
        """
        Args:
            vh_set: Description

        Returns:
            ``False`` if selection is not active, ``True`` if active
        """
        group = self.group
        if self.snap_origin_item is not None:
            self.snap_origin_item.setSnapOrigin(False)
            self.snap_origin_item = None
        selection_set = self.selection_set
        if self.is_selection_active:
            part_item = self.part_item
            for id_num in vh_set:
                vhi = part_item.getVirtualHelixItem(id_num)
                if vhi is not None:
                    group.removeFromGroup(vhi)
                    selection_set.remove(id_num)
            group.clearSelectionRect()
            group.hide()
            if len(selection_set) > 0 and len(group.childItems()) > 0:
                group.setSelectionRect()
                group.show()
            return True
        group.clearSelectionRect()
        return False
    # end def

    def selectOrSnap(self,  part_item: GridNucleicAcidPartItemT,
                            target_item: Union[GridVirtualHelixItem, GridEvent],
                            event: QGraphicsSceneMouseEvent):
        """
        Args:
            part_item: the part item
            target_item: Item to snap
            event: mosue event
        """
        self.setPartItem(part_item)
        if (self.snap_origin_item is not None and event.modifiers() == Qt.AltModifier):
            self.doSnap(part_item, target_item)
            self.individual_pick = False
        else:  # just do a selection
            if event.modifiers() != Qt.ShiftModifier:
                self.modelClearSelected()   # deselect if shift isn't held

            if isinstance(target_item, GridVirtualHelixItem):
                # NOTE: individual_pick seems not needed.
                # it's supposed to allow for single item picking
                # self.individual_pick = True

                if self.snap_origin_item is not None:
                    self.snap_origin_item.setSnapOrigin(False)
                    self.snap_origin_item = None

                doc = self.manager.document
                part = part_item.part()
                doc.addVirtualHelicesToSelection(part, [target_item.idNum()])
    # end def

    def doSnap(self, part_item: GridNucleicAcidPartItemT,
                    snap_to_item: Union[GridVirtualHelixItem, GridEvent]):
        """
        Args:
            part_item: the part item
            snap_to_item: Item to snap
                selection to
        """
        # print("snapping")
        origin = self.snap_origin_item.getCenterScenePos()

        # xy = part_item.mapFromScene(snap_to_item.scenePos())
        # xy2 = part_item.mapFromScene(self.snap_origin_item.scenePos())
        # print("snapping from:", xy2.x(), xy2.y())
        # print("snapped to:", xy.x(), xy.y())

        if isinstance(snap_to_item, GridVirtualHelixItem):
            self.setVirtualHelixItem(snap_to_item)
            destination = self.findNearestPoint(part_item, origin)
        else:  # GridEvent
            destination = snap_to_item.pos()
            # print("GridEvent", destination)

        origin = part_item.mapFromScene(origin)
        if destination is None:
            destination = origin
        if origin == destination:
            # snap clockwise
            destination = self.findNextPoint(part_item, origin)
        if origin is None or destination is None:
            # print("o", origin, "d", destination)
            pass
        delta = destination - origin
        dx, dy = delta.x(), delta.y()
        group = self.group
        pos = group.pos() + delta
        self.group.setPos(pos)
        self.moveSelection(dx, dy, False, use_undostack=True)
        self.hideLineItem()
    # end def

    def deleteSelection(self):
        """Delete Selection Group
        """
        part_item = self.part_item
        part = part_item.part()
        delete_set = self.selection_set.copy()
        self.modelClearSelected()
        part.removeVirtualHelices(delete_set)
        self.clip_board = None
    # end def

    def copySelection(self):
        """Copy Selection Group to a Clip board
        """
        part_item = self.part_item
        part_instance = part_item.partInstance()

        # SAVE the CORNER POINT of the selection box
        bri = self.group.bounding_rect_item
        br = bri.rect()
        delta = QPointF(br.width() / 2 , br.height()/2)
        self.copy_pt = bri.pos() + delta
        # print("NEW Grid copy point", self.copy_pt)

        copy_dict = v3encode.encodePartList(part_instance, list(self.selection_set))
        self.clip_board = copy_dict
        self.vhi_hint_item.hide()
    # end def

    def pasteClipboard(self):
        """
        """
        if self.clip_board is None:
            return
        doc = self.manager.document
        part_item = self.part_item
        part = part_item.part()
        sgv = self.slice_graphics_view

        #  1. get mouse point at the paste
        qc = QCursor()
        global_pos = qc.pos()
        view_pt = sgv.mapFromGlobal(global_pos)
        s_pt = sgv.mapToScene(view_pt)

        to_pt = part_item.mapFromScene(s_pt)
        # print("To Grid Point", to_pt.x(), to_pt.y())

        # self.vhi_hint_item.setParentItem(part_item)
        # self.setHintPos(to_pt)
        # self.vhi_hint_item.show()

        # 2. Calculate a delta from the CORNER of the selection box
        sf = part_item.scaleFactor()
        delta = to_pt - self.copy_pt
        distance_offset  = delta.x()/sf, -delta.y()/sf

        part_instance = self.part_item.partInstance()
        new_vh_set = v3decode.importToPart( part_instance,
                                            self.clip_board,
                                            offset=distance_offset)
        self.modelClearSelected()
        # doc.addVirtualHelicesToSelection(part, new_vh_set)
    # end def

    def moveSelection(self, dx: float, dy: float,
                        finalize: bool,
                        use_undostack: bool =True):
        """Y-axis is inverted in Qt +y === DOWN

        Args:
            dx (TYPE): Description
            dy (TYPE): Description
            finalize (TYPE): Description
            use_undostack (bool, optional): Description
        """
        # print("moveSelection: {}, {}".format(dx, dy))
        part_item = self.part_item
        sf = part_item.scaleFactor()
        part = part_item.part()
        part.translateVirtualHelices(self.selection_set,
                                     dx / sf, -dy / sf, 0,
                                     finalize,
                                     use_undostack=use_undostack)
    # end def

    def deactivate(self):
        """
        """
        if self.slice_graphics_view is not None:
            try:
                self.slice_graphics_view.rubberBandChanged.disconnect(self.selectRubberband)
            except (AttributeError, TypeError):
                pass    # required for first call
        self.modelClearSelected()
        if self.snap_origin_item is not None:
            self.snap_origin_item.setSnapOrigin(False)
            self.snap_origin_item = None
        AbstractGridTool.deactivate(self)
    # end def

    def getCustomContextMenu(self, point: QPoint):
        """
        Args:
            point: the point to place the context menu
        """
        sgv = self.slice_graphics_view
        do_show = False
        menu = None
        if len(self.selection_set) > 0:
            menu = QMenu(sgv)
            copy_act = QAction("copy selection", sgv)
            copy_act.setStatusTip("copy selection")
            copy_act.triggered.connect(self.copySelection)
            menu.addAction(copy_act)
            delete_act = QAction("delete selection", sgv)
            delete_act.setStatusTip("delete selection")
            delete_act.triggered.connect(self.deleteSelection)
            menu.addAction(delete_act)
            do_show = True
        if self.clip_board is not None:
            if menu is None:
                menu = QMenu(sgv)
            copy_act = QAction("paste", sgv)
            copy_act.setStatusTip("paste from clip board")
            copy_act.triggered.connect(self.pasteClipboard)
            menu.addAction(copy_act)
            do_show = True
        if do_show:
            # def menuClickSet(event):
            #     self.menu_pos = event.globalPos()
            #     return QMenu.mousePressEvent(menu, event)
            # menu.mousePressEvent = menuClickSet
            menu.exec_(sgv.mapToGlobal(point))
    # end def
# end class


class GridSelectionGroup(QGraphicsItemGroup):
    """
    Attributes:
        bounding_rect_item (QGraphicsRectItem):  bounding rectangle
        drag_last_position (QPointF): last drag position
        drag_start_position (QPointF): start position of a drag
        tool (SelectGridTool): the selection tool
    """

    def __init__(self,  tool: SelectGridTool,
                        parent: GridNucleicAcidPartItemT = None):
        """
        Args:
            tool: the selection tool
            parent: default is ``None``. a :class:`GridNucleicAcidPartItem`
        """
        super(GridSelectionGroup, self).__init__(parent)
        self.tool = tool
        self.setFiltersChildEvents(True)
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # for keyPressEvents
        self.setFlag(QGraphicsItem.ItemIsMovable)

        self.bounding_rect_item = bri = QGraphicsRectItem(tool)
        bri.hide()
        bri.setPen(getPenObj(_SELECT_COLOR, _SELECT_PEN_WIDTH))

        self.setZValue(styles.ZSELECTION)

        self.drag_start_position = QPointF()
        self.drag_last_position = QPointF()
    # end def

    def setSelectionRect(self):
        """Set the selection rectangle
        """
        bri = self.bounding_rect_item
        rect = self.childrenBoundingRect()
        point = rect.topLeft() + self.scenePos()
        bri.setPos(bri.mapFromScene(point))
        bri.setRect(bri.mapRectFromItem(self, rect))
        self.addToGroup(bri)
        bri.show()
        self.setFocus(True)
    # end def

    """ reimplement boundingRect if you want to call resetGroupPos
    """

    def clearSelectionRect(self):
        """reset positions to zero to keep things in check
        """
        bri = self.bounding_rect_item
        bri.hide()
        self.removeFromGroup(bri)

        # Need to reparent move back to 0,0
        bri.setParentItem(self.tool)
        temp_pt = QPointF(0, 0)
        bri.setPos(temp_pt)

        self.setFocus(False)
    # end def

    def keyPressEvent(self, event: QKeyEvent):
        """event.key() seems to be capital only?

        Args:
            event: the key event
        """
        # print("press", ord('g'))
        if event.text() == 'g':
            print("hey het")
        return QGraphicsItem.keyPressEvent(self, event)
    # end def

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen coordinates of the
                event, and previous event.
        """
        # print("GridSelectionGroup mousePress")
        tool = self.tool
        if event.button() != Qt.LeftButton:
            """ do context menu?
            """
            # slice_graphics_view = self.tool.slice_graphics_view
            # print(slice_graphics_view)
            # tool.getCustomContextMenu(event.screenPos())
            tool.individual_pick = False
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            # print("the right event")
            modifiers = event.modifiers()
            is_shift = modifiers == Qt.ShiftModifier
            # print("Is_shift is %s" % is_shift)
            # check to see if we are clicking on a previously selected item
            if tool.is_selection_active:
                # print("clicking the box")
                pos = event.scenePos()
                for item in tool.slice_graphics_view.scene().items(pos):
                    if isinstance(item, GridVirtualHelixItem):
                        doc = tool.manager.document
                        part = item.part()
                        if is_shift:
                            id_num = item.idNum()
                            if doc.isVirtualHelixSelected(part, id_num):    # maybe should ask the model?
                                doc.removeVirtualHelicesFromSelection(part, [id_num])
                        else:
                            origin_id_num = item.idNum()
                            is_alt = modifiers == Qt.AltModifier
                            if (doc.isVirtualHelixSelected(part, origin_id_num) and
                                    not is_alt):
                                # print("origin", origin_id_num)
                                if tool.snap_origin_item is not None:
                                    tool.snap_origin_item.setSnapOrigin(False)
                                tool.snap_origin_item = item
                                item.setSnapOrigin(True)
                                break
                            else:
                                item.mousePressEvent(event)
            self.drag_start_position = sp = self.pos()
            self.drag_last_position = sp

            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """because :class:`GridSelectionGroup` has the flag
        ``QGraphicsItem.ItemIsMovable`` we need only get the position of the
        item to figure out what to submit to the model

        Args:
            event: the mouse evenet
        """
        # 1. call this super class method first to get the item position updated
        res = QGraphicsItemGroup.mouseMoveEvent(self, event)
        # watch out for bugs here?  everything seems OK for now, but
        # could be weird window switching edge cases
        if not self.tool.individual_pick and event.buttons() == Qt.LeftButton:
            new_pos = self.pos()
            delta = new_pos - self.drag_last_position
            self.drag_last_position = new_pos
            dx, dy = delta.x(), delta.y()
            self.tool.moveSelection(dx, dy, False, use_undostack=False)
        return res
    # end def

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """because :class:`GridSelectionGroup` has the flag
        ``QGraphicsItem.ItemIsMovable`` we need only get the position of the
        item to figure out what to submit to the model

        Args:
            event: the mouse event
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        # print("mouse mouseReleaseEvent", self.tool.individual_pick)
        if not self.tool.individual_pick and event.button() == Qt.LeftButton:
            delta = self.pos() - self.drag_start_position
            dx, dy = delta.x(), delta.y()
            # print(abs(dx), abs(dy))
            if abs(dx) > MOVE_THRESHOLD or abs(dy) > MOVE_THRESHOLD:
                # print("finalizling", dx, dy)
                self.tool.moveSelection(dx, dy, True)
        self.tool.individual_pick = False
        return QGraphicsItemGroup.mouseReleaseEvent(self, event)
    # end def
