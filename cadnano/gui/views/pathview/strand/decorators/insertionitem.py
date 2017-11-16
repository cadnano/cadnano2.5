#!/usr/bin/env python
# encoding: utf-8
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.cnenum import StrandType

from cadnano import util
from cadnano.gui.palette import getPenObj, getBrushObj, getNoPen

from PyQt5.QtCore import QRectF, Qt, QPointF, QEvent

from PyQt5.QtGui import QBrush, QPen, QFont, QColor, QFontMetricsF, QPainterPath
from PyQt5.QtGui import QTransform, QTextCursor
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets  import QGraphicsTextItem, QLabel

_BASE_WIDTH = _BW = styles.PATH_BASE_WIDTH
_HALF_BASE_WIDTH = _HBW = _BASE_WIDTH / 2
_OFFSET1 = _BASE_WIDTH / 4
_DEFAULT_RECT = QRectF(0, 0, _BW, _BW)
_B_PEN = getPenObj(styles.BLUE_STROKE, styles.INSERTWIDTH)
_R_PEN = getPenObj(styles.RED_STROKE, styles.SKIPWIDTH)
_NO_PEN = getNoPen()

def _insertGen(path, start, c1, p1, c2):
    path.moveTo(start)
    path.quadTo(c1, p1)
    path.quadTo(c2, start)
# end def


_PATH_START = QPointF(_HBW, _HBW)
_PATH_MID_UP = QPointF(_HBW, -_BW)
_PATH_UP_UP_CTRL_PT = QPointF(-_HBW, -_BW)
_PATH_UP_DOWN_CTRL_PT = QPointF(1.5 * _BW, -_BW)
_PATH_MID_DOWN = QPointF(_HBW, 2 * _BW)
_PATH_DOWN_DOWN_CTRL_PT = QPointF(-_HBW, 2 * _BW)
_PATH_DOWN_UP_CTRL_PT = QPointF(1.5 * _BW, 2 * _BW)
_INSERT_PATH_UP = QPainterPath()
_insertGen(_INSERT_PATH_UP, _PATH_START, _PATH_UP_UP_CTRL_PT,\
         _PATH_MID_UP, _PATH_UP_DOWN_CTRL_PT)
_INSERT_PATH_UP.translate(_OFFSET1, 0)
_INSERT_PATH_UP_RECT = _INSERT_PATH_UP.boundingRect()
_INSERT_PATH_DOWN = QPainterPath()
_insertGen(_INSERT_PATH_DOWN, _PATH_START, _PATH_DOWN_DOWN_CTRL_PT,\
         _PATH_MID_DOWN, _PATH_DOWN_UP_CTRL_PT)
_INSERT_PATH_DOWN.translate(_OFFSET1, 0)
_INSERT_PATH_DOWNRect = _INSERT_PATH_DOWN.boundingRect()


_BIG_RECT = _DEFAULT_RECT.united(_INSERT_PATH_UP_RECT)
_BIG_RECT = _BIG_RECT.united(_INSERT_PATH_DOWNRect)
_B_PEN2 = getPenObj(styles.BLUE_STROKE, 2)
_OFFSET2   = _BW*0.75
_FONT = QFont(styles.THE_FONT, styles.THE_FONT_SIZE/2, QFont.Bold)
_BIG_RECT.adjust(-15, -15, 30, 30)
# Bases are drawn along and above the insert path.
# These calculations revolve around fixing the characters at a certain
# percentage of the total arclength.
# The fraction of the insert that comes before the first character and
# after the last character is the padding, and the rest is divided evenly.
_FRACTION_INSERT_TO_PAD = .10

class InsertionPath(object):
    """
    This is just the shape of the Insert item
    """

    def __init__(self):
        super(InsertionPath, self).__init__()
    # end def

    def getPen(self):
        return _B_PEN
    # end def

    def getInsert(self, is_top):
        if is_top:
            return _INSERT_PATH_UP
        else:
            return _INSERT_PATH_DOWN
    # end def
# end class

def _xGen(path, p1, p2, p3, p4):
    path.moveTo(p1)
    path.lineTo(p2)
    path.moveTo(p3)
    path.lineTo(p4)
