from cadnano.cnproxy import UndoCommand

class ChangeViewPropertyCommand(UndoCommand):
    """ Change View properties"""
    def __init__(self, part, view, key, val):
        super(ChangeViewPropertyCommand, self).__init__("change view property")
        self.part = part
        self.view = view
        self.keyval = (key, val)
        self.old_keyval = (key, part.getViewProperty(key))
    # end def

    def redo(self):
        part = self.part
        key, val = self.keyval
        part.setViewProperty(key, val)
        part.partViewPropertySignal.emit(part, self.view, key, val)
    # end def

    def undo(self):
        part = self.part
        key, val = self.old_keyval
        part.setViewProperty(key, val)
        part.partViewPropertySignal.emit(part, self.view, key, val)
    # end def
# end class
