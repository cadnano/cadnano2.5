import sys
from .abstractpathtool import AbstractPathTool
import cadnano.util

class SkipTool(AbstractPathTool):
    """
    docstring for SkipTool
    """
    def __init__(self, controller):
        super(SkipTool, self).__init__(controller)

    def __repr__(self):
        return "skip_tool"  # first letter should be lowercase
    
    def methodPrefix(self):
        return "skipTool"  # first letter should be lowercase