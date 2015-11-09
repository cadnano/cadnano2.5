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
    def __init__(self, model_virtual_helix, parent=None, key=None):
        super(VirtualHelixItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self._model_virtual_helix = m_vh = model_virtual_helix
        if key is None:
            self._controller = VirtualHelixItemController(self, model_virtual_helix)
            self._parent_tree = parent
            root = parent.invisibleRootItem() # add propertyitems as siblings
            # Properties
            self._prop_items = {}
            model_props = m_vh.getPropertyDict()
            # add properties alphabetically, but with 'name' on top

            name = "vh%s" % str(m_vh.number())
            self._key = key = "name"
            self._prop_items[key] = name
            self.setData(KEY_COL, Qt.EditRole, key)
            self.setData(VAL_COL, Qt.EditRole, name) #Qt.DisplayRole

            for key in sorted(model_props):
                p_i = VirtualHelixItem(m_vh, key=key, parent=root)
                self._prop_items[key] = p_i
                p_i.setData(KEY_COL, Qt.EditRole, key)
                model_value = m_vh.getProperty(key)
                p_i.setData(VAL_COL, Qt.EditRole, model_value)
        else:
            self._key = key
    # end def

    def key(self):
        return self._key

    # SLOTS
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

    def configureEditor(self, parent_QWidget, option, model_index):
        data_type = type(model_index.model().data(model_index, Qt.DisplayRole))
        if data_type is str:
            editor = QLineEdit(parent_QWidget)
        elif data_type is int:
            editor = QSpinBox(parent_QWidget)
            editor.setRange(-359,359)
        elif data_type is float:
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setDecimals(0)
            editor.setRange(-359,359)
        elif data_type is bool:
            editor = QCheckBox(parent_QWidget)
        elif data_type is type(None):
            return None
        else:
            raise NotImplementedError
    # end def

    def updateModel(self):
        value = self.data(1, Qt.DisplayRole)
        self._model_virtual_helix.setProperty(self._key, value)

        # m_vh = self._model_virtual_helix
        # for m_key, m_val in m_vh.getPropertyDict().items():
        #     item_val = self._prop_items[key].data(VAL_COL, Qt.DisplayRole)
        #     if m_val != item_val:
        #         m_vh.setProperty(key, item_val)
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
