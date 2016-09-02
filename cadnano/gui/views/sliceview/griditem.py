
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath, QColor
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem

from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.gui.palette import getPenObj, getBrushObj, getNoPen
from cadnano.cnenum import GridType

from . import slicestyles as styles
_ZVALUE = styles.ZSLICEHELIX + 1


class GridItem(QGraphicsPathItem):
    """Summary

    Attributes:
        allow_snap (TYPE): Description
        bounds (TYPE): Description
        dots (TYPE): Description
        draw_lines (bool): Description
        grid_type (TYPE): Description
        part_item (TYPE): Description
        points (list): Description
    """

    def __init__(self, part_item, grid_type):
        """Summary

        Args:
            part_item (TYPE): Description
            grid_type (TYPE): Description
        """
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        dot_size = 0.5
        self.dots = (dot_size, dot_size / 2)
        self.allow_snap = part_item.window().action_vhelix_snap.isChecked()
        self.draw_lines = True
        self.points = []
        color = QColor(Qt.blue)
        color.setAlphaF(0.1)
        self.setPen(color)
        self.setGridType(grid_type)
    # end def

    def updateGrid(self):
        """Summary

        Returns:
            TYPE: Description
        """
        part_item = self.part_item
        part = part_item.part()
        radius = part.radius()
        self.bounds = bounds = part_item.bounds()
        self.removePoints()
        if self.grid_type == GridType.HONEYCOMB:
            self.doHoneycomb(part_item, radius, bounds)
        elif self.grid_type == GridType.SQUARE:
            self.doSquare(part_item, radius, bounds)
        else:
            self.setPath(QPainterPath())
    # end def

    def setGridType(self, grid_type):
        """Summary

        Args:
            grid_type (TYPE): Description

        Args:
            TYPE: Description
        """
        self.grid_type = grid_type
        self.updateGrid()
    # end def

    def setDrawlines(self, draw_lines):
        """Summary

        Args:
            draw_lines (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.draw_lines = draw_lines
        self.updateGrid()
    # end def

    def doHoneycomb(self, part_item, radius, bounds):
        """Summary

        Args:
            part_item (TYPE): Description
            radius (TYPE): Description
            bounds (TYPE): Description

        Returns:
            TYPE: Description
        """
        doLattice = HoneycombDnaPart.latticeCoordToPositionXY
        doPosition = HoneycombDnaPart.positionToLatticeCoordRound
        isEven = HoneycombDnaPart.isEvenParity
        x_l, x_h, y_l, y_h = bounds
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, False, False, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, True, True, scale_factor=sf)
        # print(row_l, row_h, col_l, col_h)

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines
        for i in range(row_l, row_h):
            for j in range(col_l, col_h+1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
                if draw_lines:
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                """ +x is Left and +y is down
                origin of ellipse is Top Left corner so we subtract half in X
                and subtract in y
                """
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)
                pt.setPen(getPenObj(Qt.blue, 1.0))
                points.append(pt)
            is_pen_down = False
        # end for i
        # DO VERTICAL LINES
        if draw_lines:
            for j in range(col_l, col_h+1):
                # print("newcol")
                for i in range(row_l, row_h):
                    x, y = doLattice(radius, i, j, scale_factor=sf)
                    if is_pen_down and isEven(i, j):
                        path.lineTo(x, -y)
                        is_pen_down = False
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False
            # end for j
        self.setPath(path)
    # end def

    def doSquare(self, part_item, radius, bounds):
        """Summary

        Args:
            part_item (TYPE): Description
            radius (TYPE): Description
            bounds (TYPE): Description

        Returns:
            TYPE: Description
        """
        doLattice = SquareDnaPart.latticeCoordToPositionXY
        doPosition = SquareDnaPart.positionToLatticeCoordRound
        x_l, x_h, y_l, y_h = bounds
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, scale_factor=sf)
        # print(row_l, row_h, col_l, col_h)

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines

        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
                if draw_lines:
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                """ +x is Left and +y is down
                origin of ellipse is Top Left corner so we subtract half in X
                and subtract in y
                """
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)
                pt.setPen(getPenObj(Qt.blue, 1.0))
                points.append(pt)
            is_pen_down = False  # pen up
        # DO VERTICAL LINES
        if draw_lines:
            for j in range(col_l, col_h + 1):
                for i in range(row_l, row_h + 1):
                    x, y = doLattice(radius, i, j, scale_factor=sf)
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False  # pen up
        self.setPath(path)
    # end def

    def removePoints(self):
        """Summary

        Returns:
            TYPE: Description
        """
        points = self.points
        scene = self.scene()
        while points:
            scene.removeItem(points.pop())
    # end def
# end class


class ClickArea(QGraphicsEllipseItem):
    """Summary

    Attributes:
        parent_obj (TYPE): Description
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, diameter, parent):
        nd = 2*self._RADIUS
        offset = -0.5*nd + diameter/2
        super(ClickArea, self).__init__(offset, offset, nd, nd, parent=parent)
        self.parent_obj = parent
        self.setAcceptHoverEvents(True)
        self.setPen(getNoPen())
    # end def

    def mousePressEvent(self, event):
        return self.parent_obj.mousePressEvent(event)
