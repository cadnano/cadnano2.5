import struct

from PyQt5.QtCore import QByteArray
# from PyQt5.QtGui import QVector3D, QVector4D

from PyQt5.Qt3DCore import QEntity
from PyQt5.Qt3DExtras import QPerVertexColorMaterial
from PyQt5.Qt3DRender import QAttribute
from PyQt5.Qt3DRender import QBuffer
from PyQt5.Qt3DRender import QGeometry, QGeometryRenderer


class Line(QEntity):
    def __init__(self, parent_entity):
        super(Line, self).__init__(parent_entity)
        self._mesh = mesh = QGeometryRenderer(parent_entity)
        self._geometry = geo = QGeometry(mesh)

        # vertex_list = [
        #     2.0, 0.0, 0.0,
        #     0.0, 0.0, 2.0,
        # ]

        # color_list = [
        #     0.0, 1.0, 0.0,  # green
        #     0.0, 1.0, 0.0  # green
        # ]

        vertex_color_list = [
            2.0, 0.0, 0.0,
            0.0, 2.0, 0.0,
            1.0, 0.0, 0.0,  # red
            2.0, 0.0, 0.0,
            2.0, 2.0, -2.0,
            0.0, 1.0, 0.0  # green
        ]

        # vertex_color_list = [
        #     0.0, 2.0, 0.0,
        #     1.0, 0.0, 0.0,  # green
        #     2.0, 2.0, -2.0,
        #     1.0, 0.0, 0.0  # green
        # ]

        vertex_color_bytes = struct.pack('!%sf' % len(vertex_color_list), *vertex_color_list)
        vertex_color_bytearray = QByteArray(vertex_color_bytes)
        vertex_color_buffer = QBuffer(QBuffer.VertexBuffer)
        vertex_color_buffer.setData(vertex_color_bytearray)
        print("vertex_color_bytes size", vertex_color_bytearray.size())

        # sizeof_float = len(struct.pack('!f', 1.0))  # 4
        # sizeof_float = 4
        stride = 4  # (3+3)*sizeof_float
        num_verts = 4

        self._pos_attr = pos_attr = QAttribute()
        pos_attr.setAttributeType(QAttribute.VertexAttribute)
        pos_attr.setBuffer(vertex_color_buffer)
        pos_attr.setVertexBaseType(QAttribute.Float)
        pos_attr.setVertexSize(3)
        pos_attr.setByteOffset(1)
        pos_attr.setByteStride(stride)
        pos_attr.setCount(num_verts)
        pos_attr.setName(QAttribute.defaultPositionAttributeName())
        geo.addAttribute(pos_attr)

        self._col_attr = col_attr = QAttribute()
        col_attr.setAttributeType(QAttribute.VertexAttribute)
        col_attr.setBuffer(vertex_color_buffer)
        col_attr.setVertexBaseType(QAttribute.Float)
        col_attr.setVertexSize(3)
        col_attr.setByteOffset(1)
        col_attr.setByteStride(stride)
        col_attr.setCount(2)
        col_attr.setName(QAttribute.defaultColorAttributeName())
        geo.addAttribute(col_attr)

        # idx_list = [0, 1]
        # idx_bytes = struct.pack('!%sH' % len(idx_list), *idx_list)
        # idx_bytearray = QByteArray(idx_bytes)
        # idx_buffer = QBuffer(QBuffer.IndexBuffer)
        # idx_buffer.setData(idx_bytearray)
        # self._idx_attr = idx_attr = QAttribute()
        # idx_attr.setAttributeType(QAttribute.IndexAttribute)
        # idx_attr.setVertexBaseType(QAttribute.UnsignedShort)
        # idx_attr.setBuffer(idx_buffer)
        # idx_attr.setCount(len(idx_list))
        # geo.addAttribute(idx_attr)

        # mesh.setPrimitiveRestartEnabled(True)
        mesh.setFirstInstance(0)
        mesh.setFirstVertex(0)
        mesh.setInstanceCount(1)
        # mesh.setVerticesPerPatch(3)
        # mesh.setVertexCount(4)

        mesh.setGeometry(geo)
        mesh.setPrimitiveType(QGeometryRenderer.Lines)
        self.addComponent(mesh)

        # trans = QTransform()
        # self.addComponent(trans)

        mat = QPerVertexColorMaterial(parent_entity)
        self.addComponent(mat)
    # end def

    def setPosVertexSize(self, val):
        self._pos_attr.setVertexSize(val)

    def setPosByteOffset(self, val):
        self._pos_attr.setByteOffset(val)

    def setPosByteStride(self, val):
        self._pos_attr.setByteStride(val)

    def setPosCount(self, val):
        self._pos_attr.setPosCount(val)

    def setColVertexSize(self, val):
        self._col_attr.setVertexSize(val)

    def setColByteOffset(self, val):
        self._col_attr.setByteOffset(val)

    def setColByteStride(self, val):
        self._col_attr.setByteStride(val)

    def setColCount(self, val):
        self._col_attr.setCount(val)

    def setByteStride(self, val):
        self._pos_attr.setByteStride(val)
        # self._norm_attr.setByteStride(val)
        self._col_attr.setByteStride(val)

# end class
