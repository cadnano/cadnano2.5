from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from .customtreewidgetitems import PropertyItem, SelectionItem

KEY_COL = 0
VAL_COL = 1

class VirtualHelixItem(QTreeWidgetItem, AbstractVirtualHelixItem):
    def __init__(self, model_virtual_helix, parent=None):
        super(VirtualHelixItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._controller = VirtualHelixItemController(self, model_virtual_helix)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self._model_virtual_helix = m_vh = model_virtual_helix
        self._parent_tree = parent
        root = parent.invisibleRootItem() # add propertyitems as siblings
        # Properties
        self._prop_items = {}
        self._model_props = m_vh.getPropertyDict()
        # add properties alphabetically, but with 'name' on top
        for key in sorted(self._model_props):
            p_i = self if key == 'name' else PropertyItem(m_vh, key, root)
            self._prop_items[key] = p_i
            p_i.setData(KEY_COL, Qt.EditRole, key)
            model_value = m_vh.getProperty(key)
            p_i.setData(VAL_COL, Qt.EditRole, model_value)
    # end def

    # SLOTS
    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        if property_key == 'eulerZ':
            self._handle.rotateWithCenterOrigin(new_value)
    # end def

    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        if self._model_virtual_helix == virtual_helix:
            self.updateViewProperty(property_key)

    ### PUBLIC SUPPORT METHODS ###
    def part(self):
        return self._model_part
    # end def

    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def updateModel(self):
        m_vh = self._model_virtual_helix
        for m_key, m_val in m_vh.getPropertyDict().iterItems():
            item_val = self._prop_items[key].data(VAL_COL, Qt.DisplayRole)
            if m_val != item_val:
                m_vh.setProperty(key, item_val)
    # end def

    def updateViewProperty(self, property_key):
        model_value = self._model_virtual_helix.getProperty(property_key)
        item_value = self._prop_items[property_key].data(VAL_COL, Qt.DisplayRole)
        if model_value != item_value:
            self._prop_items[property_key].setData(VAL_COL, Qt.EditRole, model_value)
    # end def

    # def updateViewProperties(self):
    #     m_vh = self._model_virtual_helix
    #     for m_key, m_val in m_vh.getPropertyDict().iterItems():
    #         item_val = self._prop_items[key].data(VAL_COL, Qt.DisplayRole)
    #         if m_val != item_val:
    #             self.setData(VAL_COL, Qt.EditRole, m_val)


# end class
