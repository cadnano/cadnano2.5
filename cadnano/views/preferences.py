from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from cadnano.gui.dialogs.ui_preferences import Ui_Preferences
from cadnano.proxies.cnenum import OrthoViewEnum, EnumType


PREFS_GROUP_NAME = 'Preferences'

ORTHOVIEW_KEY = 'EnabledOrthoView'
ORTHOVIEW_DEFAULT = OrthoViewEnum.GRID
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
        ui_prefs = self.ui_prefs
        ui_prefs.actionClose.triggered.connect(self.hideDialog)
        ui_prefs.button_box.clicked.connect(self.handleButtonClick)
        ui_prefs.enabled_orthoview_combo_box.currentIndexChanged.connect(self.orthoviewChangedSlot)
        ui_prefs.gridview_style_combo_box.currentIndexChanged.connect(self.gridviewStyleChangedSlot)
        ui_prefs.show_icon_labels.clicked.connect(self.setShowIconLabels)
        ui_prefs.zoom_speed_slider.valueChanged.connect(self.setZoomSpeed)
    # end def

    def readPreferences(self):
        """Read the preferences from self.qs (a QSettings object) and set the
        preferences accordingly in the UI popup.
        """
        qs = self.qs
        qs.beginGroup(PREFS_GROUP_NAME)
        self.gridview_style_idx = qs.value(GRIDVIEW_STYLE_KEY,
                                            GRIDVIEW_STYLE_DEFAULT)
        self.orthoview_style_idx = qs.value(ORTHOVIEW_KEY,
                                            ORTHOVIEW_DEFAULT)
        self.zoom_speed = qs.value(ZOOM_SPEED_KEY,
                                    ZOOM_SPEED_DEFAULT)
        self.show_icon_labels = qs.value(SHOW_ICON_LABELS_KEY,
                                        SHOW_ICON_LABELS_DEFAULT)
        qs.endGroup()
        ui_prefs = self.ui_prefs
        ui_prefs.gridview_style_combo_box.setCurrentIndex(self.gridview_style_idx)
        ui_prefs.enabled_orthoview_combo_box.setCurrentIndex(self.orthoview_style_idx)
        ui_prefs.show_icon_labels.setChecked(self.show_icon_labels)
        ui_prefs.zoom_speed_slider.setProperty("value", self.zoom_speed)
    # end def

    ### SLOTS ###
    def hideDialog(self):
        self.widget.hide()
    # end def

    def showDialog(self):
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog
    # end def

    def gridviewStyleChangedSlot(self, index):
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
        gridview_style_idx = GRIDVIEW_STYLE_DEFAULT
        orthoview_idx = ORTHOVIEW_DEFAULT
        ui_prefs = self.ui_prefs
        ui_prefs.gridview_style_combo_box.setCurrentIndex(gridview_style_idx)
        ui_prefs.enabled_orthoview_combo_box.setCurrentIndex(orthoview_idx)
        ui_prefs.zoom_speed_slider.setProperty("value", ZOOM_SPEED_DEFAULT)
        ui_prefs.show_icon_labels.setChecked(SHOW_ICON_LABELS_DEFAULT)
    # end def

    def setGridviewStyleIdx(self, value):
        """Select the type of grid that should be displayed."""
        self.gridview_style_idx = value
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(GRIDVIEW_STYLE_KEY, value)
        self.qs.endGroup()
    # end def

    def orthoviewChangedSlot(self, view_idx: EnumType):
        """Handles index changes to enabled_orthoview_combo_box.
        Saves the setting and notifies the doc controller to toggle
        visibilty of appropriate 2D orthographic view (sliceview or gridview).
        """
        assert isinstance(view_idx, EnumType)
        new_orthoview_style_idx = view_idx
        assert new_orthoview_style_idx in (OrthoViewEnum.GRID, OrthoViewEnum.SLICE)

        self.orthoview_style_idx = new_orthoview_style_idx
        self.qs.beginGroup(PREFS_GROUP_NAME)
        self.qs.setValue(ORTHOVIEW_KEY, new_orthoview_style_idx)
        self.qs.endGroup()

        controller = self.document().controller()
        self.controller.setSliceOrGridViewVisible(self.orthoview_style_idx)
    # end def

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
