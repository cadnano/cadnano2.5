from cadnano.proxies.cnproxy import UndoCommand
from cadnano.cntypes import (
    NucleicAcidPartT,
)

class ResizeVirtualHelixCommand(UndoCommand):
    """set the maximum and mininum base index in the helical direction

    need to adjust all subelements in the event of a change in the
    minimum index
    """

    def __init__(self,  part: NucleicAcidPartT,
                        id_num: int,
                        is_right: bool,
                        delta: int,
                        zoom_to_fit: bool = True):
        """
        Args:
            part:
            id_num:
            is_right:
            delta: number of bases to add to the helix
            zoom_to_fit: Default is ``True``
        """
        super(ResizeVirtualHelixCommand, self).__init__("resize virtual helix")
        self._part = part
        self._info = (id_num, is_right, delta, zoom_to_fit)
    # end def

    def redo(self):
        part = self._part
        id_num, is_right, delta, zoom_to_fit = self._info
        id_min, id_max = part._resizeHelix(id_num, is_right, delta)
        part.partVirtualHelixResizedSignal.emit(
            part, id_num, part.getVirtualHelix(id_num))
        part.partZDimensionsChangedSignal.emit(part, id_min, id_max, zoom_to_fit)
    # end def

    def undo(self):
        part = self._part
        id_num, is_right, delta, zoom_to_fit = self._info
        id_min, id_max = part._resizeHelix(id_num, is_right, -delta)
        part.partVirtualHelixResizedSignal.emit(
            part, id_num, part.getVirtualHelix(id_num))
        part.partZDimensionsChangedSignal.emit(part, id_min, id_max, zoom_to_fit)
    # end def
# end class
