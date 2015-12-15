from .abstractslicetool import AbstractSliceTool
from PyQt5.QtCore import QRect, QRectF, QPointF, Qt
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsItem

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
        self.selection_set = None
        self.group = SliceSelectionGroup(self)
        self.group.hide()
        self.is_selection_active = False
    # end def

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase

    def setPartItem(self, part_item):
        if self.sgv is not None:
            self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
            self.sgv = None
        self.deselectItems()
        self.part_item = part_item
        self.group.setParentItem(part_item)
        self.sgv = part_item.window().slice_graphics_view
        self.sgv.rubberBandChanged.connect(self.selectRubberband)
    # end def

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._right_mouse_move = True
            self._button_down_pos = event.pos()
    # end def

    def mouseMoveEvent(self, event):
        if self._right_mouse_move:
            # p = event.pos() - self._button_down_pos
            # self.setPos(p)
            self.setCenterPos(p)
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
        group.setSelectionRect()
        print("showing")
        group.show()
        # self.deselectItems()
    # end def

    def deselectItems(self):
        if self.is_selection_active:
            part_item = self.part_item
            group = self.group
            for vh in self.selection_set:
                vhi = part_item.getVirtualHelixItem(vh)
                group.removeFromGroup(vhi)
            group.hide()
            self.is_selection_active = False
            return True
        return False
    # end def

    def moveSelection(self, dx, dy):
        part_item = self.part_item
        part = part_item.part()
        print("translational delta:", dx, dy)
        part.moveVirtualHelices(self.selection_set, dx, dy)
    # end def

    def deactivate(self):
        if self.sgv is not None:
            self.sgv.rubberBandChanged.disconnect(self.selectRubberband)
            self.sgv = None
        self.deselectItems()
        AbstractSliceTool.deactivate(self)
    # end def
# end class

class SliceSelectionGroup(QGraphicsItemGroup):
    def __init__(self, tool, parent=None):
        super(SliceSelectionGroup, self).__init__(parent)
        self.tool = tool
        self.setFiltersChildEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # for keyPressEvents
        self.setFlag(QGraphicsItem.ItemIsMovable)

        self.bounding_rect_item = QGraphicsRectItem(self)
        self.bounding_rect_item.hide()
        self.bounding_rect_item.setPen(getPenObj(_SELECT_COLOR,
                                            _SELECT_PEN_WIDTH))
        self.drag_start_position = QPointF()
        self.current_position = QPointF()
    # end def

    def setSelectionRect(self):
        bri = self.bounding_rect_item
        bri.setRect(self.boundingRect())
        bri.show()
    # end def

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            self.drag_start_position = event.scenePos()
            self.current_position = self.pos()
            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        """
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        if event.button() == Qt.LeftButton:
            # print("positions:", event.lastScenePos(), event.scenePos(), event.pos())
            delta = event.lastScenePos() - self.drag_start_position
            # invert y axis since qt y is positive in the down direction
            dx, dy = delta.x(), -1.*delta.y()
            if abs(dx) > MOVE_THRESHOLD or abs(dy) > MOVE_THRESHOLD:
                self.tool.moveSelection(dx, dy)
            else:
                print("small move", dx, dy)
                # restore starting position
                self.setPos(self.current_position)
                # self.setPos(self.current_position + delta)
        return QGraphicsItemGroup.mouseReleaseEvent(self, event)
    # end def
