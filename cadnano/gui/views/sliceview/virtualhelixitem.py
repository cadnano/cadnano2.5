from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsLineItem

from cadnano.enum import Parity, PartType, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.gui.palette import getColorObj, getNoPen, getPenObj, getBrushObj, getNoBrush
from . import slicestyles as styles
from .sliceextras import PreXoverItemGroup, WedgeGizmo, WEDGE_RECT

# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX + 3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL) # QBrush(QColor(250, 250, 250))
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)

class VirtualHelixItem(AbstractVirtualHelixItem, QGraphicsEllipseItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the OrigamiPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the PlasmidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    def __init__(self, id_num, part_item):
        """
        """
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        QGraphicsEllipseItem.__init__(self, parent=part_item)
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self.hide()
        x, y = self._virtual_helix_group.locationQt(id_num, part_item.scaleFactor())
        # set position to offset for radius
        # self.setTransformOriginPoint(_RADIUS, _RADIUS)
        self.setCenterPos(x, y)

        model_part = self._model_part
        vhg = model_part.virtualHelixGroup()
        # self._bases_per_repeat = self.getProperty(id_num, 'bases_per_repeat')
        # self._turns_per_repeat = self.getProperty(id_num, 'turns_per_repeat')
        # self._prexoveritemgroup = pxig = PreXoverItemGroup(_RADIUS, WEDGE_RECT, self)

        self.wedge_gizmos = {}
        self._added_wedge_gizmos = set()
        # self._prexo_gizmos = []

        self.setAcceptHoverEvents(True)
        self.setZValue(_ZVALUE)

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self._pen1, self._pen2 = (QPen(), QPen())
        self.createArrows()
        self.updateAppearance()

        self.show()

        self._right_mouse_move = False
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._part_item.part()
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def idNum(self):
        return self._id_num
    # end def

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
        part_item = self._part_item
        tool = part_item._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(tool, part_item, event)
        else:
            # event.setAccepted(False)
            QGraphicsItem.mousePressEvent(self, event)
    # end def

    def selectToolMousePress(self, tool, part_item, event):
        part = self._model_part
        part.setSelected(True)
        tool.selectOrSnap(part_item, self, event)
        # return QGraphicsItem.mousePressEvent(self, event)
    # end def

    # def selectToolMouseMove(self, tool, event):
    #     tool.mouseMoveEvent(self, event)
    #     return QGraphicsItem.hoverMoveEvent(self, event)
    # # end def

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
        tool.hideLineItem()
        self.scene().removeItem(self._label)
        self._label = None
        self._part_item = None
        self._model_part = None
        self.scene().removeItem(self)
    # end def

    def updateAppearance(self):
        part = self._model_part
        part_color = part.getProperty('color')

        self._USE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)
        self._OUT_OF_SLICE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)

        self._OUT_OF_SLICE_TEXT_BRUSH = getBrushObj(styles.OUT_OF_SLICE_TEXT_COLOR)

        self._OUT_OF_SLICE_BRUSH = _OUT_OF_SLICE_BRUSH_DEFAULT
        self._USE_BRUSH = getBrushObj(part_color, alpha=150)

        self._label.setBrush(self._OUT_OF_SLICE_TEXT_BRUSH)
        self.setBrush(self._OUT_OF_SLICE_BRUSH)
        self.setPen(self._OUT_OF_SLICE_PEN)
        self.setRect(_RECT)
    # end def

    def updatePosition(self):
        """
        coordinates in the model are always in the part
        coordinate frame
        """
        part_item = self._part_item
        sf = part_item.scaleFactor()
        vhg = self._model_part.virtualHelixGroup()
        x, y = vhg.locationQt(self._id_num, part_item.scaleFactor())
        new_pos = QPointF(x - _RADIUS, y - _RADIUS)
        ctr_pos = part_item.mapFromScene(self.scenePos())
        """
        better to compare QPointF's since it handles difference
        tolerances for you with !=
        """
        if new_pos != ctr_pos:
            parent_item = self.parentItem()
            if parent_item != part_item:
                new_pos = parent_item.mapFromItem(part_item, new_pos)
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

    def createArrows(self):
        rad = _RADIUS
        pen1 = self._pen1
        pen2 = self._pen2
        pen1.setCapStyle(Qt.RoundCap)
        pen2.setCapStyle(Qt.RoundCap)
        pen1.setWidth(3)
        pen2.setWidth(3)
        pen1.setBrush(Qt.gray)
        pen2.setBrush(Qt.lightGray)
        arrow1 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        arrow2 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        #     arrow2 = QGraphicsLineItem(0, rad, rad, rad, self)
        # else:
        #     arrow1 = QGraphicsLineItem(0, rad, rad, rad, self)
        #     arrow2 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        arrow1.setTransformOriginPoint(rad, rad)
        arrow2.setTransformOriginPoint(rad, rad)
        arrow1.setZValue(40)
        arrow2.setZValue(40)
        arrow1.setPen(pen1)
        arrow2.setPen(pen2)
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self.arrow1.hide()
        self.arrow2.hide()
    # end def

    def updateFwdArrow(self, idx):
        fwd_strand = self.fwdStrand(idx)
        if fwd_strand:
            fwd_strand_color = fwd_strand.oligo().getColor()
            fwd_alpha = 230 if fwd_strand.hasXoverAt(idx) else 128
        else:
            fwd_strand_color = '#a0a0a4' #Qt.gray
            fwd_alpha = 26

        fwd_strand_color_obj = getColorObj(fwd_strand_color, alpha=fwd_alpha)
        self._pen1.setBrush(fwd_strand_color_obj)
        self.arrow1.setPen(self._pen1)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        # for some reason rotation is CW and not CCW with increasing angle
        eulerZ = self.getProperty('eulerZ')
        self.arrow1.setRotation(angle + part._TWIST_OFFSET + eulerZ)

    def updateRevArrow(self, idx):
        rev_strand = self.revStrand(idx)
        if rev_strand:
            rev_strand_color = rev_strand.oligo().getColor()
            rev_alpha = 230 if rev_strand.hasXoverAt(idx) else 128
        else:
            rev_strand_color = '#c0c0c0' # Qt.lightGray
            rev_alpha = 26
        rev_strand_color_obj = getColorObj(rev_strand_color, alpha=rev_alpha)
        self._pen2.setBrush(rev_strand_color_obj)
        self.arrow2.setPen(self._pen2)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        eulerZ = self.getProperty('eulerZ')
        self.arrow2.setRotation(angle + part._TWIST_OFFSET + eulerZ + 180)
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

    def setActiveSliceView(self, idx, has_fwd, has_rev):
        if has_fwd:
            self.setPen(self._USE_PEN)
            self.setBrush(self._USE_BRUSH)
            self._label.setBrush(_USE_TEXT_BRUSH)
            self.updateFwdArrow(idx)
            self.arrow1.show()
        else:
            self.setPen(self._OUT_OF_SLICE_PEN)
            self.setBrush(self._OUT_OF_SLICE_BRUSH)
            self._label.setBrush(self._OUT_OF_SLICE_TEXT_BRUSH)
            self.arrow1.hide()
        if has_rev:
            self.updateRevArrow(idx)
            self.arrow2.show()
        else:
            self.arrow2.hide()
    # end def
# end class

