"""Summary
"""
from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartSetItem

KEY_COL = 0
VAL_COL = 1


class NucleicAcidPartSetItem(AbstractPropertyPartSetItem):
    """NucleicAcidPartItem for the PropertyView.
    """
    def __init__(self, model_part_list, parent, key=None):
        """Summary

        Args:
            model_part (Part): The model part
            parent (PropertyEditorWidget): The property editor
            key (None, optional): Description
        """
        super(NucleicAcidPartSetItem, self).__init__(model_part_list, parent, key=key)
        if key is None:
            for model_part in model_part_list:
                self._controller_list.append(NucleicAcidPartItemController(self, model_part))

    # end def

    def itemType(self):
        """Overrides AbstractPropertyPartItem method for NucleicAcidPartItem.

        Returns:
            ItemType: NUCLEICACID
        """
        return ItemType.NUCLEICACID
    # end def
# end class
