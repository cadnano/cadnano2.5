from cadnano.cnproxy import UndoCommand
from cadnano.virtualhelix.virtualhelixgroup import Z_PROP_INDEX

class TranslateVirtualHelicesCommand(UndoCommand):
    """ Move Virtual Helices around"""
    def __init__(self, part, virtual_helix_set, dx, dy, dz):
        super(TranslateVirtualHelicesCommand, self).__init__("translate virtual helices")
        self._part = part
        self._vhelix_set = virtual_helix_set.copy()
        self.delta = (dx, dy, dz)
    # end def

    def redo(self):
        dx, dy, dz = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, dx, dy, dz, False)
        self.doSignals(part, vh_set)
    # end def

    def undo(self):
        dx, dy, dz = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, -dx, -dy, -dz, True)
        self.doSignals(part, vh_set)
    # end def

    def doSignals(self, part, vh_set):
        vh_list = list(vh_set)
        z_vals = part.vh_properties.iloc[vh_list, Z_PROP_INDEX]
        if isinstance(z_vals, float):
            z_vals = (z_vals, )
        for id_num, z_val in zip(vh_list, z_vals):
            part.partVirtualHelixPropertyChangedSignal.emit(
                                    part, id_num, ('z',), (z_val,))
        part.partDimensionsChangedSignal.emit(part, *part.zBoundsIds(), False)
    # end def

    def specialUndo(self):
        """ does not deselect
        """
        dx, dy, dz = self.delta
        part = self._part
        vh_set = self._vhelix_set
        part._translateVirtualHelices(vh_set, -dx, -dy, -dz, False)
    # end def
# end class
