from cadnano.cnproxy import UndoCommand
from cadnano.assembly import Assembly
from cadnano.part import Part

### COMMANDS ###
class AddInstanceCommand(UndoCommand):
    """
    Undo ready command for deleting an instance.
    """
    def __init__(self, document, obj_instance):
        super(AddInstanceCommand, self).__init__("add instance")
        self._doc = document
        self._obj_instance = obj_instance
    # end def

    def instance(self):
        return self._obj_instance
    # end def

    def redo(self):
        doc = self._doc
        obji = self._obj_instance
        obji.unwipe(doc)
        if isinstance(obji.object(), Part):
            doc.documentPartAddedSignal.emit(doc, obji)
        elif isinstance(obji.object(), Assembly):
            doc.documentAssemblyAddedSignal.emit(doc, obji)
        else:
            raise NotImplementedError
    # end def

    def undo(self):
        obji = self._obj_instance
        obji.wipe(self._doc)
        obji.partRemovedSignal.emit(obji)
    # end def
# end class