# end def

_PATH_START = QPointF(_HBW, _HBW)

class SkipPath(object):
    """
    This is just the shape of the Insert item
    """

    _skip_path = QPainterPath()
    _xGen(_skip_path, _DEFAULT_RECT.bottomLeft(), _DEFAULT_RECT.topRight(), \
                        _DEFAULT_RECT.topLeft(), _DEFAULT_RECT.bottomRight())

    def __init__(self):
        super(SkipPath, self).__init__()
    # end def

    def getPen(self):
        return _R_PEN
    # end def

    def getSkip(self):
        return self._skip_path
    # end def
# end class

_insert_path = InsertionPath()
_skip_path = SkipPath()

class InsertionItem(QGraphicsPathItem):
    """
    This is just the shape of the Insert item
    """
    def __init__(self, virtual_helix_item, strand, insertion):
        super(InsertionItem, self).__init__(virtual_helix_item)
        self.hide()
        self._strand = strand
        self._insertion = insertion
        self._seq_item = QGraphicsPathItem(parent=self)
        self._is_on_top = is_on_top = strand.isForward()
        y = 0 if is_on_top else _BW
        self.setPos(_BW*insertion.idx(), y)
        self.setZValue(styles.ZINSERTHANDLE)
        self._initLabel()
        self._initClickArea()
        self.updateItem()
        self.show()
    # end def

    def _initLabel(self):
        """Display the length of the insertion."""

        self._label = InsertionLabel(self)
        self._seq_item = QGraphicsPathItem(parent=self)
        self._seq_text = None
        self.show()
    # end def

    def _initClickArea(self):
        """docstring for _initClickArea"""
        self._clickArea = cA = QGraphicsRectItem(_DEFAULT_RECT, self)
        cA.setPen(_NO_PEN)
        cA.mousePressEvent = self.mousePressEvent
        cA.mouseDoubleClickEvent = self.mouseDoubleClickEvent
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def remove(self):
        """
        Called from the following stranditem methods:
            strandRemovedSlot
            strandInsertionRemovedSlot
            refreshInsertionItems
        """
        scene = self.scene()
        self._label.setTextInteractionFlags(Qt.NoTextInteraction)
        self._label.clearFocus()
        scene.removeItem(self._label)
        self._label = None
        scene.removeItem(self._seq_item)
        self._seq_item = None
        scene.removeItem(self)
        self._insertion = None
        self._strand = None
    # end def

    def updateItem(self):
        self._updatePath()
        self._label.updateLabel()
        self._updateSequenceText()
        self._label.resetPosition()
    # end def

    ### PRIVATE SUPPORT METHODS ###

    def _updatePath(self):
        strand = self._strand
        if strand is None:
            self.hide()
            return
        else:
            self.show()
        is_on_top = self._is_on_top
        if self._insertion.length() > 0:
            self.setPen(QPen(QColor(strand.oligo().getColor()), styles.INSERTWIDTH))
            self.setBrush(QBrush(Qt.NoBrush))
            self.setPath(_insert_path.getInsert(is_on_top))
        else:  # insertion_size < 0 (a skip)
            self.setPen(_skip_path.getPen())
            self.setPath(_skip_path.getSkip())
    # end def

    def setSequence(self, sequence):
        self._seq_text = sequence
        self._updateSequenceText()
        self._seq_item.show()
    # end def

    def hideSequence(self):
        self._seq_item.hide()
    # end def

    def _updateSequenceText(self):
        seq_item = self._seq_item
        is_on_top = self._is_on_top
        index = self._insertion.idx()
        base_text = self._seq_text
        font = styles.SEQUENCEFONT
        seq_font_h = styles.SEQUENCEFONTH
        insert_w = styles.INSERTWIDTH
        seq_font_char_w = styles.SEQUENCEFONTCHARWIDTH
        # draw sequence on the insert
        if base_text:  # only draw sequences if they exist i.e. not None!
            len_BT = len(base_text)
            if is_on_top:
                angle_offset = 0
            else:
                angle_offset = 180
            if len_BT > 20:
                base_text = base_text[:17] + '...'
                len_BT = len(base_text)
            fraction_arc_len_per_char = (1.0 - 2.0*_FRACTION_INSERT_TO_PAD) / (len_BT + 1)
            seq_item.setPen(QPen(Qt.NoPen))
            seq_item.setBrush(QBrush(Qt.black))

            seq_path = QPainterPath()
            loop_path = self.path()
            for i in range(len_BT):
                frac = _FRACTION_INSERT_TO_PAD + (i+1)*fraction_arc_len_per_char
                pt = loop_path.pointAtPercent(frac)
                tang_ang = loop_path.angleAtPercent(frac)

                temp_path = QPainterPath()
                # 1. draw the text
                temp_path.addText(0, 0, font, base_text[i if is_on_top else -i-1])
                # 2. center it at the zero point different for top and bottom
                # strands
                if not is_on_top:
                    temp_path.translate(0, -seq_font_h - insert_w)

                temp_path.translate(QPointF(-seq_font_char_w / 2.,
                                          -2 if is_on_top else seq_font_h))


                mat = QTransform()
                # 3. rotate it
                mat.rotate(-tang_ang + angle_offset)

                rotated_path = mat.map(temp_path)
                # 4. translate the rotate object to it's position on the part
                rotated_path.translate(pt)
                seq_path.addPath(rotated_path)
            # end for
            seq_item.setPath(seq_path)
        # end if
    # end def

    ### EVENT HANDLERS ###
    def mouseDoubleClickEvent(self, event):
        """Double clicks remove the insertion/skip."""
        self._strand.changeInsertion(self._insertion.idx(), 0)

    def mousePressEvent(self, event):
        """This needs to be present for mouseDoubleClickEvent to work."""
        pass

