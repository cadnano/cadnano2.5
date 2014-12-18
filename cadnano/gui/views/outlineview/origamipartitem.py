from cadnano.gui.controllers.itemcontrollers.origamipartitemcontroller import OrigamiPartItemController

import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate


ORIGAMI_ITEM_TYPE = 1200
SCAF_ITEM_TYPE = 1210
STAP_ITEM_TYPE = 1220
MOD_ITEM_TYPE = 1230


class OrigamiPartItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        print("OrigamiPartItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

class OrigamiPartItem(QTreeWidgetItem):
    def __init__(self, model_part, parent):
        super(QTreeWidgetItem, self).__init__(parent, ORIGAMI_ITEM_TYPE)
        self._part = model_part
        self._parent_tree = parent
        self._controller = OrigamiPartItemController(self, model_part)
        self.setFlags(self.flags() | Qt.ItemIsEditable)

        # Part
        self._part_name = "%s%d" % (model_part.__class__.__name__,\
                                    parent.getInstanceCount())
        self._visible = True
        self._color = "#cc6600"
        self.setData(0, Qt.EditRole, self._part_name)
        self.setData(1, Qt.EditRole, self._visible)
        self.setData(2, Qt.EditRole, self._color)

        # Scaffold
        self._scaf_twi = sc = QTreeWidgetItem(self, SCAF_ITEM_TYPE)
        sc.setData(0, Qt.EditRole, "Scaffold")
        sc.setData(1, Qt.EditRole, True)
        sc.setData(2, Qt.EditRole, "#ffffff")

        # Staples
        self._stap_twi = st = QTreeWidgetItem(self, STAP_ITEM_TYPE)
        st.setData(0, Qt.EditRole, "Staples")
        st.setData(1, Qt.EditRole, True)
        st.setData(2, Qt.EditRole, "#ffffff")

        # mods
        self._mod_twi = m = QTreeWidgetItem(self, MOD_ITEM_TYPE)
        m.setData(0, Qt.EditRole, "Modifications")
        m.setData(1, Qt.EditRole, True)
        m.setData(2, Qt.EditRole, "#ffffff")

        self.setExpanded(True)
    # end def

    def partRemovedSlot(self, sender):
        self._parent_tree.removeOrigamiPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partDimensionsChangedSlot(self, sender):
        pass
    # end def

    def partParentChangedSlot(self, sender):
        pass
    # end def

    def partPreDecoratorSelectedSlot(self, sender):
        pass
    # end def

    def updatePreXoverItemsSlot(self, sender):
        pass
    # end def

    def partVirtualHelixAddedSlot(self, sender):
        pass
    # end def

    def partVirtualHelixRenumberedSlot(self, sender):
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender):
        pass
    # end def

    def partVirtualHelicesReorderedSlot(self, sender):
        pass
    # end def
# end class
