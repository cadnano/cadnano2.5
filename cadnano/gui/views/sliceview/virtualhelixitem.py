from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsLineItem

from cadnano.enum import PartType, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.palette import getColorObj, getNoPen, getPenObj, getBrushObj, getNoBrush
from . import slicestyles as styles
from .sliceextras import PreXoverItemGroup, WedgeGizmo, WEDGE_RECT

# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX
_BRUSH_DEFAULT = getBrushObj(styles.SLICE_FILL)
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)

SNAP_WIDTH = 3

class VirtualHelixItem(AbstractVirtualHelixItem, QGraphicsEllipseItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the OrigamiPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the PlasmidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    FILTER_NAME = 'virtual_helix'

    def __init__(self, id_num, part_item):
        """
        """
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        QGraphicsEllipseItem.__init__(self, parent=part_item)
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self.hide()
        model_part = self._model_part
        x, y = model_part.locationQt(id_num, part_item.scaleFactor())
        # set position to offset for radius
        # self.setTransformOriginPoint(_RADIUS, _RADIUS)
        self.setCenterPos(x, y)

        self.wedge_gizmos = {}
        self._added_wedge_gizmos = set()
        # self._prexo_gizmos = []

        self.setAcceptHoverEvents(True)
        self.setZValue(_ZVALUE)

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()

        self.old_pen = None
        self.is_active = False
        self.updateAppearance()

        self.show()

        self._right_mouse_move = False
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._part_item.part()
    # end def

    def setSnapOrigin(self, is_snap):
        if is_snap:
            op = self.pen()
            if self.old_pen is None:
                self.old_pen = op
            self.setPen(getPenObj(op.color().name(), SNAP_WIDTH))
        else:
            self.setPen(self.old_pen)
            self.old_pen = None

    def partItem(self):
        return self._part_item
    # end def

    def idNum(self):
        return self._id_num
    # end def

    def activate(self):
        self.is_active = True
        self.updateAppearance()

    def deactivate(self):
        self.is_active = False
        self.updateAppearance()

    def setCenterPos(self, x, y):
        # invert the y axis
        part_item = self._part_item
        parent_item = self.parentItem()
        pos = QPointF(x - _RADIUS, y- _RADIUS)
        if parent_item != part_item:
            pos = parent_item.mapFromItem(part_item, pos)
        self.setPos(pos)
    # end def

    def getCenterPos(self):
        """ get the scene position in case parented by a selection
        group.  Shouldn't be
        """
        pos = self.scenePos()
        pos = self._part_item.mapFromScene(pos)
        # return pos
        return QPointF(pos.x() + _RADIUS, pos.y() + _RADIUS)
    # end def

    def getCenterScenePos(self):
        """ return QPointF of the scenePos of the center
        """
        return self.scenePos() + QPointF(_RADIUS, _RADIUS)
    # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def

    def partCrossoverSpanAngle(self):
        return float(self.part().getProperty('crossover_span_angle'))
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def mousePressEvent(self, event):
        if self.FILTER_NAME not in self._part_item.getFilterSet():
            return
        if event.button() == Qt.RightButton:
            return
        part_item = self._part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
        else:
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def selectToolMousePress(self, tool, part_item, event):
        part = self._model_part
        part.setSelected(True)
        tool.selectOrSnap(part_item, self, event)
        # return QGraphicsItem.mousePressEvent(self, event)
    # end def

    def virtualHelixPropertyChangedSlot(self, keys, values):
        # for key, val in zip(keys, values):
        #     pass
        self.updateAppearance()
    # end def


    def virtualHelixRemovedSlot(self):
        self._controller.disconnectSignals()
        self._controller = None
        part_item = self._part_item
        tool = part_item._getActiveTool()
        if tool.methodPrefix() == "selectTool":
            tool.hideLineItem()
        self.scene().removeItem(self._label)
        self._label = None
        self._part_item = None
        self._model_part = None
        self.scene().removeItem(self)
    # end def

    def updateAppearance(self):
        is_visible, color = self.getProperty(['is_visible', 'color'])
        if is_visible:
            self.show()
        else:
            self.hide()
            return

        pwidth = styles.SLICE_HELIX_STROKE_WIDTH if self.old_pen is None else SNAP_WIDTH

        if self.is_active:
            self._USE_PEN = getPenObj(styles.ACTIVE_STROKE, pwidth)
        else:
            self._USE_PEN = getPenObj(color, pwidth)

        self._TEXT_BRUSH = getBrushObj(styles.SLICE_TEXT_COLOR)

        self._BRUSH = _BRUSH_DEFAULT
        self._USE_BRUSH = getBrushObj(color, alpha=150)

        self._label.setBrush(self._TEXT_BRUSH)
        self.setBrush(self._BRUSH)
        self.setPen(self._USE_PEN)
        self.setRect(_RECT)
    # end def

    def updatePosition(self):
        """
        coordinates in the model are always in the part
        coordinate frame
        """
        part_item = self._part_item
        sf = part_item.scaleFactor()
        x, y = self._model_part.locationQt(self._id_num, part_item.scaleFactor())
        new_pos = QPointF(x - _RADIUS, y - _RADIUS)         # top left
        tl_pos = part_item.mapFromScene(self.scenePos())    # top left

        """
        better to compare QPointF's since it handles difference
        tolerances for you with !=
        """
        if new_pos != tl_pos:
            parent_item = self.parentItem()
            br = self.boundingRect()
            # print("Rect", br.width(), br.height(), _RADIUS)
            # print("xy", tl_pos.x(), tl_pos.y())
            # print("xy1", new_pos.x(), new_pos.y())
            if parent_item != part_item:
                # print("different parent", parent_item)
                new_pos = parent_item.mapFromItem(part_item, new_pos)
            # print("xy2", new_pos.x(), new_pos.y())
            self.setPos(new_pos)
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self.idNum())
        label.setFont(_FONT)
        label.setZValue(_ZVALUE)
        label.setParentItem(self)
        return label
    # end def

    def beginAddWedgeGizmos(self):
        self._added_wedge_gizmos.clear()
    # end def

    def endAddWedgeGizmos(self):
        remove_list = []
        scene = self.scene()
        wg_dict = self.wedge_gizmos
        recently_added = self._added_wedge_gizmos
        for neighbor_virtual_helix in wg_dict.keys():
            if neighbor_virtual_helix not in recently_added:
                remove_list.append(neighbor_virtual_helix)
        for nvh in remove_list:
            wg = wg_dict.get(nvh)
            del wg_dict[nvh]
            scene.removeItem(wg)
    # end def

    def setWedgeGizmo(self, neighbor_virtual_helix, neighbor_virtual_helix_item):
        wg_dict = self.wedge_gizmos
        nvhi = neighbor_virtual_helix_item

        nvhi_name = nvhi.getProperty('name')
        pos = self.scenePos()
        line = QLineF(pos, nvhi.scenePos())
        line.translate(_RADIUS,_RADIUS)
        if line.length() > (_RADIUS*1.99):
            color = '#5a8bff'
        else:
            color = '#cc0000'
            nvhi_name = nvhi_name + '*' # mark as invalid
        line.setLength(_RADIUS)
        if neighbor_virtual_helix in wg_dict:
            wedge_item = wg_dict[neighbor_virtual_helix]
        else:
            wedge_item = WedgeGizmo(_RADIUS, WEDGE_RECT, self)
            wg_dict[neighbor_virtual_helix] = wedge_item
        wedge_item.showWedge(line.angle(), color, outline_only=False)
        self._added_wedge_gizmos.add(neighbor_virtual_helix)
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        num = self.idNum()
        label = self._label

        if num is not None:
            label.setText("%d" % num)
        else:
            return

        y_val = _RADIUS / 3
        if num < 10:
            label.setPos(_RADIUS / 1.5, y_val)
        elif num < 100:
            label.setPos(_RADIUS / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        b_rect = label.boundingRect()
        posx = b_rect.width()/2
        posy = b_rect.height()/2
        label.setPos(_RADIUS-posx, _RADIUS-posy)
    # end def
# end class

