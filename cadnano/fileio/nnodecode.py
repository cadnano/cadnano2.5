# -*- coding: utf-8 -*-
import json
import io
import os.path

import cadnano.fileio.v2decode as v2decode
import cadnano.fileio.c25decode as c25decode
import cadnano.fileio.v3decode as v3decode

def decodeFile(filename, document=None, emit_signals=False):
    with io.open(filename, 'r', encoding='utf-8') as fd:
        nno_dict = json.load(fd)
    if document is None:
        from cadnano.document import Document
        document = Document()
    if 'format' not in nno_dict:
        if os.path.splitext(filename)[1] == '.c25':
            c25decode.decode(document, nno_dict, emit_signals=emit_signals)
        else:
            v2decode.decode(document, nno_dict, emit_signals=emit_signals)
    else:
        v3decode.decode(document, nno_dict, emit_signals=emit_signals)
    return document
# end def

def loadtest():
    import os
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    test_path = os.path.join(root_path, 'tests', 'super_barcode_hex.json')
    return decodeFile(test_path)

if __name__ == '__main__':
    loadtest()
