"""Summary
"""
from PyQt5.QtWidgets import QGraphicsRectItem
from cadnano import util
from cadnano.cnenum import PartType
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .nucleicacidpartitem import PathNucleicAcidPartItem


class PathRootItem(QGraphicsRectItem):
    """
    PathRootItem is the root item in the PathView. It gets added directly
    to the pathscene by DocumentWindow. It receives two signals
    (partAddedSignal and documentSelectedPartChangedSignal)
    via its ViewRootController.

    PathRootItem must instantiate its own controller to receive signals
    from the model.

    Attributes:
        findChild (TYPE): Description
        manager (TYPE): Description
        name (str): Description
        select_tool (TYPE): Description
    """
    findChild = util.findChild  # for debug
    name = 'path'

    def __init__(self, rect, parent, window, document):
        """Summary

        Args:
            rect (TYPE): Description
            parent (TYPE): Description
            window (TYPE): Description
            document (TYPE): Description
        """
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
        """Summary

        Returns:
            iterator: Description
        """
        return self._part_item_for_part_instance.values()

    def partItemForPart(self, part):
        """Summary

        Args:
            part (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self._part_item_for_part_instance[part]

    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        The Pathview doesn't need to do anything on part addition, since
        the Sliceview handles setting up the appropriate lattice.

        Args:
            sender (obj): Model object that emitted the signal.
            model_part_instance (TYPE): Description

        Raises:
            NotImplementedError: Description
        """
        win = self._window
        part_type = model_part_instance.reference().partType()

        if part_type == PartType.PLASMIDPART:
            pass
        elif part_type == PartType.NUCLEICACIDPART:
            na_part_item = PathNucleicAcidPartItem(model_part_instance,
                                               viewroot=self,
                                               parent=self)
            self._part_item_for_part_instance[model_part_instance] = na_part_item
            win.path_tool_manager.setActivePart(na_part_item)
        else:
            raise NotImplementedError
    # end def

    def clearSelectionsSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        # print("yargh!!!!")
        self.select_tool.resetSelections()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def selectionFilterChangedSlot(self, filter_name_set):
        """Summary

        Args:
            filter_name_set (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.select_tool.clearSelections(False)
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        """Summary

        Args:
            filter_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        print("path updating preXovers", filter_name)
        self._prexover_filter = filter_name
    # end def

    def resetRootItemSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.select_tool.resetSelections()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._window
    # end def

    def document(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._document
    # end def

    ### PUBLIC METHODS ###
    def removePartItem(self, part_item):
        """Summary

        Args:
            part_item (TYPE): Description

        Returns:
            TYPE: Description
        """
        for k in self._part_item_for_part_instance.keys():
            if k == part_item:
                del self._part_item_for_part_instance[k]
                return
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController

        Args:
            document (TYPE): Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState

        Args:
            bool (TYPE): Description
        """
        for part_item in self._part_item_for_part_instance.values():
            part_item.setModifyState(bool)
    # end def

    def selectionFilterSet(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._document.filter_set
    # end def

    def vhiHandleSelectionGroup(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.select_tool.vhi_h_selection_group
    # end def

    def strandItemSelectionGroup(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.select_tool.strand_item_selection_group
    # end def

    def selectionLock(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.scene().views()[0].selectionLock()
    # end def

    def setSelectionLock(self, locker):
        """Summary

        Args:
            locker (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.scene().views()[0].setSelectionLock(locker)
    # end def

    def setManager(self, manager):
        """Summary

        Args:
            manager (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def

    def clearSelectionsIfActiveTool(self):
        """Summary

        Returns:
            TYPE: Description
        """
        if self.manager.isSelectToolActive():
            self.select_tool.clearSelections(False)
    # end def

    def mousePressEvent(self, event):
        """Handler for user mouse press.

        Args:
            event (QGraphicsSceneMouseEvent): Contains item, scene, and screen
            coordinates of the the event, and previous event.

        Returns:
            TYPE: Description
        """
        print("ADSDsadf")
        self.clearSelectionsIfActiveTool()
        return QGraphicsRectItem.mousePressEvent(self, event)
# end class
