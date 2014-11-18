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
        self.seq_box = None
        self.chosen_standard_sequence = None  # state for tab switching
        self.custom_sequence_is_valid = False  # state for tab switching
        self.use_custom_sequence = False  # for applying sequence
        self.validated_sequence_to_apply = None
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
        3. Watch the tab_widget change signal to determine whether a
        standard or custom sequence should be applied.
        """
        ui_dlg = Ui_AddSeqDialog()
        ui_dlg.setupUi(self.dialog)
        self.signal_mapper = QSignalMapper(self)
        # set up the radio buttons
        for i, name in enumerate(sorted(sequences.keys())):
            radio_button = QRadioButton(ui_dlg.group_box)
            radio_button.setObjectName(name + "Button")
            radio_button.setText(name)
            self.buttons.append(radio_button)
            ui_dlg.verticalLayout.addWidget(radio_button)
            self.signal_mapper.setMapping(radio_button, i)
            radio_button.clicked.connect(self.signal_mapper.map)
        self.signal_mapper.mapped.connect(self.standardSequenceChangedSlot)
        ui_dlg.tab_widget.currentChanged.connect(self.tabWidgetChangedSlot)
        # disable apply until valid option or custom sequence is chosen
        self.apply_button = ui_dlg.custom_button_box.button(QDialogButtonBox.Apply)
        self.apply_button.setEnabled(False)
        # watch sequence textedit box to validate custom sequences
        self.seq_box = ui_dlg.seq_text_edit
        self.seq_box.textChanged.connect(self.validateCustomSequence)
        self.highlighter = DNAHighlighter(self.seq_box)
        # finally, pre-click the M13mp18 radio button
        self.buttons[0].click()
        buttons = self.buttons

        self.dialog.setFocusProxy(ui_dlg.group_box)
        self.dialog.setFocusPolicy(Qt.TabFocus)
        ui_dlg.group_box.setFocusPolicy(Qt.TabFocus)
        for i in range(len(buttons)-1):
            ui_dlg.group_box.setTabOrder(buttons[i], buttons[i+1])

    def tabWidgetChangedSlot(self, index):
        apply_enabled = False
        if index == 1:  # Custom Sequence
            self.validateCustomSequence()
            if self.custom_sequence_is_valid:
                apply_enabled = True
        else:  # Standard Sequence
            self.use_custom_sequence = False
            if self.chosen_standard_sequence != None:
                # Overwrite sequence in case custom has been applied
                active_button = self.buttons[self.chosen_standard_sequence]
                sequence_name = active_button.text()
                self.validated_sequence_to_apply = sequences.get(sequence_name, None)
                apply_enabled = True
        self.apply_button.setEnabled(apply_enabled)

    def standardSequenceChangedSlot(self, optionChosen):
        """
        Connected to signal_mapper to receive a signal whenever user selects
        a different sequence in the standard tab.
        """
        sequence_name = self.buttons[optionChosen].text()
        self.validated_sequence_to_apply = sequences.get(sequence_name, None)
        self.chosen_standard_sequence = optionChosen
        self.apply_button.setEnabled(True)

    def validateCustomSequence(self):
        """
        Called when:
        1. User enters custom sequence (i.e. seq_box emits textChanged signal)
        2. tabWidgetChangedSlot sees the user has switched to custom tab.

        When the sequence is valid, make the apply_button active for clicking.
        Otherwise
        """
        user_sequence = self.seq_box.toPlainText()
        if len(user_sequence) == 0:
            self.custom_sequence_is_valid = False
            return  # tabWidgetChangedSlot will disable apply_button
        if dnapattern.indexIn(user_sequence) == -1:  # no invalid characters
            self.use_custom_sequence = True
            self.custom_sequence_is_valid = True
            self.apply_button.setEnabled(True)
        else:
            self.custom_sequence_is_valid = False
            self.apply_button.setEnabled(False)

    def applySequence(self, oligo):
        self.dialog.setFocus()
        if self.dialog.exec_():  # apply the sequence if accept was clicked
            if self.use_custom_sequence:
                self.validated_sequence_to_apply = self.seq_box.toPlainText().upper()
            oligo.applySequence(self.validated_sequence_to_apply)
            return oligo.length(), len(self.validated_sequence_to_apply)
        return (None, None)
