import struct

from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QVector3D

from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import QCuboidMesh
from PyQt5.Qt3DExtras import QPhongAlphaMaterial
# from PyQt5.Qt3DExtras import QGoochMaterial
from PyQt5.Qt3DExtras import QPerVertexColorMaterial
from PyQt5.Qt3DRender import QAttribute
from PyQt5.Qt3DRender import QBuffer
from PyQt5.Qt3DRender import QGeometry, QGeometryRenderer

from cadnano.gui.palette import getColorObj


class Cube(QEntity):
    """docstring for Cube"""

    def __init__(self, x, y, z, l, w, h, color, parent_entity):
        super(Cube, self).__init__(parent_entity)
        self._x = x
        self._y = y
        self._z = z
        self._l = l
        self._w = w
        self._h = h
        self._color = color
        self._parent_entity = parent_entity
        self._mesh = mesh = QCuboidMesh()
        self._trans = trans = QTransform()
        self._mat = mat = QPhongAlphaMaterial()

        mesh.setXExtent(l)
        mesh.setYExtent(w)
        mesh.setZExtent(h)

        trans.setTranslation(QVector3D(x, y, z))

        mat.setDiffuse(getColorObj(color))
        mat.setAlpha(0.25)

        self.addComponent(mesh)
        self.addComponent(trans)
        self.addComponent(mat)

    def setAlpha(self, value):
        self._mat.setAlpha(value)


class Line(QEntity):
    def __init__(self, parent_entity):
        super(Line, self).__init__(parent_entity)

        v0 = QVector3D(0.0, 0.0, 0.0)
        v1 = QVector3D(1.0, 0.0, 0.0)
        v2 = QVector3D(0.0, 0.0, 2.0)
        v3 = QVector3D(0.0, 1.0, 1.0)

        self._mesh = mesh = QGeometryRenderer(parent_entity)
        self._geometry = geo = QGeometry(mesh)

        vertexDataBuffer = QBuffer(QBuffer.VertexBuffer, geo)

        vertices = [v0, v1, v2, v3]
        # vertices = [v3]
        vert_bytes = bytes()
        for v in vertices:
            vert_bytes += struct.pack('!f', v.x())
            vert_bytes += struct.pack('!f', v.y())
            vert_bytes += struct.pack('!f', v.z())

        # See if we can unpack our stored values
        i = 0
        vals = []
        for val in struct.iter_unpack('!f', vert_bytes):
            vals.append(val[0])
            i += 1
            if i % 3 == 0:
                print(vals)
                vals = []

        vertexBufferData = QByteArray(vert_bytes)
        vertexDataBuffer.setData(vertexBufferData)

        float_size = len(struct.pack('!f', 1.0))  # 4

        # Attributes
        positionAttribute = QAttribute()
        positionAttribute.setAttributeType(QAttribute.VertexAttribute)
        positionAttribute.setBuffer(vertexDataBuffer)
        positionAttribute.setVertexBaseType(QAttribute.Float)
        positionAttribute.setVertexSize(3)
        positionAttribute.setByteOffset(0)
        positionAttribute.setByteStride(3)
        # positionAttribute.setCount(4)
        positionAttribute.setName(QAttribute.defaultPositionAttributeName())

        colorAttribute = QAttribute()
        colorAttribute.setAttributeType(QAttribute.VertexAttribute)
        colorAttribute.setBuffer(vertexDataBuffer)
        colorAttribute.setVertexBaseType(QAttribute.Float)
        colorAttribute.setVertexSize(3)
        colorAttribute.setByteOffset(3 * float_size)
        colorAttribute.setByteStride(9 * float_size)
        colorAttribute.setCount(4)
        colorAttribute.setName(QAttribute.defaultColorAttributeName())
        # See if we can unpack our stored values
        # i = 0
        # vals = []
        # for val in struct.iter_unpack('!f', positionAttribute.buffer().data()):
        #     vals.append(val[0])
        #     i += 1
        #     if i % 9 == 0:
        #         print(vals)
        #         vals = []

        geo.addAttribute(positionAttribute)
        # geo.addAttribute(normalAttribute)
        geo.addAttribute(colorAttribute)
        # geo.addAttribute(indexAttribute)

        mesh.setFirstInstance(0)
        mesh.setFirstVertex(0)
        mesh.setInstanceCount(4)
        mesh.setPrimitiveType(QGeometryRenderer.LineStrip)
        # mesh.setVertexCount(4)
        mesh.setGeometry(geo)

        trans = QTransform()
        # trans.setTranslation(QVector3D(x, y, -z))
        mat = QPerVertexColorMaterial(parent_entity)

        self.addComponent(mesh)
        self.addComponent(trans)
        self.addComponent(mat)


