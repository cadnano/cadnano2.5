# -*- coding: utf-8 -*-
"""This allows the model to have a :class:`Color` object class without
the need for :class:`PyQt5.QtGui.QColor`

When running the Qt Application, :class:`QColor` will be used, otherwise an
API compatible class is used and exported as a :class:`Color` object

Currently :class:`Color` objects are unused in the model and colors are stored as
QColor compatible hex string in format '#rrggbbaa', and therefore is not
exposed in the API documentation
"""

try:
    from PyQt5.QtGui import QColor as Color
except Exception:
    class Color(object):
        """ Overloaded constructor using *args to be compatible with :class:`QColor`

        usage::

            Color(r, g, b)

        or::

            Color('#rrggbb') for hex
        """

        def __init__(self, *args):
            largs = len(args)
            if largs == 1:
                # clip the `#`
                arg = args[0]
                if isinstance(arg, str):
                    raise ValueError("color doesn't support ints")
                color_number = int(arg[1:], 16)
                r = (color_number >> 16) & 0xFF
                g = (color_number >> 8) & 0xFF
                b = color_number & 0xFF
                self.setRgb(r, g, b, 255)
            elif largs == 3:
                r, g, b = args
                self.setRgb(r, g, b, 255)
            else:
                r, g, b, a = args
                self.setRgb(r, g, b, a)
        # end def

        def __repr__(self) -> str:
            return self.hex()

        def setRgb(self, r: int, g: int, b: int, a: int = 255):
            """Set the r, g, b and alpha 8 bit values

            Args:
                r: 0 - 255
                g: 0 - 255
                b: 0 - 255
                a: 0 - 255
            """
            self.r = r
            self.g = g
            self.b = b
            self.a = a
        # end def

        def setAlpha(self, a: int):
            """Set the alpha 8 bit value

            Args:
                a (int): 0 - 255
            """
            self.a = a

        def name(self) -> str:
            """The hex string name.  For :class:`QColor` compatibility

            Returns:
                :class:`QColor` compatible hex string in format '#rrggbbaa'
            """
            return self.hex()

        def hex(self) -> str:
            """The hex string name.

            Returns:
                :class:`QColor` compatible hex string in format '#rrggbbaa'
            """
            return "#{:02X}{:02X}{:02X}{:02X}".format(self.r, self.g, self.b, self.a)
    # end def


def _intToColor(color_number: int) -> Color:
    """ legacy color support for converting integers to color objects based on the
    cadnano 2 file format

    Args:
        color_number: integer value of a RGB color

    Returns:
        the :class:`Color` object
    """
    return Color('#%0.6x' % (color_number))


def intToColorHex(color_number: int) -> str:
    """Convert an integer to a hexadecimal string compatible with :class:`QColor`

    Args:
        color_number: integer value of a RGB color

    Returns:
        :class:`QColor` compatible hex string in format '#rrggbb'
    """
    return '#%0.6x' % (color_number)
