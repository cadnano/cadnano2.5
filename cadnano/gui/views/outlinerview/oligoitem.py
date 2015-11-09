
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.enum import ItemType
from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.views import styles
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController


NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class OligoItemDelegate(QStyledItemDelegate, AbstractOligoItem):
    def paint(self, painter, option, index):
        print("OligoItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

class OligoItem(QTreeWidgetItem, AbstractOligoItem):
    def __init__(self, model_part, model_oligo, parent):
        self._model_part = m_p = model_part
        self._model_oligo = m_o = model_oligo
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
        return self.model_part
    # end def

    def modelOligo(self):
        return self._model_oligo
    # end def

    def updateModel(self):
        # this works only for color. uncomment below to generalize to properties
        print("outliner oligoItem - updateModel")
        m_o = self._model_oligo
        name = self.data(NAME_COL, Qt.DisplayRole)
        color = self.data(COLOR_COL, Qt.DisplayRole)
        model_props = m_o.getPropertyDict()
        if name != model_props['name']:
            m_o.setProperty('name', name)
        if color != model_props['color']:
            m_o.setProperty('color', color)
    # end def

    ### SLOTS ###
    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        if key == 'name':
            self.setData(NAME_COL, Qt.EditRole, new_value)
        elif key == 'color': 
            self.setData(COLOR_COL, Qt.EditRole, new_value)
    # end def

    def oligoAppearanceChangedSlot(self, model_oligo):
        color = model_oligo.color()
        displayed_color = self.data(COLOR_COL, Qt.DisplayRole)
        if displayed_color != color:
            self.setData(COLOR_COL, Qt.EditRole, color)
    # end def
   

# end class
