
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QBrush, QPen, QPainterPath
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsPathItem,
                            QGraphicsEllipseItem, QGraphicsRectItem,
                            QGraphicsLineItem)

from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart

class GridItem(QGraphicsPathItem):
    def __init__(self, part_item):
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        dot_size = 0.5
        self.dots = (dot_size, dot_size/2)
        self.is_honeycomb = True
        self.draw_lines = True
        self.points = []
        self.setPen(QPen(Qt.blue))
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
                pt = QGraphicsEllipseItem(x - half_dot_size, -y - half_dot_size,
                                    dot_size, dot_size, self)
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

        for i in range(row_l, row_h+1):
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
                pt = QGraphicsEllipseItem(x - half_dot_size, -y - half_dot_size,
                                    dot_size, dot_size, self)
                pt.setPen(QPen(Qt.black))
                points.append(pt)
            is_pen_down = False # pen up
        # DO VERTICAL LINES
        if draw_lines:
            for j in range(col_l, col_h+1):
                for i in range(row_l, row_h+1):
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