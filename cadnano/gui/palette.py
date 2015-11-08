"""
Module for caching QColor, QPen, and QBrush objects
could also cache QFont objects as well
"""

from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtCore import Qt

color_cache = {}

def getColorObj(hex_string, alpha=None, lighter=None):
    global color_cache
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    key = (hex_string, lighter)
    color = color_cache.get(key)
    if color is None:
        color = QColor(hex_string)
        if lighter is not None:
            color.lighter(lighter)
        color_cache[key] = color
    return color
# end def

pen_cache = {}

def getPenObj(hex_string, stroke_width,
                alpha=None,
                lighter=None,
                capstyle=None,
                joinstyle=None):
    global pen_cache
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    # print(hex_string)
    key = (hex_string, stroke_width, lighter, capstyle, joinstyle)
    pen = pen_cache.get(key)
    if pen is None:
        color = getColorObj(hex_string, lighter=lighter)
        pen = QPen(color, stroke_width)
        if capstyle is not None:
            pen.setCapStyle(capstyle)
        if joinstyle is not None:
            pen.setJoinStyle(joinstyle)
        pen_cache[key] = pen
    return pen
# end def

def newPenObj(hex_string, stroke_width, alpha=None):
    """ use this when you need a pen with dynamic properties
    """
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    color = getColorObj(hex_string)
    return QPen(color, stroke_width)
# end def

brush_cache = {}

def getBrushObj(hex_string, alpha=None, lighter=None):
    global brush_cache
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    key = (hex_string, lighter)
    brush = brush_cache.get(key)
    if brush is None:
        color = getColorObj(hex_string, lighter=lighter)
        brush = QBrush(color)
        brush_cache[key] = brush
    return brush
# end def

def newBrushObj(hex_string, alpha=None):
    """ use this when you need a brush with dynamic properties
    """
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    color = getColorObj(hex_string)
    return QBrush(color)
# end def

no_pen = QPen(Qt.NoPen)
def getNoPen():
    global no_pen
    return no_pen

solid_brush = QBrush(Qt.SolidPattern)
def getSolidBrush():
    global solid_brush
    return solid_brush

no_brush = QBrush(Qt.NoBrush)
def getNoBrush():
    global no_brush
    return no_brush
