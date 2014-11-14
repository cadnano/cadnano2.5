from cadnano.cnproxy import UndoCommand

"""
For adding modifications from a Part
"""

class AddModCommand(UndoCommand):
    def __init__(self, part, params, mid):
        """
        params: the mods parameters
        mid: mod id
        """
        super(AddModCommand, self).__init__()
        self._part = part
        self._params = params
        self._mid = mid
    # end def

    def redo(self):
        part = self._part
        mid = self._mid
        part._mods[mid] = self._params
        part.partModAddedSignal.emit(part, self._params, mid)
    # end def

    def undo(self):
        part = self.part
        mid = self._mid
        del self._part._mods[mid]
        part.partModRemovedSignal.emit(part, mid)
    # end def
# end class

class RemoveModCommand(UndoCommand):
    def __init__(self, part, mid):
        super(RemoveModCommand, self).__init__()
        self._part = part
        self._params_old = self._part._mods[mid].copy()
        self._mid = mid
        self._ext_instances = []
        locations = part._mods[mid]['ext_locations']
        mods_strand = part._mods['ext_instances']
        for key in locations:        
            if key in mods_strand:
                self._ext_instances.append(key, strand, idx)
        self._int_instances = []
        locations = part._mods[mid]['int_locations']
        mods_strand = part._mods['int_instances']
        for key in locations:        
            if key in mods_strand:
                strand, idx = part.getModStrandIdx(key)
                self._int_instances.append(key, strand, idx)
    # end def

    def redo(self):
        part = self._part
        mid = self._mid
        # Destroy all instances of the mod
        mods_strand = part._mods['ext_instances']
        for key, strand, idx in self._ext_instances:
            strand.strandModsRemovedSignal.emit(strand, mid, idx)
            del mods_strand[key]
        # now internal locations
        mods_strand_internal = part._mods['int_instances']
        for key, strand, idx in self._int_instances:
            strand.strandModsRemovedSignal.emit(strand, mid, idx)
            del mods_strand_internal[key]
        del part._mods[mid]
        part.partModRemovedSignal.emit(part, mid)
    # end def

    def undo(self):
        part = self._part
        mid = self._mid
        part._mods[mid] = self._params_old
        # Destroy all instances of the mod
        mods_strand = part._mods['ext_instances']
        for key, strand, idx in self._ext_instances:
            mods_strand[key] = mid
            strand.strandModsAddedSignal.emit(strand, mid, idx)
        # now internal locations
        mods_strand_internal = part._mods['int_instances']
        for key, strand, idx in self._int_instances:
            mods_strand_internal[key] = mid
            strand.strandModsAddedSignal.emit(strand, mid, idx)
        part.partModAddedSignal.emit(part, self._params_old, mid)
    # end def
# end class

class ModifyModCommand(UndoCommand):
    def __init__(self, part, params, mid):
        super(ModifyModCommand, self).__init__()
        self._part = part
        params_old = part._mods[mid].copy()

        self._params = params
        self._mid = mid

        self._ext_instances = []
        locations = params_old['ext_locations']
        mods_strand = part._mods['ext_instances']
        for key in locations:        
            if key in mods_strand:
                strand, idx = part.getModStrandIdx(key)
                self._ext_instances.append((key, strand, idx))
        self._int_instances = []
        locations = params_old['int_locations']
        mods_strand = part._mods['int_instances']
        for key in locations:        
            if key in mods_strand:
                strand, idx = part.getModStrandIdx(key)
                self._int_instances.append((key, strand, idx))

        del params_old['ext_locations']
        del params_old['int_locations']
        self._params_old = params_old
    # end def

    def redo(self):
        part = self._part
        mid = self._mid
        part._mods[mid].update(self._params)
        part.partModChangedSignal.emit(part, self._params, mid)
        for key, strand, idx in self._ext_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
        for key, strand, idx in self._int_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
    # end def

    def undo(self):
        part = self._part
        mid = self._mid
        self._part._mods[mid].update(self._params_old)
        part.partModChangedSignal.emit(part, self._params_old, mid)
        for key, strand, idx in self._ext_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
        for key, strand, idx in self._int_instances:
            strand.strandModsChangedSignal.emit(strand, mid, idx)
    # end def
# end class