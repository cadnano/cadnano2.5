
from PyQt5.QtCore import  QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QAction, QActionGroup
from PyQt5.QtWidgets import QToolBar, QSizePolicy


class PathToolBar(QToolBar):

    def __init__(self, parent=None):
        super(PathToolBar, self).__init__(parent)

        self._actionGroup = QActionGroup(self)
        self._actionGroup.setExclusive(True)

        self.setOrientation(Qt.Vertical)
        self._sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self._sizePolicy.setHorizontalStretch(0)
        self._sizePolicy.setVerticalStretch(0)
        self._sizePolicy.setHeightForWidth(self._sizePolicy.hasHeightForWidth())
        self.setSizePolicy(self._sizePolicy)
        self.setMinimumSize(QSize(0, 0))
        self.setMaximumWidth(46)
        self.setLayoutDirection(Qt.LeftToRight)
        # self.setAllowedAreas(QtCore.Qt.LeftToolBarArea|QtCore.Qt.RightToolBarArea|QtCore.Qt.TopToolBarArea)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setObjectName("pathtoolbar")

        self.action_path_select = self.setupAction("Select", "V", "action_path_select", ":/pathtools/select")
        self.action_path_pencil = self.setupAction("Pencil", "N", "action_path_pencil", ":/pathtools/force")
        self.action_path_break = self.setupAction("Break", "B", "action_path_break", ":/pathtools/break")
        self.action_path_insertion = self.setupAction("Insert", "I", "action_path_insertion", ":/pathtools/insert")
        self.action_path_skip = self.setupAction("Skip", "S", "action_path_skip", ":/pathtools/skip")
        self.action_path_paint = self.setupAction("Paint", "P", "action_path_paint", ":/pathtools/paint")
        self.action_path_add_seq = self.setupAction("AddSeq", "A", "action_path_add_seq", ":/pathtools/addseq")
        self.action_path_mod = self.setupAction("Mod", "M", "action_path_mod", ":/pathtools/mods")

    def setupAction(self, actionText, shortcut, actionName, actionPixmapLoc):
        """
        Creates new QAction object, sets appearance, adds to the toolbar and action group,
        and returns a reference to the object.
        """
        action = QAction(self)
        action.setCheckable(True)
        icon = QIcon()
        icon.addPixmap(QPixmap(actionPixmapLoc), QIcon.Normal, QIcon.Off)
        action.setIcon(icon)
        action.setObjectName(actionName)
        self.addAction(action)
        action.setText(QApplication.translate("MainWindow", actionText, None))
        action.setShortcut(QApplication.translate("MainWindow", shortcut))
        return action
