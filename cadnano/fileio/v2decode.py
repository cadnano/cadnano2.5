# -*- coding: utf-8 -*-
from collections import defaultdict
from cadnano.cnenum import StrandType, LatticeType
from cadnano.part.refresholigoscmd import RefreshOligosCommand

from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen
from cadnano.color import intToColorHex
from cadnano.part.nucleicacidpart import DEFAULT_RADIUS

from .lattice import HoneycombDnaPart, SquareDnaPart

def decode(document, obj, emit_signals=False):
    """Parses a dictionary (obj) created from reading a json file and uses it
    to populate the given document with model data.
    """
    num_bases = len(obj['vstrands'][0]['scaf'])
    if num_bases % 32 == 0:
        lattice_type = LatticeType.SQUARE
    elif num_bases % 21 == 0:
        lattice_type = LatticeType.HONEYCOMB
    else:
        raise IOError("error decoding number of bases")

    part = None
    # DETERMINE MAX ROW,COL
    max_row_json = max_col_json = 0
    for helix in obj['vstrands']:
        max_row_json = max(max_row_json, int(helix['row'])+1)
        max_col_json = max(max_col_json, int(helix['col'])+1)

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
    # 2 LINES COMMENTED OUT BY NC, doesn't appear to be necessary for honeycomb
    # if delta_row & 1:
    #     delta_row += 1
    delta_column = (max_col + min_col) // 2
    if delta_column & 1:
        delta_column += 1

    # print("Found cadnano version 2 file")
    # print("\trows(%d, %d): avg: %d" % (min_row, max_row, delta_row))
    # print("\tcolumns(%d, %d): avg: %d" % (min_col, max_col, delta_column))

    for helix in obj['vstrands']:
        vh_num = helix['num']
        row = helix['row']
        col = helix['col']
        scaf= helix['scaf']
        # align row and columns to the center 0, 0
        coord = (row -  delta_row, col - delta_column)
        vh_num_to_coord[vh_num] = coord
        ordered_id_list.append(vh_num)
    # end for

    # make sure we retain the original order
    radius = DEFAULT_RADIUS
    for vh_num in sorted(vh_num_to_coord.keys()):
        row, col = vh_num_to_coord[vh_num]
        x, y = doLattice(radius, row, col)
        # print("%d:" % vh_num, x, y)
        part.createVirtualHelix(x, y, 0., num_bases,
                                id_num=vh_num, use_undostack=False)
    # zoom to fit
    if emit_signals:
        part.partZDimensionsChangedSignal.emit(part, *part.zBoundsIds(), True)
    if not getReopen():
        setBatch(False)
    part.setImportedVHelixOrder(ordered_id_list)
    setReopen(False)
    setBatch(False)

    # INSTALL STRANDS AND COLLECT XOVER LOCATIONS
    scaf_seg = defaultdict(list)
    scaf_xo = defaultdict(list)
    stap_seg = defaultdict(list)
    stap_xo = defaultdict(list)
    try:
        for helix in obj['vstrands']:
            vh_num = helix['num']
            row, col = vh_num_to_coord[vh_num]
            scaf = helix['scaf']
            stap = helix['stap']
            insertions = helix['loop']
            skips = helix['skip']

            if isEven(row, col):
                scaf_strand_set, stap_strand_set = part.getStrandSets(vh_num)
            else:
                stap_strand_set, scaf_strand_set = part.getStrandSets(vh_num)

            # validate file serialization of lists
            assert( len(scaf) == len(stap) and
                    len(scaf) == len(insertions) and
                    len(insertions) == len(skips) )

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
            part.refreshSegments(vh_num)
        # end for
    except AssertionError:
        print("Unrecognized file format.")
        raise

    # INSTALL XOVERS
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row, col = vh_num_to_coord[vh_num]

        if isEven(row, col):
            scaf_strand_set, stap_strand_set = part.getStrandSets(vh_num)
        else:
            stap_strand_set, scaf_strand_set = part.getStrandSets(vh_num)

        # install scaffold xovers
        for (idx5p, to_vh_num, idx3p) in scaf_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            try:
                strand5p = scaf_strand_set.getStrand(idx5p)
            except:
                print(vh_num, idx5p)
                print(scaf_strand_set.strand_heap)
                print(stap_strand_set.strand_heap)
                raise
            coord = vh_num_to_coord[to_vh_num]
            if isEven(*coord):
                to_scaf_strand_set, to_stap_strand_set = part.getStrandSets(to_vh_num)
            else:
                to_stap_strand_set, to_scaf_strand_set = part.getStrandSets(to_vh_num)
            strand3p = to_scaf_strand_set.getStrand(idx3p)
            part.createXover(   strand5p, idx5p,
                                strand3p, idx3p,
                                update_oligo=False,
                                use_undostack=False)

        # install staple xovers
        for (idx5p, to_vh_num, idx3p) in stap_xo[vh_num]:
            # idx3p is 3' end of strand5p, idx5p is 5' end of strand3p
            strand5p = stap_strand_set.getStrand(idx5p)
            coord = vh_num_to_coord[to_vh_num]
            if isEven(*coord):
                to_scaf_strand_set, to_stap_strand_set = part.getStrandSets(to_vh_num)
            else:
                to_stap_strand_set, to_scaf_strand_set = part.getStrandSets(to_vh_num)
            strand3p = to_stap_strand_set.getStrand(idx3p)
            part.createXover(   strand5p, idx5p,
                                strand3p, idx3p,
                                update_oligo=False,
                                use_undostack=False)

    # need to heal all oligo connections into a continuous
    # oligo for the next steps
    RefreshOligosCommand(part).redo()

    # COLORS, INSERTIONS, SKIPS
    for helix in obj['vstrands']:
        vh_num = helix['num']
        row, col = vh_num_to_coord[vh_num]
        scaf = helix['scaf']
        stap = helix['stap']
        insertions = helix['loop']
        skips = helix['skip']

        if isEven(row, col):
            scaf_strand_set, stap_strand_set = part.getStrandSets(vh_num)
        else:
            stap_strand_set, scaf_strand_set = part.getStrandSets(vh_num)

        # install insertions and skips
        for base_idx in range(len(stap)):
            sum_of_insert_skip = insertions[base_idx] + skips[base_idx]
            if sum_of_insert_skip != 0:
                strand = scaf_strand_set.getStrand(base_idx)
                strand.addInsertion(base_idx,
                                    sum_of_insert_skip,
                                    use_undostack=False)
        # end for
        # populate colors
        for base_idx, color_number in helix['stap_colors']:
            color = intToColorHex(color_number)
            strand = stap_strand_set.getStrand(base_idx)
            strand.oligo().applyColor(color, use_undostack=False)

    if 'oligos' in obj:
        for oligo in obj['oligos']:
            vh_num = oligo['vh_num']
            idx = oligo['idx']
            seq = str(oligo['seq']) if oligo['seq'] is not None else ''
            if seq != '':
                coord = vh_num_to_coord[vh_num]
                if isEven(*coord):
                    scaf_ss, stap_ss = part.getStrandSets(vh_num)
                else:
                    stap_ss, scaf_ss = part.getStrandSets(vh_num)
                strand = scaf_ss.getStrand(idx)
                # print "sequence", seq, vh, idx,  strand.oligo()._strand5p
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
        for key, mid in obj['modifications']['int_instances'].items():
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