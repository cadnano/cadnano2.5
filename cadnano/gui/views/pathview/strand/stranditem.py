#!/usr/bin/env python
# encoding: utf-8

from math import floor
from cadnano.gui.controllers.itemcontrollers.strand.stranditemcontroller import StrandItemController
from .endpointitem import EndpointItem
from cadnano.gui.views.pathview import pathstyles as styles
from .xoveritem import XoverItem
from .decorators.insertionitem import InsertionItem

import cadnano.gui.views.pathview.pathselection as pathselection

import cadnano.util as util
from cadnano import getBatch

from PyQt5.QtCore import QRectF, Qt, QObject, pyqtSignal

from PyQt5.QtGui import QBrush, QPen, QFont, QColor, QFontMetricsF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsSimpleTextItem


_BASE_WIDTH = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0,0, _BASE_WIDTH, _BASE_WIDTH)
_NO_PEN = QPen(Qt.NoPen)


class StrandItem(QGraphicsLineItem):
    _filter_name = "strand"
    
    def __init__(self, model_strand, virtual_helix_item, viewroot):
        """The parent should be a VirtualHelixItem."""
        super(StrandItem, self).__init__(virtual_helix_item)
        self._model_strand = model_strand
        self._virtual_helix_item = virtual_helix_item
        self._viewroot = viewroot
        self._getActiveTool = virtual_helix_item._getActiveTool

        self._controller = StrandItemController(self, model_strand)
        is_drawn_5to3 = model_strand.strandSet().isDrawn5to3()

        self._strand_filter = model_strand.strandFilter()

        self._insertion_items = {}
        # caps
        self._low_cap = EndpointItem(self, 'low', is_drawn_5to3)
        self._high_cap = EndpointItem(self, 'high', is_drawn_5to3)
        # self._high_cap = None
        self._dual_cap = EndpointItem(self, 'dual', is_drawn_5to3)

        # orientation
        self._is_drawn_5to3 = is_drawn_5to3
        # self._isOnTop = virtual_helix_item.isStrandOnTop(model_strand)
        # label
        self._seq_label = QGraphicsSimpleTextItem(self)
        
        self.refreshInsertionItems(model_strand)
        if not getBatch():
            self._updateSequenceText()

        # create a larger click area rect to capture mouse events
        self._click_area = c_a = QGraphicsRectItem(_DEFAULT_RECT, self)
        c_a.mousePressEvent = self.mousePressEvent
        c_a.setPen(_NO_PEN)
        self.setAcceptHoverEvents(True)
        c_a.setAcceptHoverEvents(True)
        c_a.hoverMoveEvent = self.hoverMoveEvent

        self.setZValue(styles.ZSTRANDITEM)

        # xover comming from the 3p end
        self._xover3pEnd = XoverItem(self, virtual_helix_item)
        if not getBatch():
            # initial refresh
            self._updateColor(model_strand)
            self._updateAppearance(model_strand)

        self.setZValue(styles.ZSTRANDITEM)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def strandResizedSlot(self, strand, indices):
        """docstring for strandResizedSlot"""
        low_moved = self._low_cap.updatePosIfNecessary(self.idxs()[0])
        high_moved = self._high_cap.updatePosIfNecessary(self.idxs()[1])
        group = self.group()
        self.tempReparent()  
        if low_moved:
            self.updateLine(self._low_cap)
        if high_moved:
            self.updateLine(self._high_cap)
        if strand.connection3p():
            self._xover3pEnd.update(strand)
        self.refreshInsertionItems(strand)
        self._updateSequenceText()
        if group:
            group.addToGroup(self)
    # end def

    def sequenceAddedSlot(self, oligo):
        """docstring for sequenceAddedSlot"""
        pass
    # end def

    def sequenceClearedSlot(self, oligo):
        """docstring for sequenceClearedSlot"""
        pass
    # end def

    def strandRemovedSlot(self, strand):
        # self._model_strand = None
        self._controller.disconnectSignals()
        self._controller = None
        scene = self.scene()
        scene.removeItem(self._click_area)
        self._high_cap.destroy()
        self._low_cap.destroy()
        # scene.removeItem(self._high_cap)
        # scene.removeItem(self._low_cap)
        scene.removeItem(self._seq_label)
        self._xover3pEnd.remove()
        self._xover3pEnd = None
        for insertionItem in self._insertion_items.values():
            insertionItem.remove()
        self._insertion_items = None
        self._click_area = None
        self._high_cap = None
        self._low_cap = None
        self._seq_label = None
        self._model_strand = None
        self._virtual_helix_item = None
        scene.removeItem(self)
    # end def

    def strandUpdateSlot(self, strand):
        """
        Slot for just updating connectivity and color, and endpoint showing
        """
        self._updateAppearance(strand)
    # end def

    def oligoAppearanceChangedSlot(self, oligo):
        strand = self._model_strand
        self._updateColor(strand)
        if strand.connection3p():
            self._xover3pEnd._updateColor(strand)
        for insertion in self.insertionItems().values():
            insertion.updateItem()
    # end def

    def oligoSequenceAddedSlot(self, oligo):
        self._updateSequenceText()
    # end def

    def oligoSequenceClearedSlot(self, oligo):
        self._updateSequenceText()
    # end def

    def strandHasNewOligoSlot(self, strand):
        strand = self._model_strand
        self._controller.reconnectOligoSignals()
        self._updateColor(strand)
        if strand.connection3p():
            self._xover3pEnd._updateColor(strand)
    # end def

    def strandInsertionAddedSlot(self, strand, insertion):
        self.insertionItems()[insertion.idx()] = \
                    InsertionItem(self._virtual_helix_item, strand, insertion)
    # end def
    def strandInsertionChangedSlot(self, strand, insertion):
        self.insertionItems()[insertion.idx()].updateItem()
    # end def

    def strandInsertionRemovedSlot(self, strand, index):
        instItem = self.insertionItems()[index]
        instItem.remove()
        del self.insertionItems()[index]
    # end def

    def strandModsAddedSlot(self, strand, mod_id, idx):
        idx_l, idx_h = strand.idxs()
        color = strand.part().getMod(mod_id)['color']
        if idx == idx_h:
            self._high_cap.showMod(mod_id, color)
        else:
            self._low_cap.showMod(mod_id, color) 
    # end def

    def strandModsChangedSlot(self, strand, mod_id, idx):
        idx_l, idx_h = strand.idxs()
        color = strand.part().getMod(mod_id)['color']
        if idx == idx_h:
            self._high_cap.changeMod(mod_id, color)
        else:
            self._low_cap.changeMod(mod_id, color) 
    # end def

    def strandModsRemovedSlot(self, strand, mod_id, idx):
        idx_l, idx_h = strand.idxs()
        color = strand.part().getMod(mod_id)['color']
        if idx == idx_h:
            self._high_cap.destroyMod()
        else:
            self._low_cap.destroyMod() 
    # end def

    def strandModifierAddedSlot(self, strand, modifier):
        pass
    # end def
    def strandModifierChangedSlot(self, strand, modifier):
        pass
    # end def
    def strandModifierRemovedSlot(self, strand, index):
        pass
    # end def

    def selectedChangedSlot(self, strand, indices):
        self.selectIfRequired(self.partItem().document(), indices)
    # end def

    ### ACCESSORS ###
    def viewroot(self):
        return self._viewroot
    # end def

    def insertionItems(self):
        return self._insertion_items
    # end def

    def strand(self):
        return self._model_strand
    # end def

    def strandFilter(self):
        return self._strand_filter
    # end def

    def idxs(self):
        return self._model_strand.idxs()
    # end def

    def virtualHelixItem(self):
        return self._virtual_helix_item
    # end def

    def partItem(self):
        return self._virtual_helix_item.partItem()
    # end def

    def window(self):
        return self._virtual_helix_item.window()

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def refreshInsertionItems(self, strand):
        i_items = self.insertionItems()
        i_model = strand.insertionsOnStrand()
        
        was_in_use = set(i_items)
        in_use = set()
        # add in the ones supposed to be there
        for insertion in i_model:
            idx = insertion.idx()
            in_use.add(idx)
            if idx in i_items:
                pass
            else:
                i_items[insertion.idx()] = \
                    InsertionItem(self._virtual_helix_item, strand, insertion)
        # end for
        
        # remove all in items
        not_in_use = was_in_use - in_use
        for index in not_in_use:
            i_items[index].remove()
            del i_items[index]
        # end for
    # end def

    def resetStrandItem(self, virtual_helix_item, is_drawn_5to3):
        self.setParentItem(virtual_helix_item)
        self._virtual_helix_item = virtual_helix_item
        self.resetEndPointItems(is_drawn_5to3)
    # end def

    def resetEndPointItems(self, is_drawn_5to3):
        self._is_drawn_5to3 = is_drawn_5to3
        self._low_cap.resetEndPoint(is_drawn_5to3)
        self._high_cap.resetEndPoint(is_drawn_5to3)
        self._dual_cap.resetEndPoint(is_drawn_5to3)
    # end def

    def updateLine(self, moved_cap):
        # setup
        bw = _BASE_WIDTH
        c_a = self._click_area
        line = self.line()
        # set new line coords
        if moved_cap == self._low_cap:
            p1 = line.p1()
            new_x = self._low_cap.pos().x() + bw
            p1.setX(new_x)
            line.setP1(p1)
            temp = c_a.rect()
            temp.setLeft(new_x)
            c_a.setRect(temp)
        else:
            p2 = line.p2()
            new_x = self._high_cap.pos().x()
            p2.setX(new_x)
            line.setP2(p2)
            temp = c_a.rect()
            temp.setRight(new_x)
            c_a.setRect(temp)
        self.setLine(line)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _updateAppearance(self, strand):
        """
        Prepare Strand for drawing, positions are relative to the VirtualHelixItem:
        1. Show or hide caps depending on L and R connectivity.
        2. Determine line coordinates.
        3. Apply paint styles.
        """
        # 0. Setup
        vhi = self._virtual_helix_item
        bw = _BASE_WIDTH
        half_base_width = bw / 2.0
        low_idx, high_idx = strand.lowIdx(), strand.highIdx()

        l_upper_left_x, l_upper_left_y = vhi.upperLeftCornerOfBase(low_idx, strand)
        h_upper_left_x, h_upper_left_y = vhi.upperLeftCornerOfBase(high_idx, strand)
        low_cap = self._low_cap
        high_cap = self._high_cap
        dual_cap = self._dual_cap

        # 1. Cap visibilty
        lx = l_upper_left_x + bw  # draw from right edge of base
        low_cap.safeSetPos(l_upper_left_x, l_upper_left_y)
        if strand.connectionLow() is not None:  # has low xover
            # if we are hiding it, we might as well make sure it is reparented to the StrandItem
            low_cap.restoreParent()
            low_cap.hide()
        else:  # has low cap
            if not low_cap.isVisible():
                low_cap.show()

        hx = h_upper_left_x  # draw to edge of base
        high_cap.safeSetPos(h_upper_left_x, h_upper_left_y)
        if strand.connectionHigh() is not None:  # has high xover
            # if we are hiding it, we might as well make sure it is reparented to the StrandItem
            high_cap.restoreParent()
            high_cap.hide()
        else:  # has high cap
            if not high_cap.isVisible():
                high_cap.show()

        # special case: single-base strand with no L or H connections,
        # (unconnected caps were made visible in previous block of code)
        if strand.length() == 1 and \
                  (low_cap.isVisible() and high_cap.isVisible()):
            low_cap.hide()
            high_cap.hide()
            dual_cap.safeSetPos(l_upper_left_x, l_upper_left_y)
            dual_cap.show()
        else:
            dual_cap.hide()

        # 2. Xover drawing
        xo = self._xover3pEnd
        if strand.connection3p():
            xo.update(strand)
            xo.showIt()
        else:
            xo.restoreParent()
            xo.hideIt()

        # 3. Refresh insertionItems if necessary drawing
        self.refreshInsertionItems(strand)

        # 4. Line drawing
        hy = ly = l_upper_left_y + half_base_width
        self.setLine(lx, ly, hx, hy)
        rectf = QRectF(l_upper_left_x + bw, l_upper_left_y, bw*(high_idx - low_idx - 1), bw)
        self._click_area.setRect(rectf)
        # self._updateHighlight(self.pen().color())
        self._updateColor(strand)
    # end def

    def _updateColor(self, strand):
        oligo = self._model_strand.oligo()
        color = QColor(oligo.color())
        self._updateHighlight(color)
    # end def

    def _updateHighlight(self, color):
        """
        
        """
        oligo = self._model_strand.oligo()
        pen_width = styles.PATH_STRAND_STROKE_WIDTH
        if oligo.shouldHighlight():
            color.setAlpha(128)
            pen_width = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
        pen = QPen(color, pen_width)
        # pen.setCosmetic(True)
        brush = QBrush(color)
        pen.setCapStyle(Qt.FlatCap)
        self.setPen(pen)
        self._low_cap.updateHighlight(brush)
        self._high_cap.updateHighlight(brush)
        self._dual_cap.updateHighlight(brush)
    # end def

    def _updateSequenceText(self):
        """
        docstring for _updateSequenceText
        """
        bw = _BASE_WIDTH
        seq_lbl = self._seq_label
        strand = self.strand()
        
        seq_txt = strand.sequence()
        isDrawn3to5 = not self._is_drawn_5to3
        textXCenteringOffset = styles.SEQUENCETEXTXCENTERINGOFFSET

        if seq_txt == '':
            seq_lbl.hide()
            for iItem in self.insertionItems().values():
                iItem.hideSequence()
            return
        # end if

        strand_seq_list = strand.getSequenceList()
        seq_list = [x[1][0] for x in strand_seq_list]
        insert_seq_list = [(x[0], x[1][1]) for x in strand_seq_list]
        
        i_items = self.insertionItems()
        for idx, seq_txt in insert_seq_list:
            if seq_txt != '':
                i_items[idx].setSequence(seq_txt)

        if isDrawn3to5:
            seq_list = seq_list[::-1]
            
        seq_txt = ''.join(seq_list)
        
        # seq_lbl.setPen(QPen( Qt.NoPen))    # leave the Pen as None for unless required
        seq_lbl.setBrush(QBrush(Qt.black))
        seq_lbl.setFont(styles.SEQUENCEFONT)

        # this will always draw from the 5 Prime end!
        seqX = 2*textXCenteringOffset + bw*strand.idx5Prime()
        seqY = styles.SEQUENCETEXTYCENTERINGOFFSET

        if isDrawn3to5:
            # offset it towards the bottom
            seqY += bw * .8
            # offset X by the reverse centering offset and the string length
            seqX += textXCenteringOffset
            # rotate the characters upside down this does not affect positioning
            # coordinate system, +Y is still Down, and +X is still Right
            seq_lbl.setRotation(180)
            # draw the text and reverse the string to draw 5 prime to 3 prime
            # seq_txt = seq_txt[::-1]
        # end if
        seq_lbl.setPos(seqX,seqY)
        seq_lbl.setText(seq_txt)
        seq_lbl.show()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        active_tool_str = self._getActiveTool().methodPrefix()
        self.scene().views()[0].addToPressList(self)
        idx = int(floor((event.pos().x()) / _BASE_WIDTH))
        self._virtual_helix_item.setActive(idx)
        tool_method_name =  active_tool_str + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            idx = int(floor((event.pos().x()) / _BASE_WIDTH))
            getattr(self, tool_method_name)(idx)
    # end def

    def hoverLeaveEvent(self, event):
        self.partItem().updateStatusBar("")
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverLeave"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event)
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        vhi_num = self._virtual_helix_item.number()
        idx = int(floor((event.pos().x()) / _BASE_WIDTH))
        oligo_length = self._model_strand.oligo().length()
        self.partItem().updateStatusBar("%d[%d]\tlength: %d" % (vhi_num, idx, oligo_length))
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event, idx)
    # end def

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            idx = int(floor((event.pos().x()) / _BASE_WIDTH))
            getattr(self, tool_method_name)(idx)
    # end def

    ### TOOL METHODS ###
    def breakToolMousePress(self, event, idx):
        """Break the strand is possible."""
        m_strand = self._model_strand
        m_strand.split(idx)
    # end def

    def breakToolHoverMove(self, event, idx):
        pass
        # m_strand = self._model_strand
        vhi = self._virtual_helix_item
        break_tool = self._getActiveTool()
        break_tool.hoverMove(vhi, event, flag=None)
        # break_tool.updateHoverRect(vhi, m_strand, idx, show=True)
    # end def

    def breakToolHoverLeave(self, event):
        self._getActiveTool().hoverLeaveEvent(event)
    # end def

    def selectToolMousePress(self, event, idx):
        event.setAccepted(False)
        current_filter_dict = self._viewroot.selectionFilterDict()
        if self.strandFilter() in current_filter_dict and self._filter_name in current_filter_dict:
            selection_group = self._viewroot.strandItemSelectionGroup()
            mod = Qt.MetaModifier
            if not (event.modifiers() & mod):
                 selection_group.clearSelection(False)
            selection_group.setSelectionLock(selection_group)
            selection_group.pendToAdd(self)
            selection_group.pendToAdd(self._low_cap)
            selection_group.pendToAdd(self._high_cap)
            selection_group.processPendingToAddList()
            event.setAccepted(True)
            return selection_group.mousePressEvent(event)
    # end def

    def eraseToolMousePress(self, event, idx):
        m_strand = self._model_strand
        m_strand.strandSet().removeStrand(m_strand)
    # end def

    def insertionToolMousePress(self, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._model_strand
        m_strand.addInsertion(idx, 1)
    # end def

    def paintToolMousePress(self, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._model_strand
        if m_strand.isStaple():
            color = self.window().path_color_panel.stapColorName()
        else:
            color = self.window().path_color_panel.scafColorName()
        m_strand.oligo().applyColor(color)
    # end def

    def pencilToolHoverMove(self, event, idx):
        """Pencil the strand is possible."""
        m_strand = self._model_strand
        vhi = self._virtual_helix_item
        active_tool = self._getActiveTool()

        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromStrandItem(vhi, m_strand, idx)
            # if m_strand.idx5Prime() == idx:
            #     temp_xover.hide3prime()
            # elif m_strand.idx3Prime() != idx:
            #     temp_xover.show3prime()
    # end def

    def pencilToolMousePress(self, event, idx):
        """Break the strand is possible."""
        m_strand = self._model_strand
        vhi = self._virtual_helix_item
        part_item = vhi.partItem()
        active_tool = self._getActiveTool()

        if active_tool.isFloatingXoverBegin():
            # block xovers starting at a 5 prime end
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

    def skipToolMousePress(self, event, idx):
        """Add an insert to the strand if possible."""
        m_strand = self._model_strand
        m_strand.addInsertion(idx, -1)
    # end def
    
    def addSeqToolMousePress(self, event, idx):
        """
        Checks that a scaffold was clicked, and then calls apply sequence
        to the clicked strand via its oligo.
        """
        m_strand = self._model_strand
        if m_strand.isScaffold():
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
    # end def
    
    def restoreParent(self, pos=None):
        """
        Required to restore parenting and positioning in the partItem
        """
        # map the position
        # print "restoring parent si"
        self.tempReparent(pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def
    
    def tempReparent(self, pos=None):
        vh_item = self.virtualHelixItem()
        if pos == None:
            pos = self.scenePos()
        self.setParentItem(vh_item)
        tempP = vh_item.mapFromScene(pos)
        self.setPos(tempP)
    # end def

    def setSelectedColor(self, value):
        if value == True:
            color = QColor("#ff3333")
        else:
            oligo = self._model_strand.oligo()
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
                viewroot = self._viewroot
                current_filter_dict = viewroot.selectionFilterDict()
                selection_group = viewroot.strandItemSelectionGroup()
        
                # only add if the selection_group is not locked out
                is_normal_select = selection_group.isNormalSelect()
                if value == True and (self._filter_name in current_filter_dict or not is_normal_select):
                    if self._strand_filter in current_filter_dict:
                        if self.group() != selection_group:
                            self.setSelectedColor(True)
                            # This should always be the case, but...
                            if is_normal_select:
                                selection_group.pendToAdd(self)
                                selection_group.setSelectionLock(selection_group)
                                selection_group.pendToAdd(self._low_cap)
                                selection_group.pendToAdd(self._high_cap)
                            # this else will capture the error.  Basically, the
                            # strandItem should be member of the group before this
                            # ever gets fired
                            else:
                                selection_group.addToGroup(self)
                        return True
                    else:
                        return False
                # end if
                elif value == True:
                    # Don't select
                    return False
                # end elif
                else:
                    # Deselect
                    # print "Deselecting strand"
                    selection_group.pendToRemove(self)
                    self.setSelectedColor(False)
                    selection_group.pendToRemove(self._low_cap)
                    selection_group.pendToRemove(self._high_cap)
                    return False
                # end else
            # end if
            elif active_tool.methodPrefix() == "paintTool":
                viewroot = self._viewroot
                current_filter_dict = viewroot.selectionFilterDict()
                if self._strand_filter in current_filter_dict:
                    if not active_tool.isMacrod():
                        active_tool.setMacrod()
                    self.paintToolMousePress(None, None)
            # end elif
            return False
        # end if
        return QGraphicsItem.itemChange(self, change, value)
    # end def

    def selectIfRequired(self, document, indices):
        """
        Select self or xover item as necessary
        """
        strand5p = self._model_strand
        con3p = strand5p.connection3p()
        selection_group = self._viewroot.strandItemSelectionGroup()
        # check this strand's xover
        idx_l, idx_h = indices
        if con3p:
            # perhaps change this to a direct call, but here are seeds of an 
            # indirect way of doing selection checks    
            if document.isModelStrandSelected(con3p) and document.isModelStrandSelected(strand5p):
                val3p = document.getSelectedStrandValue(con3p)
                # print "xover idx", indices
                test3p = val3p[0] if con3p.isDrawn5to3() else val3p[1]
                test5p = idx_h if strand5p.isDrawn5to3() else idx_l
                if test3p and test5p:
                    xoi = self._xover3pEnd
                    if not xoi.isSelected() or not xoi.group():
                        selection_group.setNormalSelect(False)
                        selection_group.addToGroup(xoi)
                        xoi.modelSelect(document)
                        selection_group.setNormalSelect(True)
                # end if
            # end if
        # end if
        # Now check the endpoints
        
        low_cap = self._low_cap
        if idx_l == True:
            if not low_cap.isSelected() or not low_cap.group():
                selection_group.addToGroup(low_cap)
                low_cap.modelSelect(document)
        else:
            if low_cap.isSelected() or low_cap.group():
                low_cap.restoreParent()
        high_cap = self._high_cap
        if idx_h == True:
            if not high_cap.isSelected() or not high_cap.group():
                selection_group.addToGroup(high_cap)
                high_cap.modelSelect(document)
        else:
            if high_cap.isSelected() or high_cap.group():
                high_cap.restoreParent()
        
        # now check the strand itself
        if idx_l == True and idx_h == True:
            if not self.isSelected() or not self.group():
                selection_group.setNormalSelect(False)
                selection_group.addToGroup(self)
                self.modelSelect(document)
                selection_group.setNormalSelect(True)
        elif idx_l == False and idx_h == False:
            self.modelDeselect(document)
    # end def

    def modelDeselect(self, document):
        self.restoreParent()
        self._low_cap.modelDeselect(document)
        self._high_cap.modelDeselect(document)
    # end def

    def modelSelect(self, document):
        self.setSelected(True)
        self.setSelectedColor(True)
    # end def
    
    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.drawLine(self.line())
    # end def
