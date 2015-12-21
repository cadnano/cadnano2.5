from math import atan2, degrees, floor, pi, sqrt

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty, QTimer
from PyQt5.QtGui import QBrush, QFont, QPen, QPainterPath, QTransform
from PyQt5.QtGui import QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtWidgets import QUndoCommand, QStyle

from cadnano import util
from cadnano.gui.palette import getPenObj, getNoPen, getBrushObj, getNoBrush
from cadnano.gui.views.sliceview.virtualhelixitem import PreXoverItem, PreXoverItemGroup
from . import pathstyles as styles


_RADIUS = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_RECT = QRectF(0, 0, 2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,\
        2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_DEF_BRUSH = getBrushObj(styles.GRAY_FILL)
_DEF_PEN = getPenObj(styles.GRAY_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_HOV_BRUSH = getBrushObj(styles.BLUE_FILL)
_HOV_PEN = getPenObj(styles.BLUE_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_FONT = styles.VIRTUALHELIXHANDLEITEM_FONT

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_VH_XOFFSET = styles.VH_XOFFSET


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    def __init__(self, nucleicacid_part_item, virtual_helix_item, viewroot):
        super(VirtualHelixHandleItem, self).__init__(nucleicacid_part_item)
        self._nucleicacid_part_item = nucleicacid_part_item
        self._virtual_helix_item = virtual_helix_item
        self._virtual_helix = m_vh = virtual_helix_item.virtualHelix()
        self._model_part = nucleicacid_part_item.part()
        self._viewroot = viewroot
        self._right_mouse_move = False
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
        self._radius = _RADIUS
        self._rect = QRectF(_RECT)
        self._hover_rect = QRectF(_RECT)
        self._prexoveritemgroup = PreXoverItemGroup(_RADIUS, _RECT, self)
    # end def

    ### ACCESSORS ###

    def basesPerRepeat(self):
        return self._virtual_helix_item.basesPerRepeat()

    def turnsPerRepeat(self):
        return self._virtual_helix_item.turnsPerRepeat()

    def twistPerBase(self):
        return self._virtual_helix_item.twistPerBase()

    def part(self):
        return self._model_part
    # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def

    def partCrossoverSpanAngle(self):
        return float(self._model_part.getProperty('crossover_span_angle'))
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
            self._filter_name = 'even_virtual_helix' if num%2 == 0 else 'odd_virtual_helix'
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

    ### DRAWING ###
    def paint(self, painter, option, widget):
        """Need to override paint so selection appearance is correct."""
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
    # end def

    ### EVENT HANDLERS ###
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
        elif event.button() == Qt.RightButton:
            self._right_mouse_move = True
            self._button_down_pos = event.pos()
            self._button_down_coords = (event.scenePos(), self.pos())
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
        elif self._right_mouse_move:
            event_start, handle_start = self._button_down_coords
            delta = self.mapToScene(event.pos()) - event_start
            x = handle_start.x() + int(floor(delta.x())/_BASE_WIDTH)*_BASE_WIDTH
            if x != self.x():
                self.setX(x)
                self._virtual_helix_item.setX(x+_VH_XOFFSET)
                self.partItem().updateXoverItems(self._virtual_helix_item)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        if self._right_mouse_move and event.button() == Qt.RightButton:
            self._right_mouse_move = False
            p = self.mapToScene(event.pos()) - self._button_down_pos
            z = self._virtual_helix_item.x()
            self._virtual_helix.setProperty('z', z)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def refreshColor(self):
        part_color = self._model_part.getProperty('color')
        self._USE_PEN = getPenObj(part_color, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
        self._USE_BRUSH = getBrushObj(styles.HANDLE_FILL, alpha=128)
        self.setPen(self._USE_PEN)
        self.setBrush(self._USE_BRUSH)
        self.update(self.boundingRect())
    # end def

    def updateActivePreXoverItem(self, is_fwd, step_idx):
        self._prexoveritemgroup.updateActivePreXoverItem(is_fwd, step_idx)
    # end def

    def updateBasesPerRepeat(self):
        self._prexoveritemgroup.updateBasesPerRepeat()

    def updateTurnsPerRepeat(self):
        self._prexoveritemgroup.updateTurnsPerRepeat()

    def rotateWithCenterOrigin(self, angle):
        self._prexoveritemgroup.setRotation(angle)
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
