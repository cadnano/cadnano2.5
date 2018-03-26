# -*- coding: utf-8 -*-
from cadnano.extras.wrapapi import copyWrapAPI
from cadnano.part.virtualhelix import VirtualHelix
from cadnano.cntypes import (
                            KeyT,
                            ValueT,
                            NucleicAcidPartT
)

class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def __init__(self, id_num: int, part_item):
        # super().__init__(**kwargs)
        self._id_num: int = id_num
        self._part_item = part_item
        self._model_part: NucleicAcidPartT = part_item.part() if part_item is not None else None
        self.is_active: bool = False
    # end def

    def __repr__(self):
        _id = str(id(self))[-4:]
        _name  = self.__class__.__name__
        return '%s_%s_%s' % (_name, self._id_num, _id)
    # end def

    @property
    def editable_properties(self):
        return self._model_part.vh_editable_properties

    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    # end def

    def virtualHelixRemovedSlot(self):
        pass
    # end def

    def strandAddedSlot(self, sender, strand):
        pass
    # end def

    def cnModel(self) -> NucleicAcidPartT:
        return self._model_part
    # end def

    def part(self) -> NucleicAcidPartT:
        return self._model_part
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def idNum(self) -> int:
        return self._id_num

    def getProperties(self, keys: KeyT) -> ValueT:
        return self._model_part.getVirtualHelixProperties(self._id_num, keys)
    # end def

    def setProperties(self, keys, values, id_nums=None):
        part = self._model_part
        if id_nums is not None:
            part.setVirtualHelixProperties(id_nums, keys, values)
        else:
            return part.setVirtualHelixProperties(self._id_num, keys, values)
    # end def

    def getName(self):
        return self._model_part.getVirtualHelixProperties(self._id_num, 'name')
    # end def

    def getColor(self):
        return self._model_part.getVirtualHelixProperties(self._id_num, 'color')
    # end def

    def fwdStrand(self, idx):
        self._model_part.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx):
        self._model_part.rev_strandsets[self._id_num].getStrand(idx)
    # end def

    def getAxisPoint(self, idx):
        return self._model_part.getCoordinate(self._id_num, idx)
    # end def

# end class


# ADD model methods to class
# copyWrapAPI(VirtualHelix, AbstractVirtualHelixItem, attr_str='_model_vh')
