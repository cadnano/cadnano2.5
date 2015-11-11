from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QLineEdit

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem

from .cnpropertyitem import CNPropertyItem

class VirtualHelixItem(CNPropertyItem, AbstractVirtualHelixItem):
    def __init__(self, model_virtual_helix, parent, key=None):
        super(VirtualHelixItem, self).__init__(model_virtual_helix, parent, key=key)
        if key is None:
            self._controller = VirtualHelixItemController(self, model_virtual_helix)
    # end def

    # SLOTS
    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        if self._cn_model == virtual_helix:
            self.setValue(property_key, new_value)

    def virtualHelixRemovedSlot(self, virtual_helix):
        self._cn_model = None
        self._controller.disconnectSignals()
        self._controller = None
        self.parent().removeChild(self)

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def configureEditor(self, parent_QWidget, option, model_index):
        m_vh = self._cn_model
        key = self.key()
        if key == 'name':
            editor = QLineEdit(parent_QWidget)
        elif key == 'eulerZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setDecimals(0)
            editor.setRange(0,359)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(m_vh.part().twistPerBase())
            editor.setDecimals(1)
            editor.setRange(0,359)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def
# end class
