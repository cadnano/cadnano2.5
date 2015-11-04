from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartItem

class NucleicAcidPartItem(AbstractPropertyPartItem):
    def __init__(self, model_part, parent=None):
        super(NucleicAcidPartItem, self).__init__(model_part, parent)
        self._controller = NucleicAcidPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def
# end class
