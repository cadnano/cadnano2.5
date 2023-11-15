# -*- coding: utf-8 -*-
from cadnano.fileio.lattice import HoneycombDnaPart, SquareDnaPart
from cadnano.part.nucleicacidpart import DEFAULT_RADIUS
from cadnano.part.refresholigoscmd import RefreshOligosCommand
from cadnano.proxies.cnenum import GridType, PointType, OrthoViewType


def decode(document, obj, emit_signals=False):
    """ Decode a a deserialized Document dictionary

    Args:
        document (Document):
        obj (dict): deserialized file object
    """
    obj.get('name')

    for part_dict in obj['parts']:
        grid_type = determineLatticeType(part_dict)

        ortho_view_type = determineOrthoViewType(part_dict, grid_type)
        document.setSliceOrGridViewVisible(value=ortho_view_type)

        decodePart(document, part_dict, grid_type=grid_type,
                   emit_signals=emit_signals)

    modifications = obj['modifications']

    for mod_id, item in modifications.items():
        document.createMod(item['props'], mod_id)
        ext_locations = item['ext_locations']
        for key in ext_locations:
            part, strand, idx = document.getModStrandIdx(key)
            part.addModStrandInstance(strand, idx, mod_id)
# end def


def determineOrthoViewType(part_dict, grid_type):
    THRESHOLD = 0.0005
    vh_id_list = part_dict.get('vh_list')
    origins = part_dict.get('origins')

    for vh_id, size in vh_id_list:
        vh_x, vh_y = origins[vh_id]

        if grid_type is GridType.HONEYCOMB:
            distance, point = HoneycombDnaPart.distanceFromClosestLatticeCoord(radius=DEFAULT_RADIUS, x=vh_x, y=vh_y)
            if distance > THRESHOLD:
                return OrthoViewType.GRID
        elif grid_type is GridType.SQUARE:
            if SquareDnaPart.distanceFromClosestLatticeCoord(radius=DEFAULT_RADIUS, x=vh_x, y=vh_y)[0] > THRESHOLD:
                return OrthoViewType.GRID
    return OrthoViewType.SLICE
# end def

def determineLatticeType(part_dict):
    """
    Guess the lattice type based on the sum of the vector distances between
    VHs and the closest lattice position.


    Args:
        part_dict (dict):  the dict corresponding to the part to be imported

    Returns:
        GridType.HONEYCOMB or GridType.SQUARE
    """
    vh_id_list = part_dict.get('vh_list')
    origins = part_dict.get('origins')

    square_delta_x = 0.
    square_delta_y = 0.

    honeycomb_delta_x = 0.
    honeycomb_delta_y = 0.

    for vh_id, _ in vh_id_list:
        vh_x, vh_y = origins[vh_id]
        hcd, honeycomb_guess_coordinates = HoneycombDnaPart.distanceFromClosestLatticeCoord(DEFAULT_RADIUS, vh_x, vh_y)
        sqd, square_guess_coordinates = SquareDnaPart.distanceFromClosestLatticeCoord(DEFAULT_RADIUS, vh_x, vh_y)

        honeycomb_guess_x, honeycomb_guess_y = HoneycombDnaPart.latticeCoordToQtXY(DEFAULT_RADIUS,
                                                                                   honeycomb_guess_coordinates[0],
                                                                                   honeycomb_guess_coordinates[1])
        square_guess_x, square_guess_y = SquareDnaPart.latticeCoordToQtXY(DEFAULT_RADIUS,
                                                                          square_guess_coordinates[0],
                                                                          square_guess_coordinates[1])

        honeycomb_delta_x += (vh_x - honeycomb_guess_x)
        honeycomb_delta_y += (vh_y - honeycomb_guess_y)

        square_delta_x += (vh_x - square_guess_x)
        square_delta_y += (vh_y - square_guess_y)

    sum_honeycomb_distance = (honeycomb_delta_x**2 + honeycomb_delta_y**2)**0.5
    sum_square_distance = (square_delta_x**2 + square_delta_y**2)**0.5

    if abs(sum_honeycomb_distance) < abs(sum_square_distance):
        return GridType.HONEYCOMB
    else:
        return GridType.SQUARE
# end def

