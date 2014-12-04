import os
import sys

from cadnano import app, setReopen, setBatch
from cadnano.fileio.nnodecode import decode, decodeFile
from cadnano.fileio.encoder import encode

from cadnano.gui.views.documentwindow import DocumentWindow
from cadnano.gui.ui.dialogs.ui_about import Ui_About

from cadnano.gui.views import styles
import cadnano.util as util

from PyQt5.QtCore import Qt, QFileInfo, QRect
from PyQt5.QtCore import QSettings, QSize, QDir

from PyQt5.QtGui import QPainter, QIcon, QKeySequence
from PyQt5.QtWidgets import QApplication, QDialog, QDockWidget, QFileDialog
from PyQt5.QtWidgets import QGraphicsItem, QMainWindow, QMessageBox, QStyleOptionGraphicsItem
from PyQt5.QtSvg import QSvgGenerator

class DocumentController():
    """
    Connects UI buttons to their corresponding actions in the model.
    """
    ### INIT METHODS ###
    def __init__(self, document):
        """docstring for __init__"""
        # initialize variables
        self._document = document
        print("the doc", self._document)
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
        self.win = DocumentWindow(doc_ctrlr=self)
        # self.win.setWindowIcon(app().icon)
        app().documentWindowWasCreatedSignal.emit(self._document, self.win)
        self._connectWindowSignalsToSelf()
        self.win.show()
        app().active_document = self

    def _initMaya(self):
        """
        Initialize Maya-related state. Delete Maya nodes if there
        is an old document left over from the same session. Set up
        the Maya window.
        """
        # There will only be one document
        if (app().active_document and app().active_document.win and
                                not app().active_document.win.close()):
            return
        del app().active_document
        app().active_document = self

        import maya.OpenMayaUI as OpenMayaUI
        import sip
        ptr = OpenMayaUI.MQtUtil.mainWindow()
        mayaWin = sip.wrapinstance(int(ptr), QMainWindow)
        self.windock = QDockWidget("cadnano")
        self.windock.setFeatures(QDockWidget.DockWidgetMovable
                                 | QDockWidget.DockWidgetFloatable)
        self.windock.setAllowedAreas(Qt.LeftDockWidgetArea
                                     | Qt.RightDockWidgetArea)
        self.windock.setWidget(self.win)
        mayaWin.addDockWidget(Qt.DockWidgetArea(Qt.LeftDockWidgetArea),
                                self.windock)
        self.windock.setVisible(True)

    def _connectWindowSignalsToSelf(self):
        """This method serves to group all the signal & slot connections
        made by DocumentController"""
        self.win.action_new.triggered.connect(self.actionNewSlot)
        self.win.action_open.triggered.connect(self.actionOpenSlot)
        self.win.action_close.triggered.connect(self.actionCloseSlot)
        self.win.action_save.triggered.connect(self.actionSaveSlot)
        self.win.action_save_as.triggered.connect(self.actionSaveAsSlot)
        # self.win.action_SVG.triggered.connect(self.actionSVGSlot)
        # self.win.action_autostaple.triggered.connect(self.actionAutostapleSlot)
        # self.win.action_export_staples.triggered.connect(self.actionExportSequencesSlot)
        self.win.action_preferences.triggered.connect(self.actionPrefsSlot)
        self.win.action_modify.triggered.connect(self.actionModifySlot)
        self.win.action_new_honeycomb_part.triggered.connect(\
            self.actionAddHoneycombPartSlot)
        self.win.action_new_square_part.triggered.connect(\
            self.actionAddSquarePartSlot)
        self.win.closeEvent = self.windowCloseEventHandler
        self.win.action_about.triggered.connect(self.actionAboutSlot)
        self.win.action_cadnano_website.triggered.connect(self.actionCadnanoWebsiteSlot)
        self.win.action_feedback.triggered.connect(self.actionFeedbackSlot)
        self.win.action_filter_handle.triggered.connect(self.actionFilterHandleSlot)
        self.win.action_filter_endpoint.triggered.connect(self.actionFilterEndpointSlot)
        self.win.action_filter_strand.triggered.connect(self.actionFilterStrandSlot)
        self.win.action_filter_xover.triggered.connect(self.actionFilterXoverSlot)
        self.win.action_filter_scaf.triggered.connect(self.actionFilterScafSlot)
        self.win.action_filter_stap.triggered.connect(self.actionFilterStapSlot)


    ### SLOTS ###
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
    def actionFilterHandleSlot(self):
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
        self._document.documentSelectionFilterChangedSignal.emit(["virtual_helix"])

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

    def actionFilterScafSlot(self):
        """Remains checked if no other strand-type filter is active."""
        fSc = self.win.action_filter_scaf
        fSt = self.win.action_filter_stap
        if not fSc.isChecked() and not fSt.isChecked():
            fSc.setChecked(True)
        self._strandFilterUpdate()

    def actionFilterStapSlot(self):
        """Remains checked if no other strand-type filter is active."""
        fSc = self.win.action_filter_scaf
        fSt = self.win.action_filter_stap
        if not fSc.isChecked() and not fSt.isChecked():
            fSt.setChecked(True)
        self._strandFilterUpdate()
    # end def

    def _strandFilterUpdate(self):
        win = self.win
        filter_list = []
        if win.action_filter_endpoint.isChecked():
            filter_list.append("endpoint")
        if win.action_filter_strand.isChecked():
            filter_list.append("strand")
        if win.action_filter_xover.isChecked():
            filter_list.append("xover")
        if win.action_filter_scaf.isChecked():
            filter_list.append("scaffold")
        if win.action_filter_stap.isChecked():
            filter_list.append("staple")
        self._document.documentSelectionFilterChangedSignal.emit(filter_list)
    # end def

    def actionNewSlot(self):
        """
        1. If document is has no parts, do nothing.
        2. If document is dirty, call maybeSave and continue if it succeeds.
        3. Create a new document and swap it into the existing ctrlr/window.
        """
        # clear/reset the view!
        
        if len(self._document.parts()) == 0:
            return  # no parts
        if self.maybeSave() == False:
            return  # user canceled in maybe save
        else:  # user did not cancel
            if self.filesavedialog != None:
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
                if self.filesavedialog != None:
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
        if fname == None:
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
        if self.svgsavedialog != None:
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
            from ui.dialogs.ui_warning import Ui_Warning
            dialog = QDialog()
            dialogWarning = Ui_Warning()  # reusing this dialog, should rename
            dialog.setStyleSheet("QDialog { background-image: url(ui/dialogs/images/cadnano2-about.png); background-repeat: none; }")
            dialogWarning.setupUi(dialog)

            locs = ", ".join([o.locString() for o in stap_loop_olgs])
            msg = "Part contains staple loop(s) at %s.\n\nUse the break tool to introduce 5' & 3' ends before exporting. Loops have been colored red; use undo to revert." % locs
            dialogWarning.title.setText("Staple validation failed")
            dialogWarning.message.setText(msg)
            for o in stap_loop_olgs:
                o.applyColor(styles.stapColors[0].name())
            dialog.exec_()
            return

        # Proceed with staple export.
        fname = self.filename()
        if fname == None:
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

    def actionPrefsSlot(self):
        app().prefsClicked()
    # end def

    def actionAutostapleSlot(self):
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
        # if app().isInMaya():
        #     isChecked = self.win.actionModify.isChecked()
        #     self.win.pathroot.setModifyState(isChecked)
        #     self.win.sliceroot.setModifyState(isChecked)
        #     self.win.solidroot.setModifyState(isChecked)

    def actionAddHoneycombPartSlot(self):
        part = self._document.addHoneycombPart()
        self.setActivePart(part)
    # end def

    def actionAddSquarePartSlot(self):
        part = self._document.addSquarePart()
        self.setActivePart(part)
    # end def

    def actionAddHpxPartSlot(self):
        # part = self._document.addHpxPart()
        # self.setActivePart(part)
        pass
    # end def

    def actionAddSpxPartSlot(self):
        # part = self._document.addHpxPart()
        # self.setActivePart(part)
        pass
    # end def


    def actionRenumberSlot(self):
        part = self.activePart()
        if part:
            coordList = self.win.pathroot.getSelectedPartOrderedVHList()
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
        if self._active_part == None:
            self._active_part = self._document.selectedPart()
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
        """Creates a new Document, reusing the DocumentController."""
        if fname is not None and self._filename == fname:
            setReopen(True)
        self._document.resetViews()
        setBatch(True)
        self._document.removeAllParts()  # clear out old parts
        setBatch(False)
        self._document.undoStack().clear()  # reset undostack
        self._filename = fname if fname else "untitled.json"
        self._has_no_associated_file = fname == None
        self._active_part = None
        self.win.setWindowTitle(self.documentTitle() + '[*]')
    # end def

    def saveFileDialog(self):
        fname = self.filename()
        if fname == None:
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
        if self.filesavedialog != None:
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
        if self.saveStaplesDialog != None:
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

        if self.filesavedialog != None:
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

        self.newDocument(fname=fname)
        decodeFile(fname, document=self._document)

        self.win.path_graphics_view.setViewportUpdateOn(True)
        self.win.slice_graphics_view.setViewportUpdateOn(True)

        self.win.path_graphics_view.update()
        self.win.slice_graphics_view.update()

        if hasattr(self, "filesavedialog"): # user did save
            if self.fileopendialog != None:
                self.fileopendialog.filesSelected.disconnect(\
                                              self.openAfterMaybeSaveCallback)
            # manual garbage collection to prevent hang (in osx)
            del self.fileopendialog
            self.fileopendialog = None

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
        if self.filesavedialog != None:
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
            # if app().isInMaya():
            #     self.windock.setVisible(False)
            #     del self.windock
            #     self.windock = action_new_honeycomb_part
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
                        "cadnano1 / cadnano2 Files (*.nno *.json *.cadnano)")
            self.filesavedialog = None
            self.openAfterMaybeSaveCallback(fname)
        else:  # access through non-blocking callback
            fdialog = QFileDialog(
                        self.win,
                        "Open Document",
                        path,
                        "cadnano1 / cadnano2 Files (*.nno *.json *.cadnano)")
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
        if filename == None or filename == '':
            if self._has_no_associated_file:
                return False
            filename = self.filename()
        try:
            with open(filename, 'w') as f:
                helix_order_list = self.win.pathroot.getSelectedPartOrderedVHList()
                encode(self._document, helix_order_list, f)
        except IOError:
            flags = Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint | Qt.Sheet
            errorbox = QMessageBox(QMessageBox.Critical,
                                   "cadnano",
                                   "Could not write to '%s'." % filename,
                                   QMessageBox.Ok,
                                   self.win,
                                   flags)
            errorbox.setWindowModality(Qt.WindowModal)
            errorbox.open()
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

