"""Summary
"""
from .abstractpathtool import AbstractPathTool


class EraseTool(AbstractPathTool):
    """
    docstring for EraseTool
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(EraseTool, self).__init__(manager)

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "erase_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "eraseTool"  # first letter should be lowercase
