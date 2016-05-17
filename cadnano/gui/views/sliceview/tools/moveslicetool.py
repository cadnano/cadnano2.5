from .abstractslicetool import AbstractSliceTool
import math

class MoveSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, manager):
        super(MoveSliceTool, self).__init__(manager)

    def __repr__(self):
        return "move_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "moveTool"  # first letter should be lowercase
    # end def
# end class
