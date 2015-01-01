class AbstractPartItem(object):
    """
    AbstractPartItem is a base class for partitems in all views.
    It includes slots that get connected in PartItemController which
    can be overridden.
    
    If you want to add a new signal to the model, adding the slot here
    means it's not necessary to add the same slot to every item across
    all views.
    """
    def partDimensionsChangedSlot(self, sender):
        pass
    def partOligoAddedSlot(self, part, oligo):
        pass
    def partParentChangedSlot(self, sender):
        pass
    def partPropertyChangedSlot(model_part, property_key, new_value):
        pass
    def partRemovedSlot(self, sender):
        pass
    def partSelectedChangedSlot(self, model_part, is_selected):
        pass

    def partActiveVirtualHelixChangedSlot(self, sender):
        pass
    # end def
    def partPreDecoratorSelectedSlot(self, sender):
        pass
    # end def
    def updatePreXoverItemsSlot(self, sender):
        pass
    # end def
    def partVirtualHelixAddedSlot(self, sender):
        pass
    # end def
    def partVirtualHelixRenumberedSlot(self, sender):
        pass
    # end def
    def partVirtualHelixResizedSlot(self, sender):
        pass
    # end def
    def partVirtualHelicesReorderedSlot(self, sender):
        pass
    # end def
# end class


