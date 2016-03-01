from cadnano.cnproxy import UndoCommand

class RenumberVirtualHelicesCommand(UndoCommand):
    """
    """
    def __init__(self, part, coord_list):
        super(RenumberVirtualHelicesCommand, self).__init__("renumber virtual helices")
        self._part = part
        self._vhs = [part.virtualHelixAtCoord(coord) for coord in coord_list]
        self._old_numbers = [vh.number() for vh in self._vhs]
    # end def

    def redo(self):
        even = 0
        odd = 1
        for vh in self._vhs:
            if vh.isEvenParity():
                vh.setNumber(even)
                even += 2
            else:
                vh.setNumber(odd)
                odd += 2
        # end for
        part = self._part
        active_id_num =  part.activeIdNum()
        if active_id_num:
            part.partActiveVirtualHelixChangedSignal.emit(part, active_id_num)
        for oligo in part._oligos:
            for strand in oligo.strand5p().generator3pStrand():
                strand.strandUpdateSignal.emit(strand)
    # end def

    def undo(self):
        for vh, num in izip(self._vhs, self._old_numbers):
            vh.setNumber(num)
        # end for
        part = self._part
        active_id_num =  part.activeIdNum()
        if active_id_num:
            part.partActiveVirtualHelixChangedSignal.emit(part, active_id_num)
        for oligo in part._oligos:
            for strand in oligo.strand5p().generator3pStrand():
                strand.strandUpdateSignal.emit(strand)
    # end def
# end class
