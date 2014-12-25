from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy


class DnaPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._part = m_p = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        # Part
        if m_p.getProperty("name") is None:
            self._part_name = "Dna%d" % parent.getInstanceCount()
            m_p.setProperty("name", self._part_name)
        self._visible = True
        self._color = "#0066cc"
        self.setData(0, Qt.EditRole, self._part_name)
        self.setData(1, Qt.EditRole, self._visible)
        self.setData(2, Qt.EditRole, self._color)

        self.setExpanded(True)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        self._parent_tree.removeDnaPartItem(self)
        self._part = None
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
        return self._part
    # end def
# end class
