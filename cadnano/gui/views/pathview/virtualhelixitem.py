from math import floor
from itertools import product

from PyQt5.QtCore import QRectF, QLineF, Qt, QObject, QPointF, pyqtSignal
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano import util
from cadnano.enum import StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.palette import getColorObj
from cadnano.gui.palette import newPenObj, getNoPen, getPenObj
from cadnano.gui.palette import getBrushObj, getNoBrush
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from .strand.stranditem import StrandItem
from .virtualhelixhandleitem import VirtualHelixHandleItem
from . import pathstyles as styles


_BASE_WIDTH = styles.PATH_BASE_WIDTH
_BASE_RECT = QRectF(0,0,_BASE_WIDTH,_BASE_WIDTH)
_VH_XOFFSET = styles.VH_XOFFSET

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
        _step = self._parent._bases_per_repeat
        # max_idx = self._part.maxBaseIdx()
        # for i in range(0, self._part.maxBaseIdx()+1, _step):
        #     rect = QRectF(_BASE_RECT)
        #     rect.translate(_BASE_WIDTH*i, 0)
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

    def __init__(self, idx, is_fwd, color, parent=None):
        super(QGraphicsSimpleTextItem, self).__init__(parent)
        self._txt = ''
        self._idx = idx
        self._is_fwd = is_fwd
        self._color = color
        self._parent = parent
        self._tbr = None
        self._outline = QGraphicsRectItem(self)
        self.setFont(self._XO_FONT)
        self.setBrush(getBrushObj('#666666'))
    # end def

    def setTextAndStyle(self, text, outline=False):
        self._txt = text
        str_txt = str(text)
        self._tbr = tBR = self._FM.tightBoundingRect(str_txt)
        half_label_H = tBR.height()/2.0
        half_label_W = tBR.width()/2.0

        labelX = _BASE_WIDTH/2.0 - half_label_W #
        if text == 1:  # adjust for the number one
            labelX -= half_label_W/2.0

        if self._is_fwd:
            labelY = half_label_H
        else:
            labelY = 2*half_label_H

        self.setPos(labelX, labelY)
        self.setText(str_txt)

        if outline:
            self.setFont(self._XO_BOLD)
            self.setBrush(getBrushObj('#ff0000'))
        else:
            self.setFont(self._XO_FONT)
            self.setBrush(getBrushObj('#666666'))

        if outline:
            r = QRectF(self._tbr).adjusted(-half_label_W,0,half_label_W,half_label_H)
            self._outline.setRect(r)
            self._outline.setPen(getPenObj('#ff0000', 0.5))
            self._outline.setY(2*half_label_H)
            self._outline.show()
        else:
            self._outline.hide()
    # end def

# end class

