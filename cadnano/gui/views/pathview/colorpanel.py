"""Summary
"""
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QFont
from PyQt5.QtWidgets import (QGraphicsItem, QColorDialog,
                             QGraphicsTextItem)

from cadnano.gui.palette import getColorObj
from . import pathstyles as styles


_FONT = QFont(styles.THE_FONT, 12, QFont.Bold)


class ColorPanel(QGraphicsItem):
    """Summary

    Attributes:
        colordialog (TYPE): Description
        rect (TYPE): Description
    """
    _shift_colors = [getColorObj(x) for x in styles.SCAF_COLORS]
    _colors = [getColorObj(x) for x in styles.STAP_COLORS]
    _PEN = Qt.NoPen

    def __init__(self, parent=None):
        """Summary

        Args:
            parent (None, optional): Description
        """
        super(ColorPanel, self).__init__(parent)
        self.rect = QRectF(0, 0, 30, 30)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.colordialog = QColorDialog()
        self._shift_color_index = -1  # init on -1, painttool will cycle to 0
        self._color_index = -1  # init on -1, painttool will cycle to 0
        self._shift_color = self._shift_colors[self._shift_color_index]
        self._color = self._colors[self._color_index]
        self._shift_brush = QBrush(self._shift_color)
        self._brush = QBrush(self._color)
        self._initLabel()
        self.hide()

    def _initLabel(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._label = label = QGraphicsTextItem("⇧", parent=self)
        label.setPos(28, -4)
        label.setFont(_FONT)

    def boundingRect(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self.rect

    def paint(self, painter, option, widget=None):
        """Summary

        Args:
            painter (TYPE): Description
            option (TYPE): Description
            widget (None, optional): Description

        Returns:
            TYPE: Description
        """
        painter.setPen(self._PEN)
        painter.setBrush(self._shift_brush)
        painter.drawRect(0, 0, 30, 15)
        painter.setBrush(self._brush)
        painter.drawRect(0, 15, 30, 15)

    def nextColor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._color_index += 1
        if self._color_index == len(self._colors):
            self._color_index = 0
        self._color = self._colors[self._color_index]
        self._brush.setColor(self._color)
        self.update()

    def prevColor(self):
        """Summary

        Returns:
            TYPE: Description
        """
        self._color_index -= 1

    def color(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._color

    def shiftColorName(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._shift_color.name()

    def colorName(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._color.name()

    def mousePressEvent(self, event):
        """Summary

        Args:
            event (QGraphicsSceneMouseEvent): Description

        Returns:
            TYPE: Description
        """
        if event.pos().y() < 10:
            new_color = self.colordialog.getColor(self._shift_color)
            if new_color.isValid() and new_color.name() != self._shift_color.name():
                self._shift_color = new_color
                self._shift_brush = QBrush(new_color)
                if new_color not in self._shift_colors:
                    self._shift_colors.insert(self._shift_color_index, new_color)
                self.update()
        else:
            new_color = self.colordialog.getColor(self._color)
            if new_color.isValid() and new_color.name() != self._color.name():
                self._color = new_color
                self._brush = QBrush(new_color)
                if new_color not in self._colors:
                    self._colors.insert(self._color_index, new_color)
                self.update()
