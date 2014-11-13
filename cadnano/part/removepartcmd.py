from cadnano.cnproxy import UndoCommand

class RemovePartCommand(UndoCommand):
    """
    RemovePartCommand deletes a part. Emits partRemovedSignal.
    """
    def __init__(self, part):
        super(RemovePartCommand, self).__init__("remove part")
        self._part = part
        self._doc = part.document()
    # end def

    def redo(self):
        # Remove the strand
        part = self._part
        doc = self._doc
        doc.removePart(part)
        part.setDocument(None)
        part.partRemovedSignal.emit(part)
    # end def

    def undo(self):
        part = self._part
        doc = self._doc
        doc._addPart(part)
        part.setDocument(doc)
        doc.documentPartAddedSignal.emit(doc, part)
    # end def
# end class