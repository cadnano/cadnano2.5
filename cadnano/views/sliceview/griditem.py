# -*- coding: utf-8 -*-
from typing import (
    Tuple,
    Optional
)

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import (
    QFont,
    QPainterPath
)
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent
)

from cadnano.proxies.cnenum import (
    GridEnum,
    EnumType
)
from cadnano.fileio.lattice import (
    HoneycombDnaPart,
    SquareDnaPart
)
from cadnano.gui.palette import (
    getBrushObj,
    getNoBrush,
    getNoPen,
    getPenObj
)
from cadnano.part.nucleicacidpart import DEFAULT_RADIUS
from cadnano.views.sliceview import slicestyles as styles
from cadnano.views.sliceview.tools import (
    SelectSliceToolT,
    CreateSliceToolT
)
from cadnano.views.sliceview import SliceNucleicAcidPartItemT
from cadnano.cntypes import (
    RectT
)

_RADIUS = styles.SLICE_HELIX_RADIUS
_ZVALUE = styles.ZSLICEHELIX + 1
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.


class GridItem(QGraphicsRectItem):
    def __init__(self,  part_item: SliceNucleicAcidPartItemT,
                        grid_type: EnumType):
        """previous_grid_bounds (tuple):  a tuple corresponding to the bounds of
        the grid.

        Args:
            part_item: Description
            grid_type: Description
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

    def destroyItem(self):
        print("destroying sliceView GridItem")
        scene = self.scene()
        for point in self.points:
            point.destroyItem()
        self.points = None
        scene.removeItem(self)
    # end def

    def updateGrid(self):
        """Recreates the grid according to the latest part_item outline rect.
        """
        part_item = self.part_item
        part = part_item.part()
        radius = part.radius()
        self.bounds = part_item.bounds()
        self.removePoints()

        self.setRect(self.part_item.outline.rect())
        if self.grid_type == GridEnum.HONEYCOMB:
            self.createHoneycombGrid(part_item, radius, self.bounds)
        elif self.grid_type == GridEnum.SQUARE:
            self.createSquareGrid(part_item, radius, self.bounds)
        else:
            self._path.setPath(QPainterPath())
    # end def

    def setGridType(self, grid_type: EnumType):
        """Sets the grid type. See cadnano.cnenum.GridEnum.

        Args:
            grid_type: NONE, HONEYCOMB, or SQUARE
        """
        self.grid_type = grid_type
        self.updateGrid()
    # end def

    def createHoneycombGrid(self, part_item: SliceNucleicAcidPartItemT,
                                radius: float,
                                bounds: RectT):
        """Instantiate an area of griditems arranged on a honeycomb lattice.

        Args:
            part_item: Description
            radius: Description
            bounds: Description
        """
        doLattice = HoneycombDnaPart.latticeCoordToModelXY
        doPosition = HoneycombDnaPart.positionModelToLatticeCoord
        isEven = HoneycombDnaPart.isEvenParity
        x_l, x_h, y_l, y_h = bounds
        x_l = x_l + HoneycombDnaPart.PAD_GRID_XL
        x_h = x_h + HoneycombDnaPart.PAD_GRID_XH
        y_h = y_h + HoneycombDnaPart.PAD_GRID_YL
        y_l = y_l + HoneycombDnaPart.PAD_GRID_YH
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, scale_factor=sf)

        redo_neighbors = (row_l, col_l, row_h, col_h) != self.previous_grid_bounds or\
            self.previous_grid_type != self.grid_type
        self.previous_grid_type = self.grid_type

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines

        if redo_neighbors:
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
                    font = QFont(styles.THE_FONT, 6)
                    path.addText(x - 5, -y + 4, font, "%s,%s" % (-row, column))

                pt.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
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
    # end def

    def createSquareGrid(self, part_item: SliceNucleicAcidPartItemT,
                            radius: float,
                            bounds: RectT):
        """Instantiate an area of griditems arranged on a square lattice.

        Args:
            part_item: Description
            radius: Description
            bounds: Description
        """
        doLattice = SquareDnaPart.latticeCoordToModelXY
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
                    font = QFont(styles.THE_FONT)
                    path.addText(x - 10, -y + 5, font, "%s,%s" % (-row, column))

                pt.setPen(getPenObj(styles.GRAY_STROKE, styles.EMPTY_HELIX_STROKE_WIDTH))

                # if x == 0 and y == 0:
                #     pt.setBrush(getBrushObj(Qt.gray))

                points.append(pt)
                self.points_dict[(-row, column)] = pt

                if redo_neighbors:
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

    def showCreateHint(self, coord: Tuple[int, int],
                            next_idnums: Tuple[int, int] = (0, 1),
                            show_hint: bool = True,
                            color: str = None) -> Optional[bool]:
        point_item = self.points_dict.get(coord)
        if point_item is None:
            return

        if not show_hint:
            point_item.showCreateHint(show_hint=False)

        if point_item:
            row, column = coord
            if self.grid_type is GridEnum.HONEYCOMB:
                parity = 0 if HoneycombDnaPart.isEvenParity(row=row, column=column) else 1
            elif self.grid_type is GridEnum.SQUARE:
                parity = 0 if SquareDnaPart.isEvenParity(row=row, column=column) else 1
            else:
                return
            id_num = next_idnums[1] if parity else next_idnums[0]
            point_item.showCreateHint(id_num=id_num, show_hint=show_hint, color=color)
            return parity == 1
    # end def

    def setPath(self, path: QPainterPath):
        assert isinstance(path, QPainterPath)
        self._path = path
    # end def

    def path(self) -> QPainterPath:
        return self._path
    # end def

    def highlightGridPoint(self, row: int, column: int, on: bool = True):
        grid_point = self.points_dict.get((row, column))

        if grid_point:
            grid_point.highlightGridPoint(on)
# end class


class GridPoint(QGraphicsEllipseItem):
    def __init__(self,  x: float, y: float, diameter: float,
                        parent_grid: GridItem,
                        coord: Tuple[int, int] = None):
        """
        Args:
            x:
            y:
            diameter:
            parent_grid:
            coord: This is the row, column tuple
        """
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

    def destroyItem(self):
        self.grid = None
        self.click_area.destroyItem()
        self.click_area = None
        self.scene().removeItem(self)
    # end def

    def showCreateHint(self, id_num: int = 0,
                            show_hint: bool = True,
                            color: str = None):
        label = self._label
        if show_hint:
            label.setText("%d" % id_num)
            b_rect = label.boundingRect()
            posx = b_rect.width()/2
            posy = b_rect.height()/2
            label.setPos(_RADIUS-posx, _RADIUS-posy)
            self.setBrush(getBrushObj(color if color else styles.MULTI_VHI_HINT_COLOR, alpha=64))
        else:
            label.setText("")
            self.setBrush(getNoBrush())
            # label.setParentItem(None)
    # end def

    def coord(self) -> Tuple[int, int]:
        """Lattice coordinates, if available.

        Returns:
            of form::

                (lattice row, lattice column)
        """
        if self._coord:
            row, column = self._coord
            return row, column
    # end def

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen
            coordinates of the the event, and previous event.
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        app_window = self.grid.part_item.window()
        app_window.showFilterHints(False)
        app_window.showToolHints(False)

        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event: Description
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "HoverMoveEvent"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event: Description
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "HoverEnterEvent"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
    # end def

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event: Description
        """
        # Turn the outline of the GridItem off
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

    def selectToolMousePress(self,  tool: SelectSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        """
        Args:
            tool: Description
            part_item: Description
            event: Description
        """
        return self.grid.part_item.mousePressEvent(event)
    # end def

    def selectToolMouseMove(self,   tool: SelectSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        pass
    # end def

    def selectToolMouseRelease(self, tool: SelectSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        pass
    # end def

    def createToolMousePress(self,  tool: CreateSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        """Called by :meth:`mousePressEvent` when clicking on the grid

        Args:
            tool: The tool that is being used
            part_item:
            event: The event that the mouse click triggered
        """
        part_item = self.grid.part_item
        tool = part_item._getActiveTool()
        if tool.FILTER_NAME not in part_item.part().document().filter_set:
            app_window = part_item.window()
            app_window.showFilterHints(True, filter_name='virtual_helix')
            return
        part = part_item.part()
        part.setSelected(True)
        alt_event = GridEvent(self, self.offset)
        part_item.setLastHoveredItem(self)
        part_item.createToolMousePress(tool, event, alt_event)
    # end def

    def selectToolHoverEnterEvent(self, tool: SelectSliceToolT,
                                        part_item: SliceNucleicAcidPartItemT,
                                        event: QGraphicsSceneHoverEvent):
        part_item.selectToolHoverEnter(tool, event)
    # end def

    def selectToolHoverLeaveEvent(self, tool: SelectSliceToolT,
                                        part_item: SliceNucleicAcidPartItemT,
                                        event: QGraphicsSceneHoverEvent):
        part_item.selectToolHoverLeave(tool, event)
    # end def

    def highlightGridPoint(self, on: bool = True):
        if on:
            self.setPen(getPenObj(styles.BLUE_STROKE, 2))
        else:
            self.setPen(getPenObj(  styles.GRAY_STROKE,
                                    styles.EMPTY_HELIX_STROKE_WIDTH))
    # end def

    def createToolHoverMoveEvent(self,  tool: CreateSliceToolT,
                                        part_item: SliceNucleicAcidPartItemT,
                                        event: QGraphicsSceneHoverEvent):
        if self.grid.grid_type == GridEnum.HONEYCOMB:
            positionToLatticeCoord = HoneycombDnaPart.positionModelToLatticeCoord
        else:
            positionToLatticeCoord = SquareDnaPart.positionModelToLatticeCoord
        coordinates = positionToLatticeCoord(part_item.part().radius(),
                                             event.scenePos().x(),
                                             event.scenePos().y(),
                                             scale_factor=part_item.scale_factor)
        latticeCoordToXY = HoneycombDnaPart.latticeCoordToQtXY if self.grid.grid_type is GridEnum.HONEYCOMB \
                else SquareDnaPart.latticeCoordToQtXY
        coordinate_string = '(%s, %s)' % coordinates
        coordiate_scaled_pos = '(%s, %s)' % latticeCoordToXY(DEFAULT_RADIUS, coordinates[0], coordinates[1], part_item.scale_factor)
        coordiate_pos = '(%s, %s)' % latticeCoordToXY(DEFAULT_RADIUS, coordinates[0], coordinates[1])
        position_string = '(%s, %s)' % (event.scenePos().x(), event.scenePos().y())

        part_item.updateStatusBar('%s @ %s (%s) - %s' % (coordinate_string, coordiate_scaled_pos, coordiate_pos, position_string))
        part_item.createToolHoverMove(tool, event)
    # end def

    def createToolHoverLeaveEvent(self, tool: CreateSliceToolT,
                                        part_item: SliceNucleicAcidPartItemT,
                                        event: QGraphicsSceneHoverEvent):
        part_item.createToolHoverLeave(tool, event)
    # end def
# end class

class ClickArea(QGraphicsEllipseItem):
    """An extra ellipse with slightly expanded real estate for receiving user
    mouse events. Displays no pen or brush, and directly invokes parent's
    mouse events.
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, diameter: float, parent: GridPoint):
        """
        Args:
            diameter: defines the size of the clickarea.
            parent: the item.
        """
        nd = 2*self._RADIUS
        offset = -0.5*nd + diameter/2
        super(ClickArea, self).__init__(offset, offset, nd, nd, parent=parent)
        self.parent_obj = parent
        self.setAcceptHoverEvents(True)
        self.setPen(getNoPen())
    # end def

    def destroyItem(self):
        self.parent_obj = None
        self.scene().removeItem(self)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Triggered when hovering mouse is moved on the grid."""
        self.parent_obj.hoverMoveEvent(event)
    # end def

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Triggered when the mouse is pressed anywhere on the grid."""
        return self.parent_obj.mousePressEvent(event)
    # end def

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Triggered when the mouse is pressed anywhere on the grid."""
        return self.parent_obj.mouseMoveEvent(event)
    # end def

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Triggered when the mouse is released anywhere on the grid."""
        return self.parent_obj.mouseReleaseEvent(event)
    # end def
# end class

class GridEvent(object):
    """Instantiated by :meth:`selectToolMousePress` or
    :meth:`createToolMousePress`.

    Attributes:
        grid_pt (GridPoint): Description
        offset (QPointF): Description
    """
    def __init__(self, grid_pt: GridPoint, offset: float):
        """Summary

        Args:
            grid_pt: Description
            offset: Description
        """
        self.grid_pt = grid_pt
        self.offset = QPointF(offset, offset)
    # end def

    def scenePos(self) -> QPointF:
        """Scene position, with offset.

        Returns:
            Scene position, with offset.
        """
        return self.grid_pt.scenePos() + self.offset

    def pos(self) -> QPointF:
        """Local position, with offset.

        Returns:
            local position with offset
        """
        return self.grid_pt.pos() + self.offset
# end class
