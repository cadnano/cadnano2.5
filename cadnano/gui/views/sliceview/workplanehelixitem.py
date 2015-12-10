import math
from collections import defaultdict

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtWidgets  import QGraphicsItem
from PyQt5.QtWidgets  import QGraphicsEllipseItem

from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj

from . import slicestyles as styles

class WorkplaneHelixItem(QGraphicsEllipseItem):
    """docstring for WorkplaneHelixItem"""
    # set up default, hover, and active drawing styles
    _RADIUS = styles.SLICE_HELIX_RADIUS
    temp = styles.SLICE_HELIX_STROKE_WIDTH
    _DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
    temp = (styles.SLICE_HELIX_HILIGHT_WIDTH - temp)/2
    _HOVER_RECT = _DEFAULT_RECT.adjusted(-temp, -temp, temp, temp)
    _Z_DEFAULT = styles.ZSLICEHELIX
    _Z_HOVERED = _Z_DEFAULT + 1
    temp /= 2
    _ADJUSTMENT_PLUS = (temp, temp)
    _ADJUSTMENT_MINUS = (-temp, -temp)

    def __init__(self, x, y, scale_factor, workplane_item):
        """
        x, y is a coordinate in Lattice terms
        scale_factor is the visual scaling factor for the slice view
        workplane_item is the parent WorkplaneItem
        """
        super(WorkplaneHelixItem, self).__init__(parent=workplane_item)

        self.hide()
        self._is_hovered = False
        self.setAcceptHoverEvents(True)

        self.updateAppearance()

        self.setNotHovered()

        self.setPos(x*scale_factor, y*scale_factor)
        self._coord = (x, y)
        self.show()
    # end def

    def updateAppearance(self):
        # part-specific styles
        part_color_hex = self.part().getProperty('color')
        self._HOVER_BRUSH = getBrushObj(styles.BLUE_FILL)
        self._HOVER_PEN = getPenObj(styles.BLUE_STROKE, styles.SLICE_HELIX_HILIGHT_WIDTH)

        self._DEFAULT_PEN = getPenObj(part_color_hex, styles.SLICE_HELIX_STROKE_WIDTH)
        self._DEFAULT_BRUSH = getBrushObj(part_color_hex, alpha=4)

        self.setBrush(self._DEFAULT_BRUSH)
        self.setPen(self._DEFAULT_PEN)
        self.setRect(self._DEFAULT_RECT)
    # end def

    def workplaneItem(self):
        return self.parent()
    # end def

    def partItem(self):
        return self.workplaneItem().partItem()
    # end def

    def part(self):
        return self.workplaneItem().part()
    # end def

    def translateVH(self, delta):
        """
        used to update a child virtual helix position on a hover event
        delta is a tuple of x and y values to translate

        positive delta happens when hover happens
        negative delta when something unhovers
        """
        temp = self.virtualHelixItem()

        # xor the check to translate,
        # convert to a QRectF adjustment if necessary
        check = (delta > 0) ^ self._is_hovered
        if temp and check:
            pass
            # temp.translate(*delta)
    # end def

    def setHovered(self):
        # self.setFlag(QGraphicsItem.ItemHasNoContents, False)
        self.setBrush(self._HOVER_BRUSH)
        self.setPen(self._HOVER_PEN)
        self.update(self.boundingRect())
        # self.translateVH(self._ADJUSTMENT_PLUS)
        self._is_hovered = True
        self.setZValue(self._Z_HOVERED)
        self.setRect(self._HOVER_RECT)

        self.partItem().updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from default
        to the hover colors if necessary.
        """
        self.setHovered()
    # end def

    def setNotHovered(self):
        """
        """
        # drawMe = False if self.virtualHelixItem() else True
        # self.setFlag(QGraphicsItem.ItemHasNoContents, drawMe)
        self.setBrush(self._DEFAULT_BRUSH)
        self.setPen(self._DEFAULT_PEN)
        self.update(self.boundingRect())
        # self.translateVH(self._ADJUSTMENT_MINUS)
        self._is_hovered = False
        self.setZValue(self._Z_DEFAULT)
        self.setRect(self._DEFAULT_RECT)

        self.partItem().updateStatusBar("")
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from hover
        to the default colors if necessary.
        """
        self.setNotHovered()
    # end def

    def mousePressEvent(self, event):
        action = self.decideAction(event.modifiers())
        action(self)
        self.dragSessionAction = action
    # end def

    def mouseMoveEvent(self, event):
        part_item = self._part_item
        pos_in_parent = part_item.mapFromItem(self, QPointF(event.pos()))
        # Qt doesn't have any way to ask for graphicsitem(s) at a
        # particular position but it *can* do intersections, so we
        # just use those instead
        part_item.probe.setPos(pos_in_parent)
        for ci in part_item.probe.collidingItems():
            if isinstance(ci, EmptyHelixItem):
                self.dragSessionAction(ci)
    # end def

    def getPartPosition(self):
        """return position within part item
        """
        part = self.part()
        workplane_item = self.workplaneItem()
        wp_pos = workplane_item.pos()
        x, y = self._coord
        px = wp_pos.x() + x
        py = wp_pos.y() + y
        return (px, py)
    # end def

    def decideAction(self, modifiers):
        """ On mouse press, an action (add scaffold at the active slice, add
        segment at the active slice, or create virtualhelix if missing) is
        decided upon and will be applied to all other slices happened across by
        mouseMoveEvent. The action is returned from this method in the form of a
        callable function."""
        part = self.part()
        if part.hasVirtualHelixAt(self.getPartPosition()):
            return

        vh = self.virtualHelix()
        part = self.part()

        if vh is None:
            return EmptyHelixItem.addVHIfMissing

        idx = part.activeBaseIndex()
        scafSSet, stapSSet = vh.getStrandSets()
        if modifiers & Qt.ShiftModifier:
            if not stapSSet.hasStrandAt(idx - 1, idx + 1):
                return EmptyHelixItem.addStapAtActiveSliceIfMissing
            else:
                return EmptyHelixItem.nop

        if not scafSSet.hasStrandAt(idx - 1, idx + 1):
            return EmptyHelixItem.addScafAtActiveSliceIfMissing
        return EmptyHelixItem.nop
    # end def

    def nop(self):
        self._part_item.updateStatusBar("(%d, %d)" % self._coord)

    def addStapAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()

        if vh is None:
            return

        idx = part.activeBaseIndex()
        start_idx = max(0, idx - 1)
        end_idx = min(idx + 1, part.maxBaseIdx())
        vh.stapleStrandSet().createStrand(start_idx, end_idx)

        x, y = self._coord
        tup = (part.getName(), x, y)
        self.partItem().updateStatusBar("%s:(%d, %d)" % tup)
    # end def

    def addVHIfMissing(self):
        vh = self.virtualHelix()
        coord = self._coord
        part = self.part()

        if vh is not None:
            return
        u_s = part.undoStack()
        u_s.beginMacro("Slice Click")
        part.createVirtualHelix(*coord)
        # vh.scaffoldStrandSet().createStrand(start_idx, end_idx)
        u_s.endMacro()

        x, y = self._coord
        tup = (part.getName(), x, y)
        self._part_item.updateStatusBar("%s:(%d, %d)" % tup)
    # end def
# end def

