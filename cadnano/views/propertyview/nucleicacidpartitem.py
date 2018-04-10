# -*- coding: utf-8 -*-
from cadnano.proxies.cnenum import (
    ItemEnum,
    EnumType
)
from cadnano.controllers import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartSetItem

KEY_COL = 0
VAL_COL = 1


class NucleicAcidPartSetItem(AbstractPropertyPartSetItem):
    """NucleicAcidPartItem for the PropertyView.
    """

    def __init__(self, **kwargs):
        """
        Args:
            model_part (NucleicAcidPart): The model part
            parent (PropertyEditorWidget): The property editor
            key (str, optional): Default is ``None``
        """
        self.part_set = set()
        super(NucleicAcidPartSetItem, self).__init__(**kwargs)
        if self._key == "name":
            for outline_part in self.outlineViewObjList():
                model_part = outline_part.part()
                self.part_set.add(model_part)
                self._controller_list.append(NucleicAcidPartItemController(self, model_part))

    # end def

    def cleanUp(self):
        self.part_set.clear()

    def itemType(self) -> EnumType:
        """Overrides AbstractPropertyPartItem method for NucleicAcidPartItem.

        Returns:
            ItemEnum: NUCLEICACID
        """
        return ItemEnum.NUCLEICACID
    # end def
# end class
