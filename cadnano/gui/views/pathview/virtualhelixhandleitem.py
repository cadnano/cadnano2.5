"""Summary
"""
from math import floor

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano.gui.palette import getPenObj, getBrushObj
from . import pathstyles as styles

_RADIUS = styles.VIRTUALHELIXHANDLEITEM_RADIUS
_RECT = QRectF(0,
               0,
               2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH,
               2*_RADIUS + styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_DEF_BRUSH = getBrushObj(styles.GRAY_FILL)
_DEF_PEN = getPenObj(styles.GRAY_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_HOV_BRUSH = getBrushObj(styles.BLUE_FILL)
_HOV_PEN = getPenObj(styles.BLUE_STROKE, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
_FONT = styles.VIRTUALHELIXHANDLEITEM_FONT

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_VH_XOFFSET = styles.VH_XOFFSET


class VirtualHelixHandleItem(QGraphicsEllipseItem):
    """Summary

    Attributes:
        drag_last_position (TYPE): Description
        FILTER_NAME (str): Description
        handle_start (TYPE): Description
    """
    FILTER_NAME = "virtual_helix"

    def __init__(self, virtual_helix_item, part_item, viewroot):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            part_item (TYPE): Description
            viewroot (TYPE): Description
        """
        super(VirtualHelixHandleItem, self).__init__(part_item)
        self._virtual_helix_item = virtual_helix_item
        self._id_num = virtual_helix_item.idNum()
        self._part_item = part_item
        self._model_part = part_item.part()
        self._viewroot = viewroot

        self._right_mouse_move = False
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
        # self.show()
    # end def

    def rotateWithCenterOrigin(self, angle):
        """Summary

        Args:
            angle (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def part(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._model_part
    # end def

    def idNum(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._id_num
    # end def

    def getProperty(self, key):
        """Summary

        Args:
            key (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self._model_part.getVirtualHelixProperties(self._id_num, key)
    # end def

    def getAngularProperties(self):
        """
        Returns:
            Tuple: 'bases_per_repeat, 'bases_per_turn',
                    'twist_per_base', 'minor_groove_angle'
        """
        bpr, tpr, mga = self._model_part.getVirtualHelixProperties(self._id_num,
                                                                   ['bases_per_repeat',
                                                                    'turns_per_repeat',
                                                                    'minor_groove_angle'])
        bases_per_turn = bpr / tpr
        return bpr, bases_per_turn, tpr*360./bpr, mga

    def setProperty(self, key, value):
        """Summary

        Args:
            key (TYPE): Description
            value (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self._model_part.setVirtualHelixProperties(self._id_num, key, value)
    # end def

    def modelColor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._model_part.getProperty('color')
    # end def

    def refreshColor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        part_color = self._model_part.getProperty('color')
        self._USE_PEN = getPenObj(part_color, styles.VIRTUALHELIXHANDLEITEM_STROKE_WIDTH)
        self._USE_BRUSH = getBrushObj(styles.DEFAULT_BRUSH_COLOR)
        self.setPen(self._USE_PEN)
        self.setBrush(self._USE_BRUSH)
        self.update(self.boundingRect())
    # end def

    def setSelectedColor(self, value):
        """Summary

        Args:
            value (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self._id_num >= 0:
            if value == True:  # noqa
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
        """Summary

        Returns:
            TYPE: Description
        """
        scene = self.scene()
        scene.removeItem(self._label)
        scene.removeItem(self)
        self._label = None
    # end def

    def createLabel(self):
        """Summary

        Returns:
            TYPE: Description
        """
        label = QGraphicsSimpleTextItem("%d" % (self._id_num))
        label.setFont(_FONT)
        label.setZValue(styles.ZPATHHELIX)
        label.setParentItem(self)
        return label
    # end def

    def setNumber(self):
        """docstring for setNumber
        """
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
        else:  # _number >= 100
            label.setPos(0, y_val)
        bRect = label.boundingRect()
        posx = bRect.width()/2
        posy = bRect.height()/2
        label.setPos(radius-posx, radius-posy)
    # end def

    def partItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._part_item
    # end def

    ### DRAWING ###
    def paint(self, painter, option, widget):
        """Need to override paint so selection appearance is correct.

        Args:
            painter (TYPE): Description
            option (TYPE): Description
            widget (TYPE): Description
        """
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawEllipse(self.rect())
    # end def

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the PathHelixHandle brush and pen from default
        to the hover colors if necessary.

        Args:
            event (QGraphicsSceneHoverEvent): Description
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

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        if not self.isSelected():
            self.setSelectedColor(False)
            self.update(self.boundingRect())
    # end def

    def mousePressEvent(self, event):
        """
        All mousePressEvents are passed to the group if it's in a group

        Args:
            event (TYPE): Description
        """
        selection_group = self.group()
        if selection_group is not None:
            selection_group.mousePressEvent(event)
        elif event.button() == Qt.RightButton:
            current_filter_set = self._viewroot.selectionFilterSet()
            if self.FILTER_NAME in current_filter_set and self.part().isZEditable():
                self._right_mouse_move = True
                self.drag_last_position = event.scenePos()
                self.handle_start = self.pos()
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        All mouseMoveEvents are passed to the group if it's in a group

        Args:
            event (TYPE): Description
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        selection_group = self.group()
        if selection_group is not None:
            selection_group.mousePressEvent(event)
        elif self._right_mouse_move:
            new_pos = event.scenePos()
            delta = new_pos - self.drag_last_position
            dx = int(floor(delta.x() / _BASE_WIDTH))*_BASE_WIDTH
            x = self.handle_start.x() + dx
            if abs(dx) > MOVE_THRESHOLD or dx == 0.0:
                old_x = self.x()
                self.setX(x)
                self._virtual_helix_item.setX(x + _VH_XOFFSET)
                self._part_item.updateXoverItems(self._virtual_helix_item)
                dz = self._part_item.convertToModelZ(x - old_x)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, False,
                                                         use_undostack=False)
        else:
            QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        MOVE_THRESHOLD = 0.01   # ignore small moves
        if self._right_mouse_move and event.button() == Qt.RightButton:
            self._right_mouse_move = False
            delta = self.pos() - self.handle_start
            dz = delta.x()
            if abs(dz) > MOVE_THRESHOLD:
                dz = self._part_item.convertToModelZ(dz)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, True,
                                                         use_undostack=True)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the part_item

        Args:
            pos (None, optional): Description
        """

        # map the position
        self.tempReparent(pos=pos)
        self.setSelectedColor(False)
        assert(self.group() is None)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        """Summary

        Args:
            pos (None, optional): Description

        Returns:
            TYPE: Description
        """
        part_item = self._part_item
        if pos is None:
            pos = self.scenePos()
        self.setParentItem(part_item)
        temp_point = part_item.mapFromScene(pos)
        self.setPos(temp_point)
    # end def

    def itemChange(self, change, value):
        """For selection changes test against QGraphicsItem.ItemSelectedChange
        intercept the change instead of the has changed to enable features.

        Args:
            change (TYPE): Description
            value (TYPE): Description
        """

        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            viewroot = self._viewroot
            current_filter_set = viewroot.selectionFilterSet()
            selection_group = viewroot.vhiHandleSelectionGroup()
            # print("filter set", current_filter_set, self.FILTER_NAME)
            # only add if the selection_group is not locked out
            if value == True and self.FILTER_NAME in current_filter_set:    # noqa
                if self.group() != selection_group:
                    if not selection_group.isPending(self):
                        selection_group.pendToAdd(self)
                        selection_group.setSelectionLock(selection_group)
                        self.setSelectedColor(True)
                        return False  # only select if mode says so
                    return True
                else:
                    return False
            # end if
            elif value == True:  # noqa
                # print("don't select", value)
                # don't select
                return False
            else:
                # Deselect
                # print("Deselect", value)
                selection_group.pendToRemove(self)
                self.setSelectedColor(False)
                return False
            # end else
        # end if
        else:
            return QGraphicsEllipseItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        """Summary

        Args:
            document (TYPE): Description

        Returns:
            TYPE: Description
        """
        # print("model Deselect")
        id_num = self._id_num
        part = self._model_part
        is_model_selected = document.isVirtualHelixSelected(part, id_num)
        if is_model_selected:
            document.removeVirtualHelicesFromSelection(part, [id_num])
        else:
            self.restoreParent()
    # end def

    def modelSelect(self, document):
        """Summary

        Args:
            document (TYPE): Description

        Returns:
            TYPE: Description
        """
        # print("select ms")
        id_num = self._id_num
        part = self._model_part
        is_model_selected = document.isVirtualHelixSelected(part, id_num)
        if not is_model_selected:
            # print("tell model to select")
            document.addVirtualHelicesToSelection(part, [id_num])
        else:
            # print("model selected")
            if not self.isSelected():
                # print("setting anyway")
                self.setSelected(True)
    # end def
# end class
