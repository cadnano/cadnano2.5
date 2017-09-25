"""Summary
"""
from .abstractslicetool import AbstractSliceTool


class CreateSliceTool(AbstractSliceTool):
    """
    Attributes:
        is_started (bool): Description
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(CreateSliceTool, self).__init__(manager)
        try:
            print('FILTER NAME IS %s' % self.FILTER_NAME)
        except AttributeError:
            print('FILTER NAME NOT SET IN INIT')

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "create_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "createTool"  # first letter should be lowercase

    def startCreation(self):
        """Summary

        Returns:
            TYPE: Description
        """
#        self._line_item.show()
#        self.vhi_hint_item.show()
        self.is_started = True
    # end def
