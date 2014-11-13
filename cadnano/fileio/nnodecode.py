# -*- coding: utf-8 -*-
from collections import defaultdict
import json
import io

from cadnano.document import Document
from cadnano.enum import LatticeType, StrandType
from cadnano.color import Color
import cadnano.preferences as prefs
from cadnano import setBatch, getReopen, setReopen
from cadnano.part.refresholigoscmd import RefreshOligosCommand

def decodeFile(filename, document=None):
    with io.open(filename, 'r', encoding='utf-8') as fd:
        nno_dict = json.load(fd)
    if document is None:
        document = Document()
    decode(document, nno_dict)
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

def decode(document, obj):
    """
    Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    num_bases = len(obj['vstrands'][0]['scaf'])
    if num_bases % 32 == 0:
        lattice_type = LatticeType.SQUARE
    elif num_bases % 21 == 0:
        lattice_type = LatticeType.HONEYCOMB
    else:
        raise IOError("error decoding number of bases")


    # DETERMINE MAX ROW,COL
    max_row_json = max_col_json = 0
    for helix in obj['vstrands']:
        max_row_json = max(max_row_json, int(helix['row'])+1)
        max_col_json = max(max_col_json, int(helix['col'])+1)

    # CREATE PART ACCORDING TO LATTICE TYPE
    if lattice_type == LatticeType.HONEYCOMB:
        steps = num_bases // 21
        # num_rows = max(30, max_row_json, cadnano.app().prefs.honeycombRows)
        # num_cols = max(32, max_col_json, cadnano.app().prefs.honeycombCols)
        num_rows = max(30, max_row_json, prefs.HONEYCOMB_PART_MAXROWS)
        num_cols = max(32, max_col_json, prefs.HONEYCOMB_PART_MAXCOLS)
        part = document.addHoneycombPart(num_rows, num_cols, steps)
    elif lattice_type == LatticeType.SQUARE:
        is_SQ_100 = True  # check for custom SQ100 format
        for helix in obj['vstrands']:
            if helix['col'] != 0:
                is_SQ_100 = False
                break
        if is_SQ_100:
            # num_rows, num_cols = 100, 1
            num_rows, num_cols = 40, 30
        else:
            num_rows, num_cols = 40, 30
        steps = num_bases // 32
        # num_rows = max(30, max_row_json, cadnano.app().prefs.squareRows)
        # num_cols = max(32, max_col_json, cadnano.app().prefs.squareCols)
        num_rows = max(30, max_row_json, prefs.SQUARE_PART_MAXROWS)
        num_cols = max(32, max_col_json, prefs.SQUARE_PART_MAXCOLS)
        part = document.addSquarePart(num_rows, num_cols, steps)
        # part = SquarePart(document=document, max_row=num_rows, max_col=num_cols, max_steps=steps)
    else:
        raise TypeError("Lattice type not recognized")
    # document._addPart(part, use_undostack=False)
    setBatch(True)
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
    if not getReopen():
        setBatch(False)
    part.setImportedVHelixOrder(ordered_coord_list)
    setReopen(False)
    setBatch(False)
    
    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    num_helices = len(obj['vstrands']) - 1
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
            assert(len(scaf) == len(stap) and len(stap) == part.maxBaseIdx() + 1 and\
                   len(scaf) == len(insertions) and len(insertions) == len(skips))
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
                low_idx = scaf_seg[vh_num][i]
                high_idx = scaf_seg[vh_num][i + 1]
                scaf_strand_set.createStrand(low_idx, high_idx, use_undostack=False)
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
                low_idx = stap_seg[vh_num][i]
                high_idx = stap_seg[vh_num][i + 1]
                stap_strand_set.createStrand(low_idx, high_idx, use_undostack=False)
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
        from_vh = part.virtualHelixAtCoord((row, col))
        scaf_strand_set = from_vh.scaffoldStrandSet()
        stap_strand_set = from_vh.stapleStrandSet()
        # install scaffold xovers
        for (idx5p, to_vh_num, idx3p) in scaf_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = scaf_strand_set.getStrand(idx5p)
            to_vh = part.virtualHelixAtCoord(vh_num_to_coord[to_vh_num])
            strand3p = to_vh.scaffoldStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, 
                update_oligo=False, use_undostack=False)
        # install staple xovers
        for (idx5p, to_vh_num, idx3p) in stap_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = stap_strand_set.getStrand(idx5p)
            to_vh = part.virtualHelixAtCoord(vh_num_to_coord[to_vh_num])
            strand3p = to_vh.stapleStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p, 
                update_oligo=False, use_undostack=False)

    # need to heal all oligo connections into a continuous
    # oligo for the next steps
    RefreshOligosCommand(part, include_scaffold=True, 
        colors=(prefs.DEFAULT_SCAF_COLOR, prefs.DEFAULT_STAP_COLOR)).redo()

    # SET DEFAULT COLOR
    # for oligo in part.oligos():
    #     if oligo.isStaple():
    #         default_color = prefs.DEFAULT_STAP_COLOR
    #     else:
    #         default_color = prefs.DEFAULT_SCAF_COLOR
    #     oligo.applyColor(default_color, use_undostack=False)

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
        for base_idx, color_number in helix['stap_colors']:
            color = Color(  (color_number >> 16) & 0xFF, 
                            (color_number >> 8) & 0xFF, 
                            color_number & 0xFF).name()
            strand = stap_strand_set.getStrand(base_idx)
            strand.oligo().applyColor(color, use_undostack=False) 

    if 'oligos' in obj:
        for oligo in obj['oligos']:
            vh_num = oligo['vh_num']
            idx = oligo['idx']
            seq = str(oligo['seq']) if oligo['seq'] is not None else ''
            if seq != '':
                coord = vh_num_to_coord[vhNum]
                vh = part.virtualHelixAtCoord(coord)
                scaf_ss = vh.scaffoldStrandSet()
                # stapStrandSet = vh.stapleStrandSet()
                strand = scaf_ss.getStrand(idx)
                # print "sequence", seq, vh, idx,  strand.oligo()._strand5p
                strand.oligo().applySequence(seq, use_undostack=False)
    if 'modifications' in obj:
        # print("AD", cadnano.app().activeDocument)
        # win = cadnano.app().activeDocument.win
        # modstool = win.pathToolManager.modsTool
        # modstool.connectSignals(part)
        for mod_id, item in obj['modifications'].items():
            if mod_id != 'int_instances' and mod_id != 'ext_instances':
                part.createMod(item, mod_id)
        for key, mid in obj['modifications']['ext_instances'].items():
            strand, idx = part.getModStrandIdx(key)
            try:
                strand.addMods(mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
        for key in obj['modifications']['int_instances'].items():
            strand, idx = part.getModStrandIdx(key)
            try:
                strand.addMods(mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
        # modstool.disconnectSignals(part)
# end def

def isSegmentStartOrEnd(strandtype, vh_num, base_idx, five_vh, five_idx, three_vh, three_idx):
    """Returns True if the base is a breakpoint or crossover."""
    if strandtype == StrandType.SCAFFOLD:
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

def is3primeXover(strandtype, vh_num, base_idx, three_vh, three_idx):
    """Returns True of the three_vh doesn't match vh_num, or three_idx
    is not a natural neighbor of base_idx."""
    if three_vh == -1:
        return False
    if vh_num != three_vh:
        return True
    if strandtype == StrandType.SCAFFOLD:
        offset = 1
    else:
        offset = -1
    if (vh_num % 2 == 0 and three_vh == vh_num and three_idx != base_idx+offset):
        return True
    if (vh_num % 2 == 1 and three_vh == vh_num and three_idx != base_idx-offset):
        return True