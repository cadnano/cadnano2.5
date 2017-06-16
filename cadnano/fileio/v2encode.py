# -*- coding: utf-8 -*-
from cadnano.cnenum import PointType
from cadnano.cnenum import LatticeType
# from cadnano.cnenum import StrandType
from cadnano.fileio.lattice import HoneycombDnaPart
# from cadnano.fileio.lattice import SquareDnaPart

FORMAT_VERSION = "2.0"
DEFAULT_ROWS = 30
DEFAULT_COLS = 32
lattice_type = LatticeType.HONEYCOMB
positionToLatticeCoord = HoneycombDnaPart.positionToLatticeCoordRound


def encodeDocument(document):

    part = next(document.getParts())
    radius = part.radius()

    # Determine offset to approximately center the shape
    # xLL, yLL, xUR, yUR = part.getVirtualHelixOriginLimits()
    # print(xLL, yLL, xUR, yUR)
    # rowLL, colLL = positionToLatticeCoord(radius, xLL, yLL, False, False)
    # rowUR, colUR = positionToLatticeCoord(radius, xUR, yUR, True, True)
    # print("LL=({0},{1}), UR=({2},{3})".format(rowLL, colLL, rowUR, colUR))
    # height = abs(rowLL-rowUR)
    # width = abs(colLL-colUR)
    # delta_row = (DEFAULT_ROWS-height)//2
    # if delta_row % 2 == 1:
    #     delta_row += 1
    # delta_col = (DEFAULT_COLS-width)//2
    # if delta_col % 2 == 1:
    #     delta_col += 1
    delta_row = 2  # hard code for now
    delta_col = 3
    print("Shifting each (row,col) by ({0},{1})".format(delta_row, delta_col))

    insertions = part.insertions()
    vh_order = part.getVirtualHelixOrder()
    name = "legacy-export-cn25"
    max_base_idx = max([part.maxBaseIdx(id_num) for id_num in vh_order])

    # iterate through virtualhelix list
    vh_list = []
    for id_num in vh_order:
        # vh = part.getVirtualHelix(id_num)
        fwd_ss, rev_ss = part.getStrandSets(id_num)
        # print(vh, fwd_ss, rev_ss)

        # insertions and skips
        insertion_dict = insertions[id_num]
        insts = [0 for i in range(max_base_idx)]
        skips = [0 for i in range(max_base_idx)]
        for idx, insertion in insertion_dict.items():
            if insertion.isSkip():
                skips[idx] = insertion.length()
            else:
                insts[idx] = insertion.length()
        # if sum(insts) != 0:
        #     print("insts", insts)
        # if sum(skips) != 0:
        #     print("skips", skips)

        if id_num % 2 == 0:
            scaf_ss, stap_ss = fwd_ss, rev_ss
        else:
            scaf_ss, stap_ss = rev_ss, fwd_ss  # noqa

        # colors
        stap_colors = []
        for strand in stap_ss:
            if strand.connection5p() is None:
                c = str(strand.oligo().getColor())[1:]  # drop the hash
                stap_colors.append([strand.idx5Prime(), int(c, 16)])
        # print(stap_colors)

        # convert x,y coordinates to row, col
        vh_x, vh_y = part.getVirtualHelixOrigin(id_num)
        row, col = positionToLatticeCoord(radius, vh_x, vh_y, False, False)
        new_row = -row + delta_row
        new_col = col + delta_col
        print("{0}:({1},{2}) -> ({3},{4})".format(id_num, row, col, new_row, new_col))

        vh_dict = {"row": row+delta_row,
                   "col": col+delta_col,
                   "num": id_num,
                   "scaf": getLegacyStrandSetArray(scaf_ss, max_base_idx),
                   "stap": getLegacyStrandSetArray(stap_ss, max_base_idx),
                   "loop": insts,
                   "skip": skips,
                   "scafLoop": [],
                   "stapLoop": [],
                   "stap_colors": stap_colors}
        vh_list.append(vh_dict)
    # bname = basename(str(fname))
    obj = {"name": name, "vstrands": vh_list}
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


# def encodeDocument(document):
#     """
#     Encode a Document to a dictionary to enable serialization

#     Args:
#         document (Document):

#     Returns:
#         dict: encoded document as json object
#     """
#     doc_dict = {'format': FORMAT_VERSION,
#                 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 'name': "",
#                 'parts': [],
#                 'modifications': document.modifications()
#                 }
#     parts_list = doc_dict['parts']
#     for part in document.getParts():
#         part_dict = encodePart(part)
#         parts_list.append(part_dict)
#     return doc_dict
# # end def


