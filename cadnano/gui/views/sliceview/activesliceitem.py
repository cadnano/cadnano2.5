from PyQt5.QtCore import pyqtSignal, pyqtSlot, QPointF, Qt, QObject
from PyQt5.QtCore import QRectF, QEvent
from PyQt5.QtGui import QBrush, QFont, QPen, QDrag
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QUndoCommand, QGraphicsRectItem

from cadnano.gui.controllers.itemcontrollers.activesliceitemcontroller import ActiveSliceItemController
from . import slicestyles as styles


class ActiveSliceItem(QGraphicsRectItem):
    """ActiveSliceItem for the Slice View"""
    def __init__(self, nucleicacid_part_item, active_base_index):
        super(ActiveSliceItem, self).__init__(nucleicacid_part_item)
        self._nucleicacid_part_item = nucleicacid_part_item
        self._controller = ActiveSliceItemController(self, nucleicacid_part_item.part())
        self.setFlag(QGraphicsItem.ItemHasNoContents)
    # end def

    ### SLOTS ###
    def strandChangedSlot(self, sender, id_num):
        part = self.part()
        nucleicacid_part_item = self._nucleicacid_part_item
        vhi = nucleicacid_part_item.getVirtualHelixItem(id_num)
        active_base_idx = part.activeBaseIndex()

        has_scaf, has_stap = part.hasStrandAtIdx(id_num, active_base_idx)
        vhi.setActiveSliceView(active_base_idx, has_scaf, has_stap)
    # end def

    def updateIndexSlot(self, sender, new_active_slice_z_index):
        part = self.part()
        if part.numberOfVirtualHelices() == 0:
            return
        newly_active_vhs = set()
        active_base_idx = part.activeBaseIndex()
        for vhi in self._nucleicacid_part_item.getVirtualHelixItems():
            id_num = vhi.idNum()
            has_fwd, has_rev = part.hasStrandAtIdx(id_num, active_base_idx)
            vhi.setActiveSliceView(active_base_idx, has_fwd, has_rev)
    # end def

    def updateRectSlot(self, part):
        pass
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._nucleicacid_part_item.part()
    # end def

    ### PUBLIC METHODS FOR DRAWING / LAYOUT ###
    def removed(self):
        self._nucleicacid_part_item = None
        self._controller.disconnectSignals()
        self.controller = None
    # end def
