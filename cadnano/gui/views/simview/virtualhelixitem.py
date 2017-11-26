#!/usr/bin/env python
"""Summary
"""
# encoding: utf-8

from math import atan2, sqrt

# from PyQt5.QtCore import QRectF, Qt
# from PyQt5.QtGui import QPainterPath

from PyQt5.QtGui import QVector3D, QQuaternion
from PyQt5.Qt3DCore import QEntity, QTransform
from PyQt5.Qt3DExtras import QCylinderMesh, QGoochMaterial, QPhongAlphaMaterial

from cadnano import util
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import getColorObj
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
# from .strand.stranditem import StrandItem
# from .strand.xoveritem import XoverNode3
# from . import pathstyles as styles

# _BASE_WIDTH = styles.PATH_BASE_WIDTH
# _VH_XOFFSET = styles.VH_XOFFSET

_CYLINDER_RADIUS = 1.1
_CYLINDER_RINGS = 100
_CYLINDER_SLICES = 20


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
        self._z = z
        self._length = length
        self._color = color
        self._parent_entity = parent_entity
        self._mesh = mesh = QCylinderMesh()
        self._trans = trans = QTransform()
        self._mat = mat = QPhongAlphaMaterial()
        mat.setAlpha(0.05)

        # mat.setCool(getColorObj("#0000cc"))
        # mat.setWarm(getColorObj("#cccc00"))

        mesh.setRadius(_CYLINDER_RADIUS)
        mesh.setRings(_CYLINDER_RINGS)
        mesh.setSlices(_CYLINDER_SLICES)
        mesh.setLength(length)

        trans.setTranslation(QVector3D(x, y, z))
        trans.setRotation(QQuaternion.fromAxisAndAngle(
                          QVector3D(1.0, 0.0, 0.0), 90.0))

        # print(mat.cool().name(), mat.warm().name())
        # mat.setDiffuse(getColorObj(color))

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
        self._part_entity = p_e = part_item.entity()
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        m_p = self._model_part
        x, y = m_p.locationQt(self._id_num, part_item.scaleFactor())
        z = 0
        length = 42.*0.34  # hard coding for now
        # vh_z, vh_length = m_p.getVirtualHelixProperties(self._id_num, ['z', 'length'])
        # length = vh_length * m_p.baseWidth()

        self.cylinder = Cylinder(x, -y, z, length, '#f7931e', p_e)

        # self._handle = VirtualHelixHandleItem(self, part_entity, viewroot)
        # self._last_strand_set = None
        # self._last_idx = None
        # self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        # self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        # self.setBrush(getNoBrush())

        # view = self.view()
        # view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        # should_show_details = view.shouldShowDetails()

        # pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        # pen.setCosmetic(should_show_details)
        # self.setPen(pen)

        # self.is_active = False

        # self.refreshPath()
        # self.setAcceptHoverEvents(True)  # for pathtools
        # self.setZValue(styles.ZPATHHELIX)

        # self._right_mouse_move = False
        # self.drag_last_position = self.handle_start = self.pos()

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
        print("strandAddedSlot", sender, strand)
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
