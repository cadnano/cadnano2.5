# -*- coding: utf-8 -*-
from cadnano.part.refresholigoscmd import RefreshOligosCommand
from cadnano import preferences as prefs
from cadnano import setBatch, getReopen, setReopen

def decode(document, obj):
    ""
    name = obj['name']
    for part_dict in obj['parts']:
        part_dict = decodePart(document, part_dict)
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
                fwd_strand_set.createStrand(low_idx, high_idx, use_undostack=False)
            for low_idx, high_idx in rev_idxs:
                rev_strand_set.createStrand(low_idx, high_idx, use_undostack=False)
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

    modifications = part_dict['modifications']
    for mod_id, item in modifications.items():
        if mod_id != 'int_instances' and mod_id != 'ext_instances':
            part.createMod(item, mod_id)
    for key, mid in modifications['ext_instances'].items():
        # strand, idx, coord, isstaple = part.getModStrandIdx(key)
        strand, idx = part.getModStrandIdx(key)
        try:
            strand.addMods(mid, idx, use_undostack=False)
        except:
            print(strand, idx)
            raise
    for key in modifications['int_instances'].items():
        # strand, idx, coord, isstaple  = part.getModStrandIdx(key)
        strand, idx = part.getModStrandIdx(key)
        try:
            strand.addMods(mid, idx, use_undostack=False)
        except:
            print(strand, idx)
            raise
# end def
