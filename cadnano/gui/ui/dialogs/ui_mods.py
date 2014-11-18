# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mods.ui'
#
# Created: Sun Oct 12 21:39:36 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ModsDialog(object):
    def setupUi(self, ModsDialog):
        ModsDialog.setObjectName("ModsDialog")
        ModsDialog.resize(500, 500)
        ModsDialog.setModal(True)
        self.dialogGridLayout = QtWidgets.QGridLayout(ModsDialog)
        self.dialogGridLayout.setObjectName("dialogGridLayout")
        self.custom_button_box = QtWidgets.QDialogButtonBox(ModsDialog)
        self.custom_button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel)
        self.custom_button_box.setCenterButtons(True)
        self.custom_button_box.setObjectName("custom_button_box")
        self.dialogGridLayout.addWidget(self.custom_button_box, 1, 0, 1, 1)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName("formLayout_2")
        self.nameLabel = QtWidgets.QLabel(ModsDialog)
        self.nameLabel.setObjectName("nameLabel")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.nameLabel)
        self.nameComboBox = QtWidgets.QComboBox(ModsDialog)
        self.nameComboBox.setEditable(True)
        self.nameComboBox.setObjectName("nameComboBox")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nameComboBox)
        self.colorLabel = QtWidgets.QLabel(ModsDialog)
        self.colorLabel.setObjectName("colorLabel")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.colorLabel)
        self.colorLineEdit = QtWidgets.QLineEdit(ModsDialog)
        self.colorLineEdit.setObjectName("colorLineEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.colorLineEdit)
        self.sequence5Label = QtWidgets.QLabel(ModsDialog)
        self.sequence5Label.setObjectName("sequence5Label")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.sequence5Label)
        self.sequence5LineEdit = QtWidgets.QLineEdit(ModsDialog)
        self.sequence5LineEdit.setObjectName("sequence5LineEdit")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.sequence5LineEdit)
        self.sequence3Label = QtWidgets.QLabel(ModsDialog)
        self.sequence3Label.setObjectName("sequence3Label")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.sequence3Label)
        self.sequence3LineEdit = QtWidgets.QLineEdit(ModsDialog)
        self.sequence3LineEdit.setObjectName("sequence3LineEdit")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.sequence3LineEdit)
        self.sequenceInternalLabel = QtWidgets.QLabel(ModsDialog)
        self.sequenceInternalLabel.setObjectName("sequenceInternalLabel")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.sequenceInternalLabel)
        self.sequenceInternalLineEdit = QtWidgets.QLineEdit(ModsDialog)
        self.sequenceInternalLineEdit.setObjectName("sequenceInternalLineEdit")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.sequenceInternalLineEdit)
        self.noteLabel = QtWidgets.QLabel(ModsDialog)
        self.noteLabel.setObjectName("noteLabel")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.noteLabel)
        self.noteTextEdit = QtWidgets.QTextEdit(ModsDialog)
        self.noteTextEdit.setObjectName("noteTextEdit")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.noteTextEdit)
        self.dialogGridLayout.addLayout(self.formLayout_2, 0, 0, 1, 1)

        self.retranslateUi(ModsDialog)
        self.custom_button_box.rejected.connect(ModsDialog.reject)
        self.custom_button_box.clicked['QAbstractButton*'].connect(ModsDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(ModsDialog)

    def retranslateUi(self, ModsDialog):
        _translate = QtCore.QCoreApplication.translate
        ModsDialog.setWindowTitle(_translate("ModsDialog", "Choose a Modification"))
        self.nameLabel.setText(_translate("ModsDialog", "Name"))
        self.colorLabel.setText(_translate("ModsDialog", "color"))
        self.sequence5Label.setText(_translate("ModsDialog", "sequence 5\'"))
        self.sequence3Label.setText(_translate("ModsDialog", "sequence 3\'"))
        self.sequenceInternalLabel.setText(_translate("ModsDialog", "sequence internal"))
        self.noteLabel.setText(_translate("ModsDialog", "Note"))

