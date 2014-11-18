import sys
from .abstractpathtool import AbstractPathTool
from cadnano.data.sequencemods import mods
from cadnano.gui.ui.dialogs.ui_mods import Ui_ModsDialog
import cadnano.util as util

from PyQt5.QtCore import QSignalMapper
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QPushButton

def _fromUtf8(s):
    return s

class ModsTool(AbstractPathTool):
    """
    docstring for ModsTool
    """
    def __init__(self, controller):
        super(ModsTool, self).__init__(controller)
        self.dialog = QDialog()
        self.initDialog()
        self.current_strand = None
        self.current_idx = None

    def __repr__(self):
        return "mods_tool"  # first letter should be lowercase

    def methodPrefix(self):
        return "modsTool"  # first letter should be lowercase

    def initDialog(self):
        """
        """
        uiDlg = Ui_ModsDialog()
        uiDlg.setupUi(self.dialog)

        uiDlg.createButtonBox = QDialogButtonBox(self.dialog)
        uiDlg.createButtonBox.setCenterButtons(True)
        uiDlg.custom_button_box.setObjectName(_fromUtf8("createButtonBox"))
        uiDlg.dialogGridLayout.addWidget(uiDlg.createButtonBox, 2, 0, 1, 1)
        
        saveButton = QPushButton("Save", uiDlg.createButtonBox)
        uiDlg.createButtonBox.addButton(saveButton, QDialogButtonBox.ActionRole)
        saveButton.released.connect(self.saveModChecker)

        deleteButton = QPushButton("Delete", uiDlg.createButtonBox)
        uiDlg.createButtonBox.addButton(deleteButton, QDialogButtonBox.ActionRole)
        deleteButton.released.connect(self.deleteModChecker)

        uiDlg.instanceButtonBox = QDialogButtonBox(self.dialog)
        uiDlg.instanceButtonBox.setCenterButtons(True)
        uiDlg.instanceButtonBox.setObjectName(_fromUtf8("instanceButtonBox"))
        uiDlg.dialogGridLayout.addWidget(uiDlg.instanceButtonBox, 3, 0, 1, 1)

        deleteInstButton = QPushButton("Delete Instance", uiDlg.instanceButtonBox)
        uiDlg.instanceButtonBox.addButton(deleteInstButton, QDialogButtonBox.ActionRole)
        deleteInstButton.released.connect(self.deleteInstModChecker)

        combobox = uiDlg.nameComboBox
        self.uiDlg = uiDlg
        combobox.addItem("New", "new")
        for mid, item in mods.items():
            combobox.addItem(item['name'], mid)
        # end for
        combobox.currentIndexChanged.connect(self.displayCurrent)
        self.displayCurrent()

    def saveModChecker(self):
        part = self.current_strand.part()
        item, mid = self.getCurrentItem()
        # print "save clicked", mid, item
        if mid == "new":
            item, mid = part.createMod(item)
            # combobox = self.uiDlg.nameComboBox
            # combobox.addItem(item['name'], mid)
        elif part.getMod(mid) is None: 
            item, mid = part.createMod(item, mid=mid)
        else:
            # print "modifying mod"
            part.modifyMod(item, mid)
        return 
    # end def

    def deleteModChecker(self):
        part = self.current_strand.part()
        item, mid = self.getCurrentItem() 
        if mid != "new":
            part.destroyMod(mid)
    # end def

    def deleteInstModChecker(self):
        strand = self.current_strand
        idx = self.current_idx
        part = strand.part()
        mid = part.getModID(strand, idx)
        if mid:
            strand.removeMods(mid, idx)
        # part.removeModInstance(mid)
    # end def

    def getCurrentItem(self, mid=None):
        uiDlg = self.uiDlg
        combobox = uiDlg.nameComboBox
        if mid is None:
            idx = combobox.currentIndex()
            mid = combobox.itemData(idx)
            # mid = str(qvmid.toString())
        item = {}
        item['name'] = str(combobox.currentText()) ##str(combobox.itemText(idx))
        item['color'] = str(uiDlg.colorLineEdit.text())
        item['seq5p'] = str(uiDlg.sequence5LineEdit.text())
        item['seq3p'] = str(uiDlg.sequence3LineEdit.text())
        item['seqInt'] = str(uiDlg.sequenceInternalLineEdit.text())
        item['note'] = str(uiDlg.noteTextEdit.toPlainText()) # notes
        return item, mid
    # end def

    def retrieveCurrentItem(self):
        uiDlg = self.uiDlg
        combobox = uiDlg.nameComboBox
        idx = combobox.currentIndex()
        mid = combobox.itemData(idx)
        if mid == 'new':
            return self.getCurrentItem(mid)
        return mods.get(mid), mid
    # end def

    def getItemIdxByMID(self, mid):
        combobox = self.uiDlg.nameComboBox
        idx = combobox.findData(mid)
        if idx > -1:
            return idx

    def displayCurrent(self):
        item, mid = self.retrieveCurrentItem()
        if mid != 'new':
            uiDlg = self.uiDlg
            uiDlg.colorLineEdit.setText(item['color'])
            uiDlg.sequence5LineEdit.setText(item['seq5p'])
            uiDlg.sequence3LineEdit.setText(item['seq3p'])
            uiDlg.sequenceInternalLineEdit.setText(item['seqInt'])
            uiDlg.noteTextEdit.setText(item['note']) # notes
    # end def

    # def saveCurrent(self):
    #     item, mid = self.getCurrentItem()
    #     uiDlg = self.uiDlg
    #     item['name'] = str(uiDlg.nameComboBox.currentText())
    #     item['color'] = str(uiDlg.colorLineEdit.text())
    #     item['seq5p'] = str(uiDlg.sequence5LineEdit.text())
    #     item['seq3p'] = str(uiDlg.sequence3LineEdit.text())
    #     item['seqInt'] = str(uiDlg.sequenceInternalLineEdit.text())
    #     item['note'] = str(uiDlg.noteTextEdit.toPlainText()) # notes
    # # end def

    def connectSignals(self, part):
        part.partModAddedSignal.connect(self.updateDialogMods)
        part.partModRemovedSignal.connect(self.deleteDialogMods)
        part.partModChangedSignal.connect(self.updateDialogMods)
    # end def

    def disconnectSignals(self, part):
        part.partModAddedSignal.disconnect(self.updateDialogMods)
        part.partModRemovedSignal.disconnect(self.deleteDialogMods)
        part.partModChangedSignal.disconnect(self.updateDialogMods)
    # end def

    def updateDialogMods(self, part, item, mid):
        local_item = mods.get(mid)
        combobox = self.uiDlg.nameComboBox
        if local_item:
            local_item.update(item)
            idx = self.getItemIdxByMID(mid)
            if idx:
                combobox.setItemText(idx, item['name'])
        else:
            # print "adding a mods", item, mid
            mods[mid] = {}
            mods[mid].update(item)
            combobox.addItem(item['name'], mid)
        self.displayCurrent()
    # end def

    def deleteDialogMods(self, part, mid):
        local_item = mods.get(mid)
        combobox = self.uiDlg.nameComboBox
        if local_item:
            del mods[mid]
            idx = self.getItemIdxByMID(mid)
            combobox.removeItem(idx)
        self.displayCurrent()
    # end def

    def applyMod(self, strand, idx):
        self.current_strand = strand
        self.current_idx = idx
        part = strand.part()
        self.connectSignals(part)
        self.dialog.show()
        mid = part.getModID(strand, idx)
        if mid:
            combobox = self.uiDlg.nameComboBox
            mod = strand.part().getMod(mid)
            # print mod, mid
            cidx = combobox.findText(mod['name'])
            combobox.setCurrentIndex(cidx)
        self.dialog.setFocus()
        if self.dialog.exec_():  # apply the sequence if accept was clicked
            item, mid = self.getCurrentItem()
            strand.addMods(mid, idx)
            self.disconnectSignals(part)
