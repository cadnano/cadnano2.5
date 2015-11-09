from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.views import styles
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.plasmidpartitemcontroller import PlasmidPartItemController


NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class PlasmidPartItem(QTreeWidgetItem, AbstractPartItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = PlasmidPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.setExpanded(True)

        # properties
        self._props = defaultdict(dict)
        self._model_props = m_props = m_p.getPropertyDict()

        self._props["name"]["column"] = NAME_COL
        self._props["visible"]["column"] = VISIBLE_COL
        self._props["color"]["column"] = COLOR_COL

        for p in self._props:
            if p in m_props:
                self._props[p]["value"] = m_props[p]
            else:
                self._props[p]["value"] = "?"

        for p in self._props:
            col = self._props[p]["column"]
            value = self._props[p]["value"]
            self.setData(col, Qt.EditRole, value)

        # outlinerview takes responsibility of overriding default part color
        if self._props["color"]["value"] == "#000000":
            index = len(m_p.document().children())-1
            new_color = styles.PARTCOLORS[index % len(styles.PARTCOLORS)].name()
            self._model_part.setProperty("color", new_color)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removePartItem(self)
        self._model_part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            if property_key in self._props:
                col = self._props[property_key]["column"]
                value = self.data(col, Qt.DisplayRole)
                if value != new_value:
                    self.setData(col, Qt.EditRole, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.PLASMID
    # end def

    def part(self):
        return self._model_part
    # end def

    def updateModel(self):
        # find what changed
        for p in self._props:
            col = self._props[p]["column"]
            v = self.data(col, Qt.DisplayRole)
            m_v = self._model_part.getProperty(p)
            if v != m_v:
                self._model_part.setProperty(p, v)
    # end def

# end class