ACTIVE_ALPHA = 128
PROX_ALPHA = 64

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
        self._label_txt = None
        self._label = PreXoverLabel(step_idx, is_fwd, color, self)
        self._label.hide()
        self._has_neighbor = False

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
        _twist = float(self._parent._vh_twist_per_base())
        if self._is_fwd:
            angle = round(((self._step_idx+(self._parent._vh_Z() / _BASE_WIDTH))*_twist)%360, 3)
        else:
            _groove = self._parent.part().minorGrooveAngle()
            angle = round(((self._step_idx+(self._parent._vh_Z() / _BASE_WIDTH))*_twist+_groove)%360, 3)
        return (self._parent._vh_angle() + angle) % 360

    def is_fwd(self):
        return self._is_fwd

    def virtualHelix(self):
        return self._parent._vh()

    def name(self):
        vh_name = self._parent._vh_name()
        fwd_str = 'fwd' if self._is_fwd else 'rev'
        idx = self.base_idx()
        angle = self.facing_angle()
        return '%s.%s.%d.%d' % (vh_name, fwd_str, idx, angle)

    def absolute_idx(self):
        return self.base_idx() + (self._parent._vh_Z() / _BASE_WIDTH)

    def base_idx(self):
        return self._step+self._step_idx

    def step_idx(self):
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
    def hasNeighbor(self):
        pass

    def setActive(self, is_active):
        if is_active:
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 1, 0, 128) # overwrite running anim
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
        else:
            inactive_alpha = PROX_ALPHA if self._has_neighbor else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
    # end def

    def setProximal(self, has_neighbor, vh_num=None, colliding=False):
        if has_neighbor:
            self._has_neighbor = True
            color = '#cc0000' if colliding else self._color
            self.setBrush(getBrushObj(color, alpha=PROX_ALPHA))
            self._label_txt = vh_num
            self.setLabel(vh_num)
            # self.animate(self, 'brush_alpha', 1, 0, PROX_ALPHA) # overwrite running anim
        else:
            self._has_neighbor = False
            self.setBrush(getBrushObj(self._color, alpha=0))
            self._label_txt = None
            self.setLabel()
            # self.animate(self, 'brush_alpha', 1000, PROX_ALPHA, 0)
    # end def

    def setActiveNeighbor(self, is_active, shortcut=None, active_item=None):
        if is_active:
            p1 = self._phos_item.scenePos()
            p2 = active_pos = active_item._phos_item.scenePos()
            scale = 3
            delta1 = -_BASE_WIDTH*scale if self._is_fwd else _BASE_WIDTH*scale
            delta2 = _BASE_WIDTH*scale if active_item.is_fwd() else -_BASE_WIDTH*scale
            c1 = self.mapFromScene(QPointF(p1.x(), p1.y()+delta1))
            c2 = self.mapFromScene(QPointF(p2.x(), p2.y()-delta2))
            pp = QPainterPath()
            pp.moveTo(self._phos_item.pos())
            pp.cubicTo(c1, c2, self._bond_item.mapFromScene(p2))
            self._bond_item.setPath(pp)
            self._bond_item.show()

            alpha = 32
            if self._is_fwd != active_item.is_fwd():
                if self.absolute_idx() == active_item.absolute_idx():
                    alpha = 255
            elif self.absolute_idx() == active_item.absolute_idx()+1:
                alpha = 255
            elif self.absolute_idx() == active_item.absolute_idx()-1:
                alpha = 255

            inactive_alpha = PROX_ALPHA if self._has_neighbor else 0
            self.setBrush(getBrushObj(self._color, alpha=inactive_alpha))
            self.animate(self, 'brush_alpha', 500, inactive_alpha, alpha)
            self.animate(self._phos_item, 'rotation', 500, 0, -90)
            self.setLabel(text=shortcut, outline=True)

        else:
            inactive_alpha = PROX_ALPHA if self._has_neighbor else 0
            self.setBrush(getBrushObj(self._color, alpha=128))
            self.animate(self, 'brush_alpha', 1000, 128, inactive_alpha)
            self.animate(self._phos_item, 'rotation', 500, -90, 0)
            self._bond_item.hide()
            self.setLabel(text=self._label_txt)
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

    def __init__(self, parent=None):
        super(QGraphicsRectItem, self).__init__(parent)
        self._parent = parent
        self.setPen(getNoPen())
        self._colors = []
        self._fwd_pxo_items = {}
        self._rev_pxo_items = {}
        self._active_items = []
        self._prox_items = []
        self.updateBasesPerRepeat()
    # end def

    ### ACCESSORS ###
    def window(self):
        return self._parent.window()

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def addRepeats(self, n=None):
        """
        Adds n*bases_per_repeat PreXoverItems to fwd and rev groups.
        If n is None, get the value from the parent VHI.
        """
        step_size = self._parent._bases_per_repeat
        if n is None:
            n = self._parent._repeats
            start_idx = 0
        else:
            start_idx = len(self._fwd_pxo_items)
        end_idx = start_idx + n*step_size

        iw, half_iw = PHOS_ITEM_WIDTH, 0.5*PHOS_ITEM_WIDTH
        bw, half_bw, bw2 = _BASE_WIDTH, 0.5*_BASE_WIDTH, 2*_BASE_WIDTH
        for i in range(start_idx, end_idx, step_size):
            for j in range(step_size):
                fwd = PreXoverItem(i, j, self._colors[j], is_fwd=True, parent=self)
                rev = PreXoverItem(i, j, self._colors[-1-j], is_fwd=False, parent=self)
                fwd.setPos((i+j)*bw,-bw)
                rev.setPos((i+j)*bw,bw2)
                self._fwd_pxo_items[i+j] = fwd
                self._rev_pxo_items[i+j] = rev
            # end for
        # end for
        canvas_size = self._parent._max_length
        self.setRect(0, 0, bw*canvas_size, bw2)
    # end def

    def removeRepeats(self, n=None):
        """
        Adds n*bases_per_repeat PreXoverItems to fwd and rev groups.
        If n is None, remove all PreXoverItems from fwd and rev groups.
        """
        if n:
            step_size = self._parent._bases_per_repeat
            end_idx = len(self._fwd_pxo_items)
            start_idx = end_idx - n*step_size
            for i in range(start_idx, end_idx):
                self.scene().removeItem(self._fwd_pxo_items.pop(i))
                self.scene().removeItem(self._rev_pxo_items.pop(i))
        else:
            for i in range(len(self._fwd_pxo_items)):
                self.scene().removeItem(self._fwd_pxo_items.pop(i))
                self.scene().removeItem(self._rev_pxo_items.pop(i))
    # end def

    def updateBasesPerRepeat(self):
        """Recreates colors, all vhi"""
        step_size = self._parent._bases_per_repeat
        _hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i/_hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        self.removeRepeats()
        self.addRepeats()
    # end def

    def part(self):
        return self._parent.part()

    def _vh_name(self):
        return self._parent.virtualHelix().getName()

    def _vh_angle(self):
        return self._parent.virtualHelix().getProperty('eulerZ')

    def _vh_twist_per_base(self):
        return self._parent.virtualHelix().getProperty('_twist_per_base')

    def _vh_Z(self):
        return self._parent.virtualHelix().getProperty('z')

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
        new_max = self._parent._max_length
        if new_max == old_max:
            return
        elif new_max > old_max:
            self._add_pxitems(old_max+1, new_max, self._parent._bases_per_repeat)
        else:
            self._rm_pxitems_after(new_max)
        self._max_base = new_max
    # end def

    def setActiveNeighbors(self, active_item, fwd_idxs, rev_idxs):
        # active_item is a PreXoverItem
        if active_item:
            active_absolute_idx = active_item.absolute_idx()
            cutoff = self._parent._bases_per_repeat/2
            active_idx = active_item.base_idx()
            step_idxs = range(0, self._parent._max_length, self._parent._bases_per_repeat)
            k = 0
            pre_xovers = {}
            for i,j in product(fwd_idxs, step_idxs):
                idx = i+j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                delta = item.absolute_idx()-active_absolute_idx
                if abs(delta)<cutoff and k<10:
                    item.setActiveNeighbor(True, shortcut=str(k), active_item=active_item)
                    pre_xovers[k] = item.name()
                    k+=1
                    self._active_items.append(item)
            for i,j in product(rev_idxs, step_idxs):
                idx = i+j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._rev_pxo_items[i+j]
                delta = item.absolute_idx()-active_absolute_idx
                if abs(delta)<cutoff and k<10:
                    item.setActiveNeighbor(True, shortcut=str(k), active_item=active_item)
                    pre_xovers[k] = item.name()
                    k+=1
                    self._active_items.append(item)
            self._parent.partItem().setKeyPressDict(pre_xovers)
        else:
            self._parent.partItem().setKeyPressDict({})
            while self._active_items:
                self._active_items.pop().setActiveNeighbor(False)
    # end def

    def setProximalItems(self, prox_groups):
        inactive_fwd = set(range(self._parent._max_length))
        inactive_rev = set(range(self._parent._max_length))

        step_idxs = range(0, self._parent._max_length, self._parent._bases_per_repeat)

        for vh_num, fwd_idxs, rev_idxs, is_colliding in prox_groups:
            for i,j in product(fwd_idxs, step_idxs):
                idx = i+j
                if not idx in self._fwd_pxo_items:
                    continue
                item = self._fwd_pxo_items[i+j]
                item.setProximal(True, vh_num=vh_num, colliding=is_colliding)
                if idx in inactive_fwd:
                    inactive_fwd.remove(idx)
            for i,j in product(rev_idxs, step_idxs):
                idx = i+j
                if not idx in self._rev_pxo_items:
                    continue
                item = self._rev_pxo_items[i+j]
                item.setProximal(True, vh_num=vh_num, colliding=is_colliding)
                if idx in inactive_rev:
                    inactive_rev.remove(idx)
        for idx in list(inactive_fwd):
            self._fwd_pxo_items[idx].setProximal(False)
        for idx in list(inactive_rev):
            self._rev_pxo_items[idx].setProximal(False)


    def updatePositionsAfterRotation(self, angle):
        bw = _BASE_WIDTH
        part = self._parent.part()
        canvas_size = self._parent._max_length
        step_size = self._parent._bases_per_repeat
        xdelta = angle/360. * bw*step_size
        for i, item in self._fwd_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
        for i, item in self._rev_pxo_items.items():
            x = (bw*i + xdelta) % (bw*canvas_size)
            item.setX(x)
    # end def

    def updateModelActivePhos(self, pre_xover_item):
        """Notify model of pre_xover_item hover state."""
        vh = self._parent.virtualHelix()
        if pre_xover_item is None:
            self._parent.part().setProperty('active_phos', None)
            vh.setProperty('active_phos', None)
            return
        vh_name = vh.getName()
        vh_angle = vh.getProperty('eulerZ')
        idx = pre_xover_item.base_idx() # (f|r).step_idx
        facing_angle = pre_xover_item.facing_angle()
        is_fwd = 'fwd' if pre_xover_item.is_fwd() else 'rev'
        value = '%s.%s.%d.%d' % (vh_name, is_fwd, idx, facing_angle)
        self._parent.part().setProperty('active_phos', value)
        vh.setProperty('active_phos', value)
    # end def

    def updateViewActivePhos(self, new_active_item=None):
        while self._active_items:
            self._active_items.pop().setActive(False)
        if new_active_item:
            new_active_item.setActive(True)
            self._active_items.append(new_active_item)
    # end def


