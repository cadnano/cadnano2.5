# -*- coding: utf-8 -*-
class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def __init__(self, model_virtual_helix, parent):
        self._model_vh = model_virtual_helix
        self._id_num = model_virtual_helix.idNum()
        self._part_item = parent
        self._model_part = model_virtual_helix.part()
        self.is_active = False

    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass

    def virtualHelixRemovedSlot(self):
        pass

    def strandAddedSlot(self, sender, strand):
        pass

    def setSelected(self, is_selected):
        pass
    # end def

    def cnModel(self):
        return self._model_vh
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def part(self):
        return self._model_part
    # end def

    def partItem(self):
        return self._part_item
    # end def
# end class
