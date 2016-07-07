from PyQt5.QtCore import QLineF, QObject, QPointF, Qt, QRectF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty, QTimer
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtGui import QRadialGradient, QTransform
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsEllipseItem

from cadnano.gui.palette import getColorObj, getBrushObj, getNoBrush
from cadnano.gui.palette import getPenObj, newPenObj, getNoPen
from . import slicestyles as styles

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
FWDPXI_PP.addPolygon(T270.map(TRIANGLE))
REVPXI_PP.addPolygon(T90.map(TRIANGLE))

_RADIUS = styles.SLICE_HELIX_RADIUS
_WEDGE_RECT_GAIN = 0.25
WEDGE_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
WEDGE_RECT = WEDGE_RECT.adjusted(0, 0, _WEDGE_RECT_GAIN, _WEDGE_RECT_GAIN)
_WEDGE_RECT_CENTERPT = WEDGE_RECT.center()

class PropertyWrapperObject(QObject):
    def __init__(self, item):
        super(PropertyWrapperObject, self).__init__()
        self.item = item
        self.animations = {}

    def __get_bondP2(self):
        return self.item.line().p2()

    def __set_bondP2(self, p2):
        p1 = self.item.line().p1()
        line = QLineF(p1.x(), p1.y(), p2.x(), p2.y())
        self.item.setLine(line)

    def __get_rotation(self):
        return self.item.rotation()

    def __set_rotation(self, angle):
        self.item.setRotation(angle)

    def __get_penAlpha(self):
        return self.item.pen().color().alpha()

    def __set_penAlpha(self, alpha):
        pen = QPen(self.item.pen())
        color = QColor(self.item.pen().color())
        color.setAlpha(alpha)
        pen.setColor(color)
        self.item.setPen(pen)

    def saveRef(self, property_name, animation):
        self.animations[property_name] = animation

    def getRef(self, property_name):
        return self.animations.get(property_name)

    def resetAnimations(self):
        for item in self.animations.values():
            item.deleteLater()
        self.item = None
        self.animations = {}


    bondp2 = pyqtProperty(QPointF, __get_bondP2, __set_bondP2)
    pen_alpha = pyqtProperty(int, __get_penAlpha, __set_penAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class

class Triangle(QGraphicsPathItem):
    def __init__(self, is_fwd, pre_xover_item):
        super(Triangle, self).__init__(pre_xover_item)
        color = pre_xover_item.color
        self.adapter = PropertyWrapperObject(self)
        self.setAcceptHoverEvents(True)
        self._click_area = click_area = QGraphicsRectItem(PXI_RECT, self)
        click_area.setAcceptHoverEvents(True)
        click_area.setPen(getNoPen())
        click_area.hoverMoveEvent = self.hoverMoveEvent
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
        color = parent.color
        if is_fwd: # lighter solid
            self.setPen(getPenObj(color, 0.25, alpha=42, capstyle=Qt.RoundCap))
        else: # darker, dotted
            self.setPen(getPenObj(color, 0.25,
                                    alpha=64,
                                    penstyle=Qt.DotLine,
                                    capstyle=Qt.RoundCap))
    # end def
# end class

class PreXoverItem(QGraphicsPathItem):
    def __init__(self, step_idx, color, pre_xover_item_group, is_fwd=True):
        super(PreXoverItem, self).__init__(pre_xover_item_group)
        self.step_idx = step_idx
        self.color = color
        self.is_fwd = is_fwd
        self.pre_xover_item_group = pre_xover_item_group
        self.phos_item = Triangle(is_fwd, self)
        self.item_5p = None
        self.item_3p = None
        self._default_line_5p = QLineF()
        self._default_line_3p = QLineF()
        self._default_p2_5p = QPointF(0,0)
        self._default_p2_3p = QPointF(0,0)
        self.line_5p = PhosBond(is_fwd, self)
        self.line_5p.hide()
        self.line_3p = PhosBond(is_fwd, self)

        self.setAcceptHoverEvents(True)
        self.setFiltersChildEvents(True)
    # end def

    ### ACCESSORS ###
    def facingAngle(self):
        facing_angle = self.pre_xover_item_group.eulerZAngle() + self.rotation()
        return facing_angle % 360

    def getInfo(self):
        """
        Returns:
            Tuple: (from_id_num, is_fwd, from_index, to_vh_id_num)
        """
        return (self.pre_xover_item_group.id_num, self.is_fwd, self.step_idx, None)

    def name(self):
        return "%s.%d" % ("r" if self.is_fwd else "f", self.step_idx)

    def stepIdx(self):
        return self.step_idx

    def setBondLineLength(self, value):
        self._active_p2_3p = QPointF(value, 0)
        self._active_p2_5p = QPointF(value, 0)

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        pxig = self.pre_xover_item_group
        if pxig.is_active:
            pxig.updateModelActiveBaseInfo(self.getInfo())
    # end def

    def hoverLeaveEvent(self, event):
        pxig = self.pre_xover_item_group
        if pxig.is_active:
            pxig.updateModelActiveBaseInfo(None)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def animate(self, item, property_name, duration, start_value, end_value):
        if item is not None:
            b_name = property_name.encode('ascii')
            anim = QPropertyAnimation(item.adapter, b_name)
            anim.setDuration(duration)
            anim.setStartValue(start_value)
            anim.setEndValue(end_value)
            anim.start()
            item.adapter.saveRef(property_name, anim)

    ### PUBLIC SUPPORT METHODS ###
    def setActive5p(self, is_active):
        phos = self.phos_item
        bond = self.line_5p
        if bond is None: return

        if is_active:
            # print("ENTERING", self.step_idx)
            # angle = 90 if self.is_fwd else -90
            angle = -90 if self.is_fwd else 90
            self.animate(phos, 'rotation', 300, 0, angle)
            bond.show()
            # if self.item_5p:
            #     self.item_5p.line_3p.hide()
            self.animate(bond, 'bondp2', 300, self._default_p2_5p, self._active_p2_5p)
        else:
            # print("LEAVING", self.step_idx)
            # QTimer.singleShot(300, bond.hide)
            self.animate(phos, 'rotation', 300, phos.rotation(), 0)
            if self.item_5p: QTimer.singleShot(300, self.item_5p.line_3p.show)
            self.animate(bond, 'bondp2', 300, self._active_p2_5p, self._default_p2_5p)
    # end def

    def setActive3p(self, is_active):
        phos = self.phos_item
        bond = self.line_3p
        if self.line_5p:
            self.line_5p.hide()
        if is_active:
            # angle = -90 if self.is_fwd else 90
            angle = 90 if self.is_fwd else -90
            self.animate(phos, 'rotation', 300, 0, angle)
            self.animate(bond, 'bondp2', 300, self._default_p2_3p, self._active_p2_3p)
            alpha = 42 if self.is_fwd else 64
            self.animate(bond, 'pen_alpha', 300, alpha, 180)
        else:
            self.animate(phos, 'rotation', 300, phos.rotation(), 0)
            self.animate(bond, 'bondp2', 300, bond.line().p2(), self._default_p2_3p)
            start_alpha = bond.pen().color().alpha()
            end_alpha = 42 if self.is_fwd else 64
            self.animate(bond, 'pen_alpha', 300, start_alpha, end_alpha)
    # end def

    def set5pItem(self, item_5p):
        self.item_5p = item_5p
        scenePos = item_5p.scenePos()
        p1 = QPointF(0, 0)
        p2 = self.mapFromScene(scenePos)
        self._default_p2_5p = p2
        self._default_line_5p = QLineF(p1,p2)
        self.line_5p.setLine(self._default_line_5p)
    # end def

    def set3pItem(self, item_3p):
        self.item_3p = item_3p
        scenePos = item_3p.scenePos()
        p1 = QPointF(0, 0)
        p2 = self.mapFromScene(scenePos)
        self._default_p2_3p = p2
        self._default_line_3p = QLineF(p1,p2)
        self.line_3p.setLine(self._default_line_3p)
    # end def

    def updateItemApperance(self, is_active, show_3p=True):
        if show_3p:
            self.setActive3p(is_active)
        else:
            self.setActive5p(is_active)
    # end def

    def destroy(self, scene):
        self.phos_item.adapter.resetAnimations()
        self.phos_item.adapter = None
        scene.removeItem(self.phos_item)
        self.phos_item = None
        self.line_3p.adapter.resetAnimations()
        self.line_3p.adapter = None
        scene.removeItem(self.line_3p)
        self.line_3p = None
        scene.removeItem(self)
# end class

class PreXoverItemGroup(QGraphicsEllipseItem):
    HUE_FACTOR = 1.6
    SPIRAL_FACTOR = 0.4

    def __init__(self, radius, rect, virtual_helix_item, is_active):
        super(PreXoverItemGroup, self).__init__(rect, virtual_helix_item)
        self._radius = radius
        self._rect = rect
        self.virtual_helix_item = virtual_helix_item
        self.model_part = mpart = virtual_helix_item.part()
        self.id_num = virtual_helix_item.idNum()
        self.is_active = is_active

        self.active_item = None
        self.active_wedge_gizmo = WedgeGizmo(radius, rect, self)
        self.fwd_prexover_items = {}
        self.rev_prexover_items = {}
        self._colors = self._getColors()
        self.addItems()
        self.setPen(getNoPen())
        z = styles.ZPXIGROUP + 10 if is_active else styles.ZPXIGROUP
        self.setZValue(z)
        self.setTransformOriginPoint(rect.center())
        bpr, tpr, eulerZ = virtual_helix_item.getProperty(['bases_per_repeat',
                                                'turns_per_repeat', 'eulerZ'])

        # twist_per_base = tpr*360./bpr
        # print('z:', z, mpart.baseWidth(), z/mpart.baseWidth(), twist_per_base)
        self.setRotation(-eulerZ) # add 180
    # end def

    ### ACCESSORS ###
    def eulerZAngle(self):
        return -self.virtual_helix_item.getProperty('eulerZ')
    # end def

    def getItem(self, is_fwd, step_idx):
        items = self.fwd_prexover_items if is_fwd else self.rev_prexover_items
        if step_idx in items:
            return items[step_idx]
        else:
            return None
    # end def

    def getItemIdx(self, is_fwd, idx):
        step_size = self.virtual_helix_item.getProperty('bases_per_repeat')
        return self.getItem(is_fwd, idx % step_size)
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def _getColors(self):
        step_size = self.virtual_helix_item.getProperty('bases_per_repeat')
        hue_scale = step_size*self.HUE_FACTOR
        return [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() for i in range(step_size)]
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def addItems(self):
        radius = self._radius
        step_size, bases_per_turn, tpb, mgroove = self.virtual_helix_item.getAngularProperties()
        iw = PXI_PP_ITEM_WIDTH
        ctr = self.mapToParent(self._rect).boundingRect().center()
        x = ctr.x() + radius - PXI_PP_ITEM_WIDTH
        y = ctr.y()
        tpb = -tpb # Qt +angle is Clockwise
        mgroove = -mgroove
        for i in range(step_size):
            inset = i*self.SPIRAL_FACTOR # spiral layout
            fwd = PreXoverItem(i, self._colors[i], self, is_fwd=True)
            rev = PreXoverItem(i, self._colors[-1 - i], self, is_fwd=False)
            fwd.setPos(x - inset, y)
            rev.setPos(x - inset, y)
            fwd.setTransformOriginPoint((-radius + iw + inset), 0)
            rev.setTransformOriginPoint((-radius + iw + inset), 0)
            fwd.setRotation(round((i*tpb) % 360, 3))
            rev.setRotation(round((i*tpb + mgroove) % 360, 3))
            fwd.setBondLineLength(inset + iw)
            rev.setBondLineLength(inset + iw)
            self.fwd_prexover_items[i] = fwd
            self.rev_prexover_items[i] = rev

        for i in range(step_size - 1):
            fwd, next_fwd = self.fwd_prexover_items[i], self.fwd_prexover_items[i + 1]
            j = (step_size - 1) - i
            rev, next_rev = self.rev_prexover_items[j], self.rev_prexover_items[j - 1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def remove(self):
        fpxis = self.fwd_prexover_items
        rpxis = self.rev_prexover_items
        scene = self.scene()
        for i in range(len(fpxis)):
            x = fpxis.pop(i)
            x.destroy(scene)
            x = rpxis.pop(i)
            x.destroy(scene)
        self.virtual_helix_item = None
        self.model_part = None
        scene = self.scene()
        scene.removeItem(self.active_wedge_gizmo)
        self.active_wedge_gizmo = None
        scene.removeItem(self)
    # end def

    def updateTurnsPerRepeat(self):
        step_size, bases_per_turn, tpb, mgroove = self.virtual_helix_item.getAngularProperties()
        mgroove = -mgroove
        tpb = -tpb
        fpxis = self.fwd_prexover_items
        rpxis = self.rev_prexover_items
        for i in range(step_size):
            fwd = self.fwd_prexover_items[i]
            rev = self.rev_prexover_items[i]
            fwd.setRotation(round((i*tpb) % 360, 3))
            rev.setRotation(round((i*tpb + mgroove) % 360, 3))
        for i in range(step_size - 1):
            fwd, next_fwd = fpxis[i], fpxis[i + 1]
            j = (step_size - 1) - i
            rev, next_rev = rpxis[j], rpxis[j - 1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def partCrossoverSpanAngle(self):
        return self.virtual_helix_item.partCrossoverSpanAngle()

    def updateModelActiveBaseInfo(self, pre_xover_info):
        """Notify model of pre_xover_item hover state."""
        self.model_part.setActiveBaseInfo(pre_xover_info)
    # end def
# end class



class WedgeGizmo(QGraphicsPathItem):
    def __init__(self, radius, rect, pre_xover_item_group):
        """ parent could be a PreXoverItemGroup or a VirtualHelixItem
        """
        super(WedgeGizmo, self).__init__(pre_xover_item_group)
        self._radius = radius
        self._rect = rect
        self.pre_xover_item_group = pre_xover_item_group
        self.setPen(getNoPen())
        self.setZValue(styles.ZWEDGEGIZMO - 10)
        self._last_params = None

    def showWedge(self, angle, color,
                    extended=False, rev_gradient=False, outline_only=False):
        self._last_params = (angle, color, extended, rev_gradient, outline_only)
        radius = self._radius
        span = self.pre_xover_item_group.partCrossoverSpanAngle() / 2
        radius_adjusted = radius + (_WEDGE_RECT_GAIN / 2)

        tip = QPointF(radius_adjusted, radius_adjusted)
        EXT = 1.35 if extended else 1.0

        # print("wtf", tip, pos)
        base_p2 = QPointF(1, 1)

        line0 = QLineF(tip, QPointF(base_p2))
        line1 = QLineF(tip, QPointF(base_p2))
        line2 = QLineF(tip, QPointF(base_p2))

        quad_scale = 1 + (.22*(span - 5) / 55) # lo+(hi-lo)*(val-min)/(max-min)
        line0.setLength(radius_adjusted * EXT*quad_scale) # for quadTo control point
        line1.setLength(radius_adjusted * EXT)
        line2.setLength(radius_adjusted * EXT)
        line0.setAngle(angle)
        line1.setAngle(angle - span)
        line2.setAngle(angle + span)

        path = QPainterPath()

        if outline_only:
            self.setPen(getPenObj(color, 0.5, alpha=128, capstyle=Qt.RoundCap))
            path.moveTo(line1.p2())
            path.quadTo(line0.p2(), line2.p2())
            self.setPath(path)
            self.show()
        else:
            gradient = QRadialGradient(tip, radius_adjusted * EXT)
            color1 = getColorObj(color, alpha=80)
            color2 = getColorObj(color, alpha=0)
            if rev_gradient:
                color1, color2 = color2, color1

            if extended:
                gradient.setColorAt(0, color1)
                gradient.setColorAt(radius_adjusted / (radius_adjusted * EXT), color1)
                gradient.setColorAt(radius_adjusted / (radius_adjusted * EXT) + 0.01, color2)
                gradient.setColorAt(1, color2)
            else:
                gradient.setColorAt(0, getColorObj(color, alpha=50))
            brush = QBrush(gradient)
            self.setBrush(brush)

            path.moveTo(line1.p1())
            path.lineTo(line1.p2())
            path.quadTo(line0.p2(), line2.p2())
            path.lineTo(line2.p1())
        self.setPath(path)
        self.show()
    # end def

    def updateWedgeAngle(self):
        self.showWedge(*self._last_params)
    # end def

    def deactivate(self):
        self.hide()
        self.setZValue(styles.ZWEDGEGIZMO - 10)
    # end def

    def showActive(self, pre_xover_item):
        pxi = pre_xover_item
        pos = pxi.pos()
        angle = -pxi.rotation()
        color = pxi.color
        self.setZValue(styles.ZWEDGEGIZMO)
        # self.showWedge(angle, color, span=5.0)
        if pxi.is_fwd:
            self.showWedge(angle, color, extended=True, rev_gradient=True)
            # self.showWedge(angle, color, extended=True)
        else:
            self.showWedge(angle, color, extended=True, rev_gradient=True)
            # self.showWedge(angle, color, extended=True, rev_gradient=True)
    # end def
# end class