
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

        # Scaffold
        self._scaf_twi = sc = QTreeWidgetItem(self, QTreeWidgetItem.UserType)
        sc.setData(0, Qt.EditRole, "Scaffold")
        sc.setData(1, Qt.EditRole, True)
        sc.setData(2, Qt.EditRole, "#ffffff")

        # Staples
        self._stap_twi = st = QTreeWidgetItem(self, QTreeWidgetItem.UserType)
        st.setData(0, Qt.EditRole, "Staples")
        st.setData(1, Qt.EditRole, True)
        st.setData(2, Qt.EditRole, "#ffffff")

        # mods
        self._mod_twi = m = QTreeWidgetItem(self, QTreeWidgetItem.UserType)
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

    def partOligoAddedSlot(self, part, oligo):
        print("outliner.origamipartitem oligo ADDED", oligo)
        oligo.oligoRemovedSignal.connect(self.oligoRemovedSlot)
    # end def

    def oligoRemovedSlot(self, oligo):
        print("outliner.origamipartitem oligo REMOVED", oligo)
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
