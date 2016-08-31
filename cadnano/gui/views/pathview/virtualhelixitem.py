#!/usr/bin/env python
"""Summary
"""
# encoding: utf-8

from math import floor, atan2, sqrt

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem

from cadnano import util
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import newPenObj, getNoBrush, getColorObj, getPenObj
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from .strand.stranditem import StrandItem
from .strand.xoveritem import XoverNode3
from .virtualhelixhandleitem import VirtualHelixHandleItem
from . import pathstyles as styles

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_VH_XOFFSET = styles.VH_XOFFSET


def v2DistanceAndAngle(a, b):
    """Summary

    Args:
        a (TYPE): Description
        b (TYPE): Description

    Returns:
        TYPE: Description
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = sqrt(dx*dx + dy*dy)
    angle = atan2(dy, dx)
    return dist, angle


class PathVirtualHelixItem(AbstractVirtualHelixItem, QGraphicsPathItem):
    """VirtualHelixItem for PathView

    Attributes:
        drag_last_position (TYPE): Description
        FILTER_NAME (str): Description
        findChild (TYPE): Description
        handle_start (TYPE): Description
        is_active (bool): Description
    """
    findChild = util.findChild  # for debug
    FILTER_NAME = "virtual_helix"

    def __init__(self, model_virtual_helix, part_item, viewroot):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            part_item (TYPE): Description
            viewroot (TYPE): Description
        """
        AbstractVirtualHelixItem.__init__(self, model_virtual_helix, part_item)
        QGraphicsPathItem.__init__(self, parent=part_item.proxy())
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self._handle = VirtualHelixHandleItem(self, part_item, viewroot)
        self._last_strand_set = None
        self._last_idx = None
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setBrush(getNoBrush())

        view = self.view()
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        should_show_details = view.shouldShowDetails()

        pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(should_show_details)
        self.setPen(pen)

        self.is_active = False

        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)

        self._right_mouse_move = False
        self.drag_last_position = self.handle_start = self.pos()

    # end def

    ### SIGNALS ###

    ### SLOTS indirectly called from the part ###

    def levelOfDetailChangedSlot(self, boolval):
        """Not connected to the model, only the QGraphicsView

        Args:
            boolval (TYPE): Description
        """
        pen = self.pen()
        pen.setCosmetic(boolval)
        # print("levelOfDetailChangedSlot", boolval, pen.width())
        # if boolval:
        #     pass
        # else:
        #     pass
        self.setPen(pen)
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').

        Args:
            sender (obj): Model object that emitted the signal.
            strand (TYPE): Description
        """
        StrandItem(strand, self, self._viewroot)
    # end def

    def virtualHelixRemovedSlot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.view().levelOfDetailChangedSignal.disconnect(self.levelOfDetailChangedSlot)
        self._controller.disconnectSignals()
        self._controller = None

        scene = self.scene()
        self._handle.remove()
        scene.removeItem(self)
        self._part_item = None
        self._model_part = None
        self._getActiveTool = None
        self._handle = None
    # end def

    def virtualHelixPropertyChangedSlot(self, keys, values):
        """Summary

        Args:
            keys (TYPE): Description
            values (TYPE): Description

        Returns:
            TYPE: Description
        """
        for key, val in zip(keys, values):
            if key == 'is_visible':
                if val:
                    self.show()
                    self._handle.show()
                    self.showXoverItems()
                else:
                    self.hideXoverItems()
                    self.hide()
                    self._handle.hide()
                    return
            if key == 'z':
                part_item = self._part_item
                z = part_item.convertToQtZ(val)
                if self.x() != z:
                    self.setX(z)
                    """ The handle is selected, so deselect to
                    accurately position then reselect
                    """
                    vhi_h = self._handle
                    vhi_h.tempReparent()
                    vhi_h.setX(z - _VH_XOFFSET)
                    # if self.isSelected():
                    #     print("ImZ", self.idNum())
                    part_item.updateXoverItems(self)
                    vhi_h_selection_group = self._viewroot.vhiHandleSelectionGroup()
                    vhi_h_selection_group.addToGroup(vhi_h)
            elif key == 'eulerZ':
                self._handle.rotateWithCenterOrigin(val)
                # self._prexoveritemgroup.updatePositionsAfterRotation(value)
            ### GEOMETRY PROPERTIES ###
            elif key == 'repeat_hint':
                pass
                # self.updateRepeats(int(val))
            elif key == 'bases_per_repeat':
                pass
                # self.updateBasesPerRepeat(int(val))
            elif key == 'turns_per_repeat':
                # self.updateTurnsPerRepeat(int(val))
                pass
            ### RUNTIME PROPERTIES ###
            elif key == 'neighbors':
                # this means a virtual helix in the slice view has moved
                # so we need to clear and redraw the PreXoverItems just in case
                if self.isActive():
                    self._part_item.setPreXoverItemsVisible(self)
        self.refreshPath()
    # end def

    def showXoverItems(self):
        """Summary

        Returns:
            TYPE: Description
        """
        for item in self.childItems():
            if isinstance(item, XoverNode3):
                item.showXover()
    # end def

    def hideXoverItems(self):
        """Summary

        Returns:
            TYPE: Description
        """
        for item in self.childItems():
            if isinstance(item, XoverNode3):
                item.hideXover()
    # end def

    ### ACCESSORS ###
    def viewroot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._viewroot
    # end def

    def handle(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._handle
    # end def

    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._part_item.window()
    # end def

    def view(self):
        return self._viewroot.scene().views()[0]
    # end def

    ### DRAWING METHODS ###
    def upperLeftCornerOfBase(self, idx, strand):
        """Summary

        Args:
            idx (int): the base index within the virtual helix
            strand (TYPE): Description

        Returns:
            TYPE: Description
        """
        x = idx * _BASE_WIDTH
        y = 0 if strand.isForward() else _BASE_WIDTH
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx, is_fwd):
        """Summary

        Args:
            idx (int): the base index within the virtual helix
            is_fwd (TYPE): Description

        Returns:
            TYPE: Description
        """
        x = idx * _BASE_WIDTH
        y = 0 if is_fwd else _BASE_WIDTH
        return x, y
    # end def

    def refreshPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        bw = _BASE_WIDTH
        bw2 = 2 * bw
        part = self.part()
        path = QPainterPath()
        sub_step_size = part.subStepSize()
        canvas_size = self._model_vh.getSize()
        # border
        path.addRect(0, 0, bw * canvas_size, 2 * bw)
        # minor tick marks
        for i in range(canvas_size):
            x = round(bw * i) + .5
            if i % sub_step_size == 0:
                path.moveTo(x - .5, 0)
                path.lineTo(x - .5, bw2)
                path.lineTo(x - .25, bw2)
                path.lineTo(x - .25, 0)
                path.lineTo(x, 0)
                path.lineTo(x, bw2)
                path.lineTo(x + .25, bw2)
                path.lineTo(x + .25, 0)
                path.lineTo(x + .5, 0)
                path.lineTo(x + .5, bw2)

                # path.moveTo(x-.5, 0)
                # path.lineTo(x-.5, 2 * bw)
                # path.lineTo(x+.5, 2 * bw)
                # path.lineTo(x+.5, 0)

            else:
                path.moveTo(x, 0)
                path.lineTo(x, 2 * bw)

        # staple-scaffold divider
        path.moveTo(0, bw)
        path.lineTo(bw * canvas_size, bw)

        self.setPath(path)
    # end def

    def resize(self):
        """Called by part on resize.
        """
        self.refreshPath()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def activate(self):
        """Summary

        Returns:
            TYPE: Description
        """
        pen = self.pen()
        pen.setColor(getColorObj(styles.MINOR_GRID_STROKE_ACTIVE))
        self.setPen(pen)
        self.is_active = True
    # end def

    def deactivate(self):
        """Summary

        Returns:
            TYPE: Description
        """
        pen = self.pen()
        pen.setColor(getColorObj(styles.MINOR_GRID_STROKE))
        self.setPen(pen)
        self.is_active = False
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event (TYPE): Description
        """
        # 1. Check if we are doing a Z translation
        if event.button() == Qt.RightButton:
            viewroot = self._viewroot
            current_filter_set = viewroot.selectionFilterSet()
            if self.FILTER_NAME in current_filter_set and self.part().isZEditable():
                self._right_mouse_move = True
                self.drag_last_position = event.scenePos()
                self.handle_start = self.pos()
            return

        self.scene().views()[0].addToPressList(self)
        strand_set, idx = self.baseAtPoint(event.pos())
        self._model_vh.setActive(strand_set.isForward(), idx)
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"

        if hasattr(self, tool_method_name):
            self._last_strand_set, self._last_idx = strand_set, idx
            getattr(self, tool_method_name)(strand_set, idx, event.modifiers())
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event (TYPE): Description
        """
        # 1. Check if we are doing a Z translation
        if self._right_mouse_move:
            MOVE_THRESHOLD = 0.01   # ignore small moves
            new_pos = event.scenePos()
            delta = new_pos - self.drag_last_position
            dx = int(floor(delta.x() / _BASE_WIDTH))*_BASE_WIDTH
            x = self.handle_start.x() + dx
            if abs(dx) > MOVE_THRESHOLD or dx == 0.0:
                old_x = self.x()
                self.setX(x)
                vhi_h = self._handle
                vhi_h.tempReparent()
                vhi_h.setX(x - _VH_XOFFSET)
                self._part_item.updateXoverItems(self)
                dz = self._part_item.convertToModelZ(x - old_x)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, False,
                                                         use_undostack=False)
                return
        # 2. Forward event to tool
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            strand_set, idx = self.baseAtPoint(event.pos())
            if self._last_strand_set != strand_set or self._last_idx != idx:
                self._last_strand_set, self._last_idx = strand_set, idx
                getattr(self, tool_method_name)(strand_set, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseReleaseEvent(self, event):
        """Called in the event of doing a Z translation drag

        Args:
            event (TYPE): Description
        """
        if self._right_mouse_move and event.button() == Qt.RightButton:
            MOVE_THRESHOLD = 0.01   # ignore small moves
            self._right_mouse_move = False
            delta = self.pos() - self.handle_start
            dz = delta.x()
            if abs(dz) > MOVE_THRESHOLD:
                dz = self._part_item.convertToModelZ(dz)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, True,
                                                         use_undostack=True)
    # end def

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event (TYPE): Description
        """
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(self._last_strand_set, self._last_idx)
        else:
            event.setAccepted(False)
    # end def

    ### COORDINATE UTILITIES ###
    def baseAtPoint(self, pos):
        """
        Returns the (Strandset, index) under the location x, y or None.

        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.

        Args:
            pos (TYPE): Description
        """
        x, y = pos.x(), pos.y()
        part = self._model_part
        id_num = self._id_num
        base_idx = int(floor(x / _BASE_WIDTH))
        min_base, max_base = 0, part.maxBaseIdx(id_num)
        if base_idx < min_base or base_idx >= max_base:
            base_idx = util.clamp(base_idx, min_base, max_base)
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strand_type = floor(y * 1. / _BASE_WIDTH)   # 0 for fwd, 1 for rev
        strand_type = int(util.clamp(strand_type, 0, 1))
        strand_set = part.getStrandSets(id_num)[strand_type]
        return (strand_set, base_idx)
    # end def

    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)
        """
        dx = self._part_item.part().stepSize() * _BASE_WIDTH
        return self.mapToScene(QRectF(0, 0, dx, 1)).boundingRect().width()
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        self._part_item.updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event (TYPE): Description
        """
        base_idx = int(floor(event.pos().x() / _BASE_WIDTH))
        loc = "%d[%d]" % (self._id_num, base_idx)
        self._part_item.updateStatusBar(loc)

        active_tool = self._getActiveTool()
        tool_method_name = active_tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            is_fwd, idx_x, idx_y = active_tool.baseAtPoint(self, event.pos())
            getattr(self, tool_method_name)(is_fwd, idx_x, idx_y)
    # end def

    ### TOOL METHODS ###
    def pencilToolMousePress(self, strand_set, idx, modifiers):
        """strand.getDragBounds

        Args:
            strand_set (StrandSet): Description
            idx (int): the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        if modifiers & Qt.ShiftModifier:
            bounds = strand_set.getBoundsOfEmptyRegionContaining(idx)
            ret = strand_set.createStrand(*bounds)
            print("creating strand {} was successful: {}".format(bounds, ret))
            return
        active_tool = self._getActiveTool()
        if not active_tool.isDrawingStrand():
            active_tool.initStrandItemFromVHI(self, strand_set, idx)
            active_tool.setIsDrawingStrand(True)
    # end def

    def pencilToolMouseMove(self, strand_set, idx):
        """strand.getDragBounds

        Args:
            strand_set (StrandSet): Description
            idx (int): the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.updateStrandItemFromVHI(self, strand_set, idx)
    # end def

    def pencilToolMouseRelease(self, strand_set, idx):
        """strand.getDragBounds

        Args:
            strand_set (StrandSet): Description
            idx (int): the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.setIsDrawingStrand(False)
            active_tool.attemptToCreateStrand(self, strand_set, idx)
    # end def

    def pencilToolHoverMove(self, is_fwd, idx_x, idx_y):
        """Pencil the strand is possible.

        Args:
            is_fwd (TYPE): Description
            idx_x (TYPE): Description
            idx_y (TYPE): Description
        """
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromVHI(self, is_fwd, idx_x, idx_y)
    # end def
