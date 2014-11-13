from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .partitem import PartItem
from .pathselection import SelectionItemGroup
from .pathselection import VirtualHelixHandleSelectionBox
from .pathselection import EndpointHandleSelectionBox
import cadnano.util as util

from PyQt5.QtCore import QObject, pyqtSignal

from PyQt5.QtWidgets import QGraphicsRectItem

class PathRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and documentSelectedPartChangedSignal)
    via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
    from the model.
    """
    findChild = util.findChild  # for debug

    def __init__(self, rect, parent, window, document):
        super(PathRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._model_part = None
        self._part_item_for_part = {}  # Maps Part -> PartItem
        self._selection_filter_dict = {}
        self._initSelections()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partItems(self):
        "iterator"
        return self._part_item_for_part.values()

    def partItemForPart(self, part):
        return self._part_item_for_part[part]
    
    def partAddedSlot(self, sender, model_part):
        """
        Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.
        """
        # print "PathRootItem partAddedSlot", model_part
        self._model_part = model_part
        win = self._window
        part_item = PartItem(model_part,\
                            viewroot=self, \
                            active_tool_getter=win.path_tool_manager.activeToolGetter,\
                            parent=self)
        self._part_item_for_part[model_part] = part_item
        win.path_tool_manager.setActivePart(part_item)
        self.setModifyState(win.action_modify.isChecked())
    # end def

    def selectedChangedSlot(self, itemDict):
        """Given a newly selected model_part, update the scene to indicate
        that model_part is selected and the previously selected part is
        deselected."""
        for item, value in itemDict:
            item.selectionProcess(value)
    # end def

    def clearSelectionsSlot(self, doc):
        self._vhi_h_selection_group.resetSelection()
        self._strand_item_selection_group.resetSelection()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        self._vhi_h_selection_group.clearSelection(False)
        self._strand_item_selection_group.clearSelection(False)
        self.clearSelectionFilterDict()
        for filter_name in filter_name_list:
            self.addToSelectionFilterDict(filter_name)
    # end def

    def resetRootItemSlot(self, doc):
        self._vhi_h_selection_group.resetSelection()
        self._strand_item_selection_group.resetSelection()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def sliceToolManager(self):
        """
        Used for getting access to button signals that need to be connected
        to item slots.
        """
        return self._window.slice_tool_manager
    # end def

    def window(self):
        return self._window
    # end def

    def document(self):
        return self._document
    # end def

    def _initSelections(self):
        """Initialize anything related to multiple selection."""
        bType = VirtualHelixHandleSelectionBox
        self._vhi_h_selection_group = SelectionItemGroup(boxtype=bType,\
                                                      constraint='y',\
                                                      parent=self)
        bType = EndpointHandleSelectionBox
        self._strand_item_selection_group = SelectionItemGroup(boxtype=bType,\
                                                      constraint='x',\
                                                      parent=self)
    # end def

    ### PUBLIC METHODS ###
    def getSelectedPartOrderedVHList(self):
        """Used for encoding."""
        selectedPart = self._document.selectedPart()
        return self._part_item_for_part[selectedPart].getOrderedVirtualHelixList()
    # end def

    def removePartItem(self, part_item):
        for k in self._part_item_for_part.keys():
            if k == part_item:
                del self._part_item_for_part[k]
                return
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for part_item in self._part_item_for_part.values():
            part_item.setModifyState(bool)
    # end def

    def selectionFilterDict(self):
        return self._selection_filter_dict
    # end def

    def addToSelectionFilterDict(self, filter_name):
        self._selection_filter_dict[filter_name] = True
    # end def

    def removeFromSelectionFilterDict(self, filter_name):
        del self._selection_filter_dict[filter_name]
    # end def

    def clearSelectionFilterDict(self):
        self._selection_filter_dict = {}
    # end def

    def vhiHandleSelectionGroup(self):
        return self._vhi_h_selection_group
    # end def

    def strandItemSelectionGroup(self):
        return self._strand_item_selection_group
    # end def

    def selectionLock(self):
        return self.scene().views()[0].selectionLock()
    # end def

    def setSelectionLock(self, locker):
        self.scene().views()[0].setSelectionLock(locker)
    # end def

    def clearStrandSelections(self):
        self._strand_item_selection_group.clearSelection(False)
    # end def
# end class
