# -*- coding: utf-8 -*-
# http://en.wikipedia.org/wiki/STL_(file_format)
# http://www.ennex.com/~fabbers/StL.asp

import io
import struct


def write(filename, solids, format="binary"):
    if format == "binary":
        write_binary(filename, solids)
    else:
        write_ascii(filename, solids)
# end def

# derived from stl.py in visvis
# Copyright (C) 2012, Almar Klein
# Visvis is distributed under the terms of the (new) BSD License.


def write_binary(filename, solids):
    def write_vertex(vid, d_list, solid):
        v = solid.vertices[vid]
        for val in v:
            d_list.append(struct.pack('<f', val))  # 4 byte float
    # end def

    with io.open(filename, "wb") as fd:
        fd.write(struct.pack('<B', 0)*80)   # 80 bytes header
        fd.write(struct.pack('<I', sum([len(s.faces) for s in solids])))  # 4 bytes

        data_list = []
        for solid in solids:
            for face in solid.faces:
                for val in face.normal:
                    data_list.append(struct.pack('<f', val))  # 4 byte float
                write_vertex(face.v1, data_list, solid)
                write_vertex(face.v2, data_list, solid)
                write_vertex(face.v3, data_list, solid)
                data_list.append(struct.pack('<H', 0))            # attribute byte count, set to 0
        # end for solid
        data = ''.encode('ascii').join(data_list)
        fd.write(data)
    # end with
# end def


def write_ascii(filename, solids):
    def write_vertex(vid, fd, solid):
        v = solid.vertices[vid]
        fd.write('\t\t\tvertex %E %E %E\n' % (v.x, v.y, v.z))
    # end def

    with io.open(filename, "w") as fd:
        fd.write('solid %s\n' % (solids[0].name))
        for solid in solids:
            for face in solid.faces:
                n = face.normal
                fd.write('\tfacet normal %E %E %E\n' % (n.x, n.y, n.z))
                fd.write('\t\touter loop\n')
                write_vertex(face.v1, fd, solid)
                write_vertex(face.v2, fd, solid)
                write_vertex(face.v3, fd, solid)
                fd.write('\t\tendloop\n')
                fd.write('\tendfacet\n')
        # end for solid
        fd.write('endsolid %s\n' % (solids[0].name))
    # end with
# end def
