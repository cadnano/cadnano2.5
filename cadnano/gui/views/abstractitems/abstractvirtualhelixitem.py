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

    def virtualHelixNumberChangedSlot(self, virtual_helix, number):
        pass
    def virtualHelixPropertyChangedSlot(self, virtual_helix, transform):
        pass
    def virtualHelixRemovedSlot(self):
        pass
    def strandAddedSlot(self, sender, strand):
        pass

    def setSelected(self, is_selected):
        pass
    # end def

    def getProperty(self, keys):
        return self._model_part.getVirtualHelixProperties(self._id_num, keys)
    # end def

    def getAllProperties(self):
        return self._model_part.getAllVirtualHelixProperties(self._id_num)
    # end def

    def setProperty(self, keys, values):
        return self._model_part.setVirtualHelixProperties(self._id_num, keys, values)
    # end def

    def getAxisPoint(self, idx):
        return self._model_part.getCoordinate(self._id_num, idx)
    # end def

    def getOtherAxisPoint(self, id_num, idx):
        return self._model_part.getCoordinate(id_num, idx)
    # end def

    def getSize(self):
        offset, size = self._model_part.getOffsetAndSize(self._id_num)
        return size
    # end def

    def part(self):
        return self._model_part
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def isActive(self):
        return self._model_part.isVirtualHelixActive(self._id_num)
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def fwdStrand(self, idx):
        self._model_part.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx):
        self._model_part.rev_strandsets[self._id_num].getStrand(idx)
    # end def
# end class


