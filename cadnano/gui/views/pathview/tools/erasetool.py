import sys
from .abstractpathtool import AbstractPathTool
import cadnano.util as util


class EraseTool(AbstractPathTool):
    """
    docstring for EraseTool
    """
    def __init__(self, controller):
        super(EraseTool, self).__init__(controller)

    def __repr__(self):
        return "erase_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "eraseTool"  # first letter should be lowercase