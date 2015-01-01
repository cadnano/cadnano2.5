
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.gui.views import styles
from cadnano.gui.views.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.origamipartitemcontroller import OrigamiPartItemController


NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class OrigamiPartItemDelegate(QStyledItemDelegate, AbstractPartItem):
    def paint(self, painter, option, index):
        print("OrigamiPartItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

class OrigamiPartItem(QTreeWidgetItem, AbstractPartItem):
    def __init__(self, model_part, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = OrigamiPartItemController(self, model_part)
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
            index = len(m_p.document().children())
            new_color = styles.PARTCOLORS[index % len(styles.PARTCOLORS)].name()
            self._model_part.setProperty("color", new_color)

        # child items
        self._scaf_items = {}
        self._stap_items = {}
        self._mods_items = {}

        self._scaf_root = self._createItem("Scaffolds", True, "#ffffff", True, self)
        self._stap_root = self._createItem("Staples", True, "#ffffff", True, self)
        self._mods_root = self._createItem("Modifications", True, "#ffffff", True, self)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _createItem(self, item_name, is_visible, color, is_expanded, parent):
        twi = QTreeWidgetItem(parent, QTreeWidgetItem.UserType)
        twi.setData(0, Qt.EditRole, item_name)
        twi.setData(1, Qt.EditRole, is_visible)
        twi.setData(2, Qt.EditRole, color)
        twi.setExpanded(is_expanded)
        return twi

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self._parent_tree.removeOrigamiPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partOligoAddedSlot(self, part, oligo):
        print("partOligoAddedSlot", part, oligo, id(oligo))
        oligo.oligoRemovedSignal.connect(self.partOligoRemovedSlot)
        if oligo.isStaple():
            oi_name = "staple%d" % len(self._stap_items) # need a better numbering system
            oi_parent = self._stap_root
            oi_dict = self._stap_items
        else:
            oi_name = "scaf%d" % len(self._scaf_items)
            oi_parent = self._scaf_root
            oi_dict = self._scaf_items
        oi_color = oligo.color()
        oi = self._createItem(oi_name, True, oi_color, True, oi_parent)
        oi_dict[id(oligo)] = oi
    # end def

    def partOligoRemovedSlot(self, part, oligo):
        print("partOligoRemovedSlot", oligo, id(oligo))
        if oligo.isStaple():
            oi_parent = self._stap_root
            oi_dict = self._stap_items
        else:
            oi_parent = self._scaf_root
            oi_dict = self._scaf_items
        oi_parent.removeChild(oi_dict[id(oligo)])
        del oi_dict[id(oligo)]
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

# end class