class VirtualHelixItem(QGraphicsPathItem, AbstractVirtualHelixItem):
    """
    VirtualHelixItem for PathView.

    VHI maintains local copies of model_virtual_helix properties.
    When refreshing appearance, VHI children should ask parent VHI for current
    values, introspect for comparison, and update if necessary.
    """
    def __init__(self, part_item, model_virtual_helix, viewroot):
        super(VirtualHelixItem, self).__init__(part_item.proxy())
        self._part_item = part_item
        self._model_virtual_helix = mvh = model_virtual_helix
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, model_virtual_helix)

        self._handle = VirtualHelixHandleItem(part_item, self, viewroot)
        self._last_strand_set = None
        self._last_idx = None
        self._scaffold_background = None

        self._repeats = mvh.getProperty('repeats')
        self._bases_per_repeat = mvh.getProperty('bases_per_repeat')
        # self._turns_per_repeat = mvh.getProperty('turns_per_repeat')
        self._max_length = mvh.getProperty('_max_length')

        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setBrush(getNoBrush())
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)

        view = viewroot.scene().views()[0]
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        should_show_details = view.shouldShowDetails()

        pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(should_show_details)
        self.setPen(pen)

        self.refreshPath()
        self._prexoveritemgroup = _pxig = PreXoverItemGroup(self)
        self.refreshProximalItems()
        # self._activephositem = ActivePhosItem(self)
    # end def

    ### SIGNALS ###

    ### SLOTS ###

    def levelOfDetailChangedSlot(self, boolval):
        """Not connected to the model, only the QGraphicsView"""
        pen = self.pen()
        pen.setCosmetic(boolval)
        self.setPen(pen)
    # end def

    def strandAddedSlot(self, sender, strand):
        """
        Instantiates a StrandItem upon notification that the model has a
        new Strand.  The StrandItem is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        StrandItem(strand, self, self._viewroot)
    # end def

    def decoratorAddedSlot(self, decorator):
        """
        Instantiates a DecoratorItem upon notification that the model has a
        new Decorator.  The Decorator is responsible for creating its own
        controller for communication with the model, and for adding itself to
        its parent (which is *this* VirtualHelixItem, i.e. 'self').
        """
        pass

    def virtualHelixNumberChangedSlot(self, virtual_helix, number):
        self._handle.setNumber()
    # end def

    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        ### TRANSFORM PROPERTIES ###
        mvh = self._model_virtual_helix
        if property_key == 'z':
            z = float(new_value)
            self.setX(z)
            self._handle.setX(z-_VH_XOFFSET)
            self.part().partDimensionsChangedSignal.emit(self.part(), True)
        elif property_key == 'eulerZ':
            self._handle.rotateWithCenterOrigin(new_value)
            self._prexoveritemgroup.updatePositionsAfterRotation(new_value)
        ### GEOMETRY PROPERTIES ###
        elif property_key == 'repeats':
            self.updateRepeats(int(new_value))
        elif property_key == 'bases_per_repeat':
            self.updateBasesPerRepeat(int(new_value))
        # elif property_key == 'turns_per_repeat':
        #     print(virtual_helix, property_key, new_value)
        #     pass
        ### RUNTIME PROPERTIES ###
        elif property_key == 'active_phos':
            hpxig = self._handle._prexoveritemgroup
            pxig = self._prexoveritemgroup
            if new_value:
                # vh-handle
                vh_name, fwd_str, base_idx, facing_angle = new_value.split('.')
                is_fwd = 1 if fwd_str == 'fwd' else 0
                step_idx = int(base_idx) % self._bases_per_repeat
                h_item = hpxig.getItem(is_fwd, step_idx)
                hpxig.updateViewActivePhos(h_item)
                # vh
                item = pxig.getItem(is_fwd, step_idx)
                pxig.updateViewActivePhos(item)
            else:
                hpxig.updateViewActivePhos(None) # vh-handle
                pxig.updateViewActivePhos(None) # vh
                # self._activephositem.hide()
        elif property_key == 'neighbor_active_angle':
            hpxig = self._handle._prexoveritemgroup
            pxig = self._prexoveritemgroup
            if new_value:
                active_value = self.part().getProperty('active_phos')
                if not active_value:
                    return
                vh_name, fwd_str, base_idx, facing_angle = active_value.split('.')
                is_fwd = True if fwd_str == 'fwd' else False
                active_idx = int(base_idx)
                vh = self._part_item.getVHItemByName(vh_name)
                active_item = vh._prexoveritemgroup.getItem(is_fwd, active_idx)
                neighbors = self._model_virtual_helix.getProperty('neighbors').split()
                for n in neighbors:
                    n_name, n_angle = n.split(':')
                    if n_name == vh_name:
                        fwd_items, rev_items = hpxig.getItemsFacingNearAngle(int(n_angle))
                        fwd_idxs = [item.step_idx() for item in fwd_items]
                        rev_idxs = [item.step_idx() for item in rev_items]
                        pxig.setActiveNeighbors(active_item, fwd_idxs, rev_idxs)
            else:
                hpxig.resetAllItemsAppearance()
                self._prexoveritemgroup.setActiveNeighbors(None, None, None)
        elif property_key == 'neighbors':
            pxig = self._prexoveritemgroup
            self.refreshProximalItems()
    # end def

    def refreshProximalItems(self):
        """Make PXIs visible if they have proximal neighbors."""
        hpxig = self._handle._prexoveritemgroup
        pxig = self._prexoveritemgroup
        prox_groups = []
        neighbors = self._model_virtual_helix.getProperty('neighbors').split()
        for n in neighbors:
            n_name, n_angle = n.split(':')
            fwd_items, rev_items = hpxig.getItemsFacingNearAngle(int(n_angle))
            fwd_idxs = [item.step_idx() for item in fwd_items]
            rev_idxs = [item.step_idx() for item in rev_items]
            colliding = True if n_name[-1] == '*' else False
            vh_num = n_name[2:]
            prox_groups.append((vh_num, fwd_idxs, rev_idxs, colliding))
        pxig.setProximalItems(prox_groups)
    # end def

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if property_key == 'color':
            self._handle.refreshColor()
    # end def

    def virtualHelixRemovedSlot(self, virtual_helix):
        self._controller.disconnectSignals()
        self._controller = None

        scene = self.scene()
        self._handle.remove()
        scene.removeItem(self)
        self._part_item.removeVirtualHelixItem(self)
        self._part_item = None
        self._model_virtual_helix = None
        self._getActiveTool = None
        self._handle = None
    # end def

    ### ACCESSORS ###
    def coord(self):
        return self._model_virtual_helix.coord()
    # end def

    def viewroot(self):
        return self._viewroot
    # end def

    def handle(self):
        return self._handle
    # end def

    def part(self):
        return self._part_item.part()
    # end def

    def partItem(self):
        return self._part_item
    # end def

    def number(self):
        return self._model_virtual_helix.number()
    # end def

    def virtualHelix(self):
        return self._model_virtual_helix
    # end def

    def window(self):
        return self._part_item.window()
    # end def

    ### DRAWING METHODS ###
    def isStrandOnTop(self, strand):
        return strand.strandSet().isScaffold()
        # sS = strand.strandSet()
        # isEvenParity = self._model_virtual_helix.isEvenParity()
        # return isEvenParity and sS.isScaffold() or\
        #        not isEvenParity and sS.isStaple()
    # end def

    def isStrandTypeOnTop(self, strand_type):
        return strand_type is StrandType.SCAFFOLD
        # isEvenParity = self._model_virtual_helix.isEvenParity()
        # return isEvenParity and strand_type is StrandType.SCAFFOLD or \
        #        not isEvenParity and strand_type is StrandType.STAPLE
    # end def

    def upperLeftCornerOfBase(self, idx, strand):
        x = idx * _BASE_WIDTH
        y = 0 if self.isStrandOnTop(strand) else _BASE_WIDTH
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx, strand_type):
        x = idx * _BASE_WIDTH
        y = 0 if self.isStrandTypeOnTop(strand_type) else _BASE_WIDTH
        return x, y
    # end def

    # http://stackoverflow.com/questions/6800193/
    def prime_factors(self, n):
        return set(x for tup in ([i, n//i] 
                    for i in range(1, int(n**0.5)+1) if n % i == 0) for x in tup)

    def refreshPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        path = QPainterPath()

        bw = _BASE_WIDTH
        bw2 = 2 * bw
        canvas_size = self._max_length

        # border
        path.addRect(0, 0, bw * canvas_size, 2 * bw)

        # minor tick marks at second-largest prime factor
        factor_list = sorted(self.prime_factors(self._bases_per_repeat))
        sub_step_size = factor_list[-2] if len(factor_list) > 2 else self._bases_per_repeat
        for i in range(canvas_size):
            x = round(bw * i) #+ .5
            if i % sub_step_size == 0:
                path.moveTo(x - .5,  0)
                path.lineTo(x - .5,  bw2)
                path.lineTo(x - .25, bw2)
                path.lineTo(x - .25, 0)
                path.lineTo(x,       0)
                path.lineTo(x,       bw2)
                path.lineTo(x + .25, bw2)
                path.lineTo(x + .25, 0)
                path.lineTo(x + .5,  0)
                path.lineTo(x + .5,  bw2)
            else:
                path.moveTo(x, 0)
                path.lineTo(x, 2 * bw)

        # fwd-rev divider
        path.moveTo(0, bw)
        path.lineTo(bw * canvas_size, bw)
        self.setPath(path)
    # end def

    def updateRepeats(self, new_value):
        if self._repeats == new_value:
            return
        pxig = self._prexoveritemgroup
        if self._repeats < new_value:
            n = new_value - self._repeats
            self._repeats = new_value
            pxig.addRepeats(n)
        elif self._repeats > new_value:
            n = self._repeats - new_value
            self._repeats = new_value
            pxig.removeRepeats(n)
        self._max_length = self._model_virtual_helix.getMaxLength()
        self.refreshPath()
    # end def

    def updateBasesPerRepeat(self, new_value):
        pxig = self._prexoveritemgroup
        if self._bases_per_repeat != new_value:
            self._bases_per_repeat = new_value
            pxig.updateBasesPerRepeat()
            self._max_length = self._model_virtual_helix.getMaxLength()
            self.refreshPath()
    # end def

    def resize(self):
        """Called by part on resize."""
        self.refreshPath()
        self._prexoveritemgroup.resize()
        # self._activephositem.resize()
        # self._max_base = self.part().maxBaseIdx()

    ### PUBLIC SUPPORT METHODS ###
    def setActive(self, idx):
        """Makes active the virtual helix associated with this item."""
        self.part().setActiveVirtualHelix(self._model_virtual_helix, idx)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
        self.scene().views()[0].addToPressList(self)
        strand_set, idx = self.baseAtPoint(event.pos())
        self.setActive(idx)
        tool_method_name = self._getActiveTool().methodPrefix() + "MousePress"

        ### uncomment for debugging modifier selection
        # strand_set, idx = self.baseAtPoint(event.pos())
        # row, col = strand_set.virtualHelix().coord()
        # self._part_item.part().selectPreDecorator([(row,col,idx)])

        if hasattr(self, tool_method_name):
            self._last_strand_set, self._last_idx = strand_set, idx
            getattr(self, tool_method_name)(strand_set, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            strand_set, idx = self.baseAtPoint(event.pos())
            if self._last_strand_set != strand_set or self._last_idx != idx:
                self._last_strand_set, self._last_idx = strand_set, idx
                getattr(self, tool_method_name)(strand_set, idx)
        else:
            event.setAccepted(False)
    # end def

    def customMouseRelease(self, event):
        """
        Parses a mouseReleaseEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
        tool_method_name = self._getActiveTool().methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(self._last_strand_set, self._last_idx)
        else:
            event.setAccepted(False)
    # end def

    ### COORDINATE UTILITIES ###
    def baseAtPoint(self, pos):
        """
        Returns the (strand_type, index) under the location x,y or None.

        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.
        """
        x, y = pos.x(), pos.y()
        mVH = self._model_virtual_helix
        base_idx = int(floor(x / _BASE_WIDTH))
        min_base, max_base = 0, mVH.maxBaseIdx()
        if base_idx < min_base or base_idx >= max_base:
            base_idx = util.clamp(base_idx, min_base, max_base)
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strandIdx = floor(y * 1. / _BASE_WIDTH)
        if strandIdx < 0 or strandIdx > 1:
            strandIdx = int(util.clamp(strandIdx, 0, 1))
        strand_set = mVH.getStrandSetByIdx(strandIdx)
        return (strand_set, base_idx)
    # end def

    def keyPanDeltaX(self):
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)"""
        dx = self._part_item.part().stepSize() * _BASE_WIDTH
        return self.mapToScene(QRectF(0, 0, dx, 1)).boundingRect().width()
    # end def

    def hoverLeaveEvent(self, event):
        self._part_item.updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event):
        """
        Parses a mouseMoveEvent to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.
        """
        base_idx = int(floor(event.pos().x() / _BASE_WIDTH))
        loc = "%d[%d]" % (self.number(), base_idx)
        self._part_item.updateStatusBar(loc)

        active_tool = self._getActiveTool()
        tool_method_name = self._getActiveTool().methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            strand_type, idx_x, idx_y = active_tool.baseAtPoint(self, event.pos())
            getattr(self, tool_method_name)(strand_type, idx_x, idx_y)
    # end def

    ### TOOL METHODS ###
    def pencilToolMousePress(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if not active_tool.isDrawingStrand():
            active_tool.initStrandItemFromVHI(self, strand_set, idx)
            active_tool.setIsDrawingStrand(True)
    # end def

    def pencilToolMouseMove(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.updateStrandItemFromVHI(self, strand_set, idx)
    # end def

    def pencilToolMouseRelease(self, strand_set, idx):
        """strand.getDragBounds"""
        # print "%s: %s[%s]" % (util.methodName(), strand_set, idx)
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.setIsDrawingStrand(False)
            active_tool.attemptToCreateStrand(self, strand_set, idx)
    # end def

    def pencilToolHoverMove(self, strand_type, idx_x, idx_y):
        """Pencil the strand is possible."""
        part_item = self.partItem()
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromVHI(self, strand_type, idx_x, idx_y)
    # end def
