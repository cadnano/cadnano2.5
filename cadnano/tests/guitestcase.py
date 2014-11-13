# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

import time
import unittest
from PyQt4.QtCore import *
from PyQt4.QtGui import *

main = unittest.main


class GUITestCase(unittest.TestCase):
    __qAppInitialized = False

    def __init__(self, *args, **kwargs):
        """
        We have to be careful on whether we do initialize a QApplication,
        so, we have to store a strong reference in an instance and store
        whether we did this in the class itself. When initializing again,
        we should not create another QApplication.

        (The unittest framework creates all classes and then calls setUp-
        tearDown on each one)
        """
        unittest.TestCase.__init__(self, *args, **kwargs)

        if not GUITestCase.__qAppInitialized:
            GUITestCase.__qAppInitialized = True
            self._qApplicationFirstReference = QApplication([])
        self._app = qApp
        self._app.processEvents()
        self._wait = 0

    def tearDown(self):
        self._test_widget.close()

    def setWidget(self, widget, show=True, wait=None):
        """
        Must be called in the setUp() method, giving the test widget.

        @param show: If show() should be called on the GUI. Set to False if
        you don't want to see the GUI running.

        @param wait: How long to wait between events, in seconds.
        """
        self._test_widget = widget
        self._wait = wait
        if show:
            self._test_widget.show()
        self.processEvents()

    # button flags
    NOBUTTON = Qt.NoButton
    LEFT = Qt.LeftButton
    RIGHT = Qt.RightButton
    MIDDLE = Qt.MidButton
    SHIFT = Qt.ShiftModifier
    CONTROL = Qt.ControlModifier
    ALT = Qt.AltModifier

    ############################ Mouse events ############################
    def mousePress(self, widget, button=None, position=None, state=None, modifiers=None, qgraphicsscene=None):
        """Sends a press event for the given widget.
        @param button: the pressed mouse button. Can be LEFT, RIGHT or MIDDLE.
            If not given, LEFT is assumed.
        @param position: a QPoint or a pair, indicating the position in widget
            coordinates where the button was pressed. If not given, the center
            of the widget is used.
        @param state: secondary keys. optional, can be SHIFT, CONTROL, ALT.
        """
        self._mouseEvent(QEvent.MouseButtonPress, widget, button, position, state, modifiers, qgraphicsscene)

    def mouseRelease(self, widget, button=None, position=None, state=None, modifiers=None, qgraphicsscene=None):
        """Sends a mouse release event for the given widget.

        @see: mousePress for the meaning of the arguments.
        """
        self._mouseEvent(QEvent.MouseButtonRelease, widget, button, position, state, modifiers, qgraphicsscene)

    def mouseMove(self, widget, position=None, state=None, modifiers=None, qgraphicsscene=None):
        """Sends a mouse move event for the given widget.

        @see: mousePress for the meaning of the arguments.
        """
        state = self.LEFT
        self._mouseEvent(QEvent.MouseMove, widget, self.NOBUTTON, position, state, modifiers, qgraphicsscene)

    def mouseDrag(self, widget, pressOn, releaseOn, button=None, state=None):
        """
        Makes a drag with the mouse.

        @pressOn: this is the position where the mouse is pressed.
        @releaseOn: this is the position where the mouse is released.
        """
        if state is None:
            state = self.LEFT
        self.mousePress(widget, button, pressOn, state)
        self.mouseMove(widget, releaseOn, state)
        self.mouseRelease(widget, button, releaseOn, state)

    def click(self, widget, button=None, position=None, state=None, modifiers=None, qgraphicsscene=None):
        """
        Acts as if the given widget was clicked. Equivalent to send a
        mousePress followed by a mouseRelease.

        @see: mousePress for the meaning of the arguments.
        """
        widget.setFocus()
        self.mousePress(widget, button, position, state, modifiers, qgraphicsscene)
        self.mouseRelease(widget, button, position, state, modifiers, qgraphicsscene)

    def doubleClick(self, widget, button=None, position=None, state=None):
        """Sends a double-click event to the given widget.

        @see: mousePress for the meaning of the arguments.
        """
        widget.setFocus()
        self._mouseEvent(QEvent.MouseButtonDblClick, widget, button, position, state)

    ########################## Keyboard events ############################
    def keyPress(self, widget, key, state=None):
        """Sends a key press event to the given widget.
        @param key: a qt.Qt.Key_* constant or a one-char string.
        @param state: secondary keys. optional, can be SHIFT, CONTROL, ALT.
        """
        self._keyEvent(QEvent.KeyPress, widget, key, state)

    def keyRelease(self, widget, key, state=None):
        """Sends a key release event to the given widget.
        @see: keyPress for the meaning of the arguments.
        """
        self._keyEvent(QEvent.KeyRelease, widget, key, state)

    def type(self, widget, key, state=None):
        """Acts as if a key was typed in the given widget. Equivalent to a
        keyPress followed by a keyRelease.
        @see: keyPress for the meaning of the arguments.
        """
        self.keyPress(widget, key, state)
        self.keyRelease(widget, key, state)

    def typeText(self, widget, text):
        """Types the text over the given widget."""
        for char in text:
            self.type(widget, char)

    ########################## Miscellaneous ############################
    def debugHere(self):
        """Stops the executing of the test at the caller's position, returning
        control to qt's main loop. Useful to debug the tests.
        """
        self._app.setActiveWindow(self._test_widget)
        self._app.exec_()

    def processEvents(self):
        self._app.processEvents()
        if self._wait:
            time.sleep(self._wait)

    ############################ Private Methods ############################
    def _getWidgetCenter(self, widget):
        if getattr(widget, "boundingRect", False):
            # Can't pass a QPointF to QPoint constructor, so we let
            # python cast x and y to ints instead...
            return widget.boundingRect().center().toPoint()
        else:
            return QPoint(widget.width()/2, widget.height()/2)


    def _mouseEvent(self, event_type, widget, button, position, state, modifiers, qgraphicsscene=None):
        """Sends a MouseEvent with the given event_type.
        """
        if button is None:
            button = self.LEFT
        if position is None:
            position = self._getWidgetCenter(widget)
        if not isinstance(position, QPoint):
            position = QPoint(*position)  # assume position is a tuple
        if state is None:
            state = self.NOBUTTON
        if modifiers is None:
            modifiers = Qt.NoModifier
        event = QMouseEvent(event_type, position, button, state, modifiers)
        if qgraphicsscene:
            result = qgraphicsscene.sendEvent(widget, event)
        else:
            self._app.postEvent(widget, event)
        self.processEvents()

    def _keyEvent(self, event_type, widget, key, state=None):
        """Sends a key event.
        @param key: must be either a qt.Qt.Key_* constant or a one-char string
        in string.printable.
        """
        if state is None:
            if isinstance(key, str) and key.isupper():
                state = Qt.ShiftModifier
            else:
                state = self.NOBUTTON
        new_key, ascii = self._convertKey(key)
        string = _QT_TO_STR.get(new_key, '')
        if isinstance(key, str) and key.isupper():
            string = string.upper()
        if state is None:
            state = Qt.NoModifier
        event = Qt.QKeyEvent(event_type, new_key, state, string)
        self._app.postEvent(widget, event)
        self.processEvents()

    def _convertKey(self, key):
        """
        Handles the given key for a KeyEvent. Returns (key, ascii), where
        key is one of the qt.Qt.Key_ constants. If key is a string, it is
        converted to one of the qt.Qt.Key_* constants.
        """
        if isinstance(key, str):
            if key.lower() in _STR_TO_QT:
                ascii = ord(key)
                key = _STR_TO_QT[key.lower()]
                return key, ascii
            else:
                raise ValueError('Invalid key: %s' % key)
        else:
            ascii = ord(_QT_TO_STR.get(key, '\0'))
            return key, ascii

    def executeOnElapsed(self, callback, msecs):
        """
        This function schedules the callback to be executed when 'millis' has
        elapsed
        @param callback: this is the callable that should be executed.
        @param msecs: milliseconds to call callback.
        """
        QTimer.singleShot(msecs, callback)

_toElapse = []  # List of objects that we don't want garbage collected

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
