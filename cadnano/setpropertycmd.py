from cadnano.cnproxy import UndoCommand

class SetPropertyCommand(UndoCommand):
    """Undo ready command for setting an object property
    Can be used by any objects implementing `getProperty` and `_setProperty`

    Args:
        objs (list): iterable of objects
        key (str): property key
        value (any): new value
    """
    def __init__(self, objs, key, value):
        super(SetPropertyCommand, self).__init__("change property")
        self._objs = objs
        self._key = key
        self._value = value
        self._old_values = [x.getProperty(key) for x in objs]
    # end def

    def redo(self):
        key = self._key
        val = self._value
        for obj in self._objs:
            obj._setProperty(key, val, emit_signals=True)
    # end def

    def undo(self):
        key = self._key
        for obj, val in zip(self._objs, self._old_values):
            obj._setProperty(key, val, emit_signals=True)
    # end def
# end class

class SetVHPropertyCommand(UndoCommand):
    """Undo ready command for setting an VirtualHelix for a part

    Args:
        part (NucleicAcidPart):
        id_nums (list): iterable of objects
        key (str): property key
        value (any): new value
    """
    def __init__(self, part, id_nums, keys, values, safe):
        super(SetVHPropertyCommand, self).__init__("change VirtualHelix property")
        self._part = part
        self._id_nums = id_nums
        self._keys = keys
        self._values = values
        self._safe = safe
        self._old_values = [part.getVirtualHelixProperties(x, keys) for x in id_nums]
    # end def

    def redo(self):
        part = self._part
        keys = self._keys
        vals = self._values
        safe = self._safe
        for id_num in self._id_nums:
            part._setVirtualHelixProperties(id_num, keys, vals, emit_signals=safe)
    # end def

    def undo(self):
        part = self._part
        keys = self._keys
        safe = self._safe
        for id_num, vals in zip(self._id_nums, self._old_values):
            part._setVirtualHelixProperties(id_num, keys, vals, emit_signals=safe)
    # end def
# end class