class TetrahedronMesh(QEntity):
    """docstring for TetrahedronMesh"""

    def __init__(self, x, y, z, parent_entity):
        super(TetrahedronMesh, self).__init__(parent_entity)
        self._x = x
        self._y = y
        self._z = -z
        self._parent_entity = parent_entity

        self._mesh = mesh = QGeometryRenderer(parent_entity)
        self._geometry = geo = QGeometry(mesh)

        vertexDataBuffer = QBuffer(QBuffer.VertexBuffer, geo)
        indexDataBuffer = QBuffer(QBuffer.IndexBuffer, geo)

        # Vertices
        v0 = QVector3D(-1.0, 0.0, -1.0)
        v1 = QVector3D(1.0, 0.0, -1.0)
        v2 = QVector3D(0.0, 1.0, 0.0)
        v3 = QVector3D(0.0, 0.0, 1.0)

        # Faces Normals
        n023 = QVector3D.normal(v0, v2, v3)  # 0.816, -0.408, -0.408
        n012 = QVector3D.normal(v0, v1, v2)  # 0.0, -0.707,  0.707
        n310 = QVector3D.normal(v3, v1, v0)  # 0.0, 1.0, 0.0
        n132 = QVector3D.normal(v1, v3, v2)  # -0.816, -0.408, -0.408

        # Vector Normals
        n0 = QVector3D(n023 + n012 + n310).normalized()  # 0.931, -0.132, 0.341
        n1 = QVector3D(n132 + n012 + n310).normalized()  # -0.931, -0.132, 0.341
        n2 = QVector3D(n132 + n012 + n023).normalized()  # 0.0, -0.997, -0.072
        n3 = QVector3D(n132 + n310 + n023).normalized()  # 0.0, 0.219, -0.976

        # Colors
        c0 = QVector3D(1.0, 0.0, 0.0)  # red
        c1 = QVector3D(0.0, 1.0, 0.0)  # green
        c2 = QVector3D(0.0, 0.0, 1.0)  # blue
        c3 = QVector3D(1.0, 1.0, 1.0)  # white

        vertices = [v0, n0, c0, v1, n1, c1, v2, n2, c2, v3, n3, c3]
        vert_bytes = bytes()
        for v in vertices:
            vert_bytes += struct.pack('!f', v.x())
            vert_bytes += struct.pack('!f', v.y())
            vert_bytes += struct.pack('!f', v.z())

        # See if we can unpack our stored values
        # i = 0
        # vals = []
        # for val in struct.iter_unpack('!f', vert_bytes):
        #     vals.append(val[0])
        #     i += 1
        #     if i % 9 == 0:
        #         print(vals)
        #         vals = []

        vertexBufferData = QByteArray(vert_bytes)
        print("vertexBufferData size", vertexBufferData.size())
        vertexDataBuffer.setData(vertexBufferData)

        idx_bytes = bytes()
        # Front
        idx_bytes += struct.pack('!H', 0)
        idx_bytes += struct.pack('!H', 1)
        idx_bytes += struct.pack('!H', 2)
        # Bottom
        idx_bytes += struct.pack('!H', 3)
        idx_bytes += struct.pack('!H', 1)
        idx_bytes += struct.pack('!H', 0)
        # Left
        idx_bytes += struct.pack('!H', 0)
        idx_bytes += struct.pack('!H', 2)
        idx_bytes += struct.pack('!H', 3)
        # Right
        idx_bytes += struct.pack('!H', 1)
        idx_bytes += struct.pack('!H', 3)
        idx_bytes += struct.pack('!H', 2)

        indexBufferData = QByteArray(idx_bytes)
        print("indexBufferData size", indexBufferData.size())
        indexDataBuffer.setData(indexBufferData)

        float_size = len(struct.pack('!f', 1.0))  # 4
        ushort_size = len(struct.pack('!H', 1))  # 2

        # Attributes
        positionAttribute = QAttribute()
        positionAttribute.setAttributeType(QAttribute.VertexAttribute)
        positionAttribute.setBuffer(vertexDataBuffer)
        positionAttribute.setVertexBaseType(QAttribute.Float)
        positionAttribute.setVertexSize(3)
        positionAttribute.setByteOffset(0)
        positionAttribute.setByteStride(9)
        # positionAttribute.setByteStride(9 * float_size)
        positionAttribute.setCount(4)
        positionAttribute.setName(QAttribute.defaultPositionAttributeName())

        normalAttribute = QAttribute()
        normalAttribute.setAttributeType(QAttribute.VertexAttribute)
        normalAttribute.setBuffer(vertexDataBuffer)
        normalAttribute.setVertexBaseType(QAttribute.Float)
        normalAttribute.setVertexSize(3)
        normalAttribute.setByteOffset(3 * float_size)
        normalAttribute.setByteStride(9)
        # normalAttribute.setByteStride(9 * float_size)
        normalAttribute.setCount(4)
        normalAttribute.setName(QAttribute.defaultNormalAttributeName())

        colorAttribute = QAttribute()
        colorAttribute.setAttributeType(QAttribute.VertexAttribute)
        colorAttribute.setBuffer(vertexDataBuffer)
        colorAttribute.setVertexBaseType(QAttribute.Float)
        colorAttribute.setVertexSize(3)
        colorAttribute.setByteOffset(6 * float_size)
        colorAttribute.setByteStride(9)
        # colorAttribute.setByteStride(9 * float_size)
        colorAttribute.setCount(4)
        colorAttribute.setName(QAttribute.defaultColorAttributeName())

        indexAttribute = QAttribute()
        indexAttribute.setAttributeType(QAttribute.IndexAttribute)
        indexAttribute.setBuffer(indexDataBuffer)
        indexAttribute.setVertexBaseType(QAttribute.UnsignedShort)
        indexAttribute.setVertexSize(1)
        indexAttribute.setByteOffset(0)
        indexAttribute.setByteStride(ushort_size)
        indexAttribute.setCount(12)

        # See if we can unpack our stored values
        # i = 0
        # vals = []
        # for val in struct.iter_unpack('!f', positionAttribute.buffer().data()):
        #     vals.append(val[0])
        #     i += 1
        #     if i % 9 == 0:
        #         print(vals)
        #         vals = []

        geo.addAttribute(positionAttribute)
        geo.addAttribute(normalAttribute)
        geo.addAttribute(colorAttribute)
        geo.addAttribute(indexAttribute)

        mesh.setFirstInstance(0)
        mesh.setFirstVertex(0)
        mesh.setInstanceCount(1)
        mesh.setPrimitiveType(QGeometryRenderer.Triangles)
        mesh.setVertexCount(4)
        mesh.setGeometry(geo)

        trans = QTransform()
        trans.setTranslation(QVector3D(x, y, -z))
        mat = QPerVertexColorMaterial(parent_entity)

        self.addComponent(mesh)
        self.addComponent(trans)
        self.addComponent(mat)
    # end def
