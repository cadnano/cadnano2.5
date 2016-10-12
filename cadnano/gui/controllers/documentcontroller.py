# -*- coding: utf-8 -*-
import os
import sys
import traceback

from PyQt5.QtCore import Qt, QFileInfo, QRect
from PyQt5.QtCore import QSettings, QSize, QDir
from PyQt5.QtGui import QPainter, QKeySequence
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.QtWidgets import QFileDialog, QActionGroup
from PyQt5.QtWidgets import QGraphicsItem, QMessageBox
from PyQt5.QtWidgets import QStyleOptionGraphicsItem
from PyQt5.QtSvg import QSvgGenerator
from cadnano.gui.views.documentwindow import DocumentWindow
from cadnano.gui.ui.dialogs.ui_about import Ui_About
from cadnano.gui.views import styles
from cadnano import app, setReopen, setBatch, util


ONLY_ONE = True
"""bool: Retricts Document to creating only one Part if True."""


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
        self._file_open_path = None  # will be set in _readSettings
        self._has_no_associated_file = True

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
        # print("new window", app().qApp.allWindows())
        self.win = win = DocumentWindow(doc_ctrlr=self)
        app().documentWindowWasCreatedSignal.emit(self._document, win)
        self._connectWindowSignalsToSelf()
        win.show()
        app().active_document = self

        # Connect outliner with property editor
        o = win.outliner_widget
        p_e = win.property_widget
        o.itemSelectionChanged.connect(p_e.outlinerItemSelectionChanged)
        # self.actionFilterVirtualHelixSlot()
        self.actionFilterEndpointSlot()
        self.actionFilterXoverSlot()

        # setup tool exclusivity
        self.actiongroup = ag = QActionGroup(win)
        action_group_list = ['action_global_select',
                             'action_global_pencil',
                             'action_path_nick',
                             'action_path_paint',
                             'action_path_insertion',
                             'action_path_skip',
                             'action_path_add_seq',
                             'action_path_mods']
        for action_name in action_group_list:
            ag.addAction(getattr(win, action_name))

        win.action_global_select.trigger()
    # end def

    def destroyDC(self):
        self.disconnectSignalsToSelf()
        if self.win is not None:
            self.win.destroyWin()
            self.win = None
    # end def

    def disconnectSignalsToSelf(self):
        win = self.win
        if win is not None:
            o = win.outliner_widget
            p_e = win.property_widget
            o.itemSelectionChanged.disconnect(p_e.outlinerItemSelectionChanged)
        for signal_obj, slot_method in self.self_signals:
            # print("dSS", slot_method.__name__)
            signal_obj.disconnect(slot_method)
        self.self_signals = []
    # end def

    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by DocumentController"""
        win = self.win
        win.closeEvent = self.windowCloseEventHandler
        self.self_signals = [
            (win.action_new.triggered, self.actionNewSlot),
            (win.action_open.triggered, self.actionOpenSlot),
            (win.action_close.triggered, self.actionCloseSlot),
            (win.action_save.triggered, self.actionSaveSlot),
            (win.action_save_as.triggered, self.actionSaveAsSlot),
            (win.action_SVG.triggered, self.actionSVGSlot),
            (win.action_export_staples.triggered, self.actionExportSequencesSlot),
            (win.action_preferences.triggered, self.actionPrefsSlot),
            (win.action_outliner.triggered, self.actionToggleOutlinerSlot),
            (win.action_new_dnapart.triggered, self.actionCreateNucleicAcidPart),
            (win.action_new_dnapart.triggered, lambda: win.action_global_pencil.trigger()),
            (win.action_about.triggered, self.actionAboutSlot),
            (win.action_cadnano_website.triggered, self.actionCadnanoWebsiteSlot),
            (win.action_feedback.triggered, self.actionFeedbackSlot),

            # make it so select tool in slice view activation turns on vh filter
            (win.action_filter_handle.triggered, self.actionFilterVirtualHelixSlot),
            (win.action_global_select.triggered, self.actionSelectForkSlot),
            (win.action_global_pencil.triggered, self.actionCreateForkSlot),

            (win.action_filter_endpoint.triggered, self.actionFilterEndpointSlot),
            (win.action_filter_strand.triggered, self.actionFilterStrandSlot),
            (win.action_filter_xover.triggered, self.actionFilterXoverSlot),
            (win.action_filter_fwd.triggered, self.actionFilterFwdSlot),
            (win.action_filter_rev.triggered, self.actionFilterRevSlot),

            (win.action_path_add_seq.triggered, self.actionPathAddSeqSlot),

            (win.action_vhelix_snap.triggered, self.actionVhelixSnapSlot)
        ]
        for signal_obj, slot_method in self.self_signals:
            signal_obj.connect(slot_method)
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

    def actionVhelixSnapSlot(self, state):
        for item in self.win.sliceroot.instance_items.values():
            item.griditem.allow_snap = state
    # end def

    def undoStackCleanChangedSlot(self):
        """The title changes to include [*] on modification.
        Use this when clearing out undostack to set the modified status of
        the document
        """
        self.win.setWindowModified(not self.undoStack().isClean())
        self.win.setWindowTitle(self.documentTitle())
    # end def

    def actionAboutSlot(self):
        """Displays the about cadnano dialog."""
        dialog = QDialog()
        dialog_about = Ui_About()  # reusing this dialog, should rename
        dialog.setStyleSheet(
            "QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
        dialog_about.setupUi(dialog)
        dialog.exec_()

    filter_list = ["strand", "endpoint", "xover", "virtual_helix"]
    """list: String names of enabled filter types."""

    def actionFilterVirtualHelixSlot(self):
        """Disables all other selection filters when active."""
        fH = self.win.action_filter_handle
        fE = self.win.action_filter_endpoint
        # fS = self.win.action_filter_strand
        fX = self.win.action_filter_xover
        fH.setChecked(True)
        if fE.isChecked():
            fE.setChecked(False)
        # if fS.isChecked():
        #     fS.setChecked(False)
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
            fS.setChecked(True)
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
            # filter_list.append("strand")
            add_oligo = True
        # if win.action_filter_strand.isChecked():
        #     filter_list.append("strand")
        #     add_oligo = True
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
        if self.maybeSave() is False:
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
        3. Downstream, the file is selected in openAfterMaybeSave, and the selected
           file is actually opened in openAfterMaybeSaveCallback.
        """
        if self.maybeSave() is False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if hasattr(self, "filesavedialog"):  # user did save
                if self.filesavedialog is not None:
                    self.filesavedialog.finished.connect(self.openAfterMaybeSave)
                else:
                    self.openAfterMaybeSave()  # windows
            else:  # user did not save
                self.openAfterMaybeSave()  # finalize new

    def actionCloseSlot(self):
        """Called when DocumentWindow is closed"""
        # if util.isWindows():
        # traceback.print_stack()
        the_app = app()
        self.destroyDC()
        if the_app.document_controllers:    # check we haven't done this already
            # print("App Closing")
            the_app.destroyApp()
            # print("App closed")
    #end def

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
        fname = os.path.basename(str(self.fileName()))
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()

        fdialog = QFileDialog(self.win,
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
            return QRect(200, 200)  # self.parentObject().boundingRect()

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
        part = self._document.activePart()
        if part is None:
            return
        loop_olgs = part.getLoopOligos()
        if loop_olgs:
            from cadnano.gui.ui.dialogs.ui_warning import Ui_Warning
            dialog = QDialog()
            dialogWarning = Ui_Warning()  # reusing this dialog, should rename
            dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
            dialogWarning.setupUi(dialog)

            locs = ", ".join([o.locString() for o in loop_olgs])
            msg = "Part contains staple loop(s) at %s.\n\nUse the break tool to introduce 5' & 3' ends before exporting. Loops have been colored red; use undo to revert." % locs
            dialogWarning.title.setText("Staple validation failed")
            dialogWarning.message.setText(msg)
            for o in loop_olgs:
                o.applyColor(styles.stapColors[0])
            dialog.exec_()
            return

        # Proceed with staple export.
        fname = self.fileName()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(self.win,
                                                "%s - Export As" % QApplication.applicationName(),
                                                directory,
                                                "(*.txt)")
            self.saveStaplesDialog = None
            self.exportStaplesCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self.win,
                                  "%s - Export As" % QApplication.applicationName(),
                                  directory,
                                  "(*.txt)")
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.saveStaplesDialog = fdialog
            self.saveStaplesDialog.filesSelected.connect(self.exportStaplesCallback)
            fdialog.open()
    # end def

    def actionPathAddSeqSlot(self):
        print("triggered seqslot")
        ap = self._document.activePart()
        if ap is not None:
            self._document.activePart().setAbstractSequences(emit_signals=True)
    # end def

    def actionPrefsSlot(self):
        app().prefsClicked()
    # end def

    def actionModifySlot(self):
        """
        Notifies that part root items that parts should respond to modifier
        selection signals.
        """
        pass

    def actionCreateNucleicAcidPart(self):
        if ONLY_ONE:
            self.newDocument()  # only allow one part for now
        doc = self._document
        part = doc.createNucleicAcidPart()
        active_part = doc.activePart()
        if active_part is not None:
            active_part.setActive(False)
            doc.deactivateActivePart()
        part.setActive(True)
        doc.setActivePart(part)
        return part
    # end def

    def actionToggleOutlinerSlot(self):
        outliner = self.win.outliner_property_splitter
        if outliner.isVisible():
            outliner.hide()
        else:
            outliner.show()
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

    def undoStack(self):
        return self._document.undoStack()
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def newDocument(self, fname=None):
        """Creates a new Document, reusing the DocumentController.
        Tells all of the views to reset and removes all items from
        them
        """
        if fname is not None and self.fileName() == fname:
            setReopen(True)
        self._document.makeNew()
        self._has_no_associated_file = fname is None
        self.win.setWindowTitle(self.documentTitle() + '[*]')
    # end def

    def saveFileDialog(self):
        fname = self.fileName()
        if fname is None:
            directory = "."
        else:
            directory = QFileInfo(fname).path()
        if util.isWindows():  # required for native looking file window
            fname = QFileDialog.getSaveFileName(self.win,
                                                "%s - Save As" % QApplication.applicationName(),
                                                directory,
                                                "%s (*.json)" % QApplication.applicationName())
            if isinstance(fname, (list, tuple)):
                fname = fname[0]
            self.writeDocumentToFile(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self.win,
                                  "%s - Save As" % QApplication.applicationName(),
                                  directory,
                                  "%s (*.json)" % QApplication.applicationName())
            fdialog.setAcceptMode(QFileDialog.AcceptSave)
            fdialog.setWindowFlags(Qt.Sheet)
            fdialog.setWindowModality(Qt.WindowModal)
            self.filesavedialog = fdialog
            self.filesavedialog.filesSelected.connect(self.saveFileDialogCallback)
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
        """Export all staple sequences to selected CSV file.

        Args:
            selected (Tuple, List or str): if a List or Tuple, the filename should
            be the first element
        """
        if isinstance(selected, (list, tuple)):
            fname = selected[0]
        else:
            fname = selected
        # Return if fname is '', None, or a directory path
        if not fname or fname is None or os.path.isdir(fname):
            return False
        if not fname.lower().endswith(".txt"):
            fname += ".txt"
        if self.saveStaplesDialog is not None:
            self.saveStaplesDialog.filesSelected.disconnect(self.exportStaplesCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.saveStaplesDialog
            self.saveStaplesDialog = None
        # write the file
        ap = self._document.activePart()
        if ap is not None:
            output = ap.getSequences()
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

        self._document.readFile(fname)

        self.win.path_graphics_view.setViewportUpdateOn(True)
        self.win.slice_graphics_view.setViewportUpdateOn(True)

        self.win.path_graphics_view.update()
        self.win.slice_graphics_view.update()

        if hasattr(self, "filesavedialog"):  # user did save
            if self.fileopendialog is not None:
                self.fileopendialog.filesSelected.disconnect(self.openAfterMaybeSaveCallback)
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
            self.filesavedialog.filesSelected.disconnect(self.saveFileDialogCallback)
            del self.filesavedialog  # prevents hang
            self.filesavedialog = None
        self.writeDocumentToFile(fname)
        self._writeFileOpenPath(os.path.dirname(fname))

    ### EVENT HANDLERS ###
    def windowCloseEventHandler(self, event):
        """Intercept close events when user attempts to close the window."""
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()
        self.actionCloseSlot()
        # if self.win is not None:
        #     QMainWindow.closeEvent(self.win, event)
    # end def

    ### FILE INPUT ##
    def documentTitle(self):
        fname = os.path.basename(str(self.fileName()))
        if not self.undoStack().isClean():
            fname += '[*]'
        return fname

    def fileName(self):
        return self._document.fileName()

    def setFileName(self, proposed_fname):
        if self.fileName() == proposed_fname:
            return True
        self._document.setFileName(proposed_fname)
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
            fname = QFileDialog.getOpenFileName(None,
                                                "Open Document", path,
                                                "cadnano1 / cadnano2 Files (*.nno *.json *.c25)")
            self.filesavedialog = None
            self.openAfterMaybeSaveCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(self.win,
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
            savebox = QMessageBox(QMessageBox.Warning, "Application",
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
            filename = self.fileName()
        try:
            self._document.writeToFile(filename)
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
