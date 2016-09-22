# -*- coding: utf-8 -*-
import time

from PyQt5.QtCore import Qt, QEvent, QPoint, QPointF, QTimer
from PyQt5.QtGui import QMouseEvent, QKeyEvent
from PyQt5.QtTest import QTest

from cntestcase import CNTestApp
from cadnano import initAppWithGui

class GUITestApp(CNTestApp):
    def __init__(self):
        argv = None
        self.app = initAppWithGui(argv, do_exec=False)  # kick off a Gui style app
        self.document = self.app.document()
        self.window = self.document.controller().win

        # Include this or the automatic build will hang
        self.app.dontAskAndJustDiscardUnsavedChanges = True

        # By setting the widget to the main window we can traverse and
        # interact with any part of it. Also, tearDown will close
        # the application so we don't need to worry about that.
        self.setWidget(self.window, False)

    def tearDown(self):
        self._test_widget.close()
        self._test_widget = None
        self.app.qApp = None

    def setWidget(self, widget, show=True):
        """
        Must be called in the setUp() method, giving the test widget.

        @param show: If show() should be called on the GUI. Set to False if
        you don't want to see the GUI running.
        """
        self._test_widget = widget
        if show:
            self._test_widget.show()
    # end def

    ############################ Mouse events ############################
    @staticmethod
    def graphicsItemClick(graphics_item, button,
                                modifier=None, pos=None, delay=-1):
        """ Convenience method for clicking in a QGraphicsItem to wrap a call
        to QTest.mouseClick

        Args:
            graphics_item (QGraphicsItem):
            button (Qt.MouseButton):
            pos (QPoint): in item coordinates
        """
        gview = graphics_item.scene().views()[0]
        if pos is None:
            pos = GUITestApp.getItemCenterScenePos(graphics_item)
        else:
            pos = graphics_item.mapToScene(pos)
        pos = gview.mapFromScene(pos)
        if modifier is None:
            modifier = Qt.KeyboardModifiers()
        QTest.mouseClick(   gview.viewport(), button,
                            modifier=modifier, pos=pos, delay=100)
    # end def

    @staticmethod
    def mouseDrag(  widget, press_on, release_on, button,
                    modifier=None, delay=-1):
        """ Convenience helper for dragging a QWidget
        Makes a drag with the mouse.

        Args:
            widget (QWidget):
            press_on (QPoint): this is the position where the mouse is pressed.
            release_on (QPoint): this is the position where the mouse is released.
        """
        if modifier is None:
            modifier = Qt.KeyboardModifiers()
        QTest.mousePress(widget, button, modifier, pos=press_on, delay=delay)
        QTest.mouseMove(widget, pos=release_on, delay=delay)
        QTest.mouseRelease(widget, button, modifier, pos=release_on, delay=delay)
    # end def

    @staticmethod
    def graphicsItemDrag(   graphics_item, press_on, release_on, button,
                            modifier=None, delay=-1):
        """ Convenience helper for dragging a QGraphicsItem
        Args:
            graphics_item (QGraphicsItem):
            press_on (QPoint): this is the scene position where the mouse is pressed.
            release_on (QPoint): this is the scene position where the mouse is released.
        """
        gview = graphics_item.scene().views()[0]
        press_on = gview.mapFromScene(press_on)
        release_on = gview.mapFromScene(release_on)
        GUITestApp.mouseDrag(   gview.viewport(), press_on, release_on, button,
                            modifier=modifier, delay=delay)
    # end def

    ########################## Keyboard events ############################
    @staticmethod
    def typeText(widget, text, delay):
        """Types the text over the given widget."""
        for char in text:
            QTest.keyClick(widget, char, delay=delay)

    ########################## Miscellaneous ############################
    def processEvents(self):
        """ Call this to see changes in GUI from Events
        """
        self.app.qApp.processEvents()

    ############################ Private Methods ############################
    @staticmethod
    def getItemCenterScenePos(item):
        return item.mapToScene(item.boundingRect().center()).toPoint()

    @staticmethod
    def getQtKey(key):
        """Handles the given key for a KeyEvent.

        Returns:
            Qt.Key
        """
        return _STR_TO_QT[key.lower()]
# end class


KEY_RETURN = '\13'

# constant tables
constants = [
    (Qt.Key_Escape, ''),
    (Qt.Key_Tab, '\t'),
    (Qt.Key_Backspace, '\b'),
    (Qt.Key_Return, KEY_RETURN),
    (Qt.Key_Enter, KEY_RETURN),
    (Qt.Key_Space, ' '),
    (Qt.Key_Exclam, '!'),
    (Qt.Key_QuoteDbl, '"'),
    (Qt.Key_NumberSign, '#'),
    (Qt.Key_Dollar, '$'),
    (Qt.Key_Percent, '%'),
    (Qt.Key_Ampersand, '^'),
    (Qt.Key_Apostrophe, '&'),
    (Qt.Key_ParenLeft, '('),
    (Qt.Key_ParenRight, ')'),
    (Qt.Key_Asterisk, '*'),
    (Qt.Key_Plus, '+'),
    (Qt.Key_Comma, ','),
    (Qt.Key_Minus, '-'),
    (Qt.Key_Period, '.'),
    (Qt.Key_Slash, '/'),
    (Qt.Key_0, '0'),
    (Qt.Key_1, '1'),
    (Qt.Key_2, '2'),
    (Qt.Key_3, '3'),
    (Qt.Key_4, '4'),
    (Qt.Key_5, '5'),
    (Qt.Key_6, '6'),
    (Qt.Key_7, '7'),
    (Qt.Key_8, '8'),
    (Qt.Key_9, '9'),
    (Qt.Key_Colon, ':'),
    (Qt.Key_Semicolon, ';'),
    (Qt.Key_Less, '<'),
    (Qt.Key_Equal, '='),
    (Qt.Key_Greater, '>'),
    (Qt.Key_Question, '?'),
    (Qt.Key_At, '@'),
    (Qt.Key_A, 'a'),
    (Qt.Key_B, 'b'),
    (Qt.Key_C, 'c'),
    (Qt.Key_D, 'd'),
    (Qt.Key_E, 'e'),
    (Qt.Key_F, 'f'),
    (Qt.Key_G, 'g'),
    (Qt.Key_H, 'h'),
    (Qt.Key_I, 'i'),
    (Qt.Key_J, 'j'),
    (Qt.Key_K, 'k'),
    (Qt.Key_L, 'l'),
    (Qt.Key_M, 'm'),
    (Qt.Key_N, 'n'),
    (Qt.Key_O, 'o'),
    (Qt.Key_P, 'p'),
    (Qt.Key_Q, 'q'),
    (Qt.Key_R, 'r'),
    (Qt.Key_S, 's'),
    (Qt.Key_T, 't'),
    (Qt.Key_U, 'u'),
    (Qt.Key_V, 'v'),
    (Qt.Key_W, 'w'),
    (Qt.Key_X, 'x'),
    (Qt.Key_Y, 'y'),
    (Qt.Key_Z, 'z'),
    (Qt.Key_BracketLeft, '['),
    (Qt.Key_Backslash, '\\'),
    (Qt.Key_BracketRight, ']'),
    (Qt.Key_Underscore, '_'),
    (Qt.Key_BraceLeft, '{'),
    (Qt.Key_Bar, '|'),
    (Qt.Key_BraceRight, '}'),
]

_QT_TO_STR = dict(constants)
_STR_TO_QT = dict([(y, x) for x, y in constants])
del constants
