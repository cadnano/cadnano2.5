from json import dumps
from .legacyencoder import legacy_dict_from_doc

def encode(document, helix_order_list, io):
    obj = legacy_dict_from_doc(document, io.name, helix_order_list)
    json_string = dumps(obj, separators=(',', ':'))  # compact encoding
    io.write(json_string)
