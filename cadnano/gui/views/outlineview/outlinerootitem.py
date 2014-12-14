from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .dnapartitem import DnaPartItem
from .origamipartitem import OrigamiPartItem
import cadnano.util as util

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QSizePolicy

class OutlineRootItem(QTreeWidget):
    """
    OutlineRootItem is the root item in the OutlineView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    OutlineRootItem must instantiate its own controller to receive signals
    from the model.
    """
    def __init__(self, parent, window, document):
        super(OutlineRootItem, self).__init__(parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()
        self.setCurrentItem(self._root)
        self._instance_items = {}
        self.setHeaderLabel("")

        sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMaximumWidth(150) # vertical

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.
        """
        part_type = model_part.__class__.__name__
        if part_type == "DnaPart":
            dna_part_item = DnaPartItem(model_part, parent=self)
            self.addTopLevelItem(dna_part_item)
            # self._instance_items[dna_part_item] = dna_part_item

        elif part_type in ["HoneycombPart", "SquarePart"]:
            origami_part_item = OrigamiPartItem(model_part, parent=self)
            self.addTopLevelItem(origami_part_item)
            # self._instance_items[origami_part_item] = origami_part_item
            # self.setModifyState(self._window.action_modify.isChecked())
        else:
            print(part_type)
            raise NotImplementedError
    # end def

    def clearSelectionsSlot(self, doc):
        pass
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot"""
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        pass
    # end def

    def resetRootItemSlot(self, doc):
        pass
    # end def

    ### ACCESSORS ###
    # def OutlineToolManager(self):
    #     """docstring for OutlineToolManager"""
    #     return self._window.OutlineToolManager
    # # end def

    def window(self):
        return self._window
    # end def

    ### METHODS ###
    def removeDnaPartItem(self, dna_part_item):
        index = self.indexOfTopLevelItem(dna_part_item)
        self.takeTopLevelItem(index)
        # del self._instance_items[dna_part_item]
    # end def

    def removeOrigamiPartItem(self, origami_part_item):
        index = self.indexOfTopLevelItem(origami_part_item)
        self.takeTopLevelItem(index)
        # del self._instance_items[origami_part_item]
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
