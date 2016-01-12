class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def virtualHelixNumberChangedSlot(self, virtual_helix, number):
        pass
    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    def virtualHelixRemovedSlot(self, virtual_helix):
        pass
    def strandAddedSlot(self, sender, strand):
        pass

    def getProperty(self, keys):
        return self._model_part.virtualHelixGroup().getProperties(self._id_num, keys)
    # end def

    def setProperty(self, keys, values):
        return self._model_part.virtualHelixGroup().setProperties(self._id_num, keys, values)
    # end def

    def fwdStrand(self, idx):
        self._model_part.virtualHelixGroup().fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx):
        self._model_part.virtualHelixGroup().rev_strandsets[self._id_num].getStrand(idx)
    # end def
# end class


