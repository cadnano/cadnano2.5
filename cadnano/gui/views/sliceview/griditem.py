from queue import Queue

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath, QColor, QFont
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem
from PyQt5.uic.properties import QtGui

from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.gui.palette import getPenObj, getBrushObj, getNoPen
from cadnano.cnenum import GridType

from . import slicestyles as styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_ZVALUE = styles.ZSLICEHELIX + 1
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.


class GridItem(QGraphicsPathItem):
    """Summary

    Attributes:
        allow_snap (TYPE): Description
        bounds (TYPE): Description
        dots (tuple): Index 0 corresponds to the size of the dot, index 1
        corresponds to half the size of the dot
        draw_lines (bool): Description
        grid_type (TYPE): Description
        part_item (TYPE): Description
        points (list): Description
    """

    def __init__(self, part_item, grid_type):
        """Summary

        point_map contains a mapping of i, j row-column coordinates to actual GridPoint items.  neihgbor_map contains a mapping of i, j row-column coordinates to a list of i, j row-column coordinates of neighbors

        Args:
            part_item (TYPE): Description
            grid_type (TYPE): Description
        """
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        dot_size = 30
        self.dots = (dot_size, dot_size / 2)
        self.allow_snap = part_item.window().action_vhelix_snap.isChecked()
        self.draw_lines = False
        self.points = []
        self.point_map = dict()
        self.point_coordinates = dict()
        self.neighbor_map = dict()
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
        """Do nothing; lines should never be drawn in the Grid View.

        Args:
            draw_lines (bool): Whether or not lines should be drawn

        Returns:
            None
        """
        return
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
        x_l = x_l + HoneycombDnaPart.PAD_GRID_XL
        x_h = x_h + HoneycombDnaPart.PAD_GRID_XH
        y_h = y_h + HoneycombDnaPart.PAD_GRID_YL
        y_l = y_l + HoneycombDnaPart.PAD_GRID_YH
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, False, False, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, True, True, scale_factor=sf)
        # print(row_l, row_h, col_l, col_h)

        import sys
        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines
        GridPoint(0-half_dot_size, 0-half_dot_size, 1, self)
        GridPoint(0-half_dot_size, 0-half_dot_size, 29, self)
#        GridPoint(0, 0, 29, self)
        for i in range(row_l, row_h):
            for j in range(col_l, col_h+1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
#                sys.stdout.write('%s,%s ' % (x,y))
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
                stroke_weight = 0.25
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)
                GridPoint(x, -y, 1, self)
                self.point_coordinates[(-i, j)] = (x, -y)

                # TODO[NF]:  Remove me
                font = QFont('Arial')
                path.addText(x-10, -y+5, font, "%s,%s" % (j, -i))

                pt.setPen(getPenObj(Qt.blue, stroke_weight))
                points.append(pt)

                # Handle neighbor mapping logic
                self.point_map[(-i,j)] = pt

                # This is reversed since the Y is mirrored
                if not HoneycombDnaPart.isEvenParity(i, j):
                    self.neighbor_map[(-i,j)] = [
                        (-i, j-1),
                        (-i, j+1),
                        (-i-1, j)
                    ]
                    self.point_map.setdefault((-i, j-1))
                    self.point_map.setdefault((-i, j+1))
                    self.point_map.setdefault((-i-1, j))
                else:
                    self.neighbor_map[(-i,j)] = [
                        (-i, j-1),
                        (-i, j+1),
                        (-i+1, j)
                    ]
                    self.point_map.setdefault((-i, j-1))
                    self.point_map.setdefault((-i, j+1))
                    self.point_map.setdefault((-i+1, j))

            is_pen_down = False

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
        for key, value in self.neighbor_map.items():
            print(key, value)
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

    def find_closest_point(self, position):
        """Find the closest point to a given position on the grid
        Args:
            position ():

        Returns:

        """
        from math import sqrt
        minimum = float('inf')
        best = None
        for coordinates, coordiante_position in self.point_coordinates.items():
            distance = sqrt(
                    (coordiante_position[0]-position[0])**2 +
                    (coordiante_position[1]-position[1])**2)
            if distance < minimum:
                minimum = distance
                best = coordinates
            if minimum < _RADIUS:
#                logger.debug('The closest point to %s,%s is %s,%s' % (position, best))
                return best
#        logger.debug('The closest point to %s,%s is %s,%s' % (position, best))
        return best

    def shortest_path(self, start, end):
        """Return a path of coordinates that traverses from start to end.

        Does a breadth-first search.  This could be further improved to do an A*
        search.

        Args:
            start (tuple): The i-j coordinates corresponding to the start point
            end (tuple):  The i-j coordinates corresponding to the end point

        Returns:
            A list of coordinates corresponding to a shortest path from start to
            end.  This list omits the starting point as it's assumed that the
            start point has already been clicked.
        """
        start_coordinates = self.find_closest_point(start)
        end_coordinates = self.find_closest_point(end)

        print('Finding shortest path from %s to %s...' % (str(start), str(end)))
#        assert isinstance(start, tuple) and len(start) is 2
#        assert isinstance(end, tuple) and len(end) is 2

        if self.point_map.get(start_coordinates) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              start_coordinates)
        elif self.point_map.get(end_coordinates) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              end_coordinates)

        parents = dict()
        parents[start_coordinates] = None
        queue = Queue()
        queue.put(start_coordinates)

        while queue:
            current_location = queue.get()

            if current_location == end_coordinates:
                reversed_path = []
                while current_location is not start_coordinates:
                    reversed_path.append(current_location)
                    current_location = parents[current_location]
                reversed_path.append(start_coordinates)
                return [node for node in reversed(reversed_path)]
            else:
                neighbors = self.neighbor_map.get(current_location, [])
                for neighbor in neighbors:
                    if neighbor not in parents:
                        parents[neighbor] = current_location
                        queue.put(neighbor)

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
        return
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
        part_item.createToolHoverEnter(tool, event)

    def createToolHoverMoveEvent(self, tool, part_item, event):
        part_item.createToolHoverMove(tool, event)


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
