# -*- coding: utf-8 -*-
import os

from cadnano import app

from cadnano.cntypes import (
    DocT
)

class DocumentController(object):
    '''Connects UI buttons to their corresponding actions in the model.'''
    '''list: String names of enabled filter types.'''

    ### INIT METHODS ###

    def __init__(self, document_item, document: DocT):
        ''''''
        # initialize variables
        self._document_item = document_item
        self._document = document
        self._document.setController(self)

        self.self_signals = []

        # call other init methods
        # app().document_controllers.add(self)
    # end def

    def connectSignals(self):
        doc = self._document
        d_i = self._document_item
        for signal, slot in self.connections:
            getattr(doc, signal).connect(getattr(d_i, slot))
    # end def

    def disconnectSignals(self):
        doc = self._document
        d_i = self._document_item
        for signal, slot in self.connections:
            getattr(doc, signal).disconnect(getattr(d_i, slot))
    # end def

