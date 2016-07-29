from PyQt5.QtWidgets import QGraphicsRectItem
from cadnano import util
from cadnano.enum import PartType
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .nucleicacidpartitem import NucleicAcidPartItem


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
    name = 'path'

    def __init__(self, rect, parent, window, document):
        super(PathRootItem, self).__init__(rect, parent)
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._model_part = None
        self._part_item_for_part_instance = {}  # Maps Part -> PartItem
        self._prexover_filter = None
        self.manager = None
        self.select_tool = None
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
        part_type = model_part_instance.reference().partType()

        if part_type == PartType.PLASMIDPART:
            pass
        elif part_type == PartType.NUCLEICACIDPART:
            na_part_item = NucleicAcidPartItem(model_part_instance,
                                               viewroot=self,
                                               parent=self)
            self._part_item_for_part_instance[model_part_instance] = na_part_item
            win.path_tool_manager.setActivePart(na_part_item)
        else:
            raise NotImplementedError
    # end def

    def clearSelectionsSlot(self, doc):
        # print("yargh!!!!")
        self.select_tool.resetSelections()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def selectionFilterChangedSlot(self, filter_name_set):
        self.select_tool.clearSelections(False)
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        print("path updating preXovers", filter_name)
        self._prexover_filter = filter_name
    # end def

    def resetRootItemSlot(self, doc):
        self.select_tool.resetSelections()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._window
    # end def

    def document(self):
        return self._document
    # end def

    ### PUBLIC METHODS ###
    def removePartItem(self, part_item):
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

    def selectionFilterSet(self):
        return self._document.filter_set
    # end def

    def vhiHandleSelectionGroup(self):
        return self.select_tool.vhi_h_selection_group
    # end def

    def strandItemSelectionGroup(self):
        return self.select_tool.strand_item_selection_group
    # end def

    def selectionLock(self):
        return self.scene().views()[0].selectionLock()
    # end def

    def setSelectionLock(self, locker):
        self.scene().views()[0].setSelectionLock(locker)
    # end def

    def setManager(self, manager):
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def
# end class
