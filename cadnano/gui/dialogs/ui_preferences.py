# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialogs/preferences.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName("Preferences")
        Preferences.resize(465, 374)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Preferences.sizePolicy().hasHeightForWidth())
        Preferences.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Preferences)
        self.verticalLayout.setObjectName("verticalLayout")
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldsStayAtSizeHint)
        self.form_layout.setObjectName("form_layout")
        self.enabled_sliceview_label = QtWidgets.QLabel(Preferences)
        self.enabled_sliceview_label.setObjectName("enabled_sliceview_label")
        self.form_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.enabled_sliceview_label)
        self.enabled_orthoview_combo_box = QtWidgets.QComboBox(Preferences)
        self.enabled_orthoview_combo_box.setObjectName("enabled_orthoview_combo_box")
        self.enabled_orthoview_combo_box.addItem("")
        self.enabled_orthoview_combo_box.addItem("")
        self.form_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.enabled_orthoview_combo_box)
        self.Grid = QtWidgets.QLabel(Preferences)
        self.Grid.setObjectName("Grid")
        self.form_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.Grid)
        self.gridview_style_combo_box = QtWidgets.QComboBox(Preferences)
        self.gridview_style_combo_box.setObjectName("gridview_style_combo_box")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/part/grid_points"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.gridview_style_combo_box.addItem(icon, "")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/part/grid_lines"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.gridview_style_combo_box.addItem(icon1, "")
        self.form_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.gridview_style_combo_box)
        self.zoom_speed_label = QtWidgets.QLabel(Preferences)
        self.zoom_speed_label.setObjectName("zoom_speed_label")
        self.form_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.zoom_speed_label)
        self.zoom_speed_slider = QtWidgets.QSlider(Preferences)
        self.zoom_speed_slider.setMinimumSize(QtCore.QSize(140, 0))
        self.zoom_speed_slider.setMinimum(1)
        self.zoom_speed_slider.setMaximum(100)
        self.zoom_speed_slider.setSingleStep(1)
        self.zoom_speed_slider.setProperty("value", 50)
        self.zoom_speed_slider.setOrientation(QtCore.Qt.Horizontal)
        self.zoom_speed_slider.setInvertedControls(False)
        self.zoom_speed_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.zoom_speed_slider.setTickInterval(0)
        self.zoom_speed_slider.setObjectName("zoom_speed_slider")
        self.form_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.zoom_speed_slider)
        self.show_icon_label_text = QtWidgets.QLabel(Preferences)
        self.show_icon_label_text.setObjectName("show_icon_label_text")
        self.form_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.show_icon_label_text)
        self.show_icon_labels = QtWidgets.QCheckBox(Preferences)
        self.show_icon_labels.setChecked(True)
        self.show_icon_labels.setObjectName("show_icon_labels")
        self.form_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.show_icon_labels)
        self.verticalLayout.addLayout(self.form_layout)
        self.button_box = QtWidgets.QDialogButtonBox(Preferences)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.RestoreDefaults)
        self.button_box.setObjectName("button_box")
        self.verticalLayout.addWidget(self.button_box)
        self.actionClose = QtWidgets.QAction(Preferences)
        self.actionClose.setObjectName("actionClose")

        self.retranslateUi(Preferences)
        QtCore.QMetaObject.connectSlotsByName(Preferences)

    def retranslateUi(self, Preferences):
        _translate = QtCore.QCoreApplication.translate
        Preferences.setWindowTitle(_translate("Preferences", "Preferences"))
        self.enabled_sliceview_label.setText(_translate("Preferences", "Slice View"))
        self.enabled_orthoview_combo_box.setItemText(0, _translate("Preferences", "Legacy Slice View"))
        self.enabled_orthoview_combo_box.setItemText(1, _translate("Preferences", "Grid View"))
        self.Grid.setText(_translate("Preferences", "Grid Appearance"))
        self.gridview_style_combo_box.setItemText(0, _translate("Preferences", "Points"))
        self.gridview_style_combo_box.setItemText(1, _translate("Preferences", "Lines"))
        self.zoom_speed_label.setText(_translate("Preferences", "Mousewheel zoom speed:"))
        self.show_icon_label_text.setText(_translate("Preferences", "Show Icon Labels:"))
        self.show_icon_labels.setText(_translate("Preferences", "(needs restart)"))
        self.actionClose.setText(_translate("Preferences", "Close"))
        self.actionClose.setShortcut(_translate("Preferences", "Ctrl+W"))

import cadnano.gui.dialogs.dialogicons_rc
