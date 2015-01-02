
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.enum import ItemType
from cadnano.gui.views import styles
from cadnano.gui.views.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController


NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class OligoItemDelegate(QStyledItemDelegate, AbstractPartItem):
    def paint(self, painter, option, index):
        print("OligoItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

class OligoItem(QTreeWidgetItem, AbstractPartItem):
    def __init__(self, model_part, model_oligo, parent_dict):
        self._model_part = m_p = model_part
        self._model_oligo = m_o = model_oligo
        if m_o.isStaple():
            parent = parent_dict["Staples"]
        else:
            parent = parent_dict["Scaffolds"]
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)

        self._controller = OligoItemController(self, model_oligo)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        name = "oligo%s" % str(id(m_o))[-4:]
        color = m_o.color()
        self.setData(0, Qt.EditRole, name)
        self.setData(1, Qt.EditRole, True) # is_visible
        self.setData(2, Qt.EditRole, color)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.OLIGO
    # end def

    def part(self):
        return self._model_oligo
    # end def

    def updateModel(self):
        # find what changed
        for p in self._props:
            col = self._props[p]["column"]
            v = self.data(col, Qt.DisplayRole)
            m_v = self._model_oligo.getProperty(p)
            if v != m_v:
                self._model_oligo.setProperty(p, v)
    # end def

    ### SLOTS ###
    def oligoAppearanceChangedSlot(self):
        pass
    # end def
    
    def oligoSequenceAddedSlot(self):
        pass
    # end def
    
    def oligoSequenceClearedSlot(self):
        pass
    # end def
# end class
