"""Summary
"""
from .abstractpathtool import AbstractPathTool


class SkipTool(AbstractPathTool):
    """
    docstring for SkipTool
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(SkipTool, self).__init__(manager)

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "skip_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "skipTool"  # first letter should be lowercase
