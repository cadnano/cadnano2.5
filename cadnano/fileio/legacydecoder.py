from collections import defaultdict

from cadnano import preferences as prefs
from cadnano.color import intToColorHex
from cadnano.document import Document
from cadnano.enum import LatticeType, StrandType
from .lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.virtualhelix import VirtualHelix


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

def import_legacy_dict(document, obj, lattice_type=LatticeType.HONEYCOMB):
    """
    Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    num_bases = len(obj['vstrands'][0]['scaf'])

    # DETERMINE MAX ROW,COL
    max_row_json = max_col_json = 0
    for helix in obj['vstrands']:
        max_row_json = max(max_row_json, int(helix['row'])+1)
        max_col_json = max(max_col_json, int(helix['col'])+1)

    # CREATE PART ACCORDING TO LATTICE TYPE
    if lattice_type == LatticeType.HONEYCOMB:
        steps = num_bases/21
        part = HoneycombPart(document=document)
    elif lattice_type == LatticeType.SQUARE:
        isSQ100 = True  # check for custom SQ100 format
        for helix in obj['vstrands']:
            if helix['col'] != 0:
                isSQ100 = False
                break
        if isSQ100:
            dialogLT.label.setText("Is this a SQ100 file?")
            if dialog.exec_() == 1:
                n_rows, n_cols = 100, 1
            else:
                n_rows, n_cols = 40, 30
        else:
            n_rows, n_cols = 40, 30
        steps = num_bases/32
        n_rows = max(30, max_row_json, prefs.SQUARE_PART_MAXROWS)
        n_cols = max(32, max_col_json, prefs.SQUARE_PART_MAXCOLS)
        part = SquarePart(document=document, max_row=n_rows, max_col=n_cols, max_steps=steps)
    else:
        raise TypeError("Lattice type not recognized")
    document._addPart(part, use_undostack=False)

    # POPULATE VIRTUAL HELICES
    ordered_coord_list = []
    vh_num_to_coord = {}
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        scaf= helix['scaf']
        coord = (row, col)
        vh_num_to_coord[vh_num] = coord
        ordered_coord_list.append(coord)
    # make sure we retain the original order
    for vh_num in sorted(vh_num_to_coord.keys()):
        row, col = vh_num_to_coord[vh_num]
        part.createVirtualHelix(row, col, use_undostack=False)
    part.setImportedVHelixOrder(ordered_coord_list)

    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    num_helixes = len(obj['vstrands'])-1
    scaf_seg = defaultdict(list)
    scaf_xo = defaultdict(list)
    stap_seg = defaultdict(list)
    stap_xo = defaultdict(list)
    try:
        for helix in obj['vstrands']:
            vh_num = helix['num']
            row = helix['row']
            col = helix['col']
            scaf = helix['scaf']
            stap = helix['stap']
            insertions = helix['loop']
            skips = helix['skip']
            vh = part.virtualHelixAtCoord((row, col))
            scaf_strand_set = vh.scaffoldStrandSet()
            stap_strand_set = vh.stapleStrandSet()
            assert(len(scaf)==len(stap) and len(stap)==part.maxBaseIdx()+1 and\
                   len(scaf)==len(insertions) and len(insertions)==len(skips))
            # read scaffold segments and xovers
            for i in range(len(scaf)):
                five_vh, five_idx, three_vh, three_idx = scaf[i]
                if five_vh == -1 and three_vh == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.SCAFFOLD, vh_num, i, five_vh,\
                                       five_idx, three_vh, three_idx):
                    scaf_seg[vh_num].append(i)
                if five_vh != vh_num and three_vh != vh_num:  # special case
                    scaf_seg[vh_num].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.SCAFFOLD, vh_num, i, three_vh, three_idx):
                    scaf_xo[vh_num].append((i, three_vh, three_idx))
            assert (len(scaf_seg[vh_num]) % 2 == 0)
            # install scaffold segments
            for i in range(0, len(scaf_seg[vh_num]), 2):
                lowIdx = scaf_seg[vh_num][i]
                highIdx = scaf_seg[vh_num][i+1]
                scaf_strand_set.createStrand(lowIdx, highIdx, use_undostack=False)
            # read staple segments and xovers
            for i in range(len(stap)):
                five_vh, five_idx, three_vh, three_idx = stap[i]
                if five_vh == -1 and three_vh == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.STAPLE, vh_num, i, five_vh,\
                                       five_idx, three_vh, three_idx):
                    stap_seg[vh_num].append(i)
                if five_vh != vh_num and three_vh != vh_num:  # special case
                    stap_seg[vh_num].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.STAPLE, vh_num, i, three_vh, three_idx):
                    stap_xo[vh_num].append((i, three_vh, three_idx))
            assert (len(stap_seg[vh_num]) % 2 == 0)
            # install staple segments
            for i in range(0, len(stap_seg[vh_num]), 2):
                lowIdx = stap_seg[vh_num][i]
                highIdx = stap_seg[vh_num][i+1]
                stap_strand_set.createStrand(lowIdx, highIdx, use_undostack=False)
    except AssertionError:
        print("Unrecognized file format.")
        raise

    # INSTALL XOVERS
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        scaf = helix['scaf']
        stap = helix['stap']
        insertions = helix['loop']
        skips = helix['skip']
        fromVh = part.virtualHelixAtCoord((row, col))
        scaf_strand_set = fromVh.scaffoldStrandSet()
        stap_strand_set = fromVh.stapleStrandSet()
        # install scaffold xovers
        for (idx5p, toVhNum, idx3p) in scaf_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = scaf_strand_set.getStrand(idx5p)
            toVh = part.virtualHelixAtCoord(vh_num_to_coord[toVhNum])
            strand3p = toVh.scaffoldStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, use_undostack=False)
        # install staple xovers
        for (idx5p, toVhNum, idx3p) in stap_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = stap_strand_set.getStrand(idx5p)
            toVh = part.virtualHelixAtCoord(vh_num_to_coord[toVhNum])
            strand3p = toVh.stapleStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, use_undostack=False)

    # SET DEFAULT COLOR
    for oligo in part.oligos():
        if oligo.isStaple():
            default_color = styles.DEFAULT_STAP_COLOR
        else:
            default_color = styles.DEFAULT_SCAF_COLOR
        oligo.applyColor(default_color, use_undostack=False)

    # COLORS, INSERTIONS, SKIPS
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        scaf = helix['scaf']
        stap = helix['stap']
        insertions = helix['loop']
        skips = helix['skip']
        vh = part.virtualHelixAtCoord((row, col))
        scaf_strand_set = vh.scaffoldStrandSet()
        stap_strand_set = vh.stapleStrandSet()
        # install insertions and skips
        for base_idx in range(len(stap)):
            sum_of_insert_skip = insertions[base_idx] + skips[base_idx]
            if sum_of_insert_skip != 0:
                strand = scaf_strand_set.getStrand(base_idx)
                strand.addInsertion(base_idx, sum_of_insert_skip, use_undostack=False)
        # end for
        # populate colors
        for base_idx, color_number in helix['STAP_COLORS']:
            color = intToColorHex(color_number)
            strand = stap_strand_set.getStrand(base_idx)
            strand.oligo().applyColor(color, use_undostack=False)

def isSegmentStartOrEnd(strandType, vh_num, base_idx, five_vh, five_idx, three_vh, three_idx):
    """Returns True if the base is a breakpoint or crossover."""
    if strandType == StrandType.SCAFFOLD:
        offset = 1
    else:
        offset = -1
    if (five_vh == vh_num and three_vh != vh_num):
        return True
    if (five_vh != vh_num and three_vh == vh_num):
        return True
    if (vh_num % 2 == 0 and five_vh == vh_num and five_idx != base_idx-offset):
        return True
    if (vh_num % 2 == 0 and three_vh == vh_num and three_idx != base_idx+offset):
        return True
    if (vh_num % 2 == 1 and five_vh == vh_num and five_idx != base_idx+offset):
        return True
    if (vh_num % 2 == 1 and three_vh == vh_num and three_idx != base_idx-offset):
        return True
    if (five_vh == -1 and three_vh != -1):
        return True
    if (five_vh != -1 and three_vh == -1):
        return True
    return False

def is3primeXover(strandType, vh_num, base_idx, three_vh, three_idx):
    """Returns True of the three_vh doesn't match vh_num, or three_idx
    is not a natural neighbor of base_idx."""
    if three_vh == -1:
        return False
    if vh_num != three_vh:
        return True
    if strandType == StrandType.SCAFFOLD:
        offset = 1
    else:
        offset = -1
    if (vh_num % 2 == 0 and three_vh == vh_num and three_idx != base_idx+offset):
        return True
    if (vh_num % 2 == 1 and three_vh == vh_num and three_idx != base_idx-offset):
        return True
    return False
