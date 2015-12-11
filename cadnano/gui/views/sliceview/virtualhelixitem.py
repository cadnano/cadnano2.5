from math import sqrt, atan2, degrees, pi

import cadnano.util as util

from PyQt5.QtCore import QLineF, QPointF, Qt, QRectF, QEvent
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsLineItem

from cadnano.enum import LatticeType, Parity, PartType, StrandType
from cadnano.gui.controllers.itemcontrollers.virtualhelixitemcontroller import VirtualHelixItemController
from cadnano.gui.views.abstractitems.abstractvirtualhelixitem import AbstractVirtualHelixItem
from cadnano.virtualhelix import VirtualHelix
from cadnano.gui.palette import getColorObj, getNoPen, getPenObj, getBrushObj, getNoBrush
from . import slicestyles as styles


# set up default, hover, and active drawing styles
_RADIUS = styles.SLICE_HELIX_RADIUS
_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
rect_gain = 0.25
_RECT = _RECT.adjusted(rect_gain, rect_gain, rect_gain, rect_gain)
_FONT = styles.SLICE_NUM_FONT
_ZVALUE = styles.ZSLICEHELIX+3
_OUT_OF_SLICE_BRUSH_DEFAULT = getBrushObj(styles.OUT_OF_SLICE_FILL) # QBrush(QColor(250, 250, 250))
_USE_TEXT_BRUSH = getBrushObj(styles.USE_TEXT_COLOR)

_HOVER_PEN = getPenObj('#ffffff', 128)
_HOVER_BRUSH = getBrushObj('#ffffff', alpha=5)

