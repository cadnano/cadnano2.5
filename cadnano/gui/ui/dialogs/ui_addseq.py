# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'addseq.ui'
#
# Created: Sun Oct 12 21:38:56 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AddSeqDialog(object):
    def setupUi(self, AddSeqDialog):
        AddSeqDialog.setObjectName("AddSeqDialog")
        AddSeqDialog.resize(500, 500)
        AddSeqDialog.setModal(True)
        self.dialogGridLayout = QtWidgets.QGridLayout(AddSeqDialog)
        self.dialogGridLayout.setObjectName("dialogGridLayout")
        self.tabWidget = QtWidgets.QTabWidget(AddSeqDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tabStandard = QtWidgets.QWidget()
        self.tabStandard.setObjectName("tabStandard")
        self.standardTabGridLayout = QtWidgets.QGridLayout(self.tabStandard)
        self.standardTabGridLayout.setObjectName("standardTabGridLayout")
        self.groupBox = QtWidgets.QGroupBox(self.tabStandard)
        self.groupBox.setTitle("")
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.standardTabGridLayout.addWidget(self.groupBox, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem, 0, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem1, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabStandard, "")
        self.tabCustom = QtWidgets.QWidget()
        self.tabCustom.setObjectName("tabCustom")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tabCustom)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.seqTextEdit = QtWidgets.QTextEdit(self.tabCustom)
        self.seqTextEdit.setObjectName("seqTextEdit")
        self.verticalLayout_2.addWidget(self.seqTextEdit)
        self.tabWidget.addTab(self.tabCustom, "")
        self.dialogGridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.customButtonBox = QtWidgets.QDialogButtonBox(AddSeqDialog)
        self.customButtonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel)
        self.customButtonBox.setCenterButtons(True)
        self.customButtonBox.setObjectName("customButtonBox")
        self.dialogGridLayout.addWidget(self.customButtonBox, 1, 0, 1, 1)

        self.retranslateUi(AddSeqDialog)
        self.tabWidget.setCurrentIndex(0)
        self.customButtonBox.rejected.connect(AddSeqDialog.reject)
        self.customButtonBox.clicked['QAbstractButton*'].connect(AddSeqDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AddSeqDialog)
        AddSeqDialog.setTabOrder(self.customButtonBox, self.tabWidget)
        AddSeqDialog.setTabOrder(self.tabWidget, self.seqTextEdit)

    def retranslateUi(self, AddSeqDialog):
        _translate = QtCore.QCoreApplication.translate
        AddSeqDialog.setWindowTitle(_translate("AddSeqDialog", "Choose a sequence"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabStandard), _translate("AddSeqDialog", "Standard"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCustom), _translate("AddSeqDialog", "Custom"))

