from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QGraphicsRectItem

from cadnano import util
from cadnano.enum import PartType
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .nucleicacidpartitem import NucleicAcidPartItem


class SliceRootItem(QGraphicsRectItem):
    """
    SliceRootItem is the root item in the SliceView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    SliceRootItem must instantiate its own controller to receive signals
    from the model.
    """
    name = 'slice'

    def __init__(self, rect, parent, window, document):
        super(SliceRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._instance_items = {}
        self.manager = None
        self.select_tool = None
    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.
        """
        part_type = model_part_instance.reference().partType()
        if part_type == PartType.NUCLEICACIDPART:
            na_part_item = NucleicAcidPartItem(model_part_instance,
                viewroot=self,
                parent=self)
            self._instance_items[na_part_item] = na_part_item
            self.select_tool.setPartItem(na_part_item)
            na_part_item.zoomToFit()
        else:
            raise NotImplementedError
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot"""
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        # if 'virtual_helix' not in filter_name_list:
        #     self.manager.chooseCreateTool()
        pass
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        self.select_tool.deselectItems()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def resetRootItemSlot(self, doc):
        self.select_tool.deselectItems()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def sliceToolManager(self):
        """docstring for sliceToolManager"""
        return self._window.slice_tool_manager
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
        for nucleicacid_part_item in self._instance_items:
            nucleicacid_part_item.setModifyState(bool)
    # end def

    def setManager(self, manager):
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def
