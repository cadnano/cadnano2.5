from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtGui import QRadialGradient, QTransform
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsSimpleTextItem

from cadnano.enum import LatticeType, Parity, PartType, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.virtualhelix import VirtualHelix
from cadnano.gui.palette import getColorObj, getBrushObj, getNoBrush
from cadnano.gui.palette import getPenObj, newPenObj, getNoPen
from . import slicestyles as styles


# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
rect_gain = 0.25
_RECT = _RECT.adjusted(0, 0, rect_gain, rect_gain)
_RECT_CENTERPT = _RECT.center()
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX+3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL) # QBrush(QColor(250, 250, 250))
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_ROTARYDIAL_STROKE_WIDTH = 1
_ROTARYDIAL_PEN = getPenObj(styles.BLUE_STROKE, _ROTARYDIAL_STROKE_WIDTH)
_ROTARYDIAL_BRUSH = getBrushObj('#8099ccff')
_ROTARY_DELTA_WIDTH = 10

_HOVER_PEN = getPenObj('#ff0080', .5)
_HOVER_BRUSH = getBrushObj('#ff0080')

PXI_PP_ITEM_WIDTH = 1.5
TRIANGLE = QPolygonF()
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.append(QPointF(0.75*PXI_PP_ITEM_WIDTH, 0.5*PXI_PP_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, PXI_PP_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, 0))
# TRIANGLE.translate(0, -0.5*PXI_PP_ITEM_WIDTH)
TRIANGLE.translate(-0.75*PXI_PP_ITEM_WIDTH, -0.5*PXI_PP_ITEM_WIDTH)
fwd_t, rev_t = QTransform(), QTransform()
fwd_t.rotate(90)
rev_t.rotate(-90)
FWDPXI_PP, REVPXI_PP = QPainterPath(), QPainterPath()
FWDPXI_PP.addPolygon(fwd_t.map(TRIANGLE))
REVPXI_PP.addPolygon(rev_t.map(TRIANGLE))

