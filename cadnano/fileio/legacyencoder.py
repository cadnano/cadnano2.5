
from os.path import basename

from cadnano.enum import StrandType

def legacy_dict_from_doc(document, fname, helix_order_list):
    part = document.selectedInstance().reference()
    num_bases = part.maxBaseIdx()+1

    # iterate through virtualhelix list
    vh_list = []
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
    bname = basename(str(fname))
    obj = {"name": bname , "vstrands": vh_list}
    return obj
