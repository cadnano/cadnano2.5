from math import sqrt, atan2, degrees, pi

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QFont, QPen, QPainterPath, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtWidgets import QUndoCommand, QStyle

from cadnano import util
from cadnano.gui.palette import getPenObj, getBrushObj
from . import pathstyles as styles


HOVER_WIDTH = H_W = 20
GAP = 0 # gap between inner and outer strands

_ROTATELINE_WIDTH = 1
_ROTATE_PEN = getPenObj(styles.BLUE_STROKE, _ROTATELINE_WIDTH)
_ROTATE_BRUSH = getBrushObj('#8099ccff')
_SELECT_STROKE_WIDTH = 10

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)

_RADIUS = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_RECT = QRectF(0, 0, 2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,\
        2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_DEF_BRUSH = getBrushObj(styles.GRAY_FILL)
_DEF_PEN = getPenObj(styles.GRAY_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_HOV_BRUSH = getBrushObj(styles.BLUE_FILL)
_HOV_PEN = getPenObj(styles.BLUE_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_FONT = styles.VIRTUALHELIXHANDLEITEM_FONT


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    _filter_name = "virtual_helix"

    def __init__(self, virtual_helix, nucleicacid_part_item, viewroot):
        super(VirtualHelixHandleItem, self).__init__(nucleicacid_part_item)
        self._virtual_helix = virtual_helix
        self._nucleicacid_part_item = nucleicacid_part_item
        self._model_part = nucleicacid_part_item.part()
        self._viewroot = viewroot
        self._being_hovered_over = False
        self.setAcceptHoverEvents(True)
        self.refreshColor()
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setSelectedColor(False)
        self.setZValue(styles.ZPATHHELIX)
        self.setRect(_RECT)
        self.setTransformOriginPoint(self.boundingRect().center())

        # rotation 
        self._rect = QRectF()
        self._hover_rect = QRectF()
        self._outer_line = RotateLine(self._rect, self)
        self._hover_region = RotateHoverRegion(self._hover_rect, self)
        self.updateRects()
        self.show()
    # end def

    def rotateWithCenterOrigin(self, angle):
        self.setRotation(angle)
    # end def

    def part(self):
        return self._model_part
    # end def

    def radius(self):
        return self._radius
    # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def


    def updateRects(self):
        diameter = self.boundingRect().width()/2 # round(dna_length * pi / 100,2)
        self._radius = _RADIUS
        diameter = _RADIUS * 2
        self._rect = QRectF(0, 0, diameter, diameter)
        self._outer_line.updateRect(QRectF(-GAP, -GAP, diameter+GAP*2, diameter+GAP*2))
        # self._inner_line.updateRect(QRectF(GAP/2, GAP/2, diameter-GAP, diameter-GAP))
        # self._hover_rect = self._rect.adjusted(-H_W, -H_W, H_W, H_W)
        self._hover_region.updateRect(self._rect)
    # end def

    def refreshColor(self):
        part_color = self._model_part.getProperty('color')
        self._USE_PEN = getPenObj(part_color, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
        self._USE_BRUSH = getBrushObj(part_color, alpha=128)
        self.setPen(self._USE_PEN)
        self.setBrush(self._USE_BRUSH)
        self.update(self.boundingRect())
    # end def

    def setSelectedColor(self, value):
        if self.number() >= 0:
            if value == True:
                self.setBrush(_HOV_BRUSH)
                self.setPen(_HOV_PEN)
            else:
                self.setBrush(self._USE_BRUSH)
                self.setPen(self._USE_PEN)
        else:
            self.setBrush(_DEF_BRUSH)
            self.setPen(_DEF_PEN)
        self.update(self.boundingRect())
    # end def

    def virtualHelix(self):
        return self._virtual_helix

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
    # end def

    def remove(self):
        scene = self.scene()
        scene.removeItem(self._label)
        scene.removeItem(self)
        self._label = None
    # end def

    def someVHChangedItsNumber(self, r, c):
        # If it was our VH, we need to update the number we
        # are displaying!
        if (r,c) == self.vhelix.coord():
            self.setNumber()
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtual_helix.number())
        label.setFont(_FONT)
        label.setZValue(styles.ZPATHHELIX)
        label.setParentItem(self)
        return label
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtual_helix
        num = vh.number()
        label = self._label
        radius = _RADIUS

        if num is not None:
            label.setText("%d" % num)
        else:
            return
        y_val = radius / 3
        if num < 10:
            label.setPos(radius / 1.5, y_val)
        elif num < 100:
            label.setPos(radius / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        bRect = label.boundingRect()
        posx = bRect.width()/2
        posy = bRect.height()/2
        label.setPos(radius-posx, radius-posy)
    # end def

    def number(self):
        """docstring for number"""
        return self._virtual_helix.number()

    def partItem(self):
        return self._nucleicacid_part_item
    # end def

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHandle brush and pen from default
        to the hover colors if necessary.
        """
        if not self.isSelected():
            if self.number() >= 0:
                if self.isSelected():
                    self.setBrush(_HOV_BRUSH)
                else:
                    self.setBrush(self._USE_BRUSH)
            else:
                self.setBrush(_DEF_BRUSH)
            self.setPen(_HOV_PEN)
            self.update(self.boundingRect())
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHanle brush and pen from hover
        to the default colors if necessary.
        """
        if not self.isSelected():
            self.setSelectedColor(False)
            self.update(self.boundingRect())
    # end def

    def mousePressEvent(self, event):
        """
        All mousePressEvents are passed to the group if it's in a group
        """
        selection_group = self.group()
        if selection_group is not None:
            selection_group.mousePressEvent(event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group
        """
        selection_group = self.group()
        if selection_group is not None:
            selection_group.mousePressEvent(event)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the nucleicacid_part_item
        """

        # map the position
        self.tempReparent(pos=pos)
        self.setSelectedColor(False)
        assert(self.group() is None)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        nucleicacid_part_item = self._nucleicacid_part_item
        if pos is None:
            pos = self.scenePos()
        self.setParentItem(nucleicacid_part_item)
        temp_point = nucleicacid_part_item.mapFromScene(pos)
        self.setPos(temp_point)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            viewroot = self._viewroot
            current_filter_dict = viewroot.selectionFilterDict()
            selection_group = viewroot.vhiHandleSelectionGroup()

            # only add if the selection_group is not locked out
            if value == True and self._filter_name in current_filter_dict:
                if self.group() != selection_group:
                    selection_group.pendToAdd(self)
                    selection_group.setSelectionLock(selection_group)
                    self.setSelectedColor(True)
                    return True
                else:
                    return False
            # end if
            elif value == True:
                # don't select
                return False
            else:
                # Deselect
                selection_group.pendToRemove(self)
                self.setSelectedColor(False)
                return False
            # end else
        # end if
        return QGraphicsEllipseItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        pass
        self.restoreParent()
    # end def

    def modelSelect(self, document):
        pass
        self.setSelected(True)
    # end def
# end class



class RotateSelectionItem(QGraphicsPathItem):
    def __init__(self, startAngle, spanAngle, parent=None):
        # setup DNA line
        super(QGraphicsPathItem, self).__init__(parent)
        self._parent = parent
        self.updateAngle(startAngle, spanAngle)
        self.updateColor(parent.modelColor())
    # end def

    def updateAngle(self, startAngle, spanAngle):
        self._startAngle = startAngle
        self._spanAngle = spanAngle
        path = QPainterPath()
        path.arcMoveTo(self._parent._rect, startAngle)
        path.arcTo(self._parent._rect, startAngle, spanAngle)
        self.setPath(path)
    # end def

    def updateColor(self, color):
        self.setPen(getPenObj(color,_SELECT_STROKE_WIDTH, alpha=128, capstyle=Qt.FlatCap))
    # end def
# end class

class RotateHoverRegion(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        # setup DNA line
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(_HOVER_BRUSH)
        self.setAcceptHoverEvents(True)

        # hover marker
        self._hoverLine = QGraphicsLineItem(-_SELECT_STROKE_WIDTH/2, 0, _SELECT_STROKE_WIDTH/2, 0, self)
        self._hoverLine.setPen(getPenObj('#00cc', 0.5))
        self._hoverLine.hide()

        self._startPos = None
        self._startAngle = None  # save selection start
        self._clockwise = None
        self.dummy = RotateSelectionItem(0, 0, parent)
        self.dummy.hide()

    def updateRect(self, rect):
        self.setRect(rect)

    def hoverEnterEvent(self, event):
        self.updateHoverLine(event)
        self._hoverLine.show()
    # end def

    def hoverMoveEvent(self, event):
        self.updateHoverLine(event)
    # end def

    def hoverLeaveEvent(self, event):
        self._hoverLine.hide()
    # end def

    def mousePressEvent(self, event):
        r = self._parent.radius()
        self.updateHoverLine(event)
        pos = self._hoverLine.pos()
        aX, aY, angle = self.snapPosToCircle(pos, r)
        if angle != None:
            self._startPos = QPointF(aX, aY)
            self._startAngle = self.updateHoverLine(event)
            self.dummy.updateAngle(self._startAngle, 0)
            self.dummy.show()
        # mark the start
        # f = QGraphicsEllipseItem(pX, pY, 2, 2, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0)))
    # end def

    def mouseMoveEvent(self, event):
        eventAngle = self.updateHoverLine(event)
        # Record initial direction before calling getSpanAngle
        if self._clockwise is None:
            self._clockwise = False if eventAngle > self._startAngle else True
        spanAngle = self.getSpanAngle(eventAngle)
        self.dummy.updateAngle(self._startAngle, spanAngle)
    # end def

    def mouseReleaseEvent(self, event):
        self.dummy.hide()
        endAngle = self.updateHoverLine(event)
        spanAngle = self.getSpanAngle(endAngle)
        angle = self._parent.virtualHelix().getProperty('eulerZ')
        self._parent.virtualHelix().setProperty('eulerZ', round((angle - spanAngle) % 360,0))
        
        # mark the end
        # x = self._hoverLine.x()
        # y = self._hoverLine.y()
        # f = QGraphicsEllipseItem(x, y, 6, 6, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0, 128)))
    # end def

    def updateHoverLine(self, event):
        """
        Moves red line to point (aX,aY) on RotateLine closest to event.pos.
        Returns the angle of aX, aY, using the Qt arc coordinate system
        (0 = east, 90 = north, 180 = west, 270 = south).
        """
        r = self._parent.radius()
        aX, aY, angle = self.snapPosToCircle(event.pos(), r)
        if angle != None:
            self._hoverLine.setPos(aX, aY)
            self._hoverLine.setRotation(-angle)
        return angle
    # end def

    def snapPosToCircle(self, pos, radius):
        """Given x, y and radius, return x,y of nearest point on circle, and its angle"""
        pX = pos.x()
        pY = pos.y()
        cX = cY = radius
        vX = pX - cX
        vY = pY - cY
        magV = sqrt(vX*vX + vY*vY)
        if magV == 0:
            return (None, None, None)
        aX = cX + vX / magV * radius
        aY = cY + vY / magV * radius
        angle = (atan2(aY-cY, aX-cX))
        deg = -degrees(angle) if angle < 0 else 180+(180-degrees(angle))
        return (aX, aY, deg)
    # end def

    def getSpanAngle(self, angle):
        """
        Return the spanAngle angle by checking the initial direction of the selection.
        Selections that cross 0° must be handed as an edge case.
        """
        if self._clockwise: # spanAngle is negative
            if angle < self._startAngle:
                spanAngle = angle - self._startAngle
            else:
                spanAngle = -(self._startAngle + (360-angle))
        else: # counterclockwise, spanAngle is positive
            if angle > self._startAngle:
                spanAngle = angle - self._startAngle
            else:
                spanAngle = (360-self._startAngle) + angle
        return spanAngle
    # end def
# end class

class RotateLine(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self.updateColor(parent.modelColor())
        self.setRect(rect)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)
    # end def

    def updateColor(self, color):
        self.setPen(getPenObj(color, _ROTATELINE_WIDTH))

    def updateRect(self, rect):
        self.setRect(rect)
# end class
