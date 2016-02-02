from itertools import product

from PyQt5.QtCore import QRectF, QLineF, Qt, QObject, QPointF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano.gui.palette import getNoPen, getPenObj
from cadnano.gui.palette import getBrushObj, getNoBrush
from . import pathstyles as styles


_BASE_WIDTH = styles.PATH_BASE_WIDTH
_BASE_RECT = QRectF(0, 0, _BASE_WIDTH, _BASE_WIDTH)


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
        self._parent = parent
        self._part = parent.part()
        self.adapter = PropertyWrapperObject(self)
        self.setPen(getNoPen())
        self.hide()
    # end def

    def getPath(self):
        path = QPainterPath()
        # _step = self._parent.getProperty('bases_per_repeat')
        rect = QRectF(_BASE_RECT)
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

        labelX = _BASE_WIDTH/2.0 - half_label_W #
        if str_txt == '1':  # adjust for the number one
            labelX -= tBR.width()

        labelY = half_label_H if self._is_fwd else (_BASE_WIDTH - tBR.height())/2

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
    def __init__(self,  from_virtual_helix_item, from_index,
                        color, is_fwd=True):
        super(QGraphicsRectItem, self).__init__(_BASE_RECT, from_virtual_helix_item)
        self._from_vh_item = from_virtual_helix_item
        self._from_idx = from_index
        self._to_vh_item = None
        self._to_idxs = None
        self._color = color
        self._is_fwd = is_fwd
        self._animations = []
        self.adapter = PropertyWrapperObject(self)
        self._bond_item = QGraphicsPathItem(self)
        self._bond_item.hide()
        self._label_txt = None
        self._label = PreXoverLabel(is_fwd, color, self)
        self._label.hide()

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
            self._bond_item.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH))
        else:
            phos = Triangle(REVPHOS_PP, self)
            phos.setTransformOriginPoint(0, phos.boundingRect().center().y())
            phos.setPos(_half_bw, 0)
            phos.setPen(getPenObj(color, 0.25))
            phos.setBrush(getNoBrush())
            self._bond_item.setPen(getPenObj(color, styles.PREXOVER_STROKE_WIDTH,
                                    penstyle=Qt.DotLine, capstyle=Qt.RoundCap))
        self._phos_item = phos
    # end def

    ### ACCESSORS ###
    def color(self):
        return self._color

    def isFwd(self):
        return self._is_fwd

    def absoluteIdx(self):
        vhi = self._from_vh_item
        id_num = vhi.idNum()
        x, y, _z = vhi.part().getCoordinate(id_num, 0)
        return self.baseIdx() + (_z / _BASE_WIDTH)

    def baseIdx(self):
        return self._step + self._step_idx

    def stepIdx(self):
        return self._step_idx

    def window(self):
        return self._parent.window()

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
            self.animate(self, 'brush_alpha', 1, 0, 128) # overwrite running anim
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
        else:
            inactive_alpha = PROX_ALPHA if self._to_vh_item is not None else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
    # end def

    def setProximal(self, to_virtual_helix_item, to_index, colliding=False):
        if to_virtual_helix_item is not None:
            self._to_vh_item = to_virtual_helix_item
            self._to_idx = to_index
            color = '#cc0000' if colliding else self._color
            self.setBrush(getBrushObj(color, alpha=PROX_ALPHA))
            self._label_txt = id_num
            self.setLabel(id_num)
            # self.animate(self, 'brush_alpha', 1, 0, PROX_ALPHA) # overwrite running anim
        else:
            self._to_vh_item = None
            self._to_idx = None
            self.setBrush(getBrushObj(self._color, alpha=0))
            self._label_txt = None
            self.setLabel()
            # self.animate(self, 'brush_alpha', 1000, PROX_ALPHA, 0)
    # end def

    def setActiveNeighbor(self, active_item, shortcut=None):
        if active_item is None:
            inactive_alpha = PROX_ALPHA if self._to_vh_item is not None else 0
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
            self._bond_item.hide()
            self.setLabel(text=self._label_txt)
        else:
            p1 = self._phos_item.scenePos()
            p2 = active_pos = active_item._phos_item.scenePos()
            scale = 3
            delta1 = -_BASE_WIDTH*scale if self._is_fwd else _BASE_WIDTH*scale
            delta2 = _BASE_WIDTH*scale if active_item.isFwd() else -_BASE_WIDTH*scale
            c1 = self.mapFromScene(QPointF(p1.x(), p1.y() + delta1))
            c2 = self.mapFromScene(QPointF(p2.x(), p2.y() - delta2))
            pp = QPainterPath()
            pp.moveTo(self._phos_item.pos())
            pp.cubicTo(c1, c2, self._bond_item.mapFromScene(p2))
            self._bond_item.setPath(pp)
            self._bond_item.show()

            alpha = 32
            abs_idx, active_item_abs_idx = self.absoluteIdx(), active_item.absoluteIdx()
            if self._is_fwd != active_item.isFwd():
                if abs_idx == active_item_abs_idx:
                    alpha = 255
            elif abs_idx == active_item_abs_idx + 1:
                alpha = 255
            elif abs_idx == active_item_abs_idx - 1:
                alpha = 255

            inactive_alpha = PROX_ALPHA if self._to_vh_item is not None else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 500, inactive_alpha, alpha)
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
            self.setLabel(text=shortcut, outline=True)
    # end def

    def setLabel(self, text=None, outline=False):
        if text:
            self._label.setTextAndStyle(text=text, outline=outline)
            self._label.show()
        else:
            self._label.hide()

    def animate(self, item, property_name, duration, start_value, end_value):
        b_name = property_name.encode('ascii')
        anim = QPropertyAnimation(item.adapter, b_name)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()
        item.adapter.saveRef(property_name, anim)
    # end def
