from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem

from .abstractproppartitem import AbstractPropertyPartItem
from .customtreewidgetitems import PropertyItem, SelectionItem

KEY_COL = 0
VAL_COL = 1

class OligoItem(QTreeWidgetItem, AbstractOligoItem):
    def __init__(self, model_oligo, parent=None):
        super(OligoItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._controller = OligoItemController(self, model_oligo)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        self._model_oligo = m_o = model_oligo
        self._parent_tree = parent

        root = parent.invisibleRootItem() # add propertyitems as siblings

        # Properties
        self._prop_items = {}
        self._model_props = m_o.getPropertyDict()
        for key in sorted(self._model_props):
            if key == 'name': # name on top
                p_i = self
            else:
                p_i = PropertyItem(m_o, key, root)
            self._prop_items[key] = p_i
            p_i.setData(KEY_COL, Qt.EditRole, key)
            p_i.setData(VAL_COL, Qt.EditRole, self._model_props[key])

    def itemType(self):
        return ItemType.OLIGO
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        print("oligoPropertyChangedSlot", model_oligo, key, new_value)
        p_i = self._prop_items[key]
        displayed_value = p_i.data(VAL_COL, Qt.DisplayRole)
        if displayed_value != new_value:
            p_i.setData(VAL_COL, Qt.EditRole, new_value)
    # end def

    def oligoAppearanceChangedSlot(self, model_oligo):
        color = model_oligo.color()
        p_i = self._prop_items['color']
        displayed_color = p_i.data(VAL_COL, Qt.DisplayRole)
        if displayed_color != color:
            p_i.setData(VAL_COL, Qt.EditRole, color)
    # end def

    def updateModel(self):
        m_o = self._model_oligo
        name = self._prop_items['name'].data(VAL_COL, Qt.DisplayRole)
        color = self._prop_items['color'].data(VAL_COL, Qt.DisplayRole)
        model_props = m_o.getPropertyDict()
        if name != model_props['name']:
            m_o.setProperty('name', name)
        if color != model_props['color']:
            m_o.setProperty('color', color)
    # end def
# end class
