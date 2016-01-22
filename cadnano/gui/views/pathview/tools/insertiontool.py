import sys

from .abstractpathtool import AbstractPathTool


class InsertionTool(AbstractPathTool):
    """
    docstring for InsertionTool
    """
    def __init__(self, manager):
        super(InsertionTool, self).__init__(manager)

    def __repr__(self):
        return "insertion_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "insertionTool"  # first letter should be lowercase