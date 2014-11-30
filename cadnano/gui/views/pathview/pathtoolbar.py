
from . import pathstyles as styles

from PyQt5.QtCore import  QSize, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup
from PyQt5.QtWidgets import QToolBar, QSizePolicy

_FONT = QFont(styles.THE_FONT, 8, QFont.Normal)

class PathToolBar(QToolBar):

    def __init__(self, doc, parent=None):
        super(PathToolBar, self).__init__(parent)
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

        self.action_path_select = self.setupAction("Select", "V", "action_path_select", ":/pathtools/select")
        self.action_path_pencil = self.setupAction("Pencil", "N", "action_path_pencil", ":/pathtools/force")
        self.action_path_break = self.setupAction("Break", "B", "action_path_break", ":/pathtools/break")
        self.action_path_insertion = self.setupAction("Insert", "I", "action_path_insertion", ":/pathtools/insert")
        self.action_path_skip = self.setupAction("Skip", "S", "action_path_skip", ":/pathtools/skip")
        self.action_path_paint = self.setupAction("Paint", "P", "action_path_paint", ":/pathtools/paint")
        self.action_path_add_seq = self.setupAction("AddSeq", "A", "action_path_add_seq", ":/pathtools/addseq")
        self.action_path_mod = self.setupAction("Mod", "M", "action_path_mod", ":/pathtools/mods")
        self.action_renumber = self.setupAction("Rnum", None, "action_renumber", ":/slicetools/renumber")
        self.action_renumber.triggered.connect(self.doc.controller().actionRenumberSlot)

    def setupAction(self, actionText, shortcut, actionName, rc_path):
        """
        Creates new QAction object, sets appearance, adds to the toolbar and action group,
        and returns a reference to the object.
        """
        action = QAction(self)
        icon = QIcon()
        icon.addPixmap(QPixmap(rc_path).scaled(20,20), QIcon.Normal, QIcon.Off)
        action.setIcon(icon)
        action.setObjectName(actionName)
        self.addAction(action)
        action.setText(QApplication.translate("MainWindow", actionText, None))
        if shortcut:
            action.setShortcut(QApplication.translate("MainWindow", shortcut))
            action.setCheckable(True)
        action.setFont(_FONT)
        return action
