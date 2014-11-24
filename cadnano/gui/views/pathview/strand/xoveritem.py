import time
from cadnano.gui.views.pathview import pathstyles as styles

import cadnano.util as util

from PyQt5.QtCore import QPointF, QRectF, Qt, QEvent

from PyQt5.QtGui import QBrush, QFont, QFontMetrics, QPen, QColor, QPainterPath, QPolygonF
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsSimpleTextItem

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_toHelixNumFont = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_FM = QFontMetrics(_toHelixNumFont)
_ENAB_BRUSH = QBrush(Qt.SolidPattern)  # Also for the helix number label
_NO_BRUSH = QBrush(Qt.NoBrush)
# _RECT = QRectF(0, 0, baseWidth, baseWidth)
_X_SCALE = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_Y_SCALE = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant
_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)

class XoverNode3(QGraphicsRectItem):
    """
    This is a QGraphicsRectItem to allow actions and also a 
    QGraphicsSimpleTextItem to allow a label to be drawn
    """
    def __init__(self, virtual_helix_item, xover_item, strand3p, idx):
        super(XoverNode3, self).__init__(virtual_helix_item)
        self._vhi = virtual_helix_item
        self._xover_item = xover_item
        self._idx = idx
        self._is_on_top = virtual_helix_item.isStrandOnTop(strand3p)
        self._is_drawn_5to3 = strand3p.strandSet().isDrawn5to3()
        self._strand_type = strand3p.strandSet().strandType()

        self.setPartnerVirtualHelix(strand3p)

        self.setPen(QPen(Qt.NoPen))
        self._label = None
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(_NO_BRUSH)
        self.setRect(_RECT)
        self.setZValue(styles.ZXOVERITEM)
    # end def


    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        self.scene().views()[0].addToPressList(self)
        self._vhi.setActive(self._idx)
        xoi = self._xover_item
        tool_method_name = self._getActiveTool().methodPrefix() + "MousePress"
        if hasattr(xoi, tool_method_name):
            getattr(xoi, tool_method_name)()
    # end def

    def customMouseRelease(self, event):
        pass
    # end def
    
    def virtualHelix(self):
        return self._vhi.virtualHelix()
    # end def

    def strandType(self):
        return self._strand_type
    # end def

    def refreshXover(self):
        self._xover_item.refreshXover()
    # end def

    def setPartnerVirtualHelix(self,strand):
        if strand.connection5p():
            self._partner_virtual_helix = strand.connection5p().virtualHelix()
        else:
            self._partner_virtual_helix = None
    # end def

    def idx(self):
        return self._idx
    # end def
    
    def setIdx(self, idx):
         self._idx = idx
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
        return self._is_drawn_5to3
    # end def

    def updatePositionAndAppearance(self):
        """
        Sets position by asking the VirtualHelixItem
        Sets appearance by choosing among pre-defined painterpaths (from
        normalstrandgraphicsitem) depending on drawing direction.
        """
        self.setPos(*self.point())
        # We can only expose a 5' end. But on which side?
        isLeft = True if self._is_drawn_5to3 else False
        self._updateLabel(isLeft)
    # end def

    def updateConnectivity(self):
        isLeft = True if self._is_drawn_5to3 else False
        self._updateLabel(isLeft)
    # end def

    def remove(self):
        """
        Clean up this joint
        """
        scene = self.scene()
        if scene:
            scene.removeItem(self._label)
            self._label = None
            scene.removeItem(self)
    # end def

    def _updateLabel(self, isLeft):
        """
        Called by updatePositionAndAppearance during init, or later by
        updateConnectivity. Updates drawing and position of the label.
        """
        lbl = self._label
        if self._idx != None:
            if lbl == None:
                bw = _BASE_WIDTH
                num = self._partner_virtual_helix.number()
                tbr = _FM.tightBoundingRect(str(num))
                half_label_h = tbr.height()/2.0
                half_label_w = tbr.width()/2.0
                # determine x and y positions
                labelX = bw/2.0 - half_label_w
                if self._is_on_top:
                    labelY = -0.25*half_label_h - 0.5 - 0.5*bw
                else:
                    labelY = 2*half_label_h + 0.5 + 0.5*bw
                # adjust x for left vs right
                labelXoffset = 0.25*bw if isLeft else -0.25*bw
                labelX += labelXoffset
                # adjust x for numeral 1
                if num == 1: labelX -= half_label_w/2.0
                # create text item
                lbl = QGraphicsSimpleTextItem(str(num), self)
                lbl.setPos(labelX, labelY)
                lbl.setBrush(_ENAB_BRUSH)
                lbl.setFont(_toHelixNumFont)
                self._label = lbl
            # end if
            lbl.setText( str(self._partner_virtual_helix.number()) )
        # end if
    # end def

# end class


