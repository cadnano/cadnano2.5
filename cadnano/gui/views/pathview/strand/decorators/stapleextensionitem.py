#!/usr/bin/env python
# encoding: utf-8


from exceptions import NotImplementedError
from cadnano import util
from .abstractdecoratoritem import AbstractDecoratorItem

class StapleExtensionItem(AbstractDecoratorItem):
    def __init__(self, parent):
        """The parent should be a VirtualHelixItem."""
        super(StapleExtensionItem, self).__init__(parent)

    ### SIGNALS ###

    ### SLOTS ###

    ### METHODS ###

    ### COMMANDS ###
