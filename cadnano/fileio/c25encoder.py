
from os.path import basename

from cadnano.enum import StrandType

def c25_dict_from_doc(document, fname, helix_order_list):
    part = document.selectedInstance().reference()

    # iterate through virtualhelix list
    vh_list = []
    for row, col in helix_order_list:
        vh = part.virtualHelixAtCoord((row, col))
        num_bases = vh.getProperty('_max_length')
        # insertions and deletions
        insertion_dict = part.insertions()[(row, col)]
        insertions = [0 for i in range(num_bases)]
        deletions = [0 for i in range(num_bases)]
        for idx, insertion in insertion_dict.items():
            if insertion.isSkip():
                deletions[idx] = insertion.length()
            else:
                insertions[idx] = insertion.length()
        # colors
        colors = []
        for strand in vh.fwdStrandSet():
            if strand.connection5p() is None:
                color = strand.oligo().getColor()
                colors.append([0, strand.idx5Prime(), color])
        for strand in vh.revStrandSet():
            if strand.connection5p() is None:
                color = strand.oligo().getColor()
                colors.append([1, strand.idx5Prime(), color])

        vh_dict = {'row': row,
                  'col': col,
                  'num': vh.number(),
                  'fwd_ss': vh.getLegacyStrandSetArray(StrandType.SCAFFOLD),
                  'rev_ss': vh.getLegacyStrandSetArray(StrandType.STAPLE),
                  'insertions': insertions,
                  'deletions': deletions,
                  'colors': colors,
                  'x':vh.getProperty('x'),
                  'y':vh.getProperty('y'),
                  'z':vh.getProperty('z'),
                  'eulerZ':vh.getProperty('eulerZ'),
                  'bases_per_repeat':vh.getProperty('bases_per_repeat'),
                  'turns_per_repeat':vh.getProperty('turns_per_repeat'),
                  'repeats':vh.getProperty('repeats')
                  }
        vh_list.append(vh_dict)
    bname = basename(str(fname))
    obj = {"name": bname , "vstrands": vh_list}
    return obj
