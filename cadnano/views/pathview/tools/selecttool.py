# -*- coding: utf-8 -*-
from .abstractpathtool import AbstractPathTool
from .pathselection import EndpointHandleSelectionBox
from .pathselection import SelectionItemGroup
from .pathselection import VirtualHelixHandleSelectionBox
from cadnano.views.pathview import (
        PathToolManagerT,
        PathRootItemT,
        PathVirtualHelixItemT
)

class SelectTool(AbstractPathTool):
    """
    SelectTool is the default tool. It allows editing of breakpoints
    (by clicking and dragging) and toggling of crossovers.

    Attributes:
        strand_item_selection_group (SelectionItemGroup): Description
        vhi_h_selection_group (SelectionItemGroup): Description
    """

    def __init__(self, manager: PathToolManagerT, viewroot: PathRootItemT):
        """Summary

        Args:
            manager Description
            viewroot: Description
        """
        super(SelectTool, self).__init__(manager)
        b_type = VirtualHelixHandleSelectionBox
        self.vhi_h_selection_group = SelectionItemGroup(boxtype=b_type,
                                                        constraint='y',
                                                        viewroot=viewroot)
        b_type = EndpointHandleSelectionBox
        self.strand_item_selection_group = SelectionItemGroup(boxtype=b_type,
                                                              constraint='x',
                                                              viewroot=viewroot)
        # TODO[NF]: LOGGER
        # print("A select tool was instantiated")
    # end def

    def resetSelections(self):
        """
        Returns:
            TYPE: Description
        """
        self.vhi_h_selection_group.resetSelection()
        self.strand_item_selection_group.resetSelection()

    def clearSelections(self, value):
        """
        Args:
            value (TYPE): Description
        """
        self.vhi_h_selection_group.clearSelection(value)
        self.strand_item_selection_group.clearSelection(value)

    def __repr__(self) -> str:
        """
        Returns:
            tool name
        """
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self) -> str:
        """
        Returns:
            prefix string
        """
        return "selectTool"  # first letter should be lowercase
