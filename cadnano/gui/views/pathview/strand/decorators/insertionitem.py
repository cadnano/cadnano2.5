#!/usr/bin/env python
# encoding: utf-8
from cadnano.gui.views import styles
from cadnano.enum import StrandType

import cadnano.util as util

from PyQt5.QtCore import QRectF, Qt, QPointF

from PyQt5.QtGui import QBrush, QPen, QFont, QColor, QFontMetricsF, QPainterPath
from PyQt5.QtGui import QMatrix3x3, QTextCursor
from PyQt5.QtWidgets  import QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem
from PyQt5.QtWidgets  import QGraphicsTextItem, QLabel

_baseWidth = _bw = styles.PATH_BASE_WIDTH
_halfbaseWidth = _hbw = _baseWidth / 2
_offset1 = _baseWidth / 4
_defaultRect = QRectF(0, 0, _bw, _bw)
_bpen = QPen(styles.BLUE_STROKE, styles.INSERTWIDTH)
_rpen = QPen(styles.RED_STROKE, styles.SKIPWIDTH)
_noPen = QPen(Qt.NoPen)

def _insertGen(path, start, c1, p1, c2):
    path.moveTo(start)
    path.quadTo(c1, p1)
    path.quadTo(c2, start)
# end def


_pathStart = QPointF(_hbw, _hbw)
_pathMidUp = QPointF(_hbw, -_bw)
_pathUpUpCtrlPt = QPointF(-_hbw, -_bw)
_pathUpDownCtrlPt = QPointF(1.5 * _bw, -_bw)
_pathMidDown = QPointF(_hbw, 2 * _bw)
_pathDownDownCtrlPt = QPointF(-_hbw, 2 * _bw)
_pathDownUpCtrlPt = QPointF(1.5 * _bw, 2 * _bw)
_insertPathUp = QPainterPath()
_insertGen(_insertPathUp, _pathStart, _pathUpUpCtrlPt,\
         _pathMidUp, _pathUpDownCtrlPt)
_insertPathUp.translate(_offset1, 0)
_insertPathUpRect = _insertPathUp.boundingRect()
_insertPathDown = QPainterPath()
_insertGen(_insertPathDown, _pathStart, _pathDownDownCtrlPt,\
         _pathMidDown, _pathDownUpCtrlPt)
_insertPathDown.translate(_offset1, 0)
_insertPathDownRect = _insertPathDown.boundingRect()


_bigRect = _defaultRect.united(_insertPathUpRect)
_bigRect = _bigRect.united(_insertPathDownRect)
_bpen2 = QPen(styles.BLUE_STROKE, 2)
_offset2 = _bw*0.75
_font = QFont(styles.THE_FONT, 10, QFont.Bold)
_bigRect.adjust(-15, -15, 30, 30)
# Bases are drawn along and above the insert path.
# These calculations revolve around fixing the characters at a certain
# percentage of the total arclength.
# The fraction of the insert that comes before the first character and
# after the last character is the padding, and the rest is divided evenly.
_fractionInsertToPad = .10

class InsertionPath(object):
    """
    This is just the shape of the Insert item
    """

    def __init__(self):
        super(InsertionPath, self).__init__()
    # end def

    def getPen(self):
        return _bpen
    # end def

    def getInsert(self, istop):
        if istop:
            return _insertPathUp
        else:
            return _insertPathDown
    # end def
# end class

def _xGen(path, p1, p2, p3, p4):
    path.moveTo(p1)
    path.lineTo(p2)
    path.moveTo(p3)
    path.lineTo(p4)
# end def

_pathStart = QPointF(_hbw, _hbw)

class SkipPath(object):
    """
    This is just the shape of the Insert item
    """

    _skipPath = QPainterPath()
    _xGen(_skipPath, _defaultRect.bottomLeft(), _defaultRect.topRight(), \
                        _defaultRect.topLeft(), _defaultRect.bottomRight())

    def __init__(self):
        super(SkipPath, self).__init__()
    # end def

    def getPen(self):
        return _rpen
    # end def

    def getSkip(self):
        return self._skipPath
    # end def
# end class

_insertPath = InsertionPath()
_skipPath = SkipPath()

