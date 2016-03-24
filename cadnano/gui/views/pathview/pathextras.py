from itertools import product

from PyQt5.QtCore import QRectF, QLineF, Qt, QObject, QPointF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano.gui.palette import getNoPen, getPenObj
from cadnano.gui.palette import getBrushObj, getNoBrush
from . import pathstyles as styles


BASE_WIDTH = styles.PATH_BASE_WIDTH
BASE_RECT = QRectF(0, 0, BASE_WIDTH, BASE_WIDTH)


PHOS_ITEM_WIDTH = 0.25*BASE_WIDTH
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
        self.item = item
        self.animations = {}

    def __get_brushAlpha(self):
        return self.item.brush().color().alpha()

    def __set_brushAlpha(self, alpha):
        brush = QBrush(self.item.brush())
        color = QColor(brush.color())
        color.setAlpha(alpha)
        self.item.setBrush(QBrush(color))

    def __get_rotation(self):
        return self.item.rotation()

    def __set_rotation(self, angle):
        self.item.setRotation(angle)

    def saveRef(self, property_name, animation):
        self.animations[property_name] = animation

    def getRef(self, property_name):
        return self.animations.get(property_name)

    def destroy(self):
        self.item = None
        self.animations = None
        self.deleteLater()

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
        self._parent = parent
        self._part = parent.part()
        self.adapter = PropertyWrapperObject(self)
        self.setPen(getNoPen())
        self.hide()
    # end def

    def getPath(self):
        path = QPainterPath()
        # _step = self._parent.getProperty('bases_per_repeat')
        rect = QRectF(BASE_RECT)
        path.addRect(rect)
        return path
    # end def

    def resize(self):
        self.setPath(self.getPath())

    def update(self, is_fwd, step_idx, color):
        if self.path().isEmpty():
            self.setPath(self.getPath())
        self.setBrush(getBrushObj(color, alpha=128))
        x = BASE_WIDTH*step_idx
        y = -BASE_WIDTH if is_fwd else BASE_WIDTH*2
        self.setPos(x,y)
        self.show()
    # end def
# end class


class PreXoverLabel(QGraphicsSimpleTextItem):
    _XO_FONT = styles.XOVER_LABEL_FONT
    _XO_BOLD = styles.XOVER_LABEL_FONT_BOLD
    _FM = QFontMetrics(_XO_FONT)

    def __init__(self, is_fwd, color, pre_xover_item):
        super(QGraphicsSimpleTextItem, self).__init__(pre_xover_item)
        self._txt = ''
        self._is_fwd = is_fwd
        self._color = color
        self._pre_xover_item = pre_xover_item
        self._tbr = None
        self._outline = QGraphicsRectItem(self)
        self.setFont(self._XO_FONT)
        self.setBrush(getBrushObj('#666666'))
    # end def

    def setTextAndStyle(self, text, outline=False):
        self._txt = text
        str_txt = str(text)
        self._tbr = tBR = self._FM.tightBoundingRect(str_txt)
        half_label_H = tBR.height() / 2.0
        half_label_W = tBR.width() / 2.0

        labelX = BASE_WIDTH/2.0 - half_label_W #
        if str_txt == '1':  # adjust for the number one
            labelX -= tBR.width()

        labelY = half_label_H if self._is_fwd else (BASE_WIDTH - tBR.height())/2

        self.setPos(labelX, labelY)
        self.setText(str_txt)

        if outline:
            self.setFont(self._XO_BOLD)
            self.setBrush(getBrushObj('#ff0000'))
        else:
            self.setFont(self._XO_FONT)
            self.setBrush(getBrushObj('#666666'))

        if outline:
            r = QRectF(self._tbr).adjusted(-half_label_W, 0,
                                            half_label_W, half_label_H)
            self._outline.setRect(r)
            self._outline.setPen(getPenObj('#ff0000', 0.25))
            self._outline.setY(2*half_label_H)
            self._outline.show()
        else:
            self._outline.hide()
    # end def

# end class

ACTIVE_ALPHA = 128
PROX_ALPHA = 64

