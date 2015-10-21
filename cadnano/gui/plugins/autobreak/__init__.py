from .autobreakconfig import AutobreakConfig
import cadnano

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QAction

class AutobreakHandler(object):
    def __init__(self, document, window):
        self.doc, self.win = document, window
        icon10 = QIcon()
        icon10.addPixmap(QPixmap(":/pathtools/autobreak"), QIcon.Normal, QIcon.Off)
        self.action_autobreak = QAction(window)
        self.action_autobreak.setIcon(icon10)
        self.action_autobreak.setText('AutoBreak')
        self.action_autobreak.setToolTip("Click this button to generate a default set of staples.")
        self.action_autobreak.setObjectName("action_autobreak")
        self.action_autobreak.triggered.connect(self.actionAutobreakSlot)
        self.win.menu_plugins.addAction(self.action_autobreak)
        # add to main tool bar
        self.win.selection_toolbar.insertAction(self.win.action_filters_label, self.action_autobreak)
        self.win.selection_toolbar.insertSeparator(self.win.action_filters_label)
        self.config_dialog = None

    def actionAutobreakSlot(self):
        """Only show the dialog if staple strands exist."""
        part = self.doc.controller().activePart()
        if part != None:  # is there a part?
            for o in list(part.oligos()):
                if o.isStaple():  # is there a staple oligo?
                    if self.config_dialog == None:
                        self.config_dialog = AutobreakConfig(self.win, self)
                    self.config_dialog.show()
                    return

def documentWindowWasCreatedSlot(doc, win):
    doc.autobreak_handler = AutobreakHandler(doc, win)

# # Initialization
for c in cadnano.app().document_controllers:
    doc, win = c.document(), c.window()
    doc.autobreak_handler = AutobreakHandler(doc, win)
cadnano.app().documentWindowWasCreatedSignal.connect(documentWindowWasCreatedSlot)
