from math import floor
import cadnano.util as util
from . import pathstyles as styles

from PyQt5.QtCore import QPointF, QRectF, Qt, QEvent

from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import qApp, QGraphicsItem, QGraphicsItemGroup, QGraphicsPathItem

class SelectionItemGroup(QGraphicsItemGroup):
    """
    SelectionItemGroup
    """
    def __init__(self, boxtype, constraint='y', parent=None):
        super(SelectionItemGroup, self).__init__(parent)
        self._viewroot = parent
        self.setFiltersChildEvents(True)
        
        # LOOK at Qt Source for deprecated code to replace this behavior
        # self.setHandlesChildEvents(True) # commented out NC

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # for keyPressEvents
        self.setFlag(QGraphicsItem.ItemHasNoContents)

        self._rect = QRectF()
        self._PEN = QPen(styles.BLUE_STROKE, styles.PATH_SELECTBOX_STROKE_WIDTH)

        self.selectionbox = boxtype(self)

        self._drag_enable = False
        self._dragged = False
        self._base_click = 0  # tri-state counter to enable deselection on click away

        self._r0 = 0  # save original mousedown
        self._r = 0  # latest position for moving

        # self._lastKid = 0

        # this keeps track of mousePressEvents within the class
        # to aid in intellignetly removing items from the group
        self._added_to_press_list = False

        self._pending_to_add_dict = {}

        if constraint == 'y':
            self.getR = self.selectionbox.getY
            self.translateR = self.selectionbox.translateY
        else:
            self.getR = self.selectionbox.getX
            self.translateR = self.selectionbox.translateX

        self._normal_select = True
        self._instant_add = 0

        self.setZValue(styles.ZPATHSELECTION)
    # end def

    # def paint(self, painter, option, widget):
    #     painter.drawRect(self.boundingRect())
    # # end def

    def pendToAdd(self, item):
        self._pending_to_add_dict[item] = True
    # end def

    def isPending(self, item):
        return item in self._pending_to_add_dict
    # end def
    
    def document(self):
        return self._viewroot.document()
    # end def
    
    def pendToRemove(self, item):
        if item in self._pending_to_add_dict:
            del self._pending_to_add_dict[item]
    # end def

    def setNormalSelect(self, bool_val):
        self._normal_select = bool_val
    # end def

    def isNormalSelect(self):
        return self._normal_select
    # end def

    def processPendingToAddList(self):
        """
        Adds to the local selection and the document if required
        """
        doc = self.document()

        # print "instant add is 1 from process pending"
        if len(self._pending_to_add_dict) > 0:
            for item in self._pending_to_add_dict:
                # print "just checking1", item, item.group(), item.parentItem()
                self.addToGroup(item)
                item.modelSelect(doc)
            # end for
            self._pending_to_add_dict = {}
            doc.updateSelection()
    # end def

    def resetSelection(self):
        self._pending_to_add_dict = {}
        self._added_to_press_list = False
        self.clearSelection(False)
        self.setSelectionLock(None)
        self.selectionbox.setParentItem(self._viewroot)
        self.setParentItem(self._viewroot)
    # end def

    def selectionLock(self):
        return self._viewroot.selectionLock()
    # end def

    def setSelectionLock(self, selection_group):
        self._viewroot.setSelectionLock(selection_group)
    # end def

    # def paint(self, painter, option, widget=None):
    #     # painter.setBrush(QBrush(QColor(255,128,255,128)))
    #     painter.setPen(QPen(styles.RED_STROKE))
    #     painter.drawRect(self.boundingRect())
    #     pass
    # # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        key = event.key()
        if key in [Qt.Key_Backspace, Qt.Key_Delete]:
            self.selectionbox.deleteSelection()
            # self.document().deleteSelection()
            self.clearSelection(False)
            return QGraphicsItemGroup.keyPressEvent(self, event)
        else:
            return QGraphicsItemGroup.keyPressEvent(self, event)
    # end def

    def mousePressEvent(self, event):
        # self.show()
        if event.button() != Qt.LeftButton:
            return QGraphicsItemGroup.mousePressEvent(self, event)
        else:
            self._drag_enable = True

            # required to get the itemChanged event to work
            # correctly for this
            self.setSelected(True)

            # self.selectionbox.resetTransform()
            self.selectionbox.resetPosition()
            self.selectionbox.refreshPath()

            # self.selectionbox.resetTransform()
            self.selectionbox.resetPosition()
            self.selectionbox.show()

            # for some reason we need to skip the first mouseMoveEvent
            self._dragged = False

            if self._added_to_press_list == False:
                self._added_to_press_list = True
                self.scene().views()[0].addToPressList(self)
            return QGraphicsItemGroup.mousePressEvent(self, event)
    # end def

    def mouseMoveEvent(self, event):
        if self._drag_enable == True:
            # map the item to the scene coordinates
            # to help keep coordinates uniform
            rf = self.getR(self.mapFromScene(QPointF(event.scenePos())))
            # for some reason we need to skip the first mouseMoveEvent
            if self._dragged == False:
                self._dragged = True
                self._r0 = rf
            # end if
            else:
                delta = self.selectionbox.delta(rf, self._r0)
                self.translateR(delta)
            # end else
            self._r = rf
        # end if
        else:
            QGraphicsItemGroup.mouseMoveEvent(self, event)
        # end else
    # end def

    def customMouseRelease(self, event):
        """docstring for customMouseRelease"""
        self.selectionbox.hide()
        self.selectionbox.resetTransform()
        self._drag_enable = False
        # now do stuff
        if not (self._r0 == 0 and self._r == 0):
            self.selectionbox.processSelectedItems(self._r0, self._r)
        # end if
        self._r0 = 0  # reset
        self._r = 0  # reset
        self.setFocus() # needed to get keyPresses post a move
        self._added_to_press_list = False
    # end def

    def clearSelection(self, value):
        if value == False:
            self.selectionbox.hide()
            self.selectionbox.resetPosition()
            self.removeSelectedItems()
            self._viewroot.setSelectionLock(None)
            self.clearFocus()  # this is to disable delete keyPressEvents
            self.prepareGeometryChange()
            self._rect.setWidth(0)
            # self._rect = QRectF()
        # end if
        else:
            self.setFocus()  # this is to get delete keyPressEvents
        self.update(self.boundingRect())
    # end def

    def itemChange(self, change, value):
        """docstring for itemChange"""
        if change == QGraphicsItem.ItemSelectedChange:
            if value == False:
                self.clearSelection(False)
                return False
            else:
                return True
        elif change == QGraphicsItem.ItemChildAddedChange:
            if self._added_to_press_list == False:
                # print "kid added"
                self.setFocus()  # this is to get delete keyPressEvents
                self.setParentItem(self.selectionbox.boxParent())
                self._added_to_press_list = True
                self.scene().views()[0].addToPressList(self)
            return
        return QGraphicsItemGroup.itemChange(self, change, value)
    # end def

    def removeChild(self, child):
        """
        remove only the child and ask it to
        restore it's original parent
        """
        doc = self.document()
        t_pos = child.scenePos()
        self.removeFromGroup(child)
        child.modelDeselect(doc)
    # end def

    def removeSelectedItems(self):
        """docstring for removeSelectedItems"""
        doc = self.document()
        for item in self.childItems():
            self.removeFromGroup(item)
            item.modelDeselect(doc)
        # end for
        doc.updateSelection()
    # end def

    def setBoundingRect(self, rect):
        self.prepareGeometryChange()
        self._rect = rect
    # end def

    def boundingRect(self):
        return self._rect

