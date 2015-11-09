class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def virtualHelixNumberChangedSlot(self, virtual_helix, number):
        raise NotImplementedError
    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    def virtualHelixRemovedSlot(self, virtual_helix):
        raise NotImplementedError
    def strandAddedSlot(self, sender, strand):
        pass
# end class


