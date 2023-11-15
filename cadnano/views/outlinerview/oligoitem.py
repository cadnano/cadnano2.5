from cadnano.proxies.cnenum import ItemType
from .cnoutlineritem import (CNOutlinerItem, LEAF_FLAGS)
from cadnano.views.abstractitems.abstractoligoitem import AbstractOligoItem
from cadnano.controllers.oligoitemcontroller import OligoItemController


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

    def oligoSelectedChangedSlot(self, model_oligo, new_value):
        if (self._cn_model == model_oligo and
            self.isSelected() != new_value):
            self.setSelected(new_value)
    # end def
# end class