# end class


class PreXoverItemGroup(QGraphicsRectItem):
    HUE_FACTOR = 1.6

    def __init__(self, virtualhelixitem):
        super(QGraphicsRectItem, self).__init__(virtual_helix_item)
        self._parent = virtual_helix_item
        self.setPen(getNoPen())
        self._colors = []
        self._fwd_pxo_items = {}
        self._rev_pxo_items = {}
        self._active_items = []
        self.updateBasesPerRepeat()
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._parent.window()

    def virtualHelixItem(self):
        return self.parentItem():
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def addRepeats(self, n=None):
        """
        Adds n*bases_per_repeat PreXoverItems to fwd and rev groups.
        If n is None, get the value from the parent VHI.
        """
        step_size, num_repeats = self._parent.getProperty(['bases_per_repeat', 'repeats'])
        if n is None:
            n = num_repeats
            start_idx = 0
        else:
            start_idx = len(self._fwd_pxo_items)
        end_idx = start_idx + n*step_size

        iw, half_iw = PHOS_ITEM_WIDTH, 0.5*PHOS_ITEM_WIDTH
        bw, half_bw, bw2 = _BASE_WIDTH, 0.5*_BASE_WIDTH, 2*_BASE_WIDTH
        for i in range(start_idx, end_idx, step_size):
            for j in range(step_size):
                fwd = PreXoverItem(i, j, self._colors[j], is_fwd=True, parent=self)
                rev = PreXoverItem(i, j, self._colors[-1 - j], is_fwd=False, parent=self)
                fwd.setPos((i + j)*bw, -bw)
                rev.setPos((i + j)*bw, bw2)
                self._fwd_pxo_items[i + j] = fwd
                self._rev_pxo_items[i + j] = rev
            # end for
        # end for
        canvas_size = self._parent.maxLength()
        self.setRect(0, 0, bw*canvas_size, bw2)
    # end def

    def removeRepeats(self):
        """
        remove all PreXoverItems from fwd and rev groups.
        """
        for i in range(len(self._fwd_pxo_items)):
            self.scene().removeItem(self._fwd_pxo_items.pop())
            self.scene().removeItem(self._rev_pxo_items.pop())
    # end def

    def updateBasesPerRepeat(self):
        """Recreates colors, all vhi"""
        step_size = self._parent.getProperty('bases_per_repeat')
        hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        self.removeRepeats()
        self.addRepeats()
    # end def

    def updateTurnsPerRepeat(self):
        pass
    # end def

    def part(self):
        return self._parent.part()

    ### PUBLIC SUPPORT METHODS ###
    def getItem(self, is_fwd, idx):
        if is_fwd:
            if idx in self._fwd_pxo_items:
                return self._fwd_pxo_items[idx]
        else:
            if idx in self._rev_pxo_items:
                return self._rev_pxo_items[idx]
        return None
    # end def

    def resize(self):
        old_max = len(self._fwd_pxo_items)
        new_max = self._parent.maxLength()
        if new_max == old_max:
            return
        elif new_max > old_max:
            bpr = self._parent.getProperty('bases_per_repeat')
            self._add_pxitems(old_max + 1, new_max, bpr)
        else:
            self._rm_pxitems_after(new_max)
        self._max_base = new_max
    # end def

    def setActiveNeighbors(self, active_item, fwd_idxs, rev_idxs):
        # active_item is a PreXoverItem
        if active_item:
            active_absolute_idx = active_item.absoluteIdx()
            bpr = self._parent.getProperty('bases_per_repeat')
            cutoff = bpr / 2
            active_idx = active_item.baseIdx()
            step_idxs = range(0, self._parent.maxLength(), bpr)
            k = 0
            pre_xovers = {}
            for i, j in product(fwd_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                delta = item.absoluteIdx() - active_absolute_idx
                if abs(delta) < cutoff and k < 10:
                    item.setActiveNeighbor(active_item, shortcut=str(k))
                    pre_xovers[k] = item.name()
                    k += 1
                    self._active_items.append(item)
            for i, j in product(rev_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._rev_pxo_items[i+j]
                delta = item.absoluteIdx() - active_absolute_idx
                if abs(delta) < cutoff and k < 10:
                    item.setActiveNeighbor(active_item, shortcut=str(k))
                    pre_xovers[k] = item.name()
                    k += 1
                    self._active_items.append(item)
            self._parent.partItem().setKeyPressDict(pre_xovers)
        else:
            self._parent.partItem().setKeyPressDict({})
            while self._active_items:
                self._active_items.pop().setActiveNeighbor(None)
    # end def

    def setProximalItems(self, prox_groups):
        max_length = self._parent.maxLength()
        inactive_fwd = set(range(max_length))
        inactive_rev = set(range(max_length))
        bpr = self._parent.getProperty('bases_per_repeat')
        step_idxs = range(0, max_length, bpr)
        id_
        for this_idx, neighbor_id, idxs in fwd_hits:
            item = self._fwd_pxo_items[this_idx]
            item.setProximal(True, id_num=neighbor_id)


        for id_num, fwd_idxs, rev_idxs in prox_groups:

            for i, j in product(fwd_idxs, step_idxs):
                idx = i + j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                item.setProximal(True, id_num=id_num, colliding=is_colliding)
                if idx in inactive_fwd:
                    inactive_fwd.remove(idx)
            for i, j in product(rev_idxs, step_idxs):
                idx = i + j
                if not idx in self._rev_pxo_items:
                    continue
                item = self._rev_pxo_items[i + j]
                item.setProximal(True, id_num=id_num, colliding=is_colliding)
                if idx in inactive_rev:
                    inactive_rev.remove(idx)
        for idx in list(inactive_fwd):
            self._fwd_pxo_items[idx].setProximal(False)
        for idx in list(inactive_rev):
            self._rev_pxo_items[idx].setProximal(False)


    def updatePositionsAfterRotation(self, angle):
        bw = _BASE_WIDTH
        part = self._parent.part()
        canvas_size = self._parent.maxLength()
        bpr = self._parent.getProperty('bases_per_repeat')
        xdelta = angle / 360. * bw*bpr
        for i, item in self._fwd_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
        for i, item in self._rev_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
    # end def

    def updateModelActivePhos(self, pre_xover_item):
        """Notify model of pre_xover_item hover state."""
        vhi = self._parent
        model_part = vhi.part()
        id_num = self._parent.idNum()
        if pre_xover_item is None:
            model_part.setProperty('active_phos', None)
            return
        vh_name, vh_angle  = vhi.getProperty(['name', 'eulerZ'])
        idx = pre_xover_item.baseIdx() # (f|r).step_idx
        is_fwd = 'fwd' if pre_xover_item.isFwd() else 'rev'
        value = '%s.%s.%d' % (vh_name, is_fwd, idx)
        model_part.setProperty('active_phos', value)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        while self._active_items:
            self._active_items.pop().setActive(False)
        if new_active_item:
            new_active_item.setActive(True)
            self._active_items.append(new_active_item)
    # end def

