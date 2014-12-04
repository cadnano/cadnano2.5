from cadnano.gui.ui.dialogs.ui_preferences import Ui_Preferences
from cadnano.gui.views import styles
from cadnano.gui.views.sliceview import slicestyles
import cadnano.util as util

import os.path, zipfile, shutil, platform, subprocess, tempfile, errno

from PyQt5.QtCore import pyqtSlot, Qt, QObject, QSettings
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox

class Preferences(object):
    """docstring for Preferences"""
    def __init__(self):
        self.qs = QSettings()
        self.ui_prefs = Ui_Preferences()
        self.widget = QWidget()
        self.ui_prefs.setupUi(self.widget)
        self.readPreferences()
        self.widget.addAction(self.ui_prefs.actionClose)
        self.ui_prefs.actionClose.triggered.connect(self.hideDialog)
        self.ui_prefs.honeycomb_rows_spin_box.valueChanged.connect(self.setHoneycombRows)
        self.ui_prefs.honeycomb_cols_spin_box.valueChanged.connect(self.setHoneycombCols)
        self.ui_prefs.honeycomb_steps_spin_box.valueChanged.connect(self.setHoneycombSteps)
        self.ui_prefs.square_rows_spin_box.valueChanged.connect(self.setSquareRows)
        self.ui_prefs.square_cols_spin_box.valueChanged.connect(self.setSquareCols)
        self.ui_prefs.square_steps_spin_box.valueChanged.connect(self.setSquareSteps)
        self.ui_prefs.auto_scaf_combo_box.currentIndexChanged.connect(self.setAutoScaf)
        self.ui_prefs.default_tool_combo_box.currentIndexChanged.connect(self.setStartupTool)
        self.ui_prefs.zoom_speed_slider.valueChanged.connect(self.setZoomSpeed)
        # self.ui_prefs.helixAddCheckBox.toggled.connect(self.setZoomToFitOnHelixAddition)
        self.ui_prefs.button_box.clicked.connect(self.handleButtonClick)
        self.ui_prefs.add_plugin_button.clicked.connect(self.addPlugin)
        self.ui_prefs.show_icon_labels.clicked.connect(self.setShowIconLabels)

    def showDialog(self):
        # self.exec_()
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog

    def hideDialog(self):
        self.widget.hide()

    # @pyqtSlot(object)
    def handleButtonClick(self, button):
        """
        Restores defaults. Other buttons are ignored because connections
        are already set up in qt designer.
        """
        if self.ui_prefs.button_box.buttonRole(button) == QDialogButtonBox.ResetRole:
            self.restoreDefaults()

    def readPreferences(self):
        self.qs.beginGroup("Preferences")
        self.honeycomb_rows = self.qs.value("honeycomb_rows", slicestyles.HONEYCOMB_PART_MAXROWS)
        self.honeycomb_cols = self.qs.value("honeycomb_cols", slicestyles.HONEYCOMB_PART_MAXCOLS)
        self.honeycomb_steps = self.qs.value("honeycomb_steps", slicestyles.HONEYCOMB_PART_MAXSTEPS)
        self.square_rows = self.qs.value("square_rows", slicestyles.SQUARE_PART_MAXROWS)
        self.square_cols = self.qs.value("square_cols", slicestyles.SQUARE_PART_MAXCOLS)
        self.square_steps = self.qs.value("square_steps", slicestyles.SQUARE_PART_MAXSTEPS)
        self.auto_scaf_index = self.qs.value("autoScaf", styles.PREF_AUTOSCAF_INDEX)
        self.startup_tool_index = self.qs.value("startup_tool", styles.PREF_STARTUP_TOOL_INDEX)
        self.zoom_speed = self.qs.value("zoom_speed", styles.PREF_ZOOM_SPEED)
        self.zoom_on_helix_add = self.qs.value("zoom_on_helix_add", styles.PREF_ZOOM_AFTER_HELIX_ADD)
        self.show_icon_labels = self.qs.value("ui_icons_labels", styles.PREF_SHOW_ICON_LABELS)
        self.qs.endGroup()
        self.ui_prefs.honeycomb_rows_spin_box.setProperty("value", self.honeycomb_rows)
        self.ui_prefs.honeycomb_cols_spin_box.setProperty("value", self.honeycomb_cols)
        self.ui_prefs.honeycomb_steps_spin_box.setProperty("value", self.honeycomb_steps)
        self.ui_prefs.square_rows_spin_box.setProperty("value", self.square_rows)
        self.ui_prefs.square_cols_spin_box.setProperty("value", self.square_cols)
        self.ui_prefs.square_steps_spin_box.setProperty("value", self.square_steps)
        self.ui_prefs.auto_scaf_combo_box.setCurrentIndex(self.auto_scaf_index)
        self.ui_prefs.default_tool_combo_box.setCurrentIndex(self.startup_tool_index)
        self.ui_prefs.zoom_speed_slider.setProperty("value", self.zoom_speed)
        self.ui_prefs.show_icon_labels.setChecked(self.show_icon_labels)
        ptw = self.ui_prefs.plugin_table_widget
        loaded_plugin_paths = util.loadedPlugins.keys()
        ptw.setRowCount(len(loaded_plugin_paths))
        for i in range(len(loaded_plugin_paths)):
            row = QTableWidgetItem(loaded_plugin_paths[i])
            row.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ptw.setItem(i, 0, row)
        # self.ui_prefs.helixAddCheckBox.setChecked(self.zoom_on_helix_add)
    # end def

    def restoreDefaults(self):
        self.ui_prefs.honeycomb_rows_spin_box.setProperty("value", slicestyles.HONEYCOMB_PART_MAXROWS)
        self.ui_prefs.honeycomb_cols_spin_box.setProperty("value", slicestyles.HONEYCOMB_PART_MAXCOLS)
        self.ui_prefs.honeycomb_steps_spin_box.setProperty("value", slicestyles.HONEYCOMB_PART_MAXSTEPS)
        self.ui_prefs.square_rows_spin_box.setProperty("value", slicestyles.SQUARE_PART_MAXROWS)
        self.ui_prefs.square_cols_spin_box.setProperty("value", slicestyles.SQUARE_PART_MAXCOLS)
        self.ui_prefs.square_steps_spin_box.setProperty("value", slicestyles.SQUARE_PART_MAXSTEPS)
        self.ui_prefs.auto_scaf_combo_box.setCurrentIndex(styles.PREF_AUTOSCAF_INDEX)
        self.ui_prefs.default_tool_combo_box.setCurrentIndex(styles.PREF_STARTUP_TOOL_INDEX)
        self.ui_prefs.zoom_speed_slider.setProperty("value", styles.PREF_ZOOM_SPEED)
        self.ui_prefs.show_icon_labels.setChecked("value", self.PREF_SHOW_ICON_LABELS)
        # self.ui_prefs.helixAddCheckBox.setChecked(styles.PREF_ZOOM_AFTER_HELIX_ADD)
    # end def

    def setHoneycombRows(self, rows):
        self.honeycomb_rows = rows
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycomb_rows", self.honeycomb_rows)
        self.qs.endGroup()

    def setHoneycombCols(self, cols):
        self.honeycomb_cols = cols
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycomb_cols", self.honeycomb_cols)
        self.qs.endGroup()

    def setHoneycombSteps(self, steps):
        self.honeycomb_steps = steps
        self.qs.beginGroup("Preferences")
        self.qs.setValue("honeycomb_steps", self.honeycomb_steps)
        self.qs.endGroup()

    def setSquareRows(self, rows):
        self.square_rows = rows
        self.qs.beginGroup("Preferences")
        self.qs.setValue("square_rows", self.square_rows)
        self.qs.endGroup()

    def setSquareCols(self, cols):
        self.square_cols = cols
        self.qs.beginGroup("Preferences")
        self.qs.setValue("square_cols", self.square_cols)
        self.qs.endGroup()

    def setSquareSteps(self, steps):
        self.square_steps = steps
        self.qs.beginGroup("Preferences")
        self.qs.setValue("square_steps", self.square_steps)
        self.qs.endGroup()

    def setAutoScaf(self, index):
        self.auto_scaf_index = index
        self.qs.beginGroup("Preferences")
        self.qs.setValue("autoScaf", self.auto_scaf_index)
        self.qs.endGroup()

    def setStartupTool(self, index):
        self.startup_tool_index = index
        self.qs.beginGroup("Preferences")
        self.qs.setValue("startup_tool", self.startup_tool_index)
        self.qs.endGroup()

    def setZoomSpeed(self, speed):
        self.zoom_speed = speed
        self.qs.beginGroup("Preferences")
        self.qs.setValue("zoom_speed", self.zoom_speed)
        self.qs.endGroup()

    def setShowIconLabels(self, checked):
        self.show_icon_labels = checked
        self.qs.beginGroup("Preferences")
        self.qs.setValue("ui_icons_labels", self.show_icon_labels)
        self.qs.endGroup()

    # def setZoomToFitOnHelixAddition(self, checked):
    #     self.zoom_on_helix_add = checked
    #     self.qs.beginGroup("Preferences")
    #     self.qs.setValue("zoom_on_helix_add", self.zoom_on_helix_add)
    #     self.qs.endGroup()

    def getAutoScafType(self):
        return ['Mid-seam', 'Raster'][self.auto_scaf_index]

    def getStartupToolName(self):
        return ['Select', 'Pencil', 'Paint', 'AddSeq'][self.startup_tool_index]

    def addPlugin(self):
        fdialog = QFileDialog(
                    self.widget,
                    "Install Plugin",
                    util.this_path(),
                    "Cadnano Plugins (*.cnp)")
        fdialog.setAcceptMode(QFileDialog.AcceptOpen)
        fdialog.setWindowFlags(Qt.Sheet)
        fdialog.setWindowModality(Qt.WindowModal)
        fdialog.filesSelected.connect(self.addPluginAtPath)
        self.fileopendialog = fdialog
        fdialog.open()

    def addPluginAtPath(self, fname):
        self.fileopendialog.close()
        fname = str(fname[0])
        print("Attempting to open plugin %s" % fname)
        try:
            zf = zipfile.ZipFile(fname, 'r')
        except Exception as e:
            self.failWithMsg("Plugin file seems corrupt: %s."%e)
            return
        tdir = tempfile.mkdtemp()
        try:
            for f in zf.namelist():
                if f.endswith('/'):
                    os.makedirs(os.path.join(tdir,f))
            for f in zf.namelist():
                if not f.endswith('/'):
                    zf.extract(f, tdir)
        except Exception as e:
            self.failWithMsg("Extraction of plugin archive failed: %s."%e)
            return
        files_in_zip = [(f, os.path.join(tdir, f)) for f in os.listdir(tdir)]
        try:
            self.confirmDestructiveIfNecessary(files_in_zip)
            self.removePluginsToBeOverwritten(files_in_zip)
            self.movePluginsIntoPluginsFolder(files_in_zip)
        except OSError:
            print("Couldn't copy files into plugin directory, attempting\
                   again after boosting privileges.")
            if platform.system() == 'Darwin':
                self.darwinAuthedMvPluginsIntoPluginsFolder(files_in_zip)
            elif platform.system() == 'Linux':
                self.linuxAuthedMvPluginsIntoPluginsFolder(files_in_zip)
            else:
                print("Can't boost privelages on platform %s" % platform.system())
        loadedAPlugin = util.loadAllPlugins()
        if not loadedAPlugin:
            print("Unable to load anythng from plugin %s" % fname)
        self.readPreferences()
        shutil.rmtree(tdir)

    def darwinAuthedMvPluginsIntoPluginsFolder(self, files_in_zip):
        envirn={"DST":util.this_path()+'/plugins'}
        srcstr = ''
        for i in range(len(files_in_zip)):
            file_name, file_path = files_in_zip[i]
            srcstr += ' \\"$SRC' + str(i) + '\\"'
            envirn['SRC'+str(i)] = file_path
        proc = subprocess.Popen(['osascript','-e',\
                          'do shell script "cp -fR ' + srcstr +\
                          ' \\"$DST\\"" with administrator privileges'],\
                          env=envirn)
        retval = self.waitForProcExit(proc)
        if retval != 0:
            self.failWithMsg('cp failed with code %i'%retval)

    def linuxAuthedMvPluginsIntoPluginsFolder(self, files_in_zip):
        args = ['gksudo', 'cp', '-fR']
        args.extend(file_path for file_name, file_path in files_in_zip)
        args.append(util.this_path()+'/plugins')
        proc = subprocess.Popen(args)
        retval = self.waitForProcExit(proc)
        if retval != 0:
            self.failWithMsg('cp failed with code %i'%retval)

    def confirmDestructiveIfNecessary(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            if os.path.isfile(target):
                return self.confirmDestructive()
            elif os.path.isdir(target):
                return self.confirmDestructive()

    def confirmDestructive(self):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText("The plugin you are trying to install\
has already been installed. Replace the currently installed one?")
        mb.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        mb.exec_()
        return mb.clickedButton() == mb.button(QMessageBox.Yes)
        
    def removePluginsToBeOverwritten(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            if os.path.isfile(target):
                os.unlink(target)
            elif os.path.isdir(target):
                shutil.rmtree(target)

    def movePluginsIntoPluginsFolder(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            shutil.move(file_path, target)

    def waitForProcExit(self, proc):
        procexit = False
        while not procexit:
            try:
                retval = proc.wait()
                procexit = True
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise ose
        return retval

    def failWithMsg(self, str):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText(str)
        mb.buttonClicked.connect(self.closeFailDialog)
        self.fail_message_box = mb
        mb.open()

    def closeFailDialog(self, button):
        self.fail_message_box.close()
        del self.fail_message_box
        self.fail_message_box = None