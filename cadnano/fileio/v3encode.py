# -*- coding: utf-8 -*-
from datetime import datetime
FORMAT_VERSION = "3.0"

def encodeDocument(document):
  doc_dict = {'format': FORMAT_VERSION,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'name': "",
        'parts': [],
  }
  parts_list = doc_dict['parts']
  for part in document.getParts():
      part_dict = encodePart(part)
      parts_list.append(part_dict)
  return doc_dict
# end def

def encodePart(part):
    number_of_helices = part.getIdNumMax()
    vh_insertions = part.insertions()

    # iterate through virtualhelix list
    group_props = part.getPropertyDict().copy()
    view_props = part.view_properties
    vh_props, origins = part.helixPropertiesAndOrigins()

    # group_props['total_id_nums'] =
    group_props['virtual_helices'] = vh_props
    group_props['origins'] = origins

    xover_list = []
    strand_list = []
    vh_list = []
    for id_num in range(number_of_helices + 1):
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            # add a placeholder
            strand_list.append((None, None))
        else:
            offset, size = offset_and_size
            vh_list.append((id_num, size))
            fwd_ss, rev_ss = part.getStrandSets(id_num)
            fwd_idxs = fwd_ss.dump(xover_list)
            rev_idxs = rev_ss.dump(xover_list)
            strand_list.append((fwd_idxs, rev_idxs))
    # end for
    group_props['vh_list'] = vh_list
    group_props['strands'] = {  'indices': strand_list,
                                'properties': []
                            }
    group_props['insertions'] = vh_insertions
    group_props['xovers'] = xover_list
    # oligo_dict = {k: v for k, v in zip( oligo.ALL_KEYS,
    #                                 zip(o.dump() for o in part.oligos()))
    #             }
    group_props['oligos'] = [o.dump() for o in part.oligos()]
    group_props['view_properties'] = view_props
    group_props['modifications'] = part.mods()

    return group_props
# end def