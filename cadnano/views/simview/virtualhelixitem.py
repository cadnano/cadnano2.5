# encoding: utf-8

import struct

import numpy as np
from PyQt5.QtCore import QByteArray
from PyQt5.Qt3DCore import QEntity
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


class SimVirtualHelixItem(AbstractVirtualHelixItem, QEntity):
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

    def __init__(self, model_virtual_helix, part_item_entity):
        """Summary

        Args:
            model_virtual_helix (VirtualHelix):
            part_item_entity (QEntity): Description
            viewroot_entity (QEntity): Description
        """
        AbstractVirtualHelixItem.__init__(self, model_virtual_helix, part_item_entity)
        QEntity.__init__(self, part_item_entity)
        # _id_num, _model_part, _model_vh, _part_item, is_active
        self._getActiveTool = part_item_entity._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self._strand_items = set()

        axis_pts, fwd_pts, rev_pts = self._model_part.getCoordinates(self._id_num)
        self._geometry = geom = StrandLines3DGeometry(fwd_pts, rev_pts, self)
        self._mesh = mesh = StrandLines3DMesh(geom, self)
        self._material = mat = QPerVertexColorMaterial(self)
        self.addComponent(mesh)
        self.addComponent(mat)
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
        # print("[simview] vhi: strandAdded slot")
        strand_item = StrandItem(strand, self)
        self.addStrand3D(strand, strand_item)
    # end def

    def partVirtualHelixRemovedSlot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        # self.view().levelOfDetailChangedSignal.disconnect(self.levelOfDetailChangedSlot)
        print("[simview] vhi: partVirtualHelixRemovedSlot")
        # todo: remove StrandLines3D components and entity
        self._controller.disconnectSignals()
        self._controller = None
        self._model_part = None
        self._model_vh = None
        self._part_item = None
        self._getActiveTool = None
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
    def window(self):
        return self._part_item.window()
    # end def

    ### PUBLIC METHODS ###
    def addStrand3D(self, strand, strand_item):
        self._strand_items.add(strand_item)
        if strand.isForward():
            pass
    # end def

    def removeStrand3D(self, strand_item):
        self._strand_items.remove(strand_item)
    # end def

    def resizeStrand3D(self, strand, indices):
        pass
    # end def

    def updateStrandColor3D(self, strand):
        pass
    # end def

    def updateStrandConnections3D(self, strand):
        pass
    # end def
# end class


# https://www.khronos.org/opengl/wiki/Vertex_Rendering#Primitive_Restart
GL_PRIMITIVE_RESTART_INDEX = 65535
SIZEOF_FLOAT = len(struct.pack('f', 1.0))  # 4


class StrandLines3DMesh(QGeometryRenderer):
    def __init__(self, geometry, parent_entity):
        super(StrandLines3DMesh, self).__init__(parent_entity)
        self.setGeometry(geometry)
        self.setPrimitiveRestartEnabled(True)
        self.setRestartIndexValue(GL_PRIMITIVE_RESTART_INDEX)
        self.setFirstInstance(0)
        self.setFirstVertex(0)
        self.setInstanceCount(1)
        self.setPrimitiveType(QGeometryRenderer.LineStrip)
    # end def
# end class


class StrandLines3DGeometry(QGeometry):
    def __init__(self, fwd_pts, rev_pts, parent_entity=None):
        super(StrandLines3DGeometry, self).__init__(parent_entity)
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
