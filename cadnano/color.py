try:
    from PyQt5.QtGui import QColor as Color
except:
    class Color(object):
        def __init__(self, r, g, b, a=255):
            self.setRgb(r, g, b, a)
        # end def

        def setRgb(self, r, g, b, a=255):
            self.r = r
            self.g = g
            self.b = b
            self.a = a
        # end def

        def setAlpha(self, a):
            self.a = a

        def name(self):
            return self.hex()

        def hex(self):
            return "#{:02X}{:02X}{:02X}{:02X}".format(self.r, self.g, self.b, self.a)
    #end def