#!/usr/bin/env python
# encoding: utf-8
from cadnano import util

from PyQt5.QtWidgets import QGraphicsPathItem

class AbstractDecoratorItem(QGraphicsPathItem):
    def __init__(self, parent):
        """The parent should be a VirtualHelixItem."""
        if self.__class__ == AbstractDecoratorItem:
            e = "AbstractDecoratorItem should be subclassed."
            raise NotImplementedError(e)
        super(AbstractDecoratorItem, self).__init__(parent)
        self._strand = None
        self._oligo = None

    ### SIGNALS ###

    ### SLOTS ###
    def strandResizedSlot(self):
        """docstring for strandResizedSlot"""
        pass

    def sequenceAddedSlot(self, oligo):
        """docstring for sequenceAddedSlot"""
        pass

    def decoratorRemovedSlot(self, oligo):
        """docstring for sequenceClearedSlot"""
        pass

    ### METHODS ###

    ### COMMANDS ###
