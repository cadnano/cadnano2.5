# encoding: utf-8

from math import atan2, sqrt

from PyQt5.QtGui import QVector3D, QQuaternion
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import QCylinderMesh, QSphereMesh
from PyQt5.Qt3DExtras import QGoochMaterial
from PyQt5.Qt3DExtras import QPhongAlphaMaterial

from cadnano import util
from cadnano.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import getColorObj
from cadnano.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem

from .customshapes import Points

_CYLINDER_RADIUS = 1.0
_CYLINDER_RINGS = 20
_CYLINDER_SLICES = 10

_SPHERE_RADIUS = 0.25
_SPHERE_RINGS = 8
_SPHERE_SLICES = 8


def v2DistanceAndAngle(a, b):
    """Summary

    Args:
        a (TYPE): Description
        b (TYPE): Description

    Returns:
        TYPE: Description
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = sqrt(dx*dx + dy*dy)
    angle = atan2(dy, dx)
    return dist, angle


class Cylinder(QEntity):
    """docstring for Cube"""

    def __init__(self, x, y, z, length, color, parent_entity):
        super(Cylinder, self).__init__(parent_entity)
        self._x = x
        self._y = y
        self._z = -z
        self._length = length
        self._color = color
        self._parent_entity = parent_entity
        self._mesh = mesh = QCylinderMesh()
        self._trans = trans = QTransform()
        self._mat = mat = QGoochMaterial()
        self._mat = mat = QPhongAlphaMaterial()
        mat.setAlpha(0.5)

        # mat.setCool(getColorObj("#0000cc"))
        # mat.setWarm(getColorObj("#cccc00"))

        mesh.setRadius(_CYLINDER_RADIUS)
        mesh.setRings(_CYLINDER_RINGS)
        mesh.setSlices(_CYLINDER_SLICES)
        mesh.setLength(length)

        trans.setTranslation(QVector3D(x, y, -z))
        trans.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(1.0, 0.0, 0.0), 90.0))

        # print(mat.cool().name(), mat.warm().name())
        mat.setDiffuse(getColorObj(color))

        self.addComponent(mesh)
        self.addComponent(trans)
        self.addComponent(mat)


class Sphere(QEntity):
    """docstring for Cube"""

    def __init__(self, x, y, z, color, parent_entity):
        super(Sphere, self).__init__(parent_entity)
        self._x = x
        self._y = y
        self._z = -z
        self._parent_entity = parent_entity

        self._mesh = mesh = QSphereMesh()
        self._trans = trans = QTransform()
        self._mat = mat = QGoochMaterial()
        self._color = color

        mat.setCool(getColorObj("#0000cc"))
        mat.setWarm(getColorObj(color))

        mesh.setRings(_SPHERE_RINGS)
        mesh.setSlices(_SPHERE_SLICES)
        mesh.setRadius(_SPHERE_RADIUS)

        trans.setTranslation(QVector3D(x, y, -z))

        self.addComponent(mesh)
        self.addComponent(trans)
        self.addComponent(mat)


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
        self._model_vh = m_vh = model_virtual_helix
        self._part_entity = part_item.entity()
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        id_num = m_vh.idNum()
        axis_pts, fwd_pts, rev_pts = self._model_part.getCoordinates(id_num)

        x, y, z = axis_pts[0]
        length = axis_pts[-1][2] - axis_pts[0][2]

        # m_p = self._model_part
        # x, y = m_p.locationQt(self._id_num, part_item.scaleFactor())
        # z = 0
        # length = 42.*0.34  # hard coding for now
        # vh_z, vh_length = m_p.getVirtualHelixProperties(self._id_num, ['z', 'length'])
        # length = vh_length * m_p.baseWidth()

        self.cylinder = Cylinder(x, y, z+length/2., length, '#cccc00', self._part_entity)

    # end def

    ### SIGNALS ###

    ### SLOTS indirectly called from the part ###

    def levelOfDetailChangedSlot(self, boolval):
        """Not connected to the model, only the QGraphicsView

        Args:
            boolval (TYPE): Description
        """
        pass
        # pen = self.pen()
        # pen.setCosmetic(boolval)
        # print("levelOfDetailChangedSlot", boolval, pen.width())
        # if boolval:
        #     pass
        # else:
        #     pass
        # self.setPen(pen)
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').

        Args:
            sender (obj): Model object that emitted the signal.
            strand (TYPE): Description
        """
        # print("strandAddedSlot", sender, strand)

        id_num = sender.idNum()
        color = strand.getColor()
        axis_pts, fwd_pts, rev_pts = self._model_part.getCoordinates(id_num)
        pts = fwd_pts if sender.isForward() else rev_pts

        Points(axis_pts, color, self._part_entity)

        # idx_low, idx_high = strand.idxs()
        # for idx in range(idx_low, idx_high+1):
        #     # print(idx, pts[idx])
        #     x, y, z = pts[idx]  # + axis_pts[idx]
        #     Sphere(x, y, z, strand.getColor(), self._part_entity)
        # StrandItem(strand, self, self._viewroot)
    # end def

    def virtualHelixRemovedSlot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        # self.view().levelOfDetailChangedSignal.disconnect(self.levelOfDetailChangedSlot)
        self._controller.disconnectSignals()
        self._controller = None

        # self.removeComponent(self.cylinder_3d)
        # self.removeComponent(self.material_3d)
        # self.removeComponent(self.transform_3d)

        # scene = self.scene()
        # self._handle.remove()
        # scene.removeItem(self)
        self._part_entity = None
        self._model_part = None
        self._getActiveTool = None
        self._handle = None
    # end def

    def virtualHelixPropertyChangedSlot(self, keys, values):
        """Summary

        Args:
            keys (TYPE): Description
            values (TYPE): Description

        Returns:
            TYPE: Description
        """
        pass
        # for key, val in zip(keys, values):
        #     if key == 'is_visible':
        #         if val:
        #             self.show()
        #             self._handle.show()
        #             self.showXoverItems()
        #         else:
        #             self.hideXoverItems()
        #             self.hide()
        #             self._handle.hide()
        #             return
        #     if key == 'z':
        #         part_entity = self._part_entity
        #         z = part_entity.convertToQtZ(val)
        #         if self.x() != z:
        #             self.setX(z)
        #             """ The handle is selected, so deselect to
        #             accurately position then reselect
        #             """
        #             vhi_h = self._handle
        #             vhi_h.tempReparent()
        #             vhi_h.setX(z - _VH_XOFFSET)
        #             # if self.isSelected():
        #             #     print("ImZ", self.idNum())
        #             part_entity.updateXoverItems(self)
        #             vhi_h_selection_group = self._viewroot.vhiHandleSelectionGroup()
        #             vhi_h_selection_group.addToGroup(vhi_h)
        #     elif key == 'eulerZ':
        #         self._handle.rotateWithCenterOrigin(val)
        #         # self._prexoveritemgroup.updatePositionsAfterRotation(value)
        #     ### GEOMETRY PROPERTIES ###
        #     elif key == 'repeat_hint':
        #         pass
        #         # self.updateRepeats(int(val))
        #     elif key == 'bases_per_repeat':
        #         pass
        #         # self.updateBasesPerRepeat(int(val))
        #     elif key == 'turns_per_repeat':
        #         # self.updateTurnsPerRepeat(int(val))
        #         pass
        #     ### RUNTIME PROPERTIES ###
        #     elif key == 'neighbors':
        #         # this means a virtual helix in the slice view has moved
        #         # so we need to clear and redraw the PreXoverItems just in case
        #         if self.isActive():
        #             self._part_entity.setPreXoverItemsVisible(self)
        # self.refreshPath()
    # end def

    ### ACCESSORS ###
    def viewroot(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._viewroot
    # end def

    def window(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._part_entity.window()
    # end def
