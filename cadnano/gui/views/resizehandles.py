# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, QPointF, QRectF, Qt
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PyQt5.QtWidgets import qApp
from cadnano.cnenum import HandleType
from cadnano.gui.palette import getBrushObj, getPenObj

FILL_COLOR = '#ffffff'


class ResizeHandleGroup(QObject):
    """Provides the ability to move and resize the parent."""
    def __init__(self, parent_outline_rect, width, color, is_resizable, handle_types, parent_item):
        super(ResizeHandleGroup, self).__init__()
        # self.parent_outline_rect = parent_outline_rect  # set by call to alignHandles
        self.width = w = width
        self.half_width = h_w = w/2
        self.offset = QPointF(w, w)
        self.offset_x = QPointF(w, 0)
        self.offset_y = QPointF(0, w)
        self.half_offset = QPointF(h_w, h_w)
        self.half_offset_x = QPointF(h_w, 0)
        self.half_offset_y = QPointF(0, h_w)
        self.is_resizable = is_resizable
        self.is_dragging = False

        self.handle_types = handle_types
        self._t = HandleItem(HandleType.TOP, w, color, self, parent_item) \
            if handle_types & HandleType.TOP else None
        self._b = HandleItem(HandleType.BOTTOM, w, color, self, parent_item) \
            if handle_types & HandleType.BOTTOM else None
        self._l = HandleItem(HandleType.LEFT, w, color, self, parent_item) \
            if handle_types & HandleType.LEFT else None
        self._r = HandleItem(HandleType.RIGHT, w, color, self, parent_item) \
            if handle_types & HandleType.RIGHT else None
        self._tl = HandleItem(HandleType.TOP_LEFT, w, color, self, parent_item) \
            if handle_types & HandleType.TOP_LEFT else None
        self._tr = HandleItem(HandleType.TOP_RIGHT, w, color, self, parent_item) \
            if handle_types & HandleType.TOP_RIGHT else None
        self._bl = HandleItem(HandleType.BOTTOM_LEFT, w, color, self, parent_item) \
            if handle_types & HandleType.BOTTOM_LEFT else None
        self._br = HandleItem(HandleType.BOTTOM_RIGHT, w, color, self, parent_item) \
            if handle_types & HandleType.BOTTOM_RIGHT else None

        self.alignHandles(parent_outline_rect)
    # end def

    def alignHandles(self, o_rect):
        self.parent_outline_rect = o_rect
        if self.handle_types & HandleType.TOP:
            self._t.setPos(QPointF(o_rect.center().x(), o_rect.top()) - self.half_offset)
        if self.handle_types & HandleType.BOTTOM:
            self._b.setPos(QPointF(o_rect.center().x(), o_rect.bottom()) - self.half_offset)
        if self.handle_types & HandleType.LEFT:
            self._l.setPos(QPointF(o_rect.left(), o_rect.center().y()) - self.half_offset)
        if self.handle_types & HandleType.RIGHT:
            self._r.setPos(QPointF(o_rect.right(), o_rect.center().y()) - self.half_offset)
        if self.handle_types & HandleType.TOP_LEFT:
            self._tl.setPos(o_rect.topLeft() - self.half_offset)
        if self.handle_types & HandleType.TOP_RIGHT:
            self._tr.setPos(o_rect.topRight() - self.half_offset)
        if self.handle_types & HandleType.BOTTOM_LEFT:
            self._bl.setPos(o_rect.bottomLeft() - self.half_offset)
        if self.handle_types & HandleType.BOTTOM_RIGHT:
            self._br.setPos(o_rect.bottomRight() - self.half_offset)

    def removeHandles(self):
        self._t = None
        self._b = None
        self._l = None
        self._r = None
        self._tl = None
        self._tr = None
        self._bl = None
        self._br = None
    # end def

    def setPens(self, pen):
        for handle in self._list:
            handle.setPen(pen)
    # end def

    def setZValue(self, z):
        if self.handle_types & HandleType.TOP:
            self._t.setZValue(z)
        if self.handle_types & HandleType.BOTTOM:
            self._b.setZValue(z)
        if self.handle_types & HandleType.LEFT:
            self._l.setZValue(z)
        if self.handle_types & HandleType.RIGHT:
            self._r.setZValue(z)
        if self.handle_types & HandleType.TOP_LEFT:
            self._tl.setZValue(z)
        if self.handle_types & HandleType.TOP_RIGHT:
            self._tr.setZValue(z)
        if self.handle_types & HandleType.BOTTOM_LEFT:
            self._bl.setZValue(z)
        if self.handle_types & HandleType.BOTTOM_RIGHT:
            self._br.setZValue(z)
    # end def

    def setParentItemAll(self, new_parent):
        if self.handle_types & HandleType.TOP:
            self._t.setParentItem(new_parent)
        if self.handle_types & HandleType.BOTTOM:
            self._b.setParentItem(new_parent)
        if self.handle_types & HandleType.LEFT:
            self._l.setParentItem(new_parent)
        if self.handle_types & HandleType.RIGHT:
            self._r.setParentItem(new_parent)
        if self.handle_types & HandleType.TOP_LEFT:
            self._tl.setParentItem(new_parent)
        if self.handle_types & HandleType.TOP_RIGHT:
            self._tr.setParentItem(new_parent)
        if self.handle_types & HandleType.BOTTOM_LEFT:
            self._bl.setParentItem(new_parent)
        if self.handle_types & HandleType.BOTTOM_RIGHT:
            self._br.setParentItem(new_parent)
    # end def
# end class


