
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath, QColor
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem

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
        print("RADIUS IS ORIGINALLY %s" % radius)
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

    def nearest_point_coordinates(self, mouse_x, mouse_y):
        """

        Args:
            mouse_x (float):
            mouse_y (float):

        Returns:
        """
#        print('X AND Y ARE NOW %s and %s' % (mouse_x, mouse_y))
        root3 = 1.732051
        sf = self.part_item.scale_factor
        part = self.part_item.part()
        radius = float(part.radius())

        scaled_x = mouse_x / (radius * sf * root3)
        odd_scaled_y = -mouse_y / (radius * sf * 3 + radius)
        even_scaled_y = -mouse_y / (radius * sf * 3)

        possible_x_values = [int(scaled_x), int(scaled_x+ 1)]
        possible_y_values = [int(odd_scaled_y), int(odd_scaled_y + 1),
                             int(even_scaled_y), int(even_scaled_y + 1)]
#        print('2NOW X AND Y ARE NOW %s and %s' % (x, y))
#        print('Possible x values: %s' % possible_x_values)
#        print('Possible y values: %s' % possible_y_values)
#        print('Radius is %s' % radius)
#        print('sf is %s' % sf)

        p = HoneycombDnaPart.positionToLatticeCoord(radius, mouse_x, mouse_y,
                                                    scale_factor=sf)
        row_low, col_low = HoneycombDnaPart.positionToLatticeCoordRound(radius,
                                                                        mouse_x,
                                                                        mouse_y,
                                                                        False,
                                                                        False,
                                                                        scale_factor=sf)
        row_high, col_high = HoneycombDnaPart.positionToLatticeCoordRound(radius,
                                                                          mouse_x,
                                                                          mouse_y,
                                                                          True,
                                                                          True,
                                                                          scale_factor=sf)
#        print("I SEE THAT row IS %s and column IS %s" % (p))
#        possible_centers = {
#            (possible_x_values[0], possible_y_values[0]),
#            (possible_x_values[0], possible_y_values[1]),
#            (possible_x_values[0], possible_y_values[2]),
#            (possible_x_values[0], possible_y_values[3]),
#            (possible_x_values[1], possible_y_values[0]),
#            (possible_x_values[1], possible_y_values[1]),
#            (possible_x_values[1], possible_y_values[2]),
#            (possible_x_values[1], possible_y_values[3])
#        }
        possible_centers = {
            (row_low, col_low),
            (row_low, col_high),
            (row_high, col_low),
            (row_high, col_high)
        }


#        if self.grid_type == GridType.HONEYCOMB:
#            possible_centers = {}
#
#            for grid_x in possible_x_values:
#                for grid_y in possible_y_values:
#                    possible_centers[(grid_x, grid_y)] =\
#                    HoneycombDnaPart.latticeCoordToPositionXY(radius, grid_x,
#                                                              grid_y,
#                                                          scale_factor=sf)
#        else:
#            raise NotImplementedError

#        print('NOW X AND Y ARE NOW %s and %s' % (x, y))


#        print(possible_centers)

        center_map = {}

        for center in possible_centers:
            center_x, center_y = center
            grid_x, grid_y = HoneycombDnaPart.latticeCoordToPositionXY(radius,
                                                                       center_x,
                                                                       center_y,
                                                                       scale_factor=sf)
            dx = abs(grid_x - center_x)
            dy = abs(grid_y - center_y)

            dx_squared = dx**2
            dy_squared = dy**2

            d_sum = dy_squared + dx_squared

            import math
            square_root_sum = math.sqrt(d_sum)

            center_map[(center_x, center_y)] = square_root_sum

        print(center_map)
        the_center = min(center_map, key=center_map.get)
        print("FINAL VALUE:  %s,%s" % the_center)
        print("The original thing thinks it's %s,%s" %
              HoneycombDnaPart.positionToLatticeCoord(radius, mouse_x,
                                                      mouse_y, sf))



#        for int_coordiantes, scene_pos in possible_centers.items():
#            scene_x, scene_y = scene_pos
#            print('X VALUES // scene:%s mouse:%s' %(scene_x, x))
#            dx = abs(scene_x - x)
##            print('dx is %s' % dx)
#            print('Y VALUES // scene:%s mouse:%s' %(scene_y, y))
#            dy = abs(scene_y - y)
##            print('dy is %s' % dy)
#            scaled_radius = self.dots[1]
#            if dx**2 + dy**2 <= scaled_radius**2:
#                print("FOUND: %s, %s" % int_coordiantes)
##            if (scene_x-x)**2 + (scene_y-y)**2 < radius**2:
#            else:
#                print('sum is %s, radius squared is %s' % (dx**2 + dy**2,
#                                                           scaled_radius**2))
#                print(part.radius)
#                print(part.radius())
#                print(radius)
#                print(radius**2)

