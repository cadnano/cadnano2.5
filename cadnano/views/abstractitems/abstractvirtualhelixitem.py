# -*- coding: utf-8 -*-
from typing import List, Tuple
import numpy as np

# from cadnano.extras.wrapapi import copyWrapAPI
from cadnano.part.virtualhelix import VirtualHelix
from cadnano.cntypes import (
                            KeyT,
                            ValueT,
                            NucleicAcidPartT,
                            StrandSetT,
                            StrandT
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

    def part(self) -> NucleicAcidPartT:
        return self._model_part
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def idNum(self) -> int:
        return self._id_num

    def getProperty(self, keys: KeyT) -> ValueT:
        return self._model_part.getVirtualHelixProperties(self._id_num, keys)
    # end def

    def setProperty(self, keys: KeyT, values: ValueT, id_nums=None):
        part = self._model_part
        if id_nums is not None:
            part.setVirtualHelixProperties(id_nums, keys, values)
        else:
            return part.setVirtualHelixProperties(self._id_num, keys, values)
    # end def

    def getModelProperties(self) -> dict:
        '''Used in Propert View
        '''
        return self._model_part.getAllVirtualHelixProperties(self._id_num)
    # end def

    def getSize(self) -> int:
        offset, size = self._model_part.getOffsetAndSize(self._id_num)
        return int(size)
    # end def

    def setSize(self, new_size: int, id_nums: List[int] = None):
        if id_nums:
            for id_num in id_nums:
                self._model_part.setVirtualHelixSize(id_num, new_size)
        else:
            self._model_part.setVirtualHelixSize(self._id_num, new_size)
    # end def

    def getName(self) -> str:
        return self._model_part.getVirtualHelixProperties(self._id_num, 'name')
    # end def

    def getColor(self) -> str:
        return self._model_part.getVirtualHelixProperties(self._id_num, 'color')
    # end def

    def fwdStrand(self, idx: int) -> StrandT:
        self._model_part.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx: int) -> StrandT:
        self._model_part.rev_strandsets[self._id_num].getStrand(idx)
    # end def

    def getAxisPoint(self, idx: int) -> np.ndarray:
        return self._model_part.getCoordinate(self._id_num, idx)
    # end def

    def getTwistPerBase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple: twist per base in degrees, eulerZ
        """
        bpr, tpr, eulerZ = self._model_part.getVirtualHelixProperties(self._id_num,
                                                                ['bases_per_repeat', 'turns_per_repeat', 'eulerZ'])
        return tpr*360./bpr, eulerZ
    # end def

    def getAngularProperties(self) -> Tuple[float, float, float, float]:
        """
        Returns:
            Tuple of the form::

                ('bases_per_repeat, 'bases_per_turn',
                    'twist_per_base', 'minor_groove_angle')
        """
        bpr, tpr, mga = self._model_part.getVirtualHelixProperties(self._id_num,
                                                             ['bases_per_repeat', 'turns_per_repeat', 'minor_groove_angle'])
        bases_per_turn = bpr / tpr
        return bpr, bases_per_turn, tpr*360./bpr, mga
    # end def


    def setZ(self, new_z: float, id_nums: List[int] = None):
        m_p = self._model_part
        if id_nums is None:
            id_nums = [self._id_num]

        for id_num in id_nums:
            old_z = m_p.getVirtualHelixProperties(id_num, 'z')
            if new_z != old_z:
                dz = new_z - old_z
                m_p.translateVirtualHelices([id_num], 0, 0, dz, finalize=False, use_undostack=True)
    # end def

    def getZ(self, id_num: int = None) -> float:
        """Get the 'z' property of the VirtualHelix described by ID number
        'id_num'.

        If a VirtualHelix corresponding to id_num does not exist, an IndexError
        will be thrown by getVirtualHelixProperties.
        """
        if __debug__:
            assert isinstance(id_num, int) or id_num is None

        return self._model_part.getVirtualHelixProperties(id_num if id_num is not None
                                                    else self._id_num, 'z')
    # end def



# end class


# ADD model methods to class
# copyWrapAPI(VirtualHelix, AbstractVirtualHelixItem, attr_str='_model_vh')
