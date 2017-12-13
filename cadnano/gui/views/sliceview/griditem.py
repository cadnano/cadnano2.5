from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QFont, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsSimpleTextItem

from cadnano.cnenum import GridType
from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.gui.palette import getBrushObj, getNoBrush, getNoPen, getPenObj
from cadnano.gui.views.sliceview import slicestyles as styles


_RADIUS = styles.SLICE_HELIX_RADIUS
_ZVALUE = styles.ZSLICEHELIX + 1
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.


class GridItem(QGraphicsRectItem):
    def __init__(self, part_item, grid_type):
        """Summary

        previous_grid_bounds (tuple):  a tuple corresponding to the bounds of
        the grid.

        Args:
            part_item (TYPE): Description
            grid_type (TYPE): Description
        """
        super(GridItem, self).__init__(parent=part_item)
        self.setFlag(QGraphicsItem.ItemClipsChildrenToShape)

        self._path = None
        self.part_item = part_item
        self._path = QGraphicsPathItem(self)

        self.dots = (styles.DOT_SIZE, styles.DOT_SIZE / 2)
        # self.allow_snap = part_item.window().action_vhelix_snap.isChecked()
        self._draw_gridpoint_coordinates = False
        self.draw_lines = False
        self.points = []
        self.points_dict = dict()
        self.previous_grid_bounds = None
        self.bounds = None
        self.grid_type = None

        self.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))

        self.setGridType(grid_type)
        self.previous_grid_type = grid_type
    # end def

    def updateGrid(self):
        """Summary

        Returns:
            TYPE: Description
        """
        part_item = self.part_item
        part = part_item.part()
        radius = part.radius()
        self.bounds = part_item.bounds()
        self.removePoints()

        self.setRect(self.part_item.outline.rect())
        if self.grid_type == GridType.HONEYCOMB:
            self.createHoneycombGrid(part_item, radius, self.bounds)
        elif self.grid_type == GridType.SQUARE:
            self.createSquareGrid(part_item, radius, self.bounds)
        else:
            self._path.setPath(QPainterPath())
    # end def

    def setGridType(self, grid_type):
        """Sets the grid type. See cadnano.cnenum.GridType.

        Args:
            grid_type (GridType): NONE, HONEYCOMB, or SQUARE
        """
        self.grid_type = grid_type
        self.updateGrid()
    # end def

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
            for column in range(col_l, col_h+1):
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

                if self._draw_gridpoint_coordinates:
                    font = QFont('Arial')
                    path.addText(x - 10, -y + 5, font, "%s,%s" % (-row, column))

                pt.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
                    point_coordinates[(-row, column)] = (x, -y)

                    # This is reversed since the Y is mirrored
                    if not HoneycombDnaPart.isEvenParity(row, column):
                        neighbor_map[(-row, column)] = [
                            (-row-1, column),
                            (-row, column+1),
                            (-row, column-1)
                        ]
                    else:
                        neighbor_map[(-row, column)] = [
                            (-row+1, column),
                            (-row, column-1),
                            (-row, column+1)
                        ]
                    self.previous_grid_bounds = (row_l, col_l, row_h, col_h)

            is_pen_down = False

        if draw_lines:
            for column in range(col_l, col_h+1):
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
        self._path.setPath(path)

        if redo_neighbors:
            self.part_item.setNeighborMap(neighbor_map=neighbor_map)
            self.part_item.setPointMap(point_map=point_coordinates)
    # end def

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
        x_l = x_l + SquareDnaPart.PAD_GRID_XL
        x_h = x_h + SquareDnaPart.PAD_GRID_XH
        y_h = y_h + SquareDnaPart.PAD_GRID_YL
        y_l = y_l + SquareDnaPart.PAD_GRID_YH

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

                if self._draw_gridpoint_coordinates:
                    font = QFont('Arial')
                    path.addText(x - 10, -y + 5, font, "%s,%s" % (-row, column))

                pt.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
                    point_map[(-row, column)] = (x, -y)

                    neighbor_map[(-row, column)] = [
                        (-row, column+1),
                        (-row, column-1),
                        (-row-1, column),
                        (-row+1, column)
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
        self._path.setPath(path)

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
    # end def

    def showCreateHint(self, coord, next_idnums=(0, 1), show_hint=True):
        point_item = self.points_dict.get(coord)

        if show_hint is False:
            point_item.showCreateHint(show_hint=False)

        if point_item:
            row, column = coord
            if self.grid_type is GridType.HONEYCOMB:
                parity = 0 if HoneycombDnaPart.isOddParity(row=row, column=column) else 1
            elif self.grid_type is GridType.SQUARE:
                parity = 0 if SquareDnaPart.isEvenParity(row=row, column=column) else 1
            else:
                return
            id_num = next_idnums[1] if parity else next_idnums[0]
            point_item.showCreateHint(id_num=id_num, show_hint=show_hint)
            return parity == 1
    # end def

    def setPath(self, path):
        assert isinstance(path, QPainterPath)
        self._path = path
    # end def

    def path(self):
        return self._path
    # end def


class ClickArea(QGraphicsEllipseItem):
    """An extra ellipse with slightly expanded real estate for receiving user
    mouse events. Displays no pen or brush, and directly invokes parent's
    mouse events.

    Args:
        diameter (float): defines the size of the clickarea.
        parent (GridItem): the item.
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

    def hoverMoveEvent(self, event):
        """Triggered when hovering mouse is moved on the grid."""
        self.parent_obj.hoverMoveEvent(event)
    # end def

    def mousePressEvent(self, event):
        """Triggered when the mouse is pressed anywhere on the grid."""
        return self.parent_obj.mousePressEvent(event)
    # end def

    def mouseMoveEvent(self, event):
        """Triggered when the mouse is pressed anywhere on the grid."""
        return self.parent_obj.mouseMoveEvent(event)
    # end def

    def mouseReleaseEvent(self, event):
        """Triggered when the mouse is released anywhere on the grid."""
        return self.parent_obj.mouseReleaseEvent(event)
    # end def
# end class


class GridPoint(QGraphicsEllipseItem):
    __slots__ = 'grid', 'offset'

    def __init__(self, x, y, diameter, parent_grid, coord=None):
        super(GridPoint, self).__init__(0., 0., diameter, diameter, parent=parent_grid)
        self.offset = diameter / 2
        self.grid = parent_grid
        self._coord = coord
        self._label = label = QGraphicsSimpleTextItem("", self)
        label.setFont(styles.SLICE_NUM_FONT)
        label.setZValue(styles.ZSLICEHELIX)
        label.setBrush(getBrushObj(styles.SLICE_TEXT_COLOR, alpha=64))
        b_rect = label.boundingRect()
        posx = b_rect.width()/2
        posy = b_rect.height()/2
        label.setPos(_RADIUS-posx, _RADIUS-posy)

        self.click_area = ClickArea(diameter, parent=self)

        self.setPos(x, y)
        self.setZValue(_ZVALUE)
        self.setAcceptHoverEvents(True)
    # end def

    def showCreateHint(self, id_num=0, show_hint=True):
        label = self._label
        if show_hint:
            label.setText("%d" % id_num)
            b_rect = label.boundingRect()
            posx = b_rect.width()/2
            posy = b_rect.height()/2
            label.setPos(_RADIUS-posx, _RADIUS-posy)
            self.setBrush(getBrushObj(styles.MULTI_VHI_HINT_COLOR, alpha=64))
        else:
            label.setText("")
            self.setBrush(getNoBrush())
            # label.setParentItem(None)
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
    # end def

    def mousePressEvent(self, event):
        """Handler for user mouse press.

        Args:
            event (QGraphicsSceneMouseEvent): Contains item, scene, and screen
            coordinates of the the event, and previous event.

        Returns:
            None
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def mouseMoveEvent(self, event):
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def mouseReleaseEvent(self, event):
        controller = self.grid.part_item.document().controller()
        controller.showFilterHints(False)
        controller.showToolHints(False)

        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
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
    # end def

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
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        # Turn the outline of the GridItem off
        self.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))
        self.showCreateHint(show_hint=False)

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
        # return QGraphicsEllipseItem.mousePressEvent(self, event)
        return self.grid.part_item.mousePressEvent(event)
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        controller = part_item.document().controller()

        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            controller.showFilterHints(True, filter_name='virtual_helix')
            # return
        else:  # the filter is correct, tool is wrong
            controller.showToolHints(True, tool_name='create')
        part = part_item.part()
        part.setSelected(True)
        alt_event = GridEvent(self, self.offset)
        tool.selectOrSnap(part_item, alt_event, event)
    # end def

    def selectToolMouseMove(self, tool, part_item, event):
        pass
        # return QGraphicsEllipseItem.mouseReleaseEvent(self, event)
    # end def

    def selectToolMouseRelease(self, tool, part_item, event):
        pass
        # return QGraphicsEllipseItem.mouseReleaseEvent(self, event)
    # end def

    def createToolMousePress(self, tool, part_item, event):
        """Called by mousePressEvent when clicking on the grid

        Args:
            tool (CreateSliceTool): The tool that is being used
            part_item (TYPE):
            event (QGraphicsSceneMouseEvent): The event that the mouse click triggered
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            controller = part_item.document().controller()
            controller.showFilterHints(True, filter_name='virtual_helix')
            return
        part = part_item.part()
        part.setSelected(True)
        alt_event = GridEvent(self, self.offset)
        part_item.setLastHoveredItem(self)
        part_item.createToolMousePress(tool, event, alt_event)
    # end def

    def createToolHoverEnterEvent(self, tool, part_item, event):
        self.setPen(getPenObj(styles.BLUE_STROKE, 2))
        part_item.setLastHoveredItem(self)
    # end def

    def createToolHoverMoveEvent(self, tool, part_item, event):
        part_item.createToolHoverMove(tool, event)
    # end def

    def createToolHoverLeaveEvent(self, tool, part_item, event):
        part_item.createToolHoverLeave(tool, event)
    # end def
# end class


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
    # end def

    def scenePos(self):
        """Scene position, with offset.

        Returns:
            QPointF: Description
        """
        return self.grid_pt.scenePos() + self.offset
    # end def

    def pos(self):
        """Local position, with offset.

        Returns:
            QPointF: Description
        """
        return self.grid_pt.pos() + self.offset
    # end def
# end class
