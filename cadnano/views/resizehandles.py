# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, QPointF, QRectF, Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, qApp
from PyQt5.QtWidgets import QGraphicsTextItem
from cadnano.gui.palette import getBrushObj, getPenObj
from cadnano.proxies.cnenum import Axis, HandleType
from . import styles


class ResizeHandleGroup(QObject):
    """Provides the ability to move and resize the parent."""
    def __init__(self, parent_outline_rect, width, color, is_resizable,
                 handle_types, parent_item, translates_in=None, show_coords=False):
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
        self.parent_item = parent_item
        if translates_in is None:
            self.translates_in = Axis.X | Axis.Y
        else:
            self.translates_in = translates_in
        self.show_coords = show_coords

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
            t_pt = QPointF(o_rect.center().x(), o_rect.top())
            self._t.setPos(t_pt - self.half_offset)
        if self.handle_types & HandleType.BOTTOM:
            b_pt = QPointF(o_rect.center().x(), o_rect.bottom())
            self._b.setPos(b_pt - self.half_offset)
        if self.handle_types & HandleType.LEFT:
            l_pt = QPointF(o_rect.left(), o_rect.center().y())
            self._l.setPos(l_pt - self.half_offset)
        if self.handle_types & HandleType.RIGHT:
            r_pt = QPointF(o_rect.right(), o_rect.center().y())
            self._r.setPos(r_pt - self.half_offset)
        if self.handle_types & HandleType.TOP_LEFT:
            tl_pt = o_rect.topLeft()
            self._tl.setPos(tl_pt - self.half_offset)
        if self.handle_types & HandleType.TOP_RIGHT:
            tr_pt = o_rect.topRight()
            self._tr.setPos(tr_pt - self.half_offset)
        if self.handle_types & HandleType.BOTTOM_LEFT:
            bl_pt = o_rect.bottomLeft()
            self._bl.setPos(bl_pt - self.half_offset)
        if self.handle_types & HandleType.BOTTOM_RIGHT:
            br_pt = o_rect.bottomRight()
            self._br.setPos(br_pt - self.half_offset)

        if self.show_coords:
            # t_x, t_y = self.parent_item.getModelPos(t_pt)
            # b_x, b_y = self.parent_item.getModelPos(b_pt)
            # l_x, l_y = self.parent_item.getModelPos(l_pt)
            # r_x, r_y = self.parent_item.getModelPos(r_pt)
            # tl_x, tl_y = self.parent_item.getModelPos(tl_pt)
            # bl_x, bl_y = self.parent_item.getModelPos(bl_pt)
            # tr_x, tr_y = self.parent_item.getModelPos(tr_pt)
            # br_x, br_y = self.parent_item.getModelPos(br_pt)
            # xy_html = "<font color='#cc0000'>{:.2f}</font>, " +\
            #           "<font color='#007200'>{:.2f}</font>"
            # self._t.label.updateText(xy_html.format(t_x, t_y))
            # self._b.label.updateText(xy_html.format(b_x, b_y))
            # self._l.label.updateText(xy_html.format(l_x, l_y))
            # self._r.label.updateText(xy_html.format(r_x, r_y))
            # self._tl.label.updateText(xy_html.format(tl_x, tl_y))
            # self._tr.label.updateText(xy_html.format(tr_x, tr_y))
            # self._bl.label.updateText(xy_html.format(bl_x, bl_y))
            # self._br.label.updateText(xy_html.format(br_x, br_y))
            t_x, t_y = self.parent_item.getModelPos(t_pt)
            b_x, b_y = self.parent_item.getModelPos(b_pt)
            l_x, l_y = self.parent_item.getModelPos(l_pt)
            r_x, r_y = self.parent_item.getModelPos(r_pt)
            x_html = "<font color='#cc0000'>{:.2f}</font>"
            y_html = "<font color='#007200'>{:.2f}</font>"
            self._t.label.updateText(y_html.format(t_y))
            self._b.label.updateText(y_html.format(b_y))
            self._l.label.updateText(x_html.format(l_x))
            self._r.label.updateText(x_html.format(r_x))
    # end def

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
        for handle in [self._t, self._b, self._l, self._r,
                       self._tl, self._tr, self._bl, self._br]:
            if handle:
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

    def getHandle(self, handle_type):
        if handle_type == HandleType.TOP:
            return self._t
        elif handle_type == HandleType.BOTTOM:
            return self._b
        elif handle_type == HandleType.LEFT:
            return self._l
        elif handle_type == HandleType.RIGHT:
            return self._r
        elif handle_type == HandleType.TOP_LEFT:
            return self._tl
        elif handle_type == HandleType.TOP_RIGHT:
            return self._tr
        elif handle_type == HandleType.BOTTOM_LEFT:
            return self._bl
        elif handle_type == HandleType.BOTTOM_RIGHT:
            return self._br
        else:
            raise LookupError("HandleType not found", handle_type)

    def updateText(self, handle_types, text):
        if handle_types & HandleType.TOP and self._t:
            self._t.label.updateText(text)
        if handle_types & HandleType.BOTTOM and self._b:
            self._b.label.updateText(text)
        if handle_types & HandleType.LEFT and self._l:
            self._l.label.updateText(text)
        if handle_types & HandleType.RIGHT and self._r:
            self._r.label.updateText(text)
        if handle_types & HandleType.TOP_LEFT and self._tl:
            self._tl.label.updateText(text)
        if handle_types & HandleType.TOP_RIGHT and self._tr:
            self._tr.label.updateText(text)
        if handle_types & HandleType.BOTTOM_LEFT and self._bl:
            self._bl.label.updateText(text)
        if handle_types & HandleType.BOTTOM_RIGHT and self._br:
            self._br.label.updateText(text)
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
        self.can_move_x = handle_group.translates_in & Axis.X
        self.can_move_y = handle_group.translates_in & Axis.Y

        self.setBrush(getBrushObj(styles.RESIZEHANDLE_FILL_COLOR))
        self.setPen(getPenObj(color, 0))
        self.setRect(QRectF(0, 0, w, w))

        self.label = HandleItemLabel(self)

        self.event_start_position = QPointF(0, 0)
        self.event_scene_start_position = QPointF(0, 0)

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

    def handleGroup(self):
        return self._group
    # end def

    def handleType(self):
        return self._handle_type
    # end def

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
            event.setAccepted(True)  # don't propagate
            return res
    # end def

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        epos = event.scenePos()
        h_w = self.half_width

        if self.model_bounds:
            mTLx, mTLy, mBRx, mBRy = self.model_bounds
            poTL = parent.outline.rect().topLeft()
            poBR = parent.outline.rect().bottomRight()
            poTLx, poTLy = poTL.x(), poTL.y()
            poBRx, poBRy = poBR.x(), poBR.y()
            new_pos = self.item_start + epos - self.event_start_position
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
            event.setAccepted(True)
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
                r = parent.reconfigureRect((new_x_TL, new_y_TL), (), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.TOP:
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((poTLx, new_y_TL), (), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.TOP_RIGHT:
                new_y_TL = mTLy if new_y > mTLy else new_y
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((poTLx, new_y_TL), (new_x_BR, poBRy), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((), (new_x_BR, poBRy), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (new_x_BR, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM:
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (poBRx, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.BOTTOM_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((new_x_TL, poTLy), (poBRx, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleType.LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                r = parent.reconfigureRect((new_x_TL, poTLy), (), finish=True)
                self._group.alignHandles(r)
            self.model_bounds = ()
            parent.showModelMinBoundsHint(self._handle_type, show=False)
        if self._group.is_dragging:
            self._group.is_dragging = False
            parent = self.parentItem()
            parent.setMovable(False)
            parent.finishDrag()
        self.setCursor(Qt.OpenHandCursor)
        # NOTE was QGraphicsItem.mouseReleaseEvent(parent, event) but that errored
        # NC 2018.01.29 so that seemd to fix the error
        return QGraphicsItem.mouseReleaseEvent(self, event)
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
            # print(message)
            parent = self.parentItem()
            parent.setMovable(False)
            qApp.focusWindowChanged.disconnect(self.focusWindowChangedSlot)
            parent.finishDrag()
    # end def
# end class


class HandleItemLabel(QGraphicsTextItem):
    """Text label for HandleItems. Manages its position based
    on handle type, a bit further past the handle position.

    Attributes:
        is_fwd (TYPE): Description
    """
    _COLOR = styles.RESIZEHANDLE_LABEL_COLOR
    _FONT = styles.RESIZEHANDLE_LABEL_FONT
    _FM = QFontMetrics(_FONT)

    def __init__(self, handle):
        super(QGraphicsTextItem, self).__init__(handle)
        self._handle = handle
        self.setFont(self._FONT)
        # self.setBrush(getBrushObj(self._COLOR))
    # end def

    def updateText(self, text):
        str_txt = str(text)
        self.setHtml(str_txt)

        # tBR = self._FM.tightBoundingRect(str_txt)
        br = self.boundingRect()
        text_width = br.width()
        text_height = br.height()
        handle_type = self._handle.handleType()
        if handle_type & (HandleType.LEFT |
                          HandleType.TOP_LEFT |
                          HandleType.BOTTOM_LEFT):
            x = -self._handle.half_width - text_width
        elif handle_type & (HandleType.RIGHT |
                            HandleType.TOP_RIGHT |
                            HandleType.BOTTOM_RIGHT):
            x = self._handle.width*1.5
        elif handle_type & (HandleType.TOP | HandleType.BOTTOM):
            x = self._handle.half_width-text_width/2
        else:
            x = self.pos().x()
        if handle_type & (HandleType.TOP |
                          HandleType.TOP_LEFT |
                          HandleType.TOP_RIGHT):
            y = -self._handle.half_width-text_height
        elif handle_type & (HandleType.BOTTOM |
                            HandleType.BOTTOM_LEFT |
                            HandleType.BOTTOM_RIGHT):
            y = self._handle.half_width + text_height/2
        elif handle_type & (HandleType.LEFT | HandleType.RIGHT):
            y = self._handle.half_width-text_height/2
        else:
            y = self.pos().y()
        self.setPos(QPointF(x, y))
    # end def
# end class