# end class


# bool LayerMesh::initialize(Qt3DCore::QEntity *parent)
# {
#     meshRenderer = new Qt3DRender::QGeometryRenderer;
#     geometry = new Qt3DRender::QGeometry(meshRenderer);

#     vertexDataBuffer = new Qt3DRender::QBuffer(Qt3DRender::QBuffer::VertexBuffer, geometry);
#     indexDataBuffer = new Qt3DRender::QBuffer(Qt3DRender::QBuffer::IndexBuffer, geometry);

#     int lineSize = 4;
#     int hLineSize = ((qAbs(netX1 - netX0) / netMajorStep) + 1) * lineSize * 3;
#     int vLineSize = ((qAbs(netZ1 - netZ0) / netMajorStep) + 1) * lineSize * 3;
#     int vertexNum = hLineSize + vLineSize;

#     float* vertexRawData = new float[vertexNum];
#     int idx = 0;
#     QColor majorColor = QColor(220,220,220);
#     QColor minorColor = QColor(243,243,243);
#     for(float x = netX0; x <= netX1; x += netMajorStep)
#     {
#         vertexRawData[idx++] = x; vertexRawData[idx++] = netY; vertexRawData[idx++] = netZ0;
#         vertexRawData[idx++] = majorColor.redF(); vertexRawData[idx++] = majorColor.greenF();
#         vertexRawData[idx++] = majorColor.blueF();
#         vertexRawData[idx++] = x; vertexRawData[idx++] = netY; vertexRawData[idx++] = netZ1;
#         vertexRawData[idx++] = majorColor.redF(); vertexRawData[idx++] = majorColor.greenF();
#         vertexRawData[idx++] = majorColor.blueF();
#     }

