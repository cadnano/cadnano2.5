# -*- coding: utf-8 -*-
import os
from abc import abstractmethod

from cadnano import app, setReopen, util
from cadnano.gui.ui.dialogs.ui_about import Ui_About
from cadnano.gui.views import styles
from cadnano.gui.views.documentwindow import DocumentWindow
from PyQt5.QtCore import QDir, QFileInfo, Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QGraphicsItem

DEFAULT_VHELIX_FILTER = True
ONLY_ONE = True
"""bool: Retricts Document to creating only one Part if True."""

class DocumentControllerBase(object):
    """
    Base class to connect UI buttons to their corresponding actions in the
    model.
    """
    @abstractmethod
    def __init__(self, document):
        pass

    @abstractmethod
    def _initWindow(self):
        raise NotImplementedError

    def destroyDC(self):
        self.disconnectSignalsToSelf()
        if self.win is not None:
            self.win.destroyWin()
            self.win = None

    @abstractmethod
    def disconnectSignalsToSelf(self):
        raise NotImplementedError

    @abstractmethod
    def _connectWindowSignalsToSelf(self):
        raise NotImplementedError

    ### SLOTS ###
    @abstractmethod
    def actionSelectForkSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionCreateForkSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionVhelixSnapSlot(self, state):
        raise NotImplementedError

    @abstractmethod
    def undoStackCleanChangedSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionAboutSlot(self):
        raise NotImplementedError

    filter_list = ["strand", "endpoint", "xover", "virtual_helix"]
    """list: String names of enabled filter types."""

    @abstractmethod
    def actionFilterVirtualHelixSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFilterEndpointSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFilterStrandSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFilterXoverSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFilterFwdSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFilterRevSlot(self):
        raise NotImplementedError

    @abstractmethod
    def _strandFilterUpdate(self):
        raise NotImplementedError

    @abstractmethod
    def actionNewSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionCloseSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionOpenSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionSaveSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionSaveAsSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionSVGSlot(self):
        raise NotImplementedError

    class DummyChild(QGraphicsItem):
        def boundingRect(self):
            return QRect(200, 200)  # self.parentObject().boundingRect()

        def paint(self, painter, option, widget=None):
            pass

    @abstractmethod
    def saveSVGDialogCallback(self, selected):
        raise NotImplementedError

    @abstractmethod
    def actionExportSequencesSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionPathAddSeqSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionPrefsSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionModifySlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionCreateNucleicAcidPart(self):
        raise NotImplementedError

    @abstractmethod
    def actionToggleOutlinerSlot(self):
        raise NotImplementedError

    ### ACCESSORS ###
    @abstractmethod
    def document(self):
        raise NotImplementedError

    @abstractmethod
    def window(self):
        raise NotImplementedError

    @abstractmethod
    def setDocument(self, doc):
        raise NotImplementedError

    @abstractmethod
    def undoStack(self):
        raise NotImplementedError

    ### PRIVATE SUPPORT METHODS ###
    @abstractmethod
    def newDocument(self, fname=None):
        raise NotImplementedError

    @abstractmethod
    def saveFileDialog(self):
        raise NotImplementedError

    @abstractmethod
    def _readSettings(self):
        raise NotImplementedError

    @abstractmethod
    def _writeFileOpenPath(self, path):
        raise NotImplementedError

    ### SLOT CALLBACKS ###
    @abstractmethod
    def actionNewSlotCallback(self):
        raise NotImplementedError

    @abstractmethod
    def exportStaplesCallback(self, selected):
        raise NotImplementedError

    @abstractmethod
    def newClickedCallback(self):
        raise NotImplementedError

    @abstractmethod
    def openAfterMaybeSaveCallback(self, selected):
        raise NotImplementedError

    @abstractmethod
    def saveFileDialogCallback(self, selected):
        raise NotImplementedError

    @abstractmethod
    def windowCloseEventHandler(self, event):
        raise NotImplementedError

    ### FILE INPUT ##
    @abstractmethod
    def documentTitle(self):
        raise NotImplementedError

    @abstractmethod
    def fileName(self):
        raise NotImplementedError

    @abstractmethod
    def setFileName(self, proposed_fname):
        raise NotImplementedError

    @abstractmethod
    def openAfterMaybeSave(self):
        raise NotImplementedError

    ### FILE OUTPUT ###
    @abstractmethod
    def maybeSave(self):
        raise NotImplementedError

    @abstractmethod
    def writeDocumentToFile(self, filename=None):
        raise NotImplementedError

    @abstractmethod
    def actionCadnanoWebsiteSlot(self):
        raise NotImplementedError

    @abstractmethod
    def actionFeedbackSlot(self):
        raise NotImplementedError
