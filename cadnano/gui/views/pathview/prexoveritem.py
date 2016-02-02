
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QFont, QPen, QPolygonF, QPainterPath, QFontMetrics
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsSimpleTextItem, QUndoCommand, QGraphicsRectItem

from cadnano.enum import StrandType
from cadnano.gui.palette import getPenObj, getBrushObj, getSolidBrush
from . import pathstyles as styles

_FWD_PEN = getPenObj(styles.PXI_SCAF_STROKE,
                    styles.PATH_STRAND_STROKE_WIDTH,
                    capstyle=Qt.FlatCap,
                    joinstyle=Qt.RoundJoin)
_REV_PEN = getPenObj(styles.PXI_STAP_STROKE,
                    styles.PATH_STRAND_STROKE_WIDTH,
                    capstyle=Qt.FlatCap,
                    joinstyle=Qt.RoundJoin)
_DISAB_PEN = getPenObj(styles.PXI_DISAB_STROKE,
                styles.PATH_STRAND_STROKE_WIDTH,
                capstyle=Qt.FlatCap,
                joinstyle=Qt.RoundJoin)
_DISAB_BRUSH = getBrushObj(styles.PXI_DISAB_STROKE)  # For the helix number label
_ENAB_BRUSH = getSolidBrush()  # Also for the helix number label
_BASE_WIDTH = styles.PATH_BASE_WIDTH
_RECT = QRectF(0, 0, styles.PATH_BASE_WIDTH, 1.2*styles.PATH_BASE_WIDTH)
_TO_HELIX_NUM_FONT = styles.XOVER_LABEL_FONT
# precalculate the height of a number font.  Assumes a fixed font
# and that only numbers will be used for labels
_FM = QFontMetrics(_TO_HELIX_NUM_FONT)

class PreXoverItem(QGraphicsPathItem):
    def __init__(self,  from_virtual_helix_item, to_virtual_helix_item, index, strand_type):
        super(PreXoverItem, self).__init__(from_virtual_helix_item)
        self._from_vh_item = from_virtual_helix_item
        self._to_vh_item = to_virtual_helix_item
        self._idx = index
        self._strand_type = strand_type
        # translate from Low to Left for the Path View
        self._is_low_index = is_low_idx
        self._is_active = False
        is_on_top = strand_type is StrandType.FWD
        self._pen = _FWD_PEN if is_on_top else _REV_PEN

        bw = _BASE_WIDTH
        x = bw * index
        y = (-1.25 if is_on_top else 2.25) * bw
        self.setPos(x, y)

        num = to_virtual_helix_item.idNum()
        tBR = _FM.tightBoundingRect(str(num))
        half_label_H = tBR.height()/2.0
        half_label_W = tBR.width()/2.0

        labelX = bw/2.0 - half_label_W #
        if num == 1:  # adjust for the number one
            labelX -= half_label_W/2.0

        if is_on_top:
            labelY = -0.25*half_label_H - .5
        else:
            labelY = 2*half_label_H + .5

        self._label = QGraphicsSimpleTextItem(self)
        self._label.setPos(labelX, labelY)

        # create a bounding rect item to process click events
        # over a wide area
        self._clickArea = c_a = QGraphicsRectItem(_RECT, self)
        c_a.mousePressEvent = self.mousePress
        yoffset = 0.2*bw if is_on_top else -0.4*bw
        c_a.setPos(0, yoffset)
        c_a.setPen(QPen(Qt.NoPen))

        self.updateStyle()
        self._updateLabel()
        self.setPainterPath()
    # end def

    ### DRAWING METHODS ###
    def remove(self):
        scene = self.scene()
        if scene:
            scene.removeItem(self._label)
            scene.removeItem(self._clickArea)
            scene.removeItem(self)
        self._label = None
        self._clickArea = None
        self._from_vh_item = None
        self._to_vh_item = None
    # end def

    def _updateLabel(self):
        lbl = self._label
        lbl.setBrush(self._label_brush)
        lbl.setFont(_TO_HELIX_NUM_FONT)
        lbl.setText( str(self._to_vh_item.idNum() ) )
    # end def

    ### TOOL METHODS ###
    def selectToolMousePress(self, event):
        """removexover(from_strand, from_idx, to_strand, to_idx)"""
        pass
    # end def
