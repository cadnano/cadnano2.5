"""Summary
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPlainTextEdit  # QTextEdit


class ConsoleInput(QPlainTextEdit):
    def __init__(self, parent):
        """Input field for console."""
        super(ConsoleInput, self).__init__(parent)
        self._console_output = None
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def append(self, msg):
        self.textCursor().appendPlainText(msg)
    # end def

    def setConsoleOutput(self, console_output_text):
        self._console_output_text = console_output_text
    # end def

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if self._console_output_text is not None:
                self._console_output_text.append(self.toPlainText())
                self.clear()
        else:
            return QPlainTextEdit.keyPressEvent(self, event)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
