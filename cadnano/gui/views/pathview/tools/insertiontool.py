"""Summary
"""
from .abstractpathtool import AbstractPathTool


class InsertionTool(AbstractPathTool):
    """
    docstring for InsertionTool
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(InsertionTool, self).__init__(manager)

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "insertion_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "insertionTool"  # first letter should be lowercase
