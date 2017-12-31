import struct

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QVector3D
from PyQt5.Qt3DCore import QEntity
from PyQt5.Qt3DCore import QTransform
from PyQt5.Qt3DExtras import QPerVertexColorMaterial
from PyQt5.Qt3DRender import QAttribute
from PyQt5.Qt3DRender import QBuffer
from PyQt5.Qt3DRender import QGeometry
from PyQt5.Qt3DRender import QGeometryRenderer


class StrandLines(QEntity):
    def __init__(self, parent_entity):
        super(StrandLines, self).__init__(parent_entity)
        self._geometry = geom = StrandLinesGeometry(parent_entity)
        self._mesh = mesh = StrandLinesMesh(geom, parent_entity)
        self.addComponent(mesh)
        self._material = mat = QPerVertexColorMaterial(self)
        self.addComponent(mat)
        trans = QTransform()
        trans.setTranslation(QVector3D(1, 1, -1))
        # self.addComponent(trans)
    # end def

    ### SLOTS ###
    @pyqtSlot(int)
    def setStrandLinesAndColors(self, strand_vertex_lists, strand_color_list):
        self._geometry.updateBufferData(strand_vertex_lists, strand_color_list)


class StrandLinesMesh(QGeometryRenderer):
    def __init__(self, geometry, parent_entity):
        super(StrandLinesMesh, self).__init__(parent_entity)
        self.setGeometry(geometry)

        self.setPrimitiveRestartEnabled(True)
        self.setRestartIndexValue(65535)

        self.setFirstInstance(0)
        self.setFirstVertex(0)
        self.setInstanceCount(1)
        # self.setVerticesPerPatch(3)
        # self.setVertexCount(4)
        # self.setPrimitiveType(QGeometryRenderer.Lines)
        self.setPrimitiveType(QGeometryRenderer.LineStrip)


SIZEOF_FLOAT = len(struct.pack('f', 1.0))  # 4


class StrandLinesGeometry(QGeometry):
    def __init__(self, strand_vertex_lists=None, strand_color_list=None, parent_entity=None):
        super(StrandLinesGeometry, self).__init__(parent_entity)
        self.position_attribute = pos_attr = QAttribute()
        self.color_attribute = col_attr = QAttribute()
        self.index_attribute = idx_attr = QAttribute()

        self.pos_color_buffer = pos_col_buf = QBuffer(QBuffer.VertexBuffer)
        self.idx_buffer = idx_buf = QBuffer(QBuffer.IndexBuffer)

        stride = (3+3)*SIZEOF_FLOAT  # 24

        pos_attr.setAttributeType(QAttribute.VertexAttribute)
        pos_attr.setBuffer(pos_col_buf)
        pos_attr.setVertexBaseType(QAttribute.Float)
        pos_attr.setVertexSize(3)
        pos_attr.setByteOffset(0)
        pos_attr.setByteStride(stride)
        pos_attr.setName(QAttribute.defaultPositionAttributeName())

        col_attr.setAttributeType(QAttribute.VertexAttribute)
        col_attr.setBuffer(pos_col_buf)
        col_attr.setVertexBaseType(QAttribute.Float)
        col_attr.setVertexSize(3*SIZEOF_FLOAT)
        col_attr.setByteOffset(3*SIZEOF_FLOAT)
        col_attr.setByteStride(stride)
        col_attr.setName(QAttribute.defaultColorAttributeName())

        idx_attr.setAttributeType(QAttribute.IndexAttribute)
        idx_attr.setVertexBaseType(QAttribute.UnsignedShort)
        idx_attr.setBuffer(idx_buf)

        self.updateBufferData([], [])

        self.addAttribute(pos_attr)
        self.addAttribute(col_attr)
        self.addAttribute(idx_attr)
    # end def

    def updateBufferData(self, strand_vertex_lists, strand_color_list):
        # try:
        #     num_strands = len(strand_vertex_lists)
        #     num_colors = len(strand_color_list)
        #     assert(num_strands == num_strands)
        # except AssertionError:
        #     print("Strand vertex_list count != Strand color count")
        #     raise
        pos_color_list = \
        [ -1,  1, -1, 0.8, 0.8, 0.8,  # noqa
          -1, -1, -1, 0.8, 0.8, 0.8,  # noqa
           1, -1, -1, 0.8, 0.8, 0.8,  # noqa
           1,  1, -1, 0.8, 0.8, 0.8,  # noqa
          -1,  1,  1, 0.8, 0.8, 0.8,  # noqa
          -1, -1,  1, 0.8, 0.8, 0.8,  # noqa
           1, -1,  1, 0.8, 0.8, 0.8,  # noqa
           1,  1,  1, 0.8, 0.8, 0.8,  # noqa
          ]  # noqa
        pos_color_bytes = struct.pack('%sf' % len(pos_color_list), *pos_color_list)
        pos_color_bytearray = QByteArray(pos_color_bytes)
        self.pos_color_buffer.setData(pos_color_bytearray)

        idx_list = [0, 1, 2, 3, 0, 2, 65535, 4, 5, 6, 7, 4, 6]
        idx_bytes = struct.pack('%sH' % len(idx_list), *idx_list)
        idx_bytearray = QByteArray(idx_bytes)
        self.idx_buffer.setData(idx_bytearray)

        # setCount is required
        num_verts = int(len(pos_color_list)/6)
        num_indices = len(idx_list)
        self.position_attribute.setCount(num_verts)
        self.color_attribute.setCount(num_verts)
        self.index_attribute.setCount(num_indices)
    # end def
# end class
