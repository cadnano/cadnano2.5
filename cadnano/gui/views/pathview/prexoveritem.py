
from PyQt5.QtCore import QObject, QPointF, QRectF, Qt
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QPainterPath
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QUndoCommand, QGraphicsRectItem

from cadnano.enum import StrandType
from cadnano.gui.palette import getPenObj, getBrushObj, getSolidBrush
from . import pathstyles as styles


_BASE_WIDTH = styles.PATH_BASE_WIDTH
_BASE_RECT = QRectF(0,0,_BASE_WIDTH,_BASE_WIDTH)
PHOS_ITEM_WIDTH = 0.25*_BASE_WIDTH
TRIANGLE = QPolygonF()
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.append(QPointF(0.75 * PHOS_ITEM_WIDTH, 0.5 * PHOS_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, PHOS_ITEM_WIDTH))
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.translate(0, -0.5*PHOS_ITEM_WIDTH)
T180 = QTransform()
T180.rotate(-180)
FWDPHOS_PP, REVPHOS_PP = QPainterPath(), QPainterPath()
FWDPHOS_PP.addPolygon(TRIANGLE)
REVPHOS_PP.addPolygon(T180.map(TRIANGLE))


class PropertyWrapperObject(QObject):
    def __init__(self, item):
        super(PropertyWrapperObject, self).__init__()
        self._item = item
        self._animations = {}

    def __get_brushAlpha(self):
        return self._item.brush().color().alpha()
 
    def __set_brushAlpha(self, alpha):
        brush = QBrush(self._item.brush())
        color = QColor(brush.color())
        color.setAlpha(alpha)
        self._item.setBrush(QBrush(color))

    def __get_rotation(self):
        return self._item.rotation()

    def __set_rotation(self, angle):
        self._item.setRotation(angle)

    def saveRef(self, property_name, animation):
        self._animations[property_name] = animation

    brush_alpha = pyqtProperty(int, __get_brushAlpha, __set_brushAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class


class Triangle(QGraphicsPathItem):
    def __init__(self, painter_path, parent=None):
        super(QGraphicsPathItem, self).__init__(painter_path, parent)
        self.adapter = PropertyWrapperObject(self)
    # end def
# end class


class ActivePhosItem(QGraphicsPathItem):
    def __init__(self, parent=None):
        super(QGraphicsPathItem, self).__init__(parent)
        self._part = parent.part()
        self.adapter = PropertyWrapperObject(self)
        self.setPen(getNoPen())
        self.hide()
    # end def

    def getPath(self):
        path = QPainterPath()
        _step = self._part.stepSize()
        max_idx = self._part.maxBaseIdx()
        for i in range(0, self._part.maxBaseIdx()+1, _step):
            rect = QRectF(_BASE_RECT)
            rect.translate(_BASE_WIDTH*i, 0)
            path.addRect(rect)
        return path
    # end def

    def resize(self):
        self.setPath(self.getPath())

    def update(self, is_fwd, step_idx, color):
        if self.path().isEmpty():
            self.setPath(self.getPath())
        self.setBrush(getBrushObj(color, alpha=128))
        x = _BASE_WIDTH*step_idx
        y = -_BASE_WIDTH if is_fwd else _BASE_WIDTH*2
        self.setPos(x,y)
        self.show()
    # end def
# end class


class PreXoverItem(QGraphicsRectItem):
    def __init__(self, step, step_idx, color, is_fwd=True, parent=None):
        super(QGraphicsRectItem, self).__init__(_BASE_RECT, parent)
        self._step = step
        self._step_idx = step_idx
        self._color = color
        self._is_fwd = is_fwd
        self._parent = parent
        self._animations = []
        self.adapter = PropertyWrapperObject(self)
        self._bond_item = QGraphicsPathItem(self)
        self._bond_item.hide()
        self.setPen(getNoPen())

        self.setAcceptHoverEvents(True)

        _half_bw, _bw = 0.5*_BASE_WIDTH, _BASE_WIDTH
        _half_iw, _iw = 0.5*PHOS_ITEM_WIDTH, PHOS_ITEM_WIDTH

        if is_fwd:
            phos = Triangle(FWDPHOS_PP, self)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(_half_bw, _bw)
            phos.setPen(getNoPen())
            phos.setBrush(getBrushObj(color))
            self._bond_item.setPen(getPenObj(color, 1))
        else:
            phos = Triangle(REVPHOS_PP, self)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(_half_bw, 0)
            phos.setPen(getPenObj(color, 0.5))
            phos.setBrush(getNoBrush())
            self._bond_item.setPen(getPenObj(color, 1, penstyle=Qt.DashLine, capstyle=Qt.RoundCap))
        self._phos_item = phos
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        vh_name = self._parent._vh_name()
        fwd_str = 'fwd' if self._is_fwd else 'rev'
        idx = self._step_idx
        angle = self.facing_angle()
        return "<%s>(%s.%s[%d].%d)" % (cls_name, vh_name, fwd_str, idx, angle)
    # end def

    ### ACCESSORS ###
    def color(self):
        return self._color

    def facing_angle(self):
        return (self._parent._vh_angle() + self.rotation()) % 360

    def is_fwd(self):
        return self._is_fwd

    def name(self):
        return "%s.%d" % ("r" if self._is_fwd else "f", self._step_idx)

    def base_idx(self):
        return self._step+self._step_idx

    def step_idx(self):
        return self._step_idx

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        self._parent.updateModelActivePhos(self)
        self.setActive(True)
    # end def

    def hoverLeaveEvent(self, event):
        self._parent.updateModelActivePhos(None)
        self.setActive(False)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def setActive(self, is_active):
        if is_active:
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 500, 0, 128)
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
            # self._phos_item.setRotation(-90)
        else:
            self.setBrush(getBrushObj(self._color, alpha=0))
            self.animate(self, 'brush_alpha', 1000, 128, 0)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
            # self._phos_item.setRotation(0)
    # end def

    def setActiveNeighbor(self, is_active, active_item=None):
        if is_active:
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 500, 0, 128)
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
            
            p1 = self._phos_item.scenePos()
            p2 = active_pos = active_item._phos_item.scenePos()
            # c1 = self.mapFromScene(QPointF(abs(p1.x()-p2.x()), abs(p1.y()-p2.y())))
            scale = 3
            delta1 = -_BASE_WIDTH*scale if self._is_fwd else _BASE_WIDTH*scale
            delta2 = _BASE_WIDTH*scale if active_item.is_fwd() else -_BASE_WIDTH*scale
            c1 = self.mapFromScene(QPointF(p1.x(), p1.y()+delta1))
            c2 = self.mapFromScene(QPointF(p2.x(), p2.y()-delta2))
            
            pp = QPainterPath()
            pp.moveTo(self._phos_item.pos())
            pp.cubicTo(c1,c2,self._bond_item.mapFromScene(p2))
            # pp.quadTo(c1, self._bond_item.mapFromScene(p2))
            # p2 = self._bond_item.mapFromScene(active_pos)
            self._bond_item.setPath(pp)
            self._bond_item.show()
            # self._phos_item.setRotation(-90)
        else:
            self.setBrush(getBrushObj(self._color, alpha=0))
            self.animate(self, 'brush_alpha', 1000, 128, 0)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
            self._bond_item.hide()
            # self._phos_item.setRotation(0)
    # end def

    def animate(self, item, property_name, duration, start_value, end_value):
        b_name = property_name.encode('ascii')
        anim = QPropertyAnimation(item.adapter, b_name)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()
        item.adapter.saveRef(property_name, anim)
    # end def


    ### DRAWING METHODS ###
    def remove(self):
        scene = self.scene()
        if scene:
            # scene.removeItem(self._label)
            scene.removeItem(self)
        # self._label = None
        # self._clickArea = None
        # self._from_vh_item = None
        # self._to_vh_item = None
    # end def
# end class
