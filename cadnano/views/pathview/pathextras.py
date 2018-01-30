# -*- coding: utf-8 -*-
"""Summary

Attributes:
    BASE_RECT (TYPE): Description
    BASE_WIDTH (TYPE): Description
    KEYINPUT_ACTIVE_FLAG (TYPE): Description
    PHOS_ITEM_WIDTH (TYPE): Description
    PROX_ALPHA (int): Description
    T180 (TYPE): Description
    TRIANGLE (TYPE): Description
"""
from math import floor

from PyQt5.QtCore import QObject, QPointF, QRectF, Qt
from PyQt5.QtCore import QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QBrush, QColor, QPainterPath
from PyQt5.QtGui import QPolygonF, QTransform
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem

from cadnano import util
from cadnano.gui.palette import getNoPen, getPenObj, newPenObj
from cadnano.gui.palette import getBrushObj, getNoBrush
from cadnano.proxies.cnenum import Axis, HandleType, StrandType
from cadnano.views.resizehandles import ResizeHandleGroup
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

KEYINPUT_ACTIVE_FLAG = QGraphicsItem.ItemIsFocusable

PROX_ALPHA = 64

class PropertyWrapperObject(QObject):
    """Summary

    Attributes:
        animations (dict): Description
        brush_alpha (TYPE): Description
        item (TYPE): Description
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

    def __get_brushAlpha(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.item.brush().color().alpha()

    def __set_brushAlpha(self, alpha):
        """Summary

        Args:
            alpha (TYPE): Description

        Returns:
            TYPE: Description
        """
        brush = QBrush(self.item.brush())
        color = QColor(brush.color())
        color.setAlpha(alpha)
        self.item.setBrush(QBrush(color))

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

    def destroy(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self.item = None
        self.animations = None
        self.deleteLater()

    def resetAnimations(self):
        """Summary

        Returns:
            TYPE: Description
        """
        for item in self.animations.values():
            item.stop()
            item.deleteLater()
            item = None
        self.animations = {}

    brush_alpha = pyqtProperty(int, __get_brushAlpha, __set_brushAlpha)
    rotation = pyqtProperty(float, __get_rotation, __set_rotation)
# end class


class Triangle(QGraphicsPathItem):
    """Summary

    Attributes:
        adapter (TYPE): Description
    """

    def __init__(self, painter_path, parent=None):
        """Summary

        Args:
            painter_path (TYPE): Description
            parent (None, optional): Description
        """
        super(QGraphicsPathItem, self).__init__(painter_path, parent)
        self.adapter = PropertyWrapperObject(self)
    # end def
# end class


class PreXoverLabel(QGraphicsSimpleTextItem):
    """Summary

    Attributes:
        is_fwd (TYPE): Description
    """
    _XO_FONT = styles.XOVER_LABEL_FONT
    _XO_BOLD = styles.XOVER_LABEL_FONT_BOLD
    _FM = QFontMetrics(_XO_FONT)

    def __init__(self, is_fwd, pre_xover_item):
        """Summary

        Args:
            is_fwd (TYPE): Description
            color (TYPE): Description
            pre_xover_item (TYPE): Description
        """
        super(QGraphicsSimpleTextItem, self).__init__(pre_xover_item)
        self.is_fwd = is_fwd
        self._tbr = None
        self._outline = QGraphicsRectItem(self)
        self.setFont(self._XO_FONT)
        self.setBrush(getBrushObj('#666666'))
    # end def

    def resetItem(self, is_fwd, color):
        """Summary

        Args:
            is_fwd (TYPE): Description
            color (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.resetTransform()
        self.is_fwd = is_fwd
        self.color = color
    # end def

    def setTextAndStyle(self, text, outline=False):
        """Summary

        Args:
            text (TYPE): Description
            outline (bool, optional): Description

        Returns:
            TYPE: Description
        """
        str_txt = str(text)
        self._tbr = tBR = self._FM.tightBoundingRect(str_txt)
        half_label_H = tBR.height() / 2.0
        half_label_W = tBR.width() / 2.0

        labelX = BASE_WIDTH/2.0 - half_label_W
        if str_txt == '1':  # adjust for the number one
            labelX -= tBR.width()

        labelY = half_label_H if self.is_fwd else (BASE_WIDTH - tBR.height())/2

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

def _createPreXoverPainterPath(elements, end_poly=None, is_fwd=True):
    path = QPainterPath()

    next_pt = None
    for element in elements:
        start_pt = element[0]
        path.moveTo(start_pt)
        for next_pt in element[1:]:
            path.lineTo(next_pt)

    if end_poly is not None:
        h = end_poly.boundingRect().height()/2
        xoffset = -h if is_fwd else h
        w = end_poly.boundingRect().width()
        yoffset = w if is_fwd else -w
        angle = -90 if is_fwd else 90
        T = QTransform()
        T.translate(next_pt.x()+xoffset, next_pt.y()+yoffset)
        T.rotate(angle)
        path.addPolygon(T.map(end_poly))
    return path
# end def


# create hash marks QPainterPaths only once
LO_X = BASE_RECT.left()
HI_X = BASE_RECT.right()
BOT_Y = BASE_RECT.bottom()+BASE_WIDTH/5
TOP_Y = BASE_RECT.top()-BASE_WIDTH/5
WIDTH_X = BASE_WIDTH/3
HEIGHT_Y = BASE_WIDTH/3

FWD_L1 = QPointF(LO_X, BOT_Y)
FWD_L2 = QPointF(LO_X+WIDTH_X, BOT_Y)
FWD_L3 = QPointF(LO_X+WIDTH_X, BOT_Y-HEIGHT_Y)
FWD_H1 = QPointF(HI_X, BOT_Y)
FWD_H2 = QPointF(HI_X-WIDTH_X, BOT_Y)
FWD_H3 = QPointF(HI_X-WIDTH_X, BOT_Y-HEIGHT_Y)
REV_L1 = QPointF(LO_X, TOP_Y)
REV_L2 = QPointF(LO_X+WIDTH_X, TOP_Y)
REV_L3 = QPointF(LO_X+WIDTH_X, TOP_Y+HEIGHT_Y)
REV_H1 = QPointF(HI_X, TOP_Y)
REV_H2 = QPointF(HI_X-WIDTH_X, TOP_Y)
REV_H3 = QPointF(HI_X-WIDTH_X, TOP_Y+HEIGHT_Y)

_FWD_LO_PTS = [[FWD_L1, FWD_L2, FWD_L3]]
_FWD_HI_PTS = [[FWD_H1, FWD_H2, FWD_H3]]
_REV_LO_PTS = [[REV_L1, REV_L2, REV_L3]]
_REV_HI_PTS = [[REV_H1, REV_H2, REV_H3]]
_FWD_DUAL_PTS = [[FWD_H1, FWD_H2, FWD_H3], [FWD_L1, FWD_L2, FWD_L3]]
_REV_DUAL_PTS = [[REV_H1, REV_H2, REV_H3], [REV_L1, REV_L2, REV_L3]]

END_3P_WIDTH = styles.PREXOVER_STROKE_WIDTH*2
END_3P = QPolygonF()
END_3P.append(QPointF(0, 0))
END_3P.append(QPointF(0.75 * END_3P_WIDTH, 0.5 * END_3P_WIDTH))
END_3P.append(QPointF(0, END_3P_WIDTH))
END_3P.append(QPointF(0, 0))

_FWD_LO_PATH = _createPreXoverPainterPath(_FWD_LO_PTS, end_poly=END_3P, is_fwd=True)
_FWD_HI_PATH = _createPreXoverPainterPath(_FWD_HI_PTS)
_REV_LO_PATH = _createPreXoverPainterPath(_REV_LO_PTS)
_REV_HI_PATH = _createPreXoverPainterPath(_REV_HI_PTS, end_poly=END_3P, is_fwd=False)
_FWD_DUAL_PATH = _createPreXoverPainterPath(_FWD_DUAL_PTS, end_poly=END_3P, is_fwd=True)
_REV_DUAL_PATH = _createPreXoverPainterPath(_REV_DUAL_PTS, end_poly=END_3P, is_fwd=False)

EMPTY_COL = '#cccccc'

_X_SCALE = styles.PATH_XOVER_LINE_SCALE_X  # control point x constant
_Y_SCALE = styles.PATH_XOVER_LINE_SCALE_Y  # control point y constant


class PreXoverItem(QGraphicsRectItem):
    """A PreXoverItem exists between a single 'from' VirtualHelixItem index
    and zero or more 'to' VirtualHelixItem Indices

    Attributes:
        adapter (:obj:`PropertyWrapperObject`): Description
        idx (int): the base index within the virtual helix
        is_fwd (bool): is this a forward strand?
        prexoveritem_manager (:obj:`PreXoverManager`): Manager of the PreXoverItems
        to_vh_id_num (int): Virtual Helix number this Xover point might connect to
    """
    FILTER_NAME = "xover"

    def __init__(self,  from_virtual_helix_item,
                        is_fwd,
                        from_index,
                        nearby_idxs,
                        to_vh_id_num,
                        prexoveritem_manager):
        """Summary

        Args:
            from_virtual_helix_item (cadnano.views.pathview.virtualhelixitem.VirtualHelixItem): Description
            is_fwd (bool): is this a forward strand?
            from_index (int): index of the Virtual Helix this xover is coming from
            to_vh_id_num (int): Virtual Helix number this Xover point might connect to
            prexoveritem_manager (:obj:`PreXoverManager`): Manager of the PreXoverItems
        """
        super(QGraphicsRectItem, self).__init__(BASE_RECT, from_virtual_helix_item)
        self.adapter = PropertyWrapperObject(self)
        self._tick_marks = QGraphicsPathItem(self)
        self._tick_marks.setAcceptHoverEvents(True)
        self._bond_item = QGraphicsPathItem(self)
        self._bond_item.hide()
        self._label = PreXoverLabel(is_fwd, self)
        self._path = QGraphicsPathItem()
        self.setZValue(styles.ZPREXOVERITEM)
        self.setPen(getNoPen())
        self.resetItem(from_virtual_helix_item, is_fwd, from_index, nearby_idxs, to_vh_id_num, prexoveritem_manager)

        self._getActiveTool = from_virtual_helix_item.viewroot().manager.activeToolGetter
    # end def

    def shutdown(self):
        """Summary
        """
        self.setBrush(getNoBrush())
        self.to_vh_id_num = None
        self.adapter.resetAnimations()
        self.setAcceptHoverEvents(False)
        self.hide()
    # end def

    def resetItem(self, from_virtual_helix_item, is_fwd, from_index, nearby_idxs,
                  to_vh_id_num, prexoveritem_manager):
        """Update this pooled PreXoverItem with current info.
        Called by PreXoverManager.

        Args:
            from_virtual_helix_item (cadnano.views.pathview.virtualhelixitem.VirtualHelixItem): the associated vh_item
            is_fwd (bool): True if associated with fwd strand, False if rev strand
            from_index (int): idx of associated vh
            to_vh_id_num (int): id_num of the other vh
            prexoveritem_manager (cadnano.views.pathview.prexoermanager.PreXoverManager): the manager
        """
        # to_vh_item = from_virtual_helix_item.partItem().idToVirtualHelixItem(to_vh_id_num)
        self.setParentItem(from_virtual_helix_item)
        # self.setParentItem(to_vh_item)
        self.resetTransform()
        self._id_num = from_virtual_helix_item.idNum()
        self._model_vh = from_virtual_helix_item.cnModel()
        self.idx = from_index
        self.is_low = False
        self.is_high = False
        self.nearby_idxs = nearby_idxs
        self.is_fwd = is_fwd
        self.color = None
        self.is3p = None
        self.enter_pos = None
        self.exit_pos = None
        self.to_vh_id_num = to_vh_id_num
        self._label_txt = None
        self.prexoveritem_manager = prexoveritem_manager

        # todo: check here if xover present and disable
        result = self.setPathAppearance(from_virtual_helix_item)

        if result:
            self.setBrush(getNoBrush())
            if is_fwd:
                self.setPos(from_index*BASE_WIDTH, -BASE_WIDTH - 0.1*BASE_WIDTH)
            else:
                self.setPos(from_index*BASE_WIDTH, 2*BASE_WIDTH)
            self.show()
            # label
            self._label_txt = lbt = None if to_vh_id_num is None else str(to_vh_id_num)
            self._label.resetItem(is_fwd, self.color)
            self.setLabel(text=lbt)

            # bond line
            bonditem = self._bond_item
            bonditem.setPen(getPenObj(  self.color,
                                        styles.PREXOVER_STROKE_WIDTH,
                                        penstyle=Qt.DotLine))
            bonditem.hide()
    # end def

    def setPathAppearance(self, from_virtual_helix_item):
            """Sets the PainterPath according to the index (low = Left, high = Right)
            and strand position (top = Up, bottom = Down).

            Args:
                from_virtual_helix_item (:obj:`VirtualHelixItem`):
            """
            part = self._model_vh.part()
            idx = self.idx
            is_fwd = self.is_fwd
            id_num = self._id_num
            strand_type = StrandType.FWD if is_fwd else StrandType.REV

            # relative position info
            bpr = from_virtual_helix_item.getProperty('bases_per_repeat')
            self.is_low = is_low = idx+1 in self.nearby_idxs or (idx+1) % bpr in self.nearby_idxs
            self.is_high = is_high = idx-1 in self.nearby_idxs or (idx-1) % bpr in self.nearby_idxs

            # check strand for xover and color
            if part.hasStrandAtIdx(id_num, idx)[strand_type]:
                strand = part.getStrand(self.is_fwd, id_num, idx)
                if strand.hasXoverAt(idx):
                    return False
                self.color = strand.getColor() if strand is not None else EMPTY_COL
            else:
                self.color = EMPTY_COL

            if is_low and is_high:
                path = (_FWD_DUAL_PATH, _REV_DUAL_PATH)[strand_type]
                raise NotImplementedError("Dual xovers not yet supported")
            elif is_low:
                path = (_FWD_LO_PATH, _REV_LO_PATH)[strand_type]
                self.is3p = True if is_fwd else False
                self.enter_pos = _FWD_LO_PTS[0][-1] if is_fwd else _REV_LO_PTS[0][-1]
                self.exit_pos = _FWD_LO_PTS[0][-1] if is_fwd else _REV_LO_PTS[0][-1]
            elif is_high:
                path = (_FWD_HI_PATH, _REV_HI_PATH)[strand_type]
                self.is3p = False if is_fwd else True
                self.enter_pos = _FWD_HI_PTS[0][-1] if is_fwd else _REV_HI_PTS[0][-1]
                self.exit_pos = _FWD_HI_PTS[0][-1] if is_fwd else _REV_HI_PTS[0][-1]
            else:
                # print("unpaired PreXoverItem at {}[{}]".format(self._id_num, self.idx), self.nearby_idxs)
                return False
            self._tick_marks.setPen(getPenObj(  self.color,
                                                styles.PREXOVER_STROKE_WIDTH,
                                                capstyle=Qt.FlatCap,
                                                joinstyle=Qt.RoundJoin))
            self._tick_marks.setPath(path)
            self._tick_marks.show()
            return True
    # end def

    ### ACCESSORS ###
    def color(self):
        """The PreXoverItem's color, derived from the associated strand's oligo.

        Returns:
            str: color in hex code
        """
        return self.color

    def getInfo(self):
        """
        Returns:
            Tuple: (from_id_num, is_fwd, from_index, to_vh_id_num)
        """
        return (self._id_num, self.is_fwd, self.idx, self.to_vh_id_num)

    def remove(self):
        """Removes animation adapter, label, bond_item, and this item from scene.
        """
        scene = self.scene()
        self.adapter.destroy()
        if scene:
            scene.removeItem(self._label)
            self._label = None
            scene.removeItem(self._bond_item)
            self._bond_item = None
            self.adapter.resetAnimations()
            self.adapter = None
            scene.removeItem(self)
    # end defS

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        """Only if enableActive(True) is called hover and key events disabled by default

        Args:
            event (QGraphicsSceneHoverEvent): the hover event
        """
        if self._getActiveTool().methodPrefix() != "selectTool":
            return
        self.setFocus(Qt.MouseFocusReason)
        self.prexoveritem_manager.updateModelActiveBaseInfo(self.getInfo())
        self.setActiveHovered(True)
        status_string = "%d[%d]" % (self._id_num, self.idx)
        self.parentItem().window().statusBar().showMessage(status_string)
        return QGraphicsItem.hoverEnterEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneHoverEvent): the hover event
        """
        self.prexoveritem_manager.updateModelActiveBaseInfo(None)
        self.setActiveHovered(False)
        self.clearFocus()
        self.parentItem().window().statusBar().showMessage("")
        return QGraphicsItem.hoverLeaveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """TODO: NEED TO ADD FILTER FOR A CLICK ON THE 3' MOST END OF THE XOVER TO DISALLOW OR HANDLE DIFFERENTLY
        """
        viewroot = self.parentItem().viewroot()
        current_filter_set = viewroot.selectionFilterSet()
        if  (self._getActiveTool().methodPrefix() != "selectTool" or
            (self.FILTER_NAME not in current_filter_set) ):
            return

        part = self._model_vh.part()
        is_fwd = self.is_fwd

        if self.is3p:
            strand5p = part.getStrand(is_fwd, self._id_num, self.idx)
            strand3p = part.getStrand(not is_fwd, self.to_vh_id_num, self.idx)
        else:
            strand5p = part.getStrand(not is_fwd, self.to_vh_id_num, self.idx)
            strand3p = part.getStrand(is_fwd, self._id_num, self.idx)

        if strand5p is None or strand3p is None:
            return

        # print(strand3p, strand5p)
        part.createXover(strand5p, self.idx, strand3p, self.idx)

        nkey = (self.to_vh_id_num, not is_fwd, self.idx)
        npxi = self.prexoveritem_manager.neighbor_prexover_items.get(nkey, None)
        if npxi:
            npxi.shutdown()
        self.shutdown()

        part.setActiveVirtualHelix(self._id_num, is_fwd, self.idx)
        # self.prexoveritem_manager.handlePreXoverClick(self)

    def keyPressEvent(self, event):
        """Summary

        Args:
            event (TYPE): Description
        """
        self.prexoveritem_manager.handlePreXoverKeyPress(event.key())
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def setLabel(self, text=None, outline=False):
        """Summary

        Args:
            text (None, optional): Description
            outline (bool, optional): Description
        """
        if text:
            self._label.setTextAndStyle(text=text, outline=outline)
            self._label.show()
        else:
            self._label.hide()
    # end def

    def animate(self, item, property_name, duration, start_value, end_value):
        """Summary

        Args:
            item (TYPE): Description
            property_name (TYPE): Description
            duration (TYPE): Description
            start_value (TYPE): Description
            end_value (TYPE): Description
        """
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

    def setActiveHovered(self, is_active):
        """Rotate phosphate Triangle if `self.to_vh_id_num` is not `None`

        Args:
            is_active (bool): whether or not the PreXoverItem is parented to the
                active VirtualHelixItem
        """
        pass
    # end def

    def enableActive(self, is_active, to_vh_id_num=None):
        """Call on PreXoverItems created on the active VirtualHelixItem

        Args:
            is_active (TYPE): Description
            to_vh_id_num (None, optional): Description
        """
        if is_active:
            self.to_vh_id_num = to_vh_id_num
            self.setAcceptHoverEvents(True)
            if to_vh_id_num is None:
                self.setLabel(text=None)
            else:
                self.setLabel(text=str(to_vh_id_num))
        else:
            self.setBrush(getNoBrush())
            self.setAcceptHoverEvents(False)

    def activateNeighbor(self, active_prexoveritem, shortcut=None):
        """
        Draws a quad line starting from the item5p to the item3p.
        To be called with whatever the active_prexoveritem is for the parts `active_base`.

        Args:
            active_prexoveritem (TYPE): Description
            shortcut (None, optional): Description
        """
        if self._getActiveTool().methodPrefix() != "selectTool":
            return

        if self.is3p and not active_prexoveritem.is3p:
            item5p = active_prexoveritem
            item3p = self
        elif not self.is3p and active_prexoveritem.is3p:
            item5p = self
            item3p = active_prexoveritem
        else:
            return

        same_parity = self.is_fwd == active_prexoveritem.is_fwd

        p1 = item5p._tick_marks.scenePos() + item5p.exit_pos
        p2 = item3p._tick_marks.scenePos() + item3p.exit_pos

        c1 = QPointF()

        # case 1: same parity
        if same_parity:
            dy = abs(p2.y() - p1.y())
            c1.setX(p1.x() + _X_SCALE * dy)
            c1.setY(0.5 * (p1.y() + p2.y()))
        # case 2: different parity
        else:
            if item3p.is_fwd:
                c1.setX(p1.x() - _X_SCALE * abs(p2.y() - p1.y()))
            else:
                c1.setX(p1.x() + _X_SCALE * abs(p2.y() - p1.y()))
            c1.setY(0.5 * (p1.y() + p2.y()))

        pp = QPainterPath()
        pp.moveTo(self._tick_marks.mapFromScene(p1))
        pp.quadTo(self._tick_marks.mapFromScene(c1),
                  self._tick_marks.mapFromScene(p2))
        # pp.cubicTo(c1, c2, self._tick_marks.mapFromScene(p2))
        self._bond_item.setPath(pp)
        self._bond_item.show()
    # end def

    def deactivateNeighbor(self):
        """Summary
        """
        if self.isVisible():
            self._bond_item.hide()
            self.setLabel(text=self._label_txt)
    # end def
# end class


class PathWorkplaneOutline(QGraphicsRectItem):
    """
    """
    def __init__(self, parent=None):
        """
        Args:
            parent (:obj:`QGraphicsItem`, optional): default None
        """
        super(PathWorkplaneOutline, self).__init__(parent)
        self.setPen(getNoPen())
        self._path = QGraphicsPathItem(self)
        self._path.setBrush(getNoBrush())
        self._path.setPen(newPenObj(styles.BLUE_STROKE, 0))
    # end def

    def updateAppearance(self):
        tl = self.rect().topLeft()
        tl1 = tl + QPointF(0, -BASE_WIDTH/2)
        tl2 = tl + QPointF(BASE_WIDTH/2, -BASE_WIDTH/2)
        bl = self.rect().bottomLeft()
        bl1 = bl + QPointF(0, BASE_WIDTH/2)
        bl2 = bl + QPointF(BASE_WIDTH/2, BASE_WIDTH/2)
        tr = self.rect().topRight()
        tr1 = tr + QPointF(0, -BASE_WIDTH/2)
        tr2 = tr + QPointF(-BASE_WIDTH/2, -BASE_WIDTH/2)
        br = self.rect().bottomRight()
        br1 = br + QPointF(0, BASE_WIDTH/2)
        br2 = br + QPointF(-BASE_WIDTH/2, BASE_WIDTH/2)
        pp = QPainterPath()
        pp.moveTo(tl2)
        pp.lineTo(tl1)
        pp.lineTo(bl1)
        pp.lineTo(bl2)
        pp.moveTo(tr2)
        pp.lineTo(tr1)
        pp.lineTo(br1)
        pp.lineTo(br2)
        self._path.setPath(pp)
    # end def
# end class


class PathWorkplaneItem(QGraphicsRectItem):
    """Draws the rectangle to indicate the current Workplane, i.e. the
    region of part bases affected by certain actions in other views."""
    _BOUNDING_RECT_PADDING = 0
    _HANDLE_SIZE = 6
    _MIN_WIDTH = 3

    def __init__(self, model_part, part_item):
        """
        Args:
            model_part (:obj:`Part`):
            part_item (:obj:`AbstractPartItem`):
        """
        super(QGraphicsRectItem, self).__init__(BASE_RECT, part_item.proxy())
        self.setAcceptHoverEvents(True)
        self.setBrush(getBrushObj(styles.BLUE_FILL, alpha=12))
        self.setPen(getNoPen())
        self.setZValue(styles.ZWORKPLANE)

        self._model_part = model_part
        self._part_item = part_item
        self._idx_low, self._idx_high = model_part.getProperty('workplane_idxs')
        self._low_drag_bound = 0  # idx, not pos
        self._high_drag_bound = model_part.getProperty('max_vhelix_length')  # idx, not pos
        self._moving_via_handle = False

        self.outline = PathWorkplaneOutline(self)
        self.resize_handle_group = ResizeHandleGroup(self.rect(),
                                                     self._HANDLE_SIZE,
                                                     styles.BLUE_STROKE,
                                                     True,
                                                     HandleType.LEFT | HandleType.RIGHT,
                                                     self,
                                                     translates_in=Axis.X)

        # Minimum size hint (darker internal rect, visible during resizing)
        self.model_bounds_hint = m_b_h = QGraphicsRectItem(self)
        m_b_h.setBrush(getBrushObj(styles.BLUE_FILL, alpha=64))
        m_b_h.setPen(getNoPen())
        m_b_h.hide()

        # Low and high idx labels
        self.resize_handle_group.updateText(HandleType.LEFT, self._idx_low)
        self.resize_handle_group.updateText(HandleType.RIGHT, self._idx_high)
    # end def

    def getModelMinBounds(self, handle_type=None):
        """Resize bounds in form of Qt position, scaled from model."""
        # TODO: fix bug preventing dragging in imported files
        if handle_type and handle_type & HandleType.LEFT:
            xTL = (self._idx_high-self._MIN_WIDTH)*BASE_WIDTH
            xBR = self._idx_high*BASE_WIDTH
        elif handle_type and handle_type & HandleType.RIGHT:
            xTL = (self._idx_low+self._MIN_WIDTH)*BASE_WIDTH
            xBR = (self._idx_low)*BASE_WIDTH
        else:  # default to HandleType.RIGHT behavior for all types
            print("No HandleType?")
            xTL = 0
            xBR = self._high_drag_bound*BASE_WIDTH
        yTL = self._part_item._vh_rect.top()
        yBR = self._part_item._vh_rect.bottom()-BASE_WIDTH*3
        return xTL, yTL, xBR, yBR
    # end def

    def setMovable(self, is_movable):
        """
        Args:
            is_movable (bool): is this movable?
        """
        self._moving_via_handle = is_movable
        # self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
    # end def

    def finishDrag(self):
        """Set the workplane size in the model"""
        pass
        # pos = self.pos()
        # position = pos.x(), pos.y()
        # view_name = self._viewroot.name
        # self._model_part.changeInstanceProperty(self._model_instance, view_name, 'position', position)
    # end def

    def reconfigureRect(self, top_left, bottom_right, finish=False):
        """Update the workplane rect to draw from top_left to bottom_right,
        snapping the x values to the nearest base width. Updates the outline
        and resize handles.

        Args:
            top_left (tuple): topLeft (x, y)
            bottom_right (tuple): bottomRight (x, y)

        Returns:
            QRectF: the new rect.
        """
        if top_left:
            xTL = max(top_left[0], self._low_drag_bound)
            xTL = xTL - (xTL % BASE_WIDTH)  # snap to nearest base
            self._idx_low = int(xTL/BASE_WIDTH)
            self.resize_handle_group.updateText(HandleType.LEFT, self._idx_low)
        else:
            xTL = self._idx_low*BASE_WIDTH

        if bottom_right:
            xBR = util.clamp(bottom_right[0],
                             (self._idx_low+self._MIN_WIDTH)*BASE_WIDTH,
                             (self._high_drag_bound)*BASE_WIDTH)
            xBR = xBR - (xBR % BASE_WIDTH)  # snap to nearest base
            self._idx_high = int(xBR/BASE_WIDTH)
            self.resize_handle_group.updateText(HandleType.RIGHT, self._idx_high)
        else:
            xBR = self._idx_high*BASE_WIDTH

        yTL = self._part_item._vh_rect.top()
        yBR = self._part_item._vh_rect.bottom()-BASE_WIDTH*3

        self.setRect(QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR)))
        self.outline.setRect(self.rect())
        self.outline.updateAppearance()
        self.resize_handle_group.alignHandles(self.rect())
        self._model_part.setProperty('workplane_idxs', (self._idx_low, self._idx_high), use_undostack=False)
        return self.rect()

    def setIdxs(self, new_idxs):
        if self._idx_low != new_idxs[0] or self._idx_high != new_idxs[1]:
            self._idx_low = new_idxs[0]
            self._idx_high = new_idxs[1]
            self.reconfigureRect((), ())
        self._high_drag_bound = self._model_part.getProperty('max_vhelix_length')
    # end def

    def showModelMinBoundsHint(self, handle_type, show=True):
        m_b_h = self.model_bounds_hint
        if show:
            xTL, yTL, xBR, yBR = self.getModelMinBounds(handle_type)
            m_b_h.setRect(QRectF(QPointF(xTL, yTL), QPointF(xBR, yBR)))
            m_b_h.show()
        else:
            m_b_h.hide()
            self._part_item.update()  # m_b_h hangs around unless force repaint
    # end def

    def width(self):
        """
        Returns:
            int: width of the PathWorkplaneItem in index distance
        """
        return self._idx_high - self._idx_low
    # end def

    ### EVENT HANDLERS ###
    def hoverEnterEvent(self, event):
        if event.modifiers() & Qt.ShiftModifier:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        self._part_item.updateStatusBar("{}–{}".format(self._idx_low, self._idx_high))
        QGraphicsItem.hoverEnterEvent(self, event)
    # end def

    def hoverMoveEvent(self, event):
        if event.modifiers() & Qt.ShiftModifier:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        QGraphicsItem.hoverMoveEvent(self, event)
    # end def

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self._part_item.updateStatusBar("")
        QGraphicsItem.hoverLeaveEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        """
        Parses a mousePressEvent. Stores _move_idx and _offset_idx for
        future comparison.
        """
        self._high_drag_bound = self._model_part.getProperty('max_vhelix_length') - self.width()
        if event.modifiers() & Qt.ShiftModifier or self._moving_via_handle:
            self.setCursor(Qt.ClosedHandCursor)
            self._start_idx_low = self._idx_low
            self._start_idx_high = self._idx_high
            self._delta = 0
            self._move_idx = int(floor((self.x()+event.pos().x()) / BASE_WIDTH))
            self._offset_idx = int(floor(event.pos().x()) / BASE_WIDTH)
        else:
            return QGraphicsItem.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        """
        Converts event coords into an idx delta and updates if changed.
        """
        delta = int(floor((self.x()+event.pos().x()) / BASE_WIDTH)) - self._offset_idx
        delta = util.clamp(delta,
                           self._low_drag_bound-self._start_idx_low,
                           self._high_drag_bound-self._start_idx_high+self.width())
        if self._delta != delta:
            self._idx_low = int(self._start_idx_low + delta)
            self._idx_high = int(self._start_idx_high + delta)
            self._delta = delta
            self.reconfigureRect((), ())
            self.resize_handle_group.updateText(HandleType.LEFT, self._idx_low)
            self.resize_handle_group.updateText(HandleType.RIGHT, self._idx_high)
        return QGraphicsItem.mouseMoveEvent(self, event)
    # end def

    def mouseReleaseEvent(self, event):
        """
        Repeates mouseMove calculation in case any new movement.
        """
        self.setCursor(Qt.ArrowCursor)
        delta = int(floor((self.x()+event.pos().x()) / BASE_WIDTH)) - self._offset_idx
        delta = util.clamp(delta,
                           self._low_drag_bound-self._start_idx_low,
                           self._high_drag_bound-self._start_idx_high+self.width())
        if self._delta != delta:
            self._idx_low = int(self._start_idx_low + delta)
            self._idx_high = int(self._start_idx_high + delta)
            self._delta = delta
            self.reconfigureRect((), ())
        self._high_drag_bound = self._model_part.getProperty('max_vhelix_length')  # reset for handles
        return QGraphicsItem.mouseReleaseEvent(self, event)
    # end def
