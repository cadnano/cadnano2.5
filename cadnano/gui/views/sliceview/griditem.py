# from queue import Queue

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem

from cadnano.cnenum import GridType
from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.gui.palette import getNoPen, getPenObj, getBrushObj  # getBrushObj

from . import slicestyles as styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_ZVALUE = styles.ZSLICEHELIX + 1
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH) / 2.


class GridItem(QGraphicsPathItem):
    def __init__(self, part_item, grid_type):
        """Summary

        previous_grid_bounds (tuple):  a tuple corresponding to the bounds of
        the grid.

        Args:
            part_item (TYPE): Description
            grid_type (TYPE): Description
        """
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        # TODO[NF] Make this a constant
        dot_size = 30
        self.dots = (dot_size, dot_size / 2)
        self.allow_snap = part_item.window().action_vhelix_snap.isChecked()
        self.draw_lines = False
        self.points = []
        self.points_dict = dict()
        self.previous_grid_bounds = None
        color = QColor(Qt.blue)
        color.setAlphaF(0.1)
        self.setPen(color)
        self.setGridType(grid_type)
        self.previous_grid_type = grid_type

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
            self.createHoneycombGrid(part_item, radius, bounds)
        elif self.grid_type == GridType.SQUARE:
            self.createSquareGrid(part_item, radius, bounds)
        else:
            self.setPath(QPainterPath())
    # end def

    def setGridType(self, grid_type):
        """Sets the grid type. See cadnano.cnenum.GridType.

        Args:
            grid_type (GridType): NONE, HONEYCOMB, or SQUARE
        """
        self.grid_type = grid_type
        self.updateGrid()
    # end def

    def setAppearance(self, draw_lines):
        # TODO[NF]:  Docstring
        return

    def createHoneycombGrid(self, part_item, radius, bounds):
        """Instantiate an area of griditems arranged on a honeycomb lattice.

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
        x_l = x_l + HoneycombDnaPart.PAD_GRID_XL
        x_h = x_h + HoneycombDnaPart.PAD_GRID_XH
        y_h = y_h + HoneycombDnaPart.PAD_GRID_YL
        y_l = y_l + HoneycombDnaPart.PAD_GRID_YH
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, False, False, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, True, True, scale_factor=sf)

        redo_neighbors = (row_l, col_l, row_h, col_h) != self.previous_grid_bounds or\
            self.previous_grid_type != self.grid_type
        self.previous_grid_type = self.grid_type

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines

        if redo_neighbors:
            point_coordinates = dict()
            neighbor_map = dict()
            self.points_dict = dict()

        for row in range(row_l, row_h):
            for column in range(col_l, col_h + 1):
                x, y = doLattice(radius, row, column, scale_factor=sf)
                if draw_lines:
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                """
                +x is Left and +y is down
                origin of ellipse is Top Left corner so we subtract half in X and subtract in y
                """
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size,
                               self,
                               coord=(row, column))

                pt.setPen(getPenObj(Qt.blue, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
                    point_coordinates[(-row, column)] = (x, -y)

                    # This is reversed since the Y is mirrored
                    if not HoneycombDnaPart.isEvenParity(row, column):
                        neighbor_map[(-row, column)] = [
                            (-row, column - 1),
                            (-row, column + 1),
                            (-row - 1, column)
                        ]
                    else:
                        neighbor_map[(-row, column)] = [
                            (-row, column - 1),
                            (-row, column + 1),
                            (-row + 1, column)
                        ]
                    self.previous_grid_bounds = (row_l, col_l, row_h, col_h)

            is_pen_down = False

        if draw_lines:
            for column in range(col_l, col_h + 1):
                # print("newcol")
                for row in range(row_l, row_h):
                    x, y = doLattice(radius, row, column, scale_factor=sf)
                    if is_pen_down and isEven(row, column):
                        path.lineTo(x, -y)
                        is_pen_down = False
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False
            # end for j
        self.setPath(path)

        if redo_neighbors:
            self.part_item.setNeighborMap(neighbor_map=neighbor_map)
            self.part_item.setPointMap(point_map=point_coordinates)

    def createSquareGrid(self, part_item, radius, bounds):
        """Instantiate an area of griditems arranged on a square lattice.

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

        redo_neighbors = (row_l, col_l, row_h, col_h) != \
            self.previous_grid_bounds or self.previous_grid_type != self.grid_type
        self.previous_grid_type = self.grid_type

        if redo_neighbors:
            point_map = dict()
            neighbor_map = dict()

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines

        for row in range(row_l, row_h + 1):
            for column in range(col_l, col_h + 1):
                x, y = doLattice(radius, row, column, scale_factor=sf)
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
                               dot_size,
                               self,
                               coord=(row, column))

                pt.setPen(getPenObj(Qt.blue, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
                    point_map[(-row, column)] = (x, -y)

                    neighbor_map[(-row, column)] = [
                        (-row, column + 1),
                        (-row, column - 1),
                        (-row - 1, column),
                        (-row + 1, column)
                    ]

                    self.previous_grid_bounds = (row_l, col_l, row_h, col_h)

            is_pen_down = False  # pen up

        # DO VERTICAL LINES
        if draw_lines:
            for column in range(col_l, col_h + 1):
                for row in range(row_l, row_h + 1):
                    x, y = doLattice(radius, row, column, scale_factor=sf)
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False  # pen up
        self.setPath(path)

        if redo_neighbors:
            self.part_item.setNeighborMap(neighbor_map=neighbor_map)
            self.part_item.setPointMap(point_map=point_map)
    # end def

    def removePoints(self):
        """Remove all points from the grid.
        """
        points = self.points
        scene = self.scene()
        while points:
            scene.removeItem(points.pop())

        self.points_dict = dict()

    def changeGridPointColor(self, coordinates, color):
        point = self.points_dict.get(coordinates)

        if point is None:
            print('Could not find')
        else:
            point.setBrush(getBrushObj(color))


class ClickArea(QGraphicsEllipseItem):
    """An extra ellipse with slightly.

    Args:
        diameter (float): defines the size of the clickarea.
        parent (GridItem): the item.
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, diameter, parent):
        nd = 2 * self._RADIUS
        offset = -0.5 * nd + diameter / 2
        super(ClickArea, self).__init__(offset, offset, nd, nd, parent=parent)
        self.parent_obj = parent
        self.setAcceptHoverEvents(True)
        self.setPen(getNoPen())
    # end def

    def mousePressEvent(self, event):
        """Event that is triggered when the mouse is clicked anywhere on the
        grid.
        """
        return self.parent_obj.mousePressEvent(event)

    def hoverMoveEvent(self, event):
        self.parent_obj.hoverMoveEvent(event)


class GridPoint(QGraphicsEllipseItem):
    """Summary

    Attributes:
        clickarea (TYPE): Description
        grid (TYPE): Description
        offset (TYPE): Description
    """
    __slots__ = 'grid', 'offset'

    def __init__(self, x, y, diameter, parent_grid, coord=None):
        super(GridPoint, self).__init__(0., 0., diameter, diameter, parent=parent_grid)
        self.offset = diameter / 2
        self.grid = parent_grid
        self._coord = coord

        self.clickarea = ClickArea(diameter, parent=self)

        self.setPos(x, y)
        self.setZValue(_ZVALUE)
        self.setAcceptHoverEvents(True)
    # end def

    def coord(self):
        """Lattice coordinates, if available.

        Returns:
            row (int): lattice row
            column (int): lattice column
        """
        if self._coord:
            row, column = self._coord
            return row, column

    def mousePressEvent(self, event):
        """Handler for user mouse press.

        Args:
            event (QGraphicsSceneMouseEvent): Contains item, scene, and screen
            coordinates of the the event, and previous event.

        Returns:
            None
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

    def hoverMoveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "HoverMoveEvent"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)

    def hoverEnterEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "HoverEnterEvent"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        # Turn the outline of the GridItem off
        self.setPen(getPenObj(styles.DEFAULT_GRID_DOT_COLOR, styles.EMPTY_HELIX_STROKE_WIDTH))

        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "HoverLeaveEvent"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
        return
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
        alt_event = GridEvent(self, self.offset)
        tool.selectOrSnap(part_item, alt_event, event)
        return QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def createToolMousePress(self, tool, part_item, event):
        """Called by mousePressEvent when clicking on the grid

        Args:
            tool (CreateSliceTool): The tool that is being used
            part_item (TYPE):
            event (QGraphicsSceneMouseEvent): The event that the mouseclick
            triggered
        """
        part = part_item.part()
        part.setSelected(True)
        alt_event = GridEvent(self, self.offset)
        part_item.createToolMousePress(tool, event, alt_event)

    def createToolHoverEnterEvent(self, tool, part_item, event):
        self.setPen(getPenObj(styles.DEFAULT_GRID_DOT_COLOR, 1.5))
        part_item.setLastHoveredItem(self)
        part_item.createToolHoverEnter(tool, event)

    def createToolHoverMoveEvent(self, tool, part_item, event):
        part_item.createToolHoverMove(tool, event)

    def createToolHoverLeaveEvent(self, tool, part_item, event):
        part_item.createToolHoverLeave(tool, event)


class GridEvent(object):
    """Instantiated by selectToolMousePress or createToolMousePress.

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
