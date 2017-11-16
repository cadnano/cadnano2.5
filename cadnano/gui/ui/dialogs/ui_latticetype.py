# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'latticetype.ui'
#
# Created: Sun Oct 12 21:39:15 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LatticeType(object):
    def setupUi(self, LatticeType):
        LatticeType.setObjectName("LatticeType")
        LatticeType.resize(215, 80)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LatticeType.sizePolicy().hasHeightForWidth())
        LatticeType.setSizePolicy(sizePolicy)
        LatticeType.setSizeGripEnabled(False)
        self.verticalLayout = QtWidgets.QVBoxLayout(LatticeType)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(LatticeType)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.buttonBox = QtWidgets.QDialogButtonBox(LatticeType)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No|QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(LatticeType)
        self.buttonBox.accepted.connect(LatticeType.accept)
        self.buttonBox.rejected.connect(LatticeType.reject)
        QtCore.QMetaObject.connectSlotsByName(LatticeType)

    def retranslateUi(self, LatticeType):
        _translate = QtCore.QCoreApplication.translate
        LatticeType.setWindowTitle(_translate("LatticeType", "Import"))
        self.label.setText(_translate("LatticeType", "Is this a square lattice design?"))

