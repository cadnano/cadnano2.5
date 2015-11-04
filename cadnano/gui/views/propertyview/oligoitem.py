from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController
from .abstractproppartitem import AbstractPropertyPartItem

class OligoItem(AbstractPropertyPartItem):
    def __init__(self, model_part, parent=None):
        super(AbstractPropertyPartItem, self).__init__(model_part, parent)
        self._controller = OligoItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
    # end def

    def itemType(self):
        return ItemType.OLIGO
    # end def
# end class
