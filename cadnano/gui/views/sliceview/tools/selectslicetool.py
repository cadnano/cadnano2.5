from .abstractslicetool import AbstractSliceTool

class SelectSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, controller, parent=None):
        super(SelectSliceTool, self).__init__(controller)

    def __repr__(self):
        return "select_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "selectTool"  # first letter should be lowercase
