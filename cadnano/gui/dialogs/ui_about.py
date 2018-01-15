# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialogs/about.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(474, 304)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About.sizePolicy().hasHeightForWidth())
        About.setSizePolicy(sizePolicy)
        About.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(About)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QtWidgets.QFrame(About)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(440, 270))
        self.frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setObjectName("frame")
        self.appname = QtWidgets.QLabel(self.frame)
        self.appname.setGeometry(QtCore.QRect(0, 10, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.appname.setFont(font)
        self.appname.setObjectName("appname")
        self.version = QtWidgets.QLabel(self.frame)
        self.version.setGeometry(QtCore.QRect(0, 40, 211, 31))
        self.version.setObjectName("version")
        self.info = QtWidgets.QLabel(self.frame)
        self.info.setGeometry(QtCore.QRect(0, 90, 441, 181))
        self.info.setTextFormat(QtCore.Qt.RichText)
        self.info.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.info.setWordWrap(True)
        self.info.setOpenExternalLinks(True)
        self.info.setObjectName("info")
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(About)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "About cadnano"))
        self.appname.setText(_translate("About", "cadnano"))
        self.version.setText(_translate("About", "version 2.5.1"))
        self.info.setText(_translate("About", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">Copyright © 2009–2018 </span><a href=\"http://cadnano.org/\"><span style=\" text-decoration: underline; color:#0000ff;\">http://cadnano.org/</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">Cadnano 2.5 was written by Nick Conway, Shawn Douglas, and </span><a href=\"https://github.com/cadnano/cadnano2.5/blob/master/AUTHORS\"><span style=\" text-decoration: underline; color:#0000ff;\">other contributors</span></a><span style=\" font-family:\'Lucida Grande\';\">. Funding generously provided by the </span><a href=\"https://wyss.harvard.edu/\"><span style=\" text-decoration: underline; color:#0000ff;\">Wyss Institute</span></a><span style=\" font-family:\'Lucida Grande\';\"> at Harvard University, </span><a href=\"https://www.bwfund.org/\"><span style=\" text-decoration: underline; color:#0000ff;\">Burroughs Wellcome Fund</span></a><span style=\" font-family:\'Lucida Grande\';\">, </span><a href=\"https://nsf.gov/\"><span style=\" text-decoration: underline; color:#0000ff;\">NSF</span></a><span style=\" font-family:\'Lucida Grande\';\">, and </span><a href=\"https://www.onr.navy.mil/\"><span style=\" text-decoration: underline; color:#0000ff;\">ONR</span></a><span style=\" font-family:\'Lucida Grande\';\">.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">The source code available under BSD 3-clause and GPLv3 </span><a href=\"https://github.com/cadnano/cadnano2.5/blob/master/LICENSE\"><span style=\" text-decoration: underline; color:#0000ff;\">licences</span></a><span style=\" font-family:\'Lucida Grande\';\">. </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Lucida Grande\';\">If you publish work using Cadnano, please cite Douglas </span><span style=\" font-family:\'Lucida Grande\'; font-style:italic;\">et al</span><span style=\" font-family:\'Lucida Grande\';\">. 2009 Nucleic Acids Res. 37:5001–6 (doi:</span><a href=\"https://dx.doi.org/10.1093%2Fnar%2Fgkp436\"><span style=\" text-decoration: underline; color:#0000ff;\">10.1093/nar/gkp436</span></a><span style=\" font-family:\'Lucida Grande\';\">).</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Lucida Grande\';\"><br /></p></body></html>"))

import cadnano.gui.dialogs.dialogicons_rc
