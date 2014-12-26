from collections import defaultdict

from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class DnaPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

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

        self.setExpanded(True)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removeDnaPartItem(self)
        self._model_part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partHideSlot(self):
        pass
    # end def

    def partDimensionsChangedSlot(self):
        pass
    # end def

    def partParentChangedSlot(self):
        pass
    # end def

    def partRemovedSlot(self):
        pass
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            col = self._props[property_key]["column"]
            value = self.data(col, Qt.DisplayRole)
            if value != new_value:
                self.setData(col, Qt.EditRole, new_value)
    # end def

    ### PUBLIC SUPPORT METHODS ###
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
