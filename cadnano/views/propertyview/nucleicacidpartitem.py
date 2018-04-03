# -*- coding: utf-8 -*-
"""Summary
"""
from cadnano.proxies.cnenum import ItemEnum
from cadnano.controllers import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartSetItem

KEY_COL = 0
VAL_COL = 1


class NucleicAcidPartSetItem(AbstractPropertyPartSetItem):
    """NucleicAcidPartItem for the PropertyView.
    """

    def __init__(self, **kwargs):
        """Summary

        Args:
            model_part (Part): The model part
            parent (PropertyEditorWidget): The property editor
            key (None, optional): Description
        """
        super(NucleicAcidPartSetItem, self).__init__(**kwargs)
        if self._key == "name":
            for outline_part in self.outlineViewObjList():
                model_part = outline_part.part()
                self._controller_list.append(NucleicAcidPartItemController(self, model_part))

    # end def

    def itemType(self):
        """Overrides AbstractPropertyPartItem method for NucleicAcidPartItem.

        Returns:
            ItemEnum: NUCLEICACID
        """
        return ItemEnum.NUCLEICACID
    # end def
# end class
