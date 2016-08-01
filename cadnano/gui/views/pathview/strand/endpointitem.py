#!/usr/bin/env python
# encoding: utf-8

from math import floor

# import logging
# logger = logging.getLogger(__name__)

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem

from cadnano.gui.palette import getColorObj
from cadnano.gui.views.pathview import pathstyles as styles

_BASE_WIDTH = styles.PATH_BASE_WIDTH

PP_L5 = QPainterPath()  # Left 5' PainterPath
PP_R5 = QPainterPath()  # Right 5' PainterPath
PP_L3 = QPainterPath()  # Left 3' PainterPath
PP_R3 = QPainterPath()  # Right 3' PainterPath
PP_53 = QPainterPath()  # Left 5', Right 3' PainterPath
PP_35 = QPainterPath()  # Left 5', Right 3' PainterPath
# set up PP_L5 (left 5' blue square)
PP_L5.addRect(0.25 * _BASE_WIDTH,
              0.125 * _BASE_WIDTH,
              0.75 * _BASE_WIDTH,
              0.75 * _BASE_WIDTH)
# set up PP_R5 (right 5' blue square)
PP_R5.addRect(0, 0.125 * _BASE_WIDTH, 0.75 * _BASE_WIDTH, 0.75 * _BASE_WIDTH)
# set up PP_L3 (left 3' blue triangle)
L3_POLY = QPolygonF()
L3_POLY.append(QPointF(_BASE_WIDTH, 0))
L3_POLY.append(QPointF(0.25 * _BASE_WIDTH, 0.5 * _BASE_WIDTH))
L3_POLY.append(QPointF(_BASE_WIDTH, _BASE_WIDTH))
L3_POLY.append(QPointF(_BASE_WIDTH, 0))
PP_L3.addPolygon(L3_POLY)
# set up PP_R3 (right 3' blue triangle)
R3_POLY = QPolygonF()
R3_POLY.append(QPointF(0, 0))
R3_POLY.append(QPointF(0.75 * _BASE_WIDTH, 0.5 * _BASE_WIDTH))
R3_POLY.append(QPointF(0, _BASE_WIDTH))
R3_POLY.append(QPointF(0, 0))
PP_R3.addPolygon(R3_POLY)

# single base left 5'->3'
PP_53.addRect(0, 0.125 * _BASE_WIDTH, 0.5 * _BASE_WIDTH, 0.75 * _BASE_WIDTH)
POLY_53 = QPolygonF()
POLY_53.append(QPointF(0.5 * _BASE_WIDTH, 0))
POLY_53.append(QPointF(_BASE_WIDTH, 0.5 * _BASE_WIDTH))
POLY_53.append(QPointF(0.5 * _BASE_WIDTH, _BASE_WIDTH))
PP_53.addPolygon(POLY_53)
# single base left 3'<-5'
PP_35.addRect(0.50 * _BASE_WIDTH,
              0.125 * _BASE_WIDTH,
              0.5 * _BASE_WIDTH,
              0.75 * _BASE_WIDTH)
POLY_35 = QPolygonF()
POLY_35.append(QPointF(0.5 * _BASE_WIDTH, 0))
POLY_35.append(QPointF(0, 0.5 * _BASE_WIDTH))
POLY_35.append(QPointF(0.5 * _BASE_WIDTH, _BASE_WIDTH))
PP_35.addPolygon(POLY_35)

_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_NO_PEN = QPen(Qt.NoPen)

MOD_RECT = QRectF(.25*_BASE_WIDTH, -.25*_BASE_WIDTH, 0.5*_BASE_WIDTH, 0.5*_BASE_WIDTH)


