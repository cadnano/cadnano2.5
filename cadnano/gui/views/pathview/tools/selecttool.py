import sys
from .abstractpathtool import AbstractPathTool
import cadnano.util as util

class SelectTool(AbstractPathTool):
    """
    SelectTool is the default tool. It allows editing of breakpoints
    (by clicking and dragging) and toggling of crossovers.
    """
    def __init__(self, controller):
        super(SelectTool, self).__init__(controller)

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase