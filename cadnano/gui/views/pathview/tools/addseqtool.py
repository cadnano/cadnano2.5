import re

from PyQt5.QtCore import Qt, QObject, QPointF, QRegExp, QSignalMapper, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QRadioButton

from cadnano.data.dnasequences import sequences
from cadnano.enum import StrandType
from cadnano.gui.ui.dialogs.ui_addseq import Ui_AddSeqDialog
from cadnano.gui.views.pathview import pathstyles as styles
from cadnano.gui.palette import getColorObj, getPenObj, getBrushObj

from .abstractpathtool import AbstractPathTool

RE_DNA_PATTERN = re.compile("[^ACGTacgt]")

class DNAHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        self.format = QTextCharFormat()
        self.format.setForeground(getBrushObj(Qt.white))
        self.format.setBackground(getBrushObj(styles.INVALID_DNA_COLOR))
        if styles.UNDERLINE_INVALID_DNA:
            self.format.setFontUnderline(True)
            self.format.setUnderlineColor(getColorObj(styles.INVALID_DNA_COLOR))

    def highlightBlock(self, text):
        for match in re.finditer(RE_DNA_PATTERN, text):
            index = match.start()
            length = match.end() - index
            self.setFormat(index, length, self.format)
        self.setCurrentBlockState(0)

class AddSeqTool(AbstractPathTool):
    def __init__(self, manager):
        AbstractPathTool.__init__(self, manager)
        self.dialog = QDialog()
        self.buttons = []
        self.seq_box = None
        self.sequence_radio_button_id = {}
        self.use_abstract_sequence = True
        self.validated_sequence_to_apply = None
        self.initDialog()

    def __repr__(self):
        return "add_seq_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "addSeqTool"  # first letter should be lowercase

    def initDialog(self):
        """
        1. Create buttons for each sequence option and add them to the dialog.
        2. Map the clicked signal of those buttons to keep track of what
        sequence gets selected.
        """
        ui_dlg = Ui_AddSeqDialog()
        ui_dlg.setupUi(self.dialog)
        self.signal_mapper = QSignalMapper(self)
        # set up the radio buttons
        for i, name in enumerate(['Abstract', 'Custom'] + sorted(sequences.keys())):
            radio_button = QRadioButton(ui_dlg.group_box)
            radio_button.setObjectName(name + "Button")
            radio_button.setText(name)
            self.buttons.append(radio_button)
            ui_dlg.horizontalLayout.addWidget(radio_button)
            self.signal_mapper.setMapping(radio_button, i)
            radio_button.clicked.connect(self.signal_mapper.map)
            if name in sequences:
                self.sequence_radio_button_id[sequences[name]] = i
        self.signal_mapper.mapped.connect(self.sequenceOptionChangedSlot)
        # disable apply until valid option or custom sequence is chosen
        self.apply_button = ui_dlg.custom_button_box.button(QDialogButtonBox.Apply)
        self.apply_button.setEnabled(False)
        # watch sequence textedit box to validate custom sequences
        self.seq_box = ui_dlg.seq_text_edit
        self.seq_box.textChanged.connect(self.validateCustomSequence)
        self.highlighter = DNAHighlighter(self.seq_box)
        # finally, pre-click the first radio button
        self.buttons[0].click()

    def sequenceOptionChangedSlot(self, option_chosen):
        """
        Connects to signal_mapper to receive a signal whenever user selects
        a sequence option.
        """
        option_name = self.buttons[option_chosen].text()
        if option_name == 'Abstract':
            self.use_abstract_sequence = True
        elif option_name == 'Custom':
            self.use_abstract_sequence = False
        else:
            self.use_abstract_sequence = False
            user_sequence = sequences.get(option_name, None)
            if self.seq_box.toPlainText() != user_sequence:
                self.seq_box.setText(user_sequence)

    def validateCustomSequence(self):
        """
        Called when user changes sequence (seq_box emits textChanged signal)
        If sequence is valid, make the apply_button active to click.
        Select an appropriate sequence option radio button, if necessary.
        """
        user_sequence = self.seq_box.toPlainText()
        # Validate the sequence and activate the button if it checks out.
        if re.search(RE_DNA_PATTERN, user_sequence) is None:
            self.apply_button.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)

        if len(user_sequence) == 0:
            # A zero-length custom sequence defaults to Abstract type.
            if not self.buttons[0].isChecked():
                self.buttons[0].click()
        else: 
            # Does this match a known sequence?
            if user_sequence in self.sequence_radio_button_id:
                # Handles case where the user might copy & paste in a known sequence
                i = self.sequence_radio_button_id[user_sequence]
                if not self.buttons[i].isChecked():
                    # Select the corresponding radio button for known sequence
                    self.buttons[i].click()
            else:
                # Unrecognized, Custom type
                if not self.buttons[1].isChecked():
                    self.buttons[1].click()

    def applySequence(self, oligo):
        self.dialog.setFocus()
        if self.dialog.exec_():  # apply the sequence if accept was clicked
            if self.use_abstract_sequence:
                oligo.applySequence(None)
                return (oligo.length(), None)
            else:
                self.validated_sequence_to_apply = self.seq_box.toPlainText().upper()
                oligo.applySequence(self.validated_sequence_to_apply)
                return oligo.length(), len(self.validated_sequence_to_apply)
        return (None, None)
