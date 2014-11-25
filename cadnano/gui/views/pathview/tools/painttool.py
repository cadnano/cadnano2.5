import sys
from .abstractpathtool import AbstractPathTool
import cadnano.util as util

class PaintTool(AbstractPathTool):
    """
    Handles visibility and color cycling for the paint tool.
    """
    def __init__(self, controller):
        super(PaintTool, self).__init__(controller)
        self._is_macrod = False

    def __repr__(self):
        return "paint_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "paintTool"  # first letter should be lowercase

    def setActive(self, will_be_active):
        """Show the ColorPicker widget when active, hide when inactive."""
        if will_be_active:
            self._window.path_color_panel.show()
        else:
            self._window.path_color_panel.hide()
            self._window.path_color_panel.prevColor()

    def widgetClicked(self):
        """Cycle through colors on 'p' keypress"""
        self._window.path_color_panel.nextColor()

    def customMouseRelease(self, event):
        if self._is_macrod:
            self._is_macrod = False
            self._window.undoStack().endMacro()
    # end def

    def isMacrod(self):
        return self._is_macrod
    # end def

    def setMacrod(self):
        self._is_macrod = True
        self._window.undoStack().beginMacro("Group Paint")
        self._window.path_graphics_view.addToPressList(self)
    # end def
