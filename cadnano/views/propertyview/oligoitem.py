# -*- coding: utf-8 -*-
"""Summary
"""
from cadnano.proxies.cnenum import ItemEnum
from cadnano.controllers import OligoItemController
from cadnano.views.abstractitems import AbstractOligoItem
from .cnpropertyitem import CNPropertyItem
# from cadnano import util


class OligoSetItem(AbstractOligoItem, CNPropertyItem):
    """Summary
    """
    _GROUPNAME = "oligos"
    FILTER_NAME = 'oligo'

    def __init__(self, **kwargs):
        """Summary

        Args:
            model_oligo (TYPE): Description
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(OligoSetItem, self).__init__(**kwargs)
        # print(util.trace(5), "in OligoItem init", cn_model_list)
        if self._key == "name":
            for outline_oligo in self.outlineViewObjList():
                model_oligo = outline_oligo.oligo()
                self._controller_list.append(OligoItemController(self, model_oligo))
    # end def

    def itemType(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return ItemEnum.OLIGO
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
        if model_oligo in self.outlineViewObjList():
            # print("prop: oligoPropertyChangedSlot", model_oligo, key, new_value)
            # self.setValue(key, new_value)
            displayed_val = self.getItemValue(key)
            if displayed_val != new_value:
                self.setValue(key, new_value)
    # end def
# end class
