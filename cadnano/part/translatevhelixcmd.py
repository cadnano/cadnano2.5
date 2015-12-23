from cadnano.cnproxy import UndoCommand

class TranslateVirtualHelicesCommand(UndoCommand):
    """ Move Virtual Helices around"""
    def __init__(self, part, virtual_helix_set, dx, dy):
        super(TranslateVirtualHelicesCommand, self).__init__("translate virtual helices")
        self._part = part
        self._vhelix_set = virtual_helix_set.copy()
        self.delta = (dx, dy)
    # end def

    def redo(self):
        dx, dy = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, dx, dy, False)
    # end def

    def undo(self):
        dx, dy = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, -dx, -dy, True)
    # end def

    def specialUndo(self):
        """ does not deselect
        """
        dx, dy = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, -dx, -dy, False)
    # end def
# end class
