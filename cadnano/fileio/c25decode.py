# -*- coding: utf-8 -*-
from collections import defaultdict
import json
import io

from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen
from cadnano.document import Document
from cadnano.enum import LatticeType, StrandType
from cadnano.part.refresholigoscmd import RefreshOligosCommand

def decodeFile(filename, document=None):
    with io.open(filename, 'r', encoding='utf-8') as fd:
        c25_dict = json.load(fd)
    if document is None:
        document = Document()
    decode(document, c25_dict)
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
SCAFFOLD = "fwd_strandset"
STAPLE = "rev_strandset"
INSERTION = "insertion"
DELETION = "deletion"

def decode(document, obj):
    """
    Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    num_bases = len(obj['vstrands'][0]['fwd_ss'])
    lattice_type = LatticeType.HONEYCOMB

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
        num_rows = max(10, max_row_json, prefs.HONEYCOMB_PART_MAXROWS)
        num_cols = max(18, max_col_json, prefs.HONEYCOMB_PART_MAXCOLS)
        part = document.addHoneycombDnaPart(max_row=num_rows, max_col=num_cols, max_steps=steps)

    # document._addPart(part, use_undostack=False)
    setBatch(True)
    # POPULATE VIRTUAL HELICES
    ordered_coord_list = []
    vh_num_to_coord = {}
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
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

    # SET PROPERTIES
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        vh = part.virtualHelixAtCoord((row, col))
        for key in ['x', 'y', 'z', 'eulerZ', 'repeats', 'bases_per_repeat', 'turns_per_repeat']:
            vh.setProperty(key, helix[key])

    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    num_helices = len(obj['vstrands']) - 1
    fwd_ss_seg = defaultdict(list)
    fwd_ss_xo = defaultdict(list)
    rev_ss_seg = defaultdict(list)
    rev_ss_xo = defaultdict(list)
    try:
        for helix in obj['vstrands']:
            vh_num = helix['num']
            row = helix['row']
            col = helix['col']
            fwd_ss = helix['fwd_ss']
            rev_ss = helix['rev_ss']
            insertions = helix['insertions']
            deletions = helix['deletions']
            vh = part.virtualHelixAtCoord((row, col))
            fwd_strandset = vh.fwdStrandSet()
            rev_strandset = vh.revStrandSet()
            assert(len(fwd_ss) == len(rev_ss) and \
                   len(fwd_ss) == len(insertions) and len(insertions) == len(deletions))
            # read fwd_strandset segments and xovers
            for i in range(len(fwd_ss)):
                five_vh, five_strand, five_idx, three_vh, three_strand, three_idx = fwd_ss[i]
                if five_vh == -1 and three_vh == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.SCAFFOLD, vh_num, i, five_vh,\
                                       five_idx, three_vh, three_idx):
                    fwd_ss_seg[vh_num].append(i)
                if five_vh != vh_num and three_vh != vh_num:  # special case
                    fwd_ss_seg[vh_num].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.SCAFFOLD, vh_num, i, three_vh, three_idx):
                    fwd_ss_xo[vh_num].append((i, three_vh, three_strand, three_idx))
            assert (len(fwd_ss_seg[vh_num]) % 2 == 0)
            # install fwd_strandset segments
            for i in range(0, len(fwd_ss_seg[vh_num]), 2):
                low_idx = fwd_ss_seg[vh_num][i]
                high_idx = fwd_ss_seg[vh_num][i + 1]
                fwd_strandset.createStrand(low_idx, high_idx, use_undostack=False)
            # read rev_strandset segments and xovers
            for i in range(len(rev_ss)):
                five_vh, five_strand, five_idx, three_vh, three_strand, three_idx = rev_ss[i]
                if five_vh == -1 and three_vh == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.STAPLE, vh_num, i, five_vh,\
                                       five_idx, three_vh, three_idx):
                    rev_ss_seg[vh_num].append(i)
                if five_vh != vh_num and three_vh != vh_num:  # special case
                    rev_ss_seg[vh_num].append(i)  # end segment on a double crossover
                if is3primeXover(StrandType.STAPLE, vh_num, i, three_vh, three_idx):
                    rev_ss_xo[vh_num].append((i, three_vh, three_strand, three_idx))
            assert (len(rev_ss_seg[vh_num]) % 2 == 0)
            # install rev_strandset segments
            for i in range(0, len(rev_ss_seg[vh_num]), 2):
                low_idx = rev_ss_seg[vh_num][i]
                high_idx = rev_ss_seg[vh_num][i + 1]
                rev_strandset.createStrand(low_idx, high_idx, use_undostack=False)
    except AssertionError:
        print("Unrecognized file format.")
        raise

    # INSTALL XOVERS
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        fwd_ss = helix['fwd_ss']
        rev_ss = helix['rev_ss']
        insertions = helix['insertions']
        deletions = helix['deletions']
        from_vh = part.virtualHelixAtCoord((row, col))
        fwd_strandset = from_vh.fwdStrandSet()
        rev_strandset = from_vh.revStrandSet()

        # install fwd_strandset xovers
        for (idx5p, to_vh_num, to_strand3p, idx3p) in fwd_ss_xo[vh_num]:
            print(idx5p, to_vh_num, to_strand3p, idx3p)
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = fwd_strandset.getStrand(idx5p)
            to_vh = part.virtualHelixAtCoord(vh_num_to_coord[to_vh_num])
            if to_strand3p == 0:
                strand3p = to_vh.fwdStrandSet().getStrand(idx3p)
            else:
                strand3p = to_vh.revStrandSet().getStrand(idx3p)
            part.createXover(strand5p, idx5p, strand3p, idx3p,
                update_oligo=False, use_undostack=False)
        # install rev_strandset xovers
        for (idx5p, to_vh_num, to_strand3p, idx3p) in rev_ss_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = rev_strandset.getStrand(idx5p)
            to_vh = part.virtualHelixAtCoord(vh_num_to_coord[to_vh_num])
            if to_strand3p == 0:
                strand3p = to_vh.fwdStrandSet().getStrand(idx3p)
            else:
                strand3p = to_vh.revStrandSet().getStrand(idx3p)
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
        fwd_ss = helix['fwd_ss']
        rev_ss = helix['rev_ss']
        insertions = helix['insertions']
        deletions = helix['deletions']
        vh = part.virtualHelixAtCoord((row, col))
        fwd_strandset = vh.fwdStrandSet()
        rev_strandset = vh.revStrandSet()
        # install insertions and deletions
        for base_idx in range(len(rev_ss)):
            sum_of_insert_deletion = insertions[base_idx] + deletions[base_idx]
            if sum_of_insert_deletion != 0:
                strand = fwd_strandset.getStrand(base_idx)
                strand.addInsertion(base_idx, sum_of_insert_deletion, use_undostack=False)
        # end for
        # populate colors
        for strand_type, base_idx, color in helix['colors']:
            strandset = fwd_strandset if strand_type == 0 else rev_strandset
            strand = strandset.getStrand(base_idx) 
            strand.oligo().applyColor(color, use_undostack=False)


    if 'oligos' in obj:
        for oligo in obj['oligos']:
            vh_num = oligo['vh_num']
            idx = oligo['idx']
            seq = str(oligo['seq']) if oligo['seq'] is not None else ''
            if seq != '':
                coord = vh_num_to_coord[vhNum]
                vh = part.virtualHelixAtCoord(coord)
                fwd_ss_ss = vh.fwdStrandSet()
                # rev_ssStrandSet = vh.revStrandSet()
                strand = fwd_ss_ss.getStrand(idx)
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
            strand, idx, coord, isrev_strandset = part.getModStrandIdx(key)
            try:
                strand.addMods(mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
        for key in obj['modifications']['int_instances'].items():
            strand, idx, coord, isrev_strandset  = part.getModStrandIdx(key)
            try:
                strand.addMods(mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
        # modstool.disconnectSignals(part)
# end def

def isSegmentStartOrEnd(strand_type, vh_num, base_idx, five_vh, five_idx, three_vh, three_idx):
    """Returns True if the base is a breakpoint or crossover."""
    # ENDPOINT: 5' base is null, 3' base exists
    if (five_vh == -1 and three_vh != -1):
        return True
    # ENDPOINT: 5' base exists, 3' base is null
    if (five_vh != -1 and three_vh == -1):
        return True

    # XOVER: 5' base is on this helix, 3' base is not
    if (five_vh == vh_num and three_vh != vh_num):
        return True
    # XOVER: 5' base is not on this helix, 3' base is
    if (five_vh != vh_num and three_vh == vh_num):
        return True

    # Check for unexpected index (probably XOVER within same VH)
    if strand_type == StrandType.SCAFFOLD: # FWD strand
        if (five_vh == vh_num and five_idx != base_idx-1):
            return True
        if (three_vh == vh_num and three_idx != base_idx+1):
            return True
    else: # REV strand
        if (five_vh == vh_num and five_idx != base_idx+1):
            return True
        if (three_vh == vh_num and three_idx != base_idx-1):
            return True
    return False
# end def

def is3primeXover(strandtype, vh_num, base_idx, three_vh, three_idx):
    """Returns True of the three_vh doesn't match vh_num, or three_idx
    is not a natural neighbor of base_idx."""
    if three_vh == -1:
        return False
    if vh_num != three_vh:
        return True
    offset = 1 if (strandtype is StrandType.SCAFFOLD) else -1
    if (three_vh == vh_num and three_idx != base_idx+offset):
        return True
# end def
