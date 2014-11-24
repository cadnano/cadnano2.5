
from . import pathstyles as styles
import cadnano.util as util

from PyQt5.QtCore import  QRectF, Qt
from PyQt5.QtGui import QBrush, QFont, QPen, QDrag
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsSimpleTextItem, QColorDialog

_FONT = QFont(styles.THE_FONT, 12, QFont.Bold)


class ColorPanel(QGraphicsItem):
    _scaf_colors = styles.SCAF_COLORS
    _stap_colors = styles.STAP_COLORS
    _PEN = Qt.NoPen

    def __init__(self, parent=None):
        super(ColorPanel, self).__init__(parent)
        self.rect = QRectF(0, 0, 30, 30)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.colordialog = QColorDialog()
        # self.colordialog.setOption(QColorDialog.DontUseNativeDialog)
        self._scaf_color_index = -1  # init on -1, painttool will cycle to 0
        self._stap_color_index = -1  # init on -1, painttool will cycle to 0
        self._scaf_color = self._scaf_colors[self._scaf_color_index]
        self._stap_color = self._stap_colors[self._stap_color_index]
        self._scaf_brush = QBrush(self._scaf_color)
        self._stap_brush = QBrush(self._stap_color)
        self._initLabel()
        self.hide()

    def _initLabel(self):
        self._label = label = QGraphicsSimpleTextItem("scaf\nstap", parent=self)
        label.setPos(32, 0)
        label.setFont(_FONT)
        # label.setBrush(_labelbrush)
        # label.hide()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        painter.setPen(self._PEN)
        painter.setBrush(self._scaf_brush)
        painter.drawRect(0, 0, 30, 15)
        painter.setBrush(self._stap_brush)
        painter.drawRect(0, 15, 30, 15)

    def nextColor(self):
        self._stap_color_index += 1
        if self._stap_color_index == len(self._stap_colors):
            self._stap_color_index = 0
        self._stap_color = self._stap_colors[self._stap_color_index]
        self._stap_brush.setColor(self._stap_color)
        self.update()

    def prevColor(self):
        self._stap_color_index -= 1

    def color(self):
        return self._stap_color

    def scafColorName(self):
        return self._scaf_color.name()

    def stapColorName(self):
        return self._stap_color.name()

    def changeScafColor(self):
        self.update()

    def changeStapColor(self):
        self._stap_color = self.colordialog.currentColor()
        self._stap_brush = QBrush(self._stap_color)
        self.update()

    def mousePressEvent(self, event):
        if event.pos().y() < 10:
            new_color = self.colordialog.getColor(self._scaf_color)
            if new_color.isValid() and new_color.name() != self._scaf_color.name():
                self._scaf_color = new_color
                self._scaf_brush = QBrush(new_color)
                if not new_color in self._scaf_colors:
                    self._scaf_colors.insert(self._scaf_color_index, new_color)
                self.update()
        else:
            new_color = self.colordialog.getColor(self._stap_color)
            if new_color.isValid() and new_color.name() != self._stap_color.name():
                self._stap_color = new_color
                self._stap_brush = QBrush(new_color)
                if not new_color in self._stap_colors:
                    self._stap_colors.insert(self._stap_color_index, new_color)
                self.update()

