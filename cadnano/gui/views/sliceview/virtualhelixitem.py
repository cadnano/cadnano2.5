from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem

from cadnano.enum import LatticeType, Parity, PartType, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.virtualhelix import VirtualHelix
from cadnano.gui.palette import getColorObj, getNoPen, getPenObj, getBrushObj, getNoBrush
from . import slicestyles as styles


# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
rect_gain = 0.25
_RECT = _RECT.adjusted(0, 0, rect_gain, rect_gain)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX+3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL) # QBrush(QColor(250, 250, 250))
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_REV_ANGLE = 171

_ROTARYDIAL_STROKE_WIDTH = 1
_ROTARYDIAL_PEN = getPenObj(styles.BLUE_STROKE, _ROTARYDIAL_STROKE_WIDTH)
_ROTARYDIAL_BRUSH = getBrushObj('#8099ccff')
_ROTARY_DELTA_WIDTH = 10

_HOVER_PEN = getPenObj('#ff0080', .5)
_HOVER_BRUSH = getBrushObj('#ff0080')

# BOX = QPolygonF()
# BOX.append(QPointF(0, 0))
# BOX.append(QPointF(0, PXI_PP_ITEM_WIDTH))
# BOX.append(QPointF(PXI_PP_ITEM_WIDTH, PXI_PP_ITEM_WIDTH))
# BOX.append(QPointF(PXI_PP_ITEM_WIDTH, 0))
# BOX.append(QPointF(0, 0))
# PXI_PP.addPolygon(BOX)

PXI_PP_ITEM_WIDTH = 1.5
P_POLY = QPolygonF()
P_POLY.append(QPointF(0, 0))
P_POLY.append(QPointF(0.75 * PXI_PP_ITEM_WIDTH, 0.5 * PXI_PP_ITEM_WIDTH))
P_POLY.append(QPointF(0, PXI_PP_ITEM_WIDTH))
P_POLY.append(QPointF(0, 0))
PXI_PP = QPainterPath()  # Left 5', Right 3' PainterPath
PXI_PP.addPolygon(P_POLY)



class PreXoverItem(QGraphicsPathItem):
    def __init__(self, base_idx, color, is_rev=False, parent=None):
        super(QGraphicsPathItem, self).__init__(PXI_PP, parent)
        self._name = "%s%d" % ("r" if is_rev else "f", base_idx)
        self._base_idx = base_idx
        self._color = color
        self._is_rev = is_rev
        self._parent = parent
        self.setAcceptHoverEvents(True)
        self.setPen(getNoPen())
        self.setBrush(getNoBrush())

        if self._is_rev:
            self.setPen(getPenObj(self._color, 0.25, alpha=128))
        else:
            self.setBrush(getBrushObj(self._color, alpha=128))
    # end def

    def hoverEnterEvent(self, event):
        if self._is_rev:
            self.setPen(getPenObj(self._color, 0.25))
            self.setPen(getPenObj("#ff3333", 0.25))
        else:
            self.setBrush(getBrushObj(self._color))
            self.setBrush(getBrushObj("#ff3333"))
        # self.setCursor(Qt.CrossCursor)
        self._parent.updateHoveredItem(self._name)
    # end def

    def hoverMoveEvent(self, event):
        pass
    # end def

    def hoverLeaveEvent(self, event):
        if self._is_rev:
            self.setPen(getPenObj(self._color, 0.25, alpha=128))
        else:
            self.setBrush(getBrushObj(self._color, alpha=128))
        # self.unsetCursor()
        self._parent.updateHoveredItem("None")
    # end def

# end class

