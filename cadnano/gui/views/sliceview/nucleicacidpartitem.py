from collections import OrderedDict

from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF, QEvent, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QBrush, QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtWidgets import QApplication

from cadnano import getReopen, util
from cadnano.enum import PartEdges
from cadnano.gui.controllers.itemcontrollers.nucleicacidpartitemcontroller import NucleicAcidPartItemController
from cadnano.gui.palette import getPenObj, getBrushObj
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from . import slicestyles as styles
from .activesliceitem import ActiveSliceItem
from .emptyhelixitem import EmptyHelixItem
from .virtualhelixitem import VirtualHelixItem


_RADIUS = styles.SLICE_HELIX_RADIUS
_DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.
_HOVER_RECT = _DEFAULT_RECT.adjusted(-DELTA, -DELTA, DELTA, DELTA)
_MOD_PEN = getPenObj(styles.BLUE_STROKE, HIGHLIGHT_WIDTH)

_DEFAULT_WIDTH = styles.DEFAULT_PEN_WIDTH
_DEFAULT_ALPHA = styles.DEFAULT_ALPHA
_SELECTED_COLOR = styles.SELECTED_COLOR
_SELECTED_WIDTH = styles.SELECTED_PEN_WIDTH
_SELECTED_ALPHA = styles.SELECTED_ALPHA

_BOUNDING_RECT_PADDING = 10

