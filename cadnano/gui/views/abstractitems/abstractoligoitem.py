class AbstractOligoItem(object):
    """
    AbstractOligoItem is a base class for oligoitems in all views.
    It includes slots that get connected in OligoController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def oligoAppearanceChangedSlot(self, oligo):
        pass
    def oligoSequenceAddedSlot(self, oligo):
        pass
    def oligoSequenceClearedSlot(self, oligo):
        pass
# end class


