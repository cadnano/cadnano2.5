from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .partitem import PartItem
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QGraphicsRectItem

class SliceRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
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
        part_item = PartItem(model_part, parent=self)
        self._instance_items[part_item] = part_item
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
    def removePartItem(self, part_item):
        del self._instance_items[part_item]
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
        for part_item in self._instance_items:
            part_item.setModifyState(bool)
    # end def