#        import math
#        if x < 0:
#            rounded_x = math.floor(scaled_x)
#        elif x > 0:
#            rounded_x = math.ceil(scaled_x)
#        else:
#
#        rounded_x = math.floor(scaled_x) if x < 0 else math.ceil(scaled_x)
#
#        print('Scaled x is %s' % scaled_x)
#        print('Rounded x is %s' % rounded_x)
#        print('Odd scaled y is %s' % odd_scaled_y)
#        print('Even scaled y is %s' % even_scaled_y)





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
                pt.setPen(getPenObj(Qt.blue, stroke_weight))
                points.append(pt)

                # Handle neighbor mapping logic
                self.point_map[(i,j)] = pt
                sys.stdout.write('%s,%s (%s) ' % ((x, y, 'T' if HoneycombDnaPart.isEvenParity(i,j) else 'F')))
#               sys.stdout.write('%s,%s (%s) ' % ((i, j, 'T' if HoneycombDnaPart.isEvenParity(i,j) else 'F')))

                if HoneycombDnaPart.isEvenParity(i, j):
                    self.neighbor_map[(i,j)] = [
                        (i, j-1),
                        (i, j+1),
                        (i+1, j)
                    ]
                    self.point_map.setdefault((i, j-1))
                    self.point_map.setdefault((i, j+1))
                    self.point_map.setdefault((i+1, j))
                else:
                    self.neighbor_map[(i,j)] = [
                        (i, j-1),
                        (i, j+1),
                        (i-1, j)
                    ]
                    self.point_map.setdefault((i, j-1))
                    self.point_map.setdefault((i, j+1))
                    self.point_map.setdefault((i-1, j))

            sys.stdout.write('\n')
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
        print("Points size:  %s" % len(points))
        print("Point map: %s" % self.point_map)
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

    def shortest_path(self, start, end):
        """Return a path of coordinates that traverses from start to end.

        Does a breadth-first search.  This could be further improved to do an A*
        search.

        Args:
            start (tuple): The i-j coordinates corresponding to the start point
            end (tuple):  The i-j coordinates corresponding to the end point

        Returns:
            A list of coordinates corresponding to a shortest path from start to
            end
        """
        print(start)
        assert isinstance(start, tuple) and len(start) is 2
        assert isinstance(end, tuple) and len(end) is 2

        if self.point_map.get(start) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              start)
        elif self.point_map.get(end) is None:
            raise LookupError('Could not find a point corresponding to %s',
                              start)

        current_location = start

        neighbors = self.neighbor_map.get(current_location)
        queue = [neighbor for neighbor in neighbors]
        parents = dict()
        parents[start] = None

        while queue:
            current_location = queue.pop()

            if current_location == end:
                reversed_path = []
                while parents[current_location] is not None:
                    reversed_path.append(current_location)
                    current_location = parents[current_location]
                return reversed(reversed_path)
            else:
                neighbors = self.neighbor_map.get(current_location)
                for neighbor in neighbors:
                    if neighbor not in parents:
                        parents[neighbor] = current_location
                        queue.append(neighbor)


class ClickArea(QGraphicsEllipseItem):
    """Summary

    Attributes:
        parent_obj (TYPE): Description
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, diameter, parent):
#        print("NEW CLICKAREA")
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
#        print("HOVERMOVE")
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
            None
        """
        print("FIRST")
        if self.grid.allow_snap:
            part_item = self.grid.part_item
            tool = part_item._getActiveTool()
#            print(type(tool))
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
        # print("monkey")
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
        print("SECOND")
#        print('Coordinates:  %s:%s' % (event.scenePos().x(), event.scenePos().y()))
#        from cadnano.util import qtdb_trace
#        qtdb_trace()
        part = part_item.part()
        part.setSelected(True)
        # print("paws")
        alt_event = GridEvent(self, self.offset)
        part_item.createToolMousePress(tool, event, alt_event)

    def createToolHoverEnterEvent(self, tool, part_item, event):
        part_item.createToolHoverEnter(tool, event)

    def createToolHoverMoveEvent(self, tool, part_item, event):
#        print("HM")
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
