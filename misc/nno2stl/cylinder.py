# -*- coding: utf-8 -*-
from __future__ import division
import math

if __name__ == "__main__":
    import sys
    import os
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_path)

from cadnano.extras.math.vector import Vector3, Vector2, normalizeV3
from cadnano.extras.math.solid import Solid


class Cylinder(Solid):
    def __init__(self, name, radius, length, radial_segments=32):
        """
        Order of vertices added changes normals calculation
        so whether cylinder is in the y or z direction changes
        things so that's why some code is commented out.  y used
        to be the default
        """
        super(Cylinder, self).__init__(name)
        self.radius = radius
        self.length = length

        # local vars
        half_length = length / 2.
        vertices = []
        uvs = []

        for y in range(2):

            vertices_row = []
            uvs_row = []

            v = y

            for x in range(radial_segments+1):

                u = x / radial_segments

                vertex = Vector3(radius * math.sin(u * math.pi * 2),
                                 radius * math.cos(u * math.pi * 2),
                                 - v * length + half_length
                                 )
                # vertex = Vector3(   radius * math.sin( u * math.pi * 2 ),
                #     - v * length + half_length,
                #     radius * math.cos( u * math.pi * 2 )
                # )

                self.vertices.append(vertex)

                vertices_row.append(len(self.vertices) - 1)
                uvs_row.append(Vector2(u, 1 - v))

            # end for

            vertices.append(vertices_row)
            uvs.append(uvs_row)
        # end for

        for x in range(radial_segments):

            na = Vector3(*self.vertices[vertices[0][x]])
            nb = Vector3(*self.vertices[vertices[0][x + 1]])

            na = normalizeV3(na)
            nb = normalizeV3(nb)

            y = 0

            v1 = vertices[y][x]
            v2 = vertices[y + 1][x]
            v3 = vertices[y + 1][x + 1]
            v4 = vertices[y][x + 1]

            n1 = Vector3(*na)
            Vector3(*na)
            Vector3(*nb)
            Vector3(*nb)

            uv1 = Vector2(*uvs[y][x])
            uv2 = Vector2(*uvs[y + 1][x])
            uv3 = Vector2(*uvs[y + 1][x + 1])
            uv4 = Vector2(*uvs[y][x + 1])

            # self.addFace(v1, v2, v4)
            # self.addFace(v1, v2, v4, vnormals=[n1, n2, n4])
            # self.face_vertex_uvs[ 0 ].append( [ uv1, uv2, uv4 ] )

            self.addFace(v1, v4, v2)
            self.face_vertex_uvs[0].append([uv1, uv4, uv2])

            # self.addFace(v2, v3, v4)
            # self.addFace(v2, v3, v4, vnormals=[Vector3(*n2), n3, Vector3(*n4)])
            # self.face_vertex_uvs[ 0 ].append( [ Vector2(*uv2), uv3, Vector2(*uv4) ] );

            self.addFace(v4, v3, v2)
            self.face_vertex_uvs[0].append([Vector2(*uv4), uv3, Vector2(*uv2)])
        # end for

        # TOP CAP
        self.vertices.append(Vector3(0, 0, half_length))

        for x in range(radial_segments):

            v1 = vertices[0][x]
            v2 = vertices[0][x + 1]
            v3 = len(self.vertices) - 1

            n1 = Vector3(0, 0, 1.)
            Vector3(0, 0, 1.)
            Vector3(0, 0, 1.)

            uv1 = Vector2(*uvs[0][x])
            uv2 = Vector2(*uvs[0][x + 1])
            uv3 = Vector2(uv2.x, 0)

            # self.addFace(v1, v2, v3, normal=n1)
            # self.face_vertex_uvs[ 0 ].append( [ uv1, uv2, uv3 ] )

            self.addFace(v1, v3, v2, normal=n1)
            self.face_vertex_uvs[0].append([uv1, uv3, uv2])

        # end for

        # BOTTOM CAP
        self.vertices.append(Vector3(0, 0, -half_length))
        y = 1
        for x in range(radial_segments):

            v1 = vertices[y][x + 1]
            v2 = vertices[y][x]
            v3 = len(self.vertices) - 1

            n1 = Vector3(0, 0, -1.)
            Vector3(0, 0, -1.)
            Vector3(0, 0, -1.)

            uv1 = Vector2(*uvs[y][x + 1])
            uv2 = Vector2(*uvs[y][x])
            uv3 = Vector2(uv2.x, 1)

            # self.addFace(v1, v2, v3, normal=n1)
            # self.face_vertex_uvs[ 0 ].append( [ uv1, uv2, uv3 ] )

            self.addFace(v1, v3, v2, normal=n1)
            self.face_vertex_uvs[0].append([uv1, uv3, uv2])

    # end def
# end class


if __name__ == "__main__":
    import stlwriter
    path = 'poop.stl'
    path = os.path.join('/home', 'nick', 'Dropbox', path)
    cylinder = Cylinder("dog", 5, 10)
    print("vertices:", len(cylinder.vertices), "\nfaces:", len(cylinder.faces))
    # stlwriter.write(path, [cylinder], format="ascii")
    stlwriter.write(path, [cylinder], format="binary")
