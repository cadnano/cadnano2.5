from cadnano.cnproxy import UndoCommand
from cadnano.assembly import Assembly
from cadnano.part import Part


class RemoveInstanceCommand(UndoCommand):
    """
    Undo ready command for removing an instance.

    Args:
        obj_instance (ObjectInstance): Object instance remove
    """
    def __init__(self, cnobj, obj_instance):
        super(RemoveInstanceCommand, self).__init__("remove instance")
        self._items = (cnobj, cnobj.document(), obj_instance)
    # end def

    def redo(self):
        cnobj, doc, obji = self._items
        if cnobj._canRemove():
            if isinstance(cnobj, Part):
                cnobj.partRemovedSignal.emit(obji)
            else:
                cnobj.assemblyRemovedSignal.emit(obji)
        cnobj._decrementInstance(obji)
    # end def

    def undo(self):
        cnobj, doc, obji = self._items
        cnobj._incrementInstance(doc, obji)
        if cnobj._canReAdd():
            if isinstance(cnobj, Part):
                doc.documentPartAddedSignal.emit(doc, obji)
            elif isinstance(cnobj, Assembly):
                doc.documentAssemblyAddedSignal.emit(doc, obji)
            else:
                raise NotImplementedError
    # end def
# end class
