from cadnano.cnproxy import UndoCommand
from cadnano.assembly import Assembly
from cadnano.part import Part
from cadnano.objectinstance import ObjectInstance

class AddInstanceCommand(UndoCommand):
    """Undo ready command for adding an instance.

    Args:
        document (Document): m
        obj_instance (ObjectInstance): Object instance to add to Document
    """
    def __init__(self, document, cnobj):
        super(AddInstanceCommand, self).__init__("add instance")
        self._document = document
        self._cnobj = cnobj
        self._obj_instance = ObjectInstance(cnobj)
    # end def

    def redo(self):
        doc = self._document
        cnobj = self._cnobj
        obji = self._obj_instance
        cnobj._incrementInstance(doc, obji)
        if isinstance(cnobj, Part):
            doc.documentPartAddedSignal.emit(doc, obji)
        elif isinstance(cnobj, Assembly):
            doc.documentAssemblyAddedSignal.emit(doc, obji)
        else:
            raise NotImplementedError

    # end def

    def undo(self):
        cnobj = self._cnobj
        obji = self._obj_instance
        if cnobj._canRemove():
            if isinstance(cnobj, Part):
                cnobj.partRemovedSignal.emit(obji)
            else:
                cnobj.assemblyRemovedSignal.emit(obji)
        cnobj._decrementInstance(obji)
    # end def
# end class
