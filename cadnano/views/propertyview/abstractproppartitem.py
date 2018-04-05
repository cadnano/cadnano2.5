# -*- coding: utf-8 -*-
from typing import Any

from cadnano.views.abstractitems import AbstractPartItem
from .cnpropertyitem import CNPropertyItem
from cadnano.cntypes import (
    PartT
)

class AbstractPropertyPartSetItem(CNPropertyItem, AbstractPartItem):
    """Summary
    """

    def __init__(self, **kwargs):
        """
        Args:
            model_part (Part): The model part
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(AbstractPropertyPartSetItem, self).__init__(**kwargs)
    # end def

    # SLOTS
    def partRemovedSlot(self, part: PartT):
        """
        Args:
            part: Model object that emitted the signal.
        """
        # self.parent.removePartItem(self)
        for controller in self._controller_list:
            controller.disconnectSignals()
        self._controller_list = []
    # end def

    def partPropertyChangedSlot(self, part: PartT, key: str, new_value: Any):
        """
        Args:
            part: The model part
            key: Description
            new_value: Description
        """
        if self.part() == part:
            self.setValue(key, new_value)
    # end def

    def partSelectedChangedSlot(self, part: PartT, is_selected: bool):
        """
        Args:
            part: The model part
            is_selected: Description
        """
        self.setSelected(is_selected)
    # end def
