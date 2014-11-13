import re
from .abstractpathtool import AbstractPathTool
from cadnano.enum import StrandType
from cadnano.data.dnasequences import sequences
from cadnano.gui.ui.dialogs.ui_addseq import Ui_AddSeqDialog
from cadnano.gui.views import styles
import cadnano.util as util

from PyQt5.QtCore import Qt, QObject, QPointF, QRegExp, QSignalMapper, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPen, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QRadioButton

dnapattern = QRegExp("[^ACGTacgt]")


class DNAHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        self.format = QTextCharFormat()
        self.format.setForeground(QBrush(styles.INVALID_DNA_COLOR))
        if styles.UNDERLINE_INVALID_DNA:
            self.format.setFontUnderline(True)
            self.format.setUnderlineColor(styles.INVALID_DNA_COLOR)

    def highlightBlock(self, text):
        index = dnapattern.indexIn(text)
        while index >= 0:
            length = dnapattern.matchedLength()
            self.setFormat(index, length, self.format)
            index = text.indexOf(dnapattern, index + length)
        self.setCurrentBlockState(0)


class AddSeqTool(AbstractPathTool):
    def __init__(self, controller, parent=None):
        AbstractPathTool.__init__(self, controller, parent)
        self.dialog = QDialog()
        self.buttons = []
        self.seqBox = None
        self.chosenStandardSequence = None  # state for tab switching
        self.customSequenceIsValid = False  # state for tab switching
        self.useCustomSequence = False  # for applying sequence
        self.validatedSequenceToApply = None
        self.initDialog()

    def __repr__(self):
        return "add_seq_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "addSeqTool"  # first letter should be lowercase

    def initDialog(self):
        """
        1. Create buttons according to available scaffold sequences and
        add them to the dialog.
        2. Map the clicked signal of those buttons to keep track of what
        sequence gets selected.
        3. Watch the tabWidget change signal to determine whether a
        standard or custom sequence should be applied.
        """
        uiDlg = Ui_AddSeqDialog()
        uiDlg.setupUi(self.dialog)
        self.signalMapper = QSignalMapper(self)
        # set up the radio buttons
        for i, name in enumerate(sorted(sequences.keys())):
            radioButton = QRadioButton(uiDlg.groupBox)
            radioButton.setObjectName(name + "Button")
            radioButton.setText(name)
            self.buttons.append(radioButton)
            uiDlg.verticalLayout.addWidget(radioButton)
            self.signalMapper.setMapping(radioButton, i)
            radioButton.clicked.connect(self.signalMapper.map)
        self.signalMapper.mapped.connect(self.standardSequenceChangedSlot)
        uiDlg.tabWidget.currentChanged.connect(self.tabWidgetChangedSlot)
        # disable apply until valid option or custom sequence is chosen
        self.applyButton = uiDlg.customButtonBox.button(QDialogButtonBox.Apply)
        self.applyButton.setEnabled(False)
        # watch sequence textedit box to validate custom sequences
        self.seqBox = uiDlg.seqTextEdit
        self.seqBox.textChanged.connect(self.validateCustomSequence)
        self.highlighter = DNAHighlighter(self.seqBox)
        # finally, pre-click the M13mp18 radio button
        self.buttons[0].click()
        buttons = self.buttons

        self.dialog.setFocusProxy(uiDlg.groupBox)
        self.dialog.setFocusPolicy(Qt.TabFocus)
        uiDlg.groupBox.setFocusPolicy(Qt.TabFocus)
        for i in range(len(buttons)-1):
            uiDlg.groupBox.setTabOrder(buttons[i], buttons[i+1])

    def tabWidgetChangedSlot(self, index):
        applyEnabled = False
        if index == 1:  # Custom Sequence
            self.validateCustomSequence()
            if self.customSequenceIsValid:
                applyEnabled = True
        else:  # Standard Sequence
            self.useCustomSequence = False
            if self.chosenStandardSequence != None:
                # Overwrite sequence in case custom has been applied
                activeButton = self.buttons[self.chosenStandardSequence]
                sequenceName = str(activeButton.text())
                self.validatedSequenceToApply = sequences.get(sequenceName, None)
                applyEnabled = True
        self.applyButton.setEnabled(applyEnabled)

    def standardSequenceChangedSlot(self, optionChosen):
        """
        Connected to signalMapper to receive a signal whenever user selects
        a different sequence in the standard tab.
        """
        sequenceName = str(self.buttons[optionChosen].text())
        self.validatedSequenceToApply = sequences.get(sequenceName, None)
        self.chosenStandardSequence = optionChosen
        self.applyButton.setEnabled(True)

    def validateCustomSequence(self):
        """
        Called when:
        1. User enters custom sequence (i.e. seqBox emits textChanged signal)
        2. tabWidgetChangedSlot sees the user has switched to custom tab.

        When the sequence is valid, make the applyButton active for clicking.
        Otherwise
        """
        userSequence = self.seqBox.toPlainText()
        if len(userSequence) == 0:
            self.customSequenceIsValid = False
            return  # tabWidgetChangedSlot will disable applyButton
        if dnapattern.indexIn(userSequence) == -1:  # no invalid characters
            self.useCustomSequence = True
            self.customSequenceIsValid = True
            self.applyButton.setEnabled(True)
        else:
            self.customSequenceIsValid = False
            self.applyButton.setEnabled(False)

    def applySequence(self, oligo):
        self.dialog.setFocus()
        if self.dialog.exec_():  # apply the sequence if accept was clicked
            if self.useCustomSequence:
                self.validatedSequenceToApply = str(self.seqBox.toPlainText().toUpper())
            oligo.applySequence(self.validatedSequenceToApply)
            return oligo.length(), len(self.validatedSequenceToApply)
        return (None, None)
