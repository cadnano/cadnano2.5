# -*- coding: utf-8 -*-
from cadnano.part.refresholigoscmd import RefreshOligosCommand
from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen

def decode(document, obj):
    ""
    name = obj['name']
    for part_dict in obj['parts']:
        part_dict = decodePart(document, part_dict)

    modifications = obj['modifications']
    for mod_id, item in modifications.items():
        document.createMod(item['props'], mod_id)
        ext_locations = item['ext_locations']
        for key in ext_locations:
            part, strand, idx = document.getModStrandIdx(key)
            part.addModStrandInstance(strand, idx, mod_id)
    return
# end def

def decodePart(document, part_dict):
    name = part_dict['name']
    dc = document._controller
    part = document.addDnaPart()
    dc.setActivePart(part)
    vh_id_list = part_dict['vh_list']
    vh_props = part_dict['virtual_helices']
    origins = part_dict['origins']
    keys = list(vh_props.keys())
    for id_num, size in vh_id_list:
        x, y = origins[id_num]
        vals = [vh_props[k][id_num] for k in keys]
        part.createVirtualHelix(x, y, size,
                                id_num=id_num,
                                properties=(keys, vals),
                                safe=False,
                                use_undostack=False)
    # end for
    strands = part_dict['strands']
    strand_index_list = strands['indices']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(id_num)
            fwd_idxs, rev_idxs = idx_set
            for low_idx, high_idx in fwd_idxs:
                fwd_strand_set.createDeserializedStrand(low_idx, high_idx, use_undostack=False)
            for low_idx, high_idx in rev_idxs:
                rev_strand_set.createDeserializedStrand(low_idx, high_idx, use_undostack=False)
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
        this_oligo.applyColor(color, use_undostack=False)
        if sequence is not None:
            this_oligo.applySequence(sequence, use_undostack=False)

    # INSERTIONS, SKIPS
    for id_num, idx, length in part_dict['insertions']:
        strand = part.getStrand(True, id_num, idx)
        strand.addInsertion(idx, length, use_undostack=False)
# end def

def importToPart(part, copy_dict, use_undostack=True):
    # dc.setActivePart(part)

    """ This is the Virtual Helix id number offset
    """
    next_id_num = part.getIdNumMax() + 1
    print("Starting from", next_id_num)
    vh_id_list = copy_dict['vh_list']
    origins = copy_dict['origins']
    vh_props = copy_dict['virtual_helices']

    keys = list(vh_props.keys())

    news_id_set = set()
    for i, pair in enumerate(vh_id_list):
        id_num, size = pair
        x, y = origins[i]
        vals = [vh_props[k][i] for k in keys]
        new_id_num = i + next_id_num
        part.createVirtualHelix(x, y, size,
                                id_num=new_id_num,
                                properties=(keys, vals),
                                safe=use_undostack,
                                use_undostack=use_undostack)
        news_id_set.add(new_id_num)
    # end for
    strands = copy_dict['strands']
    strand_index_list = strands['indices']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(id_num + next_id_num)
            fwd_idxs, rev_idxs = idx_set
            for low_idx, high_idx in fwd_idxs:
                fwd_strand_set.createDeserializedStrand(low_idx, high_idx, use_undostack=False)
            for low_idx, high_idx in rev_idxs:
                rev_strand_set.createDeserializedStrand(low_idx, high_idx, use_undostack=False)
    # end def

    xovers = copy_dict['xovers']
    for from_id, from_is_fwd, from_idx, to_id, to_is_fwd, to_idx in xovers:
        from_strand = part.getStrand(from_is_fwd, from_id + next_id_num, from_idx)
        to_strand = part.getStrand(to_is_fwd, to_id + next_id_num, to_idx)
        part.createXover(   from_strand, from_idx,
                            to_strand, to_idx,
                            update_oligo=use_undostack,
                            use_undostack=use_undostack)
    if not use_undostack:
        RefreshOligosCommand(part).redo()

    # INSERTIONS, SKIPS
    for id_num, idx, length in copy_dict['insertions']:
        strand = part.getStrand(True, id_num + next_id_num, idx)
        strand.addInsertion(idx, length, use_undostack=use_undostack)

    return news_id_set
# end def



