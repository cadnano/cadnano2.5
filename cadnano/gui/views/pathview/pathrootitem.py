from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGraphicsRectItem

from cadnano import util
from cadnano.enum import PartType
from cadnano.gui.controllers.viewrootcontroller import ViewRootController

from .origamipartitem import OrigamiPartItem
from .pathselection import EndpointHandleSelectionBox
from .pathselection import SelectionItemGroup
from .pathselection import VirtualHelixHandleSelectionBox


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
        self._part_item_for_part_instance = {}  # Maps Part -> PartItem
        self._selection_filter_dict = {}
        self._initSelections()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partItems(self):
        "iterator"
        return self._part_item_for_part_instance.values()

    def partItemForPart(self, part):
        return self._part_item_for_part_instance[part]

    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.
        """
        win = self._window
        part_type = model_part_instance.object().partType()

        if part_type == PartType.PLASMIDPART:
            pass
            # plasmid_part_item = PlasmidPartItem(model_part_instance, parent=self)
            # self._instance_items[plasmid_part_item] = plasmid_part_item
        elif part_type == PartType.ORIGAMIPART:
            origami_part_item = OrigamiPartItem(model_part_instance,\
                                viewroot=self, \
                                active_tool_getter=win.path_tool_manager.activeToolGetter,\
                                parent=self)
            self._part_item_for_part_instance[model_part_instance] = origami_part_item
            win.path_tool_manager.setActivePart(origami_part_item)
            self.setModifyState(win.action_modify.isChecked())
        else:
            raise NotImplementedError
    # end def

    def selectedChangedSlot(self, item_dict):
        """Given a newly selected model_part, update the scene to indicate
        that model_part is selected and the previously selected part is
        deselected."""
        for item, value in item_dict:
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
        b_type = VirtualHelixHandleSelectionBox
        self._vhi_h_selection_group = SelectionItemGroup(boxtype=b_type,\
                                                      constraint='y',\
                                                      parent=self)
        b_type = EndpointHandleSelectionBox
        self._strand_item_selection_group = SelectionItemGroup(boxtype=b_type,\
                                                      constraint='x',\
                                                      parent=self)
    # end def

    ### PUBLIC METHODS ###
    def getSelectedInstanceOrderedVHList(self):
        """Used for encoding."""
        selected_instance = self._document.selectedInstance()
        return self._part_item_for_part_instance[selected_instance].getOrderedVirtualHelixList()
    # end def

    def removeOrigamiPartItem(self, part_item):
        for k in self._part_item_for_part_instance.keys():
            if k == part_item:
                del self._part_item_for_part_instance[k]
                return
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController"""
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState"""
        for part_item in self._part_item_for_part_instance.values():
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