class NucleicAcidPartItem(QGraphicsItem, AbstractPartItem):
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, model_part_instance, parent=None):
        """
        Parent should be either a SliceRootItem, or an AssemblyItem.

        Invariant: keys in _empty_helix_hash = range(_nrows) x range(_ncols)
        where x is the cartesian product.

        Order matters for deselector, probe, and setlattice
        """
        super(NucleicAcidPartItem, self).__init__(parent)
        self._model_instance = model_part_instance
        self._model_part = m_p = model_part_instance.reference()
        self._model_props = m_props = m_p.getPropertyDict()
        self._controller = NucleicAcidPartItemController(self, m_p)
        self._active_slice_item = ActiveSliceItem(self, m_p.activeBaseIndex())
        self._scaleFactor = self._RADIUS / m_p.radius()
        self._empty_helix_hash = {}
        self._virtual_helix_hash = {}
        self._nrows, self._ncols = 0, 0
        self._rect = QRectF(0, 0, 0, 0)
        self._initDeselector()
        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        # Connect destructor. This is for removing a part from scenes.
        self.probe = self.IntersectionProbe(self)
        self.hide() # hide while until after attemptResize() to avoid flicker
        # initialize the NucleicAcidPartItem with an empty set of old coords
        self._setLattice([], m_p.generatorFullLattice())
        self.setFlag(QGraphicsItem.ItemHasNoContents)  # never call paint
        self.setZValue(styles.ZPARTITEM)
        self._initModifierCircle()
        _p = _BOUNDING_RECT_PADDING
        self._outlinerect = _orect = self.childrenBoundingRect().adjusted(-_p, -_p, _p, _p)
        self._outline = QGraphicsRectItem(_orect, self)
        self._outline.setPen(QPen(Qt.NoPen))
        self._drag_handle = DragHandle(QRectF(_orect), self)
        # self._drag_handle.attemptResize(QRectF(441.6, 360, 160, 135.5)) # show 3rows x 6cols
        if len(m_p.document().children()) > 1: 
            self._adjustPosition()
        self.show()
        # select upon creation
        for _part in m_p.document().children():
            if _part is m_p:
                _part.setSelected(True)
            else:
                _part.setSelected(False)
    # end def

    def getVHItemList(self):
        return sorted(self._virtual_helix_hash.values(), key=lambda t:t.number())

    def _adjustPosition(self):
        """Find the left-most bottom-most sibling, and reposition below."""
        _p = _BOUNDING_RECT_PADDING
        _visible_topleft_pos = self.visibleTopLeftScenePos()
        _bot_left_sib = self.mapToScene(QPointF(-_p*2,-_p*2)) # choose a starting point
        for sibling in self.parentItem().childItems():
            if sibling is self:
                continue
            _sib = sibling.visibleBottomLeftScenePos()
            if (_sib.x() >= _bot_left_sib.x() and _sib.y() >= _bot_left_sib.y()):
                _bot_left_sib = _sib
        # reposition visible-topleft curner under sibling, plus padding
        self.setPos(-_visible_topleft_pos + _bot_left_sib + QPointF(0, 2*_p) )
    # end def

    def visibleTopLeftScenePos(self):
        return self.mapToScene(self._outlinerect.topLeft())
    # end def

    def visibleBottomLeftScenePos(self):
        return self.mapToScene(self._outlinerect.bottomLeft())
    # end def

    def _initDeselector(self):
        """
        The deselector grabs mouse events that missed a slice and clears the
        selection when it gets one.
        """
        self.deselector = ds = NucleicAcidPartItem.Deselector(self)
        ds.setParentItem(self)
        ds.setFlag(QGraphicsItem.ItemStacksBehindParent)
        ds.setZValue(styles.ZDESELECTOR)

    def _initModifierCircle(self):
        self._can_show_mod_circ = False
        self._mod_circ = m_c = QGraphicsEllipseItem(_HOVER_RECT, self)
        m_c.setPen(_MOD_PEN)
        m_c.hide()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partActiveVirtualHelixChangedSlot(self, part, virtualHelix):
        pass

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            if property_key == 'color':
                for _, vhi in self._virtual_helix_hash.items():
                    vhi.updateAppearance()
                for _, ehi in self._empty_helix_hash.items():
                    ehi.updateAppearance()
            elif property_key == 'circular':
                pass
            elif property_key == 'dna_sequence':
                pass
                # self.updateRects()
    # end def

    def partRemovedSlot(self, sender):
        """docstring for partRemovedSlot"""
        self._active_slice_item.removed()
        self.parentItem().removePartItem(self)

        scene = self.scene()

        self._virtual_helix_hash = None

        for item in list(self._empty_helix_hash.items()):
            key, val = item
            scene.removeItem(val)
            del self._empty_helix_hash[key]
        self._empty_helix_hash = None

        scene.removeItem(self)

        self._model_part = None
        self.probe = None
        self._mod_circ = None

        self.deselector = None
        self._controller.disconnectSignals()
        self._controller = None
    # end def

    def partVirtualHelicesReorderedSlot(self, sender, orderedCoordList):
        pass
    # end def

    def partPreDecoratorSelectedSlot(self, sender, row, col, baseIdx):
        """docstring for partPreDecoratorSelectedSlot"""
        vhi = self.getVirtualHelixItemByCoord(row, col)
        view = self.window().slice_graphics_view
        view.scene_root_item.resetTransform()
        view.centerOn(vhi)
        view.zoomIn()
        m_c = self._mod_circ
        x,y = self._model_part.latticeCoordToPositionXY(row, col, self.scaleFactor())
        m_c.setPos(x,y)
        if self._can_show_mod_circ:
            m_c.show()
    # end def

    def partVirtualHelixAddedSlot(self, sender, virtual_helix):
        vh = virtual_helix
        coords = vh.coord()

        empty_helix_item = self._empty_helix_hash[coords]
        # TODO test to see if self._virtual_helix_hash is necessary
        vhi = VirtualHelixItem(vh, empty_helix_item)
        self._virtual_helix_hash[coords] = vhi
    # end def

    def partVirtualHelixRenumberedSlot(self, sender, coord):
        pass
    # end def

    def partVirtualHelixResizedSlot(self, sender, coord):
        pass
    # end def

    def updatePreXoverItemsSlot(self, sender, virtualHelix):
        pass
    # end def

    def partColorChangedSlot(self):
        print("sliceview Dnapart partColorChangedSlot")
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        """Set this Z to front, and return other Zs to default."""
        if is_selected:
            self._drag_handle.resetAppearance(_SELECTED_COLOR, _SELECTED_WIDTH, _SELECTED_ALPHA)
            self.setZValue(styles.ZPARTITEM+1)
        else:
            self._drag_handle.resetAppearance(self.modelColor(), _DEFAULT_WIDTH, _DEFAULT_ALPHA)
            self.setZValue(styles.ZPARTITEM)

    ### ACCESSORS ###
    def boundingRect(self):
        return self._rect
    # end def

    def part(self):
        return self._model_part
    # end def

    def modelColor(self):
        return self._model_props['color']
    # end def

    def scaleFactor(self):
        return self._scaleFactor
    # end def

    def setPart(self, new_part):
        self._model_part = new_part
    # end def

    def window(self):
        return self.parentItem().window()
    # end def



    ### PRIVATE SUPPORT METHODS ###
    def _upperLeftCornerForCoords(self, row, col):
        pass  # subclass
    # end def

    def _updateGeometry(self):
        self._rect = QRectF(0, 0, *self.part().dimensions())
    # end def

    def _spawnEmptyHelixItemAt(self, row, column):
        helix = EmptyHelixItem(row, column, self)
        # helix.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
        self._empty_helix_hash[(row, column)] = helix
    # end def

    def _killHelixItemAt(row, column):
        s = self._empty_helix_hash[(row, column)]
        s.scene().removeItem(s)
        del self._empty_helix_hash[(row, column)]
    # end def

    def _setLattice(self, old_coords, new_coords):
        """A private method used to change the number of rows,
        cols in response to a change in the dimensions of the
        part represented by the receiver"""
        old_set = set(old_coords)
        old_list = list(old_set)
        new_set = set(new_coords)
        new_list = list(new_set)
        for coord in old_list:
            if coord not in new_set:
                self._killHelixItemAt(*coord)
        # end for
        for coord in new_list:
            if coord not in old_set:
                self._spawnEmptyHelixItemAt(*coord)
        # end for
        # self._updateGeometry(newCols, newRows)
        # self.prepareGeometryChange()
        # the Deselector copies our rect so it changes too
        self.deselector.prepareGeometryChange()
        if not getReopen():
            self.zoomToFit()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def getVirtualHelixItemByCoord(self, row, column):
        if (row, column) in self._empty_helix_hash:
            return self._virtual_helix_hash[(row, column)]
        else:
            return None
    # end def

    def paint(self, painter, option, widget=None):
        pass
    # end def

    def selectionWillChange(self, newSel):
        if self.part() is None:
            return
        if self.part().selectAllBehavior():
            return
        for sh in self._empty_helix_hash.values():
            sh.setSelected(sh.virtualHelix() in newSel)
    # end def

    def setModifyState(self, bool):
        """Hides the mod_rect when modify state disabled."""
        self._can_show_mod_circ = bool
        if bool == False:
            self._mod_circ.hide()

    def updateStatusBar(self, statusString):
        """Shows statusString in the MainWindow's status bar."""
        pass  # disabled for now.
        # self.window().statusBar().showMessage(statusString, timeout)

    def vhAtCoordsChanged(self, row, col):
        self._empty_helix_hash[(row, col)].update()
    # end def

    def zoomToFit(self):
        thescene = self.scene()
        theview = thescene.views()[0]
        theview.zoomToFit()
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        # self.createOrAddBasesToVirtualHelix()
        self.part().setSelected(True)
        QGraphicsItem.mousePressEvent(self, event)
    # end def


    class Deselector(QGraphicsItem):
        """The deselector lives behind all the slices and observes mouse press
        events that miss slices, emptying the selection when they do"""
        def __init__(self, parent_HGI):
            super(NucleicAcidPartItem.Deselector, self).__init__()
            self.parent_HGI = parent_HGI
        def mousePressEvent(self, event):
            self.parent_HGI.part().setSelection(())
            super(NucleicAcidPartItem.Deselector, self).mousePressEvent(event)
        def boundingRect(self):
            return self.parent_HGI.boundingRect()
        def paint(self, painter, option, widget=None):
            pass


    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass


