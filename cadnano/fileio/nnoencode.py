from os.path import basename

from cadnano.enum import StrandType
import json
import io

def encodeToFile(filename, document):
    json_string = encode(document, nno_dict)
    with io.open(filename, 'w', encoding='utf-8') as fd:
        fd.write(json_string)
# end def

def encode(document):
    obj = legacy_dict_from_doc(document)
    json_string = json.dumps(obj, separators=(',', ':'))  # compact encoding
    return json_string

def legacy_dict_from_doc(document):
    part = document.selectedInstance().reference()
    num_bases = part.maxBaseIdx()+1
    return encodePart(part, name=fname)

def encodePart(part, name=None):
    helix_order_list = part.getImportVirtualHelixOrder()
    num_bases = part.maxBaseIdx()+1
    part_name = name if name is not None else part.name()
    vh_list = []
    # iterate through virtualhelix list
    for row, col in helix_order_list:
        vh = part.virtualHelixAtCoord((row, col))
        # insertions and skips
        insertion_dict = part.insertions()[(row, col)]
        insts = [0 for i in range(num_bases)]
        skips = [0 for i in range(num_bases)]
        for idx, insertion in insertion_dict.items():
            if insertion.isSkip():
                skips[idx] = insertion.length()
            else:
                insts[idx] = insertion.length()
        # colors
        stap_colors = []
        stap_strandset = vh.stapleStrandSet()
        for strand in stap_strandset:
            if strand.connection5p() is None:
                c = str(strand.oligo().getColor())[1:]  # drop the hash
                stap_colors.append([strand.idx5Prime(), int(c, 16)])

        vh_dict = {"row": row,
                  "col": col,
                  "num": vh.number(),
                  "scaf": vh.getLegacyStrandSetArray(StrandType.SCAFFOLD),
                  "stap": vh.getLegacyStrandSetArray(StrandType.STAPLE),
                  "loop": insts,
                  "skip": skips,
                  "scafLoop": [],
                  "stapLoop": [],
                  "stap_colors": stap_colors}
        vh_list.append(vh_dict)
    obj = {"name": part_name , "vstrands": vh_list}
    return obj
