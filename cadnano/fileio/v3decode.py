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
# end def
