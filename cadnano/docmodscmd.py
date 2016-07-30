from cadnano.cnproxy import UndoCommand

"""
For adding modifications from a document
"""


class AddModCommand(UndoCommand):
    def __init__(self, document, params, mid):
        """
        params: the mods parameters
        mid: mod id
        """
        super(AddModCommand, self).__init__()
        self._document = document
        self._params = params
        self._mid = mid
    # end def

    def redo(self):
        document = self._document
        mid = self._mid
        params = self._params
        document._mods[mid] = params
        document.documentModAddedSignal.emit(document, params['props'], mid)
    # end def

    def undo(self):
        document = self._document
        mid = self._mid
        del self._document._mods[mid]
        document.documentModRemovedSignal.emit(document, mid)
    # end def
# end class


class RemoveModCommand(UndoCommand):
    def __init__(self, document, mid):
        super(RemoveModCommand, self).__init__()
        self._document = document
        # just reference the whole dictionary
        self._params_old = self._document._mods[mid]['props']
        self._mid = mid
        self._ext_instances = []
        locations = document._mods[mid]['ext_locations']
        for key in locations:
            part, strand, idx = document.getModStrandIdx(key)
            self._ext_instances.append(key, part, strand, idx)
        self._int_instances = []
        locations = document._mods[mid]['int_locations']
        for key in locations:
            part, strand, idx = document.getModStrandIdx(key)
            self._int_instances.append(key, part, strand, idx)
    # end def

    def redo(self):
        document = self._document
        mid = self._mid
        # Destroy all instances of the mod
        for key, part, strand, idx in self._ext_instances:
            strand.strandModsRemovedSignal.emit(strand, document, mid, idx)
            part.removeModStrandInstance(strand, idx, mid)

        # now internal location
        for key, part, strand, idx in self._int_instances:
            strand.strandModsRemovedSignal.emit(strand, document, mid, idx)
            part.removeModStrandInstance(strand, idx, mid, is_internal=True)
        del document._mods[mid]
        document.documentModRemovedSignal.emit(part, mid)
    # end def

    def undo(self):
        document = self._document
        mid = self._mid
        params_old = self._params_old
        document._mods[mid]['props'] = params_old
        # Destroy all instances of the mod
        for key, part, strand, idx in self._ext_instances:
            part.addModStrandInstance(strand, idx, mid)
            strand.strandModsAddedSignal.emit(strand, document, mid, idx)
        # now internal locations
        for key, part, strand, idx in self._ext_instances:
            part.addModStrandInstance(strand, idx, mid, is_internal=True)
            strand.strandModsAddedSignal.emit(strand, document, mid, idx)
        document.documentModAddedSignal.emit(document, params_old, mid)
    # end def
# end class


class ModifyModCommand(UndoCommand):
    def __init__(self, document, params, mid):
        super(ModifyModCommand, self).__init__()
        self._document = document
        params_old = document._mods[mid].copy()

        self._params = params
        self._mid = mid

        self._ext_instances = []
        locations = params_old['ext_locations']

        for key in locations:
            part, strand, idx = document.getModStrandIdx(key)
            self._ext_instances.append((key, part, strand, idx))
        self._int_instances = []
        locations = params_old['int_locations']
        for key in locations:
            part, strand, idx = document.getModStrandIdx(key)
            self._int_instances.append((key, part, strand, idx))

        self._params_old = params_old['props']
    # end def

    def redo(self):
        document = self._document
        mid = self._mid
        document._mods[mid]['props'].update(self._params)
        document.documentModChangedSignal.emit(document, self._params, mid)
        for key, part, strand, idx in self._ext_instances:
            strand.strandModsChangedSignal.emit(strand, document, mid, idx)
        for key, part, strand, idx in self._int_instances:
            strand.strandModsChangedSignal.emit(strand, document, mid, idx)
    # end def

    def undo(self):
        document = self._document
        mid = self._mid
        document._mods[mid]['props'].update(self._params_old)
        document.documentModChangedSignal.emit(document, self._params_old, mid)
        for key, part, strand, idx in self._ext_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
        for key, part, strand, idx in self._int_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
    # end def
# end class
