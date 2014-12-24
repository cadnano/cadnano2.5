from cadnano.gui.controllers.itemcontrollers.dnapartitemcontroller import DnaPartItemController

import cadnano.util as util

from .customtreewidgetitem import CustomTreeWidgetItem

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy


class DnaPartItem(CustomTreeWidgetItem):
    def __init__(self, model_part, parent=None):
        super(CustomTreeWidgetItem, self).__init__(parent)
        self._part = m_p = model_part
        self._parent_tree = parent
        self._controller = DnaPartItemController(self, model_part)

        root = parent.invisibleRootItem() # add propertyitems as siblings

        # Properties
        self._properties = m_p.getPropertyDict()
        for key in sorted(self._properties):
            if key == "name": # name goes on top
                p_i = self
            else:
                p_i = CustomTreeWidgetItem(root)
            p_i.setData(0, Qt.EditRole, key)
            p_i.setData(1, Qt.EditRole, self._properties[key])

        # Selections
        self._selections_root = s_r = CustomTreeWidgetItem(root)
        s_r.setData(0, Qt.EditRole, "Selections")
        s_r.setExpanded(True)

        self._selections = m_p.getSelectionDict()
        for key in sorted(self._selections):
            (start, end) = self._selections[key]
            s_i = CustomTreeWidgetItem(self._selections_root)
            s_i.setData(0, Qt.EditRole, "name")
            s_i.setData(1, Qt.EditRole, key)
            start_i = CustomTreeWidgetItem(s_i)
            start_i.setData(0, Qt.EditRole, "start")
            start_i.setData(1, Qt.EditRole, start)
            end_i = CustomTreeWidgetItem(s_i)
            end_i.setData(0, Qt.EditRole, "end")
            end_i.setData(1, Qt.EditRole, end)
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
