from cadnano import util
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QActionGroup, QGraphicsObject
from PyQt5.QtWidgets import QGraphicsLineItem
from cadnano.gui.views.sliceview import slicestyles as styles

class AbstractSliceTool(QGraphicsObject):
    _RADIUS = styles.SLICE_HELIX_RADIUS

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
        self.started = False


    ######################## Drawing #######################################
    # def paint(self, painter, option, widget=None):
    #     painter.setPen(self._pen)
    #     painter.setBrush(_BRUSH)
    #     painter.drawRect(_TOOL_RECT)

    # def boundingRect(self):
    #     return self._rect

    def setVirtualHelixItem(self, virtual_helix_item):
        rad = self._RADIUS
        self._vhi = virtual_helix_item
        li = self._line_item
        li.setParentItem(virtual_helix_item)
        li.setLine(rad, rad, rad, rad)
        li.show()
        self.started = True
    # end def

    def hoverMoveEvent(self, event):
        if self.started:
            li = self._line_item
            line = li.line()
            pos = li.mapFromScene(event.scenePos())
            line.setP2(pos)
            li.setLine(line)
    # end def

    def widgetClicked(self):
        """Called every time a widget representing self gets clicked,
        not just when changing tools."""
        pass

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
        self.hide()
    # end def

    def isActive(self):
        """Returns isActive"""
        return self._active
    # end def
# end class
