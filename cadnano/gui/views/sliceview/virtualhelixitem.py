from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsLineItem

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
_RECT = _RECT.adjusted(rect_gain, rect_gain, rect_gain, rect_gain)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX+3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL) # QBrush(QColor(250, 250, 250))
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_ROTARYDIAL_STROKE_WIDTH = 1
_ROTARYDIAL_PEN = getPenObj(styles.BLUE_STROKE, _ROTARYDIAL_STROKE_WIDTH)
_ROTARYDIAL_BRUSH = getBrushObj('#8099ccff')
_ROTARY_DELTA_WIDTH = 10

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)



class PreXoverItemGroup(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self.setPen(getNoPen())

        iw = _ITEM_WIDTH = 3
        x = _RECT.width() - 2*rect_gain - 2*styles.SLICE_HELIX_STROKE_WIDTH - 1
        y = _RECT.center().y()
        prexo_items = {}
        fwd_angles = [0, 240, 120]
        fwd_colors = ['#cc0000', '#00cc00', '#0000cc']
        for i in range(len(fwd_angles)):
            item = QGraphicsEllipseItem(x, y, iw, iw, self)
            item.setPen(getNoPen())
            item.setBrush(getBrushObj(fwd_colors[i]))
            item.setTransformOriginPoint(_RECT.center())
            item.setRotation(fwd_angles[i])
            prexo_items[i] = item

        rev_angles = [150, 30, 270]
        rev_colors = ['#800000cc', '#80cc0000', '#8000cc00']
        # rev_colors = ['#ff00ff', '#3399ff', '#ff6600']
        for i in range(len(fwd_angles)):
            item = QGraphicsEllipseItem(x, y, iw, iw, self)
            item.setPen(getPenObj(rev_colors[i],0.5))
            item.setBrush(getNoBrush())
            item.setTransformOriginPoint(_RECT.center())
            item.setRotation(rev_angles[i])
            prexo_items[i] = item
    # end def



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
        self.show()

        self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
        self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())
        self.getNeighbors()
        self._right_mouse_move = False
    # end def

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.RightButton:
    #         self._right_mouse_move = True
    #         self._button_down_pos = event.pos()
    # # end def

    # def mouseMoveEvent(self, event):
    #     if self._right_mouse_move:
    #         p = self.mapToScene(event.pos()) - self._button_down_pos
    #         self._empty_helix_item.setPos(p)
    # # end def

    # def mouseReleaseEvent(self, event):
    #     if self._right_mouse_move and event.button() == Qt.RightButton:
    #         self._right_mouse_move = False
    #         p = self.mapToScene(event.pos()) - self._button_down_pos
    #         self._empty_helix_item.setPos(p)
    #         ehi = self._empty_helix_item
    #         self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
    #         self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())
    #         self.getNeighbors()
    # # end def

    def getNeighbors(self):
        vhlist = self._part_item.getVHItemList()
        alllist = '[' + ' '.join([vhi.virtualHelix().getName() for vhi in vhlist]) + ']'
        print(alllist, self.virtualHelix().getName(), self in vhlist)

        items = filter(lambda x: type(x) is VirtualHelixItem, self.collidingItems())
        nlist = '[' + ' '.join([nvhi.virtualHelix().getName() for nvhi in items]) + ']'
        self._virtual_helix.setProperty('neighbors', nlist)
        # name = self._virtual_helix.getName()
        # pos = self.scenePos()
        # print("\n%s (%d, %d)" % (name, pos.x(), pos.y()))
        # for nvhi in items:
        #     npos = nvhi.scenePos()
        #     line = QLineF(pos, npos)
        #     print("\t%s (%d, %d) %d" % (nvhi.virtualHelix().getName(), npos.x(), npos.y(), line.length()))

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

    def virtualHelix(self):
        return self._virtual_helix
    # end def

    def number(self):
        return self.virtualHelix().number()

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
        self.setPen(QPen(Qt.NoPen))
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

