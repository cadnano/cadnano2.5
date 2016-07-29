import os
import sys
import platform
from code import interact
from PyQt5.QtCore import QObject, QCoreApplication, pyqtSignal, QEventLoop, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import qApp, QApplication
from cadnano import util
from cadnano.proxyconfigure import proxyConfigure

proxyConfigure('PyQt')
decodeFile = None
Document = None
DocumentController = None

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
ICON_DIR = os.path.join(LOCAL_DIR, 'gui','ui', 'mainwindow', 'images')
ICON_PATH1 = os.path.join(ICON_DIR, 'radnano-app-icon.png')
ICON_PATH2 = os.path.join(ICON_DIR, 'radnano-app-icon256x256.png')
ICON_PATH3 = os.path.join(ICON_DIR, 'radnano-app-icon48x48.png')
CADNANO_DEFAULT_DOCUMENT = 'simple.json'
ROOTDIR = os.path.dirname(LOCAL_DIR)

os.environ['CADNANO_DEFAULT_DOCUMENT'] = os.path.join(
                ROOTDIR, 'tests', CADNANO_DEFAULT_DOCUMENT)

if platform.system() == 'Windows':
    import ctypes
    myappid = 'cadnano.cadnano.radnano.2.5.0' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class CadnanoQt(QObject):
    dontAskAndJustDiscardUnsavedChanges = False
    documentWasCreatedSignal = pyqtSignal(object)  # doc
    documentWindowWasCreatedSignal = pyqtSignal(object, object)  # doc, window

    def __init__(self, argv):
        """ Create the application object
        """
        self.argns, unused = util.parse_args(argv, gui=True)
        # util.init_logging(self.argns.__dict__)
        # logger.info("CadnanoQt initializing...")
        if argv is None:
            argv = sys.argv
        self.argv = argv
        if QCoreApplication.instance() is None:
            self.qApp = QApplication(argv)
            assert(QCoreApplication.instance() is not None)
            self.qApp.setOrganizationDomain("cadnano.org")
        else:
            self.qApp = qApp
        super(CadnanoQt, self).__init__()
        from cadnano.gui.views.preferences import Preferences
        self.prefs = Preferences()
        self.icon = icon = QIcon(ICON_PATH1)
        icon.addFile(ICON_PATH2, QSize(256, 256))
        icon.addFile(ICON_PATH3, QSize(48, 48))
        self.qApp.setWindowIcon(icon)

        self.document_controllers = set()  # Open documents
        self.active_document = None
        self.vh = {}  # Newly created VirtualHelix register here by idnum.
        self.vhi = {}
        self.partItem = None
        self.documentWasCreatedSignal.connect(self.wirePrefsSlot)

    def finishInit(self):
        global decodeFile
        global Document
        global DocumentController
        from cadnano.document import Document
        from cadnano.fileio.nnodecode import decodeFile
        from cadnano.gui.controllers.documentcontroller import DocumentController
        from cadnano.gui.views.pathview import pathstyles as styles

        doc = Document()
        self.d = self.newDocument(base_doc=doc)
        styles.setFontMetrics()

        os.environ['CADNANO_DISCARD_UNSAVED'] = 'True' ## added by Nick
        if os.environ.get('CADNANO_DISCARD_UNSAVED', False) and not self.ignoreEnv():
            self.dontAskAndJustDiscardUnsavedChanges = True
        util.loadAllPlugins()

        if self.argns.interactive:
            print("Welcome to cadnano's debug mode!")
            print("Some handy locals:")
            print("\ta\tcadnano.app() (the shared cadnano application object)")
            print("\td()\tthe last created Document")
            def d():
                return self.d

            print("\tw()\tshortcut for d().controller().window()")
            def w():
                return self.d.controller().window()

            print("\tp()\tshortcut for d().selectedInstance().reference()")
            def p():
                return self.d.selectedInstance().reference()

            print("\tpi()\tthe PartItem displaying p()")
            def pi():
                part_instance = self.d.selectedInstance()
                return w().pathroot.partItemForPart(part_instance)

            print( "\tvh(i)\tshortcut for p().reference().getStrandSets(i)")
            def strandsets(id_num):
                return p().reference().getStrandSets(id_num)

            print( "\tvhi(i)\tvirtualHelixItem displaying vh(i)")
            def vhi(id_num):
                partitem = pi()
                return partitem.vhItemForIdNum(id_num)

            print("\tquit()\tquit (for when the menu fails)")
            print("\tgraphicsItm.findChild()  see help(pi().findChild)")
            interact('', local={'a':self, 'd':d, 'w':w,\
                                'p':p, 'pi':pi, 'vh':vh, 'vhi':vhi,\
                                })


    def exec_(self):
        if hasattr(self, 'qApp'):
            self.mainEventLoop = QEventLoop()
            self.mainEventLoop.exec_()
            #self.qApp.exec_()

    def ignoreEnv(self):
        return os.environ.get('CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME', False)

    def newDocument(self, base_doc=None):
        global DocumentController
        default_file = self.argns.file or os.environ.get('CADNANO_DEFAULT_DOCUMENT', None)
        if default_file is not None and base_doc is not None:
            default_file = os.path.expanduser(default_file)
            default_file = os.path.expandvars(default_file)
            dc = DocumentController(base_doc)
            # logger.info("Loading cadnano file %s to base document %s", default_file, base_doc)
            decodeFile(default_file, document=base_doc)
            dc.setFilename(default_file)
            print("Loaded default document: %s" % (default_file))
        else:
            doc_ctrlr_count = len(self.document_controllers)
            # logger.info("Creating new empty document...")
            if doc_ctrlr_count == 0:  # first dc
                # dc adds itself to app.document_controllers
                dc = DocumentController(base_doc)
            elif doc_ctrlr_count == 1:  # dc already exists
                dc = list(self.document_controllers)[0]
                dc.newDocument()  # tell it to make a new doucment
        return dc.document()

    def prefsClicked(self):
        self.prefs.showDialog()

    def wirePrefsSlot(self, document):
        self.prefs.document = document
