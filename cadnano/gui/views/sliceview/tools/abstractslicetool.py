from cadnano import util
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QActionGroup, QGraphicsObject

class AbstractSliceTool(QGraphicsObject):
    """Abstract base class to be subclassed by all other pathview tools."""
    def __init__(self, controller, parent=None):
        super(AbstractSliceTool, self).__init__(parent)
        self._controller = controller
        self._window = controller.window
        self._active = False
        self._last_location = None
        # self._rect = _RECT
        # self._pen = _PEN
        self.hide()


    ######################## Drawing #######################################
    # def paint(self, painter, option, widget=None):
    #     painter.setPen(self._pen)
    #     painter.setBrush(_BRUSH)
    #     painter.drawRect(_TOOL_RECT)

    # def boundingRect(self):
    #     return self._rect

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
