from .abstractpathtool import AbstractPathTool
from cadnano.gui.views.pathview import pathstyles as styles
import cadnano.util as util

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QFont, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem

_BW = styles.PATH_BASE_WIDTH
_PEN = QPen(styles.RED_STROKE, 1)
_RECT = QRectF(0, 0, _BW, _BW)
_PATH_ARROW_LEFT = QPainterPath()
_L3_POLY = QPolygonF()
_L3_POLY.append(QPointF(_BW, 0))
_L3_POLY.append(QPointF(0.25 * _BW, 0.5 * _BW))
_L3_POLY.append(QPointF(_BW, _BW))
_PATH_ARROW_LEFT.addPolygon(_L3_POLY)
_PATH_ARROW_RIGHT = QPainterPath()
_R3_POLY = QPolygonF()  # right-hand 3' arr
_R3_POLY.append(QPointF(0, 0))
_R3_POLY.append(QPointF(0.75 * _BW, 0.5 * _BW))
_R3_POLY.append(QPointF(0, _BW))
_PATH_ARROW_RIGHT.addPolygon(_R3_POLY)


class BreakTool(AbstractPathTool):
    """
    docstring for BreakTool
    """
    def __init__(self, controller):
        super(BreakTool, self).__init__(controller)
        self._is_top_strand = True

    def __repr__(self):
        return "break_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "breakTool"  # first letter should be lowercase

    def paint(self, painter, option, widget=None):
        AbstractPathTool.paint(self, painter, option, widget)
        painter.setPen(_PEN)
        if self._is_top_strand:
            painter.drawPath(_PATH_ARROW_RIGHT)
        else:
            painter.drawPath(_PATH_ARROW_LEFT)

    def setTopStrand(self, is_top):
        """
        Called in hoverMovePathHelix to set whether breaktool is hovering
        over a top strand (goes 5' to 3' left to right) or bottom strand.
        """
        self._is_top_strand = is_top

    def hoverMove(self, item, event, flag=None):
        """
        flag is for the case where an item in the path also needs to
        implement the hover method
        """
        self.show()
        self.updateLocation(item, item.mapToScene(QPointF(event.pos())))
        pos_scene = item.mapToScene(QPointF(event.pos()))
        pos_item = item.mapFromScene(pos_scene)
        self.setTopStrand(self.helixIndex(pos_item)[1] == 0)
        new_position = self.helixPos(pos_item)
        if new_position != None:
            self.setPos(new_position)

