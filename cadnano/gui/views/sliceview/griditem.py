from queue import Queue

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem

from cadnano.cnenum import GridType
from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.gui.palette import getBrushObj, getNoPen, getPenObj

from . import slicestyles as styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_ZVALUE = styles.ZSLICEHELIX + 1
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.


class GridItem(QGraphicsPathItem):
    def __init__(self, part_item, grid_type):
        """Summary

        neighbor_map (dict):  a mapping of i, j row-column coordinates to a
        list of i, j row-column coordinates of neighbors to facilitate a BFS

        virtual_helices (set):  a set of tuples corresponding to virtual
        helices that exist on the Grid

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
        self.point_coordinates = dict()
        self.neighbor_map = dict()
        self.virtual_helices = set()
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
            self.create_honeycomb(part_item, radius, bounds)
        elif self.grid_type == GridType.SQUARE:
            self.create_square(part_item, radius, bounds)
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

    def set_drawlines(self, draw_lines):
        # TODO[NF]:  Docstring
        return

    def create_honeycomb(self, part_item, radius, bounds):
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

        redo_neighbors = (row_l, col_l, row_h, col_h) != self.previous_grid_bounds or self.previous_grid_type != self.grid_type
        self.previous_grid_type = self.grid_type

        if redo_neighbors:
            self.point_coordinates = dict()
            self.neighbor_map = dict()

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines
        for i in range(row_l, row_h):
            for j in range(col_l, col_h+1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
                # sys.stdout.write('%s,%s ' % (x,y))
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
                stroke_weight = styles.EMPTY_HELIX_STROKE_WIDTH
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)

                pt.setPen(getPenObj(Qt.blue, stroke_weight))
                points.append(pt)

                if redo_neighbors:
                    self.point_coordinates[(-i, j)] = (x, -y)

                    # This is reversed since the Y is mirrored
                    if not HoneycombDnaPart.isEvenParity(i, j):
                        self.neighbor_map[(-i, j)] = [
                            (-i, j-1),
                            (-i, j+1),
                            (-i-1, j)
                        ]
                    else:
                        self.neighbor_map[(-i, j)] = [
                            (-i, j-1),
                            (-i, j+1),
                            (-i+1, j)
                        ]
                    self.previous_grid_bounds = (row_l, col_l, row_h, col_h)

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

    def create_square(self, part_item, radius, bounds):
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

        redo_neighbors = (row_l, col_l, row_h, col_h) != self.previous_grid_bounds or self.previous_grid_type != self.grid_type
        self.previous_grid_type = self.grid_type

        if redo_neighbors:
            self.point_coordinates = dict()
            self.neighbor_map = dict()

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
                stroke_weight = styles.EMPTY_HELIX_STROKE_WIDTH
                pt.setPen(getPenObj(Qt.blue, stroke_weight))
                points.append(pt)

                if redo_neighbors:
                    self.point_coordinates[(-i, j)] = (x, -y)

                    self.neighbor_map[(-i, j)] = [
                        (-i, j+1),
                        (-i, j-1),
                        (-i-1, j),
                        (-i+1, j)
                    ]

                    self.previous_grid_bounds = (row_l, col_l, row_h, col_h)

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
        for coordinates, coordiante_position in self.point_coordinates.items():
            distance = (coordiante_position[0]-position[0])**2 + (coordiante_position[1]-position[1])**2
            if distance < _RADIUS**2:
                # logger.debug('The closest point to %s,%s is %s,%s' % (position, best))
                return coordinates

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
        assert isinstance(start, tuple) and len(start) is 2, "start is '%s'" % str(start)
        assert isinstance(end, tuple) and len(end) is 2, "end is '%s'" % str(end)

        start_coordinates = self.find_closest_point(start)
        end_coordinates = self.find_closest_point(end)

        if start_coordinates is None or end_coordinates is None:
            # TODO[NF]:  Change to logger
            print('Could not find path from %s to %s' % (str(start), str(end)))
            return []

            # TODO[NF]:  Change to logger
        print('Finding shortest path from %s to %s...' % (str(start), str(end)))

        if self.neighbor_map.get(start_coordinates) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              start_coordinates)
        elif self.neighbor_map.get(end_coordinates) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              end_coordinates)

        parents = dict()
        parents[start_coordinates] = None
        queue = Queue()
        queue.put(start_coordinates)

        while not queue.empty():
            try:
                current_location = queue.get(block=False)
            except Queue.Empty:
                print('Could not find path from %s to %s' % (str(start), str(end)))
                return []

            if current_location == end_coordinates:
                reversed_path = []
                while current_location is not start_coordinates:
                    reversed_path.append(current_location)
                    current_location = parents[current_location]
                return [node for node in reversed(reversed_path)]
            else:
                neighbors = self.neighbor_map.get(current_location, [])
                for neighbor in neighbors:
                    if neighbor not in parents and neighbor not in self.virtual_helices:
                        parents[neighbor] = current_location
                        queue.put(neighbor)
        print('Could not find path from %s to %s' % (str(start), str(end)))
        return []

    def added_virtual_helix(self, location):
        """
        Update the internal set of virtual helices to include the
        virtualhelix that lives at `location`.

        Args:
            location (tuple):  The location that a VH is being added to

        Returns: None
        """
        assert isinstance(location, tuple) and len(location) is 2
        self.virtual_helices.add(location)

    def removed_virtual_helix(self, location):
        """
        Update the internal set of virtual helices to no longer include the
        virtualhelix that lives at `location`.

        Args:
            location (tuple):  The location that a VH is being removed from

        Returns: None
        """
        assert isinstance(location, tuple) and len(location) is 2
        self.virtual_helices.remove(location)


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
        # self.setBrush(getBrushObj(styles.DEFAULT_GRID_DOT_COLOR))
        self.setPen(getPenObj(styles.DEFAULT_GRID_DOT_COLOR, styles.EMPTY_HELIX_STROKE_WIDTH))
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
