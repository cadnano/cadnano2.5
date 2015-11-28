from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.plasmidpartitemcontroller import PlasmidPartItemController
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem

from .cnpropertyitem import CNPropertyItem

class PlasmidPartItem(CNPropertyItem, AbstractPartItem):
    def __init__(self, model_part, parent, key=None):
        super(PlasmidPartItem, self).__init__(odel_part, parent, key=ke)
        if key is None:
        	self._controller = PlasmidPartItemController(self, model_part)
    # end def

    def itemType(self):
        return ItemType.PLASMID
    # end def

# end class
