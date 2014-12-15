from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

DNAPART_ITEM_TYPE = 1100
DNA_SELECTION_ITEM_TYPE = 1110

class DnaPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, DNAPART_ITEM_TYPE)
        self._part = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        # Part
        self._part_name = "Dna%d" % parent.getInstanceCount()
        self._visible = True
        self._color = "#0066cc"
        self.setData(0, Qt.EditRole, self._part_name)
        self.setData(1, Qt.EditRole, self._visible)
        self.setData(2, Qt.EditRole, self._color)

        # Selections
        self._selection_twi = s = QTreeWidgetItem(self, DNA_SELECTION_ITEM_TYPE)
        s.setData(0, Qt.EditRole, "Selections")
        s.setData(1, Qt.EditRole, True)
        s.setData(2, Qt.EditRole, "#ffffff")

        self.setExpanded(True)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removeDnaPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def
# end class
