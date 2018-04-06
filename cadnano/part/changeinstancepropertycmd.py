# -*- coding: utf-8 -*-
from typing import Any

from cadnano.proxies.cnproxy import UndoCommand
from cadnano.cntypes import (
    PartT,
    ObjectInstanceT
)

class ChangeInstancePropertyCommand(UndoCommand):
    """ Change ObjectInstance view properties"""

    def __init__(self, part: PartT,
                        part_instance: ObjectInstanceT,
                        view_name: str,
                        key: str,
                        val: Any):
        super(ChangeInstancePropertyCommand, self).__init__("change instance property")
        self.part = part
        self.part_instance = part_instance
        self.view_name = view_name
        self.flat_key = flat_key = '%s:%s' % (view_name, key)
        self.keyval = (key, val)
        self.old_keyval = (key, part.getInstanceProperty(part_instance, flat_key))
    # end def

    def redo(self):
        part = self.part
        part_instance = self.part_instance
        key, val = self.keyval
        part.setInstanceProperty(part_instance, self.flat_key, val)
        part.partInstancePropertySignal.emit(part_instance, self.view_name, key, val)
    # end def

    def undo(self):
        part = self.part
        part_instance = self.part_instance
        key, val = self.old_keyval
        part.setInstanceProperty(part_instance, self.flat_key, val)
        part.partInstancePropertySignal.emit(part_instance, self.view_name, key, val)
    # end def
# end class
