from .abstractslicetool import AbstractSliceTool
from PyQt5.QtCore import QRect, QRectF, QPointF, Qt
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsItem

from cadnano.gui.views.sliceview.virtualhelixitem import VirtualHelixItem
from cadnano.gui.palette import getPenObj

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

class SelectSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, controller, parent=None):
        super(SelectSliceTool, self).__init__(controller)
        self.sgv = None
        self.last_rubberband_vals = (None, None, None)
        self.selection_set = set()
        self.group = SliceSelectionGroup(self)
        self.group.hide()
        self.is_selection_active = False
        self.individual_pick = False
        self.snap_origin_item = None
    # end def

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase

    def isSelectionActive(self):
        return self.is_selection_active
    # end def

    def setPartItem(self, part_item):
        if part_item != self.part_item:
            if self.sgv is not None:
                self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
                self.sgv = None
            self.deselectItems()
            self.part_item = part_item
            self.group.setParentItem(part_item)
            self.sgv = part_item.window().slice_graphics_view
            self.sgv.rubberBandChanged.connect(self.selectRubberband)
    # end def

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.RightButton:
    #         self._right_mouse_move = True
    #         self._button_down_pos = event.pos()
    # # end def

    # def mouseMoveEvent(self, event):
    #     if self._right_mouse_move:
    #         # p = event.pos() - self._button_down_pos
    #         # self.setPos(p)
    #         self.setCenterPos(p)
    # # end def

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
            self.selection_set = res
            self.getSelectionBoundingRect()
        else:
            self.last_rubberband_vals = (rect, from_pt, to_point)
    # end def

    def getSelectionBoundingRect(self):
        part_item = self.part_item
        group = self.group
        self.deselectItems()
        for vh in self.selection_set:
            vhi = part_item.getVirtualHelixItem(vh)
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
            for vh in self.selection_set:
                vhi = part_item.getVirtualHelixItem(vh)
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

    def addToSelection(self, vhi):
        group = self.group
        group.addToGroup(vhi)
        self.selection_set.add(vhi.virtualHelix())
        if len(group.childItems()) > 0:
            self.is_selection_active = True
            group.setSelectionRect()
            group.show()
            self.individual_pick = True
            self.snap_origin_item = None
    # end def

    def selectOrSnap(self, part_item, virtual_helix_item, event):
        self.setPartItem(part_item)
        if self.snap_origin_item is not None and event.modifiers() != Qt.ShiftModifier:
            self.doSnap(part_item, virtual_helix_item)
            self.individual_pick = False
        else: # just do a selection
            if event.modifiers() != Qt.ShiftModifier:
                self.deselectItems()
            self.addToSelection(virtual_helix_item)
    # end def

    def doSnap(self, part_item, virtual_helix_item):
        origin = self.snap_origin_item.getCenterScenePos()
        self.setVirtualHelixItem(virtual_helix_item)
        destination = self.findNearestPoint(part_item, origin)
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
        self.moveSelection(dx, dy)
        self.hideLineItem()
    # end def

    def moveSelection(self, dx, dy):
        """ Y-axis is inverted in Qt +y === DOWN
        """
        # print("moveSelection: {}, {}", dx, dy)
        part_item = self.part_item
        sf = part_item.scaleFactor()
        part = part_item.part()
        part.translateVirtualHelices(self.selection_set, dx / sf, -dy / sf)
    # end def

    def deactivate(self):
        if self.sgv is not None:
            self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
            self.sgv = None
        self.deselectItems()
        self.snap_origin_item = None
        AbstractSliceTool.deactivate(self)
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
        self.current_position = QPointF()
    # end def

    def setSelectionRect(self):
        bri = self.bounding_rect_item
        bri.setRect(self.childrenBoundingRect())
        bri.setPos(bri.mapFromItem(self, self.pos()))
        self.addToGroup(bri)
        bri.show()
        self.setFocus(True)
    # end def

    def clearSelectionRect(self):
        bri = self.bounding_rect_item
        bri.hide()
        self.removeFromGroup(bri)
        self.setFocus(False)
        # self.setPos(QPointF(0,0))
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
        tool.individual_pick = False
        if event.button() != Qt.LeftButton:
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            # check to see if we are clicking on a previously selected item
            if tool.is_selection_active:
                # strategy #1
                pos = event.scenePos()
                for item in tool.sgv.scene().items(pos):
                    if isinstance(item, VirtualHelixItem):
                        print("origin", item.virtualHelix())
                        tool.snap_origin_item = item
                        break
                # strategy #2
                # pos = event.pos()
                # mapper = self.mapToItem
                # for item in self.childItems():
                #     pos_local = mapper(item, pos)
                #     if isinstance(item, VirtualHelixItem) and item.contains(pos_local):
                #         print("origin", item.virtualHelix())
                #         tool.snap_origin_item = item
                #         break
            self.drag_start_position = event.scenePos()
            self.current_position = self.pos()
            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        """
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        if not self.tool.individual_pick and event.button() == Qt.LeftButton:
            # print("positions:", event.lastScenePos(), event.scenePos(), event.pos())
            delta = event.lastScenePos() - self.drag_start_position
            # invert y axis since qt y is positive in the down direction
            dx, dy = delta.x(), delta.y()
            if abs(dx) > MOVE_THRESHOLD or abs(dy) > MOVE_THRESHOLD:
                self.tool.moveSelection(dx, dy)
            elif dx != 0.0 and dy != 0.0:
                print("small move", dx, dy)
                # restore starting position
                self.setPos(self.current_position)
                # self.setPos(self.current_position + delta)
        self.tool.individual_pick = False
        return QGraphicsItemGroup.mouseReleaseEvent(self, event)
    # end def
