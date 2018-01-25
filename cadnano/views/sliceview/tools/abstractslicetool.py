import math

from PyQt5.QtCore import QLineF, QPointF, QRectF
from PyQt5.QtWidgets import QGraphicsObject

from cadnano.gui.palette import getPenObj
from cadnano.views.sliceview import slicestyles as styles


_RADIUS = styles.SLICE_HELIX_RADIUS
_DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
_MOD_PEN = getPenObj(styles.BLUE_STROKE, HIGHLIGHT_WIDTH)
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.
# _HOVER_RECT = _DEFAULT_RECT.adjusted(-DELTA, -DELTA, DELTA, DELTA)


_INACTIVE_PEN = getPenObj(styles.GRAY_STROKE, HIGHLIGHT_WIDTH)


class AbstractSliceTool(QGraphicsObject):
    """Summary

    Attributes:
        angles (TYPE): Description
        FILTER_NAME (str): Description
        is_started (bool): Description
        manager (TYPE): Description
        part_item (TYPE): Description
        sgv (TYPE): Description
        vectors (TYPE): Description
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS
    _CENTER_OF_HELIX = QPointF(_RADIUS, _RADIUS)
    FILTER_NAME = 'virtual_helix'
    # _CENTER_OF_HELIX = QPointF(0. 0.)
    """Abstract base class to be subclassed by all other pathview tools."""

    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(AbstractSliceTool, self).__init__(parent=manager.viewroot)
        """ Pareting to viewroot to prevent orphan _line_item from occuring
        """
        self.sgv = None  # SGV is "Slice Graphics View"
        self.manager = manager
        self._active = False
        self._last_location = None
#        self._line_item = QGraphicsLineItem(self)
#        self._line_item.hide()
        self._vhi = None

        self.hide()
        self.is_started = False
        self.angles = [math.radians(x) for x in range(0, 360, 30)]
        self.vectors = self.setVectors()
        self.part_item = None

#        self.vhi_hint_item = QGraphicsEllipseItem(_DEFAULT_RECT, self)
#        self.vhi_hint_item.setPen(_MOD_PEN)
#        self.vhi_hint_item.setZValue(styles.ZPARTITEM)
    # end def

    ######################## Drawing #######################################
    def setVectors(self):
        """Summary

        Returns:
            TYPE: Description
        """
        rad = self._RADIUS
        return [QLineF(rad, rad,
                       rad*(1. + 2.*math.cos(x)), rad*(1. + 2.*math.sin(x))
                       ) for x in self.angles]
    # end def

    def setVirtualHelixItem(self, virtual_helix_item):
        """Summary

        Args:
            virtual_helix_item (cadnano.views.sliceview.virtualhelixitem.VirtualHelixItem): Description

        Returns:
            TYPE: Description
        """
        self._RADIUS
        self._vhi = virtual_helix_item
#        li = self._line_item
#        li.setParentItem(virtual_helix_item)
#        li.setLine(rad, rad, rad, rad)
        # li.setLine(0., 0., 0., 0.)
    # end def

    def setSelectionFilter(self, filter_name_list):
        pass
#        if 'virtual_helix' in filter_name_list:
#            self.vhi_hint_item.setPen(_MOD_PEN)
#        else:
#            self.vhi_hint_item.setPen(_INACTIVE_PEN)
    # end def

    def resetTool(self):
        """Summary

        Returns:
            TYPE: Description
        """
#        self._line_item.setParentItem(self)

    def idNum(self):
        """Summary

        Returns:
            TYPE: Description
        """
        if self._vhi is not None:
            return self._vhi.idNum()

    def setPartItem(self, part_item):
        """Summary

        Args:
            part_item (TYPE): Description

        Returns:
            TYPE: Description
        """
#        self.vhi_hint_item.setParentItem(part_item)
        self.part_item = part_item
    # end def

    def boundingRect(self):
        """Required to prevent NotImplementedError()
        """
        return QRectF()

    def eventToPosition(self, part_item, event):
        """take an event and return a position as a QPointF
        update widget as well

        Args:
            part_item (TYPE): Description
            event (TYPE): Description
        """
        if self.is_started:
            pos = self.findNearestPoint(part_item, event.scenePos())
        else:
            pos = event.pos()
#        self.vhi_hint_item.setPos(  pos -
#                                    QPointF(_RADIUS - DELTA, _RADIUS - DELTA))
        return pos
    # end def

    def setHintPos(self, pos):
        pass
#        self.vhi_hint_item.setPos(  pos -
#                                    QPointF(_RADIUS - DELTA, _RADIUS - DELTA))
    # end def

    def findNearestPoint(self, part_item, target_scenepos):
        """
        Args:
            part_item (TYPE): Description
            target_scenepos (TYPE): Description
        """
#        li = self._line_item
#        pos = li.mapFromScene(target_scenepos)

#        line = li.line()
#        mouse_point_vec = QLineF(self._CENTER_OF_HELIX, pos)

        # Check if the click happened on the origin VH
#        if mouse_point_vec.length() < self._RADIUS:
#            return part_item.mapFromScene(target_scenepos)

#        angle_min = 9999
#        direction_min = None
#        for vector in self.vectors:
#            angle_new = mouse_point_vec.angleTo(vector)
#            if angle_new < angle_min:
#                direction_min = vector
#                angle_min = angle_new
#        if direction_min is not None:
#            li.setLine(direction_min)
#            return part_item.mapFromItem(li, direction_min.p2())
#        else:
#            print("default point")
#            line.setP2(pos)
#            li.setLine(line)
#            return part_item.mapFromItem(li, pos)
    # end def

    def findNextPoint(self, part_item, target_part_pos):
        """
        Args:
            part_item (TYPE): Description
            target_part_pos (TYPE): Description
        """
#        li = self._line_item
#        pos = li.mapFromItem(part_item, target_part_pos)
#        for i, vector in enumerate(self.vectors):
#            if vector.p2() == pos:
#                return part_item.mapFromItem(li, self.vectors[i - 1].p2())
#        # origin VirtualHelixItem is overlapping destination VirtualHelixItem
#        return part_item.mapFromItem(li, self.vectors[0].p2())
    # end def

    def hideLineItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
#        self.vhi_hint_item.hide()
#        li = self._line_item
#        li.hide()
#        li.setParentItem(self)
#        line = li.line()
#        line.setP2(self._CENTER_OF_HELIX)
#        li.setLine(line)
#        # li.hide()
#        self.is_started = False
    # end def

    # def hoverEnterEvent(self, event):
    #     self.vhi_hint_item.show()
    #     #print("Slice VHI hoverEnterEvent")

    # # def hoverMoveEvent(self, event):
    #     # print("Slice VHI hoverMoveEvent")

    # def hoverLeaveEvent(self, event):
    #     # self.vhi_hint_item.hide()
    #     #print("Slice VHI hoverLeaveEvent")

    def hoverMoveEvent(self, part_item, event):
        """Summary

        Args:
            part_item (TYPE): Description
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        # self.vhi_hint_item.setPos(  event.pos()-
        #                             QPointF(_RADIUS - DELTA, _RADIUS - DELTA))
        pos = self.eventToPosition(part_item, event)
        return pos
    # end def

    def setActive(self, will_be_active, old_tool=None):
        """
        Called by SliceToolManager.setActiveTool when the tool becomes
        active. Used, for example, to show/hide tool-specific ui elements.

        Args:
            will_be_active (TYPE): Description
            old_tool (None, optional): Description
        """
        if self._active and not will_be_active:
            self.deactivate()
        self._active = will_be_active
        self.sgv = self.manager.window.slice_graphics_view
        if hasattr(self, 'getCustomContextMenu'):
            # print("connecting ccm")
            try:    # Hack to prevent multiple connections
                self.sgv.customContextMenuRequested.disconnect()
            except Exception:
                pass
            self.sgv.customContextMenuRequested.connect(self.getCustomContextMenu)
    # end def

    def deactivate(self):
        """Summary

        Returns:
            TYPE: Description
        """
        if hasattr(self, 'getCustomContextMenu'):
            # print("disconnecting ccm")
            self.sgv.customContextMenuRequested.disconnect(self.getCustomContextMenu)
        self.sgv = None
        self.is_started = False
        self.hideLineItem()
        self._vhi = None
        self.part_item = None
        self.hide()
        self._active = False
    # end def

    def isActive(self):
        """Returns isActive
        """
        return self._active
    # end def
# end class
