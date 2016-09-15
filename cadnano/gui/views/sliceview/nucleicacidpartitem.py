"""Summary

Attributes:
    DELTA (TYPE): Description
    HIGHLIGHT_WIDTH (TYPE): Description
"""
from ast import literal_eval
from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsRectItem

from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.palette import getPenObj, getBrushObj, getNoPen
from cadnano.gui.views.abstractitems.abstractpartitem import QAbstractPartItem
from cadnano.gui.views.grabcorneritem import GrabCornerItem

from .virtualhelixitem import SliceVirtualHelixItem
from .prexovermanager import PreXoverManager
from .griditem import GridItem
from . import slicestyles as styles

_RADIUS = styles.SLICE_HELIX_RADIUS
_DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.
_HOVER_RECT = _DEFAULT_RECT.adjusted(-DELTA, -DELTA, DELTA, DELTA)
_MOD_PEN = getPenObj(styles.BLUE_STROKE, HIGHLIGHT_WIDTH)

_DEFAULT_WIDTH = styles.DEFAULT_PEN_WIDTH
_DEFAULT_ALPHA = styles.DEFAULT_ALPHA
_SELECTED_COLOR = styles.SELECTED_COLOR
_SELECTED_WIDTH = styles.SELECTED_PEN_WIDTH
_SELECTED_ALPHA = styles.SELECTED_ALPHA

_BOUNDING_RECT_PADDING = 10


