# -*- coding: utf-8 -*-
from typing import (
    Optional,
    Tuple
)

from PyQt5.QtCore import (
    QRectF,
    QPointF
)
from PyQt5.QtGui import (
    QPen,
    QBrush
)

from cadnano import util
from cadnano.views.abstractitems import AbstractTool
from cadnano.views.pathview import pathstyles as styles
from cadnano.gui.palette import (
    getPenObj,
    getNoBrush
)
from cadnano.views.pathview import (
        PathToolManagerT,
        PathVirtualHelixItemT
)
from cadnano.cntypes import (
    DocT,
    WindowT,
    Vec2T
)


_BW: int = styles.PATH_BASE_WIDTH
_TOOL_RECT: QRectF = QRectF(0, 0, _BW, _BW)  # protected not private
_RECT: QRectF = QRectF(-styles.PATH_BASE_HL_STROKE_WIDTH,
               -styles.PATH_BASE_HL_STROKE_WIDTH,
               _BW + 2 * styles.PATH_BASE_HL_STROKE_WIDTH,
               _BW + 2 * styles.PATH_BASE_HL_STROKE_WIDTH)
_PEN: QPen = getPenObj(styles.RED_STROKE, styles.PATH_BASE_HL_STROKE_WIDTH)
_BRUSH: QBrush = getNoBrush()


class AbstractPathTool(AbstractTool):
    """Abstract base class to be subclassed by all other pathview tools.

    Attributes:
        manager: Description
    """

    def __init__(self, manager: PathToolManagerT):
        """Summary

        Args:
            manager: Description
        """
        super(AbstractPathTool, self).__init__(None)
        self.manager: PathToolManagerT = manager
        self._window: DocT = manager.window
        self._active: bool = False
        self._last_location = None
        self._rect: QRectF = _RECT
        self._pen: QPen = _PEN
        self.hide()

    ######################## Drawing #######################################
    def paint(self, painter, option, widget=None):
        """Summary

        Args:
            painter (TYPE): Description
            option (TYPE): Description
            widget (None, optional): Description

        Returns:
            TYPE: Description
        """
        painter.setPen(self._pen)
        painter.setBrush(_BRUSH)
        painter.drawRect(_TOOL_RECT)

    def boundingRect(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._rect

    ######################### Positioning and Parenting ####################
    def updateLocation(self, virtual_helix_item: PathVirtualHelixItemT,
                            scene_pos: QPointF,
                            *args):
        """Takes care of caching the location so that a tool switch
        outside the context of an event will know where to
        position the new tool and snaps self's pos to the upper
        left hand corner of the base the user is mousing over.

        Args:
            virtual_helix_item: PathVirtualHelixItem
            scene_pos: point in the scene
            *args: DESCRIPTION
        """
        if virtual_helix_item:
            if self.parentObject() != virtual_helix_item:
                self.setParentItem(virtual_helix_item)
            self._last_location = (virtual_helix_item, scene_pos)
            pos_item = virtual_helix_item.mapFromScene(scene_pos)
            pos = self.helixPos(pos_item)
            if pos is not None:
                if pos != self.pos():
                    self.setPos(pos)
                self.update(self.boundingRect())
        else:
            self._last_location = None
            if self.isVisible():
                self.hide()
    # end def

    def lastLocation(self) -> Optional[Tuple[PathVirtualHelixItemT, QPointF]]:
        """A tool's last_location consists of a :class`PathVirtualHelixItem` and
        a scene pos (:class:`QPoint`) representing the last known location of
        the mouse.

        It can be used to provide visual continuity when switching tools.
        When the new tool is selected, this method will be invoked by
        calling `updateLocation(*old_tool.lastLocation())`.

        Returns:
            location: ``(virtual_helix_item, QPointF)`` representing the last
                known location of the mouse for purposes of positioning
                the graphic of a new tool on switching tools (the tool
                will have called on it)

        """
        return self._last_location

    def setActive(self, will_be_active: bool, old_tool=None):
        """
        Called by PathToolManager.setActiveTool when the tool becomes
        active. Used, for example, to show/hide tool-specific ui elements.

        Args:
            will_be_active (TYPE): Description
            old_tool (None, optional): Description
        """
        if self._active and not will_be_active:
            self.deactivate()
        self._active = will_be_active

    def deactivate(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.hide()

    def isActive(self) -> bool:
        """Returns isActive
        """
        return self._active

    def widgetClicked(self):
        """Called every time a widget representing self gets clicked,
        not just when changing tools.
        """

    ####################### Coordinate Utilities ###########################
    def baseAtPoint(self, virtual_helix_item: PathVirtualHelixItemT,
                        pt: QPointF) -> Tuple[bool, int, int]:
        """Returns the ``(is_fwd, base_idx, strand_idx)`` corresponding
        to pt in virtual_helix_item.

        Args:
            virtual_helix_item: :class:`PathVirtualHelixItem`
            pt: Point on helix
        """
        x, strand_idx = self.helixIndex(pt)

        is_fwd = False if util.clamp(strand_idx, 0, 1) else True
        return (is_fwd, x, strand_idx)

    def helixIndex(self, point: QPointF) -> Vec2T:
        """Returns the (row, col) of the base which point lies within.

        Returns:
            point (tuple) in virtual_helix_item coordinates

        Args:
            point (TYPE): Description
        """
        x = int(int(point.x()) / _BW)
        y = int(int(point.y()) / _BW)
        return (x, y)
    # end def

    def helixPos(self, point):
        """
        Snaps a point to the upper left corner of the base
        it is within.
        point is in virtual_helix_item coordinates

        Args:
            point (TYPE): Description
        """
        col = int(int(point.x()) / _BW)
        row = int(int(point.y()) / _BW)
        # Doesn't know numBases, can't check if point is too far right
        if col < 0 or row < 0 or row > 1:
            return None
        return QPointF(col * _BW, row * _BW)
    # end def

    def hoverLeaveEvent(self, event):
        """
        flag is for the case where an item in the path also needs to
        implement the hover method

        Args:
            event (TYPE): Description
        """
        self.hide()
    # end def
# end class
