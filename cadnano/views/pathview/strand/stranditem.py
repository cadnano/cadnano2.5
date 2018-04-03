# -*- coding: utf-8 -*-
from math import floor
from typing import (
    Any
)

from PyQt5.QtCore import (
    QRectF,
    QPointF,
    Qt
)
from PyQt5.QtGui import (
    QMouseEvent,
    QPainter
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget
)

from cadnano import getBatch
from cadnano.controllers import StrandItemController
from cadnano.gui.palette import (
    getColorObj,
    getPenObj,
    getBrushObj,
    getNoPen
)
from cadnano.views.pathview import pathstyles as styles
from .decorators.insertionitem import InsertionItem
from .endpointitem import EndpointItem
from .xoveritem import XoverItem
from cadnano.views.pathview import (
    PathNucleicAcidPartItemT,
    PathVirtualHelixItemT,
    PathRootItemT
)
from cadnano.cntypes import (
    OligoT,
    StrandT,
    InsertionT,
    SegmentT,
    DocT,
    WindowT,
    ValueT
)

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_DEFAULT_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)
_NO_PEN = getNoPen()
SELECT_COLOR = "#ff3333"


class StrandItem(QGraphicsLineItem):
    FILTER_NAME = "strand"

    def __init__(self,  model_strand: StrandT,
                        virtual_helix_item: PathVirtualHelixItemT):
        """The parent should be a VirtualHelixItem.

        Args:
            model_strand:
            virtual_helix_item:
        """
        super(StrandItem, self).__init__(virtual_helix_item)
        self._model_strand = model_strand
        self._virtual_helix_item = virtual_helix_item
        self._viewroot: PathRootItemT = virtual_helix_item._viewroot
        self._getActiveTool = self._viewroot.manager.activeToolGetter

        self._controller = StrandItemController(model_strand, self)
        is_forward = model_strand.strandSet().isForward()

        self._strand_filter = model_strand.strandFilter()

        self._insertion_items = {}
        # caps
        self._low_cap = EndpointItem(self, 'low', is_forward)
        self._high_cap = EndpointItem(self, 'high', is_forward)
        self._dual_cap = EndpointItem(self, 'dual', is_forward)

        # orientation
        self.is_forward = is_forward
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
        self.xover_3p_end = XoverItem(self, virtual_helix_item)
        if not getBatch():
            # initial refresh
            self._updateColor(model_strand)
            self._updateAppearance(model_strand)

        self.setZValue(styles.ZSTRANDITEM)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def strandResizedSlot(self, strand: StrandT, indices: SegmentT):
        """Slot for handling resizing of this StrandItem

        Args:
            strand:
            indices: low and high indices
        """
        low_moved, group_low = self._low_cap.updatePosIfNecessary(self.idxs()[0])
        high_moved, group_high = self._high_cap.updatePosIfNecessary(self.idxs()[1])
        group = self.group()
        self.tempReparent()
        if low_moved:
            self.updateLine(self._low_cap)
        if high_moved:
            self.updateLine(self._high_cap)
        if strand.connection3p():
            self.xover_3p_end.update(strand)
        self.refreshInsertionItems(strand)
        self._updateSequenceText()
        if group:
            group.addToGroup(self)
        if group_low is not None:
            group_low.addToGroup(self._low_cap)
        if group_high is not None:
            group_high.addToGroup(self._high_cap)
    # end def

    def strandRemovedSlot(self, strand: StrandT):
        """Slot for handling removing of this StrandItem

        Args:
            strand:
        """
        self.destroyItem()
    # end def

    def destroyItem(self):
        print("Destroying Path StrandItem")
        self._controller.disconnectSignals()
        self._controller = None
        scene = self.scene()
        scene.removeItem(self._click_area)
        self._high_cap.destroyItem()
        self._low_cap.destroyItem()
        # scene.removeItem(self._high_cap)
        # scene.removeItem(self._low_cap)
        scene.removeItem(self._seq_label)
        self.xover_3p_end.destroyItem()
        self.xover_3p_end = None
        for insertionItem in list(self._insertion_items.values()):
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

    def strandConnectionChangedSlot(self, strand: StrandT):
        """Slot for just updating connectivity and color, and endpoint showing

        Args:
            strand:
        """
        self._updateAppearance(strand)
    # end def

    def oligoPropertyChangedSlot(self, oligo: OligoT, key: str, new_value: ValueT):
        """Slot for just updating Oligo properties in the path view

        Args:
            oligo:
            key: property key
            new_value (duck): `str`, `int`, `float`, `list`, or `tuple`
        """
        xover_3p_end = self.xover_3p_end
        strand = self._model_strand
        if key == 'is_visible':
            document = self._viewroot.document()
            # print("isselect", self.isSelected(), new_value)
            if new_value:
                self.show()
                xover_3p_end.show()
                xover_3p_end.modelSelect(document)
                self.selectIfRequired(document, (True, True))
            else:
                self._low_cap.hide()
                self._high_cap.hide()
                self._dual_cap.hide()
                self.hide()
                xover_3p_end.hide()
                return
        try:
            self._updateAppearance(strand)
        except Exception:
            print(oligo, key, new_value)
            raise
        for insertion in self.insertionItems().values():
            insertion.updateItem()
    # end def

    def oligoSequenceAddedSlot(self, oligo: OligoT):
        """Slot for updating the oligo sequence

        Args:
            oligo:
        """
        self._updateSequenceText()
    # end def

    def oligoSequenceClearedSlot(self, oligo: OligoT):
        """Slot for deleting the oligo sequence

        Args:
            oligo:
        """
        self._updateSequenceText()
    # end def

    def oligoSelectedChangedSlot(self, oligo: OligoT, new_value: ValueT):
        pass
    # end def

    def strandHasNewOligoSlot(self, strand: StrandT):
        """Slot for changing the `Oligo` of the model `Strand`

        Args:
            strand:
        """
        strand = self._model_strand
        self._controller.reconnectOligoSignals()
        self._updateColor(strand)
        if strand.connection3p():
            self.xover_3p_end._updateColor(strand)
        for insertion in self.insertionItems().values():
            insertion.updateItem()
    # end def

    def strandInsertionAddedSlot(self, strand: StrandT, insertion: InsertionT):
        """Slot for adding insertions to a `Strand`

        Args:
            strand:
            insertion:
        """
        if self._viewroot.are_signals_on:
            self.insertionItems()[insertion.idx()] = InsertionItem(self._virtual_helix_item,
                                                                   strand,
                                                                   insertion)
    # end def

    def strandInsertionChangedSlot(self, strand: StrandT, insertion: InsertionT):
        """Slot for changing an insertion on the Strand

        Args:
            strand:
            insertion:
        """
        self.insertionItems()[insertion.idx()].updateItem()
    # end def

    def strandInsertionRemovedSlot(self, strand: StrandT, index: int):
        """Slot for removing an insertion on the Strand

        Args:
            strand:
            index: index of the insertion
        """
        inst_item = self.insertionItems()[index]
        inst_item.destroyItem()
        del self.insertionItems()[index]
    # end def

    def strandModsAddedSlot(self, strand: StrandT,
                                document: DocT,
                                mod_id: str,
                                idx: int):
        """Slot for adding a modification on the Strand

        Args:
            strand:
            document:
            mod_id:
            idx:
        """
        if self._viewroot.are_signals_on:
            idx_l, idx_h = strand.idxs()
            color = document.getModProperties(mod_id)['color']
            if idx == idx_h:
                self._high_cap.showMod(mod_id, color)
            else:
                self._low_cap.showMod(mod_id, color)
    # end def

    def strandModsChangedSlot(self, strand: StrandT,
                                document: DocT,
                                mod_id: str,
                                idx: int):
        """Slot for changing a modification on the Strand

        Args:
            strand:
            document:
            mod_id:
            idx:
        """
        idx_l, idx_h = strand.idxs()
        color = document.getModProperties(mod_id)['color']
        if idx == idx_h:
            self._high_cap.changeMod(mod_id, color)
        else:
            self._low_cap.changeMod(mod_id, color)
    # end def

    def strandModsRemovedSlot(self, strand: StrandT,
                                document: DocT,
                                mod_id: str,
                                idx: int):
        """Slot for removing a modification on the Strand

        Args:
            strand:
            document:
            mod_id:
            idx:
        """
        idx_l, idx_h = strand.idxs()
        # color = document.getModProperties(mod_id)['color']
        if idx == idx_h:
            self._high_cap.destroyMod()
        else:
            self._low_cap.destroyMod()
    # end def

    def strandSelectedChangedSlot(self, strand: StrandT, indices: SegmentT):
        """Slot for changing the selection on the strand

        Args:
            strand:
            indices: low and high indices of the selection
        """
        self.selectIfRequired(self._viewroot.document(), indices)
    # end def

    ### ACCESSORS ###
    def viewroot(self) -> PathRootItemT:
        return self._viewroot
    # end def

    def insertionItems(self) -> dict:
        return self._insertion_items
    # end def

    def strand(self) -> StrandT:
        return self._model_strand
    # end def

    def strandFilter(self) -> str:
        return self._strand_filter
    # end def

    def idxs(self) -> SegmentT:
        """Return the lowest and highest (left most, righ most) in the path view
        from the model

        Returns:
            tuple: (low idx, high idx) of index integers
        """
        return self._model_strand.idxs()
    # end def

    def virtualHelixItem(self) -> PathVirtualHelixItemT:
        return self._virtual_helix_item
    # end def

    def partItem(self) -> PathNucleicAcidPartItemT:
        return self._virtual_helix_item.partItem()
    # end def

    def idNum(self):
        return self._virtual_helix_item.idNum()

    def window(self) -> WindowT:
        return self._viewroot.window()

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def refreshInsertionItems(self, strand: StrandT):
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
            i_items[index].destroyItem()
            del i_items[index]
        # end for
    # end def

    def resetStrandItem(self, virtual_helix_item: PathVirtualHelixItemT,
                            is_forward: bool):
        self.setParentItem(virtual_helix_item)
        self._virtual_helix_item = virtual_helix_item
        self.resetEndPointItems(is_forward)
    # end def

    def resetEndPointItems(self, is_forward: bool):
        self.is_forward = is_forward
        self._low_cap.resetEndPoint(is_forward)
        self._high_cap.resetEndPoint(is_forward)
        self._dual_cap.resetEndPoint(is_forward)
    # end def

    def updateLine(self, moved_cap: EndpointItem):
        """must be called when parented to a :class:`PathVirtualHelixItem`
        """
        # setup
        bw = _BASE_WIDTH
        c_a = self._click_area
        line = self.line()
        # set new line coords
        if moved_cap == self._low_cap:
            p1 = line.p1()
            new_x = self._low_cap.pos().x() + bw
            # new_x = self.mapFromScene(self._low_cap.pos()).x() + bw
            p1.setX(new_x)
            line.setP1(p1)
            temp = c_a.rect()
            temp.setLeft(new_x)
            c_a.setRect(temp)
        else:
            p2 = line.p2()
            new_x = self._high_cap.pos().x()
            # new_x = self.mapFromScene(self._high_cap.pos()).x() + bw
            p2.setX(new_x)
            line.setP2(p2)
            temp = c_a.rect()
            temp.setRight(new_x)
            c_a.setRect(temp)
        self.setLine(line)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _updateAppearance(self, strand: StrandT):
        """Prepare Strand for drawing, positions are relative to the
        :class:`PathVirtualHelixItem`:

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
        if strand.length() == 1 and (low_cap.isVisible() and high_cap.isVisible()):
            low_cap.hide()
            high_cap.hide()
            dual_cap.safeSetPos(l_upper_left_x, l_upper_left_y)
            dual_cap.show()
        else:
            dual_cap.hide()

        # 2. Xover drawing
        xo = self.xover_3p_end
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
        self._updateColor(strand)
    # end def

    def _updateColor(self, strand: StrandT):
        oligo = strand.oligo()
        color = SELECT_COLOR if self.isSelected() else oligo.getColor()
        if oligo.shouldHighlight():
            alpha = 128
            pen_width = styles.PATH_STRAND_HIGHLIGHT_STROKE_WIDTH
        else:
            pen_width = styles.PATH_STRAND_STROKE_WIDTH
            alpha = None
        self.xover_3p_end._updateColor(strand)
        pen = getPenObj(color, pen_width, alpha=alpha, capstyle=Qt.FlatCap)
        brush = getBrushObj(color, alpha=alpha)
        self.setPen(pen)
        self._low_cap.updateHighlight(brush)
        self._high_cap.updateHighlight(brush)
        self._dual_cap.updateHighlight(brush)
    # end def

    def _updateSequenceText(self):
        """update the sequences text on this :class:`StrandItem`
        """
        # print("updating sequence")
        bw = _BASE_WIDTH
        seq_lbl = self._seq_label
        strand = self.strand()

        seq_txt = strand.sequence()
        isDrawn3to5 = not self.is_forward
        text_X_centering_offset = styles.SEQUENCETEXTXCENTERINGOFFSET

        if seq_txt == '':
            seq_lbl.hide()
            for i_item in self.insertionItems().values():
                i_item.hideSequence()
            return
        # end if

        strand_seq_list = strand.getSequenceList()
        seq_list = [x[1][0] for x in strand_seq_list]
        insert_seq_list = [(x[0], x[1][1]) for x in strand_seq_list]

        i_items = self.insertionItems()
        for idx, seq_txt in insert_seq_list:
            if seq_txt not in ['', ' ']:
                i_items[idx].setSequence(seq_txt)

        if isDrawn3to5:
            seq_list = seq_list[::-1]

        seq_txt = ''.join(seq_list)

        # seq_lbl.setPen(QPen( Qt.NoPen))    # leave the Pen as None for unless required
        seq_lbl.setBrush(getBrushObj(styles.SEQUENCEFONTCOLOR))
        seq_lbl.setFont(styles.SEQUENCEFONT)

        # this will always draw from the 5 Prime end!
        seqX = 2*text_X_centering_offset + bw*strand.idx5Prime()
        seqY = styles.SEQUENCETEXTYCENTERINGOFFSET

        if isDrawn3to5:
            # offset it towards the bottom
            seqY += bw * .8
            # offset X by the reverse centering offset and the string length
            seqX += text_X_centering_offset*.75
            # rotate the characters upside down this does not affect positioning
            # coordinate system, +Y is still Down, and +X is still Right
            seq_lbl.setRotation(180)
            # draw the text and reverse the string to draw 5 prime to 3 prime
            # seq_txt = seq_txt[::-1]
        # end if
        seq_lbl.setPos(seqX, seqY)
        seq_lbl.setText(seq_txt)
        seq_lbl.show()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Parses a :class:`QGraphicsSceneMouseEvent` to extract base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event:
        """
        active_tool_str = self._getActiveTool().methodPrefix()
        self.scene().views()[0].addToPressList(self)
        idx = int(floor((event.pos().x()) / _BASE_WIDTH))
        self._virtual_helix_item.setActive(self.is_forward, idx)
        tool_method_name = active_tool_str + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Parses a :class:`QGraphicsSceneMouseEvent` to extract base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event:
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            idx = int(floor((event.pos().x()) / _BASE_WIDTH))
            getattr(self, tool_method_name)(idx)
    # end def

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """"Parses a :class:`QGraphicsSceneHoverEvent` to extract base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event:
        """
        self.partItem().updateStatusBar("")
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverLeave"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event)
    # end def

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Parses a :class:`QGraphicsSceneHoverEvent` to extract a base index,
        forwarding them to approproate tool method as necessary.
        Updates the status bar

        Args:
            event:
        """
        vhi_num = self._virtual_helix_item.idNum()
        idx = int(floor((event.pos().x()) / _BASE_WIDTH))
        oligo_length = self._model_strand.oligo().length()
        self.partItem().updateStatusBar("%d[%d]\tlength: %d" % (vhi_num, idx, oligo_length))
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(event, idx)
    # end def

    def customMouseRelease(self, event: QMouseEvent):
        """Parses a :class:`QMouseEvent` to extract strandSet and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event:
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            idx = int(floor((event.pos().x()) / _BASE_WIDTH))
            getattr(self, tool_method_name)(idx)
    # end def

    ### TOOL METHODS ###
    def addSeqToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """
        Args:
            event:
            idx:
        """
        oligo = self._model_strand.oligo()
        add_seq_tool = self._getActiveTool()
        add_seq_tool.applySequence(oligo)
    # end def

    def addSeqToolHoverMove(self, event: QGraphicsSceneHoverEvent, idx: int):
        """
        Args:
            event (:obj:`PyQt5.QtGui.QHoverEvent`):
            idx (int):
        """
        vhi = self._virtual_helix_item
        add_seq_tool = self._getActiveTool()
        add_seq_tool.hoverMove(vhi, event, flag=None)
    # end def

    def addSeqToolHoverLeave(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event (:obj:`PyQt5.QtGui.QHoverEvent`):
        """
        self._getActiveTool().hoverLeaveEvent(event)
    # end def

    def breakToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Break the strand if possible.

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        m_strand.split(idx)
    # end def

    def breakToolHoverMove(self, event: QGraphicsSceneHoverEvent, idx: int):
        """Hover move over the strand

        Args:
            event (:obj:`PyQt5.QtGui.QHoverEvent`):
            idx (int):
        """
        vhi = self._virtual_helix_item
        break_tool = self._getActiveTool()
        break_tool.hoverMove(vhi, event, flag=None)
        # break_tool.updateHoverRect(vhi, m_strand, idx, show=True)
    # end def

    def breakToolHoverLeave(self, event: QGraphicsSceneHoverEvent):
        """Hover leave the strand

        Args:
            event (:obj:`PyQt5.QtGui.QHoverEvent`):
        """
        self._getActiveTool().hoverLeaveEvent(event)
    # end def

    def selectToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Mouse press over the strand for select tool

        Args:
            event (:obj:`PyQt5.QtGui.QMouseEvent`):
            idx (int):
        """
        event.setAccepted(False)
        current_filter_set = self._viewroot.selectionFilterSet()
        if ( all(f in current_filter_set for f in self.strandFilter()) and
            self.FILTER_NAME in current_filter_set):
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

    def eraseToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Mouse press over the strand for erase tool

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        m_strand.strandSet().removeStrand(m_strand)
    # end def

    def insertionToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Add an insert to the strand if possible.

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        m_strand.addInsertion(idx, 1)
    # end def

    def paintToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Add an insert to the strand if possible.
        Called by XoverItem.paintToolMousePress with event as None
        """
        m_strand = self._model_strand
        if event is None:
            color = m_strand.oligo().getColor()
        elif event.modifiers() & Qt.ShiftModifier:
            color = self.window().path_color_panel.shiftColorName()
        else:
            color = self.window().path_color_panel.colorName()
        m_strand.oligo().applyColor(color)
    # end def

    def createToolHoverMove(self, event: QGraphicsSceneHoverEvent, idx: int):
        """Create the strand if possible.

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        vhi = self._virtual_helix_item
        active_tool = self._getActiveTool()

        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromStrandItem(vhi, m_strand, idx)
    # end def

    def createToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Break the strand is possible.

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        vhi = self._virtual_helix_item
        # part_item = vhi.partItem()
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

    def skipToolMousePress(self, event: QGraphicsSceneMouseEvent, idx: int):
        """Add an insert to the strand if possible.

        Args:
            event:
            idx:
        """
        m_strand = self._model_strand
        m_strand.addInsertion(idx, -1)
    # end def

    def restoreParent(self, pos: QPointF = None):
        """Required to restore parenting and positioning in the
        :class:`PathNucleicAcidPartItemT`

        Args:
            pos: default ``None``, position of part
        """
        self.tempReparent(pos)
        self.setSelectedColor(False)
        self.setSelected(False)
    # end def

    def tempReparent(self, pos: QPointF = None):
        """Temporarily reparent to the vh_item to make sure position is correct

        Args:
            pos: default ``None``, position of part
        """
        vh_item = self.virtualHelixItem()
        if pos is None:
            pos = self.scenePos()
        self.setParentItem(vh_item)
        tempP = vh_item.mapFromScene(pos)
        self.setPos(tempP)
    # end def

    def setSelectedColor(self, use_default: bool):
        """
        Args:
            use_default:
        """
        if use_default == True: # use_default resolves to int from QVariant, must use ==
            color = getColorObj(SELECT_COLOR)
        else:
            oligo = self._model_strand.oligo()
            color = getColorObj(oligo.getColor())
            if oligo.shouldHighlight():
                color.setAlpha(128)
        pen = self.pen()
        pen.setColor(color)
        self.setPen(pen)
    # end def

    def itemChange(self,    change: QGraphicsItem.GraphicsItemChange,
                            value: Any) -> bool:
        """Used for selection of the :class:`StrandItem`

        Args:
            change: parameter that is changing
            value : new value whose type depends on the ``change`` argument

        Returns:
            If the change is a ``QGraphicsItem.ItemSelectedChange``::

                ``True`` if selected, other ``False``

            Otherwise default to :meth:`QGraphicsItem.itemChange()` result
        """
        # for selection changes test against QGraphicsItem.ItemSelectedChange
        # intercept the change instead of the has changed to enable features.
        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            active_tool = self._getActiveTool()
            if active_tool.methodPrefix() == "selectTool":
                viewroot = self._viewroot
                current_filter_set = viewroot.selectionFilterSet()
                selection_group = viewroot.strandItemSelectionGroup()

                # only add if the selection_group is not locked out
                is_normal_select = selection_group.isNormalSelect()
                if value == True and (self.FILTER_NAME in current_filter_set or not is_normal_select):
                    if all(f in current_filter_set for f in self.strandFilter()):
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
                elif value == True: # noqa value resolves to int from QVariant, must use ==
                    # Don't select
                    return False
                # end elif
                else:
                    # Deselect
                    # print("Deselecting strand")
                    selection_group.pendToRemove(self)
                    self.setSelectedColor(False)
                    selection_group.pendToRemove(self._low_cap)
                    selection_group.pendToRemove(self._high_cap)
                    return False
                # end else
            # end if
            elif active_tool.methodPrefix() == "paintTool":
                viewroot = self._viewroot
                current_filter_set = viewroot.selectionFilterSet()
                if all(f in current_filter_set for f in self.strandFilter()):
                    if not active_tool.isMacrod():
                        active_tool.setMacrod()
                    self.paintToolMousePress(None, None)
            # end elif
            return False
        # end if
        return QGraphicsItem.itemChange(self, change, value)
    # end def

    def selectIfRequired(self, document: DocT, indices: SegmentT):
        """Select self or xover item as necessary

        Args:
            document:
            indices: low and high index
        """
        strand5p = self._model_strand
        con3p = strand5p.connection3p()
        selection_group = self._viewroot.strandItemSelectionGroup()
        # check this strand's xover
        idx_l, idx_h = indices
        if con3p:
            # perhaps change this to a direct call, but here are seeds of an
            # indirect way of doing selection checks
            if (document.isModelStrandSelected(con3p) and
               document.isModelStrandSelected(strand5p)):
                val3p = document.getSelectedStrandValue(con3p)
                # print("xover idx", indices)
                test3p = val3p[0] if con3p.isForward() else val3p[1]
                test5p = idx_h if strand5p.isForward() else idx_l
                if test3p and test5p:
                    xoi = self.xover_3p_end
                    # if not xoi.isSelected() or not xoi.group():
                    if not xoi.isSelected() or xoi.group() is None:
                        selection_group.setNormalSelect(False)
                        selection_group.addToGroup(xoi)
                        xoi.modelSelect(document)
                        selection_group.setNormalSelect(True)
            else:
                xoi = self.xover_3p_end
                xoi.restoreParent()
                # # print("should deselect xover")
                # if xoi.isSelected() or xoi.group() is not None:
                #     selection_group.setNormalSelect(False)
                #     selection_group.addToGroup(xoi)
                #     xoi.modelDeselect(document)
                #     selection_group.setNormalSelect(True)
            # end if
        # end if
        # Now check the endpoints

        low_cap = self._low_cap
        if idx_l == True: # noqa value resolves to int from QVariant, must use ==
            if not low_cap.isSelected() or not low_cap.group():
                selection_group.addToGroup(low_cap)
                low_cap.modelSelect(document)
        else:
            if low_cap.isSelected() or low_cap.group():
                low_cap.restoreParent()
        high_cap = self._high_cap
        if idx_h == True: # noqa value resolves to int from QVariant, must use ==
            if not high_cap.isSelected() or not high_cap.group():
                selection_group.addToGroup(high_cap)
                high_cap.modelSelect(document)
        else:
            if high_cap.isSelected() or high_cap.group():
                high_cap.restoreParent()

        # now check the strand itself
        if idx_l == True and idx_h == True: # noqa value resolves to int from QVariant, must use ==
            if not self.isSelected() or not self.group():
                selection_group.setNormalSelect(False)
                selection_group.addToGroup(self)
                self.modelSelect(document)
                selection_group.setNormalSelect(True)
        elif idx_l == False and idx_h == False: # noqa value resolves to int from QVariant, must use ==
            self.modelDeselect(document)
    # end def

    def modelDeselect(self, document: DocT):
        """Deselect indices

        Args:
            document:
        """
        self.restoreParent()
        self._low_cap.modelDeselect(document)
        self._high_cap.modelDeselect(document)
    # end def

    def modelSelect(self, document: DocT):
        """Select Strand

        Args:
            document:
        """
        self.setSelected(True)
        self.setSelectedColor(True)
    # end def

    def paint(self, painter: QPainter,
                    option: QStyleOptionGraphicsItem,
                    widget: QWidget):
        """Paint this strand

        Args:
            painter:
            option
            widget:
        """
        painter.setPen(self.pen())
        painter.drawLine(self.line())
    # end def

    def setActiveEndpoint(self, cap_type: str) -> int:
        """Set the active index in the VirtualHelix

        Args:
            cap_type: 'low', 'hi'

        Returns:
            index of cap as a convenience
        """
        idx_l, idx_h = self._model_strand.idxs()
        idx = idx_l if cap_type == 'low' else idx_h
        self._virtual_helix_item.setActive(self.is_forward, idx)
        return idx
# end class