class SliceNucleicAcidPartItem(QAbstractPartItem):
    """Parent should be either a SliceRootItem, or an AssemblyItem.

    Invariant: keys in _empty_helix_hash = range(_nrows) x range(_ncols)
    where x is the cartesian product.

    Attributes:
        active_virtual_helix_item (cadnano.gui.views.sliceview.virtualhelixitem.SliceVirtualHelixItem): Description
        grab_cornerBR (TYPE): Description
        grab_cornerTL (TYPE): Description
        griditem (TYPE): Description
        outline (TYPE): Description
        prexover_manager (TYPE): Description
        scale_factor (TYPE): Description
    """
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, model_part_instance, viewroot, parent=None):
        """Summary

        Args:
            model_part_instance (TYPE): Description
            viewroot (TYPE): Description
            parent (None, optional): Description
        """
        super(SliceNucleicAcidPartItem, self).__init__(model_part_instance, viewroot, parent)

        self._getActiveTool = viewroot.manager.activeToolGetter
        m_p = self._model_part
        self._controller = NucleicAcidPartItemController(self, m_p)
        self.scale_factor = self._RADIUS / m_p.radius()

        self.active_virtual_helix_item = None

        self.prexover_manager = PreXoverManager(self)

        self.hide()  # hide while until after attemptResize() to avoid flicker

        self._rect = QRectF(0., 0., 1000., 1000.)   # set this to a token value
        self.boundRectToModel()

        self.setPen(getNoPen())

        self.setRect(self._rect)
        self.setAcceptHoverEvents(True)

        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        # Connect destructor. This is for removing a part from scenes.

        # initialize the NucleicAcidPartItem with an empty set of old coords
        self.setZValue(styles.ZPARTITEM)

        self.outline = outline = QGraphicsRectItem(self)
        o_rect = self.configureOutline(outline)
        outline.setFlag(QGraphicsItem.ItemStacksBehindParent)
        outline.setZValue(styles.ZDESELECTOR)
        model_color = m_p.getColor()
        self.outline.setPen(getPenObj(model_color, _DEFAULT_WIDTH))

        GC_SIZE = 20
        self.grab_cornerTL = GrabCornerItem(GC_SIZE, model_color, True, self)
        self.grab_cornerTL.setTopLeft(o_rect.topLeft())
        self.grab_cornerBR = GrabCornerItem(GC_SIZE, model_color, True, self)
        self.grab_cornerBR.setBottomRight(o_rect.bottomRight())

        self.griditem = GridItem(self, self._model_props['grid_type'])

        self.griditem.setZValue(1)
        self.grab_cornerTL.setZValue(2)
        self.grab_cornerBR.setZValue(2)

        # select upon creation
        for part in m_p.document().children():
            if part is m_p:
                part.setSelected(True)
            else:
                part.setSelected(False)
        self.show()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part, id_num):
        """Summary

        Args:
            part (TYPE): Description
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.

        Args:
            TYPE: Description
        """
        vhi = self._virtual_helix_item_hash.get(id_num, None)
        self.setActiveVirtualHelixItem(vhi)
        self.setPreXoverItemsVisible(vhi)
    # end def

    def partActiveBaseInfoSlot(self, part, info):
        """Summary

        Args:
            part (TYPE): Description
            info (TYPE): Description

        Args:
            TYPE: Description
        """
        pxom = self.prexover_manager
        pxom.deactivateNeighbors()
        if info and info is not None:
            id_num, is_fwd, idx, _ = info
            pxom.activateNeighbors(id_num, is_fwd, idx)
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        """Summary

        Args:
            model_part (Part): The model part
            property_key (TYPE): Description
            new_value (TYPE): Description

        Args:
            TYPE: Description
        """
        if self._model_part == model_part:
            self._model_props[property_key] = new_value
            if property_key == 'color':
                self.outline.setPen(getPenObj(new_value, _DEFAULT_WIDTH))
                for vhi in self._virtual_helix_item_hash.values():
                    vhi.updateAppearance()
                self.grab_cornerTL.setBrush(getBrushObj(new_value))
                self.grab_cornerBR.setBrush(getBrushObj(new_value))
            elif property_key == 'is_visible':
                if new_value:
                    self.show()
                else:
                    self.hide()
            elif property_key == 'grid_type':
                self.griditem.setGridType(new_value)
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot

        Args:
            sender (obj): Model object that emitted the signal.
        """
        self.parentItem().removePartItem(self)

        scene = self.scene()

        scene.removeItem(self)

        self._model_part = None
        self._mod_circ = None

        self._controller.disconnectSignals()
        self._controller = None
        self.grab_cornerTL = None
        self.grab_cornerBR = None
        self.griditem = None
    # end def

    def partVirtualHelicesTranslatedSlot(self, sender,
                                         vh_set, left_overs,
                                         do_deselect):
        """
        left_overs are neighbors that need updating due to changes

        Args:
            sender (obj): Model object that emitted the signal.
            vh_set (TYPE): Description
            left_overs (TYPE): Description
            do_deselect (TYPE): Description
        """
        if do_deselect:
            tool = self._getActiveTool()
            if tool.methodPrefix() == "selectTool":
                if tool.isSelectionActive():
                    # tool.deselectItems()
                    tool.modelClear()

        # 1. move everything that moved
        for id_num in vh_set:
            vhi = self._virtual_helix_item_hash[id_num]
            vhi.updatePosition()
        # 2. now redraw what makes sense to be redrawn
        for id_num in vh_set:
            vhi = self._virtual_helix_item_hash[id_num]
            self._refreshVirtualHelixItemGizmos(id_num, vhi)
        for id_num in left_overs:
            vhi = self._virtual_helix_item_hash[id_num]
            self._refreshVirtualHelixItemGizmos(id_num, vhi)

        # 0. clear PreXovers:
        # self.prexover_manager.hideGroups()
        # if self.active_virtual_helix_item is not None:
        #     self.active_virtual_helix_item.deactivate()
        #     self.active_virtual_helix_item = None
        avhi = self.active_virtual_helix_item
        self.setPreXoverItemsVisible(avhi)
        self.enlargeRectToFit()
    # end def

    def _refreshVirtualHelixItemGizmos(self, id_num, vhi):
        """Update props and appearance of self & recent neighbors. Ultimately
        triggered by a partVirtualHelicesTranslatedSignal.

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            vhi (cadnano.gui.views.sliceview.virtualhelixitem.SliceVirtualHelixItem): the item associated with id_num
        """
        neighbors = vhi.cnModel().getProperty('neighbors')
        neighbors = literal_eval(neighbors)
        vhi.beginAddWedgeGizmos()
        for nvh in neighbors:
            nvhi = self._virtual_helix_item_hash.get(nvh, False)
            if nvhi:
                vhi.setWedgeGizmo(nvh, nvhi)
        # end for
        vhi.endAddWedgeGizmos()
    # end def

    def partVirtualHelixPropertyChangedSlot(self, sender, id_num, virtual_helix, keys, values):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            keys (tuple): keys that changed
            values (tuple): new values for each key that changed

        Args:
            TYPE: Description
        """
        if self._model_part == sender:
            vh_i = self._virtual_helix_item_hash[id_num]
            vh_i.virtualHelixPropertyChangedSlot(keys, values)
    # end def

    def partVirtualHelixAddedSlot(self, sender, id_num, virtual_helix, neighbors):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            neighbors (TYPE): Description

        Args:
            TYPE: Description
        """
        vhi = SliceVirtualHelixItem(virtual_helix, self)
        self._virtual_helix_item_hash[id_num] = vhi
        self._refreshVirtualHelixItemGizmos(id_num, vhi)
        for neighbor_id in neighbors:
            nvhi = self._virtual_helix_item_hash.get(neighbor_id, False)
            if nvhi:
                self._refreshVirtualHelixItemGizmos(neighbor_id, nvhi)
        self.enlargeRectToFit()
    # end def

    def partVirtualHelixRemovingSlot(self, sender, id_num, virtual_helix, neighbors):
        """Summary

        Args:
            sender (obj): Model object that emitted the signal.
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.
            neighbors (TYPE): Description

        Args:
            TYPE: Description
        """
        tm = self._viewroot.manager
        tm.resetTools()
        self.removeVirtualHelixItem(id_num)
        for neighbor_id in neighbors:
            nvhi = self._virtual_helix_item_hash[neighbor_id]
            self._refreshVirtualHelixItemGizmos(neighbor_id, nvhi)
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        """Set this Z to front, and return other Zs to default.

        Args:
            model_part (Part): The model part
            is_selected (TYPE): Description
        """
        if is_selected:
            # self._drag_handle.resetAppearance(_SELECTED_COLOR, _SELECTED_WIDTH, _SELECTED_ALPHA)
            self.setZValue(styles.ZPARTITEM + 1)
        else:
            # self._drag_handle.resetAppearance(self.modelColor(), _DEFAULT_WIDTH, _DEFAULT_ALPHA)
            self.setZValue(styles.ZPARTITEM)
    # end def

    def partVirtualHelicesSelectedSlot(self, sender, vh_set, is_adding):
        """is_adding (bool): adding (True) virtual helices to a selection
        or removing (False)

        Args:
            sender (obj): Model object that emitted the signal.
            vh_set (TYPE): Description
            is_adding (TYPE): Description
        """
        select_tool = self._viewroot.select_tool
        if is_adding:
            # print("got the adding slot in path")
            select_tool.selection_set.update(vh_set)
            select_tool.setPartItem(self)
            select_tool.getSelectionBoundingRect()
        else:
            select_tool.deselectSet(vh_set)
    # end def

    def partDocumentSettingChangedSlot(self, part, key, value):
        """Summary

        Args:
            part (TYPE): Description
            key (TYPE): Description
            value (TYPE): Description

        Args:
            TYPE: Description

        Raises:
            ValueError: Description
        """
        if key == 'grid':
            print("grid change", value)
            if value == 'lines and points':
                self.griditem.setDrawlines(True)
            elif value == 'points':
                self.griditem.setDrawlines(False)
            else:
                raise ValueError("unknown grid styling")
    # end def

    ### ACCESSORS ###
    def boundingRect(self):
        """Summary

        Args:
            TYPE: Description
        """
        return self._rect
    # end def

    def modelColor(self):
        """Summary

        Args:
            TYPE: Description
        """
        return self._model_props['color']
    # end def

    def window(self):
        """Summary

        Args:
            TYPE: Description
        """
        return self.parentItem().window()
    # end def

    def setActiveVirtualHelixItem(self, new_active_vhi):
        """Summary

        Args:
            new_active_vhi (TYPE): Description

        """
        current_vhi = self.active_virtual_helix_item
        # print(current_vhi, new_active_vhi)
        if new_active_vhi != current_vhi:
            if current_vhi is not None:
                current_vhi.deactivate()
            if new_active_vhi is not None:
                new_active_vhi.activate()
            self.active_virtual_helix_item = new_active_vhi
    # end def

    def setPreXoverItemsVisible(self, virtual_helix_item):
        """
        self._pre_xover_items list references prexovers parented to other
        PathHelices such that only the activeHelix maintains the list of
        visible prexovers

        Args:
            virtual_helix_item (cadnano.gui.views.sliceview.virtualhelixitem.SliceVirtualHelixItem): Description
        """
        vhi = virtual_helix_item
        pxom = self.prexover_manager
        if vhi is None:
            pxom.hideGroups()
            return

        # print("slice.setPreXoverItemsVisible", virtual_helix_item.idNum())
        part = self.part()
        info = part.active_base_info
        if info:
            id_num, is_fwd, idx, to_vh_id_num = info
            per_neighbor_hits, pairs = part.potentialCrossoverMap(id_num, idx)
            pxom.activateVirtualHelix(virtual_helix_item, idx,
                                      per_neighbor_hits, pairs)
    # end def

    def removeVirtualHelixItem(self, id_num):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.

        Args:
            TYPE: Description
        """
        vhi = self._virtual_helix_item_hash[id_num]
        if vhi == self.active_virtual_helix_item:
            self.active_virtual_helix_item = None
        vhi.virtualHelixRemovedSlot()
        del self._virtual_helix_item_hash[id_num]
    # end def

    def reconfigureRect(self, top_left, bottom_right, padding=_RADIUS):
        """Summary
        NOTE: we skip padding Bottom right Y dimension

        Args:
            top_left (TYPE): Description
            bottom_right (TYPE): Description

        Returns:
            tuple: tuple of point tuples representing the top_left and
                bottom_right as reconfigured with padding
        """
        rect = self._rect
        ptTL = QPointF(*self.padTL(padding, *top_left)) if top_left else rect.topLeft()
        ptBR = QPointF(*self.padBR(padding, *bottom_right)) if bottom_right else rect.bottomRight()
        self._rect = new_rect = QRectF(ptTL, ptBR)
        self.setRect(new_rect)
        self.configureOutline(self.outline)
        self.griditem.updateGrid()
        return (ptTL.x(), ptTL.y()), (ptBR.x(), ptBR.y())
    # end def

    def padTL(self, padding, xTL, yTL):
        return xTL - padding, yTL - padding
    # end def

    def padBR(self, padding, xBR, yBR):
        return xBR + padding, yBR
    # end def

    def enlargeRectToFit(self):
        """Enlarges Part Rectangle to fit the model bounds.  Call this
        when adding a SliceVirtualHelixItem.  Pad
        """
        xTL, yTL, xBR, yBR = self.getModelBounds()
        tl, br = self.reconfigureRect((xTL, yTL), (xBR, yBR))
        self.grab_cornerTL.alignPos(*tl)
        self.grab_cornerBR.alignPos(*br)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def configureOutline(self, outline):
        """Adjusts `outline` size with default padding.

        Args:
            outline (TYPE): Description

        Returns:
            o_rect (QRect): `outline` rect adjusted by _BOUNDING_RECT_PADDING
        """
        _p = _BOUNDING_RECT_PADDING
        o_rect = self.rect().adjusted(-_p, -_p, _p, _p)
        outline.setRect(o_rect)
        return o_rect
    # end def

    def boundRectToModel(self):
        """update the boundaries to what's in the model with a minimum
        size
        """
        xTL, yTL, xBR, yBR = self.getModelBounds()
        self._rect = QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR))
    # end def

    def getModelBounds(self):
        """Bounds in form of Qt scaled from model

        Args:
            Tuple (top_left, bottom_right)
        """
        xLL, yLL, xUR, yUR = self.part().boundDimensions(self.scale_factor)
        return xLL, -yUR, xUR, -yLL
    # end def

    def bounds(self):
        """x_low, x_high, y_low, y_high
        """
        rect = self._rect
        return (rect.left(), rect.right(), rect.bottom(), rect.top())

    ### PUBLIC SUPPORT METHODS ###
    def setModifyState(self, bool_val):
        """Hides the mod_rect when modify state disabled.

        Args:
            bool_val (TYPE): what the modifystate should be set to.
        """
        self._can_show_mod_circ = bool_val
        if bool_val == False:
            self._mod_circ.hide()
    # end def

    def updateStatusBar(self, status_str):
        """Shows status_str in the MainWindow's status bar.

        Args:
            status_str (TYPE): Description
        """
        pass  # disabled for now.
        # self.window().statusBar().showMessage(status_str, timeout)
    # end def

    def zoomToFit(self):
        """Summary

        Args:
            TYPE: Description
        """
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """Handler for user mouse press.

        Args:
            event (QGraphicsSceneMouseEvent): Contains item, scene, and screen
            coordinates of the the event, and previous event.

        Args:
            TYPE: Description
        """
        if event.button() == Qt.RightButton:
            return
        part = self._model_part
        part.setSelected(True)
        if self.isMovable():
            return QGraphicsItem.mousePressEvent(self, event)
        tool = self._getActiveTool()
        if tool.FILTER_NAME not in part.document().filter_set:
            return
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, event)
        else:
            event.setAccepted(False)
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def hoverMoveEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description

        Args:
            TYPE: Description
        """
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, event)
        else:
            event.setAccepted(False)
            QGraphicsItem.hoverMoveEvent(self, event)
    # end def

    def getModelPos(self, pos):
        """Y-axis is inverted in Qt +y === DOWN

        Args:
            pos (TYPE): Description
        """
        sf = self.scale_factor
        x, y = pos.x()/sf, -1.0*pos.y()/sf
        return x, y
    # end def

    def getVirtualHelixItem(self, id_num):
        """Summary

        Args:
            id_num (int): VirtualHelix ID number. See `NucleicAcidPart` for description and related methods.

        Returns:
            TYPE: Description
        """
        return self._virtual_helix_item_hash.get(id_num)
    # end def

    def createToolMousePress(self, tool, event, alt_event=None):
        """Summary

        Args:
            tool (TYPE): Description
            event (TYPE): Description
            alt_event (None, optional): Description

        Returns:
            TYPE: Description
        """
        # 1. get point in model coordinates:
        part = self._model_part
        if alt_event is None:
            print()
            pt = tool.eventToPosition(self, event)
            print("reg_event", pt)
        else:
            # pt = alt_event.scenePos()
            # pt = self.mapFromScene(pt)
            pt = alt_event.pos()
            # print("alt_event", pt)

        if pt is None:
            tool.deactivate()
            return QGraphicsItem.mousePressEvent(self, event)

        part_pt_tuple = self.getModelPos(pt)

        mod = Qt.MetaModifier
        if not (event.modifiers() & mod):
            pass

        # don't create a new VirtualHelix if the click overlaps with existing
        # VirtualHelix
        current_id_num = tool.idNum()
        check = part.isVirtualHelixNearPoint(part_pt_tuple, current_id_num)
        # print("current_id_num", current_id_num, check)
        # print(part_pt_tuple)
        tool.setPartItem(self)
        if check:
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            # print("got a check", id_num)
            if id_num is not None:
                # print("restart", id_num)
                vhi = self._virtual_helix_item_hash[id_num]
                tool.setVirtualHelixItem(vhi)
                tool.startCreation()
        else:
            # print("creating", part_pt_tuple)
            part.createVirtualHelix(*part_pt_tuple)
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            vhi = self._virtual_helix_item_hash[id_num]
            tool.setVirtualHelixItem(vhi)
            tool.startCreation()
    # end def

    def createToolHoverMove(self, tool, event):
        """Summary

        Args:
            tool (TYPE): Description
            event (TYPE): Description

        Returns:
            TYPE: Description
        """
        tool.hoverMoveEvent(self, event)
        return QGraphicsItem.hoverMoveEvent(self, event)
    # end def

    def selectToolMousePress(self, tool, event):
        """
        Args:
            tool (TYPE): Description
            event (TYPE): Description
        """
        tool.setPartItem(self)
        pt = tool.eventToPosition(self, event)
        part_pt_tuple = self.getModelPos(pt)
        part = self._model_part
        if part.isVirtualHelixNearPoint(part_pt_tuple):
            id_num = part.getVirtualHelixAtPoint(part_pt_tuple)
            if id_num is not None:
                print(id_num)
                loc = part.getCoordinate(id_num, 0)
                print("VirtualHelix #{} at ({:.3f}, {:.3f})".format(id_num, loc[0], loc[1]))
            else:
                # tool.deselectItems()
                tool.modelClear()
        else:
            # tool.deselectItems()
            tool.modelClear()
        return QGraphicsItem.mousePressEvent(self, event)
    # end def
# end class
