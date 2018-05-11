# -*- coding: utf-8 -*-
from typing import (
    Any
)

from cadnano.proxies.cnenum import (
    ItemEnum,
    EnumType
)
from .cnoutlineritem import (
    CNOutlinerItem,
    RootPartItem,
    LEAF_FLAGS
)
from cadnano.views.abstractitems import AbstractOligoItem
from cadnano.controllers import OligoItemController
from cadnano.cntypes import (
    OligoT,
    DocT
)

class OutlineOligoItem(CNOutlinerItem, AbstractOligoItem):
    FILTER_NAME = "oligo"

    def __init__(self, model_oligo: OligoT, parent: RootPartItem):
        super(OutlineOligoItem, self).__init__(model_oligo, parent)
        self._model_oligo = model_oligo
        self.setFlags(LEAF_FLAGS)
        self._controller = OligoItemController(self, model_oligo)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def __repr__(self) -> str:
        return "OutlineOligoItem %s" % self._cn_model.getProperty('name')

    ### PUBLIC SUPPORT METHODS ###
    def itemType(self) -> EnumType:
        return ItemEnum.OLIGO
    # end def

    def isModelSelected(self, document: DocT) -> bool:
        """Make sure the item is selected in the model

        Args:
            document: reference the the model :class:`Document`
        """
        oligo = self._cn_model
        return document.isOligoSelected(oligo)
    # end def

    ### SLOTS ###
    def oligoPropertyChangedSlot(self, oligo: OligoT, key: str, new_value: Any):
        if self._cn_model == oligo:
            self.setValue(key, new_value)
    # end def

    def oligoSelectedChangedSlot(self, oligo: OligoT, new_value: Any):
        if (self._cn_model == oligo and
            self.isSelected() != new_value):
            self.setSelected(new_value)
    # end def
# end class
