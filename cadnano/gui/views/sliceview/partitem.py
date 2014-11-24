
from cadnano.gui.controllers.itemcontrollers.partitemcontroller import PartItemController
from .emptyhelixitem import EmptyHelixItem
from .virtualhelixitem import VirtualHelixItem
from .activesliceitem import ActiveSliceItem

from . import slicestyles as styles
import cadnano.util as util
from cadnano import getReopen

from PyQt5.QtCore import QPointF, Qt, QRectF, QEvent, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QBrush, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem

_RADIUS = styles.SLICE_HELIX_RADIUS
_DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
HIGHLIGHT_WIDTH = styles.SLICE_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.SLICE_HELIX_STROKE_WIDTH)/2.
_HOVER_RECT = _DEFAULT_RECT.adjusted(-DELTA, -DELTA, DELTA, DELTA)
_MOD_PEN = QPen(styles.BLUE_STROKE, HIGHLIGHT_WIDTH)

class PartItem(QGraphicsItem):
    _RADIUS = styles.SLICE_HELIX_RADIUS

    def __init__(self, model_part, parent=None):
        """
        Parent should be either a SliceRootItem, or an AssemblyItem.

        Invariant: keys in _empty_helix_hash = range(_nrows) x range(_ncols)
        where x is the cartesian product.
        
        Order matters for deselector, probe, and setlattice
        """
        super(PartItem, self).__init__(parent)
        self._part = model_part
        self._controller = PartItemController(self, model_part)
        self._active_slice_item = ActiveSliceItem(self, model_part.activeBaseIndex())
        self._scaleFactor = self._RADIUS/model_part.radius()
        self._empty_helix_hash = {}
        self._virtual_helix_hash = {}
        self._nrows, self._ncols = 0, 0
        self._rect = QRectF(0, 0, 0, 0)
        self._initDeselector()
        # Cache of VHs that were active as of last call to activeSliceChanged
        # If None, all slices will be redrawn and the cache will be filled.
        # Connect destructor. This is for removing a part from scenes.
        self.probe = self.IntersectionProbe(self)
        # initialize the PartItem with an empty set of old coords
        self._setLattice([], model_part.generatorFullLattice())
        self.setFlag(QGraphicsItem.ItemHasNoContents)  # never call paint
        self.setZValue(styles.ZPARTITEM)
        self._initModifierCircle()
    # end def

    def _initDeselector(self):
        """
        The deselector grabs mouse events that missed a slice and clears the
        selection when it gets one.
        """
        self.deselector = ds = PartItem.Deselector(self)
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

    def partDimensionsChangedSlot(self, sender):
        pass
    # end def

    def partHideSlot(self, sender):
        self.hide()
    # end def

    def partParentChangedSlot(self, sender):
        """docstring for partParentChangedSlot"""
        # print "PartItem.partParentChangedSlot"
        pass

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
        
        self._part = None
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
        mC = self._mod_circ
        x,y = self._part.latticeCoordToPositionXY(row, col, self.scaleFactor())
        mC.setPos(x,y)
        if self._can_show_mod_circ:
            mC.show()
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

    ### ACCESSORS ###
    def boundingRect(self):
        return self._rect
    # end def

    def part(self):
        return self._part
    # end def

    def scaleFactor(self):
        return self._scaleFactor
    # end def

    def setPart(self, newPart):
        self._part = newPart
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
        if self.part() == None:
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
        QGraphicsItem.mousePressEvent(self, event)
    # end def


    class Deselector(QGraphicsItem):
        """The deselector lives behind all the slices and observes mouse press
        events that miss slices, emptying the selection when they do"""
        def __init__(self, parent_HGI):
            super(PartItem.Deselector, self).__init__()
            self.parent_HGI = parent_HGI
        def mousePressEvent(self, event):
            self.parent_HGI.part().setSelection(())
            super(PartItem.Deselector, self).mousePressEvent(event)
        def boundingRect(self):
            return self.parent_HGI.boundingRect()
        def paint(self, painter, option, widget=None):
            pass


    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass