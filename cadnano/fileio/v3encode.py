# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List

from cadnano.proxies.cnenum import PointEnum
from cadnano.objectinstance import ObjectInstance
from cadnano.cntypes import (
    DocT,
    PartT
)

FORMAT_VERSION = '3.1'


def encodeDocument(document: DocT) -> dict:
    """ Encode a Document to a dictionary to enable serialization

    Args:
        document (Document):

    Returns:
        object dictionary
    """
    doc_dict = {'format': FORMAT_VERSION,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'name': '',
                'parts': [],
                'modifications': document.modifications()
                }
    parts_list = doc_dict['parts']
    for part in document.getParts():
        part_dict = encodePart(part)
        parts_list.append(part_dict)
    return doc_dict
# end def


def encodePart(part: PartT) -> dict:
    """
    Args:
        part (Part):

    Returns:
        dict:
    """
    # iterate through virtualhelix list
    group_props = part.getModelProperties().copy()

    if not group_props.get('is_lattice', True):
        # TODO add code to encode Parts with ARBITRARY point configurations
        vh_props, origins = part.helixPropertiesAndOrigins()
        group_props['virtual_helices'] = vh_props
        group_props['origins'] = origins
    else:
        vh_props, origins = part.helixPropertiesAndOrigins()
        group_props['virtual_helices'] = vh_props
        group_props['origins'] = origins

    xover_list = []
    strand_list = []
    prop_list = []
    vh_list = []
    for id_num in part.getidNums():
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

def reEmitPart(part: PartT):
    """
    Args:
        part (Part):
    """
    # iterate through virtualhelix list
    group_props = part.getModelProperties().copy()

    if not group_props.get('is_lattice', True):
        # TODO add code to encode Parts with ARBITRARY point configurations
        pass
    else:
        vh_props, origins = part.helixPropertiesAndOrigins()
        group_props['virtual_helices'] = vh_props
        group_props['origins'] = origins

    xover_list = []
    threshold = 2.1*part.radius()
    for id_num in part.getidNums():
        offset_and_size = part.getOffsetAndSize(id_num)
        if offset_and_size is not None:
            offset, size = offset_and_size
            vh = part.getVirtualHelix(id_num)
            neighbors = part._getVirtualHelixOriginNeighbors(id_num, threshold)
            part.partVirtualHelixAddedSignal.emit(part, id_num, vh, neighbors)

            fwd_ss, rev_ss = part.getStrandSets(id_num)

            for strand in fwd_ss.strands():
                fwd_ss.strandsetStrandAddedSignal.emit(fwd_ss, strand)
            for strand in rev_ss.strands():
                fwd_ss.strandsetStrandAddedSignal.emit(rev_ss, strand)
            part.partStrandChangedSignal.emit(part, id_num)

            fwd_idxs, fwd_colors = fwd_ss.dump(xover_list)
            rev_idxs, rev_colors = rev_ss.dump(xover_list)
    # end for

    for from_id, from_is_fwd, from_idx, to_id, to_is_fwd, to_idx in xover_list:
        strand5p = from_strand = part.getStrand(from_is_fwd, from_id, from_idx)
        strand3p = to_strand = part.getStrand(to_is_fwd, to_id, to_idx)
        strand5p.strandConnectionChangedSignal.emit(strand5p)
        strand3p.strandConnectionChangedSignal.emit(strand3p)
    # end for

    for id_num, id_dict in part.insertions().items():
        for idx, insertion in id_dict.items():
            fwd_strand = part.getStrand(True, id_num, idx)
            rev_strand = part.getStrand(False, id_num, idx)
            if fwd_strand:
                fwd_strand.strandInsertionAddedSignal.emit(fwd_strand, insertion)
            if rev_strand:
                rev_strand.strandInsertionAddedSignal.emit(rev_strand, insertion)
    # end for

    # instance_props = list(part.instanceProperties())
    # emit instance properties

    return group_props
# end def


def encodePartList(part_instance: ObjectInstance, vh_group_list: List[int]) -> dict:
    """ Used for copying and pasting
    TODO: unify encodePart and encodePartList

    Args:
        part_instance: The ``Part`` ``ObjectInstance``, to allow for instance
            specific property copying
        vh_group_list: List of virtual_helices IDs to encode to
            be used with copy and paste serialization

    Returns:
        Dictionary representing the virtual helices with ordered lists of
        properties, strands, etc to allow for copy and pasting becoming
        different ID'd virtual helices
    """
    part = part_instance.reference()
    vh_group_list.sort()
    # max_id_number_of_helices = part.getMaxIdNum()
    # vh_insertions = part.insertions()

    '''NOTE This SHOULD INCLUDE 'grid_type' key
    '''
    group_props = part.getModelProperties().copy()
    assert('grid_type' in group_props)

    if not group_props.get('is_lattice', True):
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

    def filter_xovers(x):
        return (x[0] in vh_group_set and x[3] in vh_group_set)

    def filter_vh(x):
        return x[0] in vh_group_set

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
