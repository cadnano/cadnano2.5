from cadnano.proxies.cnenum import ItemType
# from .cnconsoleitem import (CNConsoleItem, LEAF_FLAGS)
from cadnano.views.abstractitems.abstractoligoitem import AbstractOligoItem
from cadnano.controllers.itemcontrollers.oligoitemcontroller import OligoItemController


class ConsoleOligoItem(AbstractOligoItem):
    FILTER_NAME = "oligo"

    def __init__(self, model_oligo, parent):
        super(ConsoleOligoItem, self).__init__(model_oligo, parent)
        self._controller = OligoItemController(self, model_oligo)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __repr__(self):
        return "ConsoleOligoItem %s" % self._cn_model.getProperty('name')

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
            print(model_oligo, "property changed:", key, new_value)
            # self.setValue(key, new_value)
    # end def
# end class
