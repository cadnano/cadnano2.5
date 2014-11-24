from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.enum import StrandType

import cadnano.util as util

from PyQt5.QtCore import QRectF, Qt, QPointF

from PyQt5.QtGui import QBrush, QPen, QFont
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsItemGroup, QGraphicsObject

_BW = styles.PATH_BASE_WIDTH
_TOOL_RECT = QRectF(0, 0, _BW, _BW)  # protected not private
_RECT = QRectF(-styles.PATH_BASE_HL_STROKE_WIDTH,\
               -styles.PATH_BASE_HL_STROKE_WIDTH,\
               _BW + 2*styles.PATH_BASE_HL_STROKE_WIDTH,\
               _BW + 2*styles.PATH_BASE_HL_STROKE_WIDTH)
_PEN = QPen(styles.RED_STROKE, styles.PATH_BASE_HL_STROKE_WIDTH)
_BRUSH = QBrush(Qt.NoBrush)

# There's a bug where C++ will free orphaned graphics items out from
# under pyqt. To avoid this, "_mother" adopts orphaned graphics items.
# _mother = QGraphicsItemGroup()


class AbstractPathTool(QGraphicsObject):
    """Abstract base class to be subclassed by all other pathview tools."""
    def __init__(self, controller, parent=None):
        super(AbstractPathTool, self).__init__(parent)
        self._controller = controller
        self._window = controller.window
        self._active = False
        self._last_location = None
        self._rect = _RECT
        self._pen = _PEN
        self.hide()

    ######################## Drawing #######################################
    def paint(self, painter, option, widget=None):
        painter.setPen(self._pen)
        painter.setBrush(_BRUSH)
        painter.drawRect(_TOOL_RECT)

    def boundingRect(self):
        return self._rect

    ######################### Positioning and Parenting ####################
    def hoverEnterVirtualHelixItem(self, virtual_helix_item, event):
        self.updateLocation(virtual_helix_item, virtual_helix_item.mapToScene(QPointF(event.pos())))

    def hoverLeaveVirtualHelixItem(self, virtual_helix_item, event):
        self.updateLocation(None, virtual_helix_item.mapToScene(QPointF(event.pos())))

    def hoverMoveVirtualHelixItem(self, virtual_helix_item, event, flag=None):
        self.updateLocation(virtual_helix_item, virtual_helix_item.mapToScene(QPointF(event.pos())))

    def updateLocation(self, virtual_helix_item, scene_pos, *varargs):
        """Takes care of caching the location so that a tool switch
        outside the context of an event will know where to
        position the new tool and snaps self's pos to the upper
        left hand corner of the base the user is mousing over"""
        if virtual_helix_item:
            if self.parentObject() != virtual_helix_item:
                self.setParentItem(virtual_helix_item)
            self._last_location = (virtual_helix_item, scene_pos)
            pos_item = virtual_helix_item.mapFromScene(scene_pos)
            pos = self.helixPos(pos_item)
            if pos != None:
                if pos != self.pos():
                    self.setPos(pos)
                self.update(self.boundingRect())
                # if not self.isVisible():
                #     self.show()
                #     pass
        else:
            self._last_location = None
            if self.isVisible():
                self.hide()
            # if self.parentItem() != _mother:
            #     self.setParentItem(_mother)

    def lastLocation(self):
        """A tuple (virtual_helix_item, QPoint) representing the last
        known location of the mouse for purposes of positioning
        the graphic of a new tool on switching tools (the tool
        will have updateLocation(*old_tool.lastLocation()) called
        on it)"""
        return self._last_location

    def setActive(self, will_be_active, old_tool=None):
        """
        Called by PathToolManager.setActiveTool when the tool becomes
        active. Used, for example, to show/hide tool-specific ui elements.
        """
        # if self.isActive() and not will_be_active:
        #     self.setParentItem(_mother)
        #     self.hide()
        if self._active and not will_be_active:
            self.deactivate()
        self._active = will_be_active
        # self._pen = _PEN

    def deactivate(self):
        self.hide()

    def isActive(self):
        """Returns isActive"""
        return self._active
        # return self._active != _mother

    def widgetClicked(self):
        """Called every time a widget representing self gets clicked,
        not just when changing tools."""
        pass

    ####################### Coordinate Utilities ###########################
    def baseAtPoint(self, virtual_helix_item, pt):
        """Returns the (strand_type, base_idx) corresponding
        to pt in virtual_helix_item."""
        x, strand_idx = self.helixIndex(pt)
        vh = virtual_helix_item.virtualHelix()
        if vh.isEvenParity():
            strand_type = (StrandType.SCAFFOLD, StrandType.STAPLE)[util.clamp(strand_idx, 0, 1)]
        else:
            strand_type = (StrandType.STAPLE, StrandType.SCAFFOLD)[util.clamp(strand_idx, 0, 1)]
        return (strand_type, x, strand_idx)

    def helixIndex(self, point):
        """
        Returns the (row, col) of the base which point
        lies within.
        point is in virtual_helix_item coordinates.
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
        """
        col = int(int(point.x()) / _BW)
        row = int(int(point.y()) / _BW)
        # Doesn't know numBases, can't check if point is too far right
        if col < 0 or row < 0 or row > 1:
            return None
        return QPointF(col*_BW, row*_BW)
    # end def

    def hoverLeaveEvent(self, event):
        """
        flag is for the case where an item in the path also needs to
        implement the hover method
        """
        self.hide()
    # end def

# end class