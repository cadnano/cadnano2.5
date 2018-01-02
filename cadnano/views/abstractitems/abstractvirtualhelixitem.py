# -*- coding: utf-8 -*-
from cadnano.extras.wrapapi import copyWrapAPI
from cadnano.part.virtualhelix import VirtualHelix


class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def __init__(self, model_virtual_helix=None, parent=None):
        # super().__init__(**kwargs)
        self._model_vh = model_virtual_helix
        self._id_num = model_virtual_helix.idNum() if model_virtual_helix is not None else None
        self._part_item = parent
        self._model_part = model_virtual_helix.part() if model_virtual_helix is not None else None
        self.is_active = False
    # end def

    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    # end def

    def virtualHelixRemovedSlot(self):
        pass
    # end def

    def strandAddedSlot(self, sender, strand):
        pass
    # end def

    def cnModel(self):
        return self._model_vh
    # end def

    def partItem(self):
        return self._part_item
    # end def
# end class


# ADD model methods to class
copyWrapAPI(VirtualHelix, AbstractVirtualHelixItem, attr_str='_model_vh')
