# -*- coding: utf-8 -*-
"""Summary
"""
from typing import Any

from cadnano.proxies.cnenum import (
    ItemEnum,
    EnumType
)
from cadnano.controllers import OligoItemController
from cadnano.views.abstractitems import AbstractOligoItem
from .cnpropertyitem import CNPropertyItem
from cadnano.cntypes import (
    OligoT
)


class OligoSetItem(AbstractOligoItem, CNPropertyItem):
    """Property View Oligo Set Item
    """
    _GROUPNAME = "oligos"
    FILTER_NAME = 'oligo'

    def __init__(self, **kwargs):
        """
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

    def itemType(self) -> EnumType:
        """
        Returns:
            ItemEnum.OLIGO
        """
        return ItemEnum.OLIGO
    # end def

    def oligoPropertyChangedSlot(self, model_oligo: OligoT, key: str, new_value: Any):
        """
        Args:
            model_oligo: Description
            key: Description
            new_value: Description
        """
        if model_oligo in self.outlineViewObjList():
            # print("prop: oligoPropertyChangedSlot", model_oligo, key, new_value)
            # self.setValue(key, new_value)
            displayed_val = self.getItemValue(key)
            if displayed_val != new_value:
                self.setValue(key, new_value)
    # end def
# end class
