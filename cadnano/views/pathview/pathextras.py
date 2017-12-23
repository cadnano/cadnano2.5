# -*- coding: utf-8 -*-
"""Summary

Attributes:
    BASE_RECT (TYPE): Description
    BASE_WIDTH (TYPE): Description
    KEYINPUT_ACTIVE_FLAG (TYPE): Description
    PHOS_ITEM_WIDTH (TYPE): Description
    PROX_ALPHA (int): Description
    T180 (TYPE): Description
    TRIANGLE (TYPE): Description
"""
from math import floor

from PyQt5.QtCore import QRectF, Qt, QObject, QPointF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano import util
from cadnano.proxies.cnenum import HandleType
from cadnano.gui.palette import getNoPen, getPenObj, newPenObj
from cadnano.gui.palette import getBrushObj, getNoBrush
from cadnano.views.resizehandles import ResizeHandleGroup
from . import pathstyles as styles


BASE_WIDTH = styles.PATH_BASE_WIDTH
BASE_RECT = QRectF(0, 0, BASE_WIDTH, BASE_WIDTH)


PHOS_ITEM_WIDTH = 0.25*BASE_WIDTH
TRIANGLE = QPolygonF()
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.append(QPointF(0.75 * PHOS_ITEM_WIDTH, 0.5 * PHOS_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, PHOS_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.translate(0, -0.5*PHOS_ITEM_WIDTH)
T180 = QTransform()
T180.rotate(-180)
FWDPHOS_PP, REVPHOS_PP = QPainterPath(), QPainterPath()
FWDPHOS_PP.addPolygon(TRIANGLE)
REVPHOS_PP.addPolygon(T180.map(TRIANGLE))

KEYINPUT_ACTIVE_FLAG = QGraphicsItem.ItemIsFocusable


class PropertyWrapperObject(QObject):
    """Summary

    Attributes:
        animations (dict): Description
        brush_alpha (TYPE): Description
        item (TYPE): Description
        rotation (TYPE): Description
    """

    def __init__(self, item):
        """Summary

        Args:
            item (TYPE): Description
        """
        super(PropertyWrapperObject, self).__init__()
        self.item = item
        self.animations = {}

    def __get_brushAlpha(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.brush().color().alpha()

    def __set_brushAlpha(self, alpha):
        """Summary

        Args:
            alpha (TYPE): Description

        Returns:
            TYPE: Description
        """
        brush = QBrush(self.item.brush())
        color = QColor(brush.color())
        color.setAlpha(alpha)
        self.item.setBrush(QBrush(color))

    def __get_rotation(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.rotation()

    def __set_rotation(self, angle):
        """Summary

        Args:
            angle (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.item.setRotation(angle)

    def saveRef(self, property_name, animation):
        """Summary

        Args:
            property_name (TYPE): Description
            animation (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.animations[property_name] = animation

    def getRef(self, property_name):
        """Summary

        Args:
            property_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self.animations.get(property_name)

    def destroy(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.item = None
        self.animations = None
        self.deleteLater()

    def resetAnimations(self):
        """Summary

        Returns:
            TYPE: Description
        """
        for item in self.animations.values():
            item.stop()
            item.deleteLater()
            item = None
        self.animations = {}

    brush_alpha = pyqtProperty(int, __get_brushAlpha, __set_brushAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class


class Triangle(QGraphicsPathItem):
    """Summary

    Attributes:
        adapter (TYPE): Description
    """

    def __init__(self, painter_path, parent=None):
        """Summary

        Args:
            painter_path (TYPE): Description
            parent (None, optional): Description
        """
        super(QGraphicsPathItem, self).__init__(painter_path, parent)
        self.adapter = PropertyWrapperObject(self)
    # end def
# end class


class PreXoverLabel(QGraphicsSimpleTextItem):
    """Summary

    Attributes:
        is_fwd (TYPE): Description
    """
    _XO_FONT = styles.XOVER_LABEL_FONT
    _XO_BOLD = styles.XOVER_LABEL_FONT_BOLD
    _FM = QFontMetrics(_XO_FONT)

    def __init__(self, is_fwd, color, pre_xover_item):
        """Summary

        Args:
            is_fwd (TYPE): Description
            color (TYPE): Description
            pre_xover_item (TYPE): Description
        """
        super(QGraphicsSimpleTextItem, self).__init__(pre_xover_item)
        self.is_fwd = is_fwd
        self._color = color
        self._tbr = None
        self._outline = QGraphicsRectItem(self)
        self.setFont(self._XO_FONT)
        self.setBrush(getBrushObj('#666666'))
    # end def

    def resetItem(self, is_fwd, color):
        """Summary

        Args:
            is_fwd (TYPE): Description
            color (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.is_fwd = is_fwd
        self._color = color
    # end def

    def setTextAndStyle(self, text, outline=False):
        """Summary

        Args:
            text (TYPE): Description
            outline (bool, optional): Description

        Returns:
            TYPE: Description
        """
        str_txt = str(text)
        self._tbr = tBR = self._FM.tightBoundingRect(str_txt)
        half_label_H = tBR.height() / 2.0
        half_label_W = tBR.width() / 2.0

        labelX = BASE_WIDTH/2.0 - half_label_W
        if str_txt == '1':  # adjust for the number one
            labelX -= tBR.width()

        labelY = half_label_H if self.is_fwd else (BASE_WIDTH - tBR.height())/2

        self.setPos(labelX, labelY)
        self.setText(str_txt)

        if outline:
            self.setFont(self._XO_BOLD)
            self.setBrush(getBrushObj('#ff0000'))
        else:
            self.setFont(self._XO_FONT)
            self.setBrush(getBrushObj('#666666'))

        if outline:
            r = QRectF(self._tbr).adjusted(-half_label_W, 0,
                                           half_label_W, half_label_H)
            self._outline.setRect(r)
            self._outline.setPen(getPenObj('#ff0000', 0.25))
            self._outline.setY(2*half_label_H)
            self._outline.show()
        else:
            self._outline.hide()
    # end def
# end class


PROX_ALPHA = 64


class PreXoverItem(QGraphicsRectItem):
    """A PreXoverItem exists between a single 'from' VirtualHelixItem index
    and zero or more 'to' VirtualHelixItem Indices

    Attributes:
        adapter (TYPE): Description
        idx (int): the base index within the virtual helix
        is_fwd (TYPE): Description
        prexoveritemgroup (TYPE): Description
        to_vh_id_num (TYPE): Description
    """

    def __init__(self, from_virtual_helix_item, is_fwd, from_index,
                 to_vh_id_num, prexoveritemgroup, color):
        """Summary

        Args:
            from_virtual_helix_item (cadnano.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_fwd (TYPE): Description
            from_index (TYPE): Description
            to_vh_id_num (TYPE): Description
            prexoveritemgroup (TYPE): Description
            color (TYPE): Description
        """
        super(QGraphicsRectItem, self).__init__(BASE_RECT, from_virtual_helix_item)
        self.adapter = PropertyWrapperObject(self)
        self._bond_item = QGraphicsPathItem(self)
        self._bond_item.hide()
        self._label = PreXoverLabel(is_fwd, color, self)
        self._phos_item = Triangle(FWDPHOS_PP, self)
        self.setPen(getNoPen())
        self.resetItem(from_virtual_helix_item, is_fwd, from_index,
                       to_vh_id_num, prexoveritemgroup, color)
    # end def

    def shutdown(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.setBrush(getBrushObj(self._color, alpha=0))
        self.to_vh_id_num = None
        self.adapter.resetAnimations()
        phos = self._phos_item
        phos.adapter.resetAnimations()
        phos.resetTransform()
        phos.setPos(0, 0)
        self.setAcceptHoverEvents(False)
        self.setFlag(KEYINPUT_ACTIVE_FLAG, False)
        self.hide()
    # end def

    def resetItem(self, from_virtual_helix_item, is_fwd, from_index,
                  to_vh_id_num, prexoveritemgroup, color):
        """Summary

        Args:
            from_virtual_helix_item (cadnano.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_fwd (TYPE): Description
            from_index (TYPE): Description
            to_vh_id_num (TYPE): Description
            prexoveritemgroup (TYPE): Description
            color (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.setParentItem(from_virtual_helix_item)
        self.resetTransform()
        self._id_num = from_virtual_helix_item.idNum()
        self.idx = from_index
        self.is_fwd = is_fwd
        self.to_vh_id_num = to_vh_id_num
        self._color = color
        self.prexoveritemgroup = prexoveritemgroup
        self._bond_item.hide()
        self._label_txt = lbt = None if to_vh_id_num is None else str(to_vh_id_num)
        self.setLabel(text=lbt)
        self._label.resetItem(is_fwd, color)

        phos = self._phos_item
        bonditem = self._bond_item

        if is_fwd:
            phos.setPath(FWDPHOS_PP)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(0.5*BASE_WIDTH, BASE_WIDTH)
            phos.setPen(getNoPen())
            phos.setBrush(getBrushObj(color))
            bonditem.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH))
            self.setPos(from_index*BASE_WIDTH, -BASE_WIDTH)
        else:
            phos.setPath(REVPHOS_PP)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(0.5*BASE_WIDTH, 0)
            phos.setPen(getPenObj(color, 0.25))
            phos.setBrush(getNoBrush())
            bonditem.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH,
                                      penstyle=Qt.DotLine, capstyle=Qt.RoundCap))
            self.setPos(from_index*BASE_WIDTH, 2*BASE_WIDTH)

        if to_vh_id_num is not None:
            inactive_alpha = PROX_ALPHA
            self.setBrush(getBrushObj(color, alpha=inactive_alpha))
        else:
            self.setBrush(getBrushObj(color, alpha=0))
        self.show()
    # end def

    def getInfo(self):
        """
        Returns:
            Tuple: (from_id_num, is_fwd, from_index, to_vh_id_num)
        """
        return (self._id_num, self.is_fwd, self.idx, self.to_vh_id_num)

    ### ACCESSORS ###
    def color(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._color

    def remove(self):
        """Summary

        Returns:
            TYPE: Description
        """
        scene = self.scene()
        self.adapter.destroy()
        if scene:
            scene.removeItem(self._label)
            self._label = None
            self._phos_item.adapter.resetAnimations()
            self._phos_item.adapter = None
            scene.removeItem(self._phos_item)
            self._phos_item = None
            scene.removeItem(self._bond_item)
            self._bond_item = None
            self.adapter.resetAnimations()
            self.adapter = None
            scene.removeItem(self)
    # end defS

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        """Only if enableActive(True) is called
        hover and key events disabled by default

        Args:
            event (TYPE): Description
        """
        self.setFocus(Qt.MouseFocusReason)
        self.prexoveritemgroup.updateModelActiveBaseInfo(self.getInfo())
        self.setActiveHovered(True)
        status_string = "%d[%d]" % (self._id_num, self.idx)
        self.parentItem().window().statusBar().showMessage(status_string)
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.prexoveritemgroup.updateModelActiveBaseInfo(None)
        self.setActiveHovered(False)
        self.clearFocus()
        self.parentItem().window().statusBar().showMessage("")
    # end def

    def keyPressEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.prexoveritemgroup.handlePreXoverKeyPress(event.key())
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def setLabel(self, text=None, outline=False):
        """Summary

        Args:
            text (None, optional): Description
            outline (bool, optional): Description

        Returns:
            TYPE: Description
        """
        if text:
            self._label.setTextAndStyle(text=text, outline=outline)
            self._label.show()
        else:
            self._label.hide()
    # end def

    def animate(self, item, property_name, duration, start_value, end_value):
        """Summary

        Args:
            item (TYPE): Description
            property_name (TYPE): Description
            duration (TYPE): Description
            start_value (TYPE): Description
            end_value (TYPE): Description

        Returns:
            TYPE: Description
        """
        b_name = property_name.encode('ascii')
        anim = item.adapter.getRef(property_name)
        if anim is None:
            anim = QPropertyAnimation(item.adapter, b_name)
            item.adapter.saveRef(property_name, anim)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()
    # end def

    def setActiveHovered(self, is_active):
        """Rotate phosphate Triangle if `self.to_vh_id_num` is not `None`

        Args:
            is_active (bool): whether or not the PreXoverItem is parented to the
                active VirtualHelixItem
        """
        if is_active:
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 1, 0, 128)  # overwrite running anim
            # if self.to_vh_id_num is not None:
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
        else:
            inactive_alpha = 0 if self.to_vh_id_num is None else PROX_ALPHA
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
    # end def

    def enableActive(self, is_active, to_vh_id_num=None):
        """Call on PreXoverItems created on the active VirtualHelixItem

        Args:
            is_active (TYPE): Description
            to_vh_id_num (None, optional): Description
        """
        if is_active:
            self.to_vh_id_num = to_vh_id_num
            self.setAcceptHoverEvents(True)
            if to_vh_id_num is None:
                self.setLabel(text=None)
                self.setBrush(getBrushObj(self._color, alpha=0))
            else:
                self.setLabel(text=str(to_vh_id_num))
                inactive_alpha = PROX_ALPHA
                self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
                self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
                self.setFlag(KEYINPUT_ACTIVE_FLAG, True)
        else:
            self.setBrush(getNoBrush())
            # self.setLabel(text=None)
            self.setAcceptHoverEvents(False)
            self.setFlag(KEYINPUT_ACTIVE_FLAG, False)

    def activateNeighbor(self, active_prexoveritem, shortcut=None):
        """To be called with whatever the active_prexoveritem
        is for the parts `active_base`

        Args:
            active_prexoveritem (TYPE): Description
            shortcut (None, optional): Description
        """
        p1 = self._phos_item.scenePos()
        p2 = active_prexoveritem._phos_item.scenePos()
        scale = 3
        delta1 = -BASE_WIDTH*scale if self.is_fwd else BASE_WIDTH*scale
        delta2 = BASE_WIDTH*scale if active_prexoveritem.is_fwd else -BASE_WIDTH*scale
        c1 = self.mapFromScene(QPointF(p1.x(), p1.y() + delta1))
        c2 = self.mapFromScene(QPointF(p2.x(), p2.y() - delta2))
        pp = QPainterPath()
        pp.moveTo(self._phos_item.pos())
        pp.cubicTo(c1, c2, self._bond_item.mapFromScene(p2))
        self._bond_item.setPath(pp)
        self._bond_item.show()

        alpha = 32
        idx, active_idx = self.idx, active_prexoveritem.idx
        if self.is_fwd != active_prexoveritem.is_fwd:
            if idx == active_idx:
                alpha = 255
        elif idx == active_idx + 1:
            alpha = 255
        elif idx == active_idx - 1:
            alpha = 255

        inactive_alpha = PROX_ALPHA if self.to_vh_id_num is not None else 0
        self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
        self.animate(self, 'brush_alpha', 500, inactive_alpha, alpha)
        self.animate(self._phos_item, 'rotation', 500, 0, -90)
        self.setLabel(text=shortcut, outline=True)
    # end def

    def deactivateNeighbor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        if self.isVisible():
            inactive_alpha = PROX_ALPHA if self.to_vh_id_num is not None else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
            self._bond_item.hide()
            self.setLabel(text=self._label_txt)
    # end def
# end class


class PathWorkplaneItem(QGraphicsRectItem):
    """Draws the rectangle to indicate the current Workplane, i.e. the
    region of part bases affected by certain actions in other views."""
    _BOUNDING_RECT_PADDING = 0
    _HANDLE_SIZE = 6
    _MIN_WIDTH = 3

    def __init__(self, model_part, part_item):
        super(QGraphicsRectItem, self).__init__(BASE_RECT, part_item)
        self.setAcceptHoverEvents(True)
        # self.setBrush(getNoBrush())
        self.setBrush(getBrushObj(styles.BLUE_FILL, alpha=12))
        self.setPen(getNoPen())

        self._model_part = model_part
        self._part_item = part_item
        self._idx_low, self._idx_high = model_part.getProperty('workplane_idxs')
        self._low_drag_bound = 0  # idx, not pos
        self._high_drag_bound = model_part.getProperty('max_vhelix_length')  # idx, not pos

        self.outline = QGraphicsRectItem(self)
        self.outline.setPen(newPenObj(styles.BLUE_STROKE, 0))
        self.resize_handle_group = ResizeHandleGroup(self.rect(), self._HANDLE_SIZE, styles.BLUE_STROKE, True,
                                                     HandleType.LEFT | HandleType.RIGHT, self)
        self.model_bounds_hint = m_b_h = QGraphicsRectItem(self)
        m_b_h.setBrush(getBrushObj(styles.BLUE_FILL, alpha=64))
        m_b_h.setPen(getNoPen())
        m_b_h.hide()

        TLx, TLy = self._idx_low*BASE_WIDTH, -BASE_WIDTH
        BRx, BRy = self._idx_high*BASE_WIDTH, self._part_item._vh_rect.height()-BASE_WIDTH*2
        self.reconfigureRect((TLx, TLy), (BRx, BRy))

    def getModelMinBounds(self, handle_type=None):
        """Resize bounds in form of Qt position, scaled from model."""
        if handle_type and handle_type & HandleType.LEFT:
            xTL = (self._idx_high-self._MIN_WIDTH)*BASE_WIDTH
            xBR = self._idx_high*BASE_WIDTH
        elif handle_type and handle_type & HandleType.RIGHT:
            xTL = (self._idx_low+self._MIN_WIDTH)*BASE_WIDTH
            xBR = (self._idx_low)*BASE_WIDTH
        else:  # default to HandleType.RIGHT behavior for all types
            print("no ht??")
            xTL = 0
            xBR = self._high_drag_bound*BASE_WIDTH
        yTL = self._part_item._vh_rect.top()
        yBR = self._part_item._vh_rect.bottom()-BASE_WIDTH*3
        return xTL, yTL, xBR, yBR
    # end def

    def setMovable(self, is_movable):
        # self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
        pass
    # end def

    def finishDrag(self):
        """Set the workplane size in the model"""
        # pos = self.pos()
        # position = pos.x(), pos.y()
        # view_name = self._viewroot.name
        # self._model_part.changeInstanceProperty(self._model_instance, view_name, 'position', position)
    # end def

    def reconfigureRect(self, top_left, bottom_right):
        """Update the workplane rect to draw from top_left to bottom_right,
        snapping the x values to the nearest base width. Updates the outline
        and resize handles.

        Args:
            top_left (tuple): topLeft (x, y)
            bottom_right (tuple): bottomRight (x, y)

        Returns:
            QRectF: the new rect.
        """
        if top_left:
            xTL = max(top_left[0], self._low_drag_bound)
            xTL = xTL - (xTL % BASE_WIDTH)  # snap to nearest base
            self._idx_low = xTL/BASE_WIDTH
        else:
            xTL = self._idx_low*BASE_WIDTH

        if bottom_right:
            xBR = util.clamp(bottom_right[0],
                             (self._idx_low+self._MIN_WIDTH)*BASE_WIDTH,
                             (self._high_drag_bound)*BASE_WIDTH)
            xBR = xBR - (xBR % BASE_WIDTH)  # snap to nearest base
            self._idx_high = xBR/BASE_WIDTH
        else:
            xBR = self._idx_high*BASE_WIDTH

        yTL = self._part_item._vh_rect.top()
        yBR = self._part_item._vh_rect.bottom()-BASE_WIDTH*3

        xoffset = styles.MINOR_GRID_STROKE_WIDTH

        self.setRect(QRectF(QPointF(xTL+xoffset, yTL), QPointF(xBR+xoffset, yBR)))
        self.outline.setRect(self.rect())
        self.resize_handle_group.alignHandles(self.rect())
        self._model_part.setProperty('workplane_idxs', (self._idx_low, self._idx_high), use_undostack=False)
        return self.rect()

    def setIdxs(self, new_idxs):
        if self._idx_low != new_idxs[0] or self._idx_high != new_idxs[1]:
            self._idx_low = new_idxs[0]
            self._idx_high = new_idxs[1]
            self.reconfigureRect((), ())

    def showModelMinBoundsHint(self, handle_type, show=True):
        m_b_h = self.model_bounds_hint
        if show:
            xTL, yTL, xBR, yBR = self.getModelMinBounds(handle_type)
            m_b_h.setRect(QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR)))
            m_b_h.show()
        else:
            m_b_h.hide()
    # end def

    def width(self):
        return self._idx_high - self._idx_low
    # end def

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        self._part_item.updateStatusBar("{}–{}".format(self._idx_low, self._idx_high))
        QGraphicsItem.hoverEnterEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event):
        self._part_item.updateStatusBar("")
        QGraphicsItem.hoverLeaveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent. Stores _move_idx and _offset_idx for
        future comparison.
        """
        # self.setCursor(Qt.ClosedHandCursor)
        if event.modifiers() != Qt.ShiftModifier:            
        # if event.button() != Qt.LeftButton:
            event.ignore()
            QGraphicsItem.mousePressEvent(self, event)
            return

        self._start_idx_low = self._idx_low
        self._start_idx_high = self._idx_high
        self._delta = 0
        self._move_idx = int(floor((self.x()+event.pos().x()) / BASE_WIDTH))
        self._offset_idx = int(floor(event.pos().x()) / BASE_WIDTH)
        self._high_drag_bound = self._model_part.getProperty('max_vhelix_length') - self.width()
    # end def

    def mouseMoveEvent(self, event):
        delta = int(floor((self.x()+event.pos().x()) / BASE_WIDTH)) - self._offset_idx
        delta = util.clamp(delta,
                           self._low_drag_bound-self._start_idx_low,
                           self._high_drag_bound-self._start_idx_high+self.width())
        if self._delta != delta:
            self._idx_low = self._start_idx_low + delta
            self._idx_high = self._start_idx_high + delta
            self._delta = delta
            self.reconfigureRect((), ())
    # end def

    def mouseReleaseEvent(self, event):
        delta = int(floor((self.x()+event.pos().x()) / BASE_WIDTH)) - self._offset_idx
        delta = util.clamp(delta,
                           self._low_drag_bound-self._start_idx_low,
                           self._high_drag_bound-self._start_idx_high+self.width())
        if self._delta != delta:
            self._idx_low = self._start_idx_low + delta
            self._idx_high = self._start_idx_high + delta
            self._delta = delta
            self.reconfigureRect((), ())
        self._high_drag_bound = self._model_part.getProperty('max_vhelix_length')  # reset for handles
    # end def
