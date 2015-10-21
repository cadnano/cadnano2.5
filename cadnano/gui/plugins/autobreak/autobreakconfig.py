import sys
# print("THE  PATH", sys.path)
import autobreak.autobreakconfig_ui as autobreakconfig_ui
import autobreak.breaker as breaker
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt

class AutobreakConfig(QDialog, autobreakconfig_ui.Ui_Dialog):
    def __init__(self, parent, handler):
        QDialog.__init__(self, parent, Qt.Sheet)
        self.setupUi(self)
        self.handler = handler
        fb = self.buttonBox.button(QDialogButtonBox.Cancel)
        fb.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_R ))

    def keyPressEvent(self, e):
        return QDialog.keyPressEvent(self, e)

    def closeDialog(self):
        self.close()

    def accept(self):
        part = self.handler.doc.controller().activePart()
        if part is not None:
            settings = {\
                'stapleScorer'    : breaker.tgtLengthStapleScorer,\
                'minStapleLegLen' : self.minLegLengthSpinBox.value(),\
                'minStapleLen'    : self.minLengthSpinBox.value(),\
                'maxStapleLen'    : self.maxLengthSpinBox.value(),\
            }
            self.handler.win.path_graphics_view.setViewportUpdateOn(False)
            # print "pre verify"
            # part.verifyOligos()
            # print "breakStaples"
            breaker.breakStaples(part, settings)
            # print "post break verify"
            # part.verifyOligos()
            self.handler.win.path_graphics_view.setViewportUpdateOn(True)
        self.close()
