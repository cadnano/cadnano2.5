from cadnano.enum import ItemType

from .cnoutlineritem import CNOutlinerItem
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController

class VirtualHelixItem(CNOutlinerItem, AbstractVirtualHelixItem):
    def __init__(self, model_virtual_helix, parent):
        super(VirtualHelixItem, self).__init__(model_virtual_helix, parent)
        self._controller = VirtualHelixItemController(self, model_virtual_helix)
        self._model_virtual_helix = model_virtual_helix
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    ### SLOTS ###
    def virtualHelixPropertyChangedSlot(self, model_vh, property_key, new_value):
        if property_key in CNOutlinerItem._PROPERTIES:
            self.setValue(property_key, new_value)
    # end def
# end class
