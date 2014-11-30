
from . import pathstyles as styles

from PyQt5.QtCore import  QSize, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup
from PyQt5.QtWidgets import QToolBar, QSizePolicy

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
        # self.setOrientation(Qt.Vertical)  # default is horizontal
        self.setMaximumHeight(40) # horizontal
        # self.setMaximumWidth(46) # vertical
        self.setIconSize(QSize(20, 20))
        self.setLayoutDirection(Qt.LeftToRight)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.action_new_honeycomb_part = self.setupAction("Hcomb", None, 
                                                          "action_new_honeycomb_part", 
                                                          ":/parttools/new-honeycomb")
        self.action_new_honeycomb_part.triggered.connect(self.doc.controller().actionAddHoneycombPartSlot)
        self.action_new_square_part = self.setupAction("Square", None, 
                                                       "action_new_square_part", 
                                                       ":/parttools/new-square")
        self.action_new_square_part.triggered.connect(self.doc.controller().actionAddSquarePartSlot)
        self.action_new_hpx_part = self.setupAction("H-PX", None, 
                                                        "action_new_honeypx_part", 
                                                        ":/parttools/new-hpx")
        self.action_new_hpx_part.triggered.connect(self.doc.controller().actionAddHpxPartSlot)
        self.action_new_spx_part = self.setupAction("Sq-PX", None, 
                                                        "action_new_squarepx_part", 
                                                        ":/parttools/new-spx")
        self.action_new_spx_part.triggered.connect(self.doc.controller().actionAddSpxPartSlot)
    # end def

    def setupAction(self, actionText, shortcut, actionName, rc_path):
        """
        Creates new QAction object, sets appearance, adds to the toolbar and action group,
        and returns a reference to the object.
        """
        action = QAction(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(rc_path), QIcon.Normal, QIcon.Off)
        action.setIcon(icon)
        action.setObjectName(actionName)
        self.addAction(action)
        action.setText(QApplication.translate("MainWindow", actionText, None))
        if shortcut:
            action.setShortcut(QApplication.translate("MainWindow", shortcut))
            action.setCheckable(True)
        action.setFont(_FONT)
        return action
    # end def

