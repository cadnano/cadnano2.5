from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from cadnano.views import styles
from cadnano.gui.dialogs.ui_preferences import Ui_Preferences
from cadnano.views.preferences_const import PreferencesConst


class Preferences(object):
    """Connect UI elements to the backend."""

    def __init__(self):
        self.qs = QSettings()
        self.ui_prefs = Ui_Preferences()
        self.widget = QWidget()
        self.ui_prefs.setupUi(self.widget)
        self.readPreferences()
        self.widget.addAction(self.ui_prefs.actionClose)
        self.ui_prefs.actionClose.triggered.connect(self.hideDialog)
        self.ui_prefs.grid_appearance_type_combo_box.currentIndexChanged.connect(self.setGridAppearanceType)
        self.ui_prefs.zoom_speed_slider.valueChanged.connect(self.setZoomSpeed)
        self.ui_prefs.button_box.clicked.connect(self.handleButtonClick)
        self.ui_prefs.show_icon_labels.clicked.connect(self.setShowIconLabels)
        self.ui_prefs.legacy_slice_view_combo_box.currentIndexChanged.connect(self.setSliceView)

        self.ui_prefs.grid_appearance_type_combo_box.activated.connect(self.updateGrid)
        self.document = None

    def showDialog(self):
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog

    def updateGrid(self, index):
        """Update the grid when the type of grid is changed.

        Calls setGridAppearanceType and updates each part of the document
        accordingly.
        """
        self.setGridAppearanceType(index)
        value = self.getGridAppearanceType()
        for part in self.document.getParts():
            part.partDocumentSettingChangedSignal.emit(part, 'grid', value)
    # end def

    def hideDialog(self):
        self.widget.hide()
    # end def

    def handleButtonClick(self, button):
        """Used only to restore defaults.

        Other buttons are ignored because connections are already set up in
        qt designer.
        """
        if self.ui_prefs.button_box.buttonRole(button) == QDialogButtonBox.ResetRole:
            self.restoreDefaults()
    # end def

    def readPreferences(self):
        """Read the preferences from self.qs (a QSettings object) and set the
        preferences accordingly in the UI popup.

        Returns: None
        """
        self.qs.beginGroup(PreferencesConst.PREFERENCES)
        self.grid_appearance_type_index = self.qs.value(PreferencesConst.GRID_APPEARANCE_TYPE_INDEX,
                                                        styles.PREF_GRID_APPEARANCE_TYPE_INDEX)
        self.slice_appearance_type_index = self.qs.value(PreferencesConst.SLICE_APPEARANCE_TYPE_INDEX,
                                                         styles.PREF_SLICE_VIEW_STYLE_INDEX)
        self.zoom_speed = self.qs.value("zoom_speed", styles.PREF_ZOOM_SPEED)
        self.show_icon_labels = self.qs.value("ui_icons_labels", styles.PREF_SHOW_ICON_LABELS)
        self.qs.endGroup()
        self.ui_prefs.grid_appearance_type_combo_box.setCurrentIndex(self.grid_appearance_type_index)
        self.ui_prefs.zoom_speed_slider.setProperty("value", self.zoom_speed)
        self.ui_prefs.show_icon_labels.setChecked(self.show_icon_labels)
    # end def

    def restoreDefaults(self):
        """Restore the default settings."""
        self.ui_prefs.grid_appearance_type_combo_box.setCurrentIndex(styles.PREF_GRID_APPEARANCE_TYPE_INDEX)
        self.ui_prefs.zoom_speed_slider.setProperty("value", styles.PREF_ZOOM_SPEED)
        self.ui_prefs.show_icon_labels.setChecked(styles.PREF_SHOW_ICON_LABELS)
        self.ui_prefs.legacy_slice_view_combo_box.setCurrentIndex(styles.PREF_SLICE_VIEW_STYLE_INDEX)
    # end def

    def setGridAppearanceType(self, grid_appearance_type_index):
        """Select the type of grid that should be displayed."""
        self.grid_appearance_type_index = grid_appearance_type_index
        self.qs.beginGroup(PreferencesConst.PREFERENCES)
        self.qs.setValue(PreferencesConst.GRID_APPEARANCE_TYPE_INDEX,
                         grid_appearance_type_index)
        self.qs.endGroup()
    # end def

    def setSliceView(self, slice_appearance_type_index):
        """Select whether the slice view, grid view, or both should be
        displayed.
        """
        self.slice_appearance_type_index = slice_appearance_type_index
        self.qs.beginGroup(PreferencesConst.PREFERENCES)
        self.qs.setValue(PreferencesConst.SLICE_APPEARANCE_TYPE_INDEX,
                         slice_appearance_type_index)
        self.qs.endGroup()

        value = self.getSliceView()

        if value == PreferencesConst.LEGACY:
            self.document.controller().toggleSliceView(True)
            self.document.controller().toggleGridView(False)
        elif value == PreferencesConst.GRID:
            self.document.controller().toggleSliceView(False)
            self.document.controller().toggleGridView(True)
        elif value == PreferencesConst.DUAL:
            self.document.controller().toggleSliceView(True)
            self.document.controller().toggleGridView(True)
        else:
            raise ValueError('Invalid slice view value: %s' % value)

    def getSliceView(self):
        """Map the index of the drop-down in the preferences UI to the slice
        view that should be shown.

        Returns: The string corresponding to the view that should be shown
        """
        return PreferencesConst.SLICE_VIEWS[self.slice_appearance_type_index]

    def getGridAppearanceType(self):
        return PreferencesConst.GRID_VIEWS[self.grid_appearance_type_index]
        # return ['circles', 'lines and points', 'points'][self.grid_appearance_type_index]
    # end def

    def setZoomSpeed(self, speed):
        self.zoom_speed = speed
        self.qs.beginGroup(PreferencesConst.PREFERENCES)
        self.qs.setValue("zoom_speed", self.zoom_speed)
        self.qs.endGroup()
    # end def

    def setShowIconLabels(self, checked):
        self.show_icon_labels = checked
        self.qs.beginGroup(PreferencesConst.PREFERENCES)
        self.qs.setValue("ui_icons_labels", self.show_icon_labels)
        self.qs.endGroup()
    # end def
