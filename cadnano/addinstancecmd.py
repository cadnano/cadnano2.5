from cadnano.cnproxy import UndoCommand
from cadnano.assembly import Assembly
from cadnano.part import Part


class AddInstanceCommand(UndoCommand):
    """Undo ready command for adding an instance.

    Args:
        document (Document): m
        obj_instance (ObjectInstance): Object instance to add to Document
    """
    def __init__(self, document, obj_instance):
        super(AddInstanceCommand, self).__init__("add instance")
        self._document = document
        self._obj_instance = obj_instance
    # end def

    def instance(self):
        """
        Returns:
            ObjectInstance: the object instance attribute of the Command
        """
        return self._obj_instance
    # end def

    def redo(self):
        doc = self._document
        obji = self._obj_instance
        print("unwipe")
        obji.unwipe(doc)
        if isinstance(obji.reference(), Part):
            doc.documentPartAddedSignal.emit(doc, obji)
        elif isinstance(obji.reference(), Assembly):
            doc.documentAssemblyAddedSignal.emit(doc, obji)
        else:
            raise NotImplementedError
    # end def

    def undo(self):
        print("wipe")
        obji = self._obj_instance
        if isinstance(obji.reference(), Part):
            obji.reference().partRemovedSignal.emit(obji)
        else:
            obji.reference().assemblyRemovedSignal.emit(obji)
        obji.wipe(self._document)
    # end def
# end class
