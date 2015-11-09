
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.enum import ItemType
from cadnano.gui.views import styles
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController


_PROPERTIES = {'name':0, 'is_visible': 1, 'color':2}

class VirtualHelixItem(QTreeWidgetItem, AbstractVirtualHelixItem):
    def __init__(self, model_part, model_vh, parent):
        self._model_part = m_p = model_part
        self._model_vh = m_vh = model_vh
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)

        self._controller = VirtualHelixItemController(self, model_vh)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        name = "vh%s" % str(m_vh.number())
        # color = m_p.color()
        self.setData(0, Qt.EditRole, name)
        self.setData(1, Qt.EditRole, True) # is_visible
        self.setData(2, Qt.EditRole, "#ffffff")
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def modelPart(self):
        return self._model_part
    # end def

    def modelVirtualHelix(self):
        return self._model_vh
    # end def

    def updateModel(self):
        for key, column in _PROPERTIES.iterItems():
            item_value = self.data(column, Qt.DisplayRole)
            model_value = self._model_vh.getProperty(key)
            if item_value != model_value:
                self._model_vh.setProperty(key, model_value)
    # end def

    def updateView(self):
        m_vh = self._model_virtual_helix
        for key, column in _PROPERTIES.iterItems():
            item_value = self.data(column, Qt.DisplayRole)
            model_value = self._model_virtual_helix.getProperty(key)
        if item_value != model_value:
            self.setData(column, Qt.EditRole, model_value)
    # end def

    def updateViewProperty(self, property_key):
        column = _PROPERTIES[property_key]
        item_value = self.data(column, Qt.DisplayRole)
        model_value = self._model_virtual_helix.getProperty(property_key)
        if item_value != model_value:
            self.setData(column, Qt.EditRole, model_value)
    # end def

    ### SLOTS ###
    def virtualHelixPropertyChangedSlot(self, model_vh, property_key, new_value):
        if self._model_vh == model_vh and property_key in _PROPERTIES:
            self.updateViewProperty(property_key)
    # end def
# end class