# end class

class InsertionLabel(QGraphicsTextItem):
    def __init__(self, parent):
        super(QGraphicsTextItem, self).__init__("", parent=parent)
        self.setFont(_FONT)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setTextWidth(-1)
    # end def

    def inputMethodEvent(self, event):
        """
        This is run on the label being changed
        or losing focus
        """
        # test = unicode(lbl.toPlainText())
        parent = self.parentItem()
        test = self.toPlainText()
        try:
            insertion_size = int(test)
        except:
            insertion_size = None
        insertion = parent._insertion
        length = insertion.length()
        if insertion_size is not None and insertion_size != length:
            parent._strand.changeInsertion(insertion.idx(), insertion_size)
            if insertion.length():
                self.resetPosition()
        else:
            self.updateLabel()
        # end if
        self.focusOut()
    # end def

    def mousePressEvent(self, event):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        cursor = self.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
    # end def

    def keyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        text = event.text()
        if a in [Qt.Key_Space, Qt.Key_Tab]:
            return
        elif a in [Qt.Key_Escape]:
            self.updateLabel()
            self.focusOut()
            return
        elif a in [Qt.Key_Return, Qt.Key_Enter]:
            self.inputMethodEvent(event)
            return
        elif text.isalpha():
            return
        else:
            return QGraphicsTextItem.keyPressEvent(self, event)
    # end def

    def mouseDoubleClickEvent(self, event):
        self.parentItem().mouseDoubleClickEvent(event)
    # end def

    def focusOutEvent(self, event):
        self.inputMethodEvent(event)
        QGraphicsTextItem.focusOutEvent(self, event)
    # end class

    def event(self, event):
       if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
           # print("tab pressed")
           return True
       return QGraphicsTextItem.event(self, event)
    # end def

    def focusOut(self):
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self.clearFocus()
    # end def

    def resetPosition(self):
        """
        Set the label position based on orientation and text alignment.
        """
        parent = self.parentItem()
        if parent is None:
            return
        txt_offset = self.boundingRect().width()/2
        insertion = parent._insertion
        y = -1.1*_BW if parent._is_on_top else 1.3*_HBW
        self.setPos(_OFFSET2 - txt_offset, y)
        if insertion.length() > 0:
            self.show()
        else:
            self.hide()
    # end def

    def updateLabel(self):
        self.setPlainText("%d" % (self.parentItem()._insertion.length()))
    # end def
# end class
