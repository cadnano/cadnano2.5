from collections import defaultdict

from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from .customtreewidgetitems import PropertyItem, SelectionItem

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

KEY_COL = 0
VAL_COL = 1

class DnaPartItem(PropertyItem):
    def __init__(self, model_part, parent=None):
        super(PropertyItem, self).__init__(parent)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        root = parent.invisibleRootItem() # add propertyitems as siblings

        # Properties
        self._props = defaultdict(dict)
        self._model_props = m_p.getPropertyDict()
        for key in sorted(self._model_props):
            if key == "name": # name on top
                p_i = self
            else:
                p_i = PropertyItem(m_p, key, root)
            self._props[key]["p_i"] = p_i
            p_i.setData(KEY_COL, Qt.EditRole, key)
            p_i.setData(VAL_COL, Qt.EditRole, self._model_props[key])

        # Selections
        self._selections_root = s_r = PropertyItem(m_p, None, root)
        s_r.setData(KEY_COL, Qt.EditRole, "selections")
        s_r.setExpanded(True)

        self._selections = m_p.getSelectionDict()
        for key in sorted(self._selections):
            (start, end) = self._selections[key]
            s_i = SelectionItem(m_p, key, start, end, self._selections_root)
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
            p_i = self._props[property_key]["p_i"]
            value = p_i.data(VAL_COL, Qt.DisplayRole)
            if value != new_value:
                p_i.setData(VAL_COL, Qt.EditRole, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def part(self):
        return self._model_part
    # end def
# end class
