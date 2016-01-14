from cadnano.enum import ItemType

from .cnoutlineritem import CNOutlinerItem
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController


class VirtualHelixItem(AbstractVirtualHelixItem, CNOutlinerItem):
    def __init__(self, id_num, part_item):
        # self._model_part = part_item.part()
        # self._id_num = id_num
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        CNOutlinerItem.__init__(self,  part_item.part(), parent=part_item)
        self._controller = VirtualHelixItemController(self, self._model_part, False, False)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self):
        return ItemType.VIRTUALHELIX
    # end def

    ### SLOTS ###
# end class