class PreXoverItem(QGraphicsRectItem):
    """ A PreXoverItem exists between a single 'from' VirtualHelixItem index
    and zero or more 'to' VirtualHelixItem Indices
    """
    def __init__(self, from_virtual_helix_item, is_fwd, from_index,
                to_vh_id_num, prexoveritemgroup, color):
        super(QGraphicsRectItem, self).__init__(BASE_RECT, from_virtual_helix_item)
        self._from_vh_item = from_virtual_helix_item
        self._id_num = from_virtual_helix_item.idNum()
        self.idx = from_index
        self.prexoveritemgroup = prexoveritemgroup
        self._to_vh_id_num = to_vh_id_num
        self._color = color
        self._is_fwd = is_fwd
        # self._animations = []
        self.adapter = PropertyWrapperObject(self)
        self._bond_item = QGraphicsPathItem(self)
        self._bond_item.hide()
        self._label_txt = lbt = None if to_vh_id_num is None else str(to_vh_id_num)
        self._label = PreXoverLabel(is_fwd, color, self)
        self.setLabel(text=lbt)
        self.setPen(getNoPen())

        if is_fwd:
            phos = Triangle(FWDPHOS_PP, self)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(0.5*BASE_WIDTH, BASE_WIDTH)
            phos.setPen(getNoPen())
            phos.setBrush(getBrushObj(color))
            self._bond_item.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH))
            self.setPos(from_index*BASE_WIDTH,-BASE_WIDTH)
        else:
            phos = Triangle(REVPHOS_PP, self)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(0.5*BASE_WIDTH, 0)
            phos.setPen(getPenObj(color, 0.25))
            phos.setBrush(getNoBrush())
            self._bond_item.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH,
                                    penstyle=Qt.DotLine, capstyle=Qt.RoundCap))
            self.setPos(from_index*BASE_WIDTH, 2*BASE_WIDTH)
        self._phos_item = phos

        self.setInstantActive(False)
    # end def

    def getInfo(self):
        """
        Returns:
            Tuple: (from_id_num, is_fwd, from_index, to_vh_id_num)
        """
        return (self._id_num, self._is_fwd, self.idx, self._to_vh_id_num)

    ### ACCESSORS ###
    def color(self):
        return self._color

    def remove(self):
        scene = self.scene()
        self.adapter.destroy()
        if scene:
            scene.removeItem(self._label)
            self._label = None
            scene.removeItem(self._phos_item)
            self._phos_item = None
            scene.removeItem(self._bond_item)
            self._bond_item = None
            scene.removeItem(self)
    # end def

    def isFwd(self):
        return self._is_fwd

    def absoluteIdx(self):
        vhi = self._from_vh_item
        # id_num = vhi.idNum()
        x, y, _z = vhi.part().getCoordinate(self._id_num, 0)
        return self.baseIdx() + (_z / BASE_WIDTH)

    def window(self):
        return self._parent.window()

    ### EVENT HANDLERS ###

    ### PUBLIC SUPPORT METHODS ###
    def setLabel(self, text=None, outline=False):
        if text:
            self._label.setTextAndStyle(text=text, outline=outline)
            self._label.show()
        else:
            self._label.hide()
    #end def

    def animate(self, item, property_name, duration, start_value, end_value):
        b_name = property_name.encode('ascii')
        anim = item.adapter.getRef(property_name)
        if anim is None:
            anim = QPropertyAnimation(item.adapter, b_name)
            item.adapter.saveRef(property_name, anim)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()
    # end def

    def setInstantActive(self, is_active):
        if is_active:
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 1, 0, 128) # overwrite running anim
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
        else:
            inactive_alpha = PROX_ALPHA if self._to_vh_id_num is not None else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
    # end def
# end class

class ActivePreXoverItem(PreXoverItem):
    def __init__(self, *args):
        super(ActivePreXoverItem, self).__init__(*args)
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsFocusable)
    # end def

    def hoverEnterEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)
        self.prexoveritemgroup.updateModelActiveBaseInfo(self.getInfo())
        self.setInstantActive(True)
    # end def

    def hoverLeaveEvent(self, event):
        self.prexoveritemgroup.updateModelActiveBaseInfo(None)
        self.setInstantActive(False)
        self.clearFocus()
    # end def

    def keyPressEvent(self, event):
        self.prexoveritemgroup.handlePreXoverKeyPress(event.key())
    # end def
# end class

class NeighborPreXoverItem(PreXoverItem):
    def activateNeighbor(self, active_prexoveritem, shortcut=None):
        """ To be called with whatever the active_prexoveritem
        is for the parts `active_base`
        """
        p1 = self._phos_item.scenePos()
        p2 = active_pos = active_prexoveritem._phos_item.scenePos()
        scale = 3
        delta1 = -BASE_WIDTH*scale if self._is_fwd else BASE_WIDTH*scale
        delta2 = BASE_WIDTH*scale if active_prexoveritem.isFwd() else -BASE_WIDTH*scale
        c1 = self.mapFromScene(QPointF(p1.x(), p1.y() + delta1))
        c2 = self.mapFromScene(QPointF(p2.x(), p2.y() - delta2))
        pp = QPainterPath()
        pp.moveTo(self._phos_item.pos())
        pp.cubicTo(c1, c2, self._bond_item.mapFromScene(p2))
        self._bond_item.setPath(pp)
        self._bond_item.show()

        alpha = 32
        idx, active_idx = self.idx, active_prexoveritem.idx
        if self._is_fwd != active_prexoveritem.isFwd():
            if idx == active_idx:
                alpha = 255
        elif idx == active_idx + 1:
            alpha = 255
        elif idx == active_idx - 1:
            alpha = 255

        inactive_alpha = PROX_ALPHA if self._to_vh_id_num is not None else 0
        self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
        self.animate(self, 'brush_alpha', 500, inactive_alpha, alpha)
        self.animate(self._phos_item, 'rotation', 500, 0, -90)
        self.setLabel(text=shortcut, outline=True)
    # end def

    def deactivateNeighbor(self):
        inactive_alpha = PROX_ALPHA if self._to_vh_id_num is not None else 0
        self.setBrush(getBrushObj(self._color, alpha=128))
        self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
        self.animate(self._phos_item, 'rotation', 500, -90, 0)
        self._bond_item.hide()
        self.setLabel(text=self._label_txt)
    # end def
# end class

