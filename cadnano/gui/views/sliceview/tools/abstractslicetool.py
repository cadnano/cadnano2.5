import math

from PyQt5.QtCore import pyqtSignal, QObject, QPointF, QLineF
from PyQt5.QtWidgets import QActionGroup, QGraphicsObject
from PyQt5.QtWidgets import QGraphicsLineItem

from cadnano.gui.views.sliceview import slicestyles as styles
from cadnano.math.vector import v2AngleBetween

class AbstractSliceTool(QGraphicsObject):
    _RADIUS = styles.SLICE_HELIX_RADIUS
    _CENTER_OF_HELIX = QPointF(_RADIUS, _RADIUS)
    """Abstract base class to be subclassed by all other pathview tools."""
    def __init__(self, controller, parent=None):
        super(AbstractSliceTool, self).__init__(parent)
        self._controller = controller
        self._window = controller.window
        self._active = False
        self._last_location = None
        self._line_item = QGraphicsLineItem(None)
        self._line_item.hide()
        self._vhi = None
        # self._rect = _RECT
        # self._pen = _PEN
        self.hide()
        self.is_started = False
        self.angles = [x*math.pi/180 for x in range(0, 360, 30)]
        self.vectors = self.setVectors()
        self._direction = None
        self.part_item = None
    # end def

    ######################## Drawing #######################################
    # def paint(self, painter, option, widget=None):
    #     painter.setPen(self._pen)
    #     painter.setBrush(_BRUSH)
    #     painter.drawRect(_TOOL_RECT)

    # def boundingRect(self):
    #     return self._rect

    def setVectors(self):
        rad = self._RADIUS
        return [QLineF( rad, rad,
                        rad*(1 + 2*math.cos(x)), rad*(1 + 2*math.sin(x))
                        ) for x in self.angles]
    # end def

    # end def
    def setVirtualHelixItem(self, virtual_helix_item):
        rad = self._RADIUS
        self._vhi = virtual_helix_item
        li = self._line_item
        li.setParentItem(virtual_helix_item)
        li.setLine(rad, rad, rad, rad)
        li.show()
        self.is_started = True
    # end def

    def setPartItem(self, part_item):
        self.part_item = part_item
    # end def

    def getAdjacentPoint(self, part_item, pt):
        """ takes and returns a QPointF
        """
        part_item.mapFromItem(self._line_item, pt)
    # end def

    def eventToPosition(self, part_item, event):
        """ take an event and return a position as a QPointF

        update widget as well
        """
        li = self._line_item
        pos = li.mapFromScene(event.scenePos())
        if self.is_started:
            line = li.line()
            mouse_point_vec = QLineF(self._CENTER_OF_HELIX, pos)
            angle_min = 9999
            direction_min = None
            for vector in self.vectors:
                angle_new = mouse_point_vec.angleTo(vector)
                if angle_new < angle_min:
                    direction_min = vector
                    angle_min = angle_new
            if direction_min is not None:
                self._direction_min = direction_min
                li.setLine(direction_min)
                return part_item.mapFromItem(li, direction_min.p2())
            else:
                line.setP2(pos)
                li.setLine(line)
                return part_item.mapFromItem(li, pos)
        else:
            return event.pos()
    # end def

    def hoverMoveEvent(self, part_item, event):
        return self.eventToPosition(part_item, event)
    # end def

    # def widgetClicked(self):
    #     """Called every time a widget representing self gets clicked,
    #     not just when changing tools."""
    #     pass

    def setActive(self, will_be_active, old_tool=None):
        """
        Called by SliceToolManager.setActiveTool when the tool becomes
        active. Used, for example, to show/hide tool-specific ui elements.
        """
        if self._active and not will_be_active:
            self.deactivate()
        self._active = will_be_active
    # end def

    def deactivate(self):
        self.is_started = False
        self._vhi = None
        self.part_item = None
        self.hide()
    # end def

    def isActive(self):
        """Returns isActive"""
        return self._active
    # end def
# end class
