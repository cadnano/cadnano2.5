"""Summary

Attributes:
    PXI_PP_ITEM_WIDTH (TYPE): Description
    PXI_RECT (TYPE): Description
    TRIANGLE (TYPE): Description
    WEDGE_RECT (TYPE): Description
"""
import numpy as np

from PyQt5.QtCore import QLineF, QObject, QPointF, Qt, QRectF
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QPen, QPainterPath, QColor, QPolygonF
from PyQt5.QtGui import QRadialGradient, QTransform
# from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PyQt5.QtWidgets import QGraphicsEllipseItem

from cadnano.gui.palette import getColorObj, getBrushObj
from cadnano.gui.palette import getPenObj, getNoPen
# from cadnano import util
from . import slicestyles as styles

PXI_PP_ITEM_WIDTH = IW = 2.0  # 1.5
TRIANGLE = QPolygonF()
TRIANGLE.append(QPointF(0, 0))
TRIANGLE.append(QPointF(0.75*IW, 0.5*IW))
TRIANGLE.append(QPointF(0, IW))
TRIANGLE.append(QPointF(0, 0))
# TRIANGLE.translate(-0.75*IW, -0.5*IW)
TRIANGLE.translate(-0.25*IW, -0.5*IW)

PXI_RECT = QRectF(0, 0, IW, IW)
T90, T270 = QTransform(), QTransform()
T90.rotate(90)
T270.rotate(270)
FWDPXI_PP, REVPXI_PP = QPainterPath(), QPainterPath()
FWDPXI_PP.addPolygon(T90.map(TRIANGLE))
REVPXI_PP.addPolygon(T270.map(TRIANGLE))

# FWDPXI_PP.moveTo(-0.5*IW, 0.7*IW)
# FWDPXI_PP.lineTo(0., -0.2*IW)
# FWDPXI_PP.lineTo(0.5*IW, 0.7*IW)
# extra1 = QPainterPath()
# extra1.addEllipse(-0.5*IW, 0.5*IW, IW, 0.4*IW)
# extra2 = QPainterPath()
# extra2.addEllipse(-0.35*IW, 0.5*IW, 0.7*IW, 0.3*IW)
# FWDPXI_PP += extra1
# FWDPXI_PP -= extra2

# REVPXI_PP.moveTo(-0.5*IW, -0.7*IW)
# REVPXI_PP.lineTo(0., 0.2*IW)
# REVPXI_PP.lineTo(0.5*IW, -0.7*IW)
# extra1 = QPainterPath()
# extra1.addEllipse(-0.5*IW, -0.9*IW, IW, 0.4*IW)
# REVPXI_PP += extra1

_RADIUS = styles.SLICE_HELIX_RADIUS
_WEDGE_RECT_GAIN = 0.25
WEDGE_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
WEDGE_RECT = WEDGE_RECT.adjusted(0, 0, _WEDGE_RECT_GAIN, _WEDGE_RECT_GAIN)
_WEDGE_RECT_CENTERPT = WEDGE_RECT.center()


