from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QLineEdit

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController

from .cnpropertyitem import CNPropertyItem

class VirtualHelixItem(CNPropertyItem):
    def __init__(self, id_num, model_part, parent, key=None):
        self._id_num = id_num
        self._model_part = model_part
        CNPropertyItem.__init__(self, model_part, parent=parent)
        if key is None:
            # different controller required for this
            self._controller = VirtualHelixItemController(self, model_part, True, False)
    # end def

    # SLOTS
    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, keys, values):
        if self._cn_model == sender and id_num == self._id_num:
            for key, val in zip(keys, values):
                self.setValue(key, val)

    def partVirtualHelixRemovedSlot(self, sender, id_num):
        if self._cn_model == sender and id_num == self._id_num:
            self.setValue(property_key, new_value)
            self._cn_model = None
            self._controller = None
            self.parent().removeChild(self)

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    def configureEditor(self, parent_QWidget, option, model_index):
        m_p = self._cn_model
        key = self.key()
        if key == 'name':
            editor = QLineEdit(parent_QWidget)
        # elif key == 'location':
        #     editor = QLineEdit(parent_QWidget)
        elif key == 'eulerZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setDecimals(0)
            editor.setRange(0,359)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(m_p.twistPerBase())
            editor.setDecimals(1)
            editor.setRange(0,359)
        elif key in ['ehiX', 'ehiY']:
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(5)
            editor.setDecimals(4)
            editor.setRange(0,1000)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def
# end class
