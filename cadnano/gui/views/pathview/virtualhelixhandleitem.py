import cadnano.util as util
from . import pathstyles as styles

from PyQt5.QtCore import QPointF, QRectF, Qt

from PyQt5.QtGui import QBrush, QFont, QPen, QDrag, QPainterPath, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QUndoCommand, QGraphicsEllipseItem, QStyle


_RADIUS = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_RECT = QRectF(0, 0, 2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,\
        2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_DEF_BRUSH = QBrush(styles.GRAY_FILL)
_DEF_PEN = QPen(styles.GRAY_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_HOV_BRUSH = QBrush(styles.BLUE_FILL)
_HOV_PEN = QPen(styles.BLUE_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_USE_BRUSH = QBrush(styles.ORANGE_FILL)
_USE_PEN = QPen(styles.ORANGE_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_FONT = styles.VIRTUALHELIXHANDLEITEM_FONT


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    """docstring for VirtualHelixHandleItem"""
    _filter_name = "virtual_helix"
    
    def __init__(self, virtual_helix, part_item, viewroot):
        super(VirtualHelixHandleItem, self).__init__(part_item)
        self._virtual_helix = virtual_helix
        self._part_item = part_item
        self._viewroot = viewroot
        self._being_hovered_over = False
        self.setAcceptHoverEvents(True)
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setSelectedColor(False)
        self.setZValue(styles.ZPATHHELIX)
        self.setRect(_RECT)
    # end def

    def setSelectedColor(self, value):
        if self.number() >= 0:
            if value == True:
                self.setBrush(_HOV_BRUSH)
                self.setPen(_HOV_PEN)
            else:
                self.setBrush(_USE_BRUSH)
                self.setPen(_USE_PEN)
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

        if num != None:
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
        return self._part_item
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
                    self.setBrush(_USE_BRUSH)
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
        if selection_group != None:
            selection_group.mousePressEvent(event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group
        """
        selection_group = self.group()
        if selection_group != None:
            selection_group.mousePressEvent(event)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the part_item
        """

        # map the position
        part_item = self._part_item
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(part_item)
        self.setSelectedColor(False)

        assert(self.parentItem() == part_item)
        # print "restore", self.number(), self.parentItem(), self.group()
        assert(self.group() == None)
        temp_p = part_item.mapFromScene(pos)
        self.setPos(temp_p)
        self.setSelected(False)
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
