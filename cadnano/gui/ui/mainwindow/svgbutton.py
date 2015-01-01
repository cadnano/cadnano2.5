from cadnano import util
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QGraphicsObject
from PyQt5.QtSvg import QSvgRenderer

class SVGButton(QGraphicsObject):
    def __init__(self, fname, parent=None):
        super(SVGButton, self).__init__(parent)
        self.svg = QSvgRenderer(fname)

    def paint(self, painter, options, widget):
        self.svg.render(painter, self.boundingRect())

    def boundingRect(self):
        return self.svg.viewBoxF()

    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()