# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, QPointF, QRectF, Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, qApp
from PyQt5.QtWidgets import QGraphicsTextItem
from cadnano.gui.palette import getBrushObj, getPenObj
from cadnano.proxies.cnenum import AxisEnum, HandleEnum
from . import styles
HANDLE_ITEM_ATTRS = ['_t', '_b', '_l', '_r', '_tl', '_tr', '_bl', '_br']
HANDLE_ENUMS = [HandleEnum.TOP,
                HandleEnum.BOTTOM,
                HandleEnum.LEFT,
                HandleEnum.RIGHT,
                HandleEnum.TOP_LEFT,
                HandleEnum.TOP_RIGHT,
                HandleEnum.BOTTOM_LEFT,
                HandleEnum.BOTTOM_RIGHT
                ]
HANDLE_ITEM_MAP = {x: y for x, y in zip(HANDLE_ENUMS, HANDLE_ITEM_ATTRS)}

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
            self.translates_in = AxisEnum.X | AxisEnum.Y
        else:
            self.translates_in = translates_in
        self.show_coords = show_coords

        self.handle_types = handle_types

        active_handle_items = []
        for enum_type, item in zip(HANDLE_ENUMS, HANDLE_ITEM_ATTRS):
            if handle_types & enum_type:
                value = HandleItem(enum_type, w, color, self, parent_item)
                active_handle_items.append(value)
            else:
                value = None
            setattr(self, item, value)
        self.active_handle_items = active_handle_items

        self.alignHandles(parent_outline_rect)
    # end def

    def alignHandles(self, o_rect):
        self.parent_outline_rect = o_rect

        if self.handle_types & HandleEnum.TOP:
            t_pt = QPointF(o_rect.center().x(), o_rect.top())
            self._t.setPos(t_pt - self.half_offset)
        if self.handle_types & HandleEnum.BOTTOM:
            b_pt = QPointF(o_rect.center().x(), o_rect.bottom())
            self._b.setPos(b_pt - self.half_offset)
        if self.handle_types & HandleEnum.LEFT:
            l_pt = QPointF(o_rect.left(), o_rect.center().y())
            self._l.setPos(l_pt - self.half_offset)
        if self.handle_types & HandleEnum.RIGHT:
            r_pt = QPointF(o_rect.right(), o_rect.center().y())
            self._r.setPos(r_pt - self.half_offset)
        if self.handle_types & HandleEnum.TOP_LEFT:
            tl_pt = o_rect.topLeft()
            self._tl.setPos(tl_pt - self.half_offset)
        if self.handle_types & HandleEnum.TOP_RIGHT:
            tr_pt = o_rect.topRight()
            self._tr.setPos(tr_pt - self.half_offset)
        if self.handle_types & HandleEnum.BOTTOM_LEFT:
            bl_pt = o_rect.bottomLeft()
            self._bl.setPos(bl_pt - self.half_offset)
        if self.handle_types & HandleEnum.BOTTOM_RIGHT:
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
            t_x, t_y, _ = self.parent_item.getModelPos(t_pt)
            b_x, b_y, _ = self.parent_item.getModelPos(b_pt)
            l_x, l_y, _ = self.parent_item.getModelPos(l_pt)
            r_x, r_y, _ = self.parent_item.getModelPos(r_pt)
            x_html = "<font color='#cc0000'>{:.2f}</font>"
            y_html = "<font color='#007200'>{:.2f}</font>"
            self._t.label.updateText(y_html.format(t_y))
            self._b.label.updateText(y_html.format(b_y))
            self._l.label.updateText(x_html.format(l_x))
            self._r.label.updateText(x_html.format(r_x))
    # end def

    def destroyItem(self):
        for item in HANDLE_ITEM_ATTRS:
            handle_item = getattr(self, item)
            if handle_item is not None:
                handle_item.destroyItem()
                setattr(self, item, None)
        self.active_handle_items = None
        self.parent_item = None

        # NOTE THIS OBJECT AS A QOBJECT HAS NO SCENE SO COMMENTED OUT
        # self.scene().removeItem(self)
    # end def

    def removeHandles(self):
        for item in HANDLE_ITEM_ATTRS:
            setattr(self, item, None)
    # end def

    def setPens(self, pen):
        for handle in self.active_handle_items:
            handle.setPen(pen)
    # end def

    def setZValue(self, z):
        for item in self.active_handle_items:
            item.setZValue(z)
    # end def

    def setParentItemAll(self, new_parent):
        for item in self.active_handle_items:
            item.setParentItem(new_parent)
    # end def

    def getHandle(self, handle_type):
        try:
            handle_item_attr = HANDLE_ITEM_MAP[handle_type]
            handle_item = getattr(self, handle_item_attr)
            return handle_item
        except:
            raise LookupError("HandleEnum not found", handle_type)
    # end def

    def updateText(self, handle_types, text):
        for handle_type in HANDLE_ENUMS:
            if handle_types & handle_type:
                handle_item = self.getHandle(getHandle)
                if handle_item is not None:
                    handle_item.label.updateText(text)
# end class


