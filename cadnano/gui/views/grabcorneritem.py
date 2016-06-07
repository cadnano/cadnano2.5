from PyQt5.QtCore import QPointF, QRectF, Qt
from cadnano.gui.palette import getPenObj, getBrushObj
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PyQt5.QtWidgets import qApp

class GrabCornerItem(QGraphicsRectItem):
    def __init__(self, width, color, parent):
        super(GrabCornerItem, self).__init__(parent)
        self.width = width
        self.offset = QPointF(width, width)
        self.offset_x = QPointF(width, 0)
        self.offset_y = QPointF(0, width)
        self.is_grabbing = False
        self.setBrush(getBrushObj(color))
    # end def

    def mousePressEvent(self, event):
        print("mousePressEvent")
        parent = self.parentItem()
        self.is_grabbing = True
        self.drag_start_position = sp = event.pos()
        self.drag_last_position = sp
        parent.setMovable(True)
        # ensure we handle window toggling during moves
        qApp.focusWindowChanged.connect(self.focusWindowChangedSlot)
        res = QGraphicsItem.mousePressEvent(parent, event)
        return res

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        res = QGraphicsItem.mouseMoveEvent(parent, event)
        return res

    def mouseReleaseEvent(self, event):
        if self.is_grabbing:
            print("I am released")
            parent = self.parentItem()
            self.is_grabbing = False
            self.parentItem().setMovable(False)
            QGraphicsItem.mouseReleaseEvent(parent, event)
    # end def

    def focusWindowChangedSlot(self, focus_window):
        self.finishDrag("I am released focus stylee")
    # end def

    def dragLeaveEvent(self, event):
        self.finishDrag("dragLeaveEvent")
    # end def

    def finishDrag(self, message):
        if self.is_grabbing:
            print(message)
            self.is_grabbing = False
            self.parentItem().setMovable(False)
            qApp.focusWindowChanged.disconnect(self.focusWindowChangedSlot)
    # end def

    def setTopLeft(self, topleft):
        """
        Args:
            topleft (QPointF): top left corner
        """
        grabrect = QRectF(topleft, topleft + self.offset)
        self.setRect(grabrect)
    # end def

    def setBottomLeft(self, bottonleft):
        """
        Args:
            bottomleft (QPointF): bottom left corner
        """
        grabrect = QRectF(  bottonleft - self.offset_y,
                            bottonleft + self.offset_x)
        self.setRect(grabrect)
    # end def

    def setBottomRight(self, bottonright):
        """
        Args:
            bottomright (QPointF): bottom right corner
        """
        grabrect = QRectF(  bottonright - self.offset,
                            bottonright)
        self.setRect(grabrect)
    # end def

    def setTopRight(self, topright):
        """
        Args:
            top right (QPointF): top right corner
        """
        grabrect = QRectF(  topright - self.offset_x,
                            topright + self.offset_y)
        self.setRect(grabrect)
    # end def
# end class


