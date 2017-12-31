# encoding: utf-8

from cadnano import util
from cadnano.controllers.virtualhelixitemcontroller import VirtualHelixItemController
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
        self._model_vh = model_virtual_helix
        self._part_item = part_item
        self._part_entity = part_item.entity()
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)
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
        # id_num = sender.idNum()
        # color = strand.getColor()
        # axis_pts, fwd_pts, rev_pts = self._model_part.getCoordinates(id_num)
        # pts = fwd_pts if sender.isForward() else rev_pts
        StrandItem(strand, self)
        self._part_item.addStrand(strand)
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