class HandleItem(QGraphicsRectItem):
    """Provides the ability to resize the document."""

    def __init__(self, handle_type, width, color, handle_group, parent):
        ''' parent is a :class:`QGraphicsItem` such as a :class:`NucleicAcidPartItem`
        '''
        super(HandleItem, self).__init__(parent)
        self.setAcceptHoverEvents(True)
        self._handle_type = handle_type
        self._group = handle_group
        self.width = w = width
        self.half_width = w/2
        self.align_offset = parent._BOUNDING_RECT_PADDING
        self.model_bounds = ()
        self.can_move_x = handle_group.translates_in & AxisEnum.X
        self.can_move_y = handle_group.translates_in & AxisEnum.Y

        self.setBrush(getBrushObj(styles.RESIZEHANDLE_FILL_COLOR))
        self.setPen(getPenObj(color, 0))
        self.setRect(QRectF(0, 0, w, w))

        self.label = HandleItemLabel(self)

        self.event_start_position = QPointF(0, 0)
        self.event_scene_start_position = QPointF(0, 0)

        if handle_type & (HandleEnum.LEFT | HandleEnum.RIGHT):
            self._resize_cursor = Qt.SizeHorCursor
        elif handle_type & (HandleEnum.TOP | HandleEnum.BOTTOM):
            self._resize_cursor = Qt.SizeVerCursor
        elif handle_type & (HandleEnum.TOP_LEFT | HandleEnum.BOTTOM_RIGHT):
            self._resize_cursor = Qt.SizeFDiagCursor
        elif handle_type & (HandleEnum.TOP_RIGHT | HandleEnum.BOTTOM_LEFT):
            self._resize_cursor = Qt.SizeBDiagCursor
        else:
            self._resize_cursor = Qt.ClosedHandCursor
    # end def

    def destroyItem(self):
        self._group = None
        self.label.destroyItem()
        self.label = None
        self.scene().removeItem(self)
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
            po_rect = parent.outline.rect()
            poTL = po_rect.topLeft()
            poBR = po_rect.bottomRight()
            poTLx, poTLy = poTL.x(), poTL.y()
            poBRx, poBRy = poBR.x(), poBR.y()
            new_pos = self.item_start + epos - self.event_start_position
            new_x = new_pos.x()+h_w
            new_y = new_pos.y()+h_w
            ht = self._handle_type
            if ht == HandleEnum.TOP_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((new_x_TL, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleEnum.TOP:
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((poTLx, new_y_TL), ())
                self._group.alignHandles(r)
            elif ht == HandleEnum.TOP_RIGHT:
                new_y_TL = mTLy if new_y > mTLy else new_y
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((poTLx, new_y_TL), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleEnum.RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((), (new_x_BR, poBRy))
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM_RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (new_x_BR, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM:
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((new_x_TL, poTLy), (poBRx, new_y_BR))
                self._group.alignHandles(r)
            elif ht == HandleEnum.LEFT:
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
            if ht == HandleEnum.TOP_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((new_x_TL, new_y_TL), (), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.TOP:
                new_y_TL = mTLy if new_y > mTLy else new_y
                r = parent.reconfigureRect((poTLx, new_y_TL), (), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.TOP_RIGHT:
                new_y_TL = mTLy if new_y > mTLy else new_y
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((poTLx, new_y_TL), (new_x_BR, poBRy), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                r = parent.reconfigureRect((), (new_x_BR, poBRy), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM_RIGHT:
                new_x_BR = mBRx if new_x < mBRx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (new_x_BR, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM:
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((), (poBRx, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.BOTTOM_LEFT:
                new_x_TL = mTLx if new_x > mTLx else new_x
                new_y_BR = mBRy if new_y < mBRy else new_y
                r = parent.reconfigureRect((new_x_TL, poTLy), (poBRx, new_y_BR), finish=True)
                self._group.alignHandles(r)
            elif ht == HandleEnum.LEFT:
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

    def destroyItem(self):
        self._handle = None
        self.scene().removeItem(self)
    # end def

    def updateText(self, text):
        str_txt = str(text)
        self.setHtml(str_txt)

        # tBR = self._FM.tightBoundingRect(str_txt)
        br = self.boundingRect()
        text_width = br.width()
        text_height = br.height()
        handle_type = self._handle.handleType()
        if handle_type & (HandleEnum.LEFT |
                          HandleEnum.TOP_LEFT |
                          HandleEnum.BOTTOM_LEFT):
            x = -self._handle.half_width - text_width
        elif handle_type & (HandleEnum.RIGHT |
                            HandleEnum.TOP_RIGHT |
                            HandleEnum.BOTTOM_RIGHT):
            x = self._handle.width*1.5
        elif handle_type & (HandleEnum.TOP | HandleEnum.BOTTOM):
            x = self._handle.half_width-text_width/2
        else:
            x = self.pos().x()
        if handle_type & (HandleEnum.TOP |
                          HandleEnum.TOP_LEFT |
                          HandleEnum.TOP_RIGHT):
            y = -self._handle.half_width-text_height
        elif handle_type & (HandleEnum.BOTTOM |
                            HandleEnum.BOTTOM_LEFT |
                            HandleEnum.BOTTOM_RIGHT):
            y = self._handle.half_width + text_height/2
        elif handle_type & (HandleEnum.LEFT | HandleEnum.RIGHT):
            y = self._handle.half_width-text_height/2
        else:
            y = self.pos().y()
        self.setPos(QPointF(x, y))
    # end def
# end class
