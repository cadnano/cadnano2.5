from cadnano.cnproxy import BaseObject

class CNObject(BaseObject):
    # __slots__ = ()

    def __init__(self, parent):
        super(CNObject, self).__init__(parent)

    def undoStack(self):
        return self._document.undoStack()
    # end def
# end class