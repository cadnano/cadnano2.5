from cadnano import app

from . import pathstyles as styles

from PyQt5.QtCore import  QSize, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup
from PyQt5.QtWidgets import QToolBar, QToolButton, QSizePolicy

_FONT = QFont(styles.THE_FONT, 8, QFont.Normal)

class PartToolBar(QToolBar):

    def __init__(self, doc, parent=None):
        super(PartToolBar, self).__init__(parent)
        self.doc = doc

        # Set the appearance
        _sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        _sizePolicy.setHorizontalStretch(0)
        _sizePolicy.setVerticalStretch(0)
        _sizePolicy.setHeightForWidth(_sizePolicy.hasHeightForWidth())
        self.setSizePolicy(_sizePolicy)
        self.setOrientation(Qt.Vertical)  # default is horizontal
        # _maxH = 40 if app().prefs.show_icon_labels else 30
        # self.setMaximumHeight(_maxH) # horizontal
        self.setMaximumWidth(36) # vertical
        self.setIconSize(QSize(20, 20))
        self.setLayoutDirection(Qt.LeftToRight)

        if app().prefs.show_icon_labels:
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Toolbar Label
        self.action_outliner = self.setupAction("Outline", None,
                                                        "action_outliner",
                                                        ":/parttools/outliner")
        self.action_outliner.triggered.connect(self.doc.controller().actionToggleOutlinerSlot)


        # Toolbar Label
        self.action_toolbar_label = self.setupLabel("Add\nPart:", "action_new_honeycomb_part")

        # DNA part
        self.action_new_plasmidpart = self.setupAction("Plasmid", None,
                                                        "action_new_plasmidpart",
                                                        ":/parttools/new-dna")
        self.action_new_plasmidpart.triggered.connect(self.doc.controller().actionAddPlasmidPartSlot)


        # Origami ToolButton
        self.add_origamipart_button = self.setupToolButton("Origami\n", None,
                                                           "add_origamipart_button",
                                                           ":/parttools/new-honeycomb")

        # Origami Part (Honeycomb)
        self.action_new_honeycomb_part = self.setupAction("Hcomb", None,
                                                          "action_new_honeycomb_part",
                                                          ":/parttools/new-honeycomb",
                                                          self.add_origamipart_button)
        self.action_new_honeycomb_part.triggered.connect(self.doc.controller().actionAddHoneycombPartSlot)
        # Origami Part (Square)
        self.action_new_square_part = self.setupAction("Square", None,
                                                       "action_new_square_part",
                                                       ":/parttools/new-square",
                                                       self.add_origamipart_button)
        self.action_new_square_part.triggered.connect(self.doc.controller().actionAddSquarePartSlot)
        # Origami Part (H-PX)
        self.action_new_hpx_part = self.setupAction("H-PX", None,
                                                        "action_new_honeypx_part",
                                                        ":/parttools/new-hpx",
                                                        self.add_origamipart_button)
        self.action_new_hpx_part.triggered.connect(self.doc.controller().addHoneycombDnaPart)
        # Origami Part (S-px)
        self.action_new_spx_part = self.setupAction("Sq-PX", None,
                                                        "action_new_squarepx_part",
                                                        ":/parttools/new-spx",
                                                        self.add_origamipart_button)
        self.action_new_spx_part.triggered.connect(self.doc.controller().actionAddSqNucleicAcidPart)

    # end def

    def setupToolButton(self, actionText, shortcut, actionName, rc_path):
        toolbutton = QToolButton(self)
        toolbutton.setPopupMode(QToolButton.InstantPopup)
        if app().prefs.show_icon_labels:
            toolbutton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolbutton.setFont(_FONT)
            toolbutton.setText(QApplication.translate("MainWindow", actionText, None))
        icon = QIcon()
        icon.addPixmap(QPixmap(rc_path), QIcon.Normal, QIcon.Off)
        toolbutton.setIcon(icon)
        self.addWidget(toolbutton)
        return toolbutton
    # end def

    def setupLabel(self, actionText, actionName):
        action = QAction(self)
        if actionText != None:
            action.setText(QApplication.translate("MainWindow", actionText, None))
        if actionName != None:
            action.setObjectName(actionName)
        self.addAction(action)
        return action
    # end def

    def setupAction(self, actionText, shortcut, actionName, rc_path, toolbutton=None):
        """
        Creates new QAction object, sets appearance, adds to the toolbar and action group,
        and returns a reference to the object.
        """
        action = QAction(self)

        if actionText != None and app().prefs.show_icon_labels or toolbutton:
            action.setText(QApplication.translate("MainWindow", actionText, None))
        if rc_path is not None:
            icon = QIcon()
            icon.addPixmap(QPixmap(rc_path), QIcon.Normal, QIcon.Off)
            action.setIcon(icon)
            action.setFont(_FONT)
        if actionName is not None:
            action.setObjectName(actionName)
        if shortcut:
            action.setShortcut(QApplication.translate("MainWindow", shortcut))
            action.setCheckable(True)
        if toolbutton is None:
            self.addAction(action)
        else:
            toolbutton.addAction(action)
        return action
    # end def

