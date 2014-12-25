from cadnano.gui.controllers.itemcontrollers.origamipartitemcontroller import OrigamiPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy


class OrigamiPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = OrigamiPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        self._property_items = []

        for key in sorted(self._properties):
            p_wi = QTreeWidgetItem(self, QTreeWidgetItem.UserType)
            p_wi.setData(0, Qt.EditRole, key)
            p_wi.setData(1, Qt.EditRole, self._properties[key])
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removeOrigamiPartItem(self)
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
    
    ### PUBLIC SUPPORT METHODS ###
    def part(self):
        return self._model_part
    # end def

# end class
