# -*- coding: utf-8 -*-
# Copyright (c) 2016 Wyss Institute at Harvard University
#
# This file may be used under the terms of the GNU General Public License
# version 3.0 as published by the Free Software Foundation and appearing in
# the file LICENSE included in the packaging of this file.  Please review the
# following information to ensure the GNU General Public License version 3.0
# requirements will be met: http://www.gnu.org/copyleft/gpl.html.
#
# If you do not wish to use this file under the terms of the GPL version 3.0
# then you may purchase a commercial license.  For more information contact
# info@riverbankcomputing.com.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

import os
import platform
import sys

from PyQt5.QtCore import (
    QCoreApplication,
    QEventLoop,
    QObject,
    QSize,
    pyqtSignal
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    qApp
)

from cadnano import util
from cadnano.proxies.proxyconfigure import proxyConfigure
from cadnano.cntypes import (
    DocT
)

proxyConfigure('PyQt')
decodeFile = None
Document = None
DocumentWindow = None

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
ICON_DIR = os.path.join(LOCAL_DIR, 'gui', 'mainwindow', 'images')
ICON_PATH1 = os.path.join(ICON_DIR, 'cadnano25-app-icon_512.png')
ICON_PATH2 = os.path.join(ICON_DIR, 'cadnano25-app-icon_256.png')
ICON_PATH3 = os.path.join(ICON_DIR, 'cadnano25-app-icon_48.png')

ROOTDIR = os.path.dirname(LOCAL_DIR)

if platform.system() == 'Windows':
    import ctypes
    myappid = 'org.cadnano.cadnano.2.5.2'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class CadnanoQt(QObject):
    dontAskAndJustDiscardUnsavedChanges = False
    documentWasCreatedSignal = pyqtSignal(object)  # doc
    documentWindowWasCreatedSignal = pyqtSignal(object, object)  # doc, window

    def __init__(self, argv):
        """Create the application object
        """
        self.argns, unused = util.parse_args(argv, use_gui=True)
        # util.init_logging(self.argns.__dict__)
        # logger.info("CadnanoQt initializing...")
        if argv is None:
            argv = sys.argv
        self.argv = argv
        # print("initializing new CadnanoQt", type(QCoreApplication.instance()))
        if QCoreApplication.instance() is None:
            self.qApp = QApplication(argv)
            assert(QCoreApplication.instance() is not None)
            self.qApp.setOrganizationDomain("cadnano.org")
        else:
            self.qApp = qApp
        super(CadnanoQt, self).__init__()
        # print("initialized new CadnanoQt")
        from cadnano.views.preferences import Preferences
        self.prefs = Preferences()
        self.icon = icon = QIcon(ICON_PATH1)
        icon.addFile(ICON_PATH2, QSize(256, 256))
        icon.addFile(ICON_PATH3, QSize(48, 48))
        self.qApp.setWindowIcon(icon)
        self.main_event_loop = None
        self.document_windows: set = set()  # Open documents
        self.active_document = None
        self._document = None
        self.documentWasCreatedSignal.connect(self.wirePrefsSlot)
    # end def

    def document(self) -> DocT:
        return self._document
    # end def

    def finishInit(self):
        global decodeFile
        global Document
        global DocumentWindow
        from cadnano.document import Document
        from cadnano.fileio.decode import decodeFile
        from cadnano.views.documentwindow import DocumentWindow
        from cadnano.views.pathview import pathstyles as styles

        styles.setFontMetrics()

        doc = Document()
        self._document = self.createDocument(base_doc=doc)

        if os.environ.get('CADNANO_DISCARD_UNSAVED', False) and not self.ignoreEnv():
            self.dontAskAndJustDiscardUnsavedChanges = True
        self.dontAskAndJustDiscardUnsavedChanges = True
    # end def

    def exec_(self):
        if hasattr(self, 'qApp'):
            self.main_event_loop = QEventLoop()
            self.main_event_loop.exec_()

    def destroyApp(self):
        """Destroy the QApplication.

        Do not set `self.qApp = None` in this method.
        Do it external to the CadnanoQt class
        """
        global decodeFile
        global Document
        global DocumentWindow
        # print("documentWasCreatedSignal", self.documentWasCreatedSignal)
        if len(self.document_windows) > 0:
            self.documentWasCreatedSignal.disconnect(self.wirePrefsSlot)
        decodeFile = None
        Document = None
        DocumentWindow = None
        self.document_windows.clear()
        self.qApp.quit()
    # end def

    def ignoreEnv(self):
        return os.environ.get('CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME', False)

    def createDocument(self, base_doc: DocT = None):
        global DocumentWindow
        # print("CadnanoQt createDocument begin")
        default_file = self.argns.file or os.environ.get('CADNANO_DEFAULT_DOCUMENT', None)
        if default_file is not None and base_doc is not None:
            default_file = os.path.expanduser(default_file)
            default_file = os.path.expandvars(default_file)
            dw = DocumentWindow(base_doc)
            self.document_windows.add(dw)
            # logger.info("Loading cadnano file %s to base document %s", default_file, base_doc)
            decodeFile(default_file, document=base_doc)
            dw.setFileName(default_file)
            print("Loaded default document: %s" % (default_file))
        else:
            doc_window_count = len(self.document_windows)
            # logger.info("Creating new empty document...")
            if doc_window_count == 0:  # first dw
                # dw adds itself to app.document_windows
                dw = DocumentWindow(base_doc)
                self.document_windows.add(dw)
            elif doc_window_count == 1:  # dw already exists
                dw = list(self.document_windows)[0]
                dw.newDocument()  # tell it to make a new doucment
        # print("CadnanoQt createDocument done")
        return dw.document()

    def prefsClicked(self):
        self.prefs.showDialog()

    def wirePrefsSlot(self, document: DocT):
        """MUST CALL THIS TO SET PREFERENCES :class:`Document`
        """
        self.prefs.document = document
