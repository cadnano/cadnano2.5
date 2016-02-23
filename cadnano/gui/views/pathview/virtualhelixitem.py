#!/usr/bin/env python
# encoding: utf-8

from math import floor

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsEllipseItem

from cadnano import util
from cadnano.enum import StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import newPenObj, getNoPen, getPenObj, getBrushObj, getNoBrush
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from .strand.stranditem import StrandItem
from .virtualhelixhandleitem import VirtualHelixHandleItem
from . import pathstyles as styles

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_VH_XOFFSET = styles.VH_XOFFSET

def v2DistanceAndAngle(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)
    return dist, angle


class VirtualHelixItem(AbstractVirtualHelixItem, QGraphicsPathItem):
    """VirtualHelixItem for PathView"""
    findChild = util.findChild  # for debug

    def __init__(self, id_num, part_item, viewroot):
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        QGraphicsPathItem.__init__(self, parent=part_item.proxy())
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self._handle = VirtualHelixHandleItem(self, part_item, viewroot)
        self._last_strand_set = None
        self._last_idx = None
        self._scaffold_background = None
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setBrush(getNoBrush())

        view = viewroot.scene().views()[0]
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        should_show_details = view.shouldShowDetails()

        pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(should_show_details)
        self.setPen(pen)

        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)

    # end def

    ### SIGNALS ###

    ### SLOTS indirectly called from the part ###

    def levelOfDetailChangedSlot(self, boolval):
        """Not connected to the model, only the QGraphicsView"""
        pen = self.pen()
        pen.setCosmetic(boolval)
        self.setPen(pen)
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        StrandItem(strand, self, self._viewroot)
    # end def

    def decoratorAddedSlot(self, decorator):
        """
        Instantiates a DecoratorItem upon notification that the model has a
        new Decorator.  The Decorator is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        pass

    # def partPropertyChangedSlot(self, model_part, property_key, new_value):
    #     if property_key == 'color':
    #         self._handle.refreshColor()
    # # end def

    def virtualHelixRemovedSlot(self):
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
        for key, val in zip(keys, values):
            if key == 'is_visible':
                if val:
                    self.show()
                    self._handle.show()
                else:
                    self.hide()
                    self._handle.hide()
                    return
            # if key == 'z':
            #     z = float(value)
            #     self.setX(z)
            #     self._handle.setX(z-_VH_XOFFSET)
            #     self.part().partDimensionsChangedSignal.emit(self.part(), True)
            # elif key == 'eulerZ':
            #     self._handle.rotateWithCenterOrigin(value)
            #     self._prexoveritemgroup.updatePositionsAfterRotation(value)
            ### GEOMETRY PROPERTIES ###
            elif key == 'repeats':
                self.updateRepeats(int(value))
            elif key == 'bases_per_repeat':
                self.updateBasesPerRepeat(int(value))
            elif key == 'turns_per_repeat':
                self.updateTurnsPerRepeat(int(value))
            ### RUNTIME PROPERTIES ###
            elif key == 'active_phos':  # this draws the curves
                # hpxig = self._handle._prexoveritemgroup
                pxoig = self._part_item.prexoveritemgroup
                if val is not None:
                    # vh-handle
                    id_num, is_fwd, idx, to_vh_id_num = val
                    # h_item = hpxoig.getItem(id_num, is_fwd, idx)
                    # hpxoig.updateViewActivePhos(h_item)
                    pxo_item = pxoig.getItem(id_num, is_fwd, idx)
                    pxoig.updateViewActivePhos(pxo_item)
                else:
                    # hpxoig.updateViewActivePhos(None) # vh-handle
                    pxoig.updateViewActivePhos(None) # vh
            elif key == 'neighbor_active_angle':
                # hpxoig = self._handle._prexoveritemgroup
                pxoig = self._part_item.prexoveritemgroup
                if val is not None:
                    id_num, is_fwd, idx, to_vh_id_num = val
                    # # handle
                    # local_angle = (int(value) + 180) % 360
                    # h_fwd_items, h_rev_items = hpxoig.getItemsFacingNearAngle(local_angle)
                    # for h_item in h_fwd_items + h_rev_items:
                    #     h_item.updateItemApperance(True, show_3p=False)
                    # # path
                    pxoig.setActiveNeighbors(id_num, is_fwd, idx)
                else:
                    # handle
                    # hpxoig.resetAllItemsAppearance()
                    # path
                    pxoig.setActiveNeighbors(None, None, None)
            elif key == 'neighbors':
                pxoig = self._prexoveritemgroup
                self.refreshProximalItems()
        self.refreshPath()
    # end def

    ### ACCESSORS ###
    def viewroot(self):
        return self._viewroot
    # end def

    def handle(self):
        return self._handle
    # end def

    def window(self):
        return self._part_item.window()
    # end def

    ### DRAWING METHODS ###
    def upperLeftCornerOfBase(self, idx, strand):
        x = idx * _BASE_WIDTH
        y = 0 if strand.isForward() else _BASE_WIDTH
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx, is_fwd):
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
        canvas_size = self.getSize()
        # border
        path.addRect(0, 0, bw * canvas_size, 2 * bw)
        # minor tick marks
        for i in range(canvas_size):
            x = round(bw * i) + .5
            if i % sub_step_size == 0:
                path.moveTo(x - .5,  0)
                path.lineTo(x - .5,  bw2)
                path.lineTo(x - .25, bw2)
                path.lineTo(x - .25, 0)
                path.lineTo(x,       0)
                path.lineTo(x,       bw2)
                path.lineTo(x + .25, bw2)
                path.lineTo(x + .25, 0)
                path.lineTo(x + .5,  0)
                path.lineTo(x + .5,  bw2)

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

        scaffoldY = bw
    # end def

    def resize(self):
        """Called by part on resize."""
        self.refreshPath()

    ### PUBLIC SUPPORT METHODS ###
    def setActive(self, idx):
        """Makes active the virtual helix associated with this item."""
        self.part().setActiveVirtualHelix(self._id_num, idx)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
        self.scene().views()[0].addToPressList(self)
        strand_set, idx = self.baseAtPoint(event.pos())
        self.setActive(idx)
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"

        if hasattr(self, tool_method_name):
            self._last_strand_set, self._last_idx = strand_set, idx
            getattr(self, tool_method_name)(strand_set, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
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

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
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
        the scene (in scene space)"""
        dx = self._part_item.part().stepSize() * _BASE_WIDTH
        return self.mapToScene(QRectF(0, 0, dx, 1)).boundingRect().width()
    # end def

    def hoverLeaveEvent(self, event):
        self._part_item.updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
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
    def pencilToolMousePress(self, strand_set, idx):
        """strand.getDragBounds"""
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if not active_tool.isDrawingStrand():
            active_tool.initStrandItemFromVHI(self, strand_set, idx)
            active_tool.setIsDrawingStrand(True)
    # end def

    def pencilToolMouseMove(self, strand_set, idx):
        """strand.getDragBounds"""
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.updateStrandItemFromVHI(self, strand_set, idx)
    # end def

    def pencilToolMouseRelease(self, strand_set, idx):
        """strand.getDragBounds"""
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.setIsDrawingStrand(False)
            active_tool.attemptToCreateStrand(self, strand_set, idx)
    # end def

    def pencilToolHoverMove(self, is_fwd, idx_x, idx_y):
        """Pencil the strand is possible."""
        part_item = self.partItem()
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromVHI(self, is_fwd, idx_x, idx_y)
    # end def