class DragHandle(QGraphicsRectItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsRectItem, self).__init__(rect, parent)
        self._parent = parent
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self._resizingRectItem = QGraphicsRectItem(self.rect(), self)
        self._bound = PartEdges.NONE
        self._resizing = False
        self.setPen(QPen(Qt.NoPen))
        self.resetAppearance(parent.modelColor(), _DEFAULT_WIDTH, _DEFAULT_ALPHA)
    # end def

    def updateRect(self, rect):
        """adds some padding to the DragHandle"""
        w = rect.width()*.6
        self.setRect(rect.adjusted(w,w,-w,-w).normalized())
    # end def

    def resetAppearance(self, color, width, alpha):
        self._resizingRectItem.setPen(getPenObj(color, width))
        self.setBrush(getBrushObj(color, alpha=alpha))
    # end def

    def getBound(self, pos):
        """return the types of edges that are hovered at pos."""
        _r = self._parent._outlinerect
        _x, _y = pos.x(), pos.y()
        _width = 6
        _bound = PartEdges.NONE
        if abs(_y - _r.top()) < _width: _bound |= PartEdges.TOP
        if abs(_x - _r.left()) < _width: _bound |= PartEdges.LEFT
        if abs(_x - _r.right()) < _width: _bound |= PartEdges.RIGHT
        if abs(_y - _r.bottom()) < _width: _bound |= PartEdges.BOTTOM
        return _bound

    def getCursor(self, bound):
        if ((bound & PartEdges.TOP and bound & PartEdges.LEFT) or
           (bound & PartEdges.BOTTOM and bound & PartEdges.RIGHT)):
            _cursor = Qt.SizeFDiagCursor
        elif ((bound & PartEdges.TOP and bound & PartEdges.RIGHT) or
             (bound & PartEdges.BOTTOM and bound & PartEdges.LEFT)):
            _cursor = Qt.SizeBDiagCursor
        elif (bound & PartEdges.LEFT or bound & PartEdges.RIGHT):
            _cursor = Qt.SizeHorCursor
        elif (bound & PartEdges.TOP or bound & PartEdges.BOTTOM):
            _cursor = Qt.SizeVerCursor
        else:
            _cursor = Qt.OpenHandCursor
        return _cursor

    def hoverEnterEvent(self, event):
        _bound = self.getBound(event.pos())
        _cursor = self.getCursor(_bound)
        self.setCursor(_cursor)
    # end def

    def hoverMoveEvent(self, event):
        _bound = self.getBound(event.pos())
        _cursor = self.getCursor(_bound)
        self.setCursor(_cursor)
    # end def

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
    # end def

    def mousePressEvent(self, event):
        self._edgesToResize = self.getBound(event.pos())
        _cursor = self.getCursor(self._edgesToResize)

        # select this part and deselect everything else
        for _part in self._parent.part().document().children():
            if _part is self._parent.part():
                _part.setSelected(True)
            else:
                _part.setSelected(False)

        self._drag_mousedown_pos = event.pos()

        if _cursor is Qt.ClosedHandCursor:
            self._resizing = False
        elif _cursor in [Qt.SizeBDiagCursor,
                         Qt.SizeFDiagCursor,
                         Qt.SizeHorCursor,
                         Qt.SizeVerCursor]:
            self._resizing = True
    # end def

    def mouseMoveEvent(self, event):
        m = QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.LeftButton))
        if m.length() < QApplication.startDragDistance():
            return
        p = self.mapToScene(QPointF(event.pos()) - QPointF(self._drag_mousedown_pos))
        # still need to correct for qgraphicsview translation
        if self._resizing:
            _x, _y = event.pos().x(), event.pos().y()
            _r = QRectF(self._parent._outlinerect)
            _e = self._edgesToResize
            if _e & PartEdges.TOP: _r.setTop(_y)
            if _e & PartEdges.LEFT: _r.setLeft(_x)
            if _e & PartEdges.RIGHT: _r.setRight(_x)
            if _e & PartEdges.BOTTOM: _r.setBottom(_y)
            self._resizingRectItem.setRect(_r)
        else:
            self._parent.setPos(p)
    # end def

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

        if self._resizing:
            self.attemptResize(self._resizingRectItem.rect())
            self._resizing = False
            self._edgesToResize = PartEdges.NONE
        else:
            pass
        # self._resizingRect.setRect(self._parent._outlinerect)
    # end def

    def attemptResize(self, rect):
        _p = _BOUNDING_RECT_PADDING
        m_p = self._parent._model_part

        # start bounds with topLeft at max, botRight at min
        x1, y1 = m_p.dimensions(self._parent._scaleFactor)
        x2, y2 = 0, 0
        rRect = self.mapRectToScene(rect)
        # only show helices >50% inside rRect
        for _ehi in self._parent._empty_helix_hash.values():
            if rRect.contains(self.mapToScene(_ehi.pos() + _ehi.boundingRect().center())):
                _ehi.show() # _ehi.setHovered()
                # update bounds
                x1 = min(x1, _ehi.pos().x())
                y1 = min(y1, _ehi.pos().y())
                x2 = max(x2, _ehi.pos().x() + _ehi.boundingRect().width())
                y2 = max(y2, _ehi.pos().y() + _ehi.boundingRect().height())
            else:
                _ehi.hide() # _ehi.setNotHovered()
        # print("resize to", x1,y1,x2,y2)
        self._parent._outlinerect = _newRect = QRectF(QPointF(x1,y1),
                          QPointF(x2,y2)).adjusted(-_p, -_p, _p, _p)
        self.updateRect(_newRect)
        self._resizingRectItem.setRect(_newRect)
        self.setRect(_newRect)

# end class
