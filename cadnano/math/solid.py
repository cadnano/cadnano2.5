# -*- coding: utf-8 -*-

from cadnano.math.vector import normalToPlane, normalizeV3, applyMatrix3, applyMatrix4
from cadnano.math.matrix3 import getNormalMatrix

from cadnano.math.face import Face

class Solid(object):
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.faces = []
        self.face_vertex_uvs = [[]]
    # end def

    def addFace(self, v1, v2, v3, normal=None):
        """ List vertices using right hand rule so that unit
        normal will point out of the surface

        vertices are given by index into vertices list

        Args:
            v1 (Vector3):
            v2 (Vector3):
            v3 (Vector3):
            normal (Vector3): face normal

        """
        # for v in vertices:
        #     if v is not in self.vertices:
        #         self.addVertex(v)
        vrts = self.vertices
        if normal is None:
            normal = normalToPlane(vrts[v1], vrts[v2], vrts[v3])
        self.faces.append(Face(normal, v1, v2, v3))
    # end def

    def addVertex(self, vertex):
        """ Add a vertex to the Solid
        Args:
            vertex (Vector3):
        """
        self.vertices.append(vertex)
    # end def

    def applyMatrix(self, matrix4):

        normal_matrix = getNormalMatrix( matrix4 );
        verts = self.vertices
        for i in range(len(verts)):
            vertex = verts[i]
            verts[i] = applyMatrix4(matrix4, vertex)
        faces = self.faces
        for i in range(len(faces)):
            face = faces[i]
            normal = normalizeV3(applyMatrix3(normal_matrix, face.normal))
            faces[i] = Face(normal, face.v1, face.v2, face.v3)

    def computeFaceNormals(self):
        vrts = self.vertices
        for i in range(len(self.faces)):
            face = self.faces[i]
            normal = normalToPlane(vrts[face.v1], vrts[face.v2], vrts[face.v3])
            self.faces[i] = Face(normal, face.v1, face.v2, face.v3)
        # end for
# end class

