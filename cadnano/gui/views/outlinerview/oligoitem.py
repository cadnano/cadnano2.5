from cadnano.cnenum import ItemType

from .cnoutlineritem import (CNOutlinerItem, NAME_COL,
                            VISIBLE_COL, COLOR_COL, LEAF_FLAGS)
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController

class OutlineOligoItem(CNOutlinerItem, AbstractOligoItem):
    FILTER_NAME = "oligo"
    def __init__(self, model_oligo, parent):
        super(OutlineOligoItem, self).__init__(model_oligo, parent)
        self.setFlags(LEAF_FLAGS)
        self._controller = OligoItemController(self, model_oligo)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __repr__(self):
        return "OutlineOligoItem %s" % self._cn_model.getProperty('name')

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.OLIGO
    # end def

    def isModelSelected(self, document):
        """Make sure the item is selected in the model

        Args:
            document (Document): reference the the model :class:`Document`
        """
        oligo = self._cn_model
        return document.isOligoSelected(oligo)
    # end def

    ### SLOTS ###
    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        if self._cn_model == model_oligo:
            self.setValue(key, new_value)
    # end def
# end class
