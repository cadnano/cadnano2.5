from math import sqrt, atan2, degrees, pi

from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF, QEvent, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QBrush, QPainter, QPainterPath, QPen, QColor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsTextItem
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem
from PyQt5.QtWidgets import QUndoCommand, QStyle
from PyQt5.QtWidgets import QApplication

from cadnano import getReopen
from cadnano.gui.views.abstractitems.abstractpartitem import AbstractPartItem
from cadnano.gui.controllers.itemcontrollers.plasmidpartitemcontroller import PlasmidPartItemController
from cadnano.gui.palette import getPenObj, getBrushObj
from . import slicestyles as styles
from .virtualhelixitem import VirtualHelixItem


HOVER_WIDTH = H_W = 20
GAP = 2 # gap between inner and outer strands

_DNALINE_WIDTH = 1
_DNA_PEN = getPenObj(styles.BLUE_STROKE, _DNALINE_WIDTH)
_DNA_BRUSH = getBrushObj('#8099ccff')
_ROTARY_DELTA_WIDTH = 10

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff')

class PlasmidPartItem(QGraphicsItem, AbstractPartItem):

    def __init__(self, model_part_instance, parent=None):
        """
        Parent should be either a SliceRootItem, or an AssemblyItem.
        Order matters for deselector, probe, and setlattice
        """
        super(PlasmidPartItem, self).__init__(parent)
        self._model_instance = model_part_instance
        self._model_part = m_p = model_part_instance.reference()
        self._model_props = m_props = m_p.getPropertyDict()
        self._controller = PlasmidPartItemController(self, m_p)
        self._selection_items = {}
        self._rect = QRectF()
        self._hover_rect = QRectF()
        self._initDeselector()
        self.probe = self.IntersectionProbe(self)
        self.setFlag(QGraphicsItem.ItemHasNoContents)  # never call paint
        self.setZValue(styles.ZPARTITEM)

        self._outer_line = DnaLine(self._rect, self)
        self._inner_line = DnaLine(self._rect, self)
        self._hover_region = DnaHoverRegion(self._hover_rect, self)
        self._drag_handle = DnaDragHandle(QRectF(0, 0, 20, 20), self)
        self.updateRects()

        p = parent.childrenBoundingRect().bottomLeft()
        self.setPos(p.x()+HOVER_WIDTH, p.y())

        self._initSelections()
    # end def

    def updateRects(self):
        circular = self._model_props["circular"]
        dna_length = len(self._model_props["dna_sequence"])
        if circular:
            diameter = round(dna_length * pi / 100,2)
            self._radius = round(diameter/2.,2)
            self._rect = QRectF(0, 0, diameter, diameter)
            self._outer_line.updateRect(QRectF(-GAP/2, -GAP/2, diameter+GAP, diameter+GAP))
            self._inner_line.updateRect(QRectF(GAP/2, GAP/2, diameter-GAP, diameter-GAP))
            self._hover_rect = self._rect.adjusted(-H_W, -H_W, H_W, H_W)
            self._hover_region.updateRect(self._hover_rect)
            self._drag_handle.updateRect(self._rect)
        else:
            pass # linear

    def model_color(self):
        return self._model_props["color"]

    def _initDeselector(self):
        """
        The deselector grabs mouse events that missed a slice and clears the
        selection when it gets one.
        """
        self.deselector = ds = PlasmidPartItem.Deselector(self)
        ds.setParentItem(self)
        ds.setFlag(QGraphicsItem.ItemStacksBehindParent)
        ds.setZValue(styles.ZDESELECTOR)
    # end def

    def _initModifierCircle(self):
        self._can_show_mod_circ = False
        self._mod_circ = m_c = QGraphicsEllipseItem(self._hover_rect, self)
        m_c.setPen(_MOD_PEN)
        m_c.hide()
    # end def

    def _initSelections(self):
        self._selections = self._model_part.getSelectionDict()
        for key in sorted(self._selections):
            (start, end) = self._selections[key]
            # convert bases to angles
    # end def

    def addSelection(self, startAngle, spanAngle):
        dSI = DnaSelectionItem(startAngle, spanAngle, self)
        self._selection_items[dSI] = True
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def partRemovedSlot(self, sender):
        self.parentItem().removePartItem(self)
        scene = self.scene()
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
        mC = self._mod_circ
        x,y = self._model_part.latticeCoordToPositionXY(row, col, self.scaleFactor())
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

    def partPropertyChangedSlot(self, model_part, property_key, new_value):
        if self._model_part == model_part:
            if property_key == "color":
                color = QColor(new_value)
                self._outer_line.updateColor(color)
                self._inner_line.updateColor(color)
                self._hover_region.dummy.updateColor(color)
                for dsi in self._selection_items:
                    dsi.updateColor(color)
            elif property_key == "circular":
                pass
            elif property_key == "dna_sequence":
                self.updateRects()
    # end def

    def partSelectedChangedSlot(self, model_part, is_selected):
        if is_selected:
            self._drag_handle.setBrush(QBrush(QColor(styles.SELECTED_COLOR)))
        else:
            self._drag_handle.setBrush(QBrush(QColor(220, 220, 220)))
    # end def

    ### ACCESSORS ###
    def radius(self):
        return self._radius
    # end def

    def boundingRect(self):
        return self._rect
    # end def

    def part(self):
        return self._model_part
    # end def

    def scaleFactor(self):
        return self._scaleFactor
    # end def

    def setPart(self, newPart):
        self._model_part = newPart
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
        self.window().statusBar().showMessage(statusString, timeout)
        pass  # disabled for now.

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
            super(PlasmidPartItem.Deselector, self).__init__()
            self.parent_HGI = parent_HGI
        def mousePressEvent(self, event):
            self.parent_HGI.part().setSelection(())
            super(PlasmidPartItem.Deselector, self).mousePressEvent(event)
        def boundingRect(self):
            return self.parent_HGI.boundingRect()
        def paint(self, painter, option, widget=None):
            pass
    # end class

    class IntersectionProbe(QGraphicsItem):
        def boundingRect(self):
            return QRectF(0, 0, .1, .1)
        def paint(self, painter, option, widget=None):
            pass
    # end class
