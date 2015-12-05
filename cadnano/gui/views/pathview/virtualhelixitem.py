from math import floor
from itertools import product

from PyQt5.QtCore import QRectF, QLineF, Qt, QObject, QPointF, pyqtSignal
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsEllipseItem

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

        # self.setPen(getPenObj('#cc0000', 0.25))
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
# end class


class PreXoverItemGroup(QGraphicsRectItem):
    HUE_FACTOR = 1.6

    def __init__(self, parent=None):
        super(QGraphicsRectItem, self).__init__(parent)
        self._parent = parent
        self.setPen(getNoPen())
        part = parent.part()
        self._max_base = part.maxBaseIdx()
        step_size = part.stepSize()
        _hue_scale = step_size*self.HUE_FACTOR
        self._colors = [QColor.fromHsvF(i/_hue_scale, 0.75, 0.8).name() \
                                    for i in range(step_size)]
        self._fwd_pxo_items = {}
        self._rev_pxo_items = {}
        self._active_items = []
        self._add_pxitems(0, self._max_base+1, step_size)
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def _add_pxitems(self, start_idx, end_idx, step_size):
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
        canvas_size = self._parent.part().maxBaseIdx()+1
        self.setRect(0, 0, bw*canvas_size, bw2)
    # end def

    def _rm_pxitems_after(self, new_max):
        # print("_rm_last_n_pxitems", n, len(self._fwd_pxo_items))
        for i in range(new_max+1, self._max_base+1):
            self.scene().removeItem(self._fwd_pxo_items.pop(i))
            self.scene().removeItem(self._rev_pxo_items.pop(i))
    # end def

    def _vh_name(self):
        return self._parent.virtualHelix().getName()

    def _vh_angle(self):
        return self._parent.virtualHelix().getProperty('eulerZ')

    ### PUBLIC SUPPORT METHODS ###
    def getItem(self, is_fwd, idx):
        if is_fwd:
            return self._fwd_pxo_items[idx]
        else:
            return self._rev_pxo_items[idx]
    # end def

    def resize(self):
        part = self._parent.part()
        old_max = self._parent._max_base
        new_max = part.maxBaseIdx()
        if new_max == old_max:
            return
        elif new_max > old_max:
            self._add_pxitems(old_max+1, new_max, part.stepSize())
        else:
            self._rm_pxitems_after(new_max)
        self._max_base = new_max
    # end def

    def setActiveNeighbors(self, active_item, fwd_rev_idxs):
        if active_item:
            part = self._parent.part()
            cutoff = part.stepSize()
            active_idx = active_item.base_idx()
            step_idxs = range(0, part.maxBaseIdx(), part.stepSize())
            fwd_idxs, rev_idxs = fwd_rev_idxs
            for i,j in product(fwd_idxs, step_idxs):
                if abs(i+j-active_idx)<cutoff:
                    item = self._fwd_pxo_items[i+j]
                    item.setActiveNeighbor(True, active_item=active_item)
                    self._active_items.append(item)
            for i,j in product(rev_idxs, step_idxs):
                if abs(i+j-active_idx)<cutoff:
                    item = self._rev_pxo_items[i+j]
                    item.setActiveNeighbor(True, active_item=active_item)
                    self._active_items.append(item)
        else:
            while self._active_items:
                self._active_items.pop().setActiveNeighbor(False)
    # end def

    def updatePositionsAfterRotation(self, angle):
        bw = _BASE_WIDTH
        part = self._parent.part()
        canvas_size = part.maxBaseIdx() + 1
        step_size = part.stepSize()
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
        step_idx = pre_xover_item.base_idx() # (f|r).step_idx
        facing_angle = pre_xover_item.facing_angle()
        is_fwd = 'fwd' if pre_xover_item.is_fwd() else 'rev'
        value = '%s.%s.%d.%d' % (vh_name, is_fwd, step_idx, facing_angle)
        self._parent.part().setProperty('active_phos', value)
        vh.setProperty('active_phos', value)
    # end def


