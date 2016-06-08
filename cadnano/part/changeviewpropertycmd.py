from cadnano.cnproxy import UndoCommand

class ChangeViewPropertyCommand(UndoCommand):
    """ Change View properties"""
    def __init__(self, part, view_name, key, val):
        super(ChangeViewPropertyCommand, self).__init__("change view property")
        self.part = part
        self.view_name = view_name
        self.flat_key = flat_key = '%s:%s' % (view_name, key)
        self.keyval = (key, val)
        self.old_keyval = (key, part.getViewProperty(flat_key))
    # end def

    def redo(self):
        part = self.part
        key, val = self.keyval
        part.setViewProperty(self.flat_key, val)
        part.partViewPropertySignal.emit(part, self.view_name, key, val)
    # end def

    def undo(self):
        part = self.part
        key, val = self.old_keyval
        part.setViewProperty(self.flat_key, val)
        part.partViewPropertySignal.emit(part, self.view_name, key, val)
    # end def
# end class