class PreXoverItemGroup(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self._virtual_helix = parent._virtual_helix
        self.setPen(getNoPen())
        STEPSIZE = 21
        iw = PXI_PP_ITEM_WIDTH
        _ctr = self.mapToParent(_RECT).boundingRect().center()
        _x = _ctr.x() + _RADIUS - PXI_PP_ITEM_WIDTH 
        _y = _ctr.y()
        prexo_items = {}

        # fwd_angles = [round(360*x/10.5,2) for x in range(STEPSIZE)]
        fwd_angles = [round(34.29*x,3) for x in range(STEPSIZE)]
        fwd_colors = [QColor() for i in range(STEPSIZE)]
        for i in range(len(fwd_colors)):
            fwd_colors[i].setHsvF(i/(STEPSIZE*1.6), 0.75, 0.8)

        for i in range(len(fwd_angles)):
            color = fwd_colors[i].name()
            item = PreXoverItem(i, color, parent=self)
            _deltaR = i*.25 # spiral layout
            item.setPos(_x - _deltaR, _y)
            item.setTransformOriginPoint((-_RADIUS + iw + _deltaR), 0)
            item.setRotation(fwd_angles[i])
            prexo_items[i] = item

        # rev_angles = [round(360*x/10.5 + _REV_ANGLE,2) for x in range(STEPSIZE)]
        rev_angles = [round(34.29*x+_REV_ANGLE,3) for x in range(STEPSIZE)]
        rev_colors = [QColor() for i in range(STEPSIZE)]
        for i in range(len(rev_colors)):
            rev_colors[i].setHsvF(i/(STEPSIZE*1.6), 0.75, 0.8)
        rev_colors = rev_colors[::-1] # reverse antiparallel color order 

        for i in range(len(rev_colors)):
            color = rev_colors[i].name()
            item = PreXoverItem(i, color, is_rev=True, parent=self)
            _deltaR = i*.25 # spiral layout
            item.setPos(_x - _deltaR,_y)
            item.setTransformOriginPoint((-_RADIUS + iw + _deltaR), 0)
            item.setRotation(rev_angles[i])
            prexo_items[i] = item
    # end def

    def updateHoveredItem(self, index):
        self._virtual_helix.setProperty('hoveredPXI', index)


class VirtualHelixItem(QGraphicsEllipseItem, AbstractVirtualHelixItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the OrigamiPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the PlasmidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    def __init__(self, model_virtual_helix, empty_helix_item):
        """
        empty_helix_item is a EmptyHelixItem that will act as a QGraphicsItem parent
        """
        super(VirtualHelixItem, self).__init__(parent=empty_helix_item)
        self._virtual_helix = model_virtual_helix
        self._empty_helix_item = ehi = empty_helix_item
        self._part_item = ehi._part_item
        self._controller = VirtualHelixItemController(self, model_virtual_helix)

        self.hide()

        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(_ZVALUE)
        self.lastMousePressAddedBases = False

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self._pen1, self._pen2 = (QPen(), QPen())
        self.createArrows()
        self.updateAppearance()

        self._prexoveritemgroup = _pxig = PreXoverItemGroup(_RECT, self)
        _pxig.setTransformOriginPoint(_RECT.center())
        _pxig.setRotation(self._virtual_helix.getProperty('eulerZ'))
        # self._rect = QRectF(_RECT)
        # self._hover_rect = QRectF(_RECT)
        # self._outer_line = RotaryDialLine(self._rect, self)
        # self._hover_region = RotaryDialHoverRegion(self._hover_rect, self)

        self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
        self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())

        self._gizmos = []
        self._neighbor_vh_items = []
        self._right_mouse_move = False
        self.refreshCollidingItems()

        self.show()
    # end def

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._right_mouse_move = True
            self._button_down_pos = event.pos()
    # end def

    def mouseMoveEvent(self, event):
        if self._right_mouse_move:
            p = self.mapToScene(event.pos()) - self._button_down_pos
            self._empty_helix_item.setPos(p)
    # end def

    def mouseReleaseEvent(self, event):
        if self._right_mouse_move and event.button() == Qt.RightButton:
            self._right_mouse_move = False
            p = self.mapToScene(event.pos()) - self._button_down_pos
            self._empty_helix_item.setPos(p)
            ehi = self._empty_helix_item
            self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
            self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())
            self.refreshCollidingItems()
    # end def

    def refreshCollidingItems(self):
        """Update props and appearance of self & recent neighbors."""
        neighbors = []
        old_neighbors = self._virtual_helix.getProperty('neighbors').split()
        self._neighbor_items = items = list(filter(lambda x: 
                            type(x) is VirtualHelixItem, self.collidingItems()))
        while self._gizmos: # clear old gizmos
            self.scene().removeItem(self._gizmos.pop())
        for nvhi in items:
            nvhi_name = nvhi.virtualHelix().getName()
            pos = self.scenePos()
            line = QLineF(pos, nvhi.scenePos())
            line.translate(_RADIUS-pos.x(),_RADIUS-pos.y())
            color = '#5a8bff' if line.length() > (_RADIUS*1.99) else '#cc0000'
            line.setLength(_RADIUS)
            line_item = QGraphicsLineItem(line, self)
            line_item.setPen(getPenObj(color, 0.25))
            self._gizmos.append(line_item) # save ref to clear later
            neighbors.append('%s:%02d' % (nvhi_name, line.angle()))
        # end for
        self._virtual_helix.setProperty('neighbors', ' '.join(sorted(neighbors)))
        added = list(set(neighbors) - set(old_neighbors)) # includes new angles
        removed = list(set(old_neighbors) - set(neighbors))
        for nvhi in self._part_item.getVHItemList(): # check all items
            nvhi_name = nvhi.virtualHelix().getName()
            added_names = [a.split(':')[0] for a in added]
            removed_names = [r.split(':')[0] for r in removed]
            if nvhi_name in added_names or nvhi_name in removed_names:
                nvhi.refreshCollidingItems()
        # end for
    # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def

    def updateAppearance(self):
        part_color = self.part().getProperty('color')

        self._USE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)
        self._OUT_OF_SLICE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)
        self._USE_BRUSH = getBrushObj(part_color, alpha=128)
        self._OUT_OF_SLICE_BRUSH = getBrushObj(part_color, alpha=64)
        self._OUT_OF_SLICE_TEXT_BRUSH = getBrushObj(styles.OUT_OF_SLICE_TEXT_COLOR)

        if self.part().crossSectionType() == LatticeType.HONEYCOMB:
            self._USE_PEN = getPenObj(styles.BLUE_STROKE, styles.SLICE_HELIX_STROKE_WIDTH)
            self._OUT_OF_SLICE_PEN = getPenObj(styles.BLUE_STROKE,\
                                          styles.SLICE_HELIX_STROKE_WIDTH)

        if self.part().partType() == PartType.NUCLEICACIDPART:
            self._OUT_OF_SLICE_BRUSH = _OUT_OF_SLICE_BRUSH_DEFAULT
            # self._USE_BRUSH = getBrushObj(part_color, lighter=180)
            self._USE_BRUSH = getBrushObj(part_color, alpha=150)

        self._label.setBrush(self._OUT_OF_SLICE_TEXT_BRUSH)
        self.setBrush(self._OUT_OF_SLICE_BRUSH)
        self.setPen(self._OUT_OF_SLICE_PEN)
        self.setRect(_RECT)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def virtualHelixNumberChangedSlot(self, virtual_helix):
        """
        receives a signal containing a virtual_helix and the oldNumber
        as a safety check
        """
        self.setNumber()
    # end def

    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        if property_key == 'eulerZ':
            self._prexoveritemgroup.setRotation(new_value)
            scamZ = self._virtual_helix.getProperty('scamZ') 
            if scamZ != new_value: 
                self._virtual_helix.setProperty('scamZ', new_value)
            active_base_idx = self.part().activeBaseIndex()
            has_fwd, has_rev = virtual_helix.hasStrandAtIdx(active_base_idx)
            self.setActiveSliceView(active_base_idx, has_fwd, has_rev)
        elif property_key == 'scamZ':
            eulerZ = self._virtual_helix.getProperty('eulerZ') 
            if eulerZ != new_value: 
                self._virtual_helix.setProperty('eulerZ', new_value)
        elif property_key == 'ehiX':
            ehi_pos = self._empty_helix_item.scenePos()
            self._empty_helix_item.setPos(new_value, ehi_pos.y())
        elif property_key == 'ehiY':
            ehi_pos = self._empty_helix_item.scenePos()
            self._empty_helix_item.setPos(ehi_pos.x(),new_value)
    # end def


    def virtualHelixRemovedSlot(self, virtual_helix):
        self._controller.disconnectSignals()
        self._controller = None
        self._empty_helix_item.setNotHovered()
        self._virtual_helix = None
        self._empty_helix_item = None
        self.scene().removeItem(self._label)
        self._label = None
        self.scene().removeItem(self)
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtual_helix.number())
        label.setFont(_FONT)
        label.setZValue(_ZVALUE)
        label.setParentItem(self)
        return label
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
        fwd_strand = self._virtual_helix.scaf(idx)
        if fwd_strand:
            fwd_strand_color = fwd_strand.oligo().getColor()
            scaf_alpha = 230 if fwd_strand.hasXoverAt(idx) else 128
        else:
            fwd_strand_color = '#a0a0a4' #Qt.gray
            scaf_alpha = 26

        fwd_strand_color_obj = getColorObj(fwd_strand_color, alpha=scaf_alpha)
        self._pen1.setBrush(fwd_strand_color_obj)
        self.arrow1.setPen(self._pen1)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        # for some reason rotation is CW and not CCW with increasing angle
        eulerZ = float(self._virtual_helix.getProperty('eulerZ'))
        self.arrow1.setRotation(angle + part._TWIST_OFFSET + eulerZ)

    def updateRevArrow(self, idx):
        rev_strand = self._virtual_helix.stap(idx)
        if rev_strand:
            rev_strand_color = rev_strand.oligo().getColor()
            stap_alpha = 230 if rev_strand.hasXoverAt(idx) else 128
        else:
            rev_strand_color = '#c0c0c0' # Qt.lightGray
            stap_alpha = 26
        rev_strand_color_obj = getColorObj(rev_strand_color, alpha=stap_alpha)
        self._pen2.setBrush(rev_strand_color_obj)
        self.arrow2.setPen(self._pen2)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        eulerZ = float(self._virtual_helix.getProperty('eulerZ'))
        self.arrow2.setRotation(angle + part._TWIST_OFFSET + eulerZ + 150)
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtual_helix
        num = vh.number()
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

    def part(self):
        return self._empty_helix_item.part()
    # end def

    def parent(self):
        return self._empty_helix_item
    # end def

    def virtualHelix(self):
        return self._virtual_helix
    # end def

    def number(self):
        return self.virtualHelix().number()
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

    ############################ User Interaction ############################
    def sceneEvent(self, event):
        """Included for unit testing in order to grab events that are sent
        via QGraphicsScene.sendEvent()."""
        # if self._parent.sliceController.testRecorder:
        #     coord = (self._row, self._col)
        #     self._parent.sliceController.testRecorder.sliceSceneEvent(event, coord)
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return True
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
            return True
        QGraphicsItem.sceneEvent(self, event)
        return False

    def hoverEnterEvent(self, event):
        """
        If the selection is configured to always select
        everything, we don't draw a focus ring around everything,
        instead we only draw a focus ring around the hovered obj.
        """
        # if self.selectAllBehavior():
        #     self.setSelected(True)
        # forward the event to the empty_helix_item as well
        self._empty_helix_item.hoverEnterEvent(event)
    # end def

    def hoverLeaveEvent(self, event):
        # if self.selectAllBehavior():
        #     self.setSelected(False)
        self._empty_helix_item.hoverEnterEvent(event)
    # end def
