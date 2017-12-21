"""Summary
"""
from PyQt5.QtGui import QTextDocument, QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit  # QTextEdit


class ConsoleOutput(QPlainTextEdit):
    def __init__(self, parent):
        """Summary

        Args:
            rect (TYPE): Description
            parent (TYPE): Description
            window (TYPE): Description
            document (TYPE): Description
        """
        super(ConsoleOutput, self).__init__(parent)
        self._text = QTextDocument()
        self._cursor = QTextCursor(self._text)
        self.setReadOnly(True)
        self.appendPlainText("Console loaded")
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def append(self, msg):
        self.appendPlainText(msg)
    # end def

    ### SIGNALS ###

    ### SLOTS ###