def decodePart(document, part_dict, grid_type, emit_signals=False):
    """ Decode a a deserialized Part dictionary

    Args:
        document (Document):
        part_dict (dict): deserialized dictionary describing the Part
    """
    part = document.createNucleicAcidPart(use_undostack=False, grid_type=grid_type)
    part.setActive(True)

    vh_id_list = part_dict.get('vh_list')
    vh_props = part_dict.get('virtual_helices')
    origins = part_dict.get('origins')
    keys = list(vh_props.keys())

    if part_dict.get('point_type') == PointType.ARBITRARY:
        # TODO add code to deserialize parts
        pass
    else:
        for id_num, size in vh_id_list:
            x, y = origins[id_num]
            z = vh_props['z'][id_num]
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
    for i in range(len(vh_id_list)):
        id_num = vh_id_list[i][0]
        idx_set = strand_index_list[i]
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(id_num)
            fwd_idxs, rev_idxs = idx_set
            fwd_colors, rev_colors = color_list[i]
            for idxs, color in zip(fwd_idxs, fwd_colors):
                low_idx, high_idx = idxs
                fwd_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                        use_undostack=False)
            for idxs, color in zip(rev_idxs, rev_colors):
                low_idx, high_idx = idxs
                rev_strand_set.createDeserializedStrand(low_idx, high_idx, color,
                                                        use_undostack=False)
            part.refreshSegments(id_num)   # update segments
    # end for

    xovers = part_dict['xovers']
    for from_id, from_is_fwd, from_idx, to_id, to_is_fwd, to_idx in xovers:
        from_strand = part.getStrand(from_is_fwd, from_id, from_idx)
        to_strand = part.getStrand(to_is_fwd, to_id, to_idx)
        part.createXover(from_strand, from_idx,
                         to_strand, to_idx,
                         update_oligo=False,
                         use_undostack=False)
    # end for

    RefreshOligosCommand(part).redo()
    for oligo in part_dict['oligos']:
        id_num = oligo['id_num']
        idx = oligo['idx5p']
        is_fwd = oligo['is_5p_fwd']
        color = oligo['color']
        sequence = oligo['sequence']
        name = oligo['name']
        strand5p = part.getStrand(is_fwd, id_num, idx)
        this_oligo = strand5p.oligo()
        # this_oligo.applyColor(color, use_undostack=False)
        if sequence is not None:
            this_oligo.applySequence(sequence, use_undostack=False)
        if name is not None:
            this_oligo.setProperty('name', name)
    # end for

    # INSERTIONS, SKIPS
    for id_num, idx, length in part_dict['insertions']:
        fwd_strand = part.getStrand(True, id_num, idx)
        rev_strand = part.getStrand(False, id_num, idx)
        if fwd_strand:
            fwd_strand.addInsertion(idx, length, use_undostack=False)
        elif rev_strand:
            rev_strand.addInsertion(idx, length, use_undostack=False)
        else:
            ins = 'Insertion' if length > 0 else 'Skip'
            print("Cannot find strand for {} at {}[{}]".format(ins, id_num, idx))
    # end for

    # TODO fix this to set position
    # instance_props = part_dict['instance_properties']    # list

    vh_order = part_dict['virtual_helix_order']
    if vh_order:
        # print("import order", vh_order)
        part.setImportedVHelixOrder(vh_order)

    # Restore additional Part properties
    for key in ('name',
                'color',
                'crossover_span_angle',
                'max_vhelix_length',
                'workplane_idxs'):
        value = part_dict.get(key)
        if value is not None:
            part.setProperty(key, value, use_undostack=False)
            part.partPropertyChangedSignal.emit(part, key, value)
# end def


def importToPart(part_instance, copy_dict, offset=None, use_undostack=True, ignore_neighbors=False):
    """
    Use this to duplicate virtual_helices within a Part. Duplicate id_nums
    will start numbering `part.getMaxIdNum()` rather than the lowest available
    id_num.  TODO should this numbering change?

    Args:
        part_instance (ObjectInstance):
        copy_dict (dict):
    """
    assert isinstance(offset, (tuple, list)) or offset is None
    assert isinstance(use_undostack, bool)

    print('Importing to part where use_undostack is %s' % use_undostack)

    part = part_instance.reference()
    id_num_offset = part.getMaxIdNum() + 1
    if id_num_offset % 2 == 1:
        id_num_offset += 1
    vh_id_list = copy_dict['vh_list']
    origins = copy_dict['origins']
    vh_props = copy_dict['virtual_helices']
    # name_suffix = ".%d"

    xoffset = offset[0] if offset else 0
    yoffset = offset[1] if offset else 0

    keys = list(vh_props.keys())
    name_index = keys.index('name')
    new_vh_id_set = set()
    for i, pair in enumerate(vh_id_list):
        id_num, size = pair
        x, y = origins[i]

        z = vh_props['z'][i]
        vals = [vh_props[k][i] for k in keys]
        new_id_num = i + id_num_offset
        vals[name_index] = 'vh%s' % new_id_num
        if ignore_neighbors:
            try:
                ignore_index = keys.index('neighbors')
                fixed_keys = keys[:ignore_index] + keys[ignore_index + 1:]
                fixed_vals = vals[:ignore_index] + vals[ignore_index + 1:]
            except ValueError:
                fixed_keys = keys
                fixed_vals = vals
        part.createVirtualHelix(x+xoffset, y+yoffset, z, size,
                                id_num=new_id_num,
                                properties=(fixed_keys, fixed_vals),
                                safe=use_undostack,
                                use_undostack=use_undostack)
        new_vh_id_set.add(new_id_num)
    # end for
    strands = copy_dict['strands']
    strand_index_list = strands['indices']
    color_list = strands['properties']
    for id_num, idx_set in enumerate(strand_index_list):
        if idx_set is not None:
            fwd_strand_set, rev_strand_set = part.getStrandSets(id_num + id_num_offset)
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
        part.createXover(from_strand, from_idx,
                         to_strand, to_idx,
                         update_oligo=use_undostack,
                         use_undostack=use_undostack)
    if not use_undostack:
        RefreshOligosCommand(part).redo()

    # INSERTIONS, SKIPS
    for id_num, idx, length in copy_dict['insertions']:
        fwd_strand = part.getStrand(True, id_num + id_num_offset, idx)
        rev_strand = part.getStrand(False, id_num + id_num_offset, idx)
        if fwd_strand:
            fwd_strand.addInsertion(idx, length, use_undostack=use_undostack)
        elif rev_strand:
            rev_strand.addInsertion(idx, length, use_undostack=use_undostack)
        else:
            ins = 'Insertion' if length > 0 else 'Skip'
            print("Cannot find strand for {} at {}[{}]".format(ins, id_num, idx))

    """
    TODO: figure out copy_dict['view_properties'] handling here
    """
    return new_vh_id_set
# end def