class XoverNode5(XoverNode3):
    """
    XoverNode5 is the partner of XoverNode3. It dif
    XoverNode3 handles:
    1. Drawing of the 5' end of an xover, and its text label. Drawing style
    is determined by the location of the xover with in a vhelix (is it a top
    or bottom vstrand?).
    2. Notifying XoverStrands in the model when connectivity changes.

    """
    def __init__(self, virtual_helix_item, xover_item, strand5p, idx):
        super(XoverNode5, self).__init__(virtual_helix_item, xover_item, strand5p, idx)
    # end def

    def setPartnerVirtualHelix(self, strand):
        if strand.connection3p():
            self._partner_virtual_helix = strand.connection3p().virtualHelix()
        else:
            self._partner_virtual_helix = None
    # end def

    def updatePositionAndAppearance(self):
        """Same as XoverItem3, but exposes 3' end"""
        self.setPos(*self.point())
        # # We can only expose a 3' end. But on which side?
        isLeft = False if self._is_drawn_5to3 else True
        self._updateLabel(isLeft)
    # end def
# end class

class XoverItem(QGraphicsPathItem):
    """
    This class handles:
    1. Drawing the spline between the XoverNode3 and XoverNode5 graphics
    items in the path view.

    XoverItem should be a child of a PartItem.
    """
    _filterName = "xover"

    def __init__(self, strand_item, virtual_helix_item):
        """
        strand_item is a the model representation of the 5prime most strand
        of a Xover
        """
        super(XoverItem, self).__init__(virtual_helix_item.partItem())
        self._strand_item = strand_item
        self._virtual_helix_item = virtual_helix_item
        self._strand5p = None
        self._node5 = None
        self._node3 = None
        self.hide()
        
        # for easier mouseclick
        self._click_area = c_a = QGraphicsRectItem(self)
        # self._click_area.setAcceptHoverEvents(True)
        # c_a.hoverMoveEvent = self.hoverMoveEvent
        c_a.mousePressEvent = self.mousePressEvent
        c_a.mouseMoveEvent = self.mouseMoveEvent
        c_a.setPen(QPen(Qt.NoPen))

        self._getActiveTool = strand_item._getActiveTool

        # self.setFlag(QGraphicsItem.ItemIsSelectable)
    # end def

    ### SLOTS ###

    ### ACCESSORS ###

    def partItem(self):
        return self._virtual_helix_item.partItem()
    # end def

    def remove(self):
        scene = self.scene()
        if self._node3:
            self._node3.remove()
            self._node5.remove()
            self._node3 = None
            self._node5 = None
        self._strand5p = None
        scene.removeItem(self._click_area)
        self._click_area = None
        scene.removeItem(self)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def hideIt(self):
        self.hide()
        if self._node3:
            self._node3.hide()
            self._node5.hide()
            self._node3.remove()
            self._node3 = None
    # end def

    def showIt(self):
        self.show()
        if self._node3:
            self._node3.show()
            self._node5.show()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    # end def

    def refreshXover(self):
        strand5p = self._strand5p
        node3 = self._node3
        if strand5p:
            strand3p = strand5p.connection3p()
            if strand3p != None and node3:
                if node3.virtualHelix():
                    self.update(self._strand5p)
                else:
                    node3.remove()
                    self._node3 = None
            elif node3:
                node3.remove()
                self._node3 = None
        elif node3:
            node3.remove()
            self._node3 = None
    # end def

    def update(self, strand5p, idx=None):
        """
        Pass idx to this method in order to install a floating
        Xover for the forced xover tool
        """
        self._strand5p = strand5p
        strand3p = strand5p.connection3p()
        vhi5p = self._virtual_helix_item
        partItem = vhi5p.partItem()

        # This condition is for floating xovers
        idx_3_prime = idx if idx else strand5p.idx3Prime()

        if self._node5 == None:
            self._node5 = XoverNode5(vhi5p, self, strand5p, idx_3_prime)
        if strand3p != None:
            if self._node3 == None:
                vhi3p = partItem.itemForVirtualHelix(strand3p.virtualHelix())
                self._node3 = XoverNode3(vhi3p, self, strand3p, strand3p.idx5Prime())
            else:
                self._node5.setIdx(idx_3_prime)
                self._node3.setIdx(strand3p.idx5Prime())
            self._node5.setPartnerVirtualHelix(strand5p)
            self._updatePath(strand5p)
        else:
            if self._node3:
                self._node3.remove()
                self._node3 = None
        # end if
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _updatePath(self, strand5p):
        """
        Draws a quad curve from the edge of the fromBase
        to the top or bottom of the toBase (q5), and
        finally to the center of the toBase (toBaseEndpoint).

        If floatPos!=None, this is a floatingXover and floatPos is the
        destination point (where the mouse is) while toHelix, toIndex
        are potentially None and represent the base at floatPos.

        """
        group = self.group()
        self.tempReparent()
        
        node3 = self._node3
        node5 = self._node5

        bw = _BASE_WIDTH

        parent = self.partItem()
        
        vhi5 = self._virtual_helix_item
        pt5 = vhi5.mapToItem(parent, *node5.point())
        
        five_is_top = node5.isOnTop()
        five_is_5to3 = node5.isDrawn5to3()

        vhi3 = node3.virtualHelixItem()
        pt3 = vhi3.mapToItem(parent, *node3.point())

        three_is_top = node3.isOnTop()
        three_is_5to3 = node3.isDrawn5to3()
        same_strand = (node5.strandType() == node3.strandType()) and vhi3 == vhi5
        same_parity = five_is_5to3 == three_is_5to3

        # Enter/exit are relative to the direction that the path travels
        # overall.
        five_enter_pt = pt5 + QPointF(0 if five_is_5to3 else 1, .5)*bw
        five_center_pt = pt5 + QPointF(.5, .5)*bw
        five_exit_pt = pt5 + QPointF(.5, 0 if five_is_top else 1)*bw

        three_enter_pt = pt3 + QPointF(.5, 0 if three_is_top else 1)*bw
        three_center_pt = pt3 + QPointF(.5, .5)*bw
        three_exit_pt = pt3 + QPointF(1 if three_is_5to3 else 0, .5)*bw

        c1 = QPointF()
        # case 1: same strand
        if same_strand:
            dx = abs(three_enter_pt.x() - five_exit_pt.x())
            c1.setX(0.5 * (five_exit_pt.x() + three_enter_pt.x()))
            if five_is_top:
                c1.setY(five_exit_pt.y() - _Y_SCALE * dx)
            else:
                c1.setY(five_exit_pt.y() + _Y_SCALE * dx)
        # case 2: same parity
        elif same_parity:
            dy = abs(three_enter_pt.y() - five_exit_pt.y())
            c1.setX(five_exit_pt.x() + _X_SCALE * dy)
            c1.setY(0.5 * (five_exit_pt.y() + three_enter_pt.y()))
        # case 3: different parity
        else:
            if five_is_top and five_is_5to3:
                c1.setX(five_exit_pt.x() - _X_SCALE *\
                        abs(three_enter_pt.y() - five_exit_pt.y()))
            else:
                c1.setX(five_exit_pt.x() + _X_SCALE *\
                        abs(three_enter_pt.y() - five_exit_pt.y()))
            c1.setY(0.5 * (five_exit_pt.y() + three_enter_pt.y()))

        # Construct painter path
        painterpath = QPainterPath()
        painterpath.moveTo(five_enter_pt)
        painterpath.lineTo(five_center_pt)
        painterpath.lineTo(five_exit_pt)

        # The xover5's non-crossing-over end (3') has a connection
        painterpath.quadTo(c1, three_enter_pt)
        painterpath.lineTo(three_center_pt)
        painterpath.lineTo(three_exit_pt)

        tempR = painterpath.boundingRect()
        tempR.adjust(-bw/2, 0, bw, 0)
        self._click_area.setRect(tempR)
        self.setPath(painterpath)
        node3.updatePositionAndAppearance()
        node5.updatePositionAndAppearance()
        
        if group:
            group.addToGroup(self)
            
        self._updateColor(strand5p)
    # end def
    
    def updateLabels(self):
        if self._node3:
            self._node3._updateLabel()
        if self._node5:
            self._node5._updateLabel()
    
    def _updateColor(self, strand):
        oligo = strand.oligo()
        color = self.pen().color() if self.isSelected() else QColor(oligo.color())
        # print "update xover color", color.value(), self.isSelected(), self.group(), self.parentItem()
        pen_width = styles.PATH_STRAND_STROKE_WIDTH
        if oligo.shouldHighlight():
            pen_width = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
            color.setAlpha(128)
        pen = QPen(color, pen_width)
        # pen.setCosmetic(True)
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
    # end def

    ### EVENT HANDERS ###
    def mousePressEvent(self, event):
        """
        Special case for xovers and select tool, for now
        """
        if self._getActiveTool().methodPrefix() == "selectTool":
            event.setAccepted(False)
            sI = self._strand_item
            viewroot = sI.viewroot()
            current_filter_dict = viewroot.selectionFilterDict()
            if sI.strandFilter() in current_filter_dict and self._filterName in current_filter_dict:
                event.setAccepted(True)
                selection_group = viewroot.strandItemSelectionGroup()
                mod = Qt.MetaModifier
                if not (event.modifiers() & mod):
                     selection_group.clearSelection(False)
                selection_group.setSelectionLock(selection_group)
                # self.setSelectedColor(True)
                selection_group.pendToAdd(self)
                selection_group.processPendingToAddList()
                return selection_group.mousePressEvent(event)
        else:
            event.setAccepted(False)
    # end def 
    
    def eraseToolMousePress(self):
        """Erase the strand."""
        self._strand_item.eraseToolMousePress(None, None)
    # end def

    def paintToolMousePress(self):
        """Paint the strand."""
        self._strand_item.paintToolMousePress(None, None)
    # end def

    def selectToolMousePress(self):
        """Remove the xover."""
        # make sure the selection is clear
        sI = self._strand_item
        viewroot = sI.viewroot()
        selection_group = viewroot.strandItemSelectionGroup()
        selection_group.clearSelection(False)
        
        strand5p = self._strand5p
        strand3p = strand5p.connection3p()
        self._virtual_helix_item.part().removeXover(strand5p, strand3p)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """
        # map the position
        self.tempReparent(pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        partItem = self.partItem()
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(partItem)
        tempP = partItem.mapFromScene(pos)
        self.setPos(tempP)
    # end def

    def setSelectedColor(self, value):
        if value == True:
            color = styles.SELECTED_COLOR
        else:
            oligo = self._strand_item.strand().oligo()
            color = QColor(oligo.color())
            if oligo.shouldHighlight():
                color.setAlpha(128)
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            active_tool = self._getActiveTool()
            if active_tool.methodPrefix() == "selectTool":
                sI = self._strand_item
                viewroot = sI.viewroot()
                current_filter_dict = viewroot.selectionFilterDict()
                selection_group = viewroot.strandItemSelectionGroup()
                # only add if the selection_group is not locked out
                if value == True and (self._filterName in current_filter_dict or not selection_group.isNormalSelect()):
                    if sI.strandFilter() in current_filter_dict:
                        # print "might add a xoi"
                        if self.group() != selection_group and selection_group.isNormalSelect():
                            # print "adding an xoi"
                            selection_group.pendToAdd(self)
                            selection_group.setSelectionLock(selection_group)
                        self.setSelectedColor(True)
                        return True
                    else:
                        # print "Doh"
                        return False
                # end if
                elif value == True:
                    # print "DOink"
                    return False
                else:
                    # Deselect
                    # Check if the strand is being added to the selection group still
                    if not selection_group.isPending(self._strand_item):
                        selection_group.pendToRemove(self)
                        self.tempReparent()
                        self.setSelectedColor(False)
                        return False
                    else:   # don't deselect it, because the strand is selected still
                        return True
                # end else
            # end if
            elif str(active_tool) == "paint_tool":
                sI = self._strand_item
                viewroot = sI.viewroot()
                current_filter_dict = viewroot.selectionFilterDict()
                if sI.strandFilter() in current_filter_dict:
                    if not active_tool.isMacrod():
                        active_tool.setMacrod()
                    self.paintToolMousePress()
            return False
        # end if
        return QGraphicsPathItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        strand5p = self._strand5p
        strand3p = strand5p.connection3p()
        test5p = document.isModelStrandSelected(strand5p)
        lowVal5p, highVal5p = document.getSelectedStrandValue(strand5p) if test5p else (False, False)
        if strand5p.isDrawn5to3():
            highVal5p = False
        else:
            lowVal5p = False
        test3p = document.isModelStrandSelected(strand3p)
        lowVal3p, highVal3p = document.getSelectedStrandValue(strand3p) if test3p else (False, False)
        if strand3p.isDrawn5to3():
            lowVal3p = False
        else:
            highVal3p = False

        if not lowVal5p and not highVal5p and test5p:
            document.removeStrandFromSelection(strand5p)
        elif test5p:
            document.addStrandToSelection(strand5p, (lowVal5p, highVal5p))
        if not lowVal3p and not highVal3p and test3p:
            document.removeStrandFromSelection(strand3p)
        elif test3p:
            document.addStrandToSelection(strand3p, (lowVal3p, highVal3p))
        self.restoreParent()
    # end def

    def modelSelect(self, document):
        strand5p = self._strand5p
        strand3p = strand5p.connection3p()

        test5p = document.isModelStrandSelected(strand5p)
        lowVal5p, highVal5p = document.getSelectedStrandValue(strand5p) if test5p else (False, False)
        if strand5p.isDrawn5to3():
            highVal5p = True
        else:
            lowVal5p = True
        test3p = document.isModelStrandSelected(strand3p)
        lowVal3p, highVal3p = document.getSelectedStrandValue(strand3p) if test3p else (False, False)
        if strand3p.isDrawn5to3():
            lowVal3p = True
        else:
            highVal3p = True
        self.setSelectedColor(True)
        self.setSelected(True)
        document.addStrandToSelection(strand5p, (lowVal5p, highVal5p))
        document.addStrandToSelection(strand3p, (lowVal3p, highVal3p))
    # end def

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(self.path())
    # end def
# end class XoverItem