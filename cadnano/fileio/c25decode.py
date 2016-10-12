# -*- coding: utf-8 -*-
from collections import defaultdict
from cadnano.cnenum import StrandType, LatticeType
from cadnano.part.refresholigoscmd import RefreshOligosCommand

from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen
from cadnano.color import intToColorHex
from cadnano.part.nucleicacidpart import DEFAULT_RADIUS

from .lattice import HoneycombDnaPart, SquareDnaPart

# hard code these for version changes
PATH_BASE_WIDTH = 10
PART_BASE_WIDTH = 0.34 # nanometers, distance between bases, pith
SCALE_2_MODEL =  PART_BASE_WIDTH/PATH_BASE_WIDTH
def convertToModelZ(z):
    """ scale Z-axis coordinate to the model
    """
    return z * SCALE_2_MODEL
# end def

def decode(document, obj, emit_signals=True):
    """
    Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    num_bases = len(obj['vstrands'][0]['fwd_ss'])

    lattice_type = LatticeType.HONEYCOMB

    part = None
    # DETERMINE MAX ROW,COL
    max_row_json = max_col_json = 0
    for helix in obj['vstrands']:
        max_row_json = max(max_row_json, int(helix['row']) + 1)
        max_col_json = max(max_col_json, int(helix['col']) + 1)

    # CREATE PART ACCORDING TO LATTICE TYPE
    if lattice_type == LatticeType.HONEYCOMB:
        doLattice = HoneycombDnaPart.legacyLatticeCoordToPositionXY
        isEven = HoneycombDnaPart.isEvenParity
    elif lattice_type == LatticeType.SQUARE:
        doLattice = SquareDnaPart.legacyLatticeCoordToPositionXY
        isEven = SquareDnaPart.isEvenParity
    else:
        raise TypeError("Lattice type not recognized")
    part = document.createNucleicAcidPart(use_undostack=False)
    part.setActive(True)
    setBatch(True)
    delta = num_bases - 42
    # POPULATE VIRTUAL HELICES
    ordered_id_list = []
    property_dict = {}
    vh_num_to_coord = {}
    min_row, max_row = 10000, -10000
    min_col, max_col = 10000, -10000

    # find row, column limits
    for helix in obj['vstrands']:
        row = helix['row']
        if row < min_row:
            min_row = row
        if row > max_row:
            max_row = row
        col = helix['col']
        if col < min_col:
            min_col = col
        if col > max_col:
            max_col = col
    # end for

    delta_row = (max_row + min_row) // 2
    if delta_row & 1:
        delta_row += 1
    delta_column = (max_col + min_col) // 2
    if delta_column & 1:
        delta_column += 1

    # print("Found cadnano version 2.5 file")
    # print("\trows(%d, %d): avg: %d" % (min_row, max_row, delta_row))
    # print("\tcolumns(%d, %d): avg: %d" % (min_col, max_col, delta_column))

    encoded_keys = ['eulerZ', 'repeats', 'bases_per_repeat',
                    'turns_per_repeat', 'z']
    model_keys = ['eulerZ', 'repeat_hint', 'bases_per_repeat',
                    'turns_per_repeat', 'z']
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        # align row and columns to the center 0, 0
        coord = (row -  delta_row, col - delta_column)
        vh_num_to_coord[vh_num] = coord
        ordered_id_list.append(vh_num)
        property_dict[vh_num] = [helix[key] for key in encoded_keys]
    # end for

    radius = DEFAULT_RADIUS
    for vh_num in sorted(vh_num_to_coord.keys()):
        row, col = vh_num_to_coord[vh_num]
        x, y = doLattice(radius, row, col)
        props = property_dict[vh_num]
        z = convertToModelZ(props[-1])
        props[-1] = z
        # print("%d:" % vh_num, x, y, z)
        # print({k:v for k, v in zip(encoded_keys, props)})
        part.createVirtualHelix(x, y, z, num_bases,
                                id_num=vh_num,
                                properties=(model_keys, props),
                                use_undostack=False)
    if not getReopen():
        setBatch(False)
    part.setImportedVHelixOrder(ordered_id_list)
    # zoom to fit
    if emit_signals:
        part.partZDimensionsChangedSignal.emit(part, *part.zBoundsIds(), True)
    setReopen(False)
    setBatch(False)

    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    fwd_ss_seg = defaultdict(list)
    fwd_ss_xo = defaultdict(list)
    rev_ss_seg = defaultdict(list)
    rev_ss_xo = defaultdict(list)
    try:
        for helix in obj['vstrands']:
            vh_num = helix['num']
            row, col = vh_num_to_coord[vh_num]
            insertions = helix['insertions']
            deletions = helix['deletions']

            if isEven(row, col):
                # parity matters still despite the fwd and rev naming of
                # this format
                fwd_strandset, rev_strandset = part.getStrandSets(vh_num)
                fwd_ss = helix['fwd_ss']
                rev_ss = helix['rev_ss']
            else:
                rev_strandset, fwd_strandset = part.getStrandSets(vh_num)
                rev_ss = helix['fwd_ss']
                fwd_ss = helix['rev_ss']

            # validate file serialization of lists
            assert( len(fwd_ss) == len(rev_ss) and
                    len(fwd_ss) == len(insertions) and
                    len(insertions) == len(deletions) )

            # read fwd_strandset segments and xovers
            for i in range(len(fwd_ss)):
                five_vh, five_strand, five_idx, three_vh, three_strand, three_idx = fwd_ss[i]

                if five_vh == -1 and three_vh == -1:
                    continue  # null base
                if isSegmentStartOrEnd(StrandType.SCAFFOLD, vh_num, i,
                                        five_vh, five_idx, three_vh, three_idx):
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
                if isSegmentStartOrEnd(StrandType.STAPLE, vh_num, i,
                                        five_vh, five_idx, three_vh, three_idx):
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
            part.refreshSegments(vh_num)
        # end for
    except AssertionError:
        print("Unrecognized file format.")
        raise

    """ INSTALL XOVERS
    parity matters for the from idx but is already encoded in
    the `to_strand3p` parameter of the tuple in `fwd_ss_xo` and `rev_ss_xo`
    """
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row, col = vh_num_to_coord[vh_num]
        if isEven(row, col):
            fwd_strandset, rev_strandset = part.getStrandSets(vh_num)
        else:
            rev_strandset, fwd_strandset = part.getStrandSets(vh_num)

        # install fwd_strandset xovers
        for (idx5p, to_vh_num, to_strand3p, idx3p) in fwd_ss_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = fwd_strandset.getStrand(idx5p)
            to_fwd_strandset, to_rev_strandset = part.getStrandSets(to_vh_num)

            if to_strand3p == 0:
                strand3p = to_fwd_strandset.getStrand(idx3p)
            else:
                strand3p = to_rev_strandset.getStrand(idx3p)
            part.createXover(   strand5p, idx5p,
                                strand3p, idx3p,
                                update_oligo=False,
                                use_undostack=False)

        # install rev_strandset xovers
        for (idx5p, to_vh_num, to_strand3p, idx3p) in rev_ss_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = rev_strandset.getStrand(idx5p)
            to_fwd_strandset, to_rev_strandset = part.getStrandSets(to_vh_num)
            coord = vh_num_to_coord[to_vh_num]

            if to_strand3p == 0:
                strand3p = to_fwd_strandset.getStrand(idx3p)
            else:
                strand3p = to_rev_strandset.getStrand(idx3p)
            part.createXover(   strand5p, idx5p,
                                strand3p, idx3p,
                                update_oligo=False,
                                use_undostack=False)

    # need to heal all oligo connections into a continuous
    # oligo for the next steps
    RefreshOligosCommand(part).redo()

    # COLORS, INSERTIONS, deletions
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row, col = vh_num_to_coord[vh_num]
        fwd_ss = helix['fwd_ss']
        rev_ss = helix['rev_ss']
        insertions = helix['insertions']
        deletions = helix['deletions']

        fwd_strandset, rev_strandset = part.getStrandSets(vh_num)

        # install insertions and deletions
        for base_idx in range(len(rev_ss)):
            sum_of_insert_deletion = insertions[base_idx] + deletions[base_idx]
            if sum_of_insert_deletion != 0:
                strand = fwd_strandset.getStrand(base_idx)
                strand.addInsertion(base_idx,
                                    sum_of_insert_deletion,
                                    use_undostack=False)
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
                coord = vh_num_to_coord[vh_num]
                fwd_strandset, rev_strandset = part.getStrandSets(vh_num)
                strand = fwd_strandset.getStrand(idx)
                strand.oligo().applySequence(seq, use_undostack=False)

    if 'modifications' in obj:
        for mod_id, item in obj['modifications'].items():
            if mod_id != 'int_instances' and mod_id != 'ext_instances':
                part.createMod(item, mod_id)
        for key, mid in obj['modifications']['ext_instances'].items():
            # strand, idx, coord, isstaple = part.getModStrandIdx(key)
            strand, idx = part.getModStrandIdx(key)
            try:
                strand.addMods(document, mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
        for key in obj['modifications']['int_instances'].items():
            # strand, idx, coord, isstaple  = part.getModStrandIdx(key)
            strand, idx = part.getModStrandIdx(key)
            try:
                strand.addMods(document, mid, idx, use_undostack=False)
            except:
                print(strand, idx)
                raise
# end def

def isSegmentStartOrEnd(strandtype, vh_num, base_idx,
                        five_vh, five_idx,
                        three_vh, three_idx):
    """
    Returns:
        bool: True if the base is a breakpoint or crossover.
    """
    if strandtype == StrandType.SCAFFOLD:
        offset = 1
    else:
        offset = -1
    if five_vh == vh_num and three_vh != vh_num:
        return True
    if five_vh != vh_num and three_vh == vh_num:
        return True
    if (vh_num % 2 == 0 and five_vh == vh_num and
        five_idx != base_idx - offset):
        return True
    if (vh_num % 2 == 0 and three_vh == vh_num and
        three_idx != base_idx + offset):
        return True
    if (vh_num % 2 == 1 and five_vh == vh_num and
        five_idx != base_idx + offset):
        return True
    if (vh_num % 2 == 1 and three_vh == vh_num and
        three_idx != base_idx - offset):
        return True
    if five_vh == -1 and three_vh != -1:
        return True
    if five_vh != -1 and three_vh == -1:
        return True
    return False
# end def

def is3primeXover(strandtype, vh_num, base_idx, three_vh, three_idx):
    """
    Returns:
        bool: True of the three_vh doesn't match vh_num, or three_idx
                is not a natural neighbor of base_idx.
    """
    if three_vh == -1:
        return False
    if vh_num != three_vh:
        return True
    if strandtype == StrandType.SCAFFOLD:
        offset = 1
    else:
        offset = -1
    if (vh_num % 2 == 0 and three_vh == vh_num and
        three_idx != base_idx + offset):
        return True
    if (vh_num % 2 == 1 and three_vh == vh_num and
        three_idx != base_idx - offset):
        return True
# end def