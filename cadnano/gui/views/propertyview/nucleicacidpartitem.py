from math import ceil

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QValidator, QIntValidator
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpinBox, QSlider

from cadnano import util
from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.views.customwidgets.stepwisespinbox import StepwiseSpinBox

from .cnpropertyitem import CNPropertyItem


class NucleicAcidPartItem(CNPropertyItem, AbstractPartItem):
    def __init__(self, model_part, parent, key=None):
        super(NucleicAcidPartItem, self).__init__(model_part, parent, key=key)
        if key is None:
            self._controller = NucleicAcidPartItemController(self, model_part)
    # end def

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self._cn_model = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._cn_model == model_part:
            self.setValue(property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        self.setSelected(is_selected)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _setCrossoverSpanAngle(self, new_value):
        self._cn_model.setProperty('crossover_span_angle', new_value)
    # end def

    ### PUBLIC METHODS ###
    def configureEditor(self, parent_QWidget, option, model_index):
        part = self._cn_model
        key = self.key()
        if key == 'crossover_span_angle':
            editor = QSlider(Qt.Horizontal, parent_QWidget)
            editor.setRange(5, 60)
            editor.valueChanged.connect(self._setCrossoverSpanAngle) # fire immediately
        elif key == 'max_vhelix_length':
            step_size = part.stepSize()
            editor = StepwiseSpinBox(step_size*2, 10000, step_size, parent_QWidget)
        else:
            editor = CNPropertyItem.configureEditor(self, parent_QWidget, option, model_index)
        return editor
    # end def

    def itemType(self):
        return ItemType.NUCLEICACID
    # end def
# end class
