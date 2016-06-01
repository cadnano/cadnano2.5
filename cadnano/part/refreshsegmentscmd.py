from cadnano.cnproxy import UndoCommand

class RefreshSegmentsCommand(UndoCommand):
    """ Add an UndoCommand to the undostack calling Part.refreshSegments
    """
    def __init__(self, part, id_nums):
        super(RefreshSegmentsCommand, self).__init__("refresh segments")
        self.part = part
        self.id_nums = id_nums
    # end def

    def redo(self):
        part = self.part
        for id_num in self.id_nums:
            part.refreshSegments(id_num)
    # end def

    def undo(self):
        part = self.part
        for id_num in self.id_nums:
            part.refreshSegments(id_num)
    # end def
# end class
