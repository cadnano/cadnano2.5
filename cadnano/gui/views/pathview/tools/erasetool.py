import sys

from .abstractpathtool import AbstractPathTool

class EraseTool(AbstractPathTool):
    """
    docstring for EraseTool
    """
    def __init__(self, manager):
        super(EraseTool, self).__init__(manager)

    def __repr__(self):
        return "erase_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "eraseTool"  # first letter should be lowercase