#     for(float z = netZ0; z <= netZ1; z += netMajorStep)
#     {
#         vertexRawData[idx++] = netX0; vertexRawData[idx++] = netY; vertexRawData[idx++] = z;
#         vertexRawData[idx++] = majorColor.redF(); vertexRawData[idx++] = majorColor.greenF();
#         vertexRawData[idx++] = majorColor.blueF();
#         vertexRawData[idx++] = netX1; vertexRawData[idx++] = netY; vertexRawData[idx++] = z;
#         vertexRawData[idx++] = majorColor.redF(); vertexRawData[idx++] = majorColor.greenF();
#         vertexRawData[idx++] = majorColor.blueF();
#     }

#     QByteArray ba;
#     int bufferSize = vertexNum * sizeof(float);
#     ba.resize(bufferSize);
#     memcpy(ba.data(), reinterpret_cast<const char*>(vertexRawData), bufferSize);
#     vertexDataBuffer->setData(ba);

#     int stride = 6 * sizeof(float);

#     // Attributes
#     Qt3DRender::QAttribute *positionAttribute = new Qt3DRender::QAttribute();
#     positionAttribute->setAttributeType(Qt3DRender::QAttribute::VertexAttribute);
#     positionAttribute->setBuffer(vertexDataBuffer);
#     positionAttribute->setDataType(Qt3DRender::QAttribute::Float);
#     positionAttribute->setDataSize(3);
#     positionAttribute->setByteOffset(0);
#     positionAttribute->setByteStride(stride);
#     positionAttribute->setCount(vertexNum / 2);
#     positionAttribute->setName(Qt3DRender::QAttribute::defaultPositionAttributeName());


#     Qt3DRender::QAttribute *colorAttribute = new Qt3DRender::QAttribute();
#     colorAttribute->setAttributeType(Qt3DRender::QAttribute::VertexAttribute);
#     colorAttribute->setBuffer(vertexDataBuffer);
#     colorAttribute->setDataType(Qt3DRender::QAttribute::Float);
#     colorAttribute->setDataSize(3);
#     colorAttribute->setByteOffset(3 * sizeof(float));
#     colorAttribute->setByteStride(stride);
#     colorAttribute->setCount(vertexNum / 2);
#     colorAttribute->setName(Qt3DRender::QAttribute::defaultColorAttributeName());

#     geometry->addAttribute(positionAttribute);
#     geometry->addAttribute(colorAttribute);

#     meshRenderer->setInstanceCount(1);
#     meshRenderer->setIndexOffset(0);
#     meshRenderer->setFirstInstance(0);
#     meshRenderer->setPrimitiveType(Qt3DRender::QGeometryRenderer::Lines);
#     meshRenderer->setGeometry(geometry);
#     meshRenderer->setVertexCount(vertexNum / 2);

#     material = new Qt3DExtras::QPerVertexColorMaterial(parentEntity);
#     transform = new Qt3DCore::QTransform;
#     transform->setScale(1.0f);

#     Qt3DCore::QEntity *entity = new Qt3DCore::QEntity(parentEntity);
#     entity->addComponent(meshRenderer);
#     entity->addComponent(transform);
#     entity->addComponent(material);

#     entity->setParent(parentEntity);

#     return true;
# }
