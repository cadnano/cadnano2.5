from ast import literal_eval

from cadnano.cnproxy import UndoCommand
from cadnano.part.nucleicacidpart import NucleicAcidPart


class CreateNucleicAcidPartCommand(UndoCommand):
    def __init__(self, document, grid_type, use_undostack):
        # TODO[NF]:  Docstring
        super(CreateNucleicAcidPartCommand, self).__init__("Create NA Part")
        self.document = document
        self.grid_type = grid_type
        self.use_undostack = use_undostack

    def redo(self):
        new_part = NucleicAcidPart(document=self.document, grid_type=self.grid_type)
        self.document._addPart(new_part, use_undostack=self.use_undostack)


    def undo(self):
        self.document.deactivateActivePart()
