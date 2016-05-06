# -*- coding: utf-8 -*-
import json
import io

from cadnano.document import Document

import .v2decode

def decodeFile(filename, document=None):
    with io.open(filename, 'r', encoding='utf-8') as fd:
        nno_dict = json.load(fd)
    if document is None:
        document = Document()
    if 'format' not in obj:
        v2decode.decode(document, nno_dict)
    else:
        pass
    return document
# end def

def loadtest():
    import os
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', 'super_barcode_hex.json')
    return decodeFile(test_path)

if __name__ == '__main__':
    loadtest()

NODETAG = "node"
NAME = "name"
OBJ_ID = "objectid"
INST_ID = "instanceid"
DONE = "done"
CHECKED = "check"
LOCKED = "locked"

VHELIX = "vhelix"
NUM = "num"
COL = "col"
ROW = "row"
SCAFFOLD = "scaffold"
STAPLE = "staple"
INSERTION = "insertion"
DELETION = "deletion"
