# -*- coding: utf-8 -*-
from cadnano.part.refresholigoscmd import RefreshOligosCommand
from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen
from cadnano.cnenum import PointType

def decode(document, obj, emit_signals=False):
    """ Decode a a deserialized Document dictionary

    Args:
        document (Document):
        obj (dict): deserialized file object
    """
    name = obj['name']
    for part_dict in obj['parts']:
        part_dict = decodePart(document, part_dict, emit_signals=emit_signals)

    modifications = obj['modifications']
    for mod_id, item in modifications.items():
        document.createMod(item['props'], mod_id)
        ext_locations = item['ext_locations']
        for key in ext_locations:
            part, strand, idx = document.getModStrandIdx(key)
            part.addModStrandInstance(strand, idx, mod_id)
    return
# end def

def decodePart(document, part_dict, emit_signals=False):
    """ Decode a a deserialized Part dictionary

    Args:
        document (Document):
        part_dict (dict): deserialized dictionary describing the Part
    """
    name = part_dict['name']
    dc = document._controller
    part = document.createNucleicAcidPart(use_undostack=False)
    part.setActive(True)

    vh_id_list = part_dict['vh_list']
    vh_props = part_dict['virtual_helices']
    origins = part_dict['origins']
    keys = list(vh_props.keys())

    if part_dict.get('point_type') == PointType.ARBITRARY:
        # TODO add code to deserialize parts
        pass
    else:
        for id_num, size in vh_id_list:
            x, y = origins[id_num]
            z = vh_props['z'][id_num]
            vh_props['eulerZ'][id_num] = 0.5*(360./10.5)
            vals = [vh_props[k][id_num] for k in keys]
            part.createVirtualHelix(x, y, z, size,
                                    id_num=id_num,
                                    properties=(keys, vals),
                                    safe=False,
                                    use_undostack=False)
        # end for
        # zoom to fit
        if emit_signals:
            part.partZDimensionsChangedSignal.emit(part, *part.zBoundsIds(), True)

    strands = part_dict['strands']
    strand_index_list = strands['indices']
    color_list = strands['properties']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(id_num)
            fwd_idxs, rev_idxs = idx_set
            fwd_colors, rev_colors = color_list[id_num]
            for idxs, color in zip(fwd_idxs, fwd_colors):
                low_idx, high_idx = idxs
                fwd_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                        use_undostack=False)
            for idxs, color in zip(rev_idxs, rev_colors):
                low_idx, high_idx = idxs
                rev_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                        use_undostack=False)
        part.refreshSegments(id_num)   # update segments
    # end def

    xovers = part_dict['xovers']
    for from_id, from_is_fwd, from_idx, to_id, to_is_fwd, to_idx in xovers:
        from_strand = part.getStrand(from_is_fwd, from_id, from_idx)
        to_strand = part.getStrand(to_is_fwd, to_id, to_idx)
        part.createXover(   from_strand, from_idx,
                            to_strand, to_idx,
                            update_oligo=False,
                            use_undostack=False)

    RefreshOligosCommand(part).redo()
    for oligo in part_dict['oligos']:
        id_num = oligo['id_num']
        idx = oligo['idx5p']
        is_fwd = oligo['is_5p_fwd']
        color = oligo['color']
        sequence = oligo['sequence']
        strand5p = part.getStrand(is_fwd, id_num, idx)
        this_oligo = strand5p.oligo()
        # this_oligo.applyColor(color, use_undostack=False)
        if sequence is not None:
            this_oligo.applySequence(sequence, use_undostack=False)

    # INSERTIONS, SKIPS
    for id_num, idx, length in part_dict['insertions']:
        strand = part.getStrand(True, id_num, idx)
        strand.addInsertion(idx, length, use_undostack=False)

    # TODO fix this to set position
    instance_props = part_dict['instance_properties']    # list

    vh_order = part_dict['virtual_helix_order']
    if vh_order:
        # print("import order", vh_order)
        part.setImportedVHelixOrder(vh_order)
# end def

def importToPart(part_instance, copy_dict, use_undostack=True):
    """Use this to duplicate virtual_helices within a Part.  duplicate id_nums
    will start numbering `part.getIdNumMax()` rather than the lowest available
    id_num.  TODO should this numbering change?

    Args:
        part_instance (ObjectInstance):
        copy_dict (dict):
    """
    part = part_instance.reference()
    id_num_offset = part.getIdNumMax() + 1
    print("Starting from", id_num_offset)
    vh_id_list = copy_dict['vh_list']
    origins = copy_dict['origins']
    vh_props = copy_dict['virtual_helices']
    name_suffix = ".%d"

    keys = list(vh_props.keys())
    name_index = keys.index('name')
    new_vh_id_set = set()
    for i, pair in enumerate(vh_id_list):
        id_num, size = pair
        x, y = origins[i]
        z = vh_props['z'][id_num]
        vals = [vh_props[k][i] for k in keys]
        new_id_num = i + id_num_offset
        vals[name_index] += (name_suffix % new_id_num)
        part.createVirtualHelix(x, y, z, size,
                                id_num=new_id_num,
                                properties=(keys, vals),
                                safe=use_undostack,
                                use_undostack=use_undostack)
        new_vh_id_set.add(new_id_num)
    # end for
    strands = copy_dict['strands']
    strand_index_list = strands['indices']
    color_list = strands['properties']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(
                                                        id_num + id_num_offset)
            fwd_idxs, rev_idxs = idx_set
            fwd_colors, rev_colors = color_list[id_num]
            for idxs, color in zip(fwd_idxs, fwd_colors):
                low_idx, high_idx = idxs
                fwd_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                    use_undostack=use_undostack)

            for idxs, color in zip(rev_idxs, rev_colors):
                low_idx, high_idx = idxs
                rev_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                    use_undostack=use_undostack)
    # end def

    xovers = copy_dict['xovers']
    for from_id, from_is_fwd, from_idx, to_id, to_is_fwd, to_idx in xovers:
        from_strand = part.getStrand(from_is_fwd, from_id + id_num_offset, from_idx)
        to_strand = part.getStrand(to_is_fwd, to_id + id_num_offset, to_idx)
        part.createXover(   from_strand, from_idx,
                            to_strand, to_idx,
                            update_oligo=use_undostack,
                            use_undostack=use_undostack)
    if not use_undostack:
        RefreshOligosCommand(part).redo()

    # INSERTIONS, SKIPS
    for id_num, idx, length in copy_dict['insertions']:
        strand = part.getStrand(True, id_num + id_num_offset, idx)
        strand.addInsertion(idx, length, use_undostack=use_undostack)


    """
    TODO: figure out copy_dict['view_properties'] handling here
    """

    return new_vh_id_set
# end def



