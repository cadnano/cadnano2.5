"""Summary
"""
from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.oligoitemcontroller import OligoItemController
from cadnano.gui.views.abstractitems.abstractoligoitem import AbstractOligoItem
from .cnpropertyitem import CNPropertyItem
# from cadnano import util


class OligoItem(AbstractOligoItem, CNPropertyItem):
    """Summary
    """
    _GROUPNAME = "oligos"

    def __init__(self, cn_model_list, parent, key=None):
        """Summary

        Args:
            model_oligo (TYPE): Description
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(OligoItem, self).__init__(cn_model_list, parent, key=key)
        # print(util.trace(5), "in OligoItem init", cn_model_list)
        if key is None:
            for model_oligo in cn_model_list:
                self._controller_list.append(OligoItemController(self, model_oligo))
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
        if model_oligo in self._cn_model_list:
            # print("prop: oligoPropertyChangedSlot", model_oligo, key, new_value)
            # self.setValue(key, new_value)
            displayed_val = self.getItemValue(key)
            if displayed_val != new_value:
                self.setValue(key, new_value)
    # end def
# end class
