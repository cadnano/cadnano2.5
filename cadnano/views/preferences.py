from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QDialogButtonBox
from cadnano.gui.dialogs.ui_preferences import Ui_Preferences

PREFS_GROUP_NAME = 'Preferences'
SLICEVIEWS = ('legacy', 'grid', 'dual')
SLICEVIEW_KEY = 'EnabledSliceview'
SLICEVIEW_DEFAULT = 0  # legacy idx
GRIDVIEW_STYLES = ('points', 'points and lines')
GRIDVIEW_STYLE_KEY = 'GridviewStyle'
GRIDVIEW_STYLE_DEFAULT = 0  # points idx
ZOOM_SPEED_KEY = 'ZoomSpeed'
ZOOM_SPEED_DEFAULT = 20
SHOW_ICON_LABELS_KEY = 'ShowIconLabels'
SHOW_ICON_LABELS_DEFAULT = True


class Preferences(object):
    """Connect UI elements to the backend."""

    def __init__(self):
        self.qs = QSettings("cadnano.org", "cadnano2.5")
        self.ui_prefs = Ui_Preferences()
        self.widget = QWidget()
        self.ui_prefs.setupUi(self.widget)
        self.readPreferences()
        self.widget.addAction(self.ui_prefs.actionClose)
        self.connectSignals()
        self.document = None
    # end def

    ### SUPPORT METHODS ###
    def connectSignals(self):
        self.ui_prefs.actionClose.triggered.connect(self.hideDialog)
        self.ui_prefs.button_box.clicked.connect(self.handleButtonClick)
        self.ui_prefs.enabled_sliceview_combo_box.currentIndexChanged.connect(self.updateEnabledSliceview)
        self.ui_prefs.gridview_style_combo_box.currentIndexChanged.connect(self.updateGridviewStyle)
        # self.ui_prefs.gridview_style_combo_box.activated.connect(self.updateGridviewStyle)
        self.ui_prefs.show_icon_labels.clicked.connect(self.setShowIconLabels)
        self.ui_prefs.zoom_speed_slider.valueChanged.connect(self.setZoomSpeed)
    # end def

    def readPreferences(self):
        """Read the preferences from self.qs (a QSettings object) and set the
        preferences accordingly in the UI popup.

        Returns: None
        """
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.gridview_style_idx = self.qs.value(GRIDVIEW_STYLE_KEY, GRIDVIEW_STYLE_DEFAULT)
        self.sliceview_idx = self.qs.value(SLICEVIEW_KEY, SLICEVIEW_DEFAULT)
        self.zoom_speed = self.qs.value(ZOOM_SPEED_KEY, ZOOM_SPEED_DEFAULT)
        self.show_icon_labels = self.qs.value(SHOW_ICON_LABELS_KEY, SHOW_ICON_LABELS_DEFAULT)
        self.qs.endGroup()
        self.ui_prefs.gridview_style_combo_box.setCurrentIndex(self.gridview_style_idx)
        self.ui_prefs.enabled_sliceview_combo_box.setCurrentIndex(self.sliceview_idx)
        self.ui_prefs.show_icon_labels.setChecked(self.show_icon_labels)
        self.ui_prefs.zoom_speed_slider.setProperty("value", self.zoom_speed)
    # end def

    ### SLOTS ###
    def hideDialog(self):
        self.widget.hide()
    # end def

    def showDialog(self):
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog
    # end def

    def updateGridviewStyle(self, index):
        """Update the grid when the type of grid is changed.

        Calls setGridviewStyleIdx and updates each part of the document
        accordingly.
        """
        gridview_style = GRIDVIEW_STYLES[self.gridview_style_idx]
        for part in self.document.getParts():
            part.partDocumentSettingChangedSignal.emit(part, 'grid', gridview_style)
    # end def

    def handleButtonClick(self, button):
        """Used only to restore defaults.

        Other buttons are ignored because connections are already set up in
        qt designer.
        """
        if self.ui_prefs.button_box.buttonRole(button) == QDialogButtonBox.ResetRole:
            self.restoreDefaults()
    # end def

    def restoreDefaults(self):
        """Restore the default settings."""
        gridview_style_idx = GRIDVIEW_STYLES.index(GRIDVIEW_STYLE_DEFAULT)
        sliceview_idx = GRIDVIEW_STYLES.index(SLICEVIEW_DEFAULT)
        self.ui_prefs.gridview_style_combo_box.setCurrentIndex(gridview_style_idx)
        self.ui_prefs.enabled_sliceview_combo_box.setCurrentIndex(sliceview_idx)
        self.ui_prefs.zoom_speed_slider.setProperty("value", ZOOM_SPEED_DEFAULT)
        self.ui_prefs.show_icon_labels.setChecked(SHOW_ICON_LABELS_DEFAULT)
    # end def

    def setGridviewStyleIdx(self, value):
        """Select the type of grid that should be displayed."""
        self.gridview_style_idx = value
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(GRIDVIEW_STYLE_KEY, value)
        self.qs.endGroup()
    # end def

    def updateEnabledSliceview(self, value):
        """Select whether the slice view, grid view, or both should be
        displayed.
        """
        self.sliceview_idx = value
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(SLICEVIEW_KEY, value)
        self.qs.endGroup()

        value = SLICEVIEWS[self.sliceview_idx]
        if value == 'legacy':
            self.document.controller().toggleSliceView(True)
            self.document.controller().toggleGridView(False)
        elif value == 'grid':
            self.document.controller().toggleSliceView(False)
            self.document.controller().toggleGridView(True)
        elif value == 'dual':
            self.document.controller().toggleSliceView(True)
            self.document.controller().toggleGridView(True)
        else:
            raise ValueError('Invalid slice view value: %s' % value)

    def setShowIconLabels(self, value):
        self.show_icon_labels = value
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(SHOW_ICON_LABELS_KEY, value)
        self.qs.endGroup()
    # end def

    def setZoomSpeed(self, value):
        self.zoom_speed = value
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(ZOOM_SPEED_KEY, value)
        self.qs.endGroup()
    # end def
