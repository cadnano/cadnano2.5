# -*- coding: utf-8 -*-
from PyQt5.QtCore import QPointF, QRectF, Qt
from cadnano.gui.palette import getBrushObj
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PyQt5.QtWidgets import qApp

TOP_LEFT = 0
BOTTOM_LEFT = 1
BOTTOM_RIGHT = 2
TOP_RIGHT = 4


class GrabCornerItem(QGraphicsRectItem):
    def __init__(self, width, color, is_resizable, parent):
        super(GrabCornerItem, self).__init__(parent)
        self.setRect(QRectF(0, 0, width, width))
        self.width = width
        self.half_width = width/2
        self.offset = QPointF(width, width)
        self.offset_x = QPointF(width, 0)
        self.offset_y = QPointF(0, width)

        self.is_grabbing = False
        self.setBrush(getBrushObj(color))
        self.is_resizable = is_resizable
        self.model_bounds = ()
        self.corner_type = TOP_LEFT
    # end def

    def mousePressEvent(self, event):
        # print("mousePressEvent")
        if event.button() == Qt.RightButton:
            return
        parent = self.parentItem()
        if self.is_resizable and event.modifiers() & Qt.ShiftModifier:
            self.model_bounds = parent.getModelBounds()
            # print("We are resizing", self.model_bounds)
            self.event_start_position = event.scenePos()
            self.item_start = self.pos()
            return
        else:
            parent = self.parentItem()
            self.is_grabbing = True
            self.event_start_position = event.pos()
            parent.setMovable(True)
            # ensure we handle window toggling during moves
            qApp.focusWindowChanged.connect(self.focusWindowChangedSlot)
            res = QGraphicsItem.mousePressEvent(parent, event)
            return res

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        if self.model_bounds:
            xTL, yTL, xBR, yBR = self.model_bounds
            ct = self.corner_type
            epos = event.scenePos()
            # print(epos, self.item_start)
            # print(xTL, self.item_start.x())
            new_pos = self.item_start + epos - self.event_start_position
            new_x = new_pos.x()
            new_y = new_pos.y()
            hwidth = self.half_width
            if ct == TOP_LEFT:
                new_x_TL = xTL - hwidth if new_x + hwidth > xTL else new_x
                new_y_TL = yTL - hwidth if new_y + hwidth > yTL else new_y
                tl, _ = parent.reconfigureRect((new_x_TL + hwidth, new_y_TL + hwidth), ())
                self.alignPos(*tl)
            elif ct == BOTTOM_RIGHT:
                new_x_BR = xBR + hwidth if new_x + hwidth < xBR else new_x
                new_y_BR = yBR + hwidth if new_y + hwidth < yBR else new_y
                _, br = parent.reconfigureRect((), (new_x_BR + hwidth, new_y_BR + hwidth))
                self.alignPos(*br)
            else:
                raise NotImplementedError("corner_type %d not supported" % (ct))
        else:
            res = QGraphicsItem.mouseMoveEvent(parent, event)
            return res
    # end def

    def alignPos(self, new_x, new_y):
        ct = self.corner_type
        hwidth = self.half_width
        if ct == TOP_LEFT:
            new_x_TL = new_x - hwidth
            new_y_TL = new_y - hwidth
            self.setPos(new_x_TL, new_y_TL)
        elif ct == BOTTOM_RIGHT:
            new_x_BR = new_x - hwidth
            new_y_BR = new_y - hwidth
            self.setPos(new_x_BR, new_y_BR)
    # end def

    def mouseReleaseEvent(self, event):
        if self.model_bounds:
            self.model_bounds = ()
        if self.is_grabbing:
            # print("I am released")
            self.is_grabbing = False
            parent = self.parentItem()
            parent.setMovable(False)
            QGraphicsItem.mouseReleaseEvent(parent, event)
            parent.finishDrag()
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
        if self.is_grabbing:
            print(message)
            self.is_grabbing = False
            parent = self.parentItem()
            parent.setMovable(False)
            qApp.focusWindowChanged.disconnect(self.focusWindowChangedSlot)
            parent.finishDrag()
    # end def

    def setTopLeft(self, topleft):
        """
        Args:
            topleft (QPointF): top left corner
        """
        self.setPos(topleft)
        self.corner_type = TOP_LEFT
    # end def

    def setBottomLeft(self, bottonleft):
        """
        Args:
            bottomleft (QPointF): bottom left corner
        """
        self.setPos(bottonleft - self.offset_y)
        self.corner_type = BOTTOM_LEFT
    # end def

    def setBottomRight(self, bottonright):
        """
        Args:
            bottomright (QPointF): bottom right corner
        """
        self.setPos(bottonright - self.offset)
        self.corner_type = BOTTOM_RIGHT
    # end def

    def setTopRight(self, topright):
        """
        Args:
            top right (QPointF): top right corner
        """
        self.setPos(topright - self.offset_x)
        self.corner_type = TOP_RIGHT
    # end def
# end class
