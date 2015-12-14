
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpinBox, QLineEdit
from PyQt5.QtWidgets import QDoubleSpinBox, QSlider

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.views.pathview import pathstyles

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

    ### PRIVATE SUPPORT METHODS ###
    def _setEulerZ(self, new_value):
        self._cn_model.setProperty('eulerZ', new_value)

    def _setZ(self, new_value):
        self._cn_model.setProperty('z', new_value)

    def _setBasesPerRepeat(self, new_value):
        self._cn_model.setProperty('bases_per_repeat', new_value)

    def _setRepeats(self, new_value):
        self._cn_model.setProperty('repeats', new_value)

    def _setTurnsPerRepeat(self, new_value):
        self._cn_model.setProperty('turns_per_repeat', new_value)

    def configureEditor(self, parent_QWidget, option, model_index):
        m_vh = self._cn_model
        key = self.key()
        if key == 'name':
            editor = QLineEdit(parent_QWidget)
        elif key == 'eulerZ':
            editor = QSlider(Qt.Horizontal, parent_QWidget)
            editor.setRange(0, 359)
            editor.valueChanged.connect(self._setEulerZ)
        elif key == 'scamZ':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(m_vh.part().twistPerBase())
            editor.setDecimals(1)
            editor.setRange(0,359)
        elif key in ['x', 'y']:
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(5)
            editor.setDecimals(4)
            editor.setRange(0,1000)
        elif key == 'z':
            editor = QDoubleSpinBox(parent_QWidget)
            editor.setSingleStep(pathstyles.PATH_BASE_WIDTH)
            editor.setDecimals(4)
            editor.setRange(-9999,9999)
            editor.valueChanged.connect(self._setZ)
        elif key == 'bases_per_repeat':
            editor = QSpinBox(parent_QWidget)
            editor.setRange(10,32)
            editor.valueChanged.connect(self._setBasesPerRepeat)
        elif key == 'turns_per_repeat':
            editor = QSpinBox(parent_QWidget)
            editor.setRange(1,3)
            editor.valueChanged.connect(self._setTurnsPerRepeat)
        elif key == 'repeats':
            editor = QSpinBox(parent_QWidget)
            editor.setRange(2,100)
            editor.valueChanged.connect(self._setRepeats)
        elif key == '_bases_per_turn':
            editor = QLineEdit(parent_QWidget)
            editor.setReadOnly(True)
        elif key == '_twist_per_base':
            editor = QLineEdit(parent_QWidget)
            editor.setReadOnly(True)
        elif key == '_max_length':
            editor = QLineEdit(parent_QWidget)
            editor.setReadOnly(True)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def
# end class
