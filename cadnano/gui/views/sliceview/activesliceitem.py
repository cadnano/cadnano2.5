from cadnano.gui.controllers.itemcontrollers.activesliceitemcontroller import ActiveSliceItemController
from . import slicestyles as styles
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QPointF, Qt, QObject
from PyQt5.QtCore import QRectF, QEvent

from PyQt5.QtGui import QBrush, QFont, QPen, QDrag
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsSimpleTextItem, QUndoCommand, QGraphicsRectItem

class ActiveSliceItem(QGraphicsRectItem):
    """ActiveSliceItem for the Slice View"""
    def __init__(self, part_item, active_base_index):
        super(ActiveSliceItem, self).__init__(part_item)
        self._part_item = part_item
        self._controller = ActiveSliceItemController(self, part_item.part())
        self.setFlag(QGraphicsItem.ItemHasNoContents)
    # end def

    ### SLOTS ###
    def strandChangedSlot(self, sender, vh):
        if vh == None:
            return
        part_item = self._part_item
        vhi = part_item.getVirtualHelixItemByCoord(*vh.coord())
        active_base_idx = part_item.part().activeBaseIndex()
        has_scaf, has_stap = vh.hasStrandAtIdx(active_base_idx)
        vhi.setActiveSliceView(active_base_idx, has_scaf, has_stap)
    # end def

    def updateIndexSlot(self, sender, newActiveSliceZIndex):
        part = self.part()
        if part.numberOfVirtualHelices() == 0:
            return
        newly_active_vhs = set()
        active_base_idx = part.activeBaseIndex()
        for vhi in self._part_item._virtual_helix_hash.values():
            vh = vhi.virtualHelix()
            if vh:
                has_scaf, has_stap = vh.hasStrandAtIdx(active_base_idx)
                vhi.setActiveSliceView(active_base_idx, has_scaf, has_stap)
    # end def

    def updateRectSlot(self, part):
        pass
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._part_item.part()
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def removed(self):
        self._part_item = None
        self._controller.disconnectSignals()
        self.controller = None
    # end def
