"""Summary
"""
from cadnano.enum import ItemType
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from .abstractproppartitem import AbstractPropertyPartItem

KEY_COL = 0
VAL_COL = 1


class NucleicAcidPartItem(AbstractPropertyPartItem):
    """Summary
    """
    def __init__(self, model_part, parent, key=None):
        """Summary

        Args:
            model_part (TYPE): Description
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(NucleicAcidPartItem, self).__init__(model_part, parent, key=key)
        if key is None:
            self._controller = NucleicAcidPartItemController(self, model_part)
    # end def

    def itemType(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return ItemType.NUCLEICACID
    # end def
# end class
