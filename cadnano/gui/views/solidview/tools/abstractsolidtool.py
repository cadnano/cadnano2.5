"""Summary
"""
from PyQt5.QtCore import QObject


class AbstractSolidTool(QObject):
    """Abstract base class to be subclassed by all other pathview tools.

    Attributes:
        manager (TYPE): Description
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(AbstractSolidTool, self).__init__(None)
        self.manager = manager
        self._window = manager.window
        self._active = False
        self._last_location = None

    ######################### Positioning and Parenting ####################
    def updateLocation(self, virtual_helix_item, scene_pos, *args):
        """Takes care of caching the location so that a tool switch
        outside the context of an event will know where to
        position the new tool and snaps self's pos to the upper
        left hand corner of the base the user is mousing over.

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            scene_pos (TYPE): Description
            *args (TYPE): Description
        """
        pass
    # end def

    def lastLocation(self):
        """A tool's last_location consists of a VirtualHelixItem and a ScenePos
        (QPoint) representing the last known location of the mouse.

        It can be used to provide visual continuity when switching tools.
        When the new tool is selected, this method will be invoked by
        calling `updateLocation(*old_tool.lastLocation())`.

        Returns:
            location (tuple): (virtual_helix_item, QPoint) representing the last
                known location of the mouse for purposes of positioning
                the graphic of a new tool on switching tools (the tool
                will have called on it)

        """
        return self._last_location

    def setActive(self, will_be_active, old_tool=None):
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

    def isActive(self):
        """Returns isActive
        """
        return self._active

    def widgetClicked(self):
        """Called every time a widget representing self gets clicked,
        not just when changing tools.
        """
        pass

    ####################### Coordinate Utilities ###########################
    # def baseAtPoint(self, virtual_helix_item, pt):
    #     """Returns the (is_fwd, base_idx, strand_idx) corresponding
    #     to pt in virtual_helix_item.

    #     Args:
    #         virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
    #         pt (TYPE): Description
    #     """
    #     x, strand_idx = self.helixIndex(pt)

    #     is_fwd = False if util.clamp(strand_idx, 0, 1) else True
    #     return (is_fwd, x, strand_idx)

    # def helixIndex(self, point):
    #     """Returns the (row, col) of the base which point lies within.

    #     Returns:
    #         point (tuple) in virtual_helix_item coordinates

    #     Args:
    #         point (TYPE): Description
    #     """
    #     x = int(int(point.x()) / _BW)
    #     y = int(int(point.y()) / _BW)
    #     return (x, y)
    # # end def

    # def helixPos(self, point):
    #     """
    #     Snaps a point to the upper left corner of the base
    #     it is within.
    #     point is in virtual_helix_item coordinates

    #     Args:
    #         point (TYPE): Description
    #     """
    #     col = int(int(point.x()) / _BW)
    #     row = int(int(point.y()) / _BW)
    #     # Doesn't know numBases, can't check if point is too far right
    #     if col < 0 or row < 0 or row > 1:
    #         return None
    #     return QPointF(col * _BW, row * _BW)
    # # end def

    # def hoverLeaveEvent(self, event):
    #     """
    #     flag is for the case where an item in the path also needs to
    #     implement the hover method

    #     Args:
    #         event (TYPE): Description
    #     """
    #     self.hide()
    # # end def
# end class