class HandleItem(QGraphicsRectItem):
    """Provides the ability to resize the document."""
    def __init__(self, handle_type, width, color, handle_group, parent):
        super(HandleItem, self).__init__(parent)
        self.setAcceptHoverEvents(True)
        self._handle_type = handle_type
        self._group = handle_group
        self.width = w = width
        self.half_width = w/2
        self.align_offset = parent._BOUNDING_RECT_PADDING
        self.model_bounds = ()

        self.setBrush(getBrushObj(FILL_COLOR))
        self.setPen(getPenObj(color, 0))
        self.setRect(QRectF(0, 0, w, w))

        if handle_type & (HandleType.LEFT | HandleType.RIGHT):
            self._resize_cursor = Qt.SizeHorCursor
        elif handle_type & (HandleType.TOP | HandleType.BOTTOM):
            self._resize_cursor = Qt.SizeVerCursor
        elif handle_type & (HandleType.TOP_LEFT | HandleType.BOTTOM_RIGHT):
            self._resize_cursor = Qt.SizeFDiagCursor
        elif handle_type & (HandleType.TOP_RIGHT | HandleType.BOTTOM_LEFT):
            self._resize_cursor = Qt.SizeBDiagCursor
        else:
            self._resize_cursor = Qt.ClosedHandCursor
    # end def

    def function():
        pass



    def hoverEnterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        # self._part_item.updateStatusBar("{}–{}".format(self._idx_low, self._idx_high))
        # QGraphicsItem.hoverEnterEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
    # end def

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return

        parent = self.parentItem()
        if self._group.is_resizable and event.modifiers() & Qt.ShiftModifier:
            self.setCursor(self._resize_cursor)
            self.model_bounds = parent.getModelMinBounds(handle_type=self._handle_type)
            self.event_start_position = event.scenePos()
            self.item_start = self.pos()
            parent.showModelMinBoundsHint(self._handle_type, show=True)
            event.setAccepted(True)  # don't propagate
            return
        else:
            self.setCursor(Qt.ClosedHandCursor)
            parent = self.parentItem()
            self._group.is_dragging = True
            self.event_start_position = event.pos()
            parent.setMovable(True)
            # ensure we handle window toggling during moves
            qApp.focusWindowChanged.connect(self.focusWindowChangedSlot)
            res = QGraphicsItem.mousePressEvent(parent, event)
            return res

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        if self.model_bounds:
            mTLx, mTLy, mBRx, mBRy = self.model_bounds
            poTL = parent.outline.rect().topLeft()
            poBR = parent.outline.rect().bottomRight()
            poTLx, poTLy = poTL.x(), poTL.y()
            poBRx, poBRy = poBR.x(), poBR.y()
            epos = event.scenePos()
            new_pos = self.item_start + epos - self.event_start_position
            h_w = self.half_width
            new_x = new_pos.x()+h_w
            new_y = new_pos.y()+h_w
            ht = self._handle_type
            if ht == HandleType.TOP_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((new_x_TL, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleType.TOP:
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((poTLx, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleType.TOP_RIGHT:
                new_y_TL = mTLy if new_y > mTLy else new_y
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((poTLx, new_y_TL), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleType.RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (new_x_BR, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM:
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((new_x_TL, poTLy), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                r = parent.reconfigureRect((new_x_TL, poTLy), ())
                self._group.alignHandles(r)
            else:
                raise NotImplementedError("handle_type %d not supported" % (ht))
        else:
            res = QGraphicsItem.mouseMoveEvent(parent, event)
            return res
    # end def

    def mouseReleaseEvent(self, event):
        if self.model_bounds:
            parent = self.parentItem()
            mTLx, mTLy, mBRx, mBRy = self.model_bounds
            poTL = parent.outline.rect().topLeft()
            poBR = parent.outline.rect().bottomRight()
            poTLx, poTLy = poTL.x(), poTL.y()
            poBRx, poBRy = poBR.x(), poBR.y()
            epos = event.scenePos()
            new_pos = self.item_start + epos - self.event_start_position
            h_w = self.half_width
            new_x = new_pos.x()+h_w
            new_y = new_pos.y()+h_w
            ht = self._handle_type
            if ht == HandleType.TOP_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((new_x_TL, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleType.TOP:
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((poTLx, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleType.TOP_RIGHT:
                new_y_TL = mTLy if new_y > mTLy else new_y
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((poTLx, new_y_TL), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleType.RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (new_x_BR, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM:
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((new_x_TL, poTLy), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleType.LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                r = parent.reconfigureRect((new_x_TL, poTLy), ())
                self._group.alignHandles(r)
            self.model_bounds = ()
            parent.showModelMinBoundsHint(self._handle_type, show=False)
        if self._group.is_dragging:
            self._group.is_dragging = False
            parent = self.parentItem()
            parent.setMovable(False)
            QGraphicsItem.mouseReleaseEvent(parent, event)
            parent.finishDrag()
        self.setCursor(Qt.OpenHandCursor)
    # end def

    def focusWindowChangedSlot(self, focus_window):
        self.finishDrag("I am released focus stylee")
    # end def

    def dragLeaveEvent(self, event):
        self.finishDrag("dragLeaveEvent")
    # end def

    def finishDrag(self, message):
        if self.model_bounds:
            self.model_bounds = ()
        if self._group.is_dragging:
            print(message)
            parent = self.parentItem()
            parent.setMovable(False)
            qApp.focusWindowChanged.disconnect(self.focusWindowChangedSlot)
            parent.finishDrag()
    # end def
# end class