# end class


class VirtualHelixHandleSelectionBox(QGraphicsPathItem):
    """
    docstring for VirtualHelixHandleSelectionBox
    """
    _HELIX_HEIGHT = styles.PATH_HELIX_HEIGHT + styles.PATH_HELIX_PADDING
    _RADIUS = styles.VIRTUALHELIXHANDLEITEM_RADIUS
    _PEN_WIDTH = styles.SELECTIONBOX_PEN_WIDTH
    _BOX_PEN = QPen(styles.BLUE_STROKE, _PEN_WIDTH)

    def __init__(self, item_group):
        """
        The item_group.parentItem() is expected to be a partItem
        """
        super(VirtualHelixHandleSelectionBox, self).__init__(
                                                        item_group.parentItem())
        self._item_group = item_group
        self._rect = item_group.boundingRect()
        self.hide()
        self.setPen(self._BOX_PEN)
        self.setZValue(styles.ZPATHSELECTION)
        self._bounds = None
        self._pos0 = QPointF()
    # end def

    def getY(self, pos):
        pos = self._item_group.mapToScene(QPointF(pos))
        return pos.y()
    # end def

    def translateY(self, delta):
        self.setY(delta)
     # end def

    def refreshPath(self):
        self.prepareGeometryChange()
        self.setPath(self.painterPath())
        self._pos0 = self.pos()
    # end def

    def painterPath(self):
        i_g = self._item_group
        # the childrenBoundingRect is necessary to get this to work
        rect = self.mapRectFromItem(i_g, i_g.childrenBoundingRect())
        radius = self._RADIUS

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        path.moveTo(rect.right(),\
                         rect.center().y())
        path.lineTo(rect.right() + radius / 2,\
                         rect.center().y())
        return path
    # end def

    def processSelectedItems(self, r_start, r_end):
        """docstring for processSelectedItems"""
        margin = styles.VIRTUALHELIXHANDLEITEM_RADIUS
        delta = (r_end - r_start)  # r delta
        mid_height = (self.boundingRect().height()) / 2 - margin
        helix_height = self._HELIX_HEIGHT

        if abs(delta) < mid_height:  # move is too short for reordering
            return
        if delta > 0:  # moved down, delta is positive
            indexDelta = int((delta - mid_height) / helix_height)
        else:  # moved up, delta is negative
            indexDelta = int((delta + mid_height) / helix_height)
        # sort on y to determine the extremes of the selection group
        items = sorted(self._item_group.childItems(), key=lambda vhhi: vhhi.y())
        part_item = items[0].partItem()
        part_item.reorderHelices(items[0].number(),\
                                items[-1].number(),\
                                indexDelta)
        part_item.updateStatusBar("")
    # end def

    def boxParent(self):
        temp = self._item_group.childItems()[0].partItem()
        self.setParentItem(temp)
        return temp
    # end def
    
    def deleteSelection(self):
        """
        Delete selection operates outside of the documents a virtual helices
        are not actually selected in the model
        """
        v_helices = [vhh.virtualHelix() for vhh in self._item_group.childItems()]
        u_s = self._item_group.document().undoStack()
        u_s.beginMacro("delete Virtual Helices")
        for vh in v_helices:
            vh.remove()
        u_s.endMacro()
    # end def

    def bounds(self):
        return self._bounds
    # end def

    def delta(self, yf, y0):
        return yf - y0
    # end def

    def resetPosition(self):
        self.setPos(self._pos0)
    # end def
