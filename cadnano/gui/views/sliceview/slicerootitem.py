from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .dnapartitem import DnaPartItem
from .origamipartitem import OrigamiPartItem
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QGraphicsRectItem

class SliceRootItem(QGraphicsRectItem):
    """
    SliceRootItem is the root item in the SliceView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    SliceRootItem must instantiate its own controller to receive signals
    from the model.
    """
    def __init__(self, rect, parent, window, document):
        super(SliceRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._instance_items = {}

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.
        """
        self._model_part = model_part

        if model_part.__class__.__name__ == "DnaPart":
            # print("yes DNApart")
            dna_part_item = DnaPartItem(model_part, parent=self)
            self._instance_items[dna_part_item] = dna_part_item
        else:
            # print("nope it's OrigamiPart")
            origami_part_item = OrigamiPartItem(model_part, parent=self)
            self._instance_items[origami_part_item] = origami_part_item
            self.setModifyState(self._window.action_modify.isChecked())
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot"""
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def resetRootItemSlot(self, doc):
        pass
    # end def

    ### ACCESSORS ###
    def sliceToolManager(self):
        """docstring for sliceToolManager"""
        return self._window.sliceToolManager
    # end def

    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def removeDnaPartItem(self, dna_part_item):
        del self._instance_items[dna_part_item]
    # end def

    def removeOrigamiPartItem(self, origami_part_item):
        del self._instance_items[origami_part_item]
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self._instance_items) > 0:
            raise ImportError
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for origami_part_item in self._instance_items:
            origami_part_item.setModifyState(bool)
    # end def
