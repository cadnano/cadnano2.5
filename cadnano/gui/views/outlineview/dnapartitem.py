from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

DNAPART_ITEM_TYPE = 1100

class DnaPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, DNAPART_ITEM_TYPE)
        self._part = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)
        self.setText(0, model_part.__class__.__name__)
    # end def

    def partRemovedSlot(self, sender):
        self._parent_tree.removeDnaPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def
# end class
