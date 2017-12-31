from cadnano.extras.wrapapi import copyWrapAPI
from cadnano.strand.strand import Strand


class AbstractStrandItem(object):
    def __init__(self, model_strand=None, parent=None):
        """The parent should be a VirtualHelixItem."""
        if self.__class__ == AbstractStrandItem:
            raise NotImplementedError("AbstractStrandItem should be subclassed.")
        super(AbstractStrandItem, self).__init__(parent)
        self._model_strand = model_strand
        self._oligo = None

    ### SIGNALS ###

    # ### SLOTS ###
    # def oligoAppeareanceChanged(self):
    #     """docstring for oligoAppeareanceChanged"""
    #     pass

    # def hasNewOligoSlot(self, oligo):
    #     """docstring for hasNewOligoSlot"""
    #     self._oligo = oligo
    #     # redraw

    # def strandRemovedSlot(self, strand):
    #     """docstring for strandRemovedSlot"""
    #     pass


# Add model methods to class
copyWrapAPI(Strand, AbstractStrandItem, attr_str='_model_strand')
