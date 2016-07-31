"""Summary
"""
from .abstractpathtool import AbstractPathTool


class PaintTool(AbstractPathTool):
    """
    Handles visibility and color cycling for the paint tool.
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(PaintTool, self).__init__(manager)
        self._is_macrod = False

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "paint_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "paintTool"  # first letter should be lowercase

    def setActive(self, will_be_active):
        """Show the ColorPicker widget when active, hide when inactive.

        Args:
            will_be_active (TYPE): Description
        """
        if will_be_active:
            self._window.path_color_panel.show()
        else:
            self._window.path_color_panel.hide()
            self._window.path_color_panel.prevColor()

    def widgetClicked(self):
        """Cycle through colors on 'p' keypress
        """
        self._window.path_color_panel.nextColor()

    def customMouseRelease(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self._is_macrod:
            self._is_macrod = False
            self._window.undoStack().endMacro()
    # end def

    def isMacrod(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._is_macrod
    # end def

    def setMacrod(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._is_macrod = True
        self._window.undoStack().beginMacro("Group Paint")
        self._window.path_graphics_view.addToPressList(self)
    # end def
