
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.enum import ItemType
from cadnano.gui.views import styles
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController


NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class VirtualHelixItemDelegate(QStyledItemDelegate, AbstractVirtualHelixItem):
    def paint(self, painter, option, index):
        print("VirtualHelixItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

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
        # find what changed
        for p in self._props:
            col = self._props[p]["column"]
            v = self.data(col, Qt.DisplayRole)
            m_v = self._model_vh.getProperty(p)
            if v != m_v:
                self._model_vh.setProperty(p, v)
    # end def

    ### SLOTS ###
    def virtualHelixTransformChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            if property_key in self._props:
                col = self._props[property_key]["column"]
                value = self.data(col, Qt.DisplayRole)
                if value != new_value:
                    self.setData(col, Qt.EditRole, new_value)
    # end def

# end class
