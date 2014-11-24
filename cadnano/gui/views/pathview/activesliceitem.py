from math import floor

from cadnano.gui.controllers.itemcontrollers.activesliceitemcontroller import ActiveSliceItemController
from . import pathstyles as styles
import cadnano.util as util

from PyQt5.QtCore import QPointF, QRectF, Qt, QObject, pyqtSignal, pyqtSlot, QEvent

from PyQt5.QtGui import QBrush, QFont, QPen, QDrag
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem, QUndoCommand, QGraphicsRectItem

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_BRUSH = QBrush(styles.ACTIVE_SLICE_HANDLE_FILL)
_LABEL_BRUSH = QBrush(styles.ORANGE_STROKE)
_PEN = QPen(styles.ACTIVE_SLICE_HANDLE_STROKE,\
            styles.SLICE_HANDLE_STROKE_WIDTH)
_FONT = QFont(styles.THE_FONT, 12, QFont.Bold)


class ActiveSliceItem(QGraphicsRectItem):
    """ActiveSliceItem for the Path View"""

    def __init__(self, part_item, active_base_index):
        super(ActiveSliceItem, self).__init__(part_item)
        self._part_item = part_item
        self._getActiveTool = part_item._getActiveTool
        self._active_slice = 0
        self._low_drag_bound = 0
        self._high_drag_bound = self.part().maxBaseIdx()
        self._controller = ActiveSliceItemController(self, part_item.part())

        self._label = QGraphicsSimpleTextItem("", parent=self)
        self._label.setPos(0, -18)
        self._label.setFont(_FONT)
        self._label.setBrush(_LABEL_BRUSH)
        self._label.hide()

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setZValue(styles.ZACTIVESLICEHANDLE)
        self.setRect(QRectF(0, 0, _BASE_WIDTH,\
                      self._part_item.boundingRect().height()))
        self.setPos(active_base_index*_BASE_WIDTH, 0)
        self.setBrush(_BRUSH)
        self.setPen(_PEN)

        # reuse select tool methods for other tools
        self.addSeqToolMousePress = self.selectToolMousePress
        self.addSeqToolMouseMove = self.selectToolMouseMove
        self.breakToolMousePress = self.selectToolMousePress
        self.breakToolMouseMove = self.selectToolMouseMove
        self.insertionToolMousePress = self.selectToolMousePress
        self.insertionToolMouseMove = self.selectToolMouseMove
        self.paintToolMousePress = self.selectToolMousePress
        self.paintToolMouseMove = self.selectToolMouseMove
        self.pencilToolMousePress = self.selectToolMousePress
        self.pencilToolMouseMove = self.selectToolMouseMove
        self.skipToolMousePress = self.selectToolMousePress
        self.skipToolMouseMove = self.selectToolMouseMove
    # end def

    ### SLOTS ###
    def strandChangedSlot(self, sender, vh):
        pass
    # end def

    def updateRectSlot(self, part):
        bw = _BASE_WIDTH
        new_rect = QRectF(0, 0, bw,\
                    self._part_item.virtualHelixBoundingRect().height())
        if new_rect != self.rect():
            self.setRect(new_rect)
        self._hideIfEmptySelection()
        self.updateIndexSlot(part, part.activeBaseIndex())
        return new_rect
    # end def

    def updateIndexSlot(self, part, base_index):
        """The slot that receives active slice changed notifications from
        the part and changes the receiver to reflect the part"""
        label = self._label
        bw = _BASE_WIDTH
        bi = util.clamp(int(base_index), 0, self.part().maxBaseIdx())
        self.setPos(bi * bw, -styles.PATH_HELIX_PADDING)
        self._active_slice = bi
        if label:
            label.setText("%d" % bi)
            label.setX((bw - label.boundingRect().width()) / 2)
    # end def

    ### ACCESSORS ###
    def activeBaseIndex(self):
        return self.part().activeBaseIndex()
    # end def

    def part(self):
        return self._part_item.part()
    # end def

    def partItem(self):
        return self._part_item
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def removed(self):
        scene = self.scene()
        scene.removeItem(self._label)
        scene.removeItem(self)
        self._part_item = None
        self._label = None
        self._controller.disconnectSignals()
        self.controller = None
    # end def

    def resetBounds(self):
        """Call after resizing virtualhelix canvas."""
        self._high_drag_bound = self.part().maxBaseIdx()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _hideIfEmptySelection(self):
        vis = self.part().numberOfVirtualHelices() > 0
        self.setVisible(vis)
        self._label.setVisible(vis)
    # end def

    def _setActiveBaseIndex(self, base_index):
        self.part().setActiveBaseIndex(base_index)
    # end def

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        self._part_item.updateStatusBar("%d" % self.part().activeBaseIndex())
        QGraphicsItem.hoverEnterEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self._part_item.updateStatusBar("")
        QGraphicsItem.hoverLeaveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent, calling the approproate tool method as
        necessary. Stores _move_idx for future comparison.
        """
        if event.button() != Qt.LeftButton:
            event.ignore()
            QGraphicsItem.mousePressEvent(self, event)
            return
        self.scene().views()[0].addToPressList(self)
        self._move_idx = int(floor((self.x() + event.pos().x()) / _BASE_WIDTH))
        tool_method_name = self._getActiveTool().methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):  # if the tool method exists
            modifiers = event.modifiers()
            getattr(self, tool_method_name)(modifiers)  # call tool method

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

    ### TOOL METHODS ###
    def selectToolMousePress(self, modifiers):
        """
        Set the allowed drag bounds for use by selectToolMouseMove.
        """
        if (modifiers & Qt.AltModifier) and (modifiers & Qt.ShiftModifier):
            self.part().undoStack().beginMacro("Auto-drag Scaffold(s)")
            for vh in self.part().getVirtualHelices():
                # SCAFFOLD
                # resize 3' first
                for strand in vh.scaffoldStrandSet():
                    idx5p = strand.idx5Prime()
                    idx3p = strand.idx3Prime()
                    if not strand.hasXoverAt(idx3p):
                        lo, hi = strand.getResizeBounds(idx3p)
                        if strand.isDrawn5to3():
                            strand.resize((idx5p, hi))
                        else:
                            strand.resize((lo, idx5p))
                # resize 5' second
                for strand in vh.scaffoldStrandSet():
                    idx5p = strand.idx5Prime()
                    idx3p = strand.idx3Prime()
                    if not strand.hasXoverAt(idx5p):
                        lo, hi = strand.getResizeBounds(idx5p)
                        if strand.isDrawn5to3():
                            strand.resize((lo, idx3p))
                        else:
                            strand.resize((idx3p, hi))
                # STAPLE
                # resize 3' first
                for strand in vh.stapleStrandSet():
                    idx5p = strand.idx5Prime()
                    idx3p = strand.idx3Prime()
                    if not strand.hasXoverAt(idx3p):
                        lo, hi = strand.getResizeBounds(idx3p)
                        if strand.isDrawn5to3():
                            strand.resize((idx5p, hi))
                        else:
                            strand.resize((lo, idx5p))
                # resize 5' second
                for strand in vh.stapleStrandSet():
                    idx5p = strand.idx5Prime()
                    idx3p = strand.idx3Prime()
                    if not strand.hasXoverAt(idx3p):
                        lo, hi = strand.getResizeBounds(idx5p)
                        if strand.isDrawn5to3():
                            strand.resize((lo, idx3p))
                        else:
                            strand.resize((idx3p, hi))

            self.part().undoStack().endMacro()
    # end def

    def selectToolMouseMove(self, modifiers, idx):
        """
        Given a new index (pre-validated as different from the prev index),
        calculate the new x coordinate for self, move there, and notify the
        parent strandItem to redraw its horizontal line.
        """
        idx = util.clamp(idx, self._low_drag_bound, self._high_drag_bound)
        x = int(idx * _BASE_WIDTH)
        self.setPos(x, self.y())
        self.updateIndexSlot(None, idx)
        self._setActiveBaseIndex(idx)
        self._part_item.updateStatusBar("%d" % self.part().activeBaseIndex())
    # end def
