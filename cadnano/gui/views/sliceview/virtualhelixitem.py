from . import slicestyles as styles
from cadnano.virtualhelix import VirtualHelix
from cadnano.enum import Parity, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController

import cadnano.util as util

from PyQt5.QtCore import QPointF, Qt, QRectF, QEvent

from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem 
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsLineItem

class VirtualHelixItem(QGraphicsEllipseItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the PartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the DNAPart. Clicking on a SliceHelix
    adds a VirtualHelix to the DNAPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    # set up default, hover, and active drawing styles
    _USE_BRUSH = QBrush(styles.ORANGE_FILL)
    _USE_PEN = QPen(styles.ORANGE_STROKE, styles.SLICE_HELIX_STROKE_WIDTH)
    _RADIUS = styles.SLICE_HELIX_RADIUS
    _OUT_OF_SLICE_PEN = QPen(styles.LIGHT_ORANGE_STROKE,\
                         styles.SLICE_HELIX_STROKE_WIDTH)
    _OUT_OF_SLICE_BRUSH = QBrush(styles.LIGHT_ORANGE_FILL)
    _RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
    _FONT = styles.SLICE_NUM_FONT
    _ZVALUE = styles.ZSLICEHELIX+3

    def __init__(self, model_virtual_helix, empty_helix_item):
        """
        empty_helix_item is a EmptyHelixItem that will act as a QGraphicsItem parent
        """
        super(VirtualHelixItem, self).__init__(parent=empty_helix_item)
        self._virtual_helix = model_virtual_helix
        self._empty_helix_item = empty_helix_item
        self.hide()
        # drawing related

        self.isHovered = False
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(self._ZVALUE)
        self.lastMousePressAddedBases = False

        self.setBrush(self._OUT_OF_SLICE_BRUSH)
        self.setPen(self._OUT_OF_SLICE_PEN)
        self.setRect(self._RECT)

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self._pen1, self._pen2 = (QPen(), QPen())
        self.createArrows()

        self._controller = VirtualHelixItemController(self, model_virtual_helix)

        self.show()
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def virtualHelixNumberChangedSlot(self, virtualHelix):
        """
        receives a signal containing a virtualHelix and the oldNumber 
        as a safety check
        """
        self.setNumber()
    # end def

    def virtualHelixRemovedSlot(self, virtualHelix):
        self._controller.disconnectSignals()
        self._controller = None
        self._empty_helix_item.setNotHovered()
        self._virtual_helix = None
        self._empty_helix_item = None
        self.scene().removeItem(self._label)
        self._label = None
        self.scene().removeItem(self)
    # end def

    def strandAddedSlot(self, sender, strand):
        pass
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtual_helix.number())
        label.setFont(self._FONT)
        label.setZValue(self._ZVALUE)
        label.setParentItem(self)
        return label
    # end def

    def createArrows(self):
        rad = self._RADIUS
        pen1 = self._pen1
        pen2 = self._pen2
        pen1.setWidth(3)
        pen2.setWidth(3)
        pen1.setBrush(Qt.gray)
        pen2.setBrush(Qt.lightGray)
        if self._virtual_helix.isEvenParity():
            arrow1 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
            arrow2 = QGraphicsLineItem(0, rad, rad, rad, self)
        else:
            arrow1 = QGraphicsLineItem(0, rad, rad, rad, self)
            arrow2 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        arrow1.setTransformOriginPoint(rad, rad)
        arrow2.setTransformOriginPoint(rad, rad)
        arrow1.setZValue(400)
        arrow2.setZValue(400)
        arrow1.setPen(pen1)
        arrow2.setPen(pen2)
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self.arrow1.hide()
        self.arrow2.hide()
    # end def

    def updateScafArrow(self, idx):
        scafStrand = self._virtual_helix.scaf(idx)
        if scafStrand:
            scafStrandColor = QColor(scafStrand.oligo().color())
            scafAlpha = 0.9 if scafStrand.hasXoverAt(idx) else 0.3
        else:
            scafStrandColor = QColor(Qt.gray)
            scafAlpha = 0.1
        scafStrandColor.setAlphaF(scafAlpha)
        self._pen1.setBrush(scafStrandColor)
        self.arrow1.setPen(self._pen1)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        # for some reason rotation is CW and not CCW with increasing angle
        self.arrow1.setRotation(angle + part._TWIST_OFFSET)

    def updateStapArrow(self, idx):
        stapStrand = self._virtual_helix.stap(idx)
        if stapStrand:
            stapStrandColor = QColor(stapStrand.oligo().color()) 
            stapAlpha = 0.9 if stapStrand.hasXoverAt(idx) else 0.3
        else:
            stapStrandColor = QColor(Qt.lightGray)
            stapAlpha = 0.1
        stapStrandColor.setAlphaF(stapAlpha)
        self._pen2.setBrush(stapStrandColor)
        self.arrow2.setPen(self._pen2)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        self.arrow2.setRotation(angle + part._TWIST_OFFSET)
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtual_helix
        num = vh.number()
        label = self._label
        radius = self._RADIUS

        if num != None:
            label.setText("%d" % num)
        else:
            return

        y_val = radius / 3
        if num < 10:
            label.setPos(radius / 1.5, y_val)
        elif num < 100:
            label.setPos(radius / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        b_rect = label.boundingRect()
        posx = b_rect.width()/2
        posy = b_rect.height()/2
        label.setPos(radius-posx, radius-posy)
    # end def

    def part(self):
        return self._empty_helix_item.part()

    def virtualHelix(self):
        return self._virtual_helix
    # end def

    def number(self):
        return self.virtualHelix().number()

    def setActiveSliceView(self, idx, has_scaf, has_stap):
        if has_scaf:
            self.setPen(self._USE_PEN)
            self.setBrush(self._USE_BRUSH)
            self.updateScafArrow(idx)
            self.arrow1.show()
        else:
            self.setPen(self._OUT_OF_SLICE_PEN)
            self.setBrush(self._OUT_OF_SLICE_BRUSH)
            self.arrow1.hide()
        if has_stap:
            self.updateStapArrow(idx)
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

    # def mousePressEvent(self, event):
    #     action = self.decideAction(event.modifiers())
    #     action(self)
    #     self.dragSessionAction = action
    # 
    # def mouseMoveEvent(self, event):
    #     parent = self._helixItem
    #     posInParent = parent.mapFromItem(self, QPointF(event.pos()))
    #     # Qt doesn't have any way to ask for graphicsitem(s) at a
    #     # particular position but it *can* do intersections, so we
    #     # just use those instead
    #     parent.probe.setPos(posInParent)
    #     for ci in parent.probe.collidingItems():
    #         if isinstance(ci, SliceHelix):
    #             self.dragSessionAction(ci)
    # # end def

    # def mouseReleaseEvent(self, event):
    #     self.part().needsFittingToView.emit()

    # def decideAction(self, modifiers):
    #     """ On mouse press, an action (add scaffold at the active slice, add
    #     segment at the active slice, or create virtualhelix if missing) is
    #     decided upon and will be applied to all other slices happened across by
    #     mouseMoveEvent. The action is returned from this method in the form of a
    #     callable function."""
    #     vh = self.virtualHelix()
    #     if vh == None: return SliceHelix.addVHIfMissing
    #     idx = self.part().activeSlice()
    #     if modifiers & Qt.ShiftModifier:
    #         if vh.stap().get(idx) == None:
    #             return SliceHelix.addStapAtActiveSliceIfMissing
    #         else:
    #             return SliceHelix.nop
    #     if vh.scaf().get(idx) == None:
    #         return SliceHelix.addScafAtActiveSliceIfMissing
    #     return SliceHelix.nop
    # 
    # def nop(self):
    #     pass
