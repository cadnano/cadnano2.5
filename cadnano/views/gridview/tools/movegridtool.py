"""Summary
"""
from .abstractgridtool import AbstractGridTool


class MoveGridTool(AbstractGridTool):
    """MoveGridTool description"""

    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(MoveGridTool, self).__init__(manager)

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
