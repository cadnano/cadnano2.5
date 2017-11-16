# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialogs/addseq.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AddSeqDialog(object):
    def setupUi(self, AddSeqDialog):
        AddSeqDialog.setObjectName("AddSeqDialog")
        AddSeqDialog.resize(800, 600)
        AddSeqDialog.setModal(True)
        self.dialogGridLayout = QtWidgets.QGridLayout(AddSeqDialog)
        self.dialogGridLayout.setObjectName("dialogGridLayout")
        self.custom_button_box = QtWidgets.QDialogButtonBox(AddSeqDialog)
        self.custom_button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel)
        self.custom_button_box.setCenterButtons(True)
        self.custom_button_box.setObjectName("custom_button_box")
        self.dialogGridLayout.addWidget(self.custom_button_box, 1, 0, 1, 1)
        self.frame = QtWidgets.QFrame(AddSeqDialog)
        self.frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.seq_text_edit = QtWidgets.QTextEdit(self.frame)
        self.seq_text_edit.setObjectName("seq_text_edit")
        self.verticalLayout.addWidget(self.seq_text_edit)
        self.group_box = QtWidgets.QGroupBox(self.frame)
        self.group_box.setTitle("")
        self.group_box.setObjectName("group_box")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.group_box)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addWidget(self.group_box, 0, QtCore.Qt.AlignVCenter)
        self.dialogGridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(AddSeqDialog)
        self.custom_button_box.rejected.connect(AddSeqDialog.reject)
        self.custom_button_box.clicked['QAbstractButton*'].connect(AddSeqDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AddSeqDialog)

    def retranslateUi(self, AddSeqDialog):
        _translate = QtCore.QCoreApplication.translate
        AddSeqDialog.setWindowTitle(_translate("AddSeqDialog", "Choose a sequence"))

