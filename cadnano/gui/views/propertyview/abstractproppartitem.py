"""Summary
"""
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from .cnpropertyitem import CNPropertyItem


class AbstractPropertyPartItem(CNPropertyItem, AbstractPartItem):
    """Summary
    """
    def __init__(self, model_part, parent, key=None):
        """Summary

        Args:
            model_part (Part): The model part
            parent (TYPE): Description
            key (None, optional): Description
        """
        super(AbstractPropertyPartItem, self).__init__(model_part, parent, key=key)
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
        self._cn_model = None
        self._controller.disconnectSignals()
        self._controller = None
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
        if self._cn_model == model_part:
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
