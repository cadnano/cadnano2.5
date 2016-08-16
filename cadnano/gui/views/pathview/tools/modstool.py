"""Summary
"""
from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QPushButton

from cadnano.data.sequencemods import mods
from cadnano.gui.ui.dialogs.ui_mods import Ui_ModsDialog

from .abstractpathtool import AbstractPathTool


def _fromUtf8(s):
    """Summary

    Args:
        s (TYPE): Description

    Returns:
        TYPE: Description
    """
    return s


class ModsTool(AbstractPathTool):
    """
    docstring for ModsTool

    Attributes:
        current_idx (int): the base index within the virtual helix
        current_strand (TYPE): Description
        dialog (TYPE): Description
        uiDlg (TYPE): Description
    """
    def __init__(self, manager):
        """Summary

        Args:
            manager (TYPE): Description
        """
        super(ModsTool, self).__init__(manager)
        self.dialog = QDialog()
        self.initDialog()
        self.current_strand = None
        self.current_idx = None

    def __repr__(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return "mods_tool"  # first letter should be lowercase

    def methodPrefix(self):
        """Summary

        Returns:
            TYPE: Description
        """
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
        """Summary

        Returns:
            TYPE: Description
        """
        # part = self.current_strand.part()
        doc = self.manager.document

        item, mid = self.getCurrentItem()
        if mid == "new":
            item, mid = doc.createMod(item)
            # combobox = self.uiDlg.nameComboBox
            # combobox.addItem(item['name'], mid)
        elif doc.getMod(mid) is None:
            item, mid = doc.createMod(item, mid=mid)
        else:
            doc.modifyMod(item, mid)
        return
    # end def

    def deleteModChecker(self):
        """Summary

        Returns:
            TYPE: Description
        """
        # part = self.current_strand.part()
        doc = self.manager.document
        item, mid = self.getCurrentItem()
        if mid != "new":
            doc.destroyMod(mid)
    # end def

    def deleteInstModChecker(self):
        """Summary

        Returns:
            TYPE: Description
        """
        strand = self.current_strand
        idx = self.current_idx
        part = strand.part()
        mid = part.getModID(strand, idx)
        if mid:
            strand.removeMods(self.manager.document, mid, idx)
        # part.removeModInstance(mid)
    # end def

    def getCurrentItem(self, mid=None):
        """Summary

        Args:
            mid (None, optional): Description

        Returns:
            TYPE: Description
        """
        uiDlg = self.uiDlg
        combobox = uiDlg.nameComboBox
        if mid is None:
            idx = combobox.currentIndex()
            mid = combobox.itemData(idx)
            # mid = str(qvmid.toString())
        item = {}
        item['name'] = str(combobox.currentText())  # str(combobox.itemText(idx))
        item['color'] = str(uiDlg.colorLineEdit.text())
        item['seq5p'] = str(uiDlg.sequence5LineEdit.text())
        item['seq3p'] = str(uiDlg.sequence3LineEdit.text())
        item['seqInt'] = str(uiDlg.sequenceInternalLineEdit.text())
        item['note'] = str(uiDlg.noteTextEdit.toPlainText())  # notes
        return item, mid
    # end def

    def retrieveCurrentItem(self):
        """Summary

        Returns:
            TYPE: Description
        """
        uiDlg = self.uiDlg
        combobox = uiDlg.nameComboBox
        idx = combobox.currentIndex()
        mid = combobox.itemData(idx)
        if mid == 'new':
            return self.getCurrentItem(mid)
        return mods.get(mid), mid
    # end def

    def getItemIdxByMID(self, mid):
        """Summary

        Args:
            mid (TYPE): Description

        Returns:
            TYPE: Description
        """
        combobox = self.uiDlg.nameComboBox
        idx = combobox.findData(mid)
        if idx > -1:
            return idx

    def displayCurrent(self):
        """Summary

        Returns:
            TYPE: Description
        """
        item, mid = self.retrieveCurrentItem()
        if mid != 'new':
            uiDlg = self.uiDlg
            uiDlg.colorLineEdit.setText(item['color'])
            uiDlg.sequence5LineEdit.setText(item['seq5p'])
            uiDlg.sequence3LineEdit.setText(item['seq3p'])
            uiDlg.sequenceInternalLineEdit.setText(item['seqInt'])
            uiDlg.noteTextEdit.setText(item['note'])  # notes
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

    def connectSignals(self, document):
        """Summary

        Args:
            document (TYPE): Description

        Returns:
            TYPE: Description
        """
        document.documentModAddedSignal.connect(self.updateDialogMods)
        document.documentModRemovedSignal.connect(self.deleteDialogMods)
        document.documentModChangedSignal.connect(self.updateDialogMods)
    # end def

    def disconnectSignals(self, document):
        """Summary

        Args:
            document (TYPE): Description

        Returns:
            TYPE: Description
        """
        document.documentModAddedSignal.disconnect(self.updateDialogMods)
        document.documentModRemovedSignal.disconnect(self.deleteDialogMods)
        document.documentModChangedSignal.disconnect(self.updateDialogMods)
    # end def

    def updateDialogMods(self, part, item, mid):
        """Summary

        Args:
            part (TYPE): Description
            item (TYPE): Description
            mid (TYPE): Description

        Returns:
            TYPE: Description
        """
        local_item = mods.get(mid)
        combobox = self.uiDlg.nameComboBox
        if local_item:
            local_item.update(item)
            idx = self.getItemIdxByMID(mid)
            if idx:
                try:
                    combobox.setItemText(idx, item['name'])
                except:
                    print(local_item)
                    print(item)
                    raise
        else:
            # print "adding a mods", item, mid
            mods[mid] = {}
            mods[mid].update(item)
            combobox.addItem(item['name'], mid)
        self.displayCurrent()
    # end def

    def deleteDialogMods(self, part, mid):
        """Summary

        Args:
            part (TYPE): Description
            mid (TYPE): Description

        Returns:
            TYPE: Description
        """
        local_item = mods.get(mid)
        combobox = self.uiDlg.nameComboBox
        if local_item:
            del mods[mid]
            idx = self.getItemIdxByMID(mid)
            combobox.removeItem(idx)
        self.displayCurrent()
    # end def

    def applyMod(self, strand, idx):
        """Summary

        Args:
            strand (TYPE): Description
            idx (int): the base index within the virtual helix

        Returns:
            TYPE: Description
        """
        self.current_strand = strand
        self.current_idx = idx
        part = strand.part()
        document = self.manager.document
        self.connectSignals(document)
        self.dialog.show()
        mid = part.getModID(strand, idx)
        if mid:
            combobox = self.uiDlg.nameComboBox
            mod = document.getModProperties(mid)
            # print(mod, mid)
            cidx = combobox.findText(mod['name'])
            combobox.setCurrentIndex(cidx)
        self.dialog.setFocus()
        if self.dialog.exec_():  # apply the sequence if accept was clicked
            item, mod_id = self.getCurrentItem()
            strand.addMods(document, mod_id, idx)
            self.disconnectSignals(document)