class VirtualHelixItem(QGraphicsEllipseItem, AbstractVirtualHelixItem):
    """
    The VirtualHelixItem is an individual circle that gets drawn in the SliceView
    as a child of the OrigamiPartItem. Taken as a group, many SliceHelix
    instances make up the crossection of the PlasmidPart. Clicking on a SliceHelix
    adds a VirtualHelix to the PlasmidPart. The SliceHelix then changes appearence
    and paints its corresponding VirtualHelix number.
    """
    def __init__(self, model_virtual_helix, part_item):
        """
        empty_helix_item is a EmptyHelixItem that will act as a QGraphicsItem parent
        """
        super(VirtualHelixItem, self).__init__(parent=part_item)
        self._virtual_helix = model_virtual_helix
        self._controller = VirtualHelixItemController(self, model_virtual_helix)
        self._part_item = part_item
        self.hide()
        x, y = model_virtual_helix.location(part_item.scaleFactor())
        # set position to offset for radius
        self.setPos(x - _RADIUS, y - _RADIUS)

        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(_ZVALUE)
        self.lastMousePressAddedBases = False

        # handle the label specific stuff
        self._label = self.createLabel()
        self.setNumber()
        self._pen1, self._pen2 = (QPen(), QPen())
        self.createArrows()
        self.updateAppearance()


        self.show()

        self._right_mouse_move = False
    # end def

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.RightButton:
    #         self._right_mouse_move = True
    #         self._button_down_pos = event.pos()
    # # end def

    # def mouseMoveEvent(self, event):
    #     if self._right_mouse_move:
    #         p = self.mapToScene(event.pos()) - self._button_down_pos
    #         self._empty_helix_item.setPos(p)
    # # end def

    # def mouseReleaseEvent(self, event):
    #     if self._right_mouse_move and event.button() == Qt.RightButton:
    #         self._right_mouse_move = False
    #         p = self.mapToScene(event.pos()) - self._button_down_pos
    #         self._empty_helix_item.setPos(p)
    #         ehi = self._empty_helix_item
    #         self._virtual_helix.setProperty('ehiX', ehi.mapToScene(0,0).x())
    #         self._virtual_helix.setProperty('ehiY', ehi.mapToScene(0,0).y())
    #         self.getNeighbors()
    # # end def

    def modelColor(self):
        return self.part().getProperty('color')
    # end def

    def updateAppearance(self):
        part_color = self.part().getProperty('color')

        self._USE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)
        self._OUT_OF_SLICE_PEN = getPenObj(part_color, styles.SLICE_HELIX_STROKE_WIDTH)
        self._USE_BRUSH = getBrushObj(part_color, alpha=128)
        self._OUT_OF_SLICE_BRUSH = getBrushObj(part_color, alpha=64)
        self._OUT_OF_SLICE_TEXT_BRUSH = getBrushObj(styles.OUT_OF_SLICE_TEXT_COLOR)

        if self.part().crossSectionType() == LatticeType.HONEYCOMB:
            self._USE_PEN = getPenObj(styles.BLUE_STROKE, styles.SLICE_HELIX_STROKE_WIDTH)
            self._OUT_OF_SLICE_PEN = getPenObj(styles.BLUE_STROKE,\
                                          styles.SLICE_HELIX_STROKE_WIDTH)

        if self.part().partType() == PartType.NUCLEICACIDPART:
            self._OUT_OF_SLICE_BRUSH = _OUT_OF_SLICE_BRUSH_DEFAULT
            # self._USE_BRUSH = getBrushObj(part_color, lighter=180)
            self._USE_BRUSH = getBrushObj(part_color, alpha=150)

        self._label.setBrush(self._OUT_OF_SLICE_TEXT_BRUSH)
        self.setBrush(self._OUT_OF_SLICE_BRUSH)
        self.setPen(self._OUT_OF_SLICE_PEN)
        self.setRect(_RECT)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def virtualHelixNumberChangedSlot(self, virtual_helix):
        """
        receives a signal containing a virtual_helix and the oldNumber
        as a safety check
        """
        self.setNumber()
    # end def

    def virtualHelixPropertyChangedSlot(self, virtual_helix, property_key, new_value):
        if property_key == 'eulerZ':
            # self._prexoveritemgroup.setRotation(new_value)
            scamZ = self._virtual_helix.getProperty('scamZ')
            if scamZ != new_value:
                self._virtual_helix.setProperty('scamZ', new_value)
            active_base_idx = self.part().activeBaseIndex()
            has_fwd, has_rev = virtual_helix.hasStrandAtIdx(active_base_idx)
            self.setActiveSliceView(active_base_idx, has_fwd, has_rev)
        elif property_key == 'scamZ':
            eulerZ = self._virtual_helix.getProperty('eulerZ')
            if eulerZ != new_value:
                self._virtual_helix.setProperty('eulerZ', new_value)
    # end def


    def virtualHelixRemovedSlot(self, virtual_helix):
        self._controller.disconnectSignals()
        self._controller = None
        self._part_item.removeVirtualHelixItem(self)
        self._virtual_helix = None
        self.scene().removeItem(self._label)
        self._label = None
        self.scene().removeItem(self)
    # end def

    def createLabel(self):
        label = QGraphicsSimpleTextItem("%d" % self._virtual_helix.number())
        label.setFont(_FONT)
        label.setZValue(_ZVALUE)
        label.setParentItem(self)
        return label
    # end def

    def createArrows(self):
        rad = _RADIUS
        pen1 = self._pen1
        pen2 = self._pen2
        pen1.setCapStyle(Qt.RoundCap)
        pen2.setCapStyle(Qt.RoundCap)
        pen1.setWidth(3)
        pen2.setWidth(3)
        pen1.setBrush(Qt.gray)
        pen2.setBrush(Qt.lightGray)
        arrow1 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        arrow2 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        #     arrow2 = QGraphicsLineItem(0, rad, rad, rad, self)
        # else:
        #     arrow1 = QGraphicsLineItem(0, rad, rad, rad, self)
        #     arrow2 = QGraphicsLineItem(rad, rad, 2*rad, rad, self)
        arrow1.setTransformOriginPoint(rad, rad)
        arrow2.setTransformOriginPoint(rad, rad)
        arrow1.setZValue(40)
        arrow2.setZValue(40)
        arrow1.setPen(pen1)
        arrow2.setPen(pen2)
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self.arrow1.hide()
        self.arrow2.hide()
    # end def

    def updateFwdArrow(self, idx):
        fwd_strand = self._virtual_helix.scaf(idx)
        if fwd_strand:
            fwd_strand_color = fwd_strand.oligo().getColor()
            scaf_alpha = 230 if fwd_strand.hasXoverAt(idx) else 128
        else:
            fwd_strand_color = '#a0a0a4' #Qt.gray
            scaf_alpha = 26

        fwd_strand_color_obj = getColorObj(fwd_strand_color, alpha=scaf_alpha)
        self._pen1.setBrush(fwd_strand_color_obj)
        self.arrow1.setPen(self._pen1)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        # for some reason rotation is CW and not CCW with increasing angle
        eulerZ = float(self._virtual_helix.getProperty('eulerZ'))
        self.arrow1.setRotation(angle + part._TWIST_OFFSET + eulerZ)

    def updateRevArrow(self, idx):
        rev_strand = self._virtual_helix.stap(idx)
        if rev_strand:
            rev_strand_color = rev_strand.oligo().getColor()
            stap_alpha = 230 if rev_strand.hasXoverAt(idx) else 128
        else:
            rev_strand_color = '#c0c0c0' # Qt.lightGray
            stap_alpha = 26
        rev_strand_color_obj = getColorObj(rev_strand_color, alpha=stap_alpha)
        self._pen2.setBrush(rev_strand_color_obj)
        self.arrow2.setPen(self._pen2)
        part = self.part()
        tpb = part._TWIST_PER_BASE
        angle = idx*tpb
        eulerZ = float(self._virtual_helix.getProperty('eulerZ'))
        self.arrow2.setRotation(angle + part._TWIST_OFFSET + eulerZ + 180)
    # end def

    def setNumber(self):
        """docstring for setNumber"""
        vh = self._virtual_helix
        num = vh.number()
        label = self._label

        if num is not None:
            label.setText("%d" % num)
        else:
            return

        y_val = _RADIUS / 3
        if num < 10:
            label.setPos(_RADIUS / 1.5, y_val)
        elif num < 100:
            label.setPos(_RADIUS / 3, y_val)
        else: # _number >= 100
            label.setPos(0, y_val)
        b_rect = label.boundingRect()
        posx = b_rect.width()/2
        posy = b_rect.height()/2
        label.setPos(_RADIUS-posx, _RADIUS-posy)
    # end def

    def part(self):
        return self._part_item.part()

    def virtualHelix(self):
        return self._virtual_helix
    # end def

    def number(self):
        return self.virtualHelix().number()

    def setActiveSliceView(self, idx, has_fwd, has_rev):
        if has_fwd:
            self.setPen(self._USE_PEN)
            self.setBrush(self._USE_BRUSH)
            self._label.setBrush(_USE_TEXT_BRUSH)
            self.updateFwdArrow(idx)
            self.arrow1.show()
        else:
            self.setPen(self._OUT_OF_SLICE_PEN)
            self.setBrush(self._OUT_OF_SLICE_BRUSH)
            self._label.setBrush(self._OUT_OF_SLICE_TEXT_BRUSH)
            self.arrow1.hide()
        if has_rev:
            self.updateRevArrow(idx)
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

    # def hoverEnterEvent(self, event):
    #     """
    #     If the selection is configured to always select
    #     everything, we don't draw a focus ring around everything,
    #     instead we only draw a focus ring around the hovered obj.
    #     """
    #     # if self.selectAllBehavior():
    #     #     self.setSelected(True)
    #     # forward the event to the empty_helix_item as well
    #     # self._empty_helix_item.hoverEnterEvent(event)
    # # end def

    # def hoverLeaveEvent(self, event):
    #     # if self.selectAllBehavior():
    #     #     self.setSelected(False)
    #     self._empty_helix_item.hoverEnterEvent(event)
    # # end def
# end class

