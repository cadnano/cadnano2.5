# encoding: utf-8

import struct

import numpy as np
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

from cadnano import util
from cadnano.controllers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import getColorObj
from cadnano.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem

from .strand.stranditem import StrandItem

# from .customshapes import Points
# from .strandlines import StrandLines


class SimVirtualHelixItem(AbstractVirtualHelixItem):
    """VirtualHelixItem for PathView

    Attributes:
        drag_last_position (TYPE): Description
        FILTER_NAME (str): Description
        findChild (TYPE): Description
        handle_start (TYPE): Description
        is_active (bool): Description
    """
    findChild = util.findChild  # for debug
    FILTER_NAME = "virtual_helix"

    def __init__(self, model_virtual_helix, part_item, viewroot):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            part_entity (TYPE): Description
            viewroot (TYPE): Description
        """
        AbstractVirtualHelixItem.__init__(self, model_virtual_helix, part_item)
        # Done in AbstractVirtualHelixItem init
        # self._model_vh = model_virtual_helix
        # self._id_num = model_virtual_helix.idNum() if model_virtual_helix is not None else None
        # self._part_item = parent
        # self._model_part = model_virtual_helix.part() if model_virtual_helix is not None else None
        # self.is_active = False

        self._part_entity = part_item.entity()
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, True, True)

        axis_pts, fwd_pts, rev_pts = self._model_part.getCoordinates(self._id_num)
        self.strand_lines = StrandLines(fwd_pts, rev_pts, self._part_entity)
    # end def

    ### SIGNALS ###

    ### SLOTS indirectly called from the part ###
    def levelOfDetailChangedSlot(self, boolval):
        pass
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand. The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').

        Args:
            sender (obj): Model object that emitted the signal.
            strand (TYPE): Description
        """
        print("[simview] vhi: strandAdded slot")
        StrandItem(strand, self)
    # end def

    def partVirtualHelixRemovedSlot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        # self.view().levelOfDetailChangedSignal.disconnect(self.levelOfDetailChangedSlot)
        print("[simview] vhi: partVirtualHelixRemovedSlot")
        # todo: remove StrandLines components and entity
        # self._controller.disconnectSignals()
        self._controller = None
        self._part_entity = None
        self._model_part = None
        self._getActiveTool = None
        self._viewroot = None
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, keys, values):
        print("[simview] vhi: partVirtualHelixPropertyChangedSlot")
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender, id_num, virtual_helix):
        print("[simview] vhi: partVirtualHelixResizedSlot")
        pass
    # end def

    ### ACCESSORS ###
    def viewroot(self):
        return self._viewroot
    # end def

    def window(self):
        return self._part_entity.window()
    # end def
# end class


class StrandLines(QEntity):
    def __init__(self, fwd_pts, rev_pts, parent_entity):
        super(StrandLines, self).__init__(parent_entity)
        self._geometry = geom = StrandLinesGeometry(fwd_pts, rev_pts, parent_entity)
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


# https://www.khronos.org/opengl/wiki/Vertex_Rendering#Primitive_Restart
GL_PRIMITIVE_RESTART_INDEX = 65535


class StrandLinesMesh(QGeometryRenderer):
    def __init__(self, geometry, parent_entity):
        super(StrandLinesMesh, self).__init__(parent_entity)
        self.setGeometry(geometry)

        self.setPrimitiveRestartEnabled(True)
        self.setRestartIndexValue(GL_PRIMITIVE_RESTART_INDEX)

        self.setFirstInstance(0)
        self.setFirstVertex(0)
        self.setInstanceCount(1)
        # self.setVerticesPerPatch(3)
        # self.setVertexCount(4)
        # self.setPrimitiveType(QGeometryRenderer.Lines)
        self.setPrimitiveType(QGeometryRenderer.LineStrip)


SIZEOF_FLOAT = len(struct.pack('f', 1.0))  # 4


class StrandLinesGeometry(QGeometry):
    def __init__(self, fwd_pts, rev_pts, parent_entity=None):
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

        self.updateBufferData(fwd_pts, rev_pts)

        self.addAttribute(pos_attr)
        self.addAttribute(col_attr)
        self.addAttribute(idx_attr)
    # end def

    def updateBufferData(self, fwd_pts, rev_pts):
        num_fwd_pts = len(fwd_pts)
        num_rev_pts = len(rev_pts)
        num_verts = num_fwd_pts+num_rev_pts

        fwd_rev_pts = np.concatenate((fwd_pts, rev_pts))
        zcorrected_pts = fwd_rev_pts  # * (1, 1, -1)  # correct for GL -z

        fr, fg, fb, falpha = getColorObj('#0066cc').getRgbF()
        rr, rg, rb, falpha = getColorObj('#cc0000').getRgbF()
        fwd_colors = [[fr, fg, fb] for i in range(num_fwd_pts)]
        rev_colors = [[rr, rg, rb] for i in range(num_rev_pts)]
        col_array = np.array(fwd_colors+rev_colors)

        pos_color_array = np.block([zcorrected_pts, col_array]).flatten()
        pos_color_bytearray = QByteArray(pos_color_array.astype('f').tostring())
        self.pos_color_buffer.setData(pos_color_bytearray)

        idx_list = list(range(num_fwd_pts)) + [GL_PRIMITIVE_RESTART_INDEX] + [p+num_rev_pts for p in range(num_rev_pts)]
        idx_bytes = struct.pack('%sH' % len(idx_list), *idx_list)
        idx_bytearray = QByteArray(idx_bytes)
        self.idx_buffer.setData(idx_bytearray)

        # setCount is always required
        self.position_attribute.setCount(num_verts)
        self.color_attribute.setCount(num_verts)
        self.index_attribute.setCount(len(idx_list))
    # end def
# end class
