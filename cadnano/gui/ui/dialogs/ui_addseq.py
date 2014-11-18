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
        self.tab_widget = QtWidgets.QTabWidget(AddSeqDialog)
        self.tab_widget.setObjectName("tab_widget")
        self.tab_standard = QtWidgets.QWidget()
        self.tab_standard.setObjectName("tab_standard")
        self.standardTabGridLayout = QtWidgets.QGridLayout(self.tab_standard)
        self.standardTabGridLayout.setObjectName("standardTabGridLayout")
        self.group_box = QtWidgets.QGroupBox(self.tab_standard)
        self.group_box.setTitle("")
        self.group_box.setFlat(True)
        self.group_box.setObjectName("group_box")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.group_box)
        self.verticalLayout.setObjectName("verticalLayout")
        self.standardTabGridLayout.addWidget(self.group_box, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem, 0, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.standardTabGridLayout.addItem(spacerItem1, 0, 0, 1, 1)
        self.tab_widget.addTab(self.tab_standard, "")
        self.tab_custom = QtWidgets.QWidget()
        self.tab_custom.setObjectName("tab_custom")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab_custom)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.seq_text_edit = QtWidgets.QTextEdit(self.tab_custom)
        self.seq_text_edit.setObjectName("seq_text_edit")
        self.verticalLayout_2.addWidget(self.seq_text_edit)
        self.tab_widget.addTab(self.tab_custom, "")
        self.dialogGridLayout.addWidget(self.tab_widget, 0, 0, 1, 1)
        self.custom_button_box = QtWidgets.QDialogButtonBox(AddSeqDialog)
        self.custom_button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel)
        self.custom_button_box.setCenterButtons(True)
        self.custom_button_box.setObjectName("custom_button_box")
        self.dialogGridLayout.addWidget(self.custom_button_box, 1, 0, 1, 1)

        self.retranslateUi(AddSeqDialog)
        self.tab_widget.setCurrentIndex(0)
        self.custom_button_box.rejected.connect(AddSeqDialog.reject)
        self.custom_button_box.clicked['QAbstractButton*'].connect(AddSeqDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AddSeqDialog)
        AddSeqDialog.setTabOrder(self.custom_button_box, self.tab_widget)
        AddSeqDialog.setTabOrder(self.tab_widget, self.seq_text_edit)

    def retranslateUi(self, AddSeqDialog):
        _translate = QtCore.QCoreApplication.translate
        AddSeqDialog.setWindowTitle(_translate("AddSeqDialog", "Choose a sequence"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_standard), _translate("AddSeqDialog", "Standard"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_custom), _translate("AddSeqDialog", "Custom"))

