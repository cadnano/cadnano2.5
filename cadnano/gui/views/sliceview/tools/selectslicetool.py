from .abstractslicetool import AbstractSliceTool
from PyQt5.QtCore import QRect, QRectF, QPointF, Qt
from PyQt5.QtWidgets import (QGraphicsItemGroup, QGraphicsRectItem,
                             QGraphicsItem, QMenu, QAction)

from cadnano.gui.views.sliceview.virtualhelixitem import VirtualHelixItem
from cadnano.gui.palette import getPenObj
from cadnano.fileio import v3encode, v3decode

def normalizeRect(rect):
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

class SelectSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, manager):
        super(SelectSliceTool, self).__init__(manager)
        self.last_rubberband_vals = (None, None, None)
        self.selection_set = set()
        self.group = SliceSelectionGroup(self)
        self.group.hide()
        self.is_selection_active = False
        self.individual_pick = False
        self.snap_origin_item = None
        self.clip_board = None
    # end def

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase

    def isSelectionActive(self):
        return self.is_selection_active
    # end def

    def modelClear(self):
        doc = self._manager.document
        doc.clearAllSelected()

    def setPartItem(self, part_item):
        if part_item != self.part_item:
            if self.sgv is not None:
                # attempt to enforce good housekeeping, not required
                try:
                    self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
                except:
                    # required for first call
                    pass
            self.modelClear()
            self.part_item = part_item
            self.group.setParentItem(part_item)

            # required for whatever reason to renable QGraphicsView.RubberBandDrag
            self.sgv.activateSelection(True)

            self.sgv.rubberBandChanged.connect(self.selectRubberband)
    # end def

    def selectRubberband(self, rect, from_pt, to_point):
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
            # print(res)

            doc = self._manager.document
            doc.clearAllSelected()
            doc.addVirtualHelicesToSelection(part, res)
        else:
            self.last_rubberband_vals = (rect, from_pt, to_point)
    # end def

    def getSelectionBoundingRect(self):
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
        # print("deselecting")
        group = self.group
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

    def deselectSet(self, vh_set):
        group = self.group
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
            return
        group.clearSelectionRect()
        return False
    # end def

    def selectOrSnap(self, part_item, target_item, event):
        """
        Args:
            part_item (PartItem):
            snap_to_item (VirtualHelixItem or GridEvent): Item to snap
                selection to
        """
        self.setPartItem(part_item)
        if (self.snap_origin_item is not None and
            event.modifiers() != Qt.ShiftModifier):
            self.doSnap(part_item, target_item)
            self.individual_pick = False
        else: # just do a selection
            if event.modifiers() != Qt.ShiftModifier:
                self.modelClear()   # deselect if shift isn't held

            if isinstance(target_item, VirtualHelixItem):
                # NOTE: individual_pick seems not needed.
                # it's supposed to allow for single item picking
                # self.individual_pick = True

                self.snap_origin_item = None

                doc = self._manager.document
                part = part_item.part()
                doc.addVirtualHelicesToSelection(part, [target_item.idNum()])
    # end def

    def doSnap(self, part_item, snap_to_item):
        """
        Args:
            part_item (PartItem):
            snap_to_item (VirtualHelixItem or GridEvent): Item to snap
                selection to
        """
        # print("snapping")
        origin = self.snap_origin_item.getCenterScenePos()

        # xy = part_item.mapFromScene(snap_to_item.scenePos())
        # xy2 = part_item.mapFromScene(self.snap_origin_item.scenePos())
        # print("snapping from:", xy2.x(), xy2.y())
        # print("snapped to:", xy.x(), xy.y())

        if isinstance(snap_to_item, VirtualHelixItem):
            self.setVirtualHelixItem(snap_to_item)
            destination = self.findNearestPoint(part_item, origin)
        else: # GridEvent
            destination = snap_to_item.pos()

        origin = part_item.mapFromScene(origin)
        if destination is None:
            destination = origin
        if origin == destination:
            # snap clockwise
            destination = self.findNextPoint(part_item, origin)
        if origin is None or destination is None:
            print("o", origin, "d", destination)
        delta = destination - origin
        dx, dy = delta.x(), delta.y()
        group = self.group
        pos = group.pos() + delta
        self.group.setPos(pos)
        self.moveSelection(dx, dy, False, use_undostack=True)
        self.hideLineItem()
    # end def

    def copySelection(self):
        part = self.part_item.part()
        copy_dict = v3encode.encodePart2(part,
                                        list(self.selection_set))
        self.clip_board = copy_dict
    # end def

    def pasteClipboard(self):
        doc = self._manager.document
        part = self.part_item.part()
        doc.undoStack().beginMacro("Paste VirtualHelices")
        new_vh_set = v3decode.importToPart(part, self.clip_board)
        doc.undoStack().endMacro()
        self.modelClear()
        doc.addVirtualHelicesToSelection(part, new_vh_set)
    # end def


    def moveSelection(self, dx, dy, finalize, use_undostack=True):
        """ Y-axis is inverted in Qt +y === DOWN
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
        if self.sgv is not None:
            try:
                self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
            except:
                pass    # required for first call
        self.modelClear()
        self.snap_origin_item = None
        AbstractSliceTool.deactivate(self)
    # end def

    def getCustomContextMenu(self, point):
        """ point (QPoint)
        """
        if len(self.selection_set) > 0:
            sgv = self.sgv
            menu = QMenu(sgv)
            copy_act = QAction("copy selection", sgv)
            copy_act.setStatusTip("copy selection")
            copy_act.triggered.connect(self.copySelection)
            menu.addAction(copy_act)
            if self.clip_board:
                copy_act = QAction("paste", sgv)
                copy_act.setStatusTip("paste from clip board")
                copy_act.triggered.connect(self.pasteClipboard)
                menu.addAction(copy_act)
            menu.exec_(sgv.mapToGlobal(point))
    # end def

# end class

class SliceSelectionGroup(QGraphicsItemGroup):
    def __init__(self, tool, parent=None):
        super(SliceSelectionGroup, self).__init__(parent)
        self.tool = tool
        self.setFiltersChildEvents(True)
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # for keyPressEvents
        self.setFlag(QGraphicsItem.ItemIsMovable)

        self.bounding_rect_item = QGraphicsRectItem()
        self.bounding_rect_item.hide()
        self.bounding_rect_item.setPen(getPenObj(_SELECT_COLOR,
                                            _SELECT_PEN_WIDTH))
        self.drag_start_position = QPointF()
        self.drag_last_position = QPointF()
    # end def

    def resetGroupPos(self, child):
        """ call this to prevent the group from drifting position over time
        """
        if len(self.childItems()) == 0:
            self.setPos(self.mapFromScene(child.scenePos()))
    # end def

    def setSelectionRect(self):
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
        """ reset positions to zero to keep things in check
        """
        bri = self.bounding_rect_item
        bri.hide()
        self.removeFromGroup(bri)
        self.setFocus(False)
    # end def

    def keyPressEvent(self, event):
        """ event.key() seems to be capital only? """
        print("press", ord('g'))
        if event.text() == 'g':
            print("hey het")
        return QGraphicsItem.keyPressEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        tool = self.tool
        if event.button() != Qt.LeftButton:
            """ do context menu?
            """
            # sgv = self.tool.sgv
            # print(sgv)
            # self.getCustomContextMenu(event.screenPos())
            tool.individual_pick = False
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            # print("the right event")
            is_shift = event.modifiers() == Qt.ShiftModifier
            # check to see if we are clicking on a previously selected item
            if tool.is_selection_active:
                # print("clicking the box")
                pos = event.scenePos()
                for item in tool.sgv.scene().items(pos):
                    if isinstance(item, VirtualHelixItem):
                        if is_shift:
                            doc = tool._manager.document
                            part = item.part()
                            id_num = item.idNum()
                            if doc.isVirtualHelixSelected(part, id_num):    # maybe should ask the model?
                                doc.removeVirtualHelicesFromSelection(part, [id_num])
                        else:
                            print("origin", item.idNum())
                            tool.snap_origin_item = item
                            break
            self.drag_start_position = sp = self.pos()
            self.drag_last_position = sp

            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """ because SliceSelectionGroup has the flag
        QGraphicsItem.ItemIsMovable
        we need only get the position of the item to figure
        out what to submit to the model
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

    def mouseReleaseEvent(self, event):
        """ because SliceSelectionGroup has the flag
        QGraphicsItem.ItemIsMovable
        we need only get the position of the item to figure
        out what to submit to the model
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