def encodePart(part):
    """
    Args:
        part (Part):

    Returns:
        dict:
    """
    max_id_number_of_helices = part.getIdNumMax()

    # iterate through virtualhelix list
    group_props = part.getModelProperties().copy()

    if group_props.get('point_type') == PointType.ARBITRARY:
        # TODO add code to encode Parts with ARBITRARY point configurations
        pass
    else:
        vh_props, origins = part.helixPropertiesAndOrigins()
        group_props['virtual_helices'] = vh_props
        group_props['origins'] = origins

    xover_list = []
    strand_list = []
    prop_list = []
    vh_list = []
    for id_num in range(max_id_number_of_helices + 1):
        offset_and_size = part.getOffsetAndSize(id_num)
        if offset_and_size is None:
            # add a placeholder
            strand_list.append(None)
            prop_list.append(None)
        else:
            offset, size = offset_and_size
            vh_list.append((id_num, size))
            fwd_ss, rev_ss = part.getStrandSets(id_num)
            fwd_idxs, fwd_colors = fwd_ss.dump(xover_list)
            rev_idxs, rev_colors = rev_ss.dump(xover_list)
            strand_list.append((fwd_idxs, rev_idxs))
            prop_list.append((fwd_colors, rev_colors))
    # end for
    group_props['vh_list'] = vh_list
    group_props['strands'] = {'indices': strand_list,
                              'properties': prop_list
                              }
    group_props['insertions'] = list(part.dumpInsertions())
    group_props['xovers'] = xover_list
    group_props['oligos'] = [o.dump() for o in part.oligos()]

    instance_props = list(part.instanceProperties())
    group_props['instance_properties'] = instance_props

    group_props['uuid'] = part.uuid
    return group_props
# end def


def encodePartList(part_instance, vh_group_list):
    """ Used for copying and pasting
    TODO: unify encodePart and encodePartList

    Args:
        part (Part):
        vh_group_list (list): of :obj:`int`, virtual_helices IDs to encode to
            be used with copy and paste serialization

    Returns:
        dict:
    """
    part = part_instance.reference()
    vh_group_list.sort()
    # max_id_number_of_helices = part.getIdNumMax()
    # vh_insertions = part.insertions()

    # iterate through virtualhelix list
    group_props = part.getModelProperties().copy()

    if group_props.get('point_type') == PointType.ARBITRARY:
        # TODO add code to encode Parts with ARBITRARY point configurations
        pass
    else:
        vh_props, origins = part.helixPropertiesAndOrigins(vh_group_list)
        group_props['virtual_helices'] = vh_props
        group_props['origins'] = origins

    xover_list = []
    strand_list = []
    prop_list = []
    vh_list = []
    vh_group_set = set(vh_group_list)
    filter_xovers = lambda x: (x[0] in vh_group_set and
                               x[3] in vh_group_set)
    filter_vh = lambda x: x[0] in vh_group_set
    for id_num in vh_group_list:
        offset_and_size = part.getOffsetAndSize(id_num)
        if offset_and_size is None:
            # add a placeholder
            strand_list.append(None)
            prop_list.append(None)
        else:
            offset, size = offset_and_size
            vh_list.append((id_num, size))
            fwd_ss, rev_ss = part.getStrandSets(id_num)
            fwd_idxs, fwd_colors = fwd_ss.dump(xover_list)
            rev_idxs, rev_colors = rev_ss.dump(xover_list)
            strand_list.append((fwd_idxs, rev_idxs))
            prop_list.append((fwd_colors, rev_colors))
    # end for

    remap = {x: y for x, y in zip(vh_group_list,
                                  range(len(vh_group_list))
                                  )}
    group_props['vh_list'] = vh_list
    group_props['strands'] = {'indices': strand_list,
                              'properties': prop_list
                              }
    filtered_insertions = filter(filter_vh, part.dumpInsertions())
    group_props['insertions'] = [(remap[x], y, z) for x, y, z in filtered_insertions]

    filtered_xover_list = filter(filter_xovers, xover_list)
    group_props['xovers'] = [(remap[a], b, c, remap[x], y, z)
                             for a, b, c, x, y, z in filtered_xover_list]

    instance_props = part_instance.properties()
    group_props['instance_properties'] = instance_props

    vh_order = filter(lambda x: x in vh_group_set, group_props['virtual_helix_order'])
    vh_order = [remap[x] for x in vh_order]
    group_props['virtual_helix_order'] = vh_order

    external_mods_instances = filter(filter_vh,
                                     part.dumpModInstances(is_internal=False))
    group_props['external_mod_instances'] = [(remap[w], x, y, z)
                                             for w, x, y, z in external_mods_instances]
    """ TODO Add in Document modifications

    """
    return group_props
# end def
