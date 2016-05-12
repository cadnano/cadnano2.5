
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsPathItem,
                            QGraphicsEllipseItem, QGraphicsRectItem,
                            QGraphicsLineItem)

from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart

from . import slicestyles as styles
_ZVALUE = styles.ZSLICEHELIX + 1

class GridItem(QGraphicsPathItem):
    def __init__(self, part_item):
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        dot_size = 4.
        self.dots = (dot_size, dot_size / 2)
        self.allow_snap = True
        # self.allow_snap = False
        self.is_honeycomb = True
        self.draw_lines = True
        self.points = []
        color = QColor(Qt.blue)
        color.setAlphaF(0.1)
        self.setPen(color)
        self.updateGrid()
    # end def

    def updateGrid(self):
        part_item = self.part_item
        part = part_item.part()
        radius = part.radius()
        self.bounds = bounds = part_item.bounds()
        self.removePoints()
        if self.is_honeycomb:
            self.doHoneycomb(part_item, radius, bounds)
        else:
            self.doSquare(part_item, radius, bounds)
    # end def

    def setHoneycomb(self, is_honeycomb):
        self.is_honeycomb = is_honeycomb
        self.updateGrid()
    # end def

    def doHoneycomb(self, part_item, radius, bounds):
        doLattice = HoneycombDnaPart.latticeCoordToPositionXY
        doPosition = HoneycombDnaPart.positionToLattticeCoordRound
        isEven = HoneycombDnaPart.isEvenParity
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
                pt = GridPoint( x - half_dot_size,
                                -y - half_dot_size,
                                dot_size, self)
                pt.setPen(QPen(Qt.black))
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
        doLattice = SquareDnaPart.latticeCoordToPositionXY
        doPosition = SquareDnaPart.positionToLattticeCoordRound
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
                pt = GridPoint( x - half_dot_size,
                                -y - half_dot_size,
                                dot_size, self)
                pt.setPen(QPen(Qt.black))
                points.append(pt)
            is_pen_down = False # pen up
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
                is_pen_down = False # pen up
        self.setPath(path)
    # end def

    def removePoints(self):
        points = self.points
        scene = self.scene()
        while points:
            scene.remove(points.pop())
    # end def
# end class

class GridPoint(QGraphicsEllipseItem):
    __slots__ = 'grid', 'offset'

    def __init__(self, x, y, diameter, parent_grid):
        super(GridPoint, self).__init__(0., 0.,
                                        diameter, diameter, parent=parent_grid)
        self.offset = diameter / 2
        self.grid = parent_grid
        self.setPos(x, y)
        self.setZValue(_ZVALUE)
    # end def

    def mousePressEvent(self, event):
        if self.grid.allow_snap:
            part_item = self.grid.part_item
            tool = part_item._getActiveTool()
            tool_method_name = tool.methodPrefix() + "MousePress"
            if hasattr(self, tool_method_name):
                getattr(self, tool_method_name)(tool, part_item, event)
        else:
            QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def selectToolMousePress(self, tool, part_item, event):
        part = part_item.part()
        part.setSelected(True)
        print("monkey")
        alt_event = GridEvent(self, self.offset)
        tool.selectOrSnap(part_item, alt_event, event)
    # end def

    def createToolMousePress(self, tool, part_item, event):
        part = part_item.part()
        part.setSelected(True)
        print("paws")
        alt_event = GridEvent(self, self.offset)
        part_item.createToolMousePress(tool, event, alt_event)
    # end def

class GridEvent(object):
    __slots__ = 'grid_pt', 'offset'
    def __init__(self, grid_pt, offset):
        self.grid_pt = grid_pt
        self.offset = QPointF(offset, offset)

    def scenePos(self):
        return self.grid_pt.scenePos() + self.offset

    def pos(self):
        return self.grid_pt.pos() + self.offset