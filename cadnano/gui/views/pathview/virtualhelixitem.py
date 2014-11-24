#!/usr/bin/env python
# encoding: utf-8

from math import floor
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.enum import StrandType
from .strand.stranditem import StrandItem
from . import pathstyles as styles
from .virtualhelixhandleitem import VirtualHelixHandleItem
import cadnano.util as util

from PyQt5.QtCore import QRectF, Qt, QObject, pyqtSignal
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem

_BASE_WIDTH = styles.PATH_BASE_WIDTH
# _gridPen = QPen(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
# _gridPen.setCosmetic(True)


class VirtualHelixItem(QGraphicsPathItem):
    """VirtualHelixItem for PathView"""
    findChild = util.findChild  # for debug

    def __init__(self, part_item, model_virtual_helix, viewroot):
        super(VirtualHelixItem, self).__init__(part_item.proxy())
        self._part_item = part_item
        self._model_virtual_helix = model_virtual_helix
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, model_virtual_helix)
        
        self._handle = VirtualHelixHandleItem(model_virtual_helix, part_item, viewroot)
        self._last_strand_set = None
        self._last_idx = None
        self._scaffoldBackground = None
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setBrush(QBrush(Qt.NoBrush))

        view = viewroot.scene().views()[0]
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        shouldShowDetails = view.shouldShowDetails()

        pen = QPen(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(shouldShowDetails)
        self.setPen(pen)
        
        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    
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

    def virtualHelixNumberChangedSlot(self, virtualHelix, number):
        self._handle.setNumber()
    # end def

    def virtualHelixRemovedSlot(self, virtualHelix):
        self._controller.disconnectSignals()
        self._controller = None
        
        scene = self.scene()
        self._handle.remove()
        scene.removeItem(self)
        self._part_item.removeVirtualHelixItem(self)
        self._part_item = None
        self._model_virtual_helix = None
        self._getActiveTool = None
        self._handle = None
    # end def

    ### ACCESSORS ###

    def coord(self):
        return self._model_virtual_helix.coord()
    # end def

    def viewroot(self):
        return self._viewroot
    # end def

    def handle(self):
        return self._handle
    # end def

    def part(self):
        return self._part_item.part()
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def number(self):
        return self._model_virtual_helix.number()
    # end def

    def virtualHelix(self):
        return self._model_virtual_helix
    # end def

    def window(self):
        return self._part_item.window()
    # end def

    ### DRAWING METHODS ###
    def isStrandOnTop(self, strand):
        sS = strand.strandSet()
        isEvenParity = self._model_virtual_helix.isEvenParity()
        return isEvenParity and sS.isScaffold() or\
               not isEvenParity and sS.isStaple()
    # end def

    def isStrandTypeOnTop(self, strand_type):
        isEvenParity = self._model_virtual_helix.isEvenParity()
        return isEvenParity and strand_type == StrandType.SCAFFOLD or \
               not isEvenParity and strand_type == StrandType.STAPLE
    # end def

    def upperLeftCornerOfBase(self, idx, strand):
        x = idx * _BASE_WIDTH
        y = 0 if self.isStrandOnTop(strand) else _BASE_WIDTH
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx, strand_type):
        x = idx * _BASE_WIDTH
        y = 0 if self.isStrandTypeOnTop(strand_type) else _BASE_WIDTH
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
        canvas_size = part.maxBaseIdx() + 1
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
        
        if self._model_virtual_helix.scaffoldIsOnTop():
            scaffoldY = 0
        else:
            scaffoldY = bw
        # if self._scaffoldBackground == None:
        #     highlightr = QGraphicsRectItem(0, scaffoldY, bw * canvas_size, bw, self)
        #     highlightr.setBrush(QBrush(styles.scaffold_bkg_fill))
        #     highlightr.setPen(QPen(Qt.NoPen))
        #     highlightr.setFlag(QGraphicsItem.ItemStacksBehindParent)
        #     self._scaffoldBackground = highlightr
        # else:
        #     self._scaffoldBackground.setRect(0, scaffoldY, bw * canvas_size, bw)
            
    # end def

    def resize(self):
        """Called by part on resize."""
        self.refreshPath()

    ### PUBLIC SUPPORT METHODS ###
    def setActive(self, idx):
        """Makes active the virtual helix associated with this item."""
        self.part().setActiveVirtualHelix(self._model_virtual_helix, idx)
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
        tool_method_name = self._getActiveTool().methodPrefix() + "MousePress"

        ### uncomment for debugging modifier selection
        # strand_set, idx = self.baseAtPoint(event.pos())
        # row, col = strand_set.virtualHelix().coord()
        # self._part_item.part().selectPreDecorator([(row,col,idx)])

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
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseMove"
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
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(self._last_strand_set, self._last_idx)
        else:
            event.setAccepted(False)
    # end def

    ### COORDINATE UTILITIES ###
    def baseAtPoint(self, pos):
        """
        Returns the (strand_type, index) under the location x,y or None.

        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.
        """
        x, y = pos.x(), pos.y()
        mVH = self._model_virtual_helix
        base_idx = int(floor(x / _BASE_WIDTH))
        min_base, max_base = 0, mVH.part().maxBaseIdx()
        if base_idx < min_base or base_idx >= max_base:
            base_idx = util.clamp(base_idx, min_base, max_base)
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strandIdx = floor(y * 1. / _BASE_WIDTH)
        if strandIdx < 0 or strandIdx > 1:
            strandIdx = int(util.clamp(strandIdx, 0, 1))
        strand_set = mVH.getStrandSetByIdx(strandIdx)
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
        loc = "%d[%d]" % (self.number(), base_idx)
        self._part_item.updateStatusBar(loc)

        active_tool = self._getActiveTool()
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            strand_type, idx_x, idx_y = active_tool.baseAtPoint(self, event.pos())
            getattr(self, tool_method_name)(strand_type, idx_x, idx_y)
    # end def

    ### TOOL METHODS ###
    def pencilToolMousePress(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if not active_tool.isDrawingStrand():
            active_tool.initStrandItemFromVHI(self, strand_set, idx)
            active_tool.setIsDrawingStrand(True)
    # end def

    def pencilToolMouseMove(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.updateStrandItemFromVHI(self, strand_set, idx)
    # end def

    def pencilToolMouseRelease(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.setIsDrawingStrand(False)
            active_tool.attemptToCreateStrand(self, strand_set, idx)
    # end def

    def pencilToolHoverMove(self, strand_type, idx_x, idx_y):
        """Pencil the strand is possible."""
        part_item = self.partItem()
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromVHI(self, strand_type, idx_x, idx_y)
    # end def
