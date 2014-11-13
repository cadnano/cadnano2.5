import sys
from .abstractpathtool import AbstractPathTool
import cadnano.util


class InsertionTool(AbstractPathTool):
    """
    docstring for InsertionTool
    """
    def __init__(self, controller):
        super(InsertionTool, self).__init__(controller)

    def __repr__(self):
        return "insertion_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "insertionTool"  # first letter should be lowercase