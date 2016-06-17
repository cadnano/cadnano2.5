import os
import sys

from cadnano import app, setReopen, setBatch
from cadnano.fileio.nnodecode import decodeFile
from cadnano.fileio.nnoencode import encodeToFile

from cadnano.gui.views.documentwindow import DocumentWindow
from cadnano.gui.ui.dialogs.ui_about import Ui_About

from cadnano.gui.views import styles
from cadnano import util

from PyQt5.QtCore import Qt, QFileInfo, QRect
from PyQt5.QtCore import QSettings, QSize, QDir

from PyQt5.QtGui import QPainter, QIcon, QKeySequence
from PyQt5.QtWidgets import (   QApplication, QDialog,
                                QDockWidget, QFileDialog, QActionGroup)
from PyQt5.QtWidgets import (   QGraphicsItem, QMainWindow,
                                QMessageBox, QStyleOptionGraphicsItem)
from PyQt5.QtSvg import QSvgGenerator

""" Allow only one part per document for now until part moving
is properly supported
"""
ONLY_ONE = True

class DocumentController():
    """
    Connects UI buttons to their corresponding actions in the model.
    """
    ### INIT METHODS ###
    def __init__(self, document):
        """docstring for __init__"""
        # initialize variables
        self._document = document
        self._document.setController(self)
        self._active_part = None
        self._filename = None
        self._file_open_path = None  # will be set in _readSettings
        self._has_no_associated_file = True
        self._path_view_instance = None
        self._slice_view_instance = None
        self._undo_stack = None
        self.win = None
        self.fileopendialog = None
        self.filesavedialog = None

        self.settings = QSettings()
        self._readSettings()

        # call other init methods
        self._initWindow()
        app().document_controllers.add(self)

    def _initWindow(self):
        """docstring for initWindow"""
        self.win = win = DocumentWindow(doc_ctrlr=self)
        app().documentWindowWasCreatedSignal.emit(self._document, win)
        self._connectWindowSignalsToSelf()
        win.show()
        app().active_document = self

        # Connect outliner with property editor
        o = win.outliner_widget
        p_e = win.property_widget
        o.itemSelectionChanged.connect(p_e.outlinerItemSelectionChanged)
        self.actionFilterVirtualHelixSlot()

        # setup tool exclusivity
        self.actiongroup = ag = QActionGroup(win)
        action_group_list = [   'action_global_select',
                                'action_global_pencil',
                                'action_path_nick',
                                'action_path_paint',
                                'action_path_insertion',
                                'action_path_skip',
                                'action_path_add_seq',
                                'action_path_mods']
        for action_name in action_group_list:
            ag.addAction(getattr(win, action_name))
    # end def

    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by DocumentController"""
        win = self.win
        win.action_new.triggered.connect(self.actionNewSlot)
        win.action_open.triggered.connect(self.actionOpenSlot)
        win.action_close.triggered.connect(self.actionCloseSlot)
        win.action_save.triggered.connect(self.actionSaveSlot)
        win.action_save_as.triggered.connect(self.actionSaveAsSlot)
        win.action_SVG.triggered.connect(self.actionSVGSlot)
        win.action_autostaple.triggered.connect(self.actionAutostapleSlot)
        win.action_export_staples.triggered.connect(self.actionExportSequencesSlot)
        win.action_preferences.triggered.connect(self.actionPrefsSlot)
        win.action_modify.triggered.connect(self.actionModifySlot)
        win.action_outliner.triggered.connect(self.actionToggleOutlinerSlot)

        win.action_new_dnapart.triggered.connect(self.actionAddDnaPart)

        win.closeEvent = self.windowCloseEventHandler
        win.action_about.triggered.connect(self.actionAboutSlot)
        win.action_cadnano_website.triggered.connect(self.actionCadnanoWebsiteSlot)
        win.action_feedback.triggered.connect(self.actionFeedbackSlot)

        # make it so select tool in slice view activation turns on vh filter
        win.action_filter_handle.triggered.connect(self.actionFilterVirtualHelixSlot)
        # self.trigger_vhelix_select = lambda x: win.action_vhelix_select.trigger()
        # win.action_filter_handle.triggered.connect(self.trigger_vhelix_select)
        # win.action_vhelix_select.triggered.connect(self.actionFilterVirtualHelixSlot)

        # win.action_vhelix_create.triggered.connect(self.actionFilterVirtualHelixSlot)
        # win.action_path_select.triggered.connect(self.actionFilterEndpointSlot)
        win.action_global_select.triggered.connect(self.actionSelectForkSlot)
        win.action_global_pencil.triggered.connect(self.actionCreateForkSlot)

        win.action_filter_endpoint.triggered.connect(self.actionFilterEndpointSlot)
        win.action_filter_strand.triggered.connect(self.actionFilterStrandSlot)
        win.action_filter_xover.triggered.connect(self.actionFilterXoverSlot)
        win.action_filter_fwd.triggered.connect(self.actionFilterFwdSlot)
        win.action_filter_rev.triggered.connect(self.actionFilterRevSlot)

        self.win.action_path_add_seq.triggered.connect(self.actionPathAddSeqSlot)
    # end def


    ### SLOTS ###
    def actionSelectForkSlot(self):
        win = self.win
        win.action_path_select.trigger()
        win.action_vhelix_select.trigger()
    # end def

    def actionCreateForkSlot(self):
        win = self.win
        win.action_vhelix_create.trigger()
        win.action_path_pencil.trigger()
    # end def

    def undoStackCleanChangedSlot(self):
        """The title changes to include [*] on modification."""
        self.win.setWindowModified(not self.undoStack().isClean())
        self.win.setWindowTitle(self.documentTitle())

    def actionAboutSlot(self):
        """Displays the about cadnano dialog."""
        dialog = QDialog()
        dialog_about = Ui_About()  # reusing this dialog, should rename
        dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
        dialog_about.setupUi(dialog)
        dialog.exec_()

    filter_list = ["strand", "endpoint", "xover", "virtual_helix"]
    def actionFilterVirtualHelixSlot(self):
        """Disables all other selection filters when active."""
        fH = self.win.action_filter_handle
        fE = self.win.action_filter_endpoint
        fS = self.win.action_filter_strand
        fX = self.win.action_filter_xover
        fH.setChecked(True)
        if fE.isChecked():
            fE.setChecked(False)
        if fS.isChecked():
            fS.setChecked(False)
        if fX.isChecked():
            fX.setChecked(False)
        types = ["virtual_helix"]
        self._document.setFilterSet(types)
    # end def

    def actionFilterEndpointSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.action_filter_handle
        fE = self.win.action_filter_endpoint
        fS = self.win.action_filter_strand
        fX = self.win.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fS.isChecked() and not fX.isChecked():
            fE.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterStrandSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.action_filter_handle
        fE = self.win.action_filter_endpoint
        fS = self.win.action_filter_strand
        fX = self.win.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fX.isChecked():
            fS.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterXoverSlot(self):
        """
        Disables handle filters when activated.
        Remains checked if no other item-type filter is active.
        """
        fH = self.win.action_filter_handle
        fE = self.win.action_filter_endpoint
        fS = self.win.action_filter_strand
        fX = self.win.action_filter_xover
        if fH.isChecked():
            fH.setChecked(False)
        if not fE.isChecked() and not fS.isChecked():
            fX.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def actionFilterFwdSlot(self):
        """Remains checked if no other strand-type filter is active."""
        f_fwd = self.win.action_filter_fwd
        f_rev = self.win.action_filter_rev
        if not f_fwd.isChecked() and not f_rev.isChecked():
            f_fwd.setChecked(True)
        self._strandFilterUpdate()

    def actionFilterRevSlot(self):
        """Remains checked if no other strand-type filter is active."""
        f_fwd = self.win.action_filter_fwd
        f_rev = self.win.action_filter_rev
        if not f_fwd.isChecked() and not f_rev.isChecked():
            f_rev.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def _strandFilterUpdate(self):
        win = self.win
        filter_list = []
        add_oligo = False
        if win.action_filter_endpoint.isChecked():
            filter_list.append("endpoint")
            add_oligo = True
        if win.action_filter_strand.isChecked():
            filter_list.append("strand")
            add_oligo = True
        if win.action_filter_xover.isChecked():
            filter_list.append("xover")
            add_oligo = True
        if win.action_filter_fwd.isChecked():
            filter_list.append("forward")
            add_oligo = True
        if win.action_filter_rev.isChecked():
            filter_list.append("reverse")
            add_oligo = True
        if add_oligo:
            filter_list.append("oligo")
        self._document.setFilterSet(filter_list)
    # end def

    def actionNewSlot(self):
        """
        1. If document is has no parts, do nothing.
        2. If document is dirty, call maybeSave and continue if it succeeds.
        3. Create a new document and swap it into the existing ctrlr/window.
        """
        # clear/reset the view!

        if len(self._document.children()) == 0:
            return  # no parts
        if self.maybeSave() == False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if self.filesavedialog is not None:
                self.filesavedialog.finished.connect(self.newClickedCallback)
            else:  # user did not save
                self.newClickedCallback()  # finalize new

    def actionOpenSlot(self):
        """
        1. If document is untouched, proceed to open dialog.
        2. If document is dirty, call maybesave and continue if it succeeds.
        Downstream, the file is selected in openAfterMaybeSave,
        and the selected file is actually opened in openAfterMaybeSaveCallback.
        """
        if self.maybeSave() == False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if hasattr(self, "filesavedialog"): # user did save
                if self.filesavedialog is not None:
                    self.filesavedialog.finished.connect(self.openAfterMaybeSave)
                else:
                    self.openAfterMaybeSave()  # windows
            else:  # user did not save
                self.openAfterMaybeSave()  # finalize new

    def actionCloseSlot(self):
        """This will trigger a Window closeEvent."""
        # if util.isWindows():
        self.win.close()
        app().qApp.exit(0)

    def actionSaveSlot(self):
        """SaveAs if necessary, otherwise overwrite existing file."""
        if self._has_no_associated_file:
            self.saveFileDialog()
            return
        self.writeDocumentToFile()

    def actionSaveAsSlot(self):
        """Open a save file dialog so user can choose a name."""
        self.saveFileDialog()

    def actionSVGSlot(self):
        """docstring for actionSVGSlot"""
        fname = os.path.basename(str(self.filename()))
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()

        fdialog = QFileDialog(
                    self.win,
                    "%s - Save As" % QApplication.applicationName(),
                    directory,
                    "%s (*.svg)" % QApplication.applicationName())
        fdialog.setAcceptMode(QFileDialog.AcceptSave)
        fdialog.setWindowFlags(Qt.Sheet)
        fdialog.setWindowModality(Qt.WindowModal)
        self.svgsavedialog = fdialog
        self.svgsavedialog.filesSelected.connect(self.saveSVGDialogCallback)
        fdialog.open()

    class DummyChild(QGraphicsItem):
        def boundingRect(self):
            return QRect(200, 200) # self.parentObject().boundingRect()
        def paint(self, painter, option, widget=None):
            pass

    def saveSVGDialogCallback(self, selected):
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        print("da fname", fname)
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".svg"):
            fname += ".svg"
        if self.svgsavedialog is not None:
            self.svgsavedialog.filesSelected.disconnect(self.saveSVGDialogCallback)
            del self.svgsavedialog  # prevents hang
            self.svgsavedialog = None

        generator = QSvgGenerator()
        generator.setFileName(fname)
        generator.setSize(QSize(200, 200))
        generator.setViewBox(QRect(0, 0, 2000, 2000))
        painter = QPainter()

        # Render through scene
        # painter.begin(generator)
        # self.win.pathscene.render(painter)
        # painter.end()

        # Render item-by-item
        painter = QPainter()
        style_option = QStyleOptionGraphicsItem()
        q = [self.win.pathroot]
        painter.begin(generator)
        while q:
            graphics_item = q.pop()
            transform = graphics_item.itemTransform(self.win.sliceroot)[0]
            painter.setTransform(transform)
            if graphics_item.isVisible():
                graphics_item.paint(painter, style_option, None)
                q.extend(graphics_item.childItems())
        painter.end()

    def actionExportSequencesSlot(self):
        """
        Triggered by clicking Export Staples button. Opens a file dialog to
        determine where the staples should be saved. The callback is
        exportStaplesCallback which collects the staple sequences and exports
        the file.
        """
        # Validate that no staple oligos are loops.
        part = self.activePart()
        if part is None:
            return
        stap_loop_olgs = part.getStapleLoopOligos()
        if stap_loop_olgs:
            from cadnano.gui.ui.dialogs.ui_warning import Ui_Warning
            dialog = QDialog()
            dialogWarning = Ui_Warning()  # reusing this dialog, should rename
            dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
            dialogWarning.setupUi(dialog)

            locs = ", ".join([o.locString() for o in stap_loop_olgs])
            msg = "Part contains staple loop(s) at %s.\n\nUse the break tool to introduce 5' & 3' ends before exporting. Loops have been colored red; use undo to revert." % locs
            dialogWarning.title.setText("Staple validation failed")
            dialogWarning.message.setText(msg)
            for o in stap_loop_olgs:
                o.applyColor(styles.stapColors[0])
            dialog.exec_()
            return

        # Proceed with staple export.
        fname = self.filename()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(
                            self.win,
                            "%s - Export As" % QApplication.applicationName(),
                            directory,
                            "(*.csv)")
            self.saveStaplesDialog = None
            self.exportStaplesCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                            self.win,
                            "%s - Export As" % QApplication.applicationName(),
                            directory,
                            "(*.csv)")
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.saveStaplesDialog = fdialog
            self.saveStaplesDialog.filesSelected.connect(self.exportStaplesCallback)
            fdialog.open()
    # end def

    def actionPathAddSeqSlot(self):
        print("triggered seqslot")
        self.activePart().setAbstractSequences()
    # end def

    def actionPrefsSlot(self):
        app().prefsClicked()
    # end def

    def actionAutostapleSlot(self):
        print("autoStapleSlot")
        part = self.activePart()
        if part:
            self.win.path_graphics_view.setViewportUpdateOn(False)
            part.autoStaple()
            self.win.path_graphics_view.setViewportUpdateOn(True)
    # end def

    def actionModifySlot(self):
        """
        Notifies that part root items that parts should respond to modifier
        selection signals.
        """
        pass
        # uncomment for debugging
        # isChecked = self.win.actionModify.isChecked()
        # self.win.pathroot.setModifyState(isChecked)
        # self.win.sliceroot.setModifyState(isChecked)


    def actionAddDnaPart(self):
        if ONLY_ONE:
            self.newDocument() # only allow one part for now
        part = self._document.addDnaPart()
        self.setActivePart(part)
        return part
    # end def

    def actionToggleOutlinerSlot(self):
        outliner = self.win.outliner_property_splitter
        if outliner.isVisible():
            outliner.hide()
        else:
            outliner.show()
    # end def

    def actionRenumberSlot(self):
        part = self.activePart()
        if part:
            coordList = self.win.pathroot.getSelectedInstanceOrderedVHList()
            part.renumber(coordList)
    # end def

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def window(self):
        return self.win
    # end def

    def setDocument(self, doc):
        """
        Sets the controller's document, and informs the document that
        this is its controller.
        """
        self._document = doc
        doc.setController(self)
    # end def

    def activePart(self):
        return self._active_part
    # end def

    def setActivePart(self, part):
        self._active_part = part
    # end def

    def undoStack(self):
        return self._document.undoStack()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def newDocument(self, doc=None, fname=None):
        """Creates a new Document, reusing the DocumentController.
        Tells all of the views to reset and removes all items from
        them
        """
        if fname is not None and self._filename == fname:
            setReopen(True)
        self._document.resetViews()
        setBatch(True)
        self._document.removeAllChildren()  # clear out old parts
        setBatch(False)
        self._document.undoStack().clear()  # reset undostack
        self._filename = fname if fname else "untitled.json"
        self._has_no_associated_file = fname is None
        self._active_part = None
        self.win.setWindowTitle(self.documentTitle() + '[*]')
    # end def

    def saveFileDialog(self):
        fname = self.filename()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(
                            self.win,
                            "%s - Save As" % QApplication.applicationName(),
                            directory,
                            "%s (*.json)" % QApplication.applicationName())
            if isinstance(fname, (list, tuple)):
                fname = fname[0]
            self.writeDocumentToFile(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                            self.win,
                            "%s - Save As" % QApplication.applicationName(),
                            directory,
                            "%s (*.json)" % QApplication.applicationName())
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.filesavedialog = fdialog
            self.filesavedialog.filesSelected.connect(
                                                self.saveFileDialogCallback)
            fdialog.open()
    # end def

    def _readSettings(self):
        self.settings.beginGroup("FileSystem")
        self._file_open_path = self.settings.value("openpath", QDir().homePath())
        self.settings.endGroup()

    def _writeFileOpenPath(self, path):
        """docstring for _writePath"""
        self._file_open_path = path
        self.settings.beginGroup("FileSystem")
        self.settings.setValue("openpath", path)
        self.settings.endGroup()

    ### SLOT CALLBACKS ###
    def actionNewSlotCallback(self):
        """
        Gets called on completion of filesavedialog after newClicked's
        maybeSave. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        """
        if self.filesavedialog is not None:
            self.filesavedialog.finished.disconnect(self.actionNewSlotCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def exportStaplesCallback(self, selected):
        """Export all staple sequences to selected CSV file."""
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".csv"):
            fname += ".csv"
        if self.saveStaplesDialog is not None:
            self.saveStaplesDialog.filesSelected.disconnect(self.exportStaplesCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.saveStaplesDialog
            self.saveStaplesDialog = None
        # write the file
        output = self.activePart().getStapleSequences()
        with open(fname, 'w') as f:
            f.write(output)
    # end def

    def newClickedCallback(self):
        """
        Gets called on completion of filesavedialog after newClicked's
        maybeSave. Removes the dialog if necessary, but it was probably
        already removed by saveFileDialogCallback.
        """

        if self.filesavedialog is not None:
            self.filesavedialog.finished.disconnect(self.newClickedCallback)
            del self.filesavedialog  # prevents hang (?)
            self.filesavedialog = None
        self.newDocument()

    def openAfterMaybeSaveCallback(self, selected):
        """
        Receives file selection info from the dialog created by
        openAfterMaybeSave, following user input.

        Extracts the file name and passes it to the decode method, which
        returns a new document doc, which is then set as the open document
        by newDocument. Calls finalizeImport and disconnects dialog signaling.
        """
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or fname == '' or os.path.isdir(fname):
            return False
        if not os.path.exists(fname):
            return False
        self._writeFileOpenPath(os.path.dirname(fname))

        self.win.path_graphics_view.setViewportUpdateOn(False)
        self.win.slice_graphics_view.setViewportUpdateOn(False)


        # NC commented out single document stuff
        if ONLY_ONE:
            self.newDocument(fname=fname)

        decodeFile(fname, document=self._document)

        self.win.path_graphics_view.setViewportUpdateOn(True)
        self.win.slice_graphics_view.setViewportUpdateOn(True)

        self.win.path_graphics_view.update()
        self.win.slice_graphics_view.update()

        if hasattr(self, "filesavedialog"): # user did save
            if self.fileopendialog is not None:
                self.fileopendialog.filesSelected.disconnect(\
                                              self.openAfterMaybeSaveCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.fileopendialog
            self.fileopendialog = None
        self.setFilename(fname)

    def saveFileDialogCallback(self, selected):
        """If the user chose to save, write to that file."""
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        if fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".json"):
            fname += ".json"
        if self.filesavedialog is not None:
            self.filesavedialog.filesSelected.disconnect(
                                                self.saveFileDialogCallback)
            del self.filesavedialog  # prevents hang
            self.filesavedialog = None
        self.writeDocumentToFile(fname)
        self._writeFileOpenPath(os.path.dirname(fname))

    ### EVENT HANDLERS ###
    def windowCloseEventHandler(self, event):
        """Intercept close events when user attempts to close the window."""
        if self.maybeSave():
            event.accept()
            dcs = app().document_controllers
            if self in dcs:
                dcs.remove(self)
        else:
            event.ignore()
        self.actionCloseSlot()

    ### FILE INPUT ##
    def documentTitle(self):
        fname = os.path.basename(str(self.filename()))
        if not self.undoStack().isClean():
            fname += '[*]'
        return fname

    def filename(self):
        return self._filename

    def setFilename(self, proposed_fname):
        if self._filename == proposed_fname:
            return True
        self._filename = proposed_fname
        self._has_no_associated_file = False
        self.win.setWindowTitle(self.documentTitle())
        return True

    def openAfterMaybeSave(self):
        """
        This is the method that initiates file opening. It is called by
        actionOpenSlot to spawn a QFileDialog and connect it to a callback
        method.
        """
        path = self._file_open_path
        if util.isWindows():  # required for native looking file window#"/",
            fname = QFileDialog.getOpenFileName(
                        None,
                        "Open Document", path,
                        "cadnano1 / cadnano2 Files (*.nno *.json *.c25)")
            self.filesavedialog = None
            self.openAfterMaybeSaveCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                        self.win,
                        "Open Document",
                        path,
                        "cadnano1 / cadnano2 Files (*.nno *.json *.c25)")
            fdialog.setAcceptMode(QFileDialog.AcceptOpen)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.fileopendialog = fdialog
            self.fileopendialog.filesSelected.connect(self.openAfterMaybeSaveCallback)
            fdialog.open()
    # end def

    ### FILE OUTPUT ###
    def maybeSave(self):
        """Save on quit, check if document changes have occured."""
        if app().dontAskAndJustDiscardUnsavedChanges:
            return True
        if not self.undoStack().isClean():    # document dirty?
            savebox = QMessageBox(QMessageBox.Warning,   "Application",
                "The document has been modified.\nDo you want to save your changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                self.win,
                Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.Sheet)
            savebox.setWindowModality(Qt.WindowModal)
            save = savebox.button(QMessageBox.Save)
            discard = savebox.button(QMessageBox.Discard)
            cancel = savebox.button(QMessageBox.Cancel)
            save.setShortcut("Ctrl+S")
            discard.setShortcut(QKeySequence("D,Ctrl+D"))
            cancel.setShortcut(QKeySequence("C,Ctrl+C,.,Ctrl+."))
            ret = savebox.exec_()
            del savebox  # manual garbage collection to prevent hang (in osx)
            if ret == QMessageBox.Save:
                return self.actionSaveAsSlot()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def writeDocumentToFile(self, filename=None):
        if filename is None or filename == '':
            if self._has_no_associated_file:
                return False
            filename = self.filename()
        try:
            encodeToFile(filename, self._document)
        except:
            flags = Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.Sheet
            errorbox = QMessageBox(QMessageBox.Critical,
                                   "cadnano",
                                   "Could not write to '%s'." % filename,
                                   QMessageBox.Ok,
                                   self.win,
                                   flags)
            errorbox.setWindowModality(Qt.WindowModal)
            errorbox.open()
            raise
            return False
        self.undoStack().setClean()
        self.setFilename(filename)
        return True

    def actionCadnanoWebsiteSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/")

    def actionFeedbackSlot(self):
        import webbrowser
        webbrowser.open("http://cadnano.org/feedback")

