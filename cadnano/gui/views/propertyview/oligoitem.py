"""Summary
"""
from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem
from .cnpropertyitem import CNPropertyItem


class OligoItem(CNPropertyItem, AbstractOligoItem):
    """Summary
    """
    def __init__(self, model_oligo, parent, key=None):
        """Summary

        Args:
            model_oligo (TYPE): Description
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(OligoItem, self).__init__(model_oligo, parent, key=key)
        if key is None:
            self._controller = OligoItemController(self, model_oligo)
    # end def

    def itemType(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return ItemType.OLIGO
    # end def

    def oligoPropertyChangedSlot(self, model_oligo, key, new_value):
        """Summary

        Args:
            model_oligo (TYPE): Description
            key (TYPE): Description
            new_value (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self._cn_model == model_oligo:
            # print("prop: oligoPropertyChangedSlot", model_oligo, key, new_value)
            self.setValue(key, new_value)
            displayed_val = self.getItemValue(key)
            if displayed_val != new_value:
                self.setValue(key, new_value)
    # end def
# end class
