from math import sqrt, atan2, degrees, pi, floor

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QFont, QPen, QPainterPath, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtWidgets import QUndoCommand, QStyle

from cadnano import util
from cadnano.gui.palette import getPenObj, getNoPen, getBrushObj, getNoBrush
from cadnano.gui.views.sliceview.sliceextras import PreXoverItem, PreXoverItemGroup
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
    _filter_name = "virtual_helix"

    def __init__(self, virtual_helix_item, part_item, viewroot):
        super(VirtualHelixHandleItem, self).__init__(part_item)
        self._virtual_helix_item = virtual_helix_item
        self._id_num = virtual_helix_item.idNum()
        self._part_item = part_item
        self._model_part = part_item.part()
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
        # self.show()

        self._prexoveritemgroup = _pxig = PreXoverItemGroup(_RADIUS, _RECT, self)
        _pxig.setTransformOriginPoint(_RECT.center())

    # end def

    def rotateWithCenterOrigin(self, angle):
        self._prexoveritemgroup.setRotation(angle)
    # end def

    def part(self):
        return self._model_part
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def getProperty(self, key):
        return self._model_part.getVirtualHelixProperties(self._id_num, key)
    # end def

    def setProperty(self, key, value):
        return self._model_part.setVirtualHelixProperties(self._id_num, key, value)
    # end def

    def modelColor(self):
        return self._model_part.getProperty('color')
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
        if self._id_num >= 0:
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
        label = QGraphicsSimpleTextItem("%d" % (self._id_num))
        label.setFont(_FONT)
        label.setZValue(styles.ZPATHHELIX)
        label.setParentItem(self)
        return label
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        num = self._id_num
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

    def partItem(self):
        return self._part_item
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
            if self._id_num >= 0:
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
            self.drag_last_position = event.scenePos()
            self.handle_start = self.pos()
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        selection_group = self.group()
        if selection_group is not None:
            selection_group.mousePressEvent(event)
        elif self._right_mouse_move:
            new_pos = event.scenePos()
            delta = new_pos - self.drag_last_position
            dx = int(floor(delta.x() / _BASE_WIDTH ))*_BASE_WIDTH
            x = self.handle_start.x() + dx
            if abs(dx) > MOVE_THRESHOLD:
                old_x = self.x()
                self.setX(x)
                self._virtual_helix_item.setX(x + _VH_XOFFSET)
                self._part_item.updateXoverItems(self._virtual_helix_item)
                dz = self._part_item.getModelAxisPoint(x - old_x)
                self._model_part.translateVirtualHelices([self.idNum()], 0, 0, dz, False, use_undostack=False)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        MOVE_THRESHOLD = 0.01   # ignore small moves
        if self._right_mouse_move and event.button() == Qt.RightButton:
            self._right_mouse_move = False
            delta = self.pos() - self.handle_start
            dz = delta.x()
            if abs(dz) > MOVE_THRESHOLD:
                dz = self._part_item.getModelAxisPoint(dz)
                self._model_part.translateVirtualHelices([self.idNum()], 0, 0, dz, True)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the part_item
        """

        # map the position
        self.tempReparent(pos=pos)
        self.setSelectedColor(False)
        assert(self.group() is None)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        part_item = self._part_item
        if pos is None:
            pos = self.scenePos()
        self.setParentItem(part_item)
        temp_point = part_item.mapFromScene(pos)
        self.setPos(temp_point)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            viewroot = self._viewroot
            current_filter_set = viewroot.selectionFilterSet()
            selection_group = viewroot.vhiHandleSelectionGroup()
            print("filter set", current_filter_set, self._filter_name)
            # only add if the selection_group is not locked out
            if value == True and self._filter_name in current_filter_set:
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
        id_num = self._id_num
        part = self._model_part
        is_selected = document.isVirtualHelixSelected(part, id_num)
        if is_selected:
            document.removeVirtualHelicesFromSelection(part, [id_num])
        else:
            self.restoreParent()
    # end def

    def modelSelect(self, document):
        id_num = self._id_num
        part = self._model_part
        is_selected = document.isVirtualHelixSelected(part, id_num)
        if not is_selected:
            # print("VHHHI pop")
            document.addVirtualHelicesToSelection(part, [id_num])
        else:
            self.setSelected(True)
    # end def
# end class
