from .abstractslicetool import AbstractSliceTool
import math

class CreateSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, manager):
        super(CreateSliceTool, self).__init__(manager)

    def __repr__(self):
        return "create_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "createTool"  # first letter should be lowercase

    def startCreation(self):
        self._line_item.show()
        self.is_started = True
    # end def
