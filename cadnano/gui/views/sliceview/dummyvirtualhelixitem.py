"""Summary

Attributes:
    SNAP_WIDTH (int): Description
"""
from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem

from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from . import slicestyles as styles

# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX
_BRUSH_DEFAULT = getBrushObj(styles.SLICE_FILL)
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)

SNAP_WIDTH = 3


class DummySliceVirtualHelixItem(AbstractVirtualHelixItem, QGraphicsEllipseItem):
    """The DummySliceVirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the NucleicAcidPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the NucleicAcidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.

    Attributes:
        FILTER_NAME (str): Belongs to the filter class 'virtual_helix'.
        is_active (bool): Does the item have focus.
        old_pen (QPen): temp storage for pen for easy restoration on appearance change.
    """
    FILTER_NAME = 'virtual_helix' #TODO:  Figure out how this should be modified for this class

    def __init__(self, x, y):
        """
        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            part_item (cadnano.gui.views.sliceview.nucleicacidpartitem.NucleicAcidPartItem): the part item
        """
        AbstractVirtualHelixItem.__init__(self)
        QGraphicsEllipseItem.__init__(self)

        self.hide() #FIXME:  This doesn't seem to do anything

        self.x = x
        self.y = y

        self.setCenterPos(self.x, self.y)

        self.setAcceptHoverEvents(True)
        self.setZValue(_ZVALUE)

        self.old_pen = None
        self.is_active = False

        self.show()
    # end def

    ### ACCESSORS ###
    def setSnapOrigin(self, is_snap):
        """Used to toggle an item as the snap origin. See `SelectSliceTool`.

        Args:
            is_snap (bool): True if this should be the snap origin, False otherwise.
        """
        if is_snap:
            op = self.pen()
            if self.old_pen is None:
                self.old_pen = op
            self.setPen(getPenObj(op.color().name(), SNAP_WIDTH))
        else:
            self.setPen(self.old_pen)
            self.old_pen = None

    def setCenterPos(self, x, y):
        """Moves this item a new position such that its center is located at
        (x,y).

        Args:
            x (float): new x coordinate
            y (float): new y coordinate
        """
        # invert the y axis
        part_item = self._part_item
        parent_item = self.parentItem()
        pos = QPointF(x - _RADIUS, y - _RADIUS)
        if parent_item != part_item:
            pos = parent_item.mapFromItem(part_item, pos)
        self.setPos(pos)
    # end def

    def getCenterScenePos(self):
        """
        Returns:
            QPointF: the scenePos of the virtualhelixitem center
        """
        return self.scenePos() + QPointF(_RADIUS, _RADIUS)
    # end def

    ### SLOTS ###
    def mousePressEvent(self, event):
        """Event handler for when the mouse button is pressed inside
        this item. If a tool-specific mouse press method is defined, it will be
        called for the currently active tool. Otherwise, the default
        QGraphicsItem.mousePressEvent will be called.

        Note:
            Only applies the event if the clicked item is in the part
            item's active filter set.

        Args:
            event (QMouseEvent): contains parameters that describe the mouse event.
        """
        if self.FILTER_NAME not in self._part_item.getFilterSet():
            return
        if event.button() == Qt.RightButton:
            return
        part_item = self._part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def selectToolMousePress(self, tool, part_item, event):
        """The event handler for when the mouse button is pressed inside this
        item with the SelectTool active.

        Args:
            tool (SelectSliceTool): reference to call tool-specific methods
            part_item (cadnano.gui.views.sliceview.nucleicacidpartitem.NucleicAcidPartItem): reference to the part item
            event (QMouseEvent): contains parameters that describe the mouse event

        """
        #TODO:  This needs to be updated to support mouse events
        part = self._model_part
        part.setSelected(True)
        tool.selectOrSnap(part_item, self, event)
        # return QGraphicsItem.mousePressEvent(self, event)
    # end def

    def pencilToolMousePress(self, tool, part_item, event):
        """Summary

        Args:
            tool (SelectSliceTool): reference to call tool-specific methods
            part_item (cadnano.gui.views.sliceview.nucleicacidpartitem.NucleicAcidPartItem): reference to the part item
            event (QMouseEvent): contains parameters that describe the mouse event
        """
        #TODO:  This needs to be updated to support mouse events
        part = self._model_part
        print("pencilToolMousePress", part)
        # tool.attemptToCreateStrand

    def virtualHelixRemovedSlot(self):
        """The event handler for when a virtual helix is removed from the model.

        Disconnects signals, and sets  internal references to label, part_item,
        and model_part to None, and finally removes the item from the scene.
        """
        self._controller.disconnectSignals()
        self._controller = None
        part_item = self._part_item
        tool = part_item._getActiveTool()
        if tool.methodPrefix() == "selectTool":
            tool.hideLineItem()
        self.scene().removeItem(self._label)
        self._label = None
        self._part_item = None
        self.scene().removeItem(self)
    # end def
# end class