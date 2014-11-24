import sys
from math import floor
from .abstractpathtool import AbstractPathTool

from cadnano.gui.views.pathview import pathstyles as styles

import cadnano.util as util

from PyQt5.QtCore import Qt, QEvent, QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainterPath, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_PENCIL_COLOR = styles.RED_STROKE
_DEFAULT_RECT = QRectF(0,0, _BASE_WIDTH, _BASE_WIDTH)
_NO_PEN = QPen(Qt.NoPen)


class PencilTool(AbstractPathTool):
    """
    docstring for PencilTool
    """
    def __init__(self, controller):
        super(PencilTool, self).__init__(controller)
        self._temp_xover = ForcedXoverItem(self, None, None)
        self._temp_strand_item = ForcedStrandItem(self, None)
        self._temp_strand_item.hide()
        self._move_idx = None
        self._is_floating_xover_begin = True
        self._is_drawing_strand = False

    def __repr__(self):
        return "pencil_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "pencilTool"  # first letter should be lowercase

    def strandItem(self):
        return self._temp_strand_item
    # end def

    def deactivate(self):
        self.setIsDrawingStrand(False)
        self._temp_xover.deactivate()
        self.hide()

    def isDrawingStrand(self):
        return self._is_drawing_strand
    # end def

    def setIsDrawingStrand(self, boolval):
        self._is_drawing_strand = boolval
        if boolval == False:
            self._temp_strand_item.hideIt()
    # end def

    def initStrandItemFromVHI(self, virtual_helix_item, strand_set, idx):
        s_i = self._temp_strand_item
        self._start_idx = idx
        self._start_strand_set = strand_set
        s_i.resetStrandItem(virtual_helix_item, strand_set.isDrawn5to3())
        self._low_drag_bound, self._high_drag_bound = strand_set.getBoundsOfEmptyRegionContaining(idx)
    # end def

    def updateStrandItemFromVHI(self, virtual_helix_item, strand_set, idx):
        s_i = self._temp_strand_item
        s_idx = self._start_idx
        if abs(s_idx - idx) > 1 and self.isWithinBounds(idx):
            idxs = (idx, s_idx) if self.isDragLow(idx) else (s_idx, idx)
            s_i.strandResizedSlot(idxs)
            s_i.showIt()
        # end def
    # end def

    def isDragLow(self, idx):
        s_idx = self._start_idx
        if s_idx - idx > 0:
            return True
        else:
            return False
    # end def

    def isWithinBounds(self, idx):
        return self._low_drag_bound <= idx <= self._high_drag_bound
    # end def

    def attemptToCreateStrand(self, virtual_helix_item, strand_set, idx):
        self._temp_strand_item.hideIt()
        s_idx = self._start_idx
        if abs(s_idx - idx) > 1:
            idx = util.clamp(idx, self._low_drag_bound, self._high_drag_bound)
            idxs = (idx, s_idx) if self.isDragLow(idx) else (s_idx, idx)
            self._start_strand_set.createStrand(*idxs)
    # end def

    def floatingXover(self):
        return self._temp_xover
    # end def

    def isFloatingXoverBegin(self):
        return self._is_floating_xover_begin
    # end def

    def setFloatingXoverBegin(self, boolval):
        self._is_floating_xover_begin = boolval
        if boolval:
            self._temp_xover.hideIt()
        else:
            self._temp_xover.showIt()
    # end def

    def attemptToCreateXover(self, virtual_helix_item, strand3p, idx):
        xoi = self._temp_xover
        n5 = xoi._node5 
        idx5 = n5._idx
        strand5p = n5._strand
        part = virtual_helix_item.part()
        part.createXover(strand5p, idx5, strand3p, idx)
    # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        # print("forced xover keypress", a)
        if a in [Qt.Key_Control, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            QGraphicsObject.keyPressEvent(self, event)
        else:
            self.deactivate()
    # end def

# end class


class ForcedStrandItem(QGraphicsLineItem):
    def __init__(self, tool, virtual_helix_item):
        """The parent should be a VirtualHelixItem."""
        super(ForcedStrandItem, self).__init__(virtual_helix_item)
        self._virtual_helix_item = virtual_helix_item
        self._tool = tool

        is_drawn_5_to_3 = True

        # caps
        self._low_cap = EndpointItem(self, 'low', is_drawn_5_to_3)
        self._high_cap = EndpointItem(self, 'high', is_drawn_5_to_3)
        self._low_cap.disableEvents()
        self._high_cap.disableEvents()
        
        # orientation
        self._is_drawn_5_to_3 = is_drawn_5_to_3

        # create a larger click area rect to capture mouse events
        self._click_area = c_a = QGraphicsRectItem(_DEFAULT_RECT, self)
        c_a.mousePressEvent = self.mousePressEvent
        c_a.setPen(_NO_PEN)

        # c_a.setBrush(QBrush(Qt.white))
        self.setZValue(styles.ZENDPOINTITEM+1)
        c_a.setZValue(styles.ZENDPOINTITEM)
        self._low_cap.setZValue(styles.ZENDPOINTITEM+2)
        self._high_cap.setZValue(styles.ZENDPOINTITEM+2)
        c_a.setFlag(QGraphicsItem.ItemStacksBehindParent)

        self._updatePensAndBrushes()
        self.hideIt()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def strandResizedSlot(self, idxs):
        """docstring for strandResizedSlot"""
        lowMoved = self._low_cap.updatePosIfNecessary(idxs[0])
        highMoved = self._high_cap.updatePosIfNecessary(idxs[1])
        if lowMoved:
            self.updateLine(self._low_cap)
        if highMoved:
            self.updateLine(self._high_cap)
    # end def

    def strandRemovedSlot(self):
        scene = self.scene()
        scene.removeItem(self._click_area)
        scene.removeItem(self._high_cap)
        scene.removeItem(self._low_cap)

        self._click_area = None
        self._high_cap = None
        self._low_cap = None

        scene.removeItem(self)
    # end def

    ### ACCESSORS ###

    def virtualHelixItem(self):
        return self._virtual_helix_item

    def activeTool(self):
        return self._tool
    # end def

    def hideIt(self):
        self.hide()
        self._low_cap.hide()
        self._high_cap.hide()
        self._click_area.hide()
    # end def

    def showIt(self):
        self._low_cap.show()
        self._high_cap.show()
        self._click_area.show()
        self.show()
    # end def

    def resetStrandItem(self, virtualHelixItem, is_drawn_5_to_3):
        self.setParentItem(virtualHelixItem)
        self._virtual_helix_item = virtualHelixItem
        self.resetEndPointItems(is_drawn_5_to_3)
    # end def

    def resetEndPointItems(self, is_drawn_5_to_3):
        bw = _BASE_WIDTH
        self._is_drawn_5_to_3 = is_drawn_5_to_3
        self._low_cap.resetEndPoint(is_drawn_5_to_3)
        self._high_cap.resetEndPoint(is_drawn_5_to_3)
        line = self.line()
        p1 = line.p1()
        p2 = line.p2()
        if is_drawn_5_to_3:
            p1.setY(bw/2)
            p2.setY(bw/2)
            self._click_area.setY(0)
        else:
            p1.setY(3*bw/2)
            p2.setY(3*bw/2)
            self._click_area.setY(bw)
        line.setP1(p1)
        line.setP2(p2)
        self.setLine(line)
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def updateLine(self, moved_cap):
        # setup
        bw = _BASE_WIDTH
        c_a = self._click_area
        line = self.line()
        # set new line coords
        if moved_cap == self._low_cap:
            p1 = line.p1()
            newX = self._low_cap.pos().x() + bw
            p1.setX(newX)
            line.setP1(p1)
            temp = c_a.rect()
            temp.setLeft(newX-bw)
            c_a.setRect(temp)
        else:
            p2 = line.p2()
            newX = self._high_cap.pos().x()
            p2.setX(newX)
            line.setP2(p2)
            temp = c_a.rect()
            temp.setRight(newX+bw)
            c_a.setRect(temp)
        self.setLine(line)
    # end def

    def _updatePensAndBrushes(self):
        color = QColor(_PENCIL_COLOR)
        penWidth = styles.PATH_STRAND_STROKE_WIDTH
        pen = QPen(color, penWidth)
        brush = QBrush(color)
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
        self._low_cap.setBrush(brush)
        self._high_cap.setBrush(brush)
    # end def
# end class

_TO_HELIX_NUM_FONT = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_FM = QFontMetrics(_TO_HELIX_NUM_FONT)
_ENAB_BRUSH = QBrush(Qt.SolidPattern)  # Also for the helix number label
_NO_BRUSH = QBrush(Qt.NoBrush)

# _rect = QRectF(0, 0, baseWidth, baseWidth)
_xScale = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_yScale = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant
_rect = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_blankRect = QRectF(0, 0, 2*_BASE_WIDTH, _BASE_WIDTH)

PPL5 = QPainterPath()  # Left 5' PainterPath
PPR5 = QPainterPath()  # Right 5' PainterPath
PPL3 = QPainterPath()  # Left 3' PainterPath
PPR3 = QPainterPath()  # Right 3' PainterPath

# set up PPL5 (left 5' blue square)
PPL5.addRect(0.25*_BASE_WIDTH, 0.125*_BASE_WIDTH,0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
# set up PPR5 (right 5' blue square)
PPR5.addRect(0, 0.125*_BASE_WIDTH, 0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
# set up PPL3 (left 3' blue triangle)
L3_POLY = QPolygonF()
L3_POLY.append(QPointF(_BASE_WIDTH, 0))
L3_POLY.append(QPointF(0.25*_BASE_WIDTH, 0.5*_BASE_WIDTH))
L3_POLY.append(QPointF(_BASE_WIDTH, _BASE_WIDTH))
PPL3.addPolygon(L3_POLY)
# set up PPR3 (right 3' blue triangle)
R3_POLY = QPolygonF()
R3_POLY.append(QPointF(0, 0))
R3_POLY.append(QPointF(0.75*_BASE_WIDTH, 0.5*_BASE_WIDTH))
R3_POLY.append(QPointF(0, _BASE_WIDTH))
PPR3.addPolygon(R3_POLY)

class ForcedXoverNode3(QGraphicsRectItem):
    """
    This is a QGraphicsRectItem to allow actions and also a 
    QGraphicsSimpleTextItem to allow a label to be drawn
    """
    def __init__(self, virtual_helix_item, xover_item, strand3p, idx):
        super(ForcedXoverNode3, self).__init__(virtual_helix_item)
        self._vhi = virtual_helix_item
        self._xover_item = xover_item
        self._idx = idx
        self._is_on_top = virtual_helix_item.isStrandOnTop(strand3p)
        self._is_drawn_5_to_3 = strand3p.strandSet().isDrawn5to3()
        self._strand_type = strand3p.strandSet().strandType()

        self._partner_virtual_helix = virtual_helix_item

        self._blank_thing = QGraphicsRectItem(_blankRect, self)
        self._blank_thing.setBrush(QBrush(Qt.white))
        self._path_thing = QGraphicsPathItem(self)
        self.configurePath()

        self.setPen(_NO_PEN)
        self._label = None
        self.setPen(_NO_PEN)
        self.setBrush(_NO_BRUSH)
        self.setRect(_rect)

        self.setZValue(styles.ZENDPOINTITEM + 1)
    # end def

    def updateForFloatFromVHI(self, virtual_helix_item, strand_type, idx_x, idx_y):
        """

        """
        self._vhi = virtual_helix_item
        self.setParentItem(virtual_helix_item)
        self._strand_type = strand_type
        self._idx = idx_x
        self._is_on_top = self._is_drawn_5_to_3 = True if idx_y == 0 else False
        self.updatePositionAndAppearance(is_from_strand=False)
    # end def

    def updateForFloatFromStrand(self, virtual_helix_item, strand3p, idx):
        """

        """
        self._vhi = virtual_helix_item
        self._strand = strand3p
        self.setParentItem(virtual_helix_item)
        self._idx = idx
        self._is_on_top = virtual_helix_item.isStrandOnTop(strand3p)
        self._is_drawn_5_to_3 = strand3p.strandSet().isDrawn5to3()
        self._strand_type = strand3p.strandSet().strandType()
        self.updatePositionAndAppearance()
    # end def

    def strandType(self):
        return self._strand_type
    # end def

    def configurePath(self):
        self._path_thing.setBrush(QBrush(styles.RED_STROKE))
        path = PPR3 if self._is_drawn_5_to_3 else PPL3
        offset = -_BASE_WIDTH if self._is_drawn_5_to_3 else _BASE_WIDTH
        self._path_thing.setPath(path)
        self._path_thing.setPos(offset, 0)

        offset = -_BASE_WIDTH if self._is_drawn_5_to_3 else 0
        self._blank_thing.setPos(offset, 0)

        self._blank_thing.show()
        self._path_thing.show()
    # end def

    def refreshXover(self):
        self._xover_item.refreshXover()
    # end def

    def setPartnerVirtualHelix(self, virtual_helix_item):
        self._partner_virtual_helix = virtual_helix_item
    # end def

    def idx(self):
        return self._idx
    # end def

    def virtualHelixItem(self):
        return self._vhi
    # end def

    def point(self):
        return self._vhi.upperLeftCornerOfBaseType(self._idx, self._strand_type)
    # end def

    def floatPoint(self):
        pt = self.pos()
        return pt.x(), pt.y()
    # end def

    def isOnTop(self):
        return self._is_on_top
    # end def

    def isDrawn5to3(self):
        return self._is_drawn_5_to_3
    # end def

    def updatePositionAndAppearance(self, is_from_strand=True):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.
        """
        self.setPos(*self.point())
        n5 = self._xover_item._node5
        if is_from_strand:
            from_strand, from_idx = (n5._strand, n5._idx) if n5 != self else (None, None)
            if self._strand.canInstallXoverAt(self._idx, from_strand, from_idx):
                self.configurePath()
                # We can only expose a 5' end. But on which side?
                is_left = True if self._is_drawn_5_to_3 else False
                self._updateLabel(is_left)
            else:
                self.hideItems()
        else:
            self.hideItems()
    # end def

    def updateConnectivity(self):
        is_left = True if self._is_drawn_5_to_3 else False
        self._updateLabel(is_left)
    # end def

    def remove(self):
        """
        Clean up this joint
        """
        scene = self.scene()
        scene.removeItem(self._label)
        self._label = None
        scene.removeItem(self._path_thing)
        self._path_thing = None
        scene.removeItem(self._blank_thing)
        self._blank_thing = None
        scene.removeItem(self)
    # end def

    def _updateLabel(self, is_left):
        """
        Called by updatePositionAndAppearance during init, or later by
        updateConnectivity. Updates drawing and position of the label.
        """
        lbl = self._label
        if self._idx != None:
            bw = _BASE_WIDTH
            num = self._partner_virtual_helix.number()
            tBR = _FM.tightBoundingRect(str(num))
            half_label_h = tBR.height()/2.0
            half_label_w = tBR.width()/2.0
            # determine x and y positions
            label_x = bw/2.0 - half_label_w
            if self._is_on_top:
                label_y = -0.25*half_label_h - 0.5 - 0.5*bw
            else:
                label_y = 2*half_label_h + 0.5 + 0.5*bw
            # adjust x for left vs right
            label_x_offset = 0.25*bw if is_left else -0.25*bw
            label_x += label_x_offset
            # adjust x for numeral 1
            if num == 1: label_x -= half_label_w/2.0
            # create text item
            if lbl == None:
                lbl = QGraphicsSimpleTextItem(str(num), self)
            lbl.setPos(label_x, label_y)
            lbl.setBrush(_ENAB_BRUSH)
            lbl.setFont(_TO_HELIX_NUM_FONT)
            self._label = lbl

            lbl.setText( str(self._partner_virtual_helix.number()) )
            lbl.show()
        # end if
    # end def

    def hideItems(self):
        if self._label:
            self._label.hide()
        if self._blank_thing:
            self._path_thing.hide()
        if self._blank_thing:
            self._blank_thing.hide()
    # end def
# end class


class ForcedXoverNode5(ForcedXoverNode3):
    """
    XoverNode5 is the partner of XoverNode3. It dif
    XoverNode3 handles:
    1. Drawing of the 5' end of an xover, and its text label. Drawing style
    is determined by the location of the xover with in a vhelix (is it a top
    or bottom vstrand?).
    2. Notifying XoverStrands in the model when connectivity changes.

    """
    def __init__(self, virtual_helix_item, xover_item, strand5p, idx):
        super(ForcedXoverNode5, self).__init__(virtual_helix_item, xover_item, strand5p, idx)
    # end def

    def configurePath(self):
        self._path_thing.setBrush(QBrush(styles.RED_STROKE))
        path = PPL5 if self._is_drawn_5_to_3 else PPR5
        offset = _BASE_WIDTH if self._is_drawn_5_to_3 else -_BASE_WIDTH
        self._path_thing.setPath(path)
        self._path_thing.setPos(offset, 0)

        offset = 0 if self._is_drawn_5_to_3 else -_BASE_WIDTH
        self._blank_thing.setPos(offset, 0)

        self._blank_thing.show()
        self._path_thing.show()
    # end def

    def updatePositionAndAppearance(self, is_from_strand=True):
        """Same as XoverItem3, but exposes 3' end"""
        self.setPos(*self.point())
        self.configurePath()
        # # We can only expose a 3' end. But on which side?
        is_left = False if self._is_drawn_5_to_3 else True
        self._updateLabel(is_left)
    # end def
# end class

class ForcedXoverItem(QGraphicsPathItem):
    """
    This class handles:
    1. Drawing the spline between the XoverNode3 and XoverNode5 graphics
    items in the path view.

    XoverItem should be a child of a PartItem.
    """

    def __init__(self, tool, part_item, virtual_helix_item):
        """
        strand_item is a the model representation of the 5prime most strand
        of a Xover
        """
        super(ForcedXoverItem, self).__init__(part_item)
        self._tool = tool
        self._virtual_helix_item = virtual_helix_item
        self._strand_type = None
        self._node5 = None
        self._node3 = None
        self.setFlag(QGraphicsItem.ItemIsFocusable) # for keyPressEvents
        self.setZValue(styles.ZPATHTOOL)
        self.hide()
    # end def

    ### SLOTS ###

    ### METHODS ###
    def remove(self):
        scene = self.scene()
        if self._node3 is not None:
            scene.removeItem(self._node3)
            scene.removeItem(self._node5)
        scene.removeItem(self)
    # end def

    def deactivate(self):
        self._tool.setFloatingXoverBegin(True)

    def strandType(self):
        return self._strand_type
    # end def
    
    def hide5prime(self):
        self._node5._path_thing.hide()

    def hide3prime(self):
        self._node3._path_thing.hide()
        
    def show3prime(self):
        if self._node3._blank_thing.isVisible():
            self._node3._path_thing.show()

    def hideIt(self):
        self.hide()
        self.clearFocus()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
    # end def

    def showIt(self):
        self.show()
        self.setFocus()
        if self._node3:
            self._node3.show()
            self._node5.show()
    # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        # print("forced xover keypress", a)
        if a in [Qt.Key_Control, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            QGraphicsPathItem.keyPressEvent(self, event)
        else:
            self._tool.setFloatingXoverBegin(True)
    # end def

    def updateBase(self, virtual_helix_item, strand5p, idx):
        # floating Xover!
        self._virtual_helix_item = virtual_helix_item
        self.setParentItem(virtual_helix_item.partItem())
        self._strand_type = strand5p.strandSet().strandType()
        if self._node5 == None:
            self._node5 = ForcedXoverNode5(virtual_helix_item, self, strand5p, idx)
            self._node3 = ForcedXoverNode3(virtual_helix_item, self, strand5p, idx)
        self._node5.updateForFloatFromStrand(virtual_helix_item, strand5p, idx)
        self._node3.updateForFloatFromStrand(virtual_helix_item, strand5p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromVHI(self, virtual_helix_item, strandType, idx_x, idx_y):
        # floating Xover!
        self._node5.setPartnerVirtualHelix(virtual_helix_item)
        self._node5.updatePositionAndAppearance()
        self._node3.setPartnerVirtualHelix(self._virtual_helix_item)
        self._node3.updateForFloatFromVHI(virtual_helix_item, strandType, idx_x, idx_y)
        self.updateFloatPath()
    # end def

    def updateFloatingFromStrandItem(self, virtual_helix_item, strand3p, idx):
        # floating Xover!
        self._node3.updateForFloatFromStrand(virtual_helix_item, strand3p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromPartItem(self, part_item, pt):
        self._node3.hideItems()
        self.updateFloatPath(pt)
    # end def

    def updateFloatPath(self, point=None):
        """
        Draws a quad curve from the edge of the fromBase
        to the top or bottom of the toBase (q5), and
        finally to the center of the toBase (toBaseEndpoint).

        If floatPos!=None, this is a floatingXover and floatPos is the
        destination point (where the mouse is) while toHelix, toIndex
        are potentially None and represent the base at floatPos.

        """
        node3 = self._node3
        node5 = self._node5

        bw = _BASE_WIDTH

        vhi5 = self._virtual_helix_item
        part_item = vhi5.partItem()
        pt5 = vhi5.mapToItem(part_item, *node5.floatPoint())

        five_is_top = node5.isOnTop()
        five_is_5_to_3 = node5.isDrawn5to3()

        # Enter/exit are relative to the direction that the path travels
        # overall.
        five_enter_pt = pt5 + QPointF(0 if five_is_5_to_3 else 1, .5)*bw
        five_center_pt = pt5 + QPointF(.5, .5)*bw
        five_exit_pt = pt5 + QPointF(.5, 0 if five_is_top else 1)*bw

        vhi3 = node3.virtualHelixItem()

        if point:
            pt3 = point
            three_is_top = True
            three_is_5_to_3 = True
            same_strand = False
            same_parity = False
            three_enter_pt = three_center_pt = three_exit_pt = pt3
        else: 
            pt3 = vhi3.mapToItem(part_item, *node3.point())
            three_is_top = node3.isOnTop()
            three_is_5_to_3 = node3.isDrawn5to3()
            same_strand = (node5.strandType() == node3.strandType()) and vhi3 == vhi5
            same_parity = five_is_5_to_3 == three_is_5_to_3

            three_enter_pt = pt3 + QPointF(.5, 0 if three_is_top else 1)*bw
            three_center_pt = pt3 + QPointF(.5, .5)*bw
            three_exit_pt = pt3 + QPointF(1 if three_is_5_to_3 else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if same_strand:
            dx = abs(three_enter_pt.x() - five_exit_pt.x())
            c1.setX(0.5 * (five_exit_pt.x() + three_enter_pt.x()))
            if five_is_top:
                c1.setY(five_exit_pt.y() - _yScale * dx)
            else:
                c1.setY(five_exit_pt.y() + _yScale * dx)
            # case 2: same parity
        elif same_parity:
             dy = abs(three_enter_pt.y() - five_exit_pt.y())
             c1.setX(five_exit_pt.x() + _xScale * dy)
             c1.setY(0.5 * (five_exit_pt.y() + three_enter_pt.y()))
        # case 3: different parity
        else:
            if five_is_top and five_is_5_to_3:
                c1.setX(five_exit_pt.x() - _xScale *\
                        abs(three_enter_pt.y() - five_exit_pt.y()))
            else:
                c1.setX(five_exit_pt.x() + _xScale *\
                        abs(three_enter_pt.y() - five_exit_pt.y()))
            c1.setY(0.5 * (five_exit_pt.y() + three_enter_pt.y()))

        # Construct painter path
        painterpath = QPainterPath()
        painterpath.moveTo(five_enter_pt)
        painterpath.lineTo(five_center_pt)
        painterpath.lineTo(five_exit_pt)
        painterpath.quadTo(c1, three_enter_pt)
        painterpath.lineTo(three_center_pt)
        painterpath.lineTo(three_exit_pt)

        self.setPath(painterpath)
        self._updateFloatPen()
    # end def

    # def _updatePen(self, strand5p):
    #     oligo = strand5p.oligo()
    #     color = QColor(oligo.color())
    #     penWidth = styles.PATH_STRAND_STROKE_WIDTH
    #     if oligo.shouldHighlight():
    #         penWidth = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
    #         color.setAlpha(128)
    #     pen = QPen(color, penWidth)
    #     pen.setCapStyle(Qt.FlatCap)
    #     self.setPen(pen)
    # # end def

    def _updateFloatPen(self):
        pen_width = styles.PATH_STRAND_STROKE_WIDTH
        pen = QPen(_PENCIL_COLOR, pen_width)
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
    # end def
# end class XoverItem

PPL5 = QPainterPath()  # Left 5' PainterPath
PPR5 = QPainterPath()  # Right 5' PainterPath
PPL3 = QPainterPath()  # Left 3' PainterPath
PPR3 = QPainterPath()  # Right 3' PainterPath
PP53 = QPainterPath()  # Left 5', Right 3' PainterPath
PP35 = QPainterPath()  # Left 5', Right 3' PainterPath
# set up PPL5 (left 5' blue square)
PPL5.addRect(0.25*_BASE_WIDTH, 0.125*_BASE_WIDTH,0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
# set up PPR5 (right 5' blue square)
PPR5.addRect(0, 0.125*_BASE_WIDTH, 0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
# set up PPL3 (left 3' blue triangle)
L3_POLY = QPolygonF()
L3_POLY.append(QPointF(_BASE_WIDTH, 0))
L3_POLY.append(QPointF(0.25*_BASE_WIDTH, 0.5*_BASE_WIDTH))
L3_POLY.append(QPointF(_BASE_WIDTH, _BASE_WIDTH))
PPL3.addPolygon(L3_POLY)
# set up PPR3 (right 3' blue triangle)
R3_POLY = QPolygonF()
R3_POLY.append(QPointF(0, 0))
R3_POLY.append(QPointF(0.75*_BASE_WIDTH, 0.5*_BASE_WIDTH))
R3_POLY.append(QPointF(0, _BASE_WIDTH))
PPR3.addPolygon(R3_POLY)

# single base left 5'->3'
PP53.addRect(0, 0.125*_BASE_WIDTH, 0.5*_BASE_WIDTH, 0.75*_BASE_WIDTH)
POLY_53 = QPolygonF()
POLY_53.append(QPointF(0.5*_BASE_WIDTH, 0))
POLY_53.append(QPointF(_BASE_WIDTH, 0.5*_BASE_WIDTH))
POLY_53.append(QPointF(0.5*_BASE_WIDTH, _BASE_WIDTH))
PP53.addPolygon(POLY_53)
# single base left 3'<-5'
PP35.addRect(0.50*_BASE_WIDTH, 0.125*_BASE_WIDTH, 0.5*_BASE_WIDTH, 0.75*_BASE_WIDTH)
POLY_35 = QPolygonF()
POLY_35.append(QPointF(0.5*_BASE_WIDTH, 0))
POLY_35.append(QPointF(0, 0.5*_BASE_WIDTH))
POLY_35.append(QPointF(0.5*_BASE_WIDTH, _BASE_WIDTH))
PP35.addPolygon(POLY_35)

class EndpointItem(QGraphicsPathItem):
    def __init__(self, strand_item, cap_type, is_drawn_5_to_3):
        """The parent should be a StrandItem."""
        super(EndpointItem, self).__init__(strand_item.virtualHelixItem())

        self._strand_item = strand_item
        self._getActiveTool = strand_item.activeTool()
        self._cap_type = cap_type
        self._low_drag_bound = None
        self._high_drag_bound = None
        self._initCapSpecificState(is_drawn_5_to_3)
        self.setPen(_NO_PEN)
        # for easier mouseclick
        self._click_area = c_a = QGraphicsRectItem(_DEFAULT_RECT, self)
        self._click_area.setAcceptHoverEvents(True)
        c_a.hoverMoveEvent = self.hoverMoveEvent
        c_a.mousePressEvent = self.mousePressEvent
        c_a.mouseMoveEvent = self.mouseMoveEvent
        c_a.setPen(_NO_PEN)
        
    # end def

    def __repr__(self):
        return "%s" % self.__class__.__name__

    ### SIGNALS ###

    ### SLOTS ###

    ### ACCESSORS ###
    def idx(self):
        """Look up baseIdx, as determined by strand_item idxs and cap type."""
        if self._cap_type == 'low':
            return self._strand_item.idxs()[0]
        else:  # high or dual, doesn't matter
            return self._strand_item.idxs()[1]
    # end def
    
    def partItem(self):
        return self._strand_item.partItem()
    # end def

    def disableEvents(self):
        self._click_area.setAcceptHoverEvents(False)
        self.mouseMoveEvent = QGraphicsPathItem.mouseMoveEvent
        self.mousePressEvent = QGraphicsPathItem.mousePressEvent
    # end def

    def window(self):
        return self._strand_item.window()

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def updatePosIfNecessary(self, idx):
        """Update position if necessary and return True if updated."""
        x = int(idx*_BASE_WIDTH)
        if x != self.x():
            self.setPos(x, self.y())
            return True
        return False

    def resetEndPoint(self, is_drawn_5_to_3):
        self.setParentItem(self._strand_item.virtualHelixItem())
        self._initCapSpecificState(is_drawn_5_to_3)
        upper_left_y = 0 if is_drawn_5_to_3 else _BASE_WIDTH
        self.setY(upper_left_y)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _initCapSpecificState(self, is_drawn_5_to_3):
        c_t = self._cap_type
        if c_t == 'low':
            path = PPL5 if is_drawn_5_to_3 else PPL3
        elif c_t == 'high':
            path = PPR3 if is_drawn_5_to_3 else PPR5
        elif c_t == 'dual':
            path = PP53 if is_drawn_5_to_3 else PP35
        self.setPath(path)
    # end def

    def _getNewIdxsForResize(self, baseIdx):
        """Returns a tuple containing idxs to be passed to the """
        c_t = self._cap_type
        if c_t == 'low':
            return (baseIdx, self._strand_item.idxs()[1])
        elif c_t == 'high':
            return (self._strand_item.idxs()[0], baseIdx)
        elif c_t == 'dual':
            raise NotImplementedError

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.
        """
        self.scene().views()[0].addToPressList(self)
        self._strand_item.virtualHelixItem().setActive(self.idx())
        self._move_idx = self.idx()
        active_tool_str = self._getActiveTool().methodPrefix()
        if active_tool_str == 'pencilTool':
            return self._strand_item.pencilToolMousePress(self.idx())
        tool_method_name = active_tool_str + "MousePress"
        if hasattr(self, tool_method_name):  # if the tool method exists
            modifiers = event.modifiers()
            getattr(self, tool_method_name)(modifiers)  # call tool method

    def hoverMoveEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.
        """
        active_tool_str = self._getActiveTool().methodPrefix()
        if active_tool_str == 'pencilTool':
            return self._strand_item.pencilToolHoverMove(event, self.idx())

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent, calling the approproate tool method as
        necessary. Updates _move_idx if it changed.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):  # if the tool method exists
            idx = int(floor((self.x()+event.pos().x()) / _BASE_WIDTH))
            if idx != self._move_idx:  # did we actually move?
                modifiers = event.modifiers()
                self._move_idx = idx
                getattr(self, tool_method_name)(modifiers, idx)  # call tool method

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent, calling the approproate tool method as
        necessary. Deletes _move_idx if necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):  # if the tool method exists
            modifiers = event.modifiers()
            x = event.pos().x()
            getattr(self, tool_method_name)(modifiers, x)  # call tool method
        if hasattr(self, '_move_idx'):
            del self._move_idx
# end class