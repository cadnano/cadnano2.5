from PyQt5.QtCore import QPointF, QRectF, Qt
from cadnano.gui.palette import getPenObj, getBrushObj
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem

class GrabCornerItem(QGraphicsRectItem):
    def __init__(self, width, parent):
        super(GrabCornerItem, self).__init__(parent)
        self.width = width
        self.offset = QPointF(width, width)
        self.offset_x = QPointF(width, 0)
        self.offset_y = QPointF(0, width)
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