# end class


class EndpointHandleSelectionBox(QGraphicsPathItem):
    _PEN_WIDTH = styles.SELECTIONBOX_PEN_WIDTH
    _BOX_PEN = QPen(styles.SELECTED_COLOR, _PEN_WIDTH)
    _BASE_WIDTH = styles.PATH_BASE_WIDTH

    def __init__(self, item_group):
        """
        The item_group.parentItem() is expected to be a partItem
        """
        super(EndpointHandleSelectionBox, self).__init__(
                                                    item_group.parentItem())
        self._item_group = item_group
        self._rect = item_group.boundingRect()
        self.hide()
        self.setPen(self._BOX_PEN)
        self.setZValue(styles.ZPATHSELECTION)
        self._bounds = (0, 0)
        self._pos0 = QPointF()
    # end def

    def getX(self, pos):
        return pos.x()
    # end def

    def translateX(self, delta):
        children = self._item_group.childItems()
        if children:
            p_i = children[0].partItem()
            str = "+%d" % delta if delta >= 0 else "%d" % delta
            p_i.updateStatusBar(str)
        self.setX(self._BASE_WIDTH * delta)
    # end def

    def resetPosition(self):
        self.setPos(self._pos0)

    def delta(self, xf, x0):
        bound_l, bound_h = self._bounds
        delta = int(floor((xf - x0) / self._BASE_WIDTH))
        if delta > 0 and delta > bound_h:
            delta = bound_h
        elif delta < 0 and abs(delta) > bound_l:
            delta = -bound_l
        return delta

    def refreshPath(self):
        temp_low, temp_high = \
                    self._item_group._viewroot.document().getSelectionBounds()
        self._bounds = (temp_low, temp_high)
        self.prepareGeometryChange()
        self.setPath(self.painterPath())
        self._pos0 = self.pos()
    # end def

    def painterPath(self):
        bw = self._BASE_WIDTH
        i_g = self._item_group
        # the childrenBoundingRect is necessary to get this to work
        rectIG = i_g.childrenBoundingRect()
        rect = self.mapRectFromItem(i_g, rectIG)
        if rect.width() < bw:
            rect.adjust(-bw / 4, 0, bw / 2, 0)
        path = QPainterPath()
        path.addRect(rect)
        self._item_group.setBoundingRect(rectIG)

        # path.addRoundedRect(rect, radius, radius)
        # path.moveTo(rect.right(),\
        #                  rect.center().y())
        # path.lineTo(rect.right() + radius / 2,\
        #                  rect.center().y())
        return path
    # end def

    def processSelectedItems(self, r_start, r_end):
        """docstring for processSelectedItems"""
        delta = self.delta(r_end, r_start)
        self._item_group._viewroot.document().resizeSelection(delta)
    # end def
    
    def deleteSelection(self):
        self._item_group.document().deleteSelection()

    def boxParent(self):
        temp = self._item_group.childItems()[0].partItem()
        self.setParentItem(temp)
        return temp
    # end def

    def bounds(self):
        return self._bounds
    # end def
# end class
