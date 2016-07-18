import os.path, zipfile, shutil, platform, subprocess, tempfile, errno

from PyQt5.QtCore import Qt, QObject, QSettings, pyqtSignal
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox

from cadnano import util
from cadnano.gui.views import styles
from cadnano.gui.views.sliceview import slicestyles
from cadnano.gui.ui.dialogs.ui_preferences import Ui_Preferences


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
        self.ui_prefs.grid_appearance_type_combo_box.currentIndexChanged.connect(self.setGridAppearanceType)
        self.ui_prefs.zoom_speed_slider.valueChanged.connect(self.setZoomSpeed)
        self.ui_prefs.button_box.clicked.connect(self.handleButtonClick)
        self.ui_prefs.add_plugin_button.clicked.connect(self.addPlugin)
        self.ui_prefs.show_icon_labels.clicked.connect(self.setShowIconLabels)

        self.ui_prefs.grid_appearance_type_combo_box.activated.connect(self.updateGrid)
        self.document = None
    # end def

    def showDialog(self):
        self.readPreferences()
        self.widget.show()  # launch prefs in mode-less dialog
    # end def

    def updateGrid(self, index):
        self.setGridAppearanceType(index)
        value = self.getGridAppearanceType()
        for part in self.document.getParts():
            part.partDocumentSettingChangedSignal.emit(part, 'grid', value)
    # end def

    def hideDialog(self):
        self.widget.hide()
    # end def

    def handleButtonClick(self, button):
        """
        Restores defaults. Other buttons are ignored because connections
        are already set up in qt designer.
        """
        if self.ui_prefs.button_box.buttonRole(button) == QDialogButtonBox.ResetRole:
            self.restoreDefaults()
    # end def

    def readPreferences(self):
        self.qs.beginGroup("Preferences")
        self.grid_appearance_type_index = self.qs.value("grid_appearance_type_index", styles.PREF_GRID_APPEARANCE_TYPE_INDEX)
        self.zoom_speed = self.qs.value("zoom_speed", styles.PREF_ZOOM_SPEED)
        self.show_icon_labels = self.qs.value("ui_icons_labels", styles.PREF_SHOW_ICON_LABELS)
        self.qs.endGroup()
        self.ui_prefs.grid_appearance_type_combo_box.setCurrentIndex(self.grid_appearance_type_index)
        self.ui_prefs.zoom_speed_slider.setProperty("value", self.zoom_speed)
        self.ui_prefs.show_icon_labels.setChecked(self.show_icon_labels)
        ptw = self.ui_prefs.plugin_table_widget
        loaded_plugin_paths = util.loadedPlugins.keys()
        ptw.setRowCount(len(loaded_plugin_paths))
        for i in range(len(loaded_plugin_paths)):
            row = QTableWidgetItem(loaded_plugin_paths[i])
            row.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ptw.setItem(i, 0, row)
    # end def

    def restoreDefaults(self):
        self.ui_prefs.grid_appearance_type_combo_box.setCurrentIndex(styles.PREF_GRID_APPEARANCE_TYPE_INDEX)
        self.ui_prefs.zoom_speed_slider.setProperty("value", styles.PREF_ZOOM_SPEED)
        self.ui_prefs.show_icon_labels.setChecked(styles.PREF_SHOW_ICON_LABELS)
    # end def

    def setGridAppearanceType(self, grid_appearance_type_index):
        self.grid_appearance_type_index = grid_appearance_type_index
        self.qs.beginGroup("Preferences")
        self.qs.setValue("grid_appearance_type_index", grid_appearance_type_index)
        self.qs.endGroup()
    # end def

    def getGridAppearanceType(self):
        return ['circles', 'lines and points', 'points'][self.grid_appearance_type_index]
    # end def

    def setZoomSpeed(self, speed):
        self.zoom_speed = speed
        self.qs.beginGroup("Preferences")
        self.qs.setValue("zoom_speed", self.zoom_speed)
        self.qs.endGroup()
    # end def

    def setShowIconLabels(self, checked):
        self.show_icon_labels = checked
        self.qs.beginGroup("Preferences")
        self.qs.setValue("ui_icons_labels", self.show_icon_labels)
        self.qs.endGroup()
    # end def

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
    # end def

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
    # end def

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
    # end def

    def linuxAuthedMvPluginsIntoPluginsFolder(self, files_in_zip):
        args = ['gksudo', 'cp', '-fR']
        args.extend(file_path for file_name, file_path in files_in_zip)
        args.append(util.this_path()+'/plugins')
        proc = subprocess.Popen(args)
        retval = self.waitForProcExit(proc)
        if retval != 0:
            self.failWithMsg('cp failed with code %i'%retval)
    # end def

    def confirmDestructiveIfNecessary(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            if os.path.isfile(target):
                return self.confirmDestructive()
            elif os.path.isdir(target):
                return self.confirmDestructive()
    # end def

    def confirmDestructive(self):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText("The plugin you are trying to install\
has already been installed. Replace the currently installed one?")
        mb.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        mb.exec_()
        return mb.clickedButton() == mb.button(QMessageBox.Yes)
    # end def

    def removePluginsToBeOverwritten(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            if os.path.isfile(target):
                os.unlink(target)
            elif os.path.isdir(target):
                shutil.rmtree(target)
    # end def

    def movePluginsIntoPluginsFolder(self, files_in_zip):
        for file_name, file_path in files_in_zip:
            target = os.path.join(util.this_path(), 'plugins', file_name)
            shutil.move(file_path, target)
    # end def

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
    # end def

    def failWithMsg(self, str):
        mb = QMessageBox(self.widget)
        mb.setIcon(QMessageBox.Warning)
        mb.setInformativeText(str)
        mb.buttonClicked.connect(self.closeFailDialog)
        self.fail_message_box = mb
        mb.open()
    # end def

    def closeFailDialog(self, button):
        self.fail_message_box.close()
        del self.fail_message_box
        self.fail_message_box = None
    # end def
