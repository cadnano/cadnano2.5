# -*- coding: utf-8 -*-
from cadnano.proxies.cnenum import GridType
from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart

FORMAT_VERSION = "2.0"
ROW_OFFSET = 0
COL_OFFSET = 0
# DEFAULT_ROWS = 30
# DEFAULT_COLS = 32


def encodeDocument(document):

    grid_type = document.getGridType()

    if grid_type is GridType.HONEYCOMB or grid_type is None:
        grid_type = GridType.HONEYCOMB
        positionToLatticeCoord = HoneycombDnaPart.positionQtToLatticeCoord
        positionToLatticeCoordRound = HoneycombDnaPart.positionToLatticeCoordRound
    else:
        grid_type = GridType.SQUARE
        positionToLatticeCoord = SquareDnaPart.positionQtToLatticeCoord
        positionToLatticeCoordRound = SquareDnaPart.positionToLatticeCoordRound

    part = next(document.getParts())
    radius = part.radius()

    # Attempt to shift the design to the center of the lattice
    # height = abs(rowLL-rowUR)
    # width = abs(colLL-colUR)
    # delta_row = (DEFAULT_ROWS-height)//2
    # if delta_row % 2 == 1:
    #     delta_row += 1
    # delta_col = (DEFAULT_COLS-width)//2
    # print("Shifting each (row,col) by ({0},{1})".format(delta_row, delta_col))

    insertions = part.insertions()
    vh_order = part.getVirtualHelixOrder()
    name = "legacy-export-cn25"
    max_base_idx = max([part.maxBaseIdx(id_num) for id_num in vh_order])

    # print("Translating vh:(row,col) to legacy coordinates...")

    min_row = float('inf')
    min_col = float('inf')

    # Iterate over VHs to determine which one should be at the lattice
    # coordinates (0, 0)
    for id_num in vh_order:
        vh_x, vh_y = part.getVirtualHelixOrigin(id_num)
        row, col = positionToLatticeCoord(radius, vh_x, vh_y)

        min_row = min(row, min_row)
        min_col = min(col, min_col)

    row_offset = abs(min_row)
    col_offset = abs(min_col)

    if row_offset % 2 != 0:
        row_offset += 1
    if col_offset % 2 != 0:
        col_offset += 1

    # Iterate through virtualhelix list
    vh_list = []
    for id_num in vh_order:
        fwd_ss, rev_ss = part.getStrandSets(id_num)

        # Insertions and skips
        insertion_dict = insertions[id_num]
        insts = [0 for i in range(max_base_idx)]
        skips = [0 for i in range(max_base_idx)]
        for idx, insertion in insertion_dict.items():
            if insertion.isSkip():
                skips[idx] = insertion.length()
            else:
                insts[idx] = insertion.length()

        if id_num % 2 == 0:
            scaf_ss, stap_ss = fwd_ss, rev_ss
        else:
            scaf_ss, stap_ss = rev_ss, fwd_ss  # noqa

        # Colors
        stap_colors = []
        for strand in stap_ss:
            if strand.connection5p() is None:
                c = str(strand.oligo().getColor())[1:]  # drop the hash
                stap_colors.append([strand.idx5Prime(), int(c, 16)])

        # Convert x,y coordinates to new (row, col)
        vh_x, vh_y = part.getVirtualHelixOrigin(id_num)
        row, col = positionToLatticeCoord(radius, vh_x, vh_y)

        new_row = row + row_offset
        new_col = col + col_offset

        # print("{0:>2}: ({1:>2},{2:>2}) -> ({3:>2},{4:>2})".format(id_num, row, col, new_row, new_col))

        # Put everything together in a new dict
        vh_dict = {"row": new_row,
                   "col": new_col,
                   "num": id_num,
                   "scaf": getLegacyStrandSetArray(scaf_ss, max_base_idx),
                   "stap": getLegacyStrandSetArray(stap_ss, max_base_idx),
                   "loop": insts,
                   "skip": skips,
                   "scafLoop": [],
                   "stapLoop": [],
                   "stap_colors": stap_colors}
        vh_list.append(vh_dict)
    obj = {"name": name, "sequenceOffset": part.getSequenceOffset(), "vstrands": vh_list}
    return obj


def getLegacyStrandSetArray(ss, max_base_idx):
    """Given a strandset and max_base_idx, return legacy serialization array format."""
    num = ss.idNum()
    ret = [[-1, -1, -1, -1] for i in range(max_base_idx)]
    if ss.isForward():
        for strand in ss.strands():
            lo, hi = strand.idxs()
            assert strand.idx5Prime() == lo and strand.idx3Prime() == hi
            # map the first base (5' xover if necessary)
            s5p = strand.connection5p()
            if s5p is not None:
                ret[lo][0] = s5p.idNum()
                ret[lo][1] = s5p.idx3Prime()
            ret[lo][2] = num
            ret[lo][3] = lo + 1
            # map the internal bases
            for idx in range(lo + 1, hi):
                ret[idx][0] = num
                ret[idx][1] = idx - 1
                ret[idx][2] = num
                ret[idx][3] = idx + 1
            # map the last base (3' xover if necessary)
            ret[hi][0] = num
            ret[hi][1] = hi - 1
            s3p = strand.connection3p()
            if s3p is not None:
                ret[hi][2] = s3p.idNum()
                ret[hi][3] = s3p.idx5Prime()
            # end if
        # end for
    # end if
    else:
        for strand in ss.strands():
            lo, hi = strand.idxs()
            assert strand.idx3Prime() == lo and strand.idx5Prime() == hi
            # map the first base (3' xover if necessary)
            ret[lo][0] = num
            ret[lo][1] = lo + 1
            s3p = strand.connection3p()
            if s3p is not None:
                ret[lo][2] = s3p.idNum()
                ret[lo][3] = s3p.idx5Prime()
            # map the internal bases
            for idx in range(lo + 1, hi):
                ret[idx][0] = num
                ret[idx][1] = idx + 1
                ret[idx][2] = num
                ret[idx][3] = idx - 1
            # map the last base (5' xover if necessary)
            ret[hi][2] = num
            ret[hi][3] = hi - 1
            s5p = strand.connection5p()
            if s5p is not None:
                ret[hi][0] = s5p.idNum()
                ret[hi][1] = s5p.idx3Prime()
            # end if
        # end for
    return ret
# end def
