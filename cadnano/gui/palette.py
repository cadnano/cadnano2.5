"""
Module for caching `QColor <http://doc.qt.io/qt-5/qcolor.html>`_, 
`QPen <http://doc.qt.io/qt-5/qpen.html>`_, and 
`QBrush <http://doc.qt.io/qt-5/qbrush.html>`_ objects.
Could be extended to cache `QFont <http://doc.qt.io/qt-5/qfont.html>`_ objects as well.
"""

from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtCore import Qt

color_cache = {}
pen_cache = {}
brush_cache = {}
no_pen = QPen(Qt.NoPen)
no_brush = QBrush(Qt.NoBrush)
solid_brush = QBrush(Qt.SolidPattern)



def getColorObj(hex_string, alpha=None, lighter=None):
    """Checks internal cache for specified color. If not in the cache, add it.

    Args:
        hex_string (str): hexadecimal color code in the form: #RRGGBB
        alpha (int): 0–255
        lighter (int): see `QColor.lighter <http://doc.qt.io/qt-5/qcolor.html#lighter>`_.

    Returns:
        color (QColor)
    """
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


def getPenObj(hex_string, stroke_width,
              alpha=None,
              lighter=None,
              penstyle=None,
              capstyle=None,
              joinstyle=None):
    """If the specified QPen is cached, return it.
    Otherwise, cache and return a new QPen.

    Args:
        hex_string (str): hexadecimal color code in the form: #RRGGBB
        stroke_width (int)
        alpha (int): 0–255
        lighter (int): see `QColor.lighter <http://doc.qt.io/qt-5/qcolor.html#lighter>`_.
        penstyle (Qt.PenStyle): see `QPen.pen-style <http://doc.qt.io/qt-5/qpen.html#pen-style>`_.
        capstyle (Qt.CapStyle): see `QPen.cap-style <http://doc.qt.io/qt-5/qpen.html#cap-style>`_.
        joinstyle (Qt.JoinStyle): see `QPen.join-style <http://doc.qt.io/qt-5/qpen.html#join-style>`_.

    Returns:
        pen (QPen)
    """
    global pen_cache
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    # print(hex_string)
    key = (hex_string, stroke_width, lighter, capstyle, joinstyle)
    pen = pen_cache.get(key)
    if pen is None:
        color = getColorObj(hex_string, lighter=lighter)
        pen = QPen(color, stroke_width)
        if penstyle is not None:
            pen.setStyle(penstyle)
        if capstyle is not None:
            pen.setCapStyle(capstyle)
        if joinstyle is not None:
            pen.setJoinStyle(joinstyle)
        pen_cache[key] = pen
    return pen
# end def


def newPenObj(hex_string, stroke_width, alpha=None):
    """Returns a new QPen object. Use this when you need a pen with dynamic 
    properties, or wish to use features that are not supported by the cache, 
    such as  `setCosmetic <http://doc.qt.io/qt-5/qpen.html#setCosmetic>`_.

    Does not use the cache.

    Args:
        hex_string (str): hexadecimal color code in the form: #RRGGBB
        stroke_width (int)
        alpha (int): 0–255
    
    
    Returns:
        pen (QPen)
    """
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    color = getColorObj(hex_string)
    return QPen(color, stroke_width)
# end def



def getBrushObj(hex_string, alpha=None, lighter=None):
    """If the specified QBrush is cached, return it. 
    Otherwise, cache and return a new QPen.

    Args:
        hex_string (str): hexadecimal color code in the form: #RRGGBB
        alpha (int): 0–255
        lighter (int): see `QColor.lighter <http://doc.qt.io/qt-5/qcolor.html#lighter>`_.

    Returns:
        brush (QBrush)
    """
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
    """ Returns a new QPen object. Use this when you need a pen with dynamic 
    properties, or wish to use features that are not supported by the cache, 
    such as  `setTexture <http://doc.qt.io/qt-5/qbrush.html#setTexture>`_.

    Does not use the cache.

    Args:
        hex_string (str): hexadecimal color code in the form: #RRGGBB
        alpha (int): 0–255
        
    Returns:
        brush (QBrush)
    """
    if alpha is not None:
        hex_string = '#%0.2x%s' % (alpha, hex_string[1:])
    color = getColorObj(hex_string)
    return QBrush(color)
# end def


def getNoPen():
    """Global instance of QPen(Qt.NoPen).

    Returns:
        QPen(Qt.NoPen)
    """
    global no_pen
    return no_pen


def getNoBrush():
    """Global instance of QBrush(Qt.NoBrush).

    Returns:
        QBrush(Qt.NoBrush)
    """
    global no_brush
    return no_brush

def getSolidBrush():
    """Global instance of QBrush(Qt.SolidPattern).

    Returns:
        QBrush(Qt.SolidPattern)        
    """
    global solid_brush
    return solid_brush
