
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy, QStyledItemDelegate

from cadnano.enum import ItemType, PartType
from cadnano.gui.views import styles
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .oligoitem import OligoItem
from .virtualhelixitem import VirtualHelixItem

NAME_COL = 0
VISIBLE_COL = 1
COLOR_COL = 2

class NucleicAcidPartItemDelegate(QStyledItemDelegate, AbstractPartItem):
    def paint(self, painter, option, index):
        print("NucleicAcidPartItemDelegate")
        option.rect.adjust(-5,0,0,0)
        QItemDelegate.paint(painter, option, index)

class NucleicAcidPartItem(QTreeWidgetItem, AbstractPartItem):
    def __init__(self, model_part, parent):
        super(QTreeWidgetItem, self).__init__(parent, QTreeWidgetItem.UserType)
        self._model_part = m_p = model_part
        self._parent_tree = parent
        self._controller = NucleicAcidPartItemController(self, m_p)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.setExpanded(True)

        # properties
        self._props = defaultdict(dict)
        self._model_props = m_props = m_p.getPropertyDict()
        self._props['name']['column'] = NAME_COL
        self._props['visible']['column'] = VISIBLE_COL
        self._props['color']['column'] = COLOR_COL

        for p in self._props:
            if p in m_props:
                self._props[p]['value'] = m_props[p]
            else:
                self._props[p]['value'] = "?"
        for p in self._props:
            col = self._props[p]['column']
            value = self._props[p]['value']
            self.setData(col, Qt.EditRole, value)

        # outlinerview takes responsibility of overriding default part color
        if self._props['color']['value'] == "#000000":
            index = len(m_p.document().children()) - 1
            new_color = styles.PARTCOLORS[index % len(styles.PARTCOLORS)]
            self._model_part.setProperty('color', new_color)

        # item groups
        self._root_items = {}
        self._root_items['VHelixList'] = self._createRootItem('VHelixList', self)
        self._root_items['OligoList'] = self._createRootItem('OligoList', self)
        # self._root_items['Modifications'] = self._createRootItem('Modifications', self)
        self._items = {} # children
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _createRootItem(self, item_name, parent):
        twi = QTreeWidgetItem(parent, QTreeWidgetItem.UserType)
        twi.setData(0, Qt.EditRole, item_name)
        twi.setData(1, Qt.EditRole, True) # is_visible
        twi.setData(2, Qt.EditRole, "#ffffff") # color
        twi.setFlags(twi.flags() & ~Qt.ItemIsSelectable)
        twi.setExpanded(True)
        return twi

    ### PUBLIC SUPPORT METHODS ###
    def rootItems(self):
        return self._root_items
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def

    def part(self):
        return self._model_part
    # end def

    def updateModel(self):
        # find what changed
        for p in self._props:
            col = self._props[p]['column']
            v = self.data(col, Qt.DisplayRole)
            m_v = self._model_part.getProperty(p)
            if v != m_v:
                self._model_part.setProperty(p, v)
    # end def

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self._parent_tree.removeNucleicAcidPartItem(self)
        self._part = None
        self._parent_tree = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partOligoAddedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.connect(self.partOligoRemovedSlot)
        o_i = OligoItem(model_part, m_o, self._root_items['OligoList'])
        self._items[id(m_o)] = o_i
    # end def

    def partOligoRemovedSlot(self, model_part, model_oligo):
        m_o = model_oligo
        m_o.oligoRemovedSignal.disconnect(self.partOligoRemovedSlot)
        o_i = self._items[id(m_o)]
        o_i.parent().removeChild(o_i)
        del self._items[id(m_o)]

    # end def

    def partVirtualHelixAddedSlot(self, model_part, model_virtual_helix):
        m_vh = model_virtual_helix
        m_vh.virtualHelixRemovedSignal.connect(self.partVirtualHelixRemovedSlot)
        vh_i = VirtualHelixItem(model_part, m_vh, self._root_items['VHelixList'])
        self._items[id(m_vh)] = vh_i

    def partVirtualHelixRemovedSlot(self, model_part, model_virtual_helix):
        m_vh = model_virtual_helix
        vh_i = self._items[id(m_vh)]
        vh_i.parent().removeChild(vh_i)
        del self._items[id(m_vh)]
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            if property_key in self._props:
                col = self._props[property_key]['column']
                value = self.data(col, Qt.DisplayRole)
                if value != new_value:
                    self.setData(col, Qt.EditRole, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def
# end class
