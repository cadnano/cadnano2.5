import math
import re

from cadnano import app

from cadnano.enum import StrandType
from . import slicestyles as styles
import cadnano.util as util

GL = False

from PyQt5.QtCore import QPointF, Qt, QRectF

from PyQt5.QtGui import QBrush, QFont, QPen, QDrag, QTransform
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsSimpleTextItem, QGraphicsTextItem
from PyQt5.QtWidgets  import QUndoCommand, QGraphicsEllipseItem, QStyle

# strand addition stores some meta information in the UndoCommand's text
_strand_re = re.compile("\((\d+),(\d+)\)\.0\^(\d+)")

class EmptyHelixItem(QGraphicsEllipseItem):
    """docstring for EmptyHelixItem"""
    # set up default, hover, and active drawing styles
    _DEFAULT_BRUSH = QBrush(styles.GRAY_FILL)
    _DEFAULT_PEN = QPen(styles.GRAY_STROKE, styles.SLICE_HELIX_STROKE_WIDTH)
    _HOVER_BRUSH = QBrush(styles.BLUE_FILL)
    _HOVER_PEN = QPen(styles.BLUE_STROKE, styles.SLICE_HELIX_HILIGHT_WIDTH)
    _RADIUS = styles.SLICE_HELIX_RADIUS
    temp = styles.SLICE_HELIX_STROKE_WIDTH
    _DEFAULT_RECT = QRectF(0, 0, 2 * _RADIUS, 2 * _RADIUS)
    temp = (styles.SLICE_HELIX_HILIGHT_WIDTH - temp)/2
    _HOVER_RECT = _DEFAULT_RECT.adjusted(-temp, -temp, temp, temp)
    _Z_DEFAULT = styles.ZSLICEHELIX 
    _Z_HOVERED = _Z_DEFAULT + 1 
    temp /= 2
    _ADJUSTMENT_PLUS = (temp, temp)
    _ADJUSTMENT_MINUS = (-temp, -temp)
    # _PI = 3.141592
    # _temp = [x*_PI*0.1 for x in range(20)]
    # _temp = [(math.sin(angle) * _RADIUS, math.cos(angle) * _RADIUS) for angle in _temp]
    def __init__(self, row, column, part_item):
        """
        row, column is a coordinate in Lattice terms
        part_item is a PartItem that will act as a QGraphicsItem parent
        """
        super(EmptyHelixItem, self).__init__(parent=part_item)
        self._part_item = part_item
        self._lastvh = None  # for decideAction
        self.hide()
        self._is_hovered = False
        self.setAcceptHoverEvents(True)

        self.setNotHovered()

        x, y = part_item.part().latticeCoordToPositionXY(row, column, part_item.scaleFactor())
        self.setPos(x, y)
        self._coord = (row, column)
        self.show()
    # end def

    def virtualHelix(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.virtualHelixItem()
        if temp:
            return temp.virtualHelix()
        else:
            return None
    # end def

    def virtualHelixItem(self):
        """
        virtualHelixItem should be the HelixItems only child if it exists
        and virtualHelix should be it member
        """
        temp = self.childItems()
        if len(temp) > 0:
            return temp[0]
        else:
            return None
    # end def

    def part(self):
        return self._part_item.part()
    # end def

    def translateVH(self, delta):
        """
        used to update a child virtual helix position on a hover event
        delta is a tuple of x and y values to translate

        positive delta happens when hover happens
        negative delta when something unhovers
        """
        temp = self.virtualHelixItem()

        # xor the check to translate, 
        # convert to a QRectF adjustment if necessary
        check = (delta > 0) ^ self._is_hovered
        if temp and check:
            pass
            # temp.translate(*delta)
    # end def

    def setHovered(self):
        # self.setFlag(QGraphicsItem.ItemHasNoContents, False)  
        self.setBrush(self._HOVER_BRUSH)
        self.setPen(self._HOVER_PEN)
        self.update(self.boundingRect())
        # self.translateVH(self._ADJUSTMENT_PLUS)
        self._is_hovered = True
        self.setZValue(self._Z_HOVERED)
        self.setRect(self._HOVER_RECT)

        self._part_item.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def hoverEnterEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from default
        to the hover colors if necessary.
        """
        self.setHovered()
    # end def

    def setNotHovered(self):
        """
        """
        # drawMe = False if self.virtualHelixItem() else True
        # self.setFlag(QGraphicsItem.ItemHasNoContents, drawMe)
        self.setBrush(self._DEFAULT_BRUSH)
        self.setPen(self._DEFAULT_PEN)
        # self.translateVH(self._ADJUSTMENT_MINUS)
        self._is_hovered = False
        self.setZValue(self._Z_DEFAULT)
        self.setRect(self._DEFAULT_RECT)

        self._part_item.updateStatusBar("")
    # end def

    def hoverLeaveEvent(self, event):
        """
        hoverEnterEvent changes the HelixItem brush and pen from hover
        to the default colors if necessary.
        """
        self.setNotHovered()
    # end def

    def mousePressEvent(self, event):
        action = self.decideAction(event.modifiers())
        action(self)
        self.dragSessionAction = action
    # end def

    def mouseMoveEvent(self, event):
        part_item = self._part_item
        pos_in_parent = part_item.mapFromItem(self, QPointF(event.pos()))
        # Qt doesn't have any way to ask for graphicsitem(s) at a
        # particular position but it *can* do intersections, so we
        # just use those instead
        part_item.probe.setPos(pos_in_parent)
        for ci in part_item.probe.collidingItems():
            if isinstance(ci, EmptyHelixItem):
                self.dragSessionAction(ci)
    # end def

    def autoScafMidSeam(self, strands):
        """docstring for autoScafMidSeam"""
        part = self.part()
        strand_type = StrandType.SCAFFOLD
        idx = part.activeBaseIndex()
        for i in range(1, len(strands)):
            row1, col1, ss_idx1 = strands[i - 1]  # previous strand
            row2, col2, ss_idx2 = strands[i]  # current strand
            vh1 = part.virtualHelixAtCoord((row1, col1))
            vh2 = part.virtualHelixAtCoord((row2, col2))
            strand1 = vh1.scaffoldStrandSet()._strand_list[ss_idx1]
            strand2 = vh2.scaffoldStrandSet()._strand_list[ss_idx2]
            # determine if the pair of strands are neighbors
            neighbors = part.getVirtualHelixNeighbors(vh1)
            if vh2 in neighbors:
                p2 = neighbors.index(vh2)
                if vh2.number() % 2 == 1:
                    # resize and install external xovers
                    try:
                        # resize to the nearest prexover on either side of idx
                        new_lo = util.nearest(idx, 
                            part.getPreXoversHigh(strand_type, p2, max_idx=idx - 10))
                        new_hi = util.nearest(idx, 
                            part.getPreXoversLow(strand_type, p2, min_idx=idx + 10))
                        if strand1.canResizeTo(new_lo, new_hi) and \
                           strand2.canResizeTo(new_lo, new_hi):
                            # do the resize
                            strand1.resize((new_lo, new_hi))
                            strand2.resize((new_lo, new_hi))
                            # install xovers
                            part.createXover(strand1, new_hi, strand2, new_hi)
                            part.createXover(strand2, new_lo, strand1, new_lo)
                    except ValueError:
                        pass  # nearest not found in the expanded list

                    # go back an install the internal xovers
                    if i > 2:
                        row0, col0, ss_idx0 = strands[i - 2]  # two strands back
                        vh0 = part.virtualHelixAtCoord((row0, col0))
                        strand0 = vh0.scaffoldStrandSet()._strand_list[ss_idx0]
                        if vh0 in neighbors:
                            p0 = neighbors.index(vh0)
                            l0, h0 = strand0.idxs()
                            l1, h1 = strand1.idxs()
                            o_low, o_high = util.overlap(l0, h0, l1, h1)
                            try:
                                l_list = list(filter(lambda x: x > o_low and \
                                        x < o_high,
                                        part.getPreXoversLow(strand_type, p0)))
                                l_x = l_list[len(l_list) // 2]
                                h_list = list(filter(lambda x: x > o_low and \
                                        x < o_high,
                                        part.getPreXoversHigh(strand_type, p0)))
                                h_x = h_list[len(h_list) // 2]
                                # install high xover first
                                part.createXover(strand0, h_x, strand1, h_x)
                                # install low xover after getting new strands
                                # following the breaks caused by the high xover
                                strand3 = vh0.scaffoldStrandSet()._strand_list[ss_idx0]
                                strand4 = vh1.scaffoldStrandSet()._strand_list[ss_idx1]
                                part.createXover(strand4, l_x, strand3, l_x)
                            except IndexError:
                                pass  # filter was unhappy


    def autoScafRaster(self, strands):
        """docstring for autoScafRaster"""
        part = self.part()
        idx = part.activeBaseIndex()
        for i in range(1, len(strands)):
            row1, col1, ss_idx1 = strands[i - 1]  # previous strand
            row2, col2, ss_idx2 = strands[i]  # current strand
            vh1 = part.virtualHelixAtCoord((row1, col1))
            vh2 = part.virtualHelixAtCoord((row2, col2))
            strand1 = vh1.scaffoldStrandSet()._strand_list[ss_idx1]
            strand2 = vh2.scaffoldStrandSet()._strand_list[ss_idx2]
            # determine if the pair of strands are neighbors
            neighbors = part.getVirtualHelixNeighbors(vh1)
            if vh2 in neighbors:
                p2 = neighbors.index(vh2)
                if vh2.number() % 2 == 1:
                    # resize and install external xovers
                    try:
                        # resize to the nearest prexover on either side of idx
                        new_lo1 = new_lo2 = util.nearest(idx, 
                            part.getPreXoversHigh(StrandType.SCAFFOLD, 
                                p2, max_idx=idx - 8))
                        new_hi = util.nearest(idx, 
                            part.getPreXoversLow(StrandType.SCAFFOLD, 
                                p2, min_idx=idx + 8))

                        if vh1.number() != 0:  # after the first helix
                            new_lo1 = strand1.lowIdx()  # leave alone the lowIdx

                        if vh2.number() != len(strands)-1:  # before the last
                            new_lo2 = strand2.lowIdx()  # leave alone the lowIdx

                        if strand1.canResizeTo(new_lo1, new_hi) and \
                           strand2.canResizeTo(new_lo2, new_hi):
                            strand1.resize((new_lo1, new_hi))
                            strand2.resize((new_lo2, new_hi))
                        else:
                            raise ValueError
                        # install xovers
                        part.createXover(strand1, new_hi, strand2, new_hi)
                    except ValueError:
                        pass  # nearest not found in the expanded list
                else:
                    # resize and install external xovers
                    idx = part.activeBaseIndex()
                    try:
                        # resize to the nearest prexover on either side of idx
                        new_lo = util.nearest(idx, 
                            part.getPreXoversHigh(StrandType.SCAFFOLD, 
                                p2, max_idx=idx - 8))

                        if strand1.canResizeTo(new_lo, strand1.highIdx()) and \
                           strand2.canResizeTo(new_lo, strand2.highIdx()):
                            strand1.resize((new_lo, strand1.highIdx()))
                            strand2.resize((new_lo, strand2.highIdx()))
                            # install xovers
                            part.createXover(strand1, new_lo, strand2, new_lo)
                        else:
                            raise ValueError
                    except ValueError:
                        pass  # nearest not found in the expanded list

    def mouseReleaseEvent(self, event):
        """docstring for mouseReleaseEvent"""
        part = self.part()
        u_s = part.undoStack()
        strands = []
        # Look at the undo stack in reverse order
        for i in range(u_s.index() - 1, 0, -1):
            # Check for contiguous strand additions
            m = _strand_re.match(u_s.text(i))
            if m:
                strands.insert(0, list(map(int, m.groups())))
            else:
                break

        if len(strands) > 1:
            auto_scaf_type = app().prefs.getAutoScafType()
            util.beginSuperMacro(part, "Auto-connect")
            if auto_scaf_type == "Mid-seam":
                self.autoScafMidSeam(strands)
            elif auto_scaf_type == "Raster":
                self.autoScafRaster(strands)
            util.endSuperMacro(part)

    def decideAction(self, modifiers):
        """ On mouse press, an action (add scaffold at the active slice, add
        segment at the active slice, or create virtualhelix if missing) is
        decided upon and will be applied to all other slices happened across by
        mouseMoveEvent. The action is returned from this method in the form of a
        callable function."""
        vh = self.virtualHelix()
        part = self.part()

        if vh == None:
            return EmptyHelixItem.addVHIfMissing

        idx = part.activeBaseIndex()
        scafSSet, stapSSet = vh.getStrandSets()
        if modifiers & Qt.ShiftModifier:
            if not stapSSet.hasStrandAt(idx - 1, idx + 1):
                return EmptyHelixItem.addStapAtActiveSliceIfMissing
            else:
                return EmptyHelixItem.nop

        if not scafSSet.hasStrandAt(idx - 1, idx + 1):
            return EmptyHelixItem.addScafAtActiveSliceIfMissing
        return EmptyHelixItem.nop
    # end def

    def nop(self):
        self._part_item.updateStatusBar("(%d, %d)" % self._coord)

    def addScafAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()
        if vh == None:
            return

        idx = part.activeBaseIndex()
        start_idx = max(0,idx-1)
        end_idx = min(idx+1, part.maxBaseIdx())
        vh.scaffoldStrandSet().createStrand(start_idx, end_idx)

        self._part_item.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def addStapAtActiveSliceIfMissing(self):
        vh = self.virtualHelix()
        part = self.part()

        if vh == None:
            return

        idx = part.activeBaseIndex()
        start_idx = max(0, idx - 1)
        end_idx = min(idx + 1, part.maxBaseIdx())
        vh.stapleStrandSet().createStrand(start_idx, end_idx)

        self._part_item.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    def addVHIfMissing(self):
        vh = self.virtualHelix()
        coord = self._coord
        part = self.part()

        if vh != None:
            return
        u_s = part.undoStack()
        u_s.beginMacro("Slice Click")
        part.createVirtualHelix(*coord)
        # vh.scaffoldStrandSet().createStrand(start_idx, end_idx)
        u_s.endMacro()

        self._part_item.updateStatusBar("(%d, %d)" % self._coord)
    # end def

    if GL:
        def paint(self, painter, option, widget):
            painter.beginNativePainting()
    
            radius = self._RADIUS
    
            # GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
            # GL.glClear(GL.GL_COLOR_BUFFER_BIT)
    
            # Draw the filled circle
    
            GL.glColor3f (1, 0.5, 0)       # Set to orange
    
            GL.glBegin (GL.GL_POLYGON)
            for X, Y in self._temp:
                GL.glVertex2f (X,Y)
            # end for
            GL.glEnd()
    
            # Draw the anti-aliased outline
    
            # GL.glEnable(GL.GL_BLEND)
            # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            # GL.glEnable(GL.GL_LINE_SMOOTH)
    
            # GL.glBegin(GL.GL_LINE_LOOP)
            # for angle in [x*PI*0.01 for x in range(200)]:
            #     GL.glVertex2f(X + math.sin(angle) * radius, Y + math.cos(angle) * radius)
            # # end for
            # GL.glDisable(GL.GL_BLEND)
            # GL.glEnd()
            # GL.glPopAttrib()
            painter.endNativePainting()
        # end def
    # end if

    