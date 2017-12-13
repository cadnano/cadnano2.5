"""Summary
"""
from PyQt5.Qt3DCore import QEntity
from cadnano.cnenum import PartType
from cadnano.gui.controllers.viewrootcontroller import ViewRootController
from .nucleicacidpartitem import SimNucleicAcidPartItem


class SimRootItem(QEntity):
    """
    SimRootItem is the root item in the SimView. It gets added directly
    to the simscene by DocumentWindow. It receives two signals
    (partAddedSignal and selectedPartChangedSignal) via its ViewRootController.

    SimRootItem must instantiate its own controller to receive signals
    from the model.

    Attributes:
        instance_items (dict): Description
        manager (TYPE): Description
        name (str): Description
        select_tool (TYPE): Description
    """
    name = 'sim'

    def __init__(self, window, document):
        """Summary

        Args:
            parent (TYPE): Description
            window (TYPE): Description
            document (TYPE): Description
        """
        super(SimRootItem, self).__init__()
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self.instance_items = {}
        self.manager = None
        self.select_tool = None

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender, model_part_instance):
        """
        Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.

        Args:
            sender (obj): Model object that emitted the signal.
            model_part_instance (Part): Description

        Raises:
            NotImplementedError: partAddedSlot should always be overridden.
        """
        part_type = model_part_instance.reference().partType()
        if part_type == PartType.NUCLEICACIDPART:
            na_part_item = SimNucleicAcidPartItem(model_part_instance,
                                                  viewroot_entity=self,
                                                  parent=self)
            self.instance_items[na_part_item] = na_part_item
            # self.select_tool.setPartItem(na_part_item)
            # na_part_item.zoomToFit()
        else:
            raise NotImplementedError
    # end def

    def selectedChangedSlot(self, item_dict):
        """docstring for selectedChangedSlot

        Args:
            item_dict (TYPE): Description
        """
        pass
    # end def

    def selectionFilterChangedSlot(self, filter_name_list):
        """Summary

        Args:
            filter_name_list (TYPE): Description

        Returns:
            TYPE: Description
        """
        # if 'virtual_helix' not in filter_name_list:
        #     self.manager.chooseCreateTool()
        pass
        # for nucleicacid_part_item in self.instance_items:
        #     nucleicacid_part_item.setSelectionFilter(filter_name_list)
    # end def

    def preXoverFilterChangedSlot(self, filter_name):
        """Summary

        Args:
            filter_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
    # end def

    def clearSelectionsSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
        # self.select_tool.deselectItems()
        # self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def resetRootItemSlot(self, doc):
        """Summary

        Args:
            doc (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
        # self.select_tool.deselectItems()
        # self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._window
    # end def

    ### METHODS ###
    def removePartItem(self, part_item):
        """Summary

        Args:
            part_item (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
        # del self.instance_items[part_item]
    # end def

    def resetDocumentAndController(self, document):
        """docstring for resetDocumentAndController

        Args:
            document (TYPE): Description

        Raises:
            ImportError: Description
        """
        pass
        # self._document = document
        # self._controller = ViewRootController(self, document)
        # if len(self.instance_items) > 0:
        #     raise ImportError
    # end def

    def setModifyState(self, bool):
        """docstring for setModifyState

        Args:
            bool (TYPE): Description
        """
        pass
        # for nucleicacid_part_item in self.instance_items:
        #     nucleicacid_part_item.setModifyState(bool)
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