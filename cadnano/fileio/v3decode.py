# -*- coding: utf-8 -*-

def decode(document, obj):
    ""
    name = obj['name']
    for part_dict in obj['parts']:
        part_dict = decodePart(document, part_dict)
    return
# end def

def decodePart(document, part_dict):
    name = part_dict['name']
    part = document._controller.actionAddDnaPart()
    vh_id_list = part_dict['vh_list']
    vh_props = part_dict['virtual_helices']
    origins = part_dict['origins']
    keys = list(vh_props.keys())
    for id_num, size in vh_id_list:
        x, y = origins[id_num]
        vals = [vh_props[k][id_num] for k in keys]
        part.createVirtualHelix(x, y, size,
                                id_num=id_num,
                                properties=(keys, vals)
                                safe=False
                                use_undostack=False)
    # end for
    strands = part_dict['strands']
    strand_index_list = strands['indices']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strandset = part.getStrandSets(id_num)
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
                            from_idx, to_idx,
                            update_oligo=False,
                            use_undostack=False)

    RefreshOligosCommand(part,
                     colors=(   prefs.DEFAULT_SCAF_COLOR,
                                prefs.DEFAULT_STAP_COLOR)).redo()
    # for oligo in part_dict['oligos']:
    #     id_num = oligo['id_num']
    #     idx = oligo['idx5p']
    #     is_fwd = oligo['is_5p_fwd']
    #     seq = str(oligo['seq']) if oligo['seq'] is not None else ''
    #     if seq != '':
    #         strand = part.getStrand(is_fwd, id_num, idx)
    #         strand.oligo().applySequence(seq, use_undostack=False)
# end def
