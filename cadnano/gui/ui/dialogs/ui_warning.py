# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'warning.ui'
#
# Created: Sun Oct 12 21:40:14 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Warning(object):
    def setupUi(self, Warning):
        Warning.setObjectName("Warning")
        Warning.setWindowModality(QtCore.Qt.ApplicationModal)
        Warning.resize(400, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(Warning)
        self.buttonBox.setGeometry(QtCore.QRect(30, 250, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.title = QtWidgets.QLabel(Warning)
        self.title.setGeometry(QtCore.QRect(20, 30, 361, 31))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.title.setFont(font)
        self.title.setObjectName("title")
        self.message = QtWidgets.QLabel(Warning)
        self.message.setGeometry(QtCore.QRect(20, 80, 361, 151))
        self.message.setWordWrap(True)
        self.message.setObjectName("message")

        self.retranslateUi(Warning)
        self.buttonBox.accepted.connect(Warning.accept)
        self.buttonBox.rejected.connect(Warning.reject)
        QtCore.QMetaObject.connectSlotsByName(Warning)

    def retranslateUi(self, Warning):
        _translate = QtCore.QCoreApplication.translate
        Warning.setWindowTitle(_translate("Warning", "Dialog"))
        self.title.setText(_translate("Warning", "Warning"))
        self.message.setText(_translate("Warning", "Text here."))