# end class


class DnaSelectionItem(QGraphicsPathItem):
    def __init__(self, startAngle, spanAngle, parent=None):
        # setup DNA line
        super(QGraphicsPathItem, self).__init__(parent)
        self._parent = parent
        self.updateAngle(startAngle, spanAngle)
        self.updateColor(parent.model_color())
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


class DnaHoverRegion(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        # setup DNA line
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(_HOVER_BRUSH)
        self.setAcceptHoverEvents(True)

        # hover marker
        self._hoverLine = QGraphicsLineItem(-_ROTARY_DELTA_WIDTH/2, 0, _ROTARY_DELTA_WIDTH/2, 0, self)
        self._hoverLine.setPen(QPen(QColor(204, 0, 0), .5))
        self._hoverLine.hide()

        self._startPos = None
        self._startAngle = None  # save selection start
        self._clockwise = None
        self.dummy = DnaSelectionItem(0, 0, parent)
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
        r = self._parent.radius()
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

        if self._startPos != None and self._clockwise != None:
            self.parentItem().addSelection(self._startAngle, spanAngle)
            self._startPos = self._clockwise = None
        # mark the end
        # x = self._hoverLine.x()
        # y = self._hoverLine.y()
        # f = QGraphicsEllipseItem(x, y, 6, 6, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0, 128)))
    # end def

    def updateHoverLine(self, event):
        """
        Moves red line to point (aX,aY) on DnaLine closest to event.pos.
        Returns the angle of aX, aY, using the Qt arc coordinate system
        (0 = east, 90 = north, 180 = west, 270 = south).
        """
        r = self._parent.radius()
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


class DnaLine(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        # setup DNA line
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        if "color" in parent._model_props:
            self.setPen(QPen(QColor(parent._model_props["color"]), _DNALINE_WIDTH))
        else:
            self.setPen(_DNA_PEN)
        self.setRect(rect)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)
    # end def

    def updateColor(self, color):
        self.setPen(QPen(color, _DNALINE_WIDTH))

    def updateRect(self, rect):
        self.setRect(rect)
# end class


class DnaDragHandle(QGraphicsEllipseItem):
    def __init__(self, rect, parent=None):
        super(QGraphicsEllipseItem, self).__init__(rect, parent)
        self._parent = parent
        # self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(QColor(220, 220, 220)))
    # end def

    def updateRect(self, rect):
        """docstring for updateRect"""
        w = rect.width()*.6
        self.setRect(rect.adjusted(w,w,-w,-w).normalized())
    # end def

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
    # end def

    def hoverMoveEvent(self, event):
        pass
    # end def

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
    # end def

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        self._parent.part().setSelected(True)

        # r = self._parent.radius()
        # self.updateDragHandleLine(event)
        # pos = self._DragHandleLine.pos()
        # aX, aY, angle = self.snapPosToCircle(pos, r)
        # if angle != None:
        #     self._startPos = QPointF(aX, aY)
        #     self._startAngle = self.updateDragHandleLine(event)
        #     self.dummy.updateAngle(self._startAngle, 0)
        #     self.dummy.show()
        # mark the start
        # f = QGraphicsEllipseItem(pX, pY, 2, 2, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0)))
    # end def

    def mouseMoveEvent(self, event):
        m = QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.LeftButton))
        if m.length() < QApplication.startDragDistance():
            return
        p = self.mapToScene(QPointF(event.pos()) - QPointF(self.rect().center()))
        # still need to correct for qgraphicsview translation
        self._parent.setPos(p)

        # eventAngle = self.updateDragHandleLine(event)
        # # Record initial direction before calling getSpanAngle
        # if self._clockwise is None:
        #     self._clockwise = False if eventAngle > self._startAngle else True
        # spanAngle = self.getSpanAngle(eventAngle)
        # self.dummy.updateAngle(self._startAngle, spanAngle)
    # end def

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

        # self.dummy.hide()
        # endAngle = self.updateDragHandleLine(event)
        # spanAngle = self.getSpanAngle(endAngle)
        #
        # if self._startPos != None and self._clockwise != None:
        #     self.parentItem().addSelection(self._startAngle, spanAngle)
        #     self._startPos = self._clockwise = None
        #
        # mark the end
        # x = self._DragHandleLine.x()
        # y = self._DragHandleLine.y()
        # f = QGraphicsEllipseItem(x, y, 6, 6, self)
        # f.setPen(QPen(Qt.NoPen))
        # f.setBrush(QBrush(QColor(204, 0, 0, 128)))
    # end def
# end class
