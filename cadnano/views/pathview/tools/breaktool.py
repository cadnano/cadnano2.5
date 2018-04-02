# -*- coding: utf-8 -*-
from PyQt5.QtCore import (
    QRectF,
    QPointF
)
from PyQt5.QtGui import (
    QPainterPath,
    QPolygonF
)
from PyQt5.QtWidgets import QGraphicsSceneHoverEvent

from cadnano.views.pathview import pathstyles as styles
from cadnano.gui.palette import getPenObj
from .abstractpathtool import AbstractPathTool
from cadnano.views.pathview import (
    PathVirtualHelixItemT,
    PathRootItemT,
    PathToolManagerT
)


_BW = styles.PATH_BASE_WIDTH
_PEN = getPenObj(styles.RED_STROKE, 1)
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

    def __init__(self, manager: PathToolManagerT):
        """
        Args:
            manager: Description
        """
        super(BreakTool, self).__init__(manager)
        self._is_top_strand: bool = True

    def __repr__(self) -> str:
        """
        Returns:
            string
        """
        return "break_tool"  # first letter should be lowercase

    def methodPrefix(self) -> str:
        """
        Returns:
            prefix string
        """
        return "breakTool"  # first letter should be lowercase

    def paint(self, painter, option, widget=None):
        """
        Args:
            painter (TYPE): Description
            option (TYPE): Description
            widget (None, optional): Description
        """
        AbstractPathTool.paint(self, painter, option, widget)
        painter.setPen(_PEN)
        if self._is_top_strand:
            painter.drawPath(_PATH_ARROW_RIGHT)
        else:
            painter.drawPath(_PATH_ARROW_LEFT)

    def setTopStrand(self, is_top: bool):
        """Called in hoverMovePathHelix to set whether breaktool is hovering
        over a top strand (goes 5' to 3' left to right) or bottom strand.

        Args:
            is_top: Description
        """
        self._is_top_strand = is_top

    def hoverMove(self, item: PathVirtualHelixItemT,
                        event: QGraphicsSceneHoverEvent,
                        flag: bool = None):
        """flag is for the case where an item in the path also needs to
        implement the hover method

        Args:
            item (TYPE): Description
            event (TYPE): Description
            flag (None, optional): Description
        """
        self.show()
        self.updateLocation(item, item.mapToScene(QPointF(event.pos())))
        pos_scene = item.mapToScene(QPointF(event.pos()))
        pos_item = item.mapFromScene(pos_scene)
        self.setTopStrand(self.helixIndex(pos_item)[1] == 0)
        new_position = self.helixPos(pos_item)
        if new_position is not None:
            self.setPos(new_position)