class PreXoverItem(QGraphicsPathItem):
    def __init__(self, step_idx, color, is_fwd=True, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        self._step_idx = step_idx
        self._color = color
        self._is_fwd = is_fwd
        self._parent = parent
        self._default_line = QLineF()
        self._bond_line = QGraphicsLineItem(self)
        self._bond_line.hide()
        self.setAcceptHoverEvents(True)
        self.setPen(getNoPen())
        self.setBrush(getNoBrush())
        if self._is_fwd:
            self.setPath(FWDPXI_PP)
            # self._bond_p1_offset = 0.375*PXI_PP_ITEM_WIDTH
            self.setBrush(getBrushObj(self._color, alpha=128))
            self._bond_pen = getPenObj(self._color, 0.25, alpha=42, capstyle=Qt.RoundCap)
            self._active_pen = getPenObj(self._color, 0.25, alpha=128, capstyle=Qt.RoundCap)
            self._bond_line.setPen(self._bond_pen)
        else:
            self.setPath(REVPXI_PP)
            # self._bond_p1_offset = -0.375*PXI_PP_ITEM_WIDTH
            self.setPen(getPenObj(self._color, 0.25, alpha=128))
            self._bond_pen = getPenObj(self._color, 0.25, alpha=64, penstyle=Qt.DotLine, capstyle=Qt.RoundCap)
            self._active_pen = getPenObj(self._color, 0.25, alpha=128, penstyle=Qt.DotLine, capstyle=Qt.RoundCap)
            self._bond_line.setPen(self._bond_pen)
    # end def

    ### ACCESSORS ###
    def facing_angle(self):
        facing_angle = self._parent.virtual_helix_angle() + self.rotation()
        return facing_angle % 360

    def color(self):
        return self._color

    def name(self):
        return "%s.%d" % ("r" if self._is_fwd else "f", self._step_idx)

    def step_idx(self):
        return self._step_idx

    def is_fwd(self):
        return self._is_fwd

    def setBondLineLength(self, value):
        self._bond_line_len = value

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        self._parent.updateModelActivePhos(self)
    # end def

    # def hoverMoveEvent(self, event):
    #     pass
    # # end def

    def hoverLeaveEvent(self, event):
        self._parent.updateModelActivePhos(None)
        self._parent.resetAllItemsAppearance()
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def setActiveBondPos(self, is_active):
        if is_active:
            self._bond_line.setLine(QLineF(0,0,self._bond_line_len,0))
            # self._bond_line.setLine(QLineF(0,self._bond_p1_offset,self._bond_line_len,0))
            self._bond_line.setPen(self._active_pen)
            self._bond_line.show()
        elif self._default_line:
            self._bond_line.setLine(self._default_line)
            self._bond_line.setPen(self._bond_pen)
            self._bond_line.show()
        else:
            self._bond_line.hide()
    # end def

    def setDefaultBondPos(self, scenePos):
        p1 = QPointF(0,0)
        # p1 = QPointF(0,self._bond_p1_offset)
        p2 = self.mapFromScene(scenePos)
        self._default_line = QLineF(p1,p2)
        self._bond_line.setLine(self._default_line)
        self._bond_line.show()
    # end def

    def updateItemApperance(self, is_active):
        self.setActiveBondPos(is_active)
        if is_active:
            if self._is_fwd:
                self.setBrush(getBrushObj(self._color))
            else:
                self.setPen(getPenObj(self._color, 0.25))
        else:
            if self._is_fwd:
                self.setBrush(getBrushObj(self._color, alpha=128))
            else:
                self.setPen(getPenObj(self._color, 0.25, alpha=128))
    # end def
# end class

class PreXoverItemGroup(QGraphicsEllipseItem):
    HUE_FACTOR = 1.6
    SPIRAL_FACTOR = 0.4

    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self._virtual_helix = parent._virtual_helix
        self.fwd_prexo_items = {}
        self.rev_prexo_items = {}
        self.old_active_item = None
        self.setPen(getNoPen())

        part = parent.part()
        _step = part.stepSize()
        _twist = part._TWIST_PER_BASE
        _groove = part.minorGrooveAngle()
        _hue_scale = _step*self.HUE_FACTOR

        _iw = PXI_PP_ITEM_WIDTH
        _ctr = self.mapToParent(_RECT).boundingRect().center()
        _x = _ctr.x() + _RADIUS - PXI_PP_ITEM_WIDTH 
        _y = _ctr.y()

        colors = [QColor.fromHsvF(i/_hue_scale, 0.75, 0.8).name() for i in range(_step)]

        for i in range(_step):
            inset = i*self.SPIRAL_FACTOR # spiral layout
            fwd = PreXoverItem(i, colors[i], is_fwd=True, parent=self)
            rev = PreXoverItem(i, colors[-1-i], is_fwd=False, parent=self)
            fwd.setPos(_x-inset, _y)
            rev.setPos(_x-inset, _y)
            fwd.setTransformOriginPoint((-_RADIUS+_iw+inset), 0)
            rev.setTransformOriginPoint((-_RADIUS+_iw+inset), 0)
            fwd.setRotation(round((i*_twist) % 360, 3))
            rev.setRotation(round((i*_twist+_groove) % 360, 3))
            fwd.setBondLineLength(inset+_iw)
            rev.setBondLineLength(inset+_iw)
            self.fwd_prexo_items[i] = fwd
            self.rev_prexo_items[i] = rev

        for i in range(_step-1):
            fwd, next_fwd = self.fwd_prexo_items[i], self.fwd_prexo_items[i+1]
            j = (_step-1)-i
            rev, next_rev = self.rev_prexo_items[j], self.rev_prexo_items[j-1]
            fwd.setDefaultBondPos(next_fwd.scenePos())
            rev.setDefaultBondPos(next_rev.scenePos())
    # end def

    ### ACCESSORS ###
    def virtual_helix_angle(self):
        return self._virtual_helix.getProperty('eulerZ')

    def getItem(self, is_fwd, step_idx):
        items = self.fwd_prexo_items if is_fwd else self.rev_prexo_items
        if step_idx in items:
            return items[step_idx]
        else:
            return None
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def updateModelActivePhos(self, pre_xover_item):
        """Notify model of pre_xover_item hover state."""
        if pre_xover_item is None:
            # self._virtual_helix.part().setProperty('active_phos_pos', None)
            self._virtual_helix.setProperty('active_phos', None)
            return
        vh_name = self._virtual_helix.getName()
        vh_angle = self._virtual_helix.getProperty('eulerZ')
        step_idx = pre_xover_item.step_idx() # (f|r).step_idx
        facing_angle = (vh_angle + pre_xover_item.rotation()) % 360
        is_fwd = 'fwd' if pre_xover_item.is_fwd() else 'rev'
        value = "%s.%s.%d.%0d" % (vh_name, is_fwd, step_idx, facing_angle)
        # p = pre_xover_item.scenePos()
        # pos = '%d,%d' % (p.x(), p.y())
        # self._virtual_helix.part().setProperty('active_phos_pos', pos)
        self._virtual_helix.setProperty('active_phos', value)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        """Refresh appearance of items whose active state changed."""
        if self.old_active_item:
            self.old_active_item.updateItemApperance(False)
        if new_active_item:
            new_active_item.updateItemApperance(True)
            self.old_active_item = new_active_item
    # end def

    def resetAllItemsAppearance(self):
        for item in self.fwd_prexo_items.values():
            item.updateItemApperance(False)
        for item in self.rev_prexo_items.values():
            item.updateItemApperance(False)
    # end def

    def getItemsFacingNearAngle(self, angle):
        _span = self._parent.partCrossoverSpanAngle()/2
        lowZ = angle-_span
        highZ = angle+_span
        fwd = list(filter(lambda p: lowZ < p.facing_angle() < highZ , self.fwd_prexo_items.values()))
        rev = list(filter(lambda p: lowZ < p.facing_angle() < highZ , self.rev_prexo_items.values()))
        return (fwd, rev)
    # end def


class PreCrossoverGizmo(QGraphicsLineItem):
    def __init__(self, pre_xover_item, active_scenePos, parent=None):
        super(QGraphicsLineItem, self).__init__(parent)
        p1 = parent.mapFromScene(pre_xover_item.scenePos())
        p2 = parent.mapFromScene(active_scenePos)
        self.setLine(QLineF(p1, p2))
        color = pre_xover_item.color()
        self.setPen(getPenObj(color, 0.25, alpha=32, capstyle=Qt.RoundCap))
        # self.setZValue(styles.ZGIZMO)
    # end def
# end class

class LineGizmo(QGraphicsLineItem):
    def __init__(self, line, color, nvhi, parent=None):
        super(QGraphicsLineItem, self).__init__(line, parent)
        self.nvhi = nvhi
        self.nvhi_name = nvhi.virtualHelix().getName()
        self.setPen(getPenObj(color, 0.25))
    # end def

    def angle(self):
        return 360-self.line().angle()
# end class

class WedgeGizmo(QGraphicsPathItem):
    def __init__(self, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        self._parent = parent
        self.setPen(getNoPen())
        self._last_params = None

    def showWedge(self, pos, angle, color, extended=False, rev_gradient=False, outline_only=False):
        self._last_params = (pos, angle, color, extended, rev_gradient, outline_only)
        _span = self._parent.partCrossoverSpanAngle()/2
        _r = _RADIUS+(rect_gain/2)
        _c = _RECT_CENTERPT
        _EXT = 1.35 if extended else 1.0
        _line = QLineF(_c, pos)
        line1 = QLineF(_c, pos)
        line2 = QLineF(_c, pos)
        _line.setLength(_r*_EXT*1.02) # for quadTo control point
        line1.setLength(_r*_EXT)
        line2.setLength(_r*_EXT)
        _line.setAngle(angle)
        line1.setAngle(angle-_span)
        line2.setAngle(angle+_span)

        path = QPainterPath()

        if outline_only:
            self.setPen(getPenObj(color, 0.5, alpha=128, capstyle=Qt.RoundCap))
            path.moveTo(line1.p2())
            path.quadTo(_line.p2(), line2.p2())
            self.setPath(path)
            self.show()
        else:
            gradient = QRadialGradient(_c, _r*_EXT*1.11)
            color1 = getColorObj(color, alpha=80)
            color2 = getColorObj(color, alpha=24)
            if rev_gradient:
                color1, color2 = color2, color1

            if extended:
                gradient.setColorAt(0, color1)
                gradient.setColorAt(0.66, color1)
                gradient.setColorAt(0.67, color2)
                gradient.setColorAt(1, color2)
            else:
                gradient.setColorAt(0, getColorObj(color, alpha=50))
            brush = QBrush(gradient)
            self.setBrush(brush)

            path.moveTo(line1.p1())
            path.lineTo(line1.p2())
            path.quadTo(_line.p2(), line2.p2())
            path.lineTo(line2.p1())
        self.setPath(path)
        self.show()
    # end def

    def updateWedgeAngle(self):
        self.showWedge(*self._last_params)
    # end def

    def update(self, pre_xover_item):
        pxi = pre_xover_item
        pos = pxi.pos()
        angle = -pxi.rotation()
        color = pxi.color()
        if pxi.is_fwd():
            self.showWedge(pos, angle, color, extended=True)
        else:
            self.showWedge(pos, angle, color, extended=True, rev_gradient=True)
    # end def
# end class


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
        self._prexoveritemgroup = _pxig = PreXoverItemGroup(_RECT, self)

        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(_ZVALUE)
        self.lastMousePressAddedBases = False

        self.hide()
        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self._pen1, self._pen2 = (QPen(), QPen())
        self.createArrows()
        self.updateAppearance()

        self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
        self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())

        _pxig.setTransformOriginPoint(_RECT.center())
        _pxig.setRotation(self._virtual_helix.getProperty('eulerZ'))
        self._line_gizmos = []
        self._wedge_gizmos = []
        self._prexo_gizmos = []
        self._neighbor_vh_items = []
        self._right_mouse_move = False
        self.refreshCollidingItems()
        self.show()
    # end def

    ### ACCESSORS ###
    def part(self):
        return self._empty_helix_item.part()
    # end def

    def parent(self):
        return self._empty_helix_item
    # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def

    def partCrossoverSpanAngle(self):
        return float(self.part().getProperty('crossover_span_angle'))
    # end def

    def virtualHelix(self):
        return self._virtual_helix
    # end def

    def number(self):
        return self.virtualHelix().number()
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

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._right_mouse_move = True
            self._button_down_pos = event.pos()
    # end def

    def mouseMoveEvent(self, event):
        if self._right_mouse_move:
            p = self.mapToScene(event.pos()) - self._button_down_pos
            self._empty_helix_item.setPos(p)
            ehi = self._empty_helix_item
            self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
            self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())
            self.refreshCollidingItems()
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

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###

    def refreshCrossoverSpanAngles(self):
        for wg in self._wedge_gizmos:
            wg.updateWedgeAngle()
    # end def

    def refreshCollidingItems(self):
        """Update props and appearance of self & recent neighbors."""
        neighbors = []
        old_neighbors = self._virtual_helix.getProperty('neighbors').split()

        items = list(filter(lambda x: type(x) is VirtualHelixItem, self.collidingItems()))
        while self._line_gizmos: # clear old gizmos
            self.scene().removeItem(self._line_gizmos.pop())
        while self._wedge_gizmos:
            self.scene().removeItem(self._wedge_gizmos.pop())
        for nvhi in items:
            nvhi_name = nvhi.virtualHelix().getName()
            pos = self.scenePos()
            line = QLineF(pos, nvhi.scenePos())
            line.translate(_RADIUS-pos.x(),_RADIUS-pos.y())
            
            if line.length() > (_RADIUS*1.99):
                color = '#5a8bff' 
            else:
                color = '#cc0000'
                nvhi_name = nvhi_name + '*' # mark as invalid
            line.setLength(_RADIUS)
            line_item = LineGizmo(line, color, nvhi, self)
            line_item.hide()
            wedge_item = WedgeGizmo(self)
            wedge_item.showWedge(line.p1(), line.angle(), color, outline_only=False)
            self._line_gizmos.append(line_item) # save ref to clear later
            self._wedge_gizmos.append(wedge_item)
            neighbors.append('%s:%02d' % (nvhi_name, 360-line.angle()))
        # end for

        self._virtual_helix.setProperty('neighbors', ' '.join(sorted(neighbors)))
        added = list(set(neighbors) - set(old_neighbors)) # includes new angles
        removed = list(set(old_neighbors) - set(neighbors))
        for nvhi in self._part_item.getVHItemList(): # check all items
            nvhi_name = nvhi.virtualHelix().getName()
            alt_name = nvhi_name + '*'
            changed_names = [a.split(':')[0] for a in added] + \
                            [r.split(':')[0] for r in removed]
            if nvhi_name in changed_names or alt_name in changed_names:
                nvhi.refreshCollidingItems()

        # end for
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
        _pxig = self._prexoveritemgroup
        if property_key == 'eulerZ':
            _pxig.setRotation(new_value)
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
        elif property_key == 'active_phos':
            if new_value:
                vh_name, fwd_str, step_idx, facing_angle = new_value.split('.')
                is_fwd = 1 if fwd_str == 'fwd' else 0
                new_active_item = _pxig.getItem(int(is_fwd), int(step_idx))
                _pxig.updateViewActivePhos(new_active_item)
                self.updateNeighborsNearActivePhos(new_active_item, True)
            else:
                self.updateNeighborsNearActivePhos(_pxig.old_active_item, False)
                _pxig.updateViewActivePhos(None)
                self._virtual_helix.setProperty('neighbor_active_angle', '')
        elif property_key == 'neighbor_active_angle':
            if new_value:
                local_angle = (int(new_value)+180) % 360
                fwd_items, rev_items = _pxig.getItemsFacingNearAngle(local_angle)
                for item in fwd_items+rev_items:
                    item.updateItemApperance(True)
            else:
                _pxig.resetAllItemsAppearance()
    # end def


    def getPreXoverItemsFacingNearAngle(self, angle):
        return self._prexoveritemgroup.getItemsFacingNearAngle(angle)
    # end def

    def updateNeighborsNearActivePhos(self, item, is_active):
        """Update part prop to reflect VHs near the active (hovered) phos."""
        _vh = self._virtual_helix
        if not is_active:
            _vh.part().setProperty('neighbor_active_angle', '')
            return

        facing_angle = item.facing_angle()
        ret = []
        span = self.partCrossoverSpanAngle()/2
        lowZ  = facing_angle - span
        highZ = facing_angle + span
        neighbors = _vh.getProperty('neighbors').split()
        for n in neighbors:
            n_name, n_angle = n.split(':')
            n_angle = int(n_angle)
            d = n_angle-facing_angle
            if lowZ < n_angle < highZ:
                ret.append('%s:%d' % (n_name, n_angle+d))
        _vh.part().setProperty('neighbor_active_angle', ' '.join(ret))


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

