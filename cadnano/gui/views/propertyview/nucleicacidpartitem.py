from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.views.abstractpartitem import AbstractPartItem


class NucleicAcidPartItem(QTreeWidgetItem, AbstractPartItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = NucleicAcidPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        self._property_items = []

        for key in sorted(self._properties):
            p_wi = QTreeWidgetItem(self, QTreeWidgetItem.UserType)
            p_wi.setData(0, Qt.EditRole, key)
            p_wi.setData(1, Qt.EditRole, self._properties[key])
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removeNucleicAcidPartItem(self)
        self._model_part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            p_i = self._props[property_key]["p_i"]
            value = p_i.data(VAL_COL, Qt.DisplayRole)
            if value != new_value:
                p_i.setData(VAL_COL, Qt.EditRole, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def part(self):
        return self._model_part
    # end def

    def itemType(self):
        return ItemType.Dna
    # end def
# end class
