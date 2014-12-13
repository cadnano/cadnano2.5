from cadnano import app

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
        self.setOrientation(Qt.Vertical)  # default is horizontal
        # _maxH = 40 if app().prefs.show_icon_labels else 30
        # self.setMaximumHeight(_maxH) # horizontal
        self.setMaximumWidth(46) # vertical
        self.setIconSize(QSize(20, 20))
        self.setLayoutDirection(Qt.LeftToRight)

        if app().prefs.show_icon_labels:
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Tools
        self.action_path_select = self.setupAction("Select", "V", "action_path_select", ":/pathtools/select")
        self.action_path_pencil = self.setupAction("Pencil", "N", "action_path_pencil", ":/pathtools/force")
        self.action_path_break = self.setupAction("Nick", "K", "action_path_break", ":/pathtools/nick")
        self.action_path_insertion = self.setupAction("Insert", "I", "action_path_insertion", ":/pathtools/insert")
        self.action_path_skip = self.setupAction("Skip", "S", "action_path_skip", ":/pathtools/skip")
        self.action_path_paint = self.setupAction("Paint", "P", "action_path_paint", ":/pathtools/paint")
        self.action_path_mod = self.setupAction("Mod", "M", "action_path_mod", ":/pathtools/mod")
        self.action_path_add_seq = self.setupAction("Seq", "A", "action_path_add_seq", ":/pathtools/addseq")

        # Separator
        self.addSeparator()

        # Buttons
        self.action_autostaple = self.setupAction("Auto", None, "action_autostaple", ":/pathtools/autostaple")
        self.action_autostaple.triggered.connect(self.doc.controller().actionAutostapleSlot)
        self.action_renumber = self.setupAction("Rnum", None, "action_renumber", ":/parttools/renum")
        self.action_renumber.triggered.connect(self.doc.controller().actionRenumberSlot)
        self.action_svg = self.setupAction("SVG", None, "action_svg", ":/filetools/svg")
        self.action_svg.triggered.connect(self.doc.controller().actionSVGSlot)
        self.action_export = self.setupAction("Export", None, "action_export_staples", ":/filetools/export")
        self.action_export.triggered.connect(self.doc.controller().actionExportSequencesSlot)

    # end def


    def setupAction(self, actionText, shortcut, actionName, rc_path):
        """
        Creates new QAction object, sets appearance, adds to the toolbar and action group,
        and returns a reference to the object.
        """
        action = QAction(self)
        if actionText != None and app().prefs.show_icon_labels:
            action.setText(QApplication.translate("MainWindow", actionText, None))
        if shortcut:
            action.setShortcut(QApplication.translate("MainWindow", shortcut))
            action.setCheckable(True)
        if actionName != None:
            action.setObjectName(actionName)
        if rc_path != None:
            icon = QIcon()
            icon.addPixmap(QPixmap(rc_path).scaled(20,20), QIcon.Normal, QIcon.Off)
            action.setIcon(icon)
            action.setFont(_FONT)
        self.addAction(action)
        return action
    # end def

