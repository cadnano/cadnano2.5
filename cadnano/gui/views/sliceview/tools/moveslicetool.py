"""Summary
"""
from .abstractslicetool import AbstractSliceTool


class MoveSliceTool(AbstractSliceTool):
    """MoveSliceTool description"""
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(MoveSliceTool, self).__init__(manager)

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "move_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "moveTool"  # first letter should be lowercase
    # end def
# end class
