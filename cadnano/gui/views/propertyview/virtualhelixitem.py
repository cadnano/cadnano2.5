from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject, QVariant
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QLineEdit

from PyQt5.QtWidgets import QCheckBox

KEY_COL = 0
VAL_COL = 1


from cadnano.enum import ItemType
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController

from .cnpropertyitem import CNPropertyItem

class VirtualHelixItem(QTreeWidgetItem):
    def __init__(self, model_part, parent, id_num, key=None):
        self._id_num = id_num
        self._cn_model = model_part
        self._virtual_helix_group = model_part.virtualHelixGroup()
        self._controller = None
        # QTreeWidgetItem.__init__(self, parent, QTreeWidgetItem.UserType)
        super(VirtualHelixItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        if key is None:
            self._controller = VirtualHelixItemController(self, model_part, True, False)
            self._parent_tree = parent
            root = parent.invisibleRootItem() # add propertyitems as siblings

            # Properties
            self._prop_items = {}
            model_props = AbstractVirtualHelixItem.getAllProperties(self)
            # print("^^^^^^^", model_props)
            # add properties alphabetically, but with 'name' on top
            name = model_props['name']
            if name is None:
                name = "generic"
            self._key = key = "name"
            self._prop_items[key] = self
            self.setData(KEY_COL, Qt.EditRole, key)
            self.setData(VAL_COL, Qt.EditRole, name)

            for key in sorted(model_props):
                if key == 'name':
                    continue
                p_i = VirtualHelixItem(model_part, root, id_num, key=key)
                self._prop_items[key] = p_i
                p_i.setData(KEY_COL, Qt.EditRole, key)
                model_value = model_props[key]
                if isinstance(model_value, float):
                    model_value = "%0.2f" % model_value
                elif not isinstance(model_value, str):    # can't get non-strings to work
                    model_value = str(model_value)
                p_i.setData(VAL_COL, Qt.EditRole, model_value)
        else:
            self._key = key
    # end def

    def key(self):
        return self._key

    ### PUBLIC SUPPORT METHODS ###
    def cnModel(self):
        return self._cn_model
    # end def

    def itemType(self):
        return None
    # end def

    def disconnectSignals(self):
        if self._controller is not None:
            self._controller.disconnectSignals()
            self._controller = None
    # end def

    # SLOTS
    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, keys, values):
        if self._cn_model == sender and id_num == self._id_num:
            for key, val in zip(keys, values):
                self.setValue(key, val)

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        if self._cn_model == sender and id_num == self._id_num:
            self._cn_model = None
            self._controller = None
            self.parent().removeChild(self)

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def configureEditor(self, parent_QWidget, option, model_index):
        key = self.key()
        if key == 'eulerZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_QWidget)
            tpb = AbstractVirtualHelixItem.getProperty(self, 'twist_per_base')
            editor.setSingleStep(tpb)
            editor.setDecimals(1)
            editor.setRange(0, 359)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def

    def updateCNModel(self):
        value = self.data(1, Qt.DisplayRole)
        AbstractVirtualHelixItem.setProperty(self, self._key, value)
    # end def

    def setValue(self, property_key, new_value):
        p_i = self._prop_items[property_key]
        current_value = p_i.data(VAL_COL, Qt.DisplayRole)
        if current_value != new_value:
            p_i.setData(VAL_COL, Qt.EditRole, new_value)
    # end def

    def getItemValue(self, property_key):
        return self._prop_items[property_key].data(VAL_COL, Qt.DisplayRole)
    # end def

    def updateViewProperty(self, property_key):
        model_value = AbstractVirtualHelixItem.getProperty(self, property_key)
        item_value = self._prop_items[property_key].data(VAL_COL, Qt.DisplayRole)
        if model_value != item_value:
            self._prop_items[property_key].setData(VAL_COL, Qt.EditRole, model_value)
    # end def
# end class