# end class

class RotaryDialDeltaItem(QGraphicsPathItem):
    def __init__(self, startAngle, spanAngle, parent=None):
        # setup DNA line
        super(QGraphicsPathItem, self).__init__(parent)
        self._parent = parent
        self.updateAngle(startAngle, spanAngle)
        self.updateColor(parent.modelColor())
    # end def

    def updateAngle(self, startAngle, spanAngle):
        self._startAngle = startAngle
        self._spanAngle = spanAngle
        path = QPainterPath()
        path.arcMoveTo(self._parent._rect, startAngle)
        path.arcTo(self._parent._rect, startAngle, spanAngle)
        self.setPath(path)
    # end def

    def updateColor(self, color):
        c = QColor(color)
        c.setAlpha(128)
        self.setPen(QPen(c, _ROTARY_DELTA_WIDTH, Qt.SolidLine, Qt.FlatCap))
    # end def
# end class

class RotaryDialHoverRegion(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        # setup DNA line
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self.setPen(getNoPen())
        self.setBrush(_HOVER_BRUSH)
        self.setAcceptHoverEvents(True)

        # hover marker
        self._hoverLine = QGraphicsLineItem(-_ROTARY_DELTA_WIDTH/2, 0, _ROTARY_DELTA_WIDTH/2, 0, self)
        self._hoverLine.setPen(QPen(QColor(204, 0, 0), .5))
        self._hoverLine.hide()

        self._startPos = None
        self._startAngle = None  # save selection start
        self._clockwise = None
        self.dummy = RotaryDialDeltaItem(0, 0, parent)
        self.dummy.hide()

    def updateRect(self, rect):
        self.setRect(rect)

    def hoverEnterEvent(self, event):
        self.updateHoverLine(event)
        self._hoverLine.show()
    # end def

    def hoverMoveEvent(self, event):
        self.updateHoverLine(event)
    # end def

    def hoverLeaveEvent(self, event):
        self._hoverLine.hide()
    # end def

    def mousePressEvent(self, event):
        r = _RADIUS
        self.updateHoverLine(event)
        pos = self._hoverLine.pos()
        aX, aY, angle = self.snapPosToCircle(pos, r)
        if angle != None:
            self._startPos = QPointF(aX, aY)
            self._startAngle = self.updateHoverLine(event)
            self.dummy.updateAngle(self._startAngle, 0)
            self.dummy.show()
        # mark the start
        # f = QGraphicsEllipseItem(pX, pY, 2, 2, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0)))
    # end def

    def mouseMoveEvent(self, event):
        eventAngle = self.updateHoverLine(event)
        # Record initial direction before calling getSpanAngle
        if self._clockwise is None:
            self._clockwise = False if eventAngle > self._startAngle else True
        spanAngle = self.getSpanAngle(eventAngle)
        self.dummy.updateAngle(self._startAngle, spanAngle)
    # end def

    def mouseReleaseEvent(self, event):
        self.dummy.hide()
        endAngle = self.updateHoverLine(event)
        spanAngle = self.getSpanAngle(endAngle)
        old_angle = self._parent.virtualHelix().getProperty('eulerZ')
        new_angle = round((old_angle - spanAngle) % 360,0)
        self._parent.virtualHelix().setProperty('eulerZ', new_angle)

        # mark the end
        # x = self._hoverLine.x()
        # y = self._hoverLine.y()
        # f = QGraphicsEllipseItem(x, y, 6, 6, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0, 128)))
    # end def

    def updateHoverLine(self, event):
        """
        Moves red line to point (aX,aY) on RotaryDialLine closest to event.pos.
        Returns the angle of aX, aY, using the Qt arc coordinate system
        (0 = east, 90 = north, 180 = west, 270 = south).
        """
        r = _RADIUS
        aX, aY, angle = self.snapPosToCircle(event.pos(), r)
        if angle != None:
            self._hoverLine.setPos(aX, aY)
            self._hoverLine.setRotation(-angle)
        return angle
    # end def

    def snapPosToCircle(self, pos, radius):
        """Given x, y and radius, return x,y of nearest point on circle, and its angle"""
        pX = pos.x()
        pY = pos.y()
        cX = cY = radius
        vX = pX - cX
        vY = pY - cY
        magV = sqrt(vX*vX + vY*vY)
        if magV == 0:
            return (None, None, None)
        aX = cX + vX / magV * radius
        aY = cY + vY / magV * radius
        angle = (atan2(aY-cY, aX-cX))
        deg = -degrees(angle) if angle < 0 else 180+(180-degrees(angle))
        return (aX, aY, deg)
    # end def

    def getSpanAngle(self, angle):
        """
        Return the spanAngle angle by checking the initial direction of the selection.
        Selections that cross 0° must be handed as an edge case.
        """
        if self._clockwise: # spanAngle is negative
            if angle < self._startAngle:
                spanAngle = angle - self._startAngle
            else:
                spanAngle = -(self._startAngle + (360-angle))
        else: # counterclockwise, spanAngle is positive
            if angle > self._startAngle:
                spanAngle = angle - self._startAngle
            else:
                spanAngle = (360-self._startAngle) + angle
        return spanAngle
    # end def
# end class

class RotaryDialLine(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self.updateColor(parent.modelColor())
        self.setRect(rect)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)
    # end def

    def updateColor(self, color):
        self.setPen(getPenObj(color, _ROTARYDIAL_STROKE_WIDTH))

    def updateRect(self, rect):
        self.setRect(rect)
# end class

