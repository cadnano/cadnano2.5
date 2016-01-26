from cadnano.enum import ItemType

from .cnoutlineritem import CNOutlinerItem
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController

class OligoItem(CNOutlinerItem, AbstractOligoItem):
    _filter_name = "strand"
    def __init__(self, model_oligo, parent):
        super(OligoItem, self).__init__(model_oligo, parent)
        self._controller = OligoItemController(self, model_oligo)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.OLIGO
    # end def

    ### SLOTS ###
    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        if self._cn_model == model_oligo:
            self.setValue(key, new_value)
    # end def

    def oligoAppearanceChangedSlot(self, model_oligo):
        color = model_oligo.getColor()
        self.setValue('color', color)
    # end def


# end class
