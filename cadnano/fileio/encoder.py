from json import dumps
from .c25encoder import c25_dict_from_doc

def encode(document, helix_order_list, io):
    obj = c25_dict_from_doc(document, io.name, helix_order_list)
    json_string = dumps(obj, separators=(',', ':'))  # compact encoding
    io.write(json_string)