# end class


class GridPoint(QGraphicsEllipseItem):
    """Summary

    Attributes:
        clickarea (TYPE): Description
        grid (TYPE): Description
        offset (TYPE): Description
    """
    __slots__ = 'grid', 'offset'

    def __init__(self, x, y, diameter, parent_grid):
        super(GridPoint, self).__init__(0., 0.,
                                        diameter, diameter, parent=parent_grid)
        self.offset = diameter / 2
        self.grid = parent_grid

        self.clickarea = ClickArea(diameter, parent=self)

        self.setPos(x, y)
        self.setZValue(_ZVALUE)
        self.setAcceptHoverEvents(True)
    # end def

    def mousePressEvent(self, event):
        """Handler for user mouse press.

        Args:
            event (QGraphicsSceneMouseEvent): Contains item, scene, and screen
            coordinates of the the event, and previous event.

        Returns:
            TYPE: Description
        """
        if self.grid.allow_snap:
            part_item = self.grid.part_item
            tool = part_item._getActiveTool()
            if tool.FILTER_NAME not in part_item.part().document().filter_set:
                return
            tool_method_name = tool.methodPrefix() + "MousePress"
            if hasattr(self, tool_method_name):
                getattr(self, tool_method_name)(tool, part_item, event)
        else:
            QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def hoverEnterEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        self.setBrush(getBrushObj(styles.ACTIVE_GRID_DOT_COLOR))
        self.setPen(getPenObj(styles.ACTIVE_GRID_DOT_COLOR, 1.0))
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        self.setBrush(getBrushObj(styles.DEFAULT_GRID_DOT_COLOR))
        self.setPen(getPenObj(styles.DEFAULT_GRID_DOT_COLOR, 1.0))
    # end def

    def selectToolMousePress(self, tool, part_item, event):
        """Summary

        Args:
            tool (TYPE): Description
            part_item (TYPE): Description
            event (TYPE): Description
        """
        part = part_item.part()
        part.setSelected(True)
        # print("monkey")
        alt_event = GridEvent(self, self.offset)
        tool.selectOrSnap(part_item, alt_event, event)
        return QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def createToolMousePress(self, tool, part_item, event):
        """Summary

        Args:
            tool (TYPE): Description
            part_item (TYPE): Description
            event (TYPE): Description
        """
        part = part_item.part()
        part.setSelected(True)
        # print("paws")
        alt_event = GridEvent(self, self.offset)
        part_item.createToolMousePress(tool, event, alt_event)
    # end def


class GridEvent(object):
    """Summary

    Attributes:
        grid_pt (TYPE): Description
        offset (QPointF): Description
    """
    __slots__ = 'grid_pt', 'offset'

    def __init__(self, grid_pt, offset):
        """Summary

        Args:
            grid_pt (TYPE): Description
            offset (TYPE): Description
        """
        self.grid_pt = grid_pt
        self.offset = QPointF(offset, offset)

    def scenePos(self):
        """Scene position, with offset.

        Returns:
            QPointF: Description
        """
        return self.grid_pt.scenePos() + self.offset

    def pos(self):
        """Local position, with offset.

        Returns:
            QPointF: Description
        """
        return self.grid_pt.pos() + self.offset
