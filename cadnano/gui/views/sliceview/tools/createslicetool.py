from .abstractslicetool import AbstractSliceTool

class CreateSliceTool(AbstractSliceTool):
    """"""
    def __init__(self, controller, parent=None):
        super(CreateSliceTool, self).__init__(controller)

    def __repr__(self):
        return "create_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "createTool"  # first letter should be lowercase