class EndpointItem(QGraphicsPathItem):

    FILTER_NAME = "endpoint"
    __slots__ = ('_strand_item', '_getActiveTool', 'cap_type',
                 '_low_drag_bound', '_high_drag_bound', '_mod_item',
                 '_click_area')

    def __init__(self, strand_item, cap_type, is_drawn5to3):
        """The parent should be a StrandItem."""
        super(EndpointItem, self).__init__(strand_item.virtualHelixItem())

        self._strand_item = strand_item
        self._getActiveTool = strand_item._getActiveTool
        self.cap_type = cap_type
        self._low_drag_bound = None
        self._high_drag_bound = None
        self._mod_item = None
        self._initCapSpecificState(is_drawn5to3)
        self.setPen(QPen())
        # for easier mouseclick
        self._click_area = cA = QGraphicsRectItem(_DEFAULT_RECT, self)
        self._click_area.setAcceptHoverEvents(True)
        cA.hoverMoveEvent = self.hoverMoveEvent
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseMoveEvent = self.mouseMoveEvent
        cA.setPen(_NO_PEN)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    # end def

    ### SIGNALS ###

    ### SLOTS ###

    ### ACCESSORS ###
    def idx(self):
        """Look up base_idx, as determined by strandItem idxs and cap type."""
        if self.cap_type == 'low':
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
        group = self.group()
        self.tempReparent()
        x = int(idx * _BASE_WIDTH)
        if x != self.x():
            self.setPos(x, self.y())
            # if group:
            #     group.addToGroup(self)
            return True, group
        else:
            # if group:
            #     group.addToGroup(self)
            return False, group

    def safeSetPos(self, x, y):
        """
        Required to ensure proper reparenting if selected
        """
        group = self.group()
        self.tempReparent()
        self.setPos(x, y)
        if group:
            group.addToGroup(self)
    # end def

    def resetEndPoint(self, is_drawn5to3):
        self.setParentItem(self._strand_item.virtualHelixItem())
        self._initCapSpecificState(is_drawn5to3)
        upperLeftY = 0 if is_drawn5to3 else _BASE_WIDTH
        self.setY(upperLeftY)
    # end def

    def showMod(self, mod_id, color):
        self._mod_item = QGraphicsEllipseItem(MOD_RECT, self)
        self.changeMod(mod_id, color)
        self._mod_item.show()
        # print("Showing {}".format(mod_id))
    # end def

    def changeMod(self, mod_id, color):
        self._mod_id = mod_id
        self._mod_item.setBrush(QBrush(getColorObj(color)))
    # end def

    def destroyMod(self):
        self.scene().removeItem(self._mod_item)
        self._mod_item = None
        self._mod_id = None
    # end def

    def destroy(self):
        scene = self.scene()
        if self._mod_item is not None:
            self.destroyMod()
        scene.removeItem(self._click_area)
        self._click_area = None
        scene.removeItem(self)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _initCapSpecificState(self, is_drawn5to3):
        c_t = self.cap_type
        if c_t == 'low':
            path = PP_L5 if is_drawn5to3 else PP_L3
        elif c_t == 'high':
            path = PP_R3 if is_drawn5to3 else PP_R5
        elif c_t == 'dual':
            path = PP_53 if is_drawn5to3 else PP_35
        self.setPath(path)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.
        """
        self.scene().views()[0].addToPressList(self)
        idx = self._strand_item.setActiveEndpoint(self.cap_type)
        self._move_idx = idx
        active_tool_str = self._getActiveTool().methodPrefix()
        tool_method_name = active_tool_str + "MousePress"
        if hasattr(self, tool_method_name):  # if the tool method exists
            modifiers = event.modifiers()
            getattr(self, tool_method_name)(modifiers, event, self.idx())

    def hoverLeaveEvent(self, event):
        self._strand_item.hoverLeaveEvent(event)
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.
        """
        vhi_num = self._strand_item.idNum()
        oligo_length = self._strand_item._model_strand.oligo().length()
        msg = "%d[%d]\tlength: %d" % (vhi_num, self.idx(), oligo_length)
        self.partItem().updateStatusBar(msg)

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
            idx = int(floor((self.x() + event.pos().x()) / _BASE_WIDTH))
            if idx != self._move_idx:  # did we actually move?
                modifiers = event.modifiers()
                self._move_idx = idx
                getattr(self, tool_method_name)(modifiers, idx)

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

    ### TOOL METHODS ###
    def addSeqToolMousePress(self, modifiers, event, idx):
        """
        Checks that a scaffold was clicked, and then calls apply sequence
        to the clicked strand via its oligo.
        """
        m_strand = self._strand_item._model_strand
        s_i = self._strand_item
        viewroot = s_i.viewroot()
        current_filter_set = viewroot.selectionFilterSet()
        if (s_i.strandFilter() in current_filter_set and self.FILTER_NAME in current_filter_set):
            olgLen, seqLen = self._getActiveTool().applySequence(m_strand.oligo())
            if olgLen:
                msg = "Populated %d of %d scaffold bases." % (min(seqLen, olgLen), olgLen)
                if olgLen > seqLen:
                    d = olgLen - seqLen
                    msg = msg + " Warning: %d bases have no sequence." % d
                elif olgLen < seqLen:
                    d = seqLen - olgLen
                    msg = msg + " Warning: %d sequence bases unused." % d
                self.partItem().updateStatusBar(msg)
        else:
            pass
            # logger.info("The clicked strand %s does not match current selection filter %s. "\
            #             "strandFilter()=%s, FILTER_NAME=%s", m_strand, current_filter_set,
            #             s_i.strandFilter(), self.FILTER_NAME)
    # end def

    def modsToolMousePress(self, modifiers, event, idx):
        """
        Checks that a scaffold was clicked, and then calls apply sequence
        to the clicked strand via its oligo.
        """
        m_strand = self._strand_item._model_strand
        self._getActiveTool().applyMod(m_strand, idx)
    # end def

    def nickToolMouseRelease(self, modifiers, x):
        """Shift-click to merge without switching back to select tool."""
        m_strand = self._strand_item._model_strand
        if modifiers & Qt.ShiftModifier:
            m_strand.merge(self.idx())
    # end def

    def eraseToolMousePress(self, modifiers, event, idx):
        """Erase the strand."""
        m_strand = self._strand_item._model_strand
        m_strand.strandSet().removeStrand(m_strand)
    # end def

    def insertionToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._strand_item._model_strand
        m_strand.addInsertion(idx, 1)
    # end def

    def paintToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._strand_item._model_strand
        if modifiers & Qt.ShiftModifier:
            color = self.window().path_color_panel.shiftColorName()
        else:
            color = self.window().path_color_panel.colorName()
        m_strand.oligo().applyColor(color)
    # end def

    def pencilToolHoverMove(self, idx):
        """Pencil the strand is possible."""
        m_strand = self._strand_item._model_strand
        vhi = self._strand_item._virtual_helix_item
        active_tool = self._getActiveTool()

        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromStrandItem(vhi, m_strand, idx)
    # end def

    def pencilToolMousePress(self, modifiers, event, idx):
        """Break the strand is possible."""
        m_strand = self._strand_item._model_strand
        vhi = self._strand_item._virtual_helix_item
        active_tool = self._getActiveTool()

        if active_tool.isFloatingXoverBegin():
            if m_strand.idx5Prime() == idx:
                return
            else:
                temp_xover = active_tool.floatingXover()
                temp_xover.updateBase(vhi, m_strand, idx)
                active_tool.setFloatingXoverBegin(False)
        else:
            active_tool.setFloatingXoverBegin(True)
            # install Xover
            active_tool.attemptToCreateXover(vhi, m_strand, idx)
    # end def

    def selectToolMousePress(self, modifiers, event, idx):
        """
        Set the allowed drag bounds for use by selectToolMouseMove.
        """
        # print("%s.%s [%d]" % (self, util.methodName(), self.idx()))
        self._low_drag_bound, self._high_drag_bound = self._strand_item._model_strand.getResizeBounds(self.idx())
        s_i = self._strand_item
        viewroot = s_i.viewroot()
        current_filter_set = viewroot.selectionFilterSet()
        if (s_i.strandFilter() in current_filter_set and self.FILTER_NAME in current_filter_set):
            selection_group = viewroot.strandItemSelectionGroup()
            mod = Qt.MetaModifier
            if not (modifiers & mod):
                selection_group.clearSelection(False)
            selection_group.setSelectionLock(selection_group)
            selection_group.pendToAdd(self)
            selection_group.processPendingToAddList()
            return selection_group.mousePressEvent(event)
    # end def

    def selectToolMouseMove(self, modifiers, idx):
        """
        Given a new index (pre-validated as different from the prev index),
        calculate the new x coordinate for self, move there, and notify the
        parent strandItem to redraw its horizontal line.
        """
        pass
    # end def

    def selectToolMouseRelease(self, modifiers, x):
        """
        If the positional-calculated idx differs from the model idx, it means
        we have moved and should notify the model to resize.

        If the mouse event had a key modifier, perform special actions:
            shift = attempt to merge with a neighbor
            alt = extend to max drag bound
        """
        m_strand = self._strand_item._model_strand

        if modifiers & Qt.ShiftModifier:
            self.setSelected(False)
            self.restoreParent()
            m_strand.merge(self.idx())
    # end def

    def skipToolMousePress(self, modifiers, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._strand_item._model_strand
        m_strand.addInsertion(idx, -1)
    # end def

    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """
        # map the position
        self.tempReparent(pos=pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos=None):
        vh_item = self._strand_item.virtualHelixItem()
        if pos is None:
            pos = self.scenePos()
        self.setParentItem(vh_item)
        temp_point = vh_item.mapFromScene(pos)
        self.setPos(temp_point)
    # end def

    def setSelectedColor(self, value):
        if value == True:
            color = getColorObj(styles.SELECTED_COLOR)
        else:
            oligo = self._strand_item.strand().oligo()
            if oligo.shouldHighlight():
                color = getColorObj(oligo.getColor(), alpha=128)
            else:
                color = getColorObj(oligo.getColor())
        brush = self.brush()
        brush.setColor(color)
        self.setBrush(brush)
    # end def

    def updateHighlight(self, brush):
        if not self.isSelected():
            self.setBrush(brush)
    # end def

    def itemChange(self, change, value):
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            active_tool = self._getActiveTool()
            if str(active_tool) == "select_tool":
                s_i = self._strand_item
                viewroot = s_i.viewroot()
                current_filter_set = viewroot.selectionFilterSet()
                selection_group = viewroot.strandItemSelectionGroup()

                # only add if the selection_group is not locked out
                if value == True and self.FILTER_NAME in current_filter_set:
                    # if (self.group() != selection_group and
                    #     s_i.strandFilter() in current_filter_set):
                    if s_i.strandFilter() in current_filter_set:
                        if self.group() != selection_group or not self.isSelected():
                            # print("select ep")
                            selection_group.pendToAdd(self)
                            selection_group.setSelectionLock(selection_group)
                            self.setSelectedColor(True)
                        # print("select2 ep")
                        return True
                    else:
                        return False
                # end if
                elif value == True:
                    # don't select
                    return False
                else:
                    # Deselect
                    # print("deselect ep")
                    # Check if strand is being added to the selection group still
                    if not selection_group.isPending(self._strand_item):
                        selection_group.pendToRemove(self)
                        self.tempReparent()
                        self.setSelectedColor(False)
                        return False
                    else:   # don't deselect, because the strand is still selected
                        return True
                # end else
            # end if
            elif str(active_tool) == "paint_tool":
                s_i = self._strand_item
                viewroot = s_i.viewroot()
                current_filter_set = viewroot.selectionFilterSet()
                if s_i.strandFilter() in current_filter_set:
                    if not active_tool.isMacrod():
                        active_tool.setMacrod()
                    self.paintToolMousePress(None, None, None)
            # end elif
            return False
        # end if
        return QGraphicsPathItem.itemChange(self, change, value)
    # end def

    def modelDeselect(self, document):
        """ A strand is selected based on whether its low or high endpoints
        are selected.  this value is a tuple (is_low, is_high) of booleans
        """
        strand = self._strand_item.strand()
        test = document.isModelStrandSelected(strand)
        low_val, high_val = document.getSelectedStrandValue(strand) if test else (False, False)
        if self.cap_type == 'low':
            out_value = (False, high_val)
        else:
            out_value = (low_val, False)
        if not out_value[0] and not out_value[1] and test:
            document.removeStrandFromSelection(strand)
        elif out_value[0] or out_value[1]:
            document.addStrandToSelection(strand, out_value)
        self.restoreParent()
    # end def

    def modelSelect(self, document):
        """ A strand is selected based on whether its low or high endpoints
        are selected.  this value is a tuple (is_low, is_high) of booleans
        """
        strand = self._strand_item.strand()
        test = document.isModelStrandSelected(strand)
        low_val, high_val = document.getSelectedStrandValue(strand) if test else (False, False)
        if self.cap_type == 'low':
            out_value = (True, high_val)
        else:
            out_value = (low_val, True)
        self.setSelected(True)
        self.setSelectedColor(True)
        document.addStrandToSelection(strand, out_value)
    # end def

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(self.path())
    # end def
