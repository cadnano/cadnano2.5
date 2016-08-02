"""Summary

Attributes:
    L3_POLY (TYPE): Description
    POLY_35 (TYPE): Description
    POLY_53 (TYPE): Description
    PP35 (TYPE): Description
    PP53 (TYPE): Description
    PPL3 (TYPE): Description
    PPL5 (TYPE): Description
    PPR3 (TYPE): Description
    PPR5 (TYPE): Description
    R3_POLY (TYPE): Description
"""
from math import floor

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtGui import QFontMetrics, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsObject
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsSimpleTextItem

from cadnano import util
from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.views.pathview import pathstyles as styles

from .abstractpathtool import AbstractPathTool


_BASE_WIDTH = styles.PATH_BASE_WIDTH
_PENCIL_COLOR = styles.RED_STROKE
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_NO_PEN = QPen(Qt.NoPen)


class PencilTool(AbstractPathTool):
    """
    docstring for PencilTool
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(PencilTool, self).__init__(manager)
        self._temp_xover = ForcedXoverItem(self, None, None)
        self._temp_strand_item = ForcedStrandItem(self, None)
        self._temp_strand_item.hide()
        self._move_idx = None
        self._is_floating_xover_begin = True
        self._is_drawing_strand = False

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "pencil_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "pencilTool"  # first letter should be lowercase

    def strandItem(self):
        """Summary

        Returns:
            ForcedStrandItem: Description
        """
        return self._temp_strand_item
    # end def

    def deactivate(self):
        """setIsDrawingStrand to False, deactive() the temp_xover, and hide.
        """
        self.setIsDrawingStrand(False)
        self._temp_xover.deactivate()
        self.hide()

    def isDrawingStrand(self):
        """Get _is_drawing_strand

        Returns:
            bool: is_drawing_strand
        """
        return self._is_drawing_strand
    # end def

    def setIsDrawingStrand(self, boolval):
        """Set _is_drawing_strand

        Args:
            boolval (bool): True or False.
        """
        self._is_drawing_strand = boolval
        if boolval is False:
            self._temp_strand_item.hideIt()
    # end def

    def initStrandItemFromVHI(self, virtual_helix_item, strand_set, idx):
        """Called from VHI pencilToolMousePress. Stores the starting point
        of the strand to be created.

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): reference to the VHI
            strand_set (StrandSet): reference to the clicked strand_set
            idx (int): index where clicked
        """
        s_i = self._temp_strand_item
        self._start_idx = idx
        self._start_strand_set = strand_set
        s_i.resetStrandItem(virtual_helix_item, strand_set.isForward())
        self._low_drag_bound, self._high_drag_bound = strand_set.getBoundsOfEmptyRegionContaining(idx)
    # end def

    def updateStrandItemFromVHI(self, virtual_helix_item, strand_set, idx):
        """A temporary strand item is drawn and refreshed on mousemoves before
        the final mouse release. This method updates its appearance to the
        most recent index.

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): reference to the VHI
            strand_set (StrandSet): reference to the clicked strand_set
            idx (int): index of cursor from last mousemove
        """
        s_i = self._temp_strand_item
        s_idx = self._start_idx
        if abs(s_idx - idx) > 1 and self.isWithinBounds(idx):
            idxs = (idx, s_idx) if self.isDragLow(idx) else (s_idx, idx)
            s_i.strandResizedSlot(idxs)
            s_i.showIt()
        # end def
    # end def

    def isDragLow(self, idx):
        """Is the pencil tool being dragged to a lower idx than the start idx.
        Used to determine how the temp strand should be drawn.

        Args:
            idx (int): the dragged-to base index within the virtual helix

        Returns:
            bool: True if dragging lower (left), False if higher (right).
        """
        s_idx = self._start_idx
        if s_idx - idx > 0:
            return True
        else:
            return False
    # end def

    def isWithinBounds(self, idx):
        """Is the idx with the low and high drag boundaries.

        Args:
            idx (int): the base index within the virtual helix

        Returns:
            bool: True if inside the bounds, False otherwise.
        """
        return self._low_drag_bound <= idx <= self._high_drag_bound
    # end def

    def attemptToCreateStrand(self, virtual_helix_item, strand_set, idx):
        """Attempt to create a new strand within the VHI `strand_set` with
        bounds of the original mouse press index (stored as `self._start_idx`)
        and the mouse release index `idx`.

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): from vhi
            strand_set (StrandSet): Description
            idx (int): mouse release index
        """
        self._temp_strand_item.hideIt()
        s_idx = self._start_idx
        if abs(s_idx - idx) > 1:
            idx = util.clamp(idx, self._low_drag_bound, self._high_drag_bound)
            idxs = (idx, s_idx) if self.isDragLow(idx) else (s_idx, idx)
            self._start_strand_set.createStrand(*idxs)
    # end def

    def floatingXover(self):
        """Returns a temporary Xover item used for drawing purposes.

        Returns:
            ForcedXoverItem: Description
        """
        return self._temp_xover
    # end def

    def isFloatingXoverBegin(self):
        """Returns current status of floating crossover.

        Returns:
            bool: True if begun, False otherwise
        """
        return self._is_floating_xover_begin
    # end def

    def setFloatingXoverBegin(self, boolval):
        """Sets current status of floating crossover.

        Args:
            boolval (bool): True to begin, False otherwise.

        """
        self._is_floating_xover_begin = boolval
        if boolval:
            self._temp_xover.hideIt()
        else:
            self._temp_xover.showIt()
    # end def

    def attemptToCreateXover(self, virtual_helix_item, strand3p, idx):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): the VHI
            strand3p (Strand): reference to the 3' strand
            idx (int): the base index within the virtual helix

        """
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

        Args:
            event (TYPE): Description
        """
        a = event.key()
        # print("PencilTool keypress", a)
        if a in [Qt.Key_Control, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            QGraphicsObject.keyPressEvent(self, event)
        else:
            self.deactivate()
    # end def

# end class


class ForcedStrandItem(QGraphicsLineItem):
    """Summary

    Attributes:
        is_forward (bool): True if forward strand, False if reverse.
    """
    def __init__(self, tool, virtual_helix_item):
        """The parent should be a VirtualHelixItem.

        Args:
            tool (TYPE): Description
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
        """
        super(ForcedStrandItem, self).__init__(virtual_helix_item)
        self._virtual_helix_item = virtual_helix_item
        self._tool = tool

        is_forward = True

        # caps
        self._low_cap = EndpointItem(self, 'low', is_forward)
        self._high_cap = EndpointItem(self, 'high', is_forward)
        self._low_cap.disableEvents()
        self._high_cap.disableEvents()

        # orientation
        self.is_forward = is_forward

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
        """docstring for strandResizedSlot

        Args:
            idxs (TYPE): Description
        """
        low_moved = self._low_cap.updatePosIfNecessary(idxs[0])
        high_moved = self._high_cap.updatePosIfNecessary(idxs[1])
        if low_moved:
            self.updateLine(self._low_cap)
        if high_moved:
            self.updateLine(self._high_cap)
    # end def

    def strandRemovedSlot(self):
        """Removes click_aear, caps, and self.
        """
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
        """
        Returns:
            VirtualHelixItem: Description
        """
        return self._virtual_helix_item

    def activeTool(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._tool
    # end def

    def hideIt(self):
        """Hide caps, click area, and self.
        """
        self.hide()
        self._low_cap.hide()
        self._high_cap.hide()
        self._click_area.hide()
    # end def

    def showIt(self):
        """Show caps, click area, and self.
        """
        self._low_cap.show()
        self._high_cap.show()
        self._click_area.show()
        self.show()
    # end def

    def resetStrandItem(self, virtualHelixItem, is_forward):
        """Summary

        Args:
            virtualHelixItem (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_forward (bool): Description
        """
        self.setParentItem(virtualHelixItem)
        self._virtual_helix_item = virtualHelixItem
        self.resetEndPointItems(is_forward)
    # end def

    def resetEndPointItems(self, is_forward):
        """Summary

        Args:
            is_forward (TYPE): Description
        """
        bw = _BASE_WIDTH
        self.is_forward = is_forward
        self._low_cap.resetEndPoint(is_forward)
        self._high_cap.resetEndPoint(is_forward)
        line = self.line()
        p1 = line.p1()
        p2 = line.p2()
        if is_forward:
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
        """Summary

        Args:
            moved_cap (TYPE): Description

        """
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
        """Summary

        Returns:
            TYPE: Description
        """
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
PPL5.addRect(0.25*_BASE_WIDTH, 0.125*_BASE_WIDTH, 0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
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

    Attributes:
        is_forward (TYPE): Description
    """
    def __init__(self, virtual_helix_item, xover_item, strand3p, idx):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): from vhi
            xover_item (TYPE): Description
            strand3p (Strand): reference to the 3' strand
            idx (int): the base index within the virtual helix
        """
        super(ForcedXoverNode3, self).__init__(virtual_helix_item)
        self._vhi = virtual_helix_item
        self._xover_item = xover_item
        self._idx = idx

        self.is_forward = strand3p.strandSet().isForward()
        self._is_on_top = self.is_forward

        self._partner_virtual_helix = virtual_helix_item

        self._blank_thing = QGraphicsRectItem(_blankRect, self)
        self._blank_thing.setBrush(QBrush(Qt.white))
        self._path_thing = QGraphicsPathItem(self)
        self.configurePath()

        self._label = None
        self.setPen(_NO_PEN)
        self.setBrush(_NO_BRUSH)
        self.setRect(_rect)

        self.setZValue(styles.ZENDPOINTITEM + 1)
    # end def

    def updateForFloatFromVHI(self, virtual_helix_item, is_forward, idx_x, idx_y):
        """
        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_forward (TYPE): Description
            idx_x (TYPE): Description
            idx_y (TYPE): Description
        """
        self._vhi = virtual_helix_item
        self.setParentItem(virtual_helix_item)
        self._idx = idx_x
        self._is_on_top = self.is_forward = True if is_forward else False
        self.updatePositionAndAppearance(is_from_strand=False)
    # end def

    def updateForFloatFromStrand(self, virtual_helix_item, strand3p, idx):
        """
        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            strand3p (Strand): reference to the 3' strand
            idx (int): the base index within the virtual helix
        """
        self._vhi = virtual_helix_item
        self._strand = strand3p
        self.setParentItem(virtual_helix_item)
        self._idx = idx
        self._is_on_top = self.is_forward = strand3p.strandSet().isForward()
        self.updatePositionAndAppearance()
    # end def

    def configurePath(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._path_thing.setBrush(getBrushObj(_PENCIL_COLOR))
        path = PPR3 if self.is_forward else PPL3
        offset = -_BASE_WIDTH if self.is_forward else _BASE_WIDTH
        self._path_thing.setPath(path)
        self._path_thing.setPos(offset, 0)

        offset = -_BASE_WIDTH if self.is_forward else 0
        self._blank_thing.setPos(offset, 0)

        self._blank_thing.show()
        self._path_thing.show()
    # end def

    def refreshXover(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._xover_item.refreshXover()
    # end def

    def setPartnerVirtualHelix(self, virtual_helix_item):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description

        Returns:
            TYPE: Description
        """
        self._partner_virtual_helix = virtual_helix_item
    # end def

    def idx(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._idx
    # end def

    def virtualHelixItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._vhi
    # end def

    def point(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._vhi.upperLeftCornerOfBaseType(self._idx, self.is_forward)
    # end def

    def floatPoint(self):
        """Summary

        Returns:
            TYPE: Description
        """
        pt = self.pos()
        return pt.x(), pt.y()
    # end def

    def isForward(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.is_forward
    # end def

    def updatePositionAndAppearance(self, is_from_strand=True):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.

        Args:
            is_from_strand (bool, optional): Description
        """
        self.setPos(*self.point())
        n5 = self._xover_item._node5
        if is_from_strand:
            from_strand, from_idx = (n5._strand, n5._idx) if n5 != self else (None, None)
            if self._strand.canInstallXoverAt(self._idx, from_strand, from_idx):
                self.configurePath()
                # We can only expose a 5' end. But on which side?
                is_left = True if self.is_forward else False
                self._updateLabel(is_left)
            else:
                self.hideItems()
        else:
            self.hideItems()
    # end def

    def remove(self):
        """Clean up this joint
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
        """Called by updatePositionAndAppearance during init.
        Updates drawing and position of the label.

        Args:
            is_left (TYPE): Description
        """
        lbl = self._label
        if self._idx is not None:
            bw = _BASE_WIDTH
            num = self._partner_virtual_helix.idNum()
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
            if num == 1:
                label_x -= half_label_w/2.0
            # create text item
            if lbl is None:
                lbl = QGraphicsSimpleTextItem(str(num), self)
            lbl.setPos(label_x, label_y)
            lbl.setBrush(_ENAB_BRUSH)
            lbl.setFont(_TO_HELIX_NUM_FONT)
            self._label = lbl

            lbl.setText(str(self._partner_virtual_helix.idNum()))
            lbl.show()
        # end if
    # end def

    def hideItems(self):
        """Summary

        Returns:
            TYPE: Description
        """
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
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            xover_item (TYPE): Description
            strand5p (TYPE): Description
            idx (int): the base index within the virtual helix
        """
        super(ForcedXoverNode5, self).__init__(virtual_helix_item, xover_item, strand5p, idx)
    # end def

    def configurePath(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._path_thing.setBrush(getBrushObj(_PENCIL_COLOR))
        path = PPL5 if self.is_forward else PPR5
        offset = _BASE_WIDTH if self.is_forward else -_BASE_WIDTH
        self._path_thing.setPath(path)
        self._path_thing.setPos(offset, 0)

        offset = 0 if self.is_forward else -_BASE_WIDTH
        self._blank_thing.setPos(offset, 0)

        self._blank_thing.show()
        self._path_thing.show()
    # end def

    def updatePositionAndAppearance(self, is_from_strand=True):
        """Same as XoverItem3, but exposes 3' end

        Args:
            is_from_strand (bool, optional): Description
        """
        self.setPos(*self.point())
        self.configurePath()
        # # We can only expose a 3' end. But on which side?
        is_left = False if self.is_forward else True
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

    def __init__(self, tool, nucleicacid_part_item, virtual_helix_item):
        """
        strand_item is a the model representation of the 5prime most strand
        of a Xover

        Args:
            tool (TYPE): Description
            nucleicacid_part_item (TYPE): Description
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
        """
        super(ForcedXoverItem, self).__init__(nucleicacid_part_item)
        self._tool = tool
        self._virtual_helix_item = virtual_helix_item
        self._node5 = None
        self._node3 = None
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # for keyPressEvents
        self.setZValue(styles.ZPATHTOOL)
        self.hide()
    # end def

    ### SLOTS ###

    ### METHODS ###
    def remove(self):
        """Summary

        Returns:
            TYPE: Description
        """
        scene = self.scene()
        if self._node3 is not None:
            scene.removeItem(self._node3)
            scene.removeItem(self._node5)
        scene.removeItem(self)
    # end def

    def deactivate(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._tool.setFloatingXoverBegin(True)

    def hideIt(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.hide()
        self.clearFocus()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
    # end def

    def showIt(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.show()
        self.setFocus()
        if self._node3:
            self._node3.show()
            self._node5.show()
    # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        Use QWidget.changeEvent Slot for intercepting window changes in order to
        regain focus if necessary in DocumentWindow or CustomGraphicsView classes
        looking for event.type() QEvent.ActivationChange and using isActiveWindow()
        or focus to get focus

        Args:
            event (TYPE): Description
        """
        a = event.key()
        # print("ForcedXoverItem keypress", a)
        if a in [Qt.Key_Control, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            QGraphicsPathItem.keyPressEvent(self, event)
        else:
            # reset the tool
            self._tool.setFloatingXoverBegin(True)
    # end def

    def updateBase(self, virtual_helix_item, strand5p, idx):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            strand5p (TYPE): Description
            idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description
        """
        # floating Xover!
        self._virtual_helix_item = virtual_helix_item
        self.setParentItem(virtual_helix_item.partItem())
        if self._node5 is None:
            self._node5 = ForcedXoverNode5(virtual_helix_item, self, strand5p, idx)
            self._node3 = ForcedXoverNode3(virtual_helix_item, self, strand5p, idx)
        self._node5.updateForFloatFromStrand(virtual_helix_item, strand5p, idx)
        self._node3.updateForFloatFromStrand(virtual_helix_item, strand5p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromVHI(self, virtual_helix_item, is_forward, idx_x, idx_y):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_forward (TYPE): Description
            idx_x (TYPE): Description
            idx_y (TYPE): Description

        Returns:
            TYPE: Description
        """
        # floating Xover!
        self._node5.setPartnerVirtualHelix(virtual_helix_item)
        self._node5.updatePositionAndAppearance()
        self._node3.setPartnerVirtualHelix(self._virtual_helix_item)
        self._node3.updateForFloatFromVHI(virtual_helix_item, is_forward, idx_x, idx_y)
        self.updateFloatPath()
    # end def

    def updateFloatingFromStrandItem(self, virtual_helix_item, strand3p, idx):
        """Summary

        Args:
            virtual_helix_item (cadnano.gui.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            strand3p (Strand): reference to the 3' strand
            idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description
        """
        # floating Xover!
        self._node3.updateForFloatFromStrand(virtual_helix_item, strand3p, idx)
        self.updateFloatPath()
    # end def

    def updateFloatingFromPartItem(self, nucleicacid_part_item, pt):
        """Summary

        Args:
            nucleicacid_part_item (TYPE): Description
            pt (TYPE): Description

        Returns:
            TYPE: Description
        """
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

        Args:
            point (None, optional): Description

        """
        node3 = self._node3
        node5 = self._node5

        bw = _BASE_WIDTH

        vhi5 = self._virtual_helix_item
        nucleicacid_part_item = vhi5.partItem()
        pt5 = vhi5.mapToItem(nucleicacid_part_item, *node5.floatPoint())

        n5_is_forward = node5.is_forward

        # Enter/exit are relative to the direction that the path travels
        # overall.
        five_enter_pt = pt5 + QPointF(0 if n5_is_forward else 1, .5)*bw
        five_center_pt = pt5 + QPointF(.5, .5)*bw
        five_exit_pt = pt5 + QPointF(.5, 0 if n5_is_forward else 1)*bw

        vhi3 = node3.virtualHelixItem()

        if point:
            pt3 = point
            n3_is_forward = True
            same_strand = False
            same_parity = False
            three_enter_pt = three_center_pt = three_exit_pt = pt3
        else:
            pt3 = vhi3.mapToItem(nucleicacid_part_item, *node3.point())
            n3_is_forward = node3.is_forward
            same_strand = (n5_is_forward == n3_is_forward) and vhi3 == vhi5
            same_parity = n5_is_forward == n3_is_forward

            three_enter_pt = pt3 + QPointF(.5, 0 if n3_is_forward else 1)*bw
            three_center_pt = pt3 + QPointF(.5, .5)*bw
            three_exit_pt = pt3 + QPointF(1 if n3_is_forward else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if same_strand:
            dx = abs(three_enter_pt.x() - five_exit_pt.x())
            c1.setX(0.5 * (five_exit_pt.x() + three_enter_pt.x()))
            if n5_is_forward:
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
            if n5_is_forward:
                c1.setX(five_exit_pt.x() - _xScale *
                        abs(three_enter_pt.y() - five_exit_pt.y()))
            else:
                c1.setX(five_exit_pt.x() + _xScale *
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
    #     color = QColor(oligo.getColor())
    #     penWidth = styles.PATH_STRAND_STROKE_WIDTH
    #     if oligo.shouldHighlight():
    #         penWidth = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
    #         color.setAlpha(128)
    #     pen = QPen(color, penWidth)
    #     pen.setCapStyle(Qt.FlatCap)
    #     self.setPen(pen)
    # # end def

    def _updateFloatPen(self):
        """Summary

        Returns:
            TYPE: Description
        """
        pen_width = styles.PATH_STRAND_STROKE_WIDTH
        pen = getPenObj(_PENCIL_COLOR, pen_width)
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
PPL5.addRect(0.25*_BASE_WIDTH, 0.125*_BASE_WIDTH, 0.75*_BASE_WIDTH, 0.75*_BASE_WIDTH)
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
    """Summary

    Attributes:
        cap_type (TYPE): Description
        mouseMoveEvent (TYPE): Description
        mousePressEvent (TYPE): Description
    """
    def __init__(self, strand_item, cap_type, is_forward):
        """The parent should be a StrandItem.

        Args:
            strand_item (TYPE): Description
            cap_type (TYPE): Description
            is_forward (TYPE): Description
        """
        super(EndpointItem, self).__init__(strand_item.virtualHelixItem())

        self._strand_item = strand_item
        self._getActiveTool = strand_item.activeTool()
        self.cap_type = cap_type
        self._low_drag_bound = None
        self._high_drag_bound = None
        self._initCapSpecificState(is_forward)
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
        """Summary

        Returns:
            TYPE: Description
        """
        return "%s" % self.__class__.__name__

    ### SIGNALS ###

    ### SLOTS ###

    ### ACCESSORS ###
    def idx(self):
        """Look up baseIdx, as determined by strand_item idxs and cap type.
        """
        if self.cap_type == 'low':
            return self._strand_item.idxs()[0]
        else:  # high or dual, doesn't matter
            return self._strand_item.idxs()[1]
    # end def

    def partItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._strand_item.partItem()
    # end def

    def disableEvents(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._click_area.setAcceptHoverEvents(False)
        self.mouseMoveEvent = QGraphicsPathItem.mouseMoveEvent
        self.mousePressEvent = QGraphicsPathItem.mousePressEvent
    # end def

    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._strand_item.window()

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def updatePosIfNecessary(self, idx):
        """Update position if necessary and return True if updated.

        Args:
            idx (int): the base index within the virtual helix
        """
        x = int(idx*_BASE_WIDTH)
        if x != self.x():
            self.setPos(x, self.y())
            return True
        return False

    def resetEndPoint(self, is_forward):
        """Summary

        Args:
            is_forward (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.setParentItem(self._strand_item.virtualHelixItem())
        self._initCapSpecificState(is_forward)
        upper_left_y = 0 if is_forward else _BASE_WIDTH
        self.setY(upper_left_y)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _initCapSpecificState(self, is_forward):
        """Summary

        Args:
            is_forward (TYPE): Description

        Returns:
            TYPE: Description
        """
        c_t = self.cap_type
        if c_t == 'low':
            path = PPL5 if is_forward else PPL3
        elif c_t == 'high':
            path = PPR3 if is_forward else PPR5
        elif c_t == 'dual':
            path = PP53 if is_forward else PP35
        self.setPath(path)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.

        Args:
            event (TYPE): Description
        """
        self.scene().views()[0].addToPressList(self)
        self._strand_item.setActiveEndpoint(self.cap_type)
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
        Parses a hoverMoveEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.

        Args:
            event (TYPE): Description
        """
        active_tool_str = self._getActiveTool().methodPrefix()
        if active_tool_str == 'pencilTool':
            return self._strand_item.pencilToolHoverMove(event, self.idx())

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent, calling the approproate tool method as
        necessary. Updates _move_idx if it changed.

        Args:
            event (TYPE): Description
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

        Args:
            event (TYPE): Description
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):  # if the tool method exists
            modifiers = event.modifiers()
            x = event.pos().x()
            getattr(self, tool_method_name)(modifiers, x)  # call tool method
        if hasattr(self, '_move_idx'):
            del self._move_idx
# end class
