from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QEvent, QLineF, QObject, QPointF, Qt, QRectF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty, QTimer
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtGui import QRadialGradient, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem
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
_RECT_GAIN = 0.25
_RECT = _RECT.adjusted(0, 0, _RECT_GAIN, _RECT_GAIN)
_RECT_CENTERPT = _RECT.center()
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX+3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL)
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_HOVER_PEN = getPenObj('#ff0080', .5)
_HOVER_BRUSH = getBrushObj('#ff0080')

PXI_PP_ITEM_WIDTH = IW = 1.5
TRIANGLE = QPolygonF()
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.append(QPointF(0.75*IW, 0.5*IW))
TRIANGLE.append(QPointF(0, IW))
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.translate(-0.75*IW, -0.5*IW)
PXI_RECT = QRectF(0, 0, IW, IW)
T90, T270 = QTransform(), QTransform()
T90.rotate(90)
T270.rotate(270)
FWDPXI_PP, REVPXI_PP = QPainterPath(), QPainterPath()
FWDPXI_PP.addPolygon(T90.map(TRIANGLE))
REVPXI_PP.addPolygon(T270.map(TRIANGLE))


class PropertyWrapperObject(QObject):
    def __init__(self, item):
        super(PropertyWrapperObject, self).__init__()
        self._item = item
        self._animations = {}

    def __get_bondP2(self):
        return self._item.line().p2()

    def __set_bondP2(self, p2):
        p1 = self._item.line().p1()
        line = QLineF(p1.x(),p1.y(),p2.x(),p2.y())
        self._item.setLine(line)

    def __get_rotation(self):
        return self._item.rotation()

    def __set_rotation(self, angle):
        self._item.setRotation(angle)

    def __get_penAlpha(self):
        return self._item.pen().color().alpha()
 
    def __set_penAlpha(self, alpha):
        pen = QPen(self._item.pen())
        color = QColor(self._item.pen().color())
        color.setAlpha(alpha)
        pen.setColor(color)
        self._item.setPen(pen)

    def saveRef(self, property_name, animation):
        self._animations[property_name] = animation

    bondp2 = pyqtProperty(QPointF, __get_bondP2, __set_bondP2)
    pen_alpha = pyqtProperty(int, __get_penAlpha, __set_penAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class

class Triangle(QGraphicsPathItem):
    def __init__(self, is_fwd, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        color = parent._color
        self.adapter = PropertyWrapperObject(self)
        self.setAcceptHoverEvents(True)
        self._click_area = cA = QGraphicsRectItem(PXI_RECT, self)
        cA.setAcceptHoverEvents(True)
        cA.setPen(getNoPen())
        cA.hoverMoveEvent = self.hoverMoveEvent
        if is_fwd:
            self.setPath(FWDPXI_PP)
            self.setPen(getNoPen())
            self.setBrush(getBrushObj(color, alpha=128))
            self._click_area.setPos(-0.5*IW, -0.75*IW)
        else:
            self.setPath(REVPXI_PP)
            self.setPen(getPenObj(color, 0.25, alpha=128))
            self._click_area.setPos(-0.5*IW, -0.25*IW)
    # end def
# end class

class PhosBond(QGraphicsLineItem):
    def __init__(self, is_fwd, parent=None):
        super(PhosBond, self).__init__(parent)
        self.adapter = PropertyWrapperObject(self)
        color = parent._color
        if is_fwd: # lighter solid
            self.setPen(getPenObj(color, 0.25, alpha=42, capstyle=Qt.RoundCap))
        else: # darker, dotted
            self.setPen(getPenObj(color, 0.25, alpha=64, penstyle=Qt.DotLine, capstyle=Qt.RoundCap))
    # end def
# end class

class PreXoverItem(QGraphicsPathItem):
    def __init__(self, step_idx, color, is_fwd=True, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        self._step_idx = step_idx
        self._color = color
        self._is_fwd = is_fwd
        self._parent = parent
        self._phos_item = Triangle(is_fwd, self)
        self._item_5p = None
        self._item_3p = None
        self._default_line_5p = QLineF()
        self._default_line_3p = QLineF()
        self._default_p2_5p = QPointF(0,0)
        self._default_p2_3p = QPointF(0,0)
        self._5p_line = PhosBond(is_fwd, self)
        self._5p_line.hide()
        self._3p_line = PhosBond(is_fwd, self)
        # self.adapter = PropertyWrapperObject(self)
        self.setAcceptHoverEvents(True)
        self.setFiltersChildEvents(True)
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
        self._active_p2_3p = QPointF(value, 0)
        self._active_p2_5p = QPointF(value, 0)

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        self._parent.updateModelActivePhos(self)
    # end def

    def hoverLeaveEvent(self, event):
        self._parent.updateModelActivePhos(None)
        self._parent.resetAllItemsAppearance()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def animate(self, item, property_name, duration, start_value, end_value):
        b_name = property_name.encode('ascii')
        anim = QPropertyAnimation(item.adapter, b_name)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()
        item.adapter.saveRef(property_name, anim)


    ### PUBLIC SUPPORT METHODS ###
    def setActive5p(self, is_active):
        phos = self._phos_item
        bond = self._5p_line
        if bond is None: return

        if is_active:
            angle = 90 if self._is_fwd else -90
            self.animate(phos, 'rotation', 300, 0, angle)
            bond.show()
            if self._item_5p:
                self._item_5p._3p_line.hide()
            self.animate(bond, 'bondp2', 300, self._default_p2_5p, self._active_p2_5p)
        else:
            QTimer.singleShot(300, bond.hide)
            self.animate(phos, 'rotation', 300, phos.rotation(), 0)
            if self._item_5p: QTimer.singleShot(300, self._item_5p._3p_line.show)
            self.animate(bond, 'bondp2', 300, self._active_p2_5p, self._default_p2_5p)
    # end def

    def setActive3p(self, is_active):
        phos = self._phos_item
        bond = self._3p_line
        if self._5p_line: self._5p_line.hide()
        if is_active:
            angle = -90 if self._is_fwd else 90
            self.animate(phos, 'rotation', 300, 0, angle)
            self.animate(bond, 'bondp2', 300, self._default_p2_3p, self._active_p2_3p)
            alpha = 42 if self._is_fwd else 64
            self.animate(bond, 'pen_alpha', 300, alpha, 180)
        else:
            self.animate(phos, 'rotation', 300, phos.rotation(), 0)
            self.animate(bond, 'bondp2', 300, bond.line().p2(), self._default_p2_3p)
            start_alpha = bond.pen().color().alpha()
            end_alpha = 42 if self._is_fwd else 64
            self.animate(bond, 'pen_alpha', 300, start_alpha, end_alpha)
    # end def

    def set5pItem(self, item_5p):
        self._item_5p = item_5p
        scenePos = item_5p.scenePos()
        p1 = QPointF(0,0)
        p2 = self.mapFromScene(scenePos)
        self._default_p2_5p = p2
        self._default_line_5p = QLineF(p1,p2)
        self._5p_line.setLine(self._default_line_5p)
    # end def

    def set3pItem(self, item_3p):
        self._item_3p = item_3p
        scenePos = item_3p.scenePos()
        p1 = QPointF(0,0)
        p2 = self.mapFromScene(scenePos)
        self._default_p2_3p = p2
        self._default_line_3p = QLineF(p1,p2)
        self._3p_line.setLine(self._default_line_3p)
    # end def

    def updateItemApperance(self, is_active, show_3p=True):
        if show_3p:
            self.setActive3p(is_active)
        else:
            self.setActive5p(is_active)
    # end def
# end class

class PreXoverItemGroup(QGraphicsEllipseItem):
    HUE_FACTOR = 1.6
    SPIRAL_FACTOR = 0.4

    def __init__(self, radius, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._radius = radius
        self._rect = rect
        self._parent = parent
        self._virtual_helix = parent._virtual_helix
        self._active_item = None
        self._active_wedge_gizmo = WedgeGizmo(radius, rect, self)
        self.fwd_prexo_items = {}
        self.rev_prexo_items = {}
        self._colors = self._get_colors()
        self.addItems()
        self.setPen(getNoPen())
        self.setZValue(styles.ZPXIGROUP)
    # end def

    ### ACCESSORS ###
    def virtual_helix_angle(self):
        return self._virtual_helix.getProperty('eulerZ')
    # end def

    def getItem(self, is_fwd, step_idx):
        items = self.fwd_prexo_items if is_fwd else self.rev_prexo_items
        if step_idx in items:
            return items[step_idx]
        else:
            return None
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def _get_colors(self):
        step_size = self._parent.basesPerRepeat()
        _hue_scale = step_size*self.HUE_FACTOR
        return [QColor.fromHsvF(i/_hue_scale, 0.75, 0.8).name() for i in range(step_size)]
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def addItems(self):
        _radius = self._radius
        _step = self._parent.basesPerRepeat()
        _twist = self._parent.twistPerBase()
        _groove = self._parent.part().minorGrooveAngle()
        _hue_scale = _step*self.HUE_FACTOR

        _iw = PXI_PP_ITEM_WIDTH
        _ctr = self.mapToParent(self._rect).boundingRect().center()
        _x = _ctr.x() + _radius - PXI_PP_ITEM_WIDTH 
        _y = _ctr.y()

        for i in range(_step):
            inset = i*self.SPIRAL_FACTOR # spiral layout
            fwd = PreXoverItem(i, self._colors[i], is_fwd=True, parent=self)
            rev = PreXoverItem(i, self._colors[-1-i], is_fwd=False, parent=self)
            fwd.setPos(_x-inset, _y)
            rev.setPos(_x-inset, _y)
            fwd.setTransformOriginPoint((-_radius+_iw+inset), 0)
            rev.setTransformOriginPoint((-_radius+_iw+inset), 0)
            fwd.setRotation(round((i*_twist)%360, 3))
            rev.setRotation(round((i*_twist+_groove)%360, 3))
            fwd.setBondLineLength(inset+_iw)
            rev.setBondLineLength(inset+_iw)
            self.fwd_prexo_items[i] = fwd
            self.rev_prexo_items[i] = rev

        for i in range(_step-1):
            fwd, next_fwd = self.fwd_prexo_items[i], self.fwd_prexo_items[i+1]
            j = (_step-1)-i
            rev, next_rev = self.rev_prexo_items[j], self.rev_prexo_items[j-1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def removeItems(self):
        for i in range(len(self.fwd_prexo_items)):
            self.scene().removeItem(self.fwd_prexo_items.pop(i))
            self.scene().removeItem(self.rev_prexo_items.pop(i))
    # end def

    def updateBasesPerRepeat(self):
        self._colors = self._get_colors()
        self.removeItems()
        self.addItems()
    # end def

    def updateTurnsPerRepeat(self):
        twist_per_base = self._parent.twistPerBase()
        step_size = self._parent.basesPerRepeat()
        _groove = self._parent.part().minorGrooveAngle()
        for i in range(step_size):
            fwd = self.fwd_prexo_items[i]
            rev = self.rev_prexo_items[i]
            fwd.setRotation(round((i*twist_per_base)%360, 3))
            rev.setRotation(round((i*twist_per_base+_groove)%360, 3))
        for i in range(step_size-1):
            fwd, next_fwd = self.fwd_prexo_items[i], self.fwd_prexo_items[i+1]
            j = (step_size-1)-i
            rev, next_rev = self.rev_prexo_items[j], self.rev_prexo_items[j-1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def partCrossoverSpanAngle(self):
        return self._parent.partCrossoverSpanAngle()

    def updateModelActivePhos(self, pre_xover_item):
        """Notify model of pre_xover_item hover state."""
        if pre_xover_item is None:
            self._parent.part().setProperty('active_phos', None)
            self._virtual_helix.setProperty('active_phos', None)
            return
        vh_name = self._virtual_helix.getName()
        vh_angle = self._virtual_helix.getProperty('eulerZ')
        step_idx = pre_xover_item.step_idx() # (f|r).step_idx
        facing_angle = (vh_angle + pre_xover_item.rotation()) % 360
        is_fwd = 'fwd' if pre_xover_item.is_fwd() else 'rev'
        value = "%s.%s.%d.%0d" % (vh_name, is_fwd, step_idx, facing_angle)
        self._parent.part().setProperty('active_phos', value)
        self._virtual_helix.setProperty('active_phos', value)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        """Refresh appearance of items whose active state changed."""
        if self._active_item:
            self._active_item.updateItemApperance(False, show_3p=True)
            self._active_wedge_gizmo.hide()
        if new_active_item:
            new_active_item.updateItemApperance(True, show_3p=True)
            self._active_wedge_gizmo.showActive(new_active_item)
            self._active_item = new_active_item
    # end def

    def resetAllItemsAppearance(self):
        for item in self.fwd_prexo_items.values():
            item.updateItemApperance(False, show_3p=False)
        for item in self.rev_prexo_items.values():
            item.updateItemApperance(False, show_3p=False)
    # end def

    def getItemsFacingNearAngle(self, angle):
        _span = self._parent.partCrossoverSpanAngle()/2
        fwd = list(filter(lambda p: \
                            180-abs(abs(p.facing_angle()-angle)-180)<_span,\
                            self.fwd_prexo_items.values()))
        rev = list(filter(lambda p: \
                            180-abs(abs(p.facing_angle()-angle)-180)<_span,\
                            self.rev_prexo_items.values()))
        return (fwd, rev)
    # end def
# end class


class PreCrossoverGizmo(QGraphicsLineItem):
    def __init__(self, pre_xover_item, active_scenePos, parent=None):
        super(QGraphicsLineItem, self).__init__(parent)
        p1 = parent.mapFromScene(pre_xover_item.scenePos())
        p2 = parent.mapFromScene(active_scenePos)
        self.setLine(QLineF(p1, p2))
        color = pre_xover_item.getColor()
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
    def __init__(self, radius, rect, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        self._radius = radius
        self._rect = rect
        self._parent = parent
        self.setPen(getNoPen())
        self.setZValue(styles.ZWEDGEGIZMO)
        self._last_params = None

    def showWedge(self, pos, angle, color, extended=False, rev_gradient=False, outline_only=False):
        self._last_params = (pos, angle, color, extended, rev_gradient, outline_only)
        _radius = self._radius
        _span = self._parent.partCrossoverSpanAngle()/2
        _r = _radius+(_RECT_GAIN/2)
        _c = self._rect.center()
        _EXT = 1.35 if extended else 1.0
        _line = QLineF(_c, pos)
        line1 = QLineF(_c, pos)
        line2 = QLineF(_c, pos)
        
        _quad_scale = 1+(.22*(_span-5)/55) # lo+(hi-lo)*(val-min)/(max-min)
        _line.setLength(_r*_EXT*_quad_scale) # for quadTo control point
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
            gradient = QRadialGradient(_c, _r*_EXT)
            color1 = getColorObj(color, alpha=80)
            color2 = getColorObj(color, alpha=0)
            if rev_gradient:
                color1, color2 = color2, color1

            if extended:
                gradient.setColorAt(0, color1)
                gradient.setColorAt(_r/(_r*_EXT), color1)
                gradient.setColorAt(_r/(_r*_EXT)+0.01, color2)
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

    def showActive(self, pre_xover_item):
        pxi = pre_xover_item
        pos = pxi.pos()
        angle = -pxi.rotation()
        color = pxi.color()
        # self.showWedge(pos, angle, color, span=5.0)
        if pxi.is_fwd():
            self.showWedge(pos, angle, color, extended=True, rev_gradient=True)
            # self.showWedge(pos, angle, color, extended=True)
        else:
            self.showWedge(pos, angle, color, extended=True, rev_gradient=True)
            # self.showWedge(pos, angle, color, extended=True, rev_gradient=True)
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
        self._virtual_helix = m_vh = model_virtual_helix
        self._empty_helix_item = ehi = empty_helix_item
        self._part_item = ehi._part_item
        self._controller = VirtualHelixItemController(self, m_vh)
        self._bases_per_repeat = m_vh.getProperty('bases_per_repeat')
        self._turns_per_repeat = m_vh.getProperty('turns_per_repeat')
        # self._twist_per_base = m_vh.getProperty('_twist_per_base')
        self._prexoveritemgroup = pxig = PreXoverItemGroup(_RADIUS, _RECT, self)

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

        self._virtual_helix.setProperty('x', ehi.mapToScene(0,0).x())
        self._virtual_helix.setProperty('y', ehi.mapToScene(0,0).y())

        pxig.setTransformOriginPoint(_RECT.center())
        pxig.setRotation(self._virtual_helix.getProperty('eulerZ'))
        self._line_gizmos = []
        self._wedge_gizmos = []
        self._prexo_gizmos = []
        self._neighbor_vh_items = []
        self._right_mouse_move = False
        self.refreshCollidingItems()
        self.show()
    # end def

    ### ACCESSORS ###
    def basesPerRepeat(self):
        return self._bases_per_repeat

    def turnsPerRepeat(self):
        return self._turns_per_repeat

    def twistPerBase(self):
        bases_per_turn = self._bases_per_repeat/self._turns_per_repeat
        return 360./bases_per_turn

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
        return self._virtual_helix.number()
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

    def addStrandsAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()
        if vh is None:
            return

        idx = part.activeBaseIndex()
        start_idx = max(0,idx-1)
        end_idx = min(idx+1, part.maxBaseIdx())
        vh.scaffoldStrandSet().createStrand(start_idx, end_idx)
        vh.stapleStrandSet().createStrand(start_idx, end_idx)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.addStrandsAtActiveSliceIfMissing()
        elif event.button() == Qt.RightButton:
            self._right_mouse_move = True
            self._button_down_pos = event.pos()
    # end def

    def mouseMoveEvent(self, event):
        if self._right_mouse_move:
            p = self.mapToScene(event.pos()) - self._button_down_pos
            self._empty_helix_item.setPos(p)
            ehi = self._empty_helix_item
            self._virtual_helix.setProperty('x', ehi.mapToScene(0,0).x())
            self._virtual_helix.setProperty('y', ehi.mapToScene(0,0).y())
            self.refreshCollidingItems()
    # end def

    def mouseReleaseEvent(self, event):
        if self._right_mouse_move and event.button() == Qt.RightButton:
            self._right_mouse_move = False
            p = self.mapToScene(event.pos()) - self._button_down_pos
            self._empty_helix_item.setPos(p)
            ehi = self._empty_helix_item
            self._virtual_helix.setProperty('x', ehi.mapToScene(0,0).x())
            self._virtual_helix.setProperty('y', ehi.mapToScene(0,0).y())
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
            wedge_item = WedgeGizmo(_RADIUS, _RECT, self)
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
        pxig = self._prexoveritemgroup
        ### TRANSFORM PROPERTIES ###
        if property_key == 'eulerZ':
            pxig.setRotation(new_value)
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
        elif property_key == 'x':
            ehi_pos = self._empty_helix_item.scenePos()
            self._empty_helix_item.setPos(new_value, ehi_pos.y())
        elif property_key == 'y':
            ehi_pos = self._empty_helix_item.scenePos()
            self._empty_helix_item.setPos(ehi_pos.x(),new_value)
        ### GEOMETRY PROPERTIES ###
        elif property_key == 'bases_per_repeat':
            self._bases_per_repeat = int(new_value)
            pxig.updateBasesPerRepeat()
            # pxig.updateTwist()
        elif property_key == 'turns_per_repeat':
            self._turns_per_repeat = int(new_value)
            pxig.updateTurnsPerRepeat()
        ### RUNTIME PROPERTIES ###
        elif property_key == 'active_phos':
            if new_value:
                vh_name, fwd_str, base_idx, facing_angle = new_value.split('.')
                is_fwd = True if fwd_str == 'fwd' else False
                step_idx = int(base_idx) % self._bases_per_repeat
                new_active_item = pxig.getItem(is_fwd, step_idx)
                pxig.updateViewActivePhos(new_active_item)
                self.updateNeighborsNearActivePhos(new_active_item, True)
                self.setZValue(_ZVALUE+1)
            else:
                self.updateNeighborsNearActivePhos(pxig._active_item, False)
                pxig.updateViewActivePhos(None)
                self._virtual_helix.setProperty('neighbor_active_angle', '')
        elif property_key == 'neighbor_active_angle':
            if new_value:
                local_angle = (int(new_value)+180) % 360
                fwd_items, rev_items = pxig.getItemsFacingNearAngle(local_angle)
                for item in fwd_items+rev_items:
                    item.updateItemApperance(True, show_3p=False)
            else:
                pxig.resetAllItemsAppearance()
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
        neighbors = _vh.getProperty('neighbors').split()
        for n in neighbors:
            n_name, n_angle = n.split(':')
            n_angle = int(n_angle)
            d = n_angle-facing_angle
            if 180-abs(abs(d)-180)<span:
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
        tpb = self._twist_per_base
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
        tpb = self._twist_per_base
        angle = idx*tpb
        eulerZ = float(self._virtual_helix.getProperty('eulerZ'))
        self.arrow2.setRotation(angle + part._TWIST_OFFSET + eulerZ + 150)
    # end def

    def setActiveSliceView(self, idx, has_fwd, has_rev):
        return
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
