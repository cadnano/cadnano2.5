# -*- coding: utf-8 -*-
from cadnano.cnproxy import UndoCommand

class ApplyColorCommand(UndoCommand):
    def __init__(self, oligo, color):
        super(ApplyColorCommand, self).__init__("apply color")
        self._oligo = oligo
        self._new_color = color
        self._old_color = oligo.getColor()
    # end def

    def redo(self):
        olg = self._oligo
        nc = self._new_color
        olg._setColor(nc)
        olg.oligoPropertyChangedSignal.emit(olg, 'color', nc)
    # end def

    def undo(self):
        olg = self._oligo
        oc = self._old_color
        olg._setColor(oc)
        olg.oligoPropertyChangedSignal.emit(olg, 'color', oc)
    # end def
# end class