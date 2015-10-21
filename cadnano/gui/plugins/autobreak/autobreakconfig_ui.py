# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'autobreakconfig.ui'
#
# Created by: PyQt5 UI code generator 5.5
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(297, 264)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.layoutWidget = QtWidgets.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 0, 276, 251))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldsStayAtSizeHint)
        self.formLayout.setObjectName("formLayout")
        self.maxLengthLabel = QtWidgets.QLabel(self.layoutWidget)
        self.maxLengthLabel.setObjectName("maxLengthLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.maxLengthLabel)
        self.maxLengthSpinBox = QtWidgets.QSpinBox(self.layoutWidget)
        self.maxLengthSpinBox.setMaximum(10000)
        self.maxLengthSpinBox.setProperty("value", 60)
        self.maxLengthSpinBox.setObjectName("maxLengthSpinBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.maxLengthSpinBox)
        self.targetLengthSpinBox = QtWidgets.QSpinBox(self.layoutWidget)
        self.targetLengthSpinBox.setMaximum(10000)
        self.targetLengthSpinBox.setProperty("value", 49)
        self.targetLengthSpinBox.setObjectName("targetLengthSpinBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.targetLengthSpinBox)
        self.targetLengthLabel = QtWidgets.QLabel(self.layoutWidget)
        self.targetLengthLabel.setObjectName("targetLengthLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.targetLengthLabel)
        self.minLengthLabel = QtWidgets.QLabel(self.layoutWidget)
        self.minLengthLabel.setObjectName("minLengthLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.minLengthLabel)
        self.minLengthSpinBox = QtWidgets.QSpinBox(self.layoutWidget)
        self.minLengthSpinBox.setMaximum(10000)
        self.minLengthSpinBox.setProperty("value", 15)
        self.minLengthSpinBox.setObjectName("minLengthSpinBox")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.minLengthSpinBox)
        self.minLegLengthLabel = QtWidgets.QLabel(self.layoutWidget)
        self.minLegLengthLabel.setObjectName("minLegLengthLabel")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.minLegLengthLabel)
        self.minLegLengthSpinBox = QtWidgets.QSpinBox(self.layoutWidget)
        self.minLegLengthSpinBox.setMinimum(2)
        self.minLegLengthSpinBox.setMaximum(10000)
        self.minLegLengthSpinBox.setProperty("value", 3)
        self.minLegLengthSpinBox.setObjectName("minLegLengthSpinBox")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.minLegLengthSpinBox)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.layoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.targetLengthSpinBox, self.minLengthSpinBox)
        Dialog.setTabOrder(self.minLengthSpinBox, self.maxLengthSpinBox)
        Dialog.setTabOrder(self.maxLengthSpinBox, self.minLegLengthSpinBox)
        Dialog.setTabOrder(self.minLegLengthSpinBox, self.buttonBox)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Choose autobreak parameters:"))
        self.maxLengthLabel.setText(_translate("Dialog", "max length"))
        self.targetLengthLabel.setText(_translate("Dialog", "target length"))
        self.minLengthLabel.setText(_translate("Dialog", "min length"))
        self.minLegLengthLabel.setText(_translate("Dialog", "min distance to xover"))

