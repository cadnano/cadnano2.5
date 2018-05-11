# -*- coding: utf-8 -*-
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

    def __repr__(self) -> str:
        """Summary

        Returns:
            lower case name
        """
        return "insertion_tool"  # first letter should be lowercase

    def methodPrefix(self) -> str:
        """Summary

        Returns:
            prefix string
        """
        return "insertionTool"  # first letter should be lowercase
