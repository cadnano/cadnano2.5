"""Summary
"""
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from .cnpropertyitem import CNPropertyItem


class AbstractPropertyPartSetItem(CNPropertyItem, AbstractPartItem):
    """Summary
    """
    def __init__(self, **kwargs):
        """Summary

        Args:
            model_part (Part): The model part
            parent (TYPE): Description
            key (None, optional): Description
        """
        super().__init__(**kwargs)
    # end def

    # SLOTS
    def partRemovedSlot(self, sender):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.

        Returns:
            TYPE: Description
        """
        # self.parent.removePartItem(self)
        for controller in self._controller_list:
            controller.disconnectSignals()
        self._controller_list = []
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        """Summary

        Args:
            model_part (Part): The model part
            property_key (TYPE): Description
            new_value (TYPE): Description

        Returns:
            TYPE: Description
        """
        if self.cnModel() == model_part:
            self.setValue(property_key, new_value)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        """Summary

        Args:
            model_part (Part): The model part
            is_selected (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.setSelected(is_selected)
    # end def