class VirtualHelixItem(QGraphicsPathItem, AbstractVirtualHelixItem):
    """VirtualHelixItem for PathView"""
    findChild = util.findChild  # for debug

    def __init__(self, part_item, model_virtual_helix, viewroot):
        super(VirtualHelixItem, self).__init__(part_item.proxy())
        self._part_item = part_item
        self._model_virtual_helix = model_virtual_helix
        self._viewroot = viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, model_virtual_helix)

        self._handle = VirtualHelixHandleItem(part_item, self, viewroot)
        self._last_strand_set = None
        self._last_idx = None
        self._scaffold_background = None
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setBrush(getNoBrush())

        view = viewroot.scene().views()[0]
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        should_show_details = view.shouldShowDetails()

        pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(should_show_details)
        self.setPen(pen)

        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)

        self._max_base = self.part().maxBaseIdx()
        self._prexoveritemgroup = _pxig = PreXoverItemGroup(self)
        self._activephositem = ActivePhosItem(self)
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
        if property_key == 'z':
            z = float(new_value)
            self.setX(z)
            self._handle.setX(z-_VH_XOFFSET)
            self.part().partDimensionsChangedSignal.emit(self.part())
        elif property_key == 'eulerZ':
            self._handle.rotateWithCenterOrigin(new_value)
            self._prexoveritemgroup.updatePositionsAfterRotation(new_value)
        elif property_key == 'active_phos':
            hpxig = self._handle._prexoveritemgroup
            if new_value:
                # vh-handle
                vh_name, fwd_str, base_idx, facing_angle = new_value.split('.')
                is_fwd = 1 if fwd_str == 'fwd' else 0
                step_idx = int(base_idx) % self.part().stepSize()
                item = hpxig.getItem(is_fwd, step_idx)
                hpxig.updateViewActivePhos(item)
                # vh
                vh_angle = self.virtualHelix().getProperty('eulerZ')
                # _tbp = self.part()._TWIST_PER_BASE
                # offset = round(vh_angle/_tbp, 0)
                # idx = int(step_idx) + offset
                self._activephositem.update(is_fwd, step_idx, item.color())
            else:
                # vh-handle
                self._activephositem.hide()
                hpxig.updateViewActivePhos(None)
                # vh
                self._activephositem.hide()
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
                local_angle = (int(new_value)+180) % 360
                fwd_items, rev_items = hpxig.getItemsFacingNearAngle(local_angle)
                fwd_idxs = [item.step_idx() for item in fwd_items]
                rev_idxs = [item.step_idx() for item in rev_items]
                # close_fwd = list(filter(lambda x:abs(x-active_idx)<delta, fwd_idxs))
                # close_rev = list(filter(lambda x:abs(x-active_idx)<delta, rev_idxs))
                # print(fwd_idxs)
                # print(close)
                # self._prexoveritemgroup.setActiveNeighbor(active_item, (close_fwd, close_rev))
                self._prexoveritemgroup.setActiveNeighbors(active_item, (fwd_idxs, rev_idxs))
            else:
                hpxig.resetAllItemsAppearance()
                self._prexoveritemgroup.setActiveNeighbors(None, None)
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

    def refreshPath(self):
        """
        Returns a QPainterPath object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        bw = _BASE_WIDTH
        bw2 = 2 * bw
        part = self.part()
        path = QPainterPath()
        sub_step_size = part.subStepSize()
        canvas_size = part.maxBaseIdx() + 1
        # border
        path.addRect(0, 0, bw * canvas_size, 2 * bw)
        # minor tick marks
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

                # path.moveTo(x-.5, 0)
                # path.lineTo(x-.5, 2 * bw)
                # path.lineTo(x+.5, 2 * bw)
                # path.lineTo(x+.5, 0)

            else:
                path.moveTo(x, 0)
                path.lineTo(x, 2 * bw)

        # staple-scaffold divider
        path.moveTo(0, bw)
        path.lineTo(bw * canvas_size, bw)

        self.setPath(path)

        if self._model_virtual_helix.scaffoldIsOnTop():
            scaffoldY = 0
        else:
            scaffoldY = bw
    # end def

    def resize(self):
        """Called by part on resize."""
        self.refreshPath()
        self._prexoveritemgroup.resize()
        self._activephositem.resize()
        self._max_base = self.part().maxBaseIdx()

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
        min_base, max_base = 0, mVH.part().maxBaseIdx()
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
