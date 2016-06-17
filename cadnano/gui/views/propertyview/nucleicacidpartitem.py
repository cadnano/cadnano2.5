from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartItem

KEY_COL = 0
VAL_COL = 1

class NucleicAcidPartItem(AbstractPropertyPartItem):
    def __init__(self, model_part, parent, key=None):
        super(NucleicAcidPartItem, self).__init__(model_part, parent, key=key)
        if key is None:
            self._controller = NucleicAcidPartItemController(self, model_part)
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def
# end class
