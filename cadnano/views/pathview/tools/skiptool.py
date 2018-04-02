# -*- coding: utf-8 -*-
from .abstractpathtool import AbstractPathTool
from cadnano.views.pathview import (
        PathToolManagerT
)


class SkipTool(AbstractPathTool):
    """
    """

    def __init__(self, manager: PathToolManagerT):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(SkipTool, self).__init__(manager)

    def __repr__(self) -> str:
        """
        Returns:
            tool name
        """
        return "skip_tool"  # first letter should be lowercase

    def methodPrefix(self) -> str:
        """
        Returns:
            prefix string
        """
        return "skipTool"  # first letter should be lowercase
