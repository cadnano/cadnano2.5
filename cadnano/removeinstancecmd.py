from cadnano.cnproxy import UndoCommand
from cadnano.assembly import Assembly
from cadnano.part import Part

### COMMANDS ###
class RemoveInstanceCommand(UndoCommand):
    """
    Undo ready command for adding an instance.
    """
    def __init__(self, obj_instance):
        super(RemoveInstanceCommand, self).__init__("add instance")
        self._items = (obj_instance, obj_instance.document())
    # end def

    def instance(self):
        return self._items[0]
    # end def

    def redo(self):
        obji, doc = self._items
        if isinstance(obji.reference(), Part):
            obji.reference().partRemovedSignal.emit(obji)
        else:
            obji.reference().assemblyRemovedSignal.emit(obji)
        obji.wipe(doc)
    # end def

    def undo(self):
        obji, doc = self._items
        obji.unwipe(doc)
        if isinstance(obji.reference(), Part):
            doc.documentPartAddedSignal.emit(doc, obji)
        elif isinstance(obji.reference(), Assembly):
            doc.documentAssemblyAddedSignal.emit(doc, obji)
        else:
            raise NotImplementedError
    # end def
# end class
