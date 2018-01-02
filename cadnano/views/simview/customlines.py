import struct

from PyQt5.QtCore import QByteArray
# from PyQt5.QtGui import QVector3D, QVector4D

from PyQt5.Qt3DCore import QEntity
from PyQt5.Qt3DExtras import QPerVertexColorMaterial
from PyQt5.Qt3DRender import QAttribute
from PyQt5.Qt3DRender import QBuffer
from PyQt5.Qt3DRender import QGeometry, QGeometryRenderer

from cadnano.gui.palette import getColorObj


class Line(QEntity):
    def __init__(self, p1, p2, color, parent_entity):
        super(Line, self).__init__(parent_entity)
        p1x, p1y, p1z = p1[:]
        p2x, p2y, p2z = p2[:]

        self.color = color
        self._mesh = mesh = QGeometryRenderer(parent_entity)
        self._geometry = geo = QGeometry(mesh)

        mesh.setRestartIndexValue(65535)

        color_obj = getColorObj(color)
        cr, cg, cb, calpha = color_obj.getRgbF()

        vertex_color_list = [p1x, p1y, p1z, cr, cg, cb,
                             p2x, p2y, p2z, cr, cg, cb]

        vertex_color_bytes = struct.pack('%sf' % len(vertex_color_list), *vertex_color_list)
        vertex_color_bytearray = QByteArray(vertex_color_bytes)
        vertex_color_buffer = QBuffer(QBuffer.VertexBuffer)
        vertex_color_buffer.setData(vertex_color_bytearray)

        sizeof_float = len(struct.pack('f', 1.0))  # 4
        stride = (3 + 3)*sizeof_float  # 24
        num_verts = 2

        self._pos_attr = pos_attr = QAttribute()
        pos_attr.setAttributeType(QAttribute.VertexAttribute)
        pos_attr.setBuffer(vertex_color_buffer)
        pos_attr.setVertexBaseType(QAttribute.Float)
        pos_attr.setVertexSize(3)
        pos_attr.setByteOffset(0)
        pos_attr.setByteStride(stride)
        pos_attr.setCount(num_verts)
        pos_attr.setName(QAttribute.defaultPositionAttributeName())
        geo.addAttribute(pos_attr)

        self._col_attr = col_attr = QAttribute()
        col_attr.setAttributeType(QAttribute.VertexAttribute)
        col_attr.setBuffer(vertex_color_buffer)
        col_attr.setVertexBaseType(QAttribute.Float)
        col_attr.setVertexSize(3*sizeof_float)
        col_attr.setByteOffset(3*sizeof_float)
        col_attr.setByteStride(stride)
        col_attr.setCount(num_verts)
        col_attr.setName(QAttribute.defaultColorAttributeName())
        geo.addAttribute(col_attr)

        idx_list = [0, 1]
        idx_bytes = struct.pack('%sH' % len(idx_list), *idx_list)
        idx_bytearray = QByteArray(idx_bytes)
        idx_buffer = QBuffer(QBuffer.IndexBuffer)
        idx_buffer.setData(idx_bytearray)
        self._idx_attr = idx_attr = QAttribute()
        idx_attr.setAttributeType(QAttribute.IndexAttribute)
        idx_attr.setVertexBaseType(QAttribute.UnsignedShort)
        idx_attr.setBuffer(idx_buffer)
        idx_attr.setCount(len(idx_list))
        geo.addAttribute(idx_attr)

        mesh.setPrimitiveRestartEnabled(True)
        mesh.setFirstInstance(0)
        mesh.setFirstVertex(0)
        mesh.setInstanceCount(1)
        # mesh.setVerticesPerPatch(3)
        # mesh.setVertexCount(4)

        mesh.setGeometry(geo)
        # mesh.setPrimitiveType(QGeometryRenderer.Lines)
        mesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.addComponent(mesh)

        # trans = QTransform()
        # self.addComponent(trans)

        mat = QPerVertexColorMaterial(parent_entity)
        self.addComponent(mat)
    # end def
# end class