class InsertionItem(QGraphicsPathItem):
    """
    This is just the shape of the Insert item
    """
    def __init__(self, virtualHelixItem, strand, insertion):
        super(InsertionItem, self).__init__(virtualHelixItem)
        self.hide()
        self._strand = strand
        self._insertion = insertion
        self._seqItem = QGraphicsPathItem(parent=self)
        self._isOnTop = isOnTop = virtualHelixItem.isStrandOnTop(strand)
        y = 0 if isOnTop else _bw
        self.setPos(_bw*insertion.idx(), y)
        self.setZValue(styles.ZINSERTHANDLE)
        self._initLabel()
        self._initClickArea()
        self.updateItem()
        self.show()
    # end def

    def _initLabel(self):
        """Display the length of the insertion."""
        self._label = label = QGraphicsTextItem("", parent=self)
        label.setFont(_font)
        label.setTextInteractionFlags(Qt.TextEditorInteraction)
        label.inputMethodEvent = self.inputMethodEventHandler
        label.keyPressEvent = self.textkeyPressEvent
        label.mousePressEvent = self.labelMousePressEvent
        label.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        label.setTextWidth(-1)

        self._label = label
        self._seqItem = QGraphicsPathItem(parent=self)
        self._seqText = None
        self.updateItem()
        self.show()
    # end def

    def _initClickArea(self):
        """docstring for _initClickArea"""
        self._clickArea = cA = QGraphicsRectItem(_defaultRect, self)
        cA.setPen(_noPen)
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
        scene.removeItem(self._seqItem)
        self._seqItem = None
        scene.removeItem(self)
        self._insertion = None
        self._strand = None
    # end def

    def updateItem(self):
        self._updatePath()
        self._updateLabel()
        self._updateSequenceText()
        self._resetPosition()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _focusOut(self):
        lbl = self._label
        if lbl == None:
            return
        cursor = lbl.textCursor()
        cursor.clearSelection()
        lbl.setTextCursor(cursor)
        lbl.clearFocus()
    # end def

    def _resetPosition(self):
        """
        Set the label position based on orientation and text alignment.
        """
        lbl = self._label
        if lbl == None:
            return
        txtOffset = lbl.boundingRect().width()/2
        insertion = self._insertion
        y = -_bw if self._isOnTop else _bw
        lbl.setPos(_offset2-txtOffset, y)
        if insertion.length() > 0:
            lbl.show()
        else:
            lbl.hide()
    # end def

    def _updateLabel(self):
        self._label.setPlainText("%d" % (self._insertion.length()))
    # end def

    def _updatePath(self):
        strand = self._strand
        if strand == None:
            self.hide()
            return
        else:
            self.show()
        isOnTop = self._isOnTop
        if self._insertion.length() > 0:
            self.setPen(QPen(QColor(strand.oligo().color()), styles.INSERTWIDTH))
            self.setBrush(QBrush(Qt.NoBrush))
            self.setPath(_insertPath.getInsert(isOnTop))
        else:  # insertionSize < 0 (a skip)
            self.setPen(_skipPath.getPen())
            self.setPath(_skipPath.getSkip())
    # end def

    def setSequence(self, sequence):
        self._seqText = sequence
        self._updateSequenceText()
        self._seqItem.show()
    # end def
    
    def hideSequence(self):
        self._seqItem.hide()
    # end def

    def _updateSequenceText(self):
        seqItem = self._seqItem
        isOnTop = self._isOnTop
        index = self._insertion.idx()
        baseText = self._seqText
        font = styles.SEQUENCEFONT
        seqFontH = styles.SEQUENCEFONTH
        insertW = styles.INSERTWIDTH
        seqFontCharW = styles.SEQUENCEFONTCHARWIDTH
        # draw sequence on the insert
        if baseText:  # only draw sequences if they exist i.e. not None!
            lenBT = len(baseText)
            if isOnTop:
                angleOffset = 0
            else:
                angleOffset = 180
            if lenBT > 20:
                baseText = baseText[:17] + '...'
                lenBT = len(baseText)
            fractionArclenPerChar = (1.0-2.0*_fractionInsertToPad)/(lenBT+1)
            seqItem.setPen(QPen(Qt.NoPen))
            seqItem.setBrush(QBrush(Qt.black))
            
            seqPath = QPainterPath()
            loopPath = self.path()
            for i in range(lenBT):
                frac = _fractionInsertToPad + (i+1)*fractionArclenPerChar
                pt = loopPath.pointAtPercent(frac)
                tangAng = loopPath.angleAtPercent(frac)

                tempPath = QPainterPath()
                # 1. draw the text
                tempPath.addText(0,0, font, baseText[i if isOnTop else -i-1])
                # 2. center it at the zero point different for top and bottom
                # strands
                if not isOnTop:
                    tempPath.translate(0, -seqFontH - insertW)
                    
                tempPath.translate(QPointF(-seqFontCharW/2.,
                                          -2 if isOnTop else seqFontH))
                mat = QMatrix3x3()
                # 3. rotate it
                mat.rotate(-tangAng + angleOffset)
                rotatedPath = mat.map(tempPath)
                # 4. translate the rotate object to it's position on the part
                rotatedPath.translate(pt)
                seqPath.addPath(rotatedPath)
            # end for
            seqItem.setPath(seqPath)
        # end if
    # end def

    ### EVENT HANDLERS ###
    def mouseDoubleClickEvent(self, event):
        """Double clicks remove the insertion/skip."""
        self._strand.changeInsertion(self._insertion.idx(), 0)

    def mousePressEvent(self, event):
        """This needs to be present for mouseDoubleClickEvent to work."""
        pass

    def labelMousePressEvent(self, event):
        """
        Pre-selects the text for editing when you click
        the label.
        """
        lbl = self._label
        lbl.setTextInteractionFlags(Qt.TextEditorInteraction)
        cursor = lbl.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        lbl.setTextCursor(cursor)

    def textkeyPressEvent(self, event):
        """
        Must intercept invalid input events.  Make changes here
        """
        a = event.key()
        text = event.text()
        if a in [Qt.Key_Space, Qt.Key_Tab]:
            return
        elif a in [Qt.Key_Return, Qt.Key_Enter]:
            self.inputMethodEventHandler(event)
            return
        # elif unicode(text).isalpha():
        elif text.isalpha():
            return
        else:
            return QGraphicsTextItem.keyPressEvent(self._label, event)

    def inputMethodEventHandler(self, event):
        """
        This is run on the label being changed
        or losing focus
        """
        lbl = self._label
        if lbl == None:
            return
        # test = unicode(lbl.toPlainText())
        test = lbl.toPlainText()
        try:
            insertionSize = int(test)
        except:
            insertionSize = None
        insertion = self._insertion
        length = insertion.length()
        if insertionSize != None and insertionSize != length:
            self._strand.changeInsertion(insertion.idx(), insertionSize)
            if insertion.length():
                self._resetPosition()
        else:
            self._updateLabel()
        # end if
        self._focusOut()
    # end def
# end class
