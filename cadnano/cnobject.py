# -*- coding: utf-8 -*-
from cadnano.cnproxy import BaseObject


class CNObject(BaseObject):
    def __init__(self, parent):
        super(CNObject, self).__init__(parent)

    def undoStack(self):
        return self._document.undoStack()
    # end def
# end class
