from cadnano.cnproxy import UndoCommand

class ApplyColorCommand(UndoCommand):
    def __init__(self, oligo, color):
        super(ApplyColorCommand, self).__init__("apply color")
        self._oligo = oligo
        self._new_color = color
        self._old_color = oligo.color()
    # end def

    def redo(self):
        olg = self._oligo
        olg.setColor(self._new_color)
        olg.oligoAppearanceChangedSignal.emit(olg)
    # end def

    def undo(self):
        olg = self._oligo
        olg.setColor(self._old_color)
        olg.oligoAppearanceChangedSignal.emit(olg)
    # end def
# end class