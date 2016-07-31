"""Summary
"""
from .abstractpathtool import AbstractPathTool
from .pathselection import EndpointHandleSelectionBox
from .pathselection import SelectionItemGroup
from .pathselection import VirtualHelixHandleSelectionBox


class SelectTool(AbstractPathTool):
    """
    SelectTool is the default tool. It allows editing of breakpoints
    (by clicking and dragging) and toggling of crossovers.

    Attributes:
        strand_item_selection_group (TYPE): Description
        vhi_h_selection_group (TYPE): Description
    """
    def __init__(self, manager, viewroot):
        """Summary

        Args:
            manager (TYPE): Description
            viewroot (TYPE): Description
        """
        super(SelectTool, self).__init__(manager)
        b_type = VirtualHelixHandleSelectionBox
        self.vhi_h_selection_group = SelectionItemGroup(boxtype=b_type,
                                                        constraint='y',
                                                        parent=viewroot)
        b_type = EndpointHandleSelectionBox
        self.strand_item_selection_group = SelectionItemGroup(boxtype=b_type,
                                                              constraint='x',
                                                              parent=viewroot)
    # end def

    def resetSelections(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.vhi_h_selection_group.resetSelection()
        self.strand_item_selection_group.resetSelection()

    def clearSelections(self, value):
        """Summary

        Args:
            value (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.vhi_h_selection_group.clearSelection(value)
        self.strand_item_selection_group.clearSelection(value)

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "selectTool"  # first letter should be lowercase