class PropertyWrapperObject(QObject):
    """Summary

    Attributes:
        animations (dict): Description
        bondp2 (TYPE): Description
        item (TYPE): Description
        pen_alpha (TYPE): Description
        rotation (TYPE): Description
    """
    def __init__(self, item):
        """Summary

        Args:
            item (TYPE): Description
        """
        super(PropertyWrapperObject, self).__init__()
        self.item = item
        self.animations = {}

    def __get_bondP2(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.line().p2()

    def __set_bondP2(self, p2):
        """Summary

        Args:
            p2 (TYPE): Description

        Returns:
            TYPE: Description
        """
        p1 = self.item.line().p1()
        line = QLineF(p1.x(), p1.y(), p2.x(), p2.y())
        self.item.setLine(line)

    def __get_rotation(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.rotation()

    def __set_rotation(self, angle):
        """Summary

        Args:
            angle (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.item.setRotation(angle)

    def __get_penAlpha(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.pen().color().alpha()

    def __set_penAlpha(self, alpha):
        """Summary

        Args:
            alpha (TYPE): Description

        Returns:
            TYPE: Description
        """
        pen = QPen(self.item.pen())
        color = QColor(self.item.pen().color())
        color.setAlpha(alpha)
        pen.setColor(color)
        self.item.setPen(pen)

    def saveRef(self, property_name, animation):
        """Summary

        Args:
            property_name (TYPE): Description
            animation (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.animations[property_name] = animation

    def getRef(self, property_name):
        """Summary

        Args:
            property_name (TYPE): Description

        Returns:
            TYPE: Description
        """
        return self.animations.get(property_name)

    def resetAnimations(self):
        """Summary

        Returns:
            TYPE: Description
        """
        for item in self.animations.values():
            item.stop()
            item.deleteLater()
        self.item = None
        self.animations = {}

    bondp2 = pyqtProperty(QPointF, __get_bondP2, __set_bondP2)
    pen_alpha = pyqtProperty(int, __get_penAlpha, __set_penAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class


class Triangle(QGraphicsPathItem):
    """Triangle is used to represent individual bases in sliceview
    VirtualHelixItems. Forward bases (5'–3' into the screen) are drawn with a
    solid color fill color. Reverse bases (5'–3' out of the screen) drawn with
    a stroke ouline and no fill.

    Attributes:
        adapter (TYPE): Description
    """
    def __init__(self, is_fwd, pre_xover_item):
        """
        Args:
            is_fwd (bool): True if forward strand base, False if reverse.
            pre_xover_item (TYPE): Description
        """
        super(Triangle, self).__init__(pre_xover_item)
        color = pre_xover_item.color
        self.adapter = PropertyWrapperObject(self)
        self.setAcceptHoverEvents(True)
        self.setFiltersChildEvents(True)
        self._click_area = click_area = QGraphicsRectItem(PXI_RECT, self)
        click_area.setAcceptHoverEvents(True)
        click_area.setPen(getNoPen())
        click_area.hoverMoveEvent = self.hoverMoveEvent
        if is_fwd:
            # grad = QLinearGradient(0., 0., 0., 1.)
            # grad.setColorAt(0, getColorObj(color))
            # grad.setColorAt(1, Qt.black)
            # self.setBrush(grad)
            self.setBrush(getBrushObj(color, alpha=128))
            self.setPath(FWDPXI_PP)
            self.setPen(getNoPen())
            self._click_area.setPos(-0.5*IW, -0.75*IW)
        else:
            self.setPath(REVPXI_PP)
            self.setPen(getPenObj(color, 0.25, alpha=128))
            # grad = QLinearGradient(0., 0., 0., -1.)
            # grad.setColorAt(1, getColorObj(color))
            # grad.setColorAt(0, Qt.black)
            # self.setPen(getNoPen())
            # self.setBrush(grad)
            self._click_area.setPos(-0.5*IW, -0.25*IW)
        # self.setPos(TRIANGLE_OFFSET)
    # end def
# end class


class PhosBond(QGraphicsLineItem):
    """Summary

    Attributes:
        adapter (TYPE): Description
    """
    def __init__(self, is_fwd, parent=None):
        """Summary

        Args:
            is_fwd (TYPE): Description
            parent (None, optional): Description
        """
        super(PhosBond, self).__init__(parent)
        self.adapter = PropertyWrapperObject(self)
        color = parent.color
        if is_fwd:  # lighter solid
            self.setPen(getPenObj(color, 0.25, alpha=42, capstyle=Qt.RoundCap))
        else:  # darker, dotted
            self.setPen(getPenObj(color, 0.25,
                                  alpha=64,
                                  penstyle=Qt.DotLine,
                                  capstyle=Qt.RoundCap))
    # end def
# end class


class PreXoverItem(QGraphicsRectItem):
    """Summary

    Attributes:
        bond_3p (TYPE): Description
        color (TYPE): Description
        is_active3p (bool): Description
        is_active5p (bool): Description
        is_fwd (TYPE): Description
        item_3p (TYPE): Description
        item_5p (TYPE): Description
        phos_item (TYPE): Description
        pre_xover_item_group (PreXoverItemGroup): Description
        step_idx (int): the base index within the virtual helix
        theta0 (TYPE): Description
    """
    def __init__(self, step_idx, twist_per_base, bases_per_repeat,
                 color, pre_xover_item_group, is_fwd=True):
        """Summary

        Args:
            step_idx (int): the base index within the virtual helix
            twist_per_base (float): (turns per repeat)*360/(base per repeat)
            bases_per_repeat (int): number of bases that will be displayed
            color (str): hexadecimal color code in the form: `#RRGGBB`
            pre_xover_item_group (TYPE): Description
            is_fwd (bool, optional): Description
        """
        super(PreXoverItem, self).__init__(pre_xover_item_group)
        self.step_idx = step_idx
        self.color = color
        self.is_fwd = is_fwd
        self.pre_xover_item_group = pre_xover_item_group
        self.phos_item = Triangle(is_fwd, self)
        self.phos_item.setScale((bases_per_repeat - step_idx)/(2*bases_per_repeat) + 0.5)
        self.theta0 = rot = twist_per_base/2 if is_fwd else -twist_per_base/2
        self.phos_item.setRotation(rot)
        self.is_active5p = self.is_active3p = False
        self.item_5p = None
        self.item_3p = None
        self._default_bond_3p = QLineF()
        self._default_p2_3p = QPointF(0, 0)
        self.bond_3p = PhosBond(is_fwd, self)
        self.setAcceptHoverEvents(True)
        self.setFiltersChildEvents(True)
        self.setRect(self.phos_item.boundingRect())
        self.setPen(getNoPen())
        # self.setPen(getPenObj('#cccccc', 0.1, alpha=128, capstyle=Qt.RoundCap))
    # end def

    ### ACCESSORS ###
    def getInfo(self):
        """
        Returns:
            Tuple: (from_id_num, is_fwd, from_index, to_vh_id_num)
        """
        return (self.pre_xover_item_group.id_num, self.is_fwd, self.step_idx, None)

    def name(self):
        """Summary
        """
        return "%s.%d" % ("r" if self.is_fwd else "f", self.step_idx)
    # end def

    def setBondLineLength(self, value):
        """Summary

        Args:
            value (TYPE): Description
        """
        self._active_p2_3p = QPointF(value, 0)
        self._active_p2_5p = QPointF(value, 0)
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event):
        # print("PreXoverItem press")
        pxig = self.pre_xover_item_group
        pxig.baseNearLine.show()
        self.initStrandFromTriangle()
        # QGraphicsItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        # print("PreXoverItem move", event.pos())
        pxig = self.pre_xover_item_group
        pxig.baseNearestPoint(self.is_fwd, event.scenePos())
        # self.updateStrandFromTriangle()
        # QGraphicsItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        # print("PreXoverItem release")
        pxig = self.pre_xover_item_group
        pxig.baseNearLine.hide()
        self.attemptToCreateStrand()
        # QGraphicsItem.mouseMoveEvent(self, event)

    def hoverEnterEvent(self, event):
        """Handler for hoverEnterEvent.

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        # print("PreXoverItem hoverEnterEvent")
        pxig = self.pre_xover_item_group
        if pxig.is_active:
            pxig.updateModelActiveBaseInfo(self.getInfo())
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): Description
        """
        pxig = self.pre_xover_item_group
        if pxig.is_active:
            pxig.updateModelActiveBaseInfo(None)
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def animate(self, item, property_name, duration, start_value, end_value):
        """Summary

        Args:
            item (TYPE): Description
            property_name (TYPE): Description
            duration (TYPE): Description
            start_value (TYPE): Description
            end_value (TYPE): Description
        """
        if item is not None:
            b_name = property_name.encode('ascii')
            anim = QPropertyAnimation(item.adapter, b_name)
            anim.setDuration(duration)
            anim.setStartValue(start_value)
            anim.setEndValue(end_value)
            anim.start()
            item.adapter.saveRef(property_name, anim)

    def initStrandFromTriangle(self):
        print('initStrandFromTriangle')

    def updateStrandFromTriangle(self):
        print("updateStrandFromTriangle")

    def attemptToCreateStrand(self):
        print("attemptToCreateStrand")

    ### PUBLIC SUPPORT METHODS ###
    def setActive5p(self, is_active, neighbor_item=None):
        """Summary

        Args:
            is_active (TYPE): Description
            neighbor_item (None, optional): Description
        """
        phos = self.phos_item
        bond = self.bond_3p
        if bond is None:
            return
        if not self.is_active5p and is_active:
            self.pre_xover_item_group.virtual_helix_item.setZValue(styles.ZSLICEHELIX + 10)
            self.is_active5p = True
            if neighbor_item is not None:
                n_scene_pos = neighbor_item.scenePos()
                p2 = self.mapFromScene(n_scene_pos)
                bline = bond.line()
                test = QLineF(bline.p1(), p2)
                # angle = test.angleTo(bline) + self.theta0 if self.is_fwd else -bline.angleTo(test) + self.theta0
                angle = -bline.angleTo(test) + self.theta0 if self.is_fwd else test.angleTo(bline) + self.theta0
            else:
                p2 = self._active_p2_3p
                angle = -90 if self.is_fwd else 90
            self.animate(phos, 'rotation', 300, self.theta0, angle)
            self.animate(bond, 'bondp2', 300, self._default_p2_3p, p2)
        elif self.is_active5p:
            self.pre_xover_item_group.virtual_helix_item.setZValue(styles.ZSLICEHELIX)
            self.is_active5p = False
            self.animate(phos, 'rotation', 300, phos.rotation(), self.theta0)
            self.animate(bond, 'bondp2', 300, bond.line().p2(), self._default_p2_3p)
    # end def

    def setActive3p(self, is_active, neighbor_item=None):
        """Summary

        Args:
            is_active (TYPE): Description
            neighbor_item (None, optional): Description

        Returns:
            TYPE: Description
        """
        phos = self.phos_item
        # bond = self.bond_3p
        if not self.is_active3p and is_active:
            self.is_active3p = True
            if self.item_5p is not None:
                self.item_5p.bond_3p.hide()
            # angle = -90 if self.is_fwd else 90
            alpha = 42 if self.is_fwd else 64
            self.animate(phos, 'pen_alpha', 300, alpha, 255)
        elif self.is_active3p:
            self.is_active3p = False
            start_alpha = phos.pen().color().alpha()
            end_alpha = 42 if self.is_fwd else 64
            self.animate(phos, 'pen_alpha', 300, start_alpha, end_alpha)
            if self.item_5p is not None:
                self.item_5p.bond_3p.show()
    # end def

    def set5pItem(self, item_5p):
        """Summary

        Args:
            item_5p (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.item_5p = item_5p
    # end def

    def set3pItem(self, item_3p):
        """Summary

        Args:
            item_3p (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.item_3p = item_3p
        scene_pos3p = item_3p.phos_item.scenePos()
        p1 = QPointF(0, 0)
        p2 = self.mapFromScene(scene_pos3p)
        self._default_p2_3p = p2
        self._default_bond_3p = QLineF(p1, p2)
        self.bond_3p.setLine(self._default_bond_3p)
    # end def

    def destroy(self, scene):
        """Summary

        Args:
            scene (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.phos_item.adapter.resetAnimations()
        self.phos_item.adapter = None
        scene.removeItem(self.phos_item)
        self.phos_item = None
        self.bond_3p.adapter.resetAnimations()
        self.bond_3p.adapter = None
        scene.removeItem(self.bond_3p)
        self.bond_3p = None
        scene.removeItem(self)
# end class


class PreXoverItemGroup(QGraphicsEllipseItem):
    """Summary

    Attributes:
        active_wedge_gizmo (TYPE): Description
        fwd_prexover_items (dict): Description
        HUE_FACTOR (float): Description
        id_num (TYPE): Description
        is_active (TYPE): Description
        model_part (Part): The model part
        rev_prexover_items (dict): Description
        SPIRAL_FACTOR (float): Description
        virtual_helix_item (VirtualHelixItem): Description
    """
    HUE_FACTOR = 1.6
    SPIRAL_FACTOR = 0.4

    def __init__(self, radius, rect, virtual_helix_item, is_active):
        """Summary

        Args:
            radius (TYPE): Description
            rect (TYPE): Description
            virtual_helix_item (VirtualHelixItem): Description
            is_active (TYPE): Description
        """
        super(PreXoverItemGroup, self).__init__(rect, virtual_helix_item)

        self._radius = radius
        self._rect = rect
        self.virtual_helix_item = virtual_helix_item
        self.model_part = virtual_helix_item.part()
        self.id_num = virtual_helix_item.idNum()
        self.is_active = is_active
        self.active_wedge_gizmo = WedgeGizmo(radius, rect, self)
        self.fwd_prexover_items = fwd_pxis = {}
        self.rev_prexover_items = rev_pxis = {}
        self._colors = self._getColors()
        self.addItems()
        self.setPen(getNoPen())
        z = styles.ZPXIGROUP + 10 if is_active else styles.ZPXIGROUP
        self.setZValue(z)
        self.setTransformOriginPoint(rect.center())

        bpr, tpr, eulerZ = virtual_helix_item.getProperty(['bases_per_repeat',
                                                           'turns_per_repeat',
                                                           'eulerZ'])

        self.setRotation(-eulerZ)  # add 180

        # for baseNearestPoint
        fwd_pos, rev_pos = [], []
        step_size = self.virtual_helix_item.getProperty('bases_per_repeat')
        for i in range(step_size):
            fwd_pos.append((fwd_pxis[i].scenePos().x(),
                            fwd_pxis[i].scenePos().y()))
            rev_pos.append((rev_pxis[i].scenePos().x(),
                            rev_pxis[i].scenePos().y()))
        self.fwd_pos_array = np.asarray(fwd_pos)
        self.rev_pos_array = np.asarray(rev_pos)
        self.baseNearLine = QGraphicsLineItem(self)
        self.baseNearLine.setPen(getPenObj("#000000", 0.25, capstyle=Qt.RoundCap))
    # end def

    def mousePressEvent(self, event):
        print("PreXoverGroup press")

    def mouseMoveEvent(self, event):
        print("PreXoverGroup move")

    def mouseReleaseEvent(self, event):
        print("PreXoverGroup release")

    ### ACCESSORS ###
    def partItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.virtual_helix_item.partItem()
    # end def

    def getItem(self, is_fwd, step_idx):
        """Summary

        Args:
            is_fwd (TYPE): Description
            step_idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description
        """
        items = self.fwd_prexover_items if is_fwd else self.rev_prexover_items
        if step_idx in items:
            return items[step_idx]
        else:
            return None
    # end def

    def getItemIdx(self, is_fwd, idx):
        """Summary

        Args:
            is_fwd (TYPE): Description
            idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description
        """
        step_size = self.virtual_helix_item.getProperty('bases_per_repeat')
        return self.getItem(is_fwd, idx % step_size)
    # end def

    ### EVENT HANDLERS ###

    ### PRIVATE SUPPORT METHODS ###
    def _getColors(self):
        """Summary

        Returns:
            TYPE: Description
        """
        step_size = self.virtual_helix_item.getProperty('bases_per_repeat')
        hue_scale = step_size*self.HUE_FACTOR
        return [QColor.fromHsvF(i / hue_scale, 0.75, 0.8).name() for i in range(step_size)]
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def addItems(self):
        """Summary
        """
        radius = self._radius
        step_size, bases_per_turn, tpb, mgroove = self.virtual_helix_item.getAngularProperties()
        # print("TPB", tpb, step_size)
        iw = PXI_PP_ITEM_WIDTH
        spiral_factor = self.SPIRAL_FACTOR
        colors = self._colors
        ctr = self.mapToParent(self._rect).boundingRect().center()
        x = ctr.x() + radius - PXI_PP_ITEM_WIDTH
        y = ctr.y()
        # tpb = -tpb
        # Qt +angle is Clockwise (CW), model +angle is CCW
        mgroove = -mgroove
        fwd_pxis = self.fwd_prexover_items
        rev_pxis = self.rev_prexover_items
        for i in range(step_size):
            inset = i*spiral_factor  # spiral layout
            fwd = PreXoverItem(i, tpb, step_size, colors[i], self, is_fwd=True)
            rev = PreXoverItem(i, tpb, step_size, colors[-1 - i], self, is_fwd=False)
            fwd.setPos(x - inset, y)
            rev.setPos(x - inset, y)
            fwd.setTransformOriginPoint((-radius + iw + inset), 0)
            rev.setTransformOriginPoint((-radius + iw + inset), 0)
            fwd.setRotation(round(i*tpb % 360, 3))
            rev.setRotation(round((i*tpb + mgroove) % 360, 3))
            fwd.setBondLineLength(inset + iw)
            rev.setBondLineLength(inset + iw)
            fwd_pxis[i] = fwd
            rev_pxis[i] = rev

        for i in range(step_size - 1):
            fwd, next_fwd = fwd_pxis[i], fwd_pxis[i + 1]
            j = (step_size - 1) - i
            rev, next_rev = rev_pxis[j], rev_pxis[j - 1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def baseNearestPoint(self, is_fwd, scene_pos):
        """Summary

        Args:
            is_fwd (bool): used to check fwd or rev lists.
            scene_pos (QPointF): scene coordinate position

        Returns:
            PreXoverItem: base nearest to position
        """
        pos_array = self.fwd_pos_array if is_fwd else self.rev_pos_array
        dist_2 = np.sum((pos_array - (scene_pos.x(), scene_pos.y()))**2, axis=1)
        near_idx = np.argmin(dist_2)
        near_pxi = self.fwd_prexover_items[near_idx] if is_fwd else self.rev_prexover_items[near_idx]
        # Draw a line
        p1 = self.mapFromScene(scene_pos.x(), scene_pos.y())
        p2 = self.mapFromScene(near_pxi.scenePos())
        line = QLineF(p1, p2)
        self.baseNearLine.setLine(line)

    def remove(self):
        """Summary
        """
        fpxis = self.fwd_prexover_items
        rpxis = self.rev_prexover_items
        scene = self.scene()
        for i in range(len(fpxis)):
            x = fpxis.pop(i)
            x.destroy(scene)
            x = rpxis.pop(i)
            x.destroy(scene)
        self.virtual_helix_item = None
        self.model_part = None
        scene.removeItem(self.active_wedge_gizmo)
        self.active_wedge_gizmo = None
        scene.removeItem(self)
    # end def

    def updateTurnsPerRepeat(self):
        """Summary
        """
        step_size, bases_per_turn, tpb, mgroove = self.virtual_helix_item.getAngularProperties()
        mgroove = -mgroove
        fpxis = self.fwd_prexover_items
        rpxis = self.rev_prexover_items
        for i in range(step_size):
            fwd = self.fwd_prexover_items[i]
            rev = self.rev_prexover_items[i]
            fwd.setRotation(round((i*tpb) % 360, 3))
            rev.setRotation(round((i*tpb + mgroove) % 360, 3))
        for i in range(step_size - 1):
            fwd, next_fwd = fpxis[i], fpxis[i + 1]
            j = (step_size - 1) - i
            rev, next_rev = rpxis[j], rpxis[j - 1]
            fwd.set3pItem(next_fwd)
            rev.set3pItem(next_rev)
            next_fwd.set5pItem(fwd)
            next_rev.set5pItem(rev)
    # end def

    def partCrossoverSpanAngle(self):
        """
        Returns:
            int: Crossover span angle from Part.
        """
        return self.virtual_helix_item.partCrossoverSpanAngle()

    def updateModelActiveBaseInfo(self, pre_xover_info):
        """Notify model of pre_xover_item hover state.
        """
        self.model_part.setActiveBaseInfo(pre_xover_info)
    # end def
# end class


class WedgeGizmo(QGraphicsPathItem):
    """Summary

    Attributes:
        pre_xover_item_group (PreXoverItemGroup): usually the parent of WG.
    """
    def __init__(self, radius, rect, pre_xover_item_group):
        """parent could be a PreXoverItemGroup or a VirtualHelixItem

        Args:
            radius (TYPE): Description
            rect (TYPE): Description
            pre_xover_item_group (TYPE): Description
        """
        super(WedgeGizmo, self).__init__(pre_xover_item_group)
        self._radius = radius
        self._rect = rect
        self.pre_xover_item_group = pre_xover_item_group
        self.setPen(getNoPen())
        self.setZValue(styles.ZWEDGEGIZMO - 10)
        self._last_params = None

        # # Hack to keep wedge in front
        # scene_pos = self.scenePos()
        # ctr = self.mapToScene(pre_xover_item_group.boundingRect().center())
        # self.setParentItem(pre_xover_item_group.partItem())
        # self.setPos(self.mapFromScene(scene_pos))
        # self.setTransformOriginPoint(self.mapFromScene(ctr))
    # end def

    def showWedge(self, angle, color,
                  extended=False, rev_gradient=False, outline_only=False):
        """Summary

        Args:
            angle (TYPE): Description
            color (TYPE): Description
            extended (bool, optional): Description
            rev_gradient (bool, optional): Description
            outline_only (bool, optional): Description
        """
        # Hack to keep wedge in front
        # self.setRotation(self.pre_xover_item_group.rotation())

        self._last_params = (angle, color, extended, rev_gradient, outline_only)
        radius = self._radius
        span = self.pre_xover_item_group.partCrossoverSpanAngle() / 2
        radius_adjusted = radius + (_WEDGE_RECT_GAIN / 2)

        tip = QPointF(radius_adjusted, radius_adjusted)
        EXT = 1.35 if extended else 1.0

        # print("wtf", tip, pos)
        base_p2 = QPointF(1, 1)

        line0 = QLineF(tip, QPointF(base_p2))
        line1 = QLineF(tip, QPointF(base_p2))
        line2 = QLineF(tip, QPointF(base_p2))

        quad_scale = 1 + (.22*(span - 5) / 55)  # lo+(hi-lo)*(val-min)/(max-min)
        line0.setLength(radius_adjusted * EXT*quad_scale)  # for quadTo control point
        line1.setLength(radius_adjusted * EXT)
        line2.setLength(radius_adjusted * EXT)
        line0.setAngle(angle)
        line1.setAngle(angle - span)
        line2.setAngle(angle + span)

        path = QPainterPath()

        if outline_only:
            self.setPen(getPenObj(color, 0.5, alpha=128, capstyle=Qt.RoundCap))
            path.moveTo(line1.p2())
            path.quadTo(line0.p2(), line2.p2())
        else:
            gradient = QRadialGradient(tip, radius_adjusted * EXT)
            color1 = getColorObj(color, alpha=80)
            color2 = getColorObj(color, alpha=0)
            if rev_gradient:
                color1, color2 = color2, color1

            if extended:
                gradient.setColorAt(0, color1)
                gradient.setColorAt(radius_adjusted / (radius_adjusted * EXT), color1)
                gradient.setColorAt(radius_adjusted / (radius_adjusted * EXT) + 0.01, color2)
                gradient.setColorAt(1, color2)
            else:
                gradient.setColorAt(0, getColorObj(color, alpha=50))
            brush = QBrush(gradient)
            self.setBrush(brush)

            path.moveTo(line1.p1())
            path.lineTo(line1.p2())
            path.quadTo(line0.p2(), line2.p2())
            path.lineTo(line2.p1())

        self.setPath(path)
        self.show()
    # end def

    def deactivate(self):
        """Summary
        """
        self.hide()
        self.setZValue(styles.ZWEDGEGIZMO - 10)
    # end def

    def pointToPreXoverItem(self, pre_xover_item):
        """Summary

        Args:
            pre_xover_item (TYPE): Description
        """
        pxig = self.pre_xover_item_group
        scene_pos = self.scenePos()
        self.setParentItem(pxig)
        temp_point = pxig.mapFromScene(scene_pos)
        self.setPos(temp_point)
        scene_pos = self.scenePos()

        pxi = pre_xover_item
        angle = -pxi.rotation()
        color = pxi.color
        self.setZValue(styles.ZWEDGEGIZMO)
        if pxi.is_fwd:
            self.showWedge(angle, color, extended=True, rev_gradient=True)
        else:
            self.showWedge(angle, color, extended=True, rev_gradient=True)
        part_item = pxig.partItem()
        self.setParentItem(part_item)
        temp_point = part_item.mapFromScene(scene_pos)
        self.setPos(temp_point)
        self.setRotation(pxig.rotation())
    # end def
# end class
