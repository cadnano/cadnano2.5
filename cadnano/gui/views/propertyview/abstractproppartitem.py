from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.plasmidpartitemcontroller import PlasmidPartItemController
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem

from .cnpropertyitem import CNPropertyItem

class AbstractPropertyPartItem(CNPropertyItem, AbstractPartItem):
    def __init__(self, model_part, parent, key=None):
        super(AbstractPropertyPartItem, self).__init__(model_part, parent, key=key)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        # self.parent.removePartItem(self)
        self._cn_model = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._cn_model == model_part:
            self.setValue(property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def