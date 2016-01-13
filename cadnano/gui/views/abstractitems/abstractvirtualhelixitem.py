class AbstractVirtualHelixItem(object):
    """
    AbstractVirtualHelixItem is a base class for virtualhelixitem in all views.
    It includes slots that get connected in VirtualHelixItemController which
    can be overridden.

    Slots that must be overridden should raise an exception.
    """
    def __init__(self, id_num, part_item):
        self._id_num = id_num
        self._part_item = part_item
        self._model_part = part_item.part()
        self._virtual_helix_group = self._model_part.virtualHelixGroup()

    def virtualHelixNumberChangedSlot(self, virtual_helix, number):
        pass
    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    def virtualHelixRemovedSlot(self, virtual_helix):
        pass
    def strandAddedSlot(self, sender, strand):
        pass

    def getProperty(self, keys):
        return self._virtual_helix_group.getProperties(self._id_num, keys)
    # end def

    def setProperty(self, keys, values):
        return self._virtual_helix_group.setProperties(self._id_num, keys, values)
    # end def

    def part(self):
        return self._model_part
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def fwdStrand(self, idx):
        self._virtual_helix_group.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx):
        self._virtual_helix_group.rev_strandsets[self._id_num].getStrand(idx)
    # end def
# end class


