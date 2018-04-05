# -*- coding: utf-8 -*-
"""
Attributes:
    SNAP_WIDTH (int): Description
"""
import logging
import random

from PyQt5.QtCore import (
    QLineF,
    QPointF,
    Qt,
    QRectF
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsSimpleTextItem,
    QGraphicsSceneMouseEvent
)

from cadnano.views.pathview import pathstyles
from cadnano.controllers import VirtualHelixItemController
from cadnano.views.abstractitems import AbstractVirtualHelixItem
from cadnano.gui.palette import (
    getPenObj,
    getBrushObj
)

from . import slicestyles as styles
from .sliceextras import (
    WedgeGizmo,
    WEDGE_RECT
)
from cadnano.views.sliceview.tools import (
    CreateSliceToolT,
    SelectSliceToolT
)
from . import (
    SliceNucleicAcidPartItemT,
    SliceVirtualHelixItemT
)
from cadnano.cntypes import (
    KeyT,
    ValueT
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class SliceVirtualHelixItem(AbstractVirtualHelixItem, QGraphicsEllipseItem):
    """The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the NucleicAcidPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the NucleicAcidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.

    Attributes:
        FILTER_NAME (str): Belongs to the filter class 'virtual_helix'.
        is_active (bool): Does the item have focus.
        old_pen (QPen): temp storage for pen for easy restoration on appearance change.
        wedge_gizmos (dict): dictionary of `WedgeGizmo` objects.
    """
    FILTER_NAME = 'virtual_helix'

    def __init__(self, id_num: int, part_item: SliceNucleicAcidPartItemT):
        """
        Args:
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            part_item: the part item
        """
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        QGraphicsEllipseItem.__init__(self, parent=part_item)
        self._doc_controller = part_item.document().controller()
        self._controller = VirtualHelixItemController(self, self._model_part, do_wire_part=False, do_wire_strands=True)

        self.hide()
        self._viewroot = part_item._viewroot
        model_part = self._model_part
        x, y = model_part.locationQt(self._id_num, part_item.scaleFactor())
        # set position to offset for radius
        # self.setTransformOriginPoint(_RADIUS, _RADIUS)
        self.setCenterPos(x, y)

        self.wedge_gizmos = {}
        self._added_wedge_gizmos = set()
        # self._prexo_gizmos = []

        self.setAcceptHoverEvents(True)
        self.setZValue(_ZVALUE)

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()

        self.old_pen = None
        self.is_active = False
        self.updateAppearance()

        self.show()

        self._right_mouse_move = False
    # end def

    ### ACCESSORS ###
    def setSnapOrigin(self, is_snap: bool):
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

    def activate(self):
        """Sets the VirtualHelixItem object as active (i.e. having focus due
        to user input) and calls updateAppearance.
        """
        self.is_active = True
        self.updateAppearance()

    def deactivate(self):
        """Sets the VirtualHelixItem object as not active (i.e. does not have
        focus) and calls updateAppearance.
        """
        self.is_active = False
        self.updateAppearance()

    def setCenterPos(self, x: float, y: float):
        """Moves this item a new position such that its center is located at
        (x,y).

        Args:
            x: new x coordinate
            y: new y coordinate
        """
        # invert the y axis
        part_item = self._part_item
        parent_item = self.parentItem()
        pos = QPointF(x - _RADIUS, y - _RADIUS)
        if parent_item != part_item:
            pos = parent_item.mapFromItem(part_item, pos)
        self.setPos(pos)
    # end def

    def getCenterScenePos(self) -> QPointF:
        """
        Returns:
            the scenePos of the virtualhelixitem center
        """
        return self.scenePos() + QPointF(_RADIUS, _RADIUS)
    # end def

    def partCrossoverSpanAngle(self) -> float:
        """The angle span, centered at each base, within which crossovers
        will be allowed by the interface. The span is drawn by the WedgeGizmo.

        Returns:
            The span angle (default is set in NucleicAcidPart init)
        """
        return float(self._model_part.getProperty('crossover_span_angle'))
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
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
            self._doc_controller.showFilterHints(True, filter_name=self.FILTER_NAME)
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

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self._doc_controller.showFilterHints(False)

    def createToolMousePress(self,  tool: CreateSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        shift = event.modifiers() & Qt.ShiftModifier
        fwd_ss, rev_ss = self.part().getStrandSets(self._id_num)
        idx_high = fwd_ss.length() - 1

        parity = self._id_num % 2
        c = random.choice(pathstyles.STAP_COLORS) if shift else None

        if parity:
            if shift:
                fwd_ss.createStrand(0, idx_high, color=c)
            else:
                rev_ss.createStrand(0, idx_high, color=c)
        else:
            if shift:
                rev_ss.createStrand(0, idx_high, color=c)
            else:
                fwd_ss.createStrand(0, idx_high, color=c)

    def selectToolMousePress(self,  tool: SelectSliceToolT,
                                    part_item: SliceNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        """The event handler for when the mouse button is pressed inside this
        item with the :class:`SelectSliceTool` active.

        Args:
            tool: reference to call tool-specific methods
            part_item: reference to the part item
            event: contains parameters that describe the mouse event

        """
        part = self._model_part
        part.setSelected(True)
        tool.selectOrSnap(part_item, self, event)
        # return QGraphicsItem.mousePressEvent(self, event)
    # end def

    def virtualHelixPropertyChangedSlot(self, keys: KeyT, values: ValueT):
        """The event handler for when the a model virtual helix propety has
        changed. See ``partVirtualHelixPropertyChangedSignal``.

        Calls :meth:`updateAppearance()`, which will refresh styles if needed.

        Args:
            keys: names of properties that changed
            values: new values of properties that change

        """
        # for key, val in zip(keys, values):
        #     pass
        self.updateAppearance()
    # end def

    def virtualHelixRemovedSlot(self):
        """The event handler for when a virtual helix is removed from the model.
        """
        self.destroyItem()
    # end def

    def destroyItem(self):
        """Disconnects signals, and sets  internal references to label, part_item,
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
        self._model_part = None
        self._viewroot = None
        self.scene().removeItem(self)
    # end def

    def updateAppearance(self):
        """Check item's current visibility, color and active state, and sets
        pen, brush, text according to style defaults.
        """
        is_visible, color = self._model_part.getVirtualHelixProperties(self._id_num, ['is_visible', 'color'])
        if is_visible:
            self.show()
        else:
            self.hide()
            return

        pwidth = styles.SLICE_HELIX_STROKE_WIDTH if self.old_pen is None else SNAP_WIDTH

        if self.is_active:
            self._USE_PEN = getPenObj(styles.ACTIVE_STROKE, pwidth)
        else:
            self._USE_PEN = getPenObj(color, pwidth)

        self._TEXT_BRUSH = getBrushObj(styles.SLICE_TEXT_COLOR)

        self._BRUSH = _BRUSH_DEFAULT
        self._USE_BRUSH = getBrushObj(color, alpha=150)

        self._label.setBrush(self._TEXT_BRUSH)
        self.setBrush(self._BRUSH)
        self.setPen(self._USE_PEN)
        self.setRect(_RECT)
    # end def

    def updatePosition(self):
        """Queries the model virtual helix for latest x,y coodinates, and sets
        them in the scene if necessary.

        NOTE:
            coordinates in the model are always in the part
        """
        part_item = self._part_item
        # sf = part_item.scaleFactor()
        x, y = self._model_part.locationQt(self._id_num, part_item.scaleFactor())
        new_pos = QPointF(x - _RADIUS, y - _RADIUS)         # top left
        tl_pos = part_item.mapFromScene(self.scenePos())    # top left

        """
        better to compare QPointF's since it handles difference
        tolerances for you with !=
        """
        if new_pos != tl_pos:
            parent_item = self.parentItem()
            if parent_item != part_item:
                new_pos = parent_item.mapFromItem(part_item, new_pos)
            self.setPos(new_pos)
    # end def

    def createLabel(self) -> QGraphicsSimpleTextItem:
        """Creates a text label to display the ID number. Font and Z are set
        in slicestyles.

        Returns:
            the label
        """
        label = QGraphicsSimpleTextItem("%d" % self.idNum())
        label.setFont(_FONT)
        label.setZValue(_ZVALUE)
        label.setParentItem(self)
        return label
    # end def

    def beginAddWedgeGizmos(self):
        """Resets the list of :class:`WedgeGizmos` that will be processed by
        endAddWedgeGizmos.

        Called by :meth:`SliceNucleicAcidPartItem._refreshVirtualHelixItemGizmos`,
        before :meth:`setWedgeGizmo` and :meth:`endAddWedgeGizmos`.
        """
        self._added_wedge_gizmos.clear()
    # end def

    def endAddWedgeGizmos(self):
        """Removes :meth:`beginAddWedgeGizmos` that no longer point at a
        neighbor virtual helix.

        Called by :meth:`SliceNucleicAcidPartItem._refreshVirtualHelixItemGizmos`,
        before :meth:`setWedgeGizmo` and :meth:`endAddWedgeGizmos`.
        """
        remove_list = []
        scene = self.scene()
        wg_dict = self.wedge_gizmos
        recently_added = self._added_wedge_gizmos
        for neighbor_virtual_helix in wg_dict.keys():
            if neighbor_virtual_helix not in recently_added:
                remove_list.append(neighbor_virtual_helix)
        for nvh in remove_list:
            wg = wg_dict.get(nvh)
            del wg_dict[nvh]
            scene.removeItem(wg)
    # end def

    def setWedgeGizmo(self, neighbor_virtual_helix: int,
                            neighbor_virtual_helix_item: SliceVirtualHelixItemT):
        """Adds a :class:`WedgeGizmo` to oriented toward the specified neighbor vhi.

        Called by :meth:`SliceNucleicAcidPartItem._refreshVirtualHelixItemGizmos`,
        before :meth:`setWedgeGizmo` and :meth:`endAddWedgeGizmos`.

        Args:
            neighbor_virtual_helix: the id_num of neighboring virtual helix
            neighbor_virtual_helix_item: the neighboring virtual helix item
        """
        wg_dict = self.wedge_gizmos
        nvhi = neighbor_virtual_helix_item
        pos = self.scenePos()
        line = QLineF(pos, nvhi.scenePos())
        line.translate(_RADIUS, _RADIUS)
        if line.length() > (_RADIUS*1.99):
            color = '#5a8bff'
        else:
            color = '#cc0000'
        line.setLength(_RADIUS)
        if neighbor_virtual_helix in wg_dict:
            wedge_item = wg_dict[neighbor_virtual_helix]
        else:
            wedge_item = WedgeGizmo(_RADIUS, WEDGE_RECT, self)
            wg_dict[neighbor_virtual_helix] = wedge_item
        wedge_item.showWedge(line.angle(), color, outline_only=False)
        self._added_wedge_gizmos.add(neighbor_virtual_helix)
    # end def

    def setNumber(self):
        """Updates the associated :class:`QGraphicsSimpleTextItem` label text
        to match the id_num. Adjusts the label position so it is centered
        regardless of number of digits in the label.
        """
        num = self.idNum()
        label = self._label

        if num is not None:
            label.setText("%d" % num)
        else:
            return

        y_val = _RADIUS / 3
        if num < 10:
            label.setPos(_RADIUS / 1.5, y_val)
        elif num < 100:
            label.setPos(_RADIUS / 3, y_val)
        else:  # _number >= 100
            label.setPos(0, y_val)
        b_rect = label.boundingRect()
        posx = b_rect.width()/2
        posy = b_rect.height()/2
        label.setPos(_RADIUS-posx, _RADIUS-posy)
    # end def
# end class
