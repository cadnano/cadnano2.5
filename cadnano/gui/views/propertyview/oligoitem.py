from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QSizePolicy

from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem

from .cnpropertyitem import CNPropertyItem

class OligoItem(CNPropertyItem, AbstractOligoItem):
    def __init__(self, model_oligo, parent, key=None):
        super(OligoItem, self).__init__(model_oligo, parent, key=key)
        if key is None:
            self._controller = OligoItemController(self, model_oligo)
    # end def

    def itemType(self):
        return ItemType.OLIGO
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        if self._cn_model == model_oligo:
            print("prop: oligoPropertyChangedSlot", model_oligo, key, new_value)
            self.setValue(key, new_value)
    # end def

    def oligoAppearanceChangedSlot(self, model_oligo):
        print("prop: appearance changed")
        color = model_oligo.getColor()
        displayed_color = self.getItemValue('color')
        if displayed_color != color:
            self.setValue('color', color)
    # end def
# end class
