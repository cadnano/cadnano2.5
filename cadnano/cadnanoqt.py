import sys, os

from code import interact

from cadnano.proxyconfigure import proxyConfigure
proxyConfigure('PyQt')
import cadnano.util as util
decode = None
Document = None
DocumentController = None


from PyQt5.QtCore import QObject, QCoreApplication, pyqtSignal, Qt, QEventLoop, QSize

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import qApp, QApplication, QUndoGroup

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__)) 
# ICON_PATH = os.path.join(LOCAL_DIR, 'gui','ui', 'mainwindow', 
#                                 'images', 'cadnano2-app-icon.png')
# print(ICON_PATH)
ICON_PATH = os.path.join(LOCAL_DIR, 'gui','ui', 'mainwindow', 
                                'images', 'radnano-app-icon.png')
class CadnanoQt(QObject):
    dontAskAndJustDiscardUnsavedChanges = False
    shouldPerformBoilerplateStartupScript = False
    documentWasCreatedSignal = pyqtSignal(object)  # doc
    documentWindowWasCreatedSignal = pyqtSignal(object, object)  # doc, window

    def __init__(self, argv):
        """ Create the application object
        """
        if argv is None:
            argv = []
        self.argv = argv
        if QCoreApplication.instance() == None:
            self.qApp = QApplication(argv)
            self.qApp.setWindowIcon(QIcon(ICON_PATH))
            assert(QCoreApplication.instance() != None)
            self.qApp.setOrganizationDomain("cadnano.org")
        else:
            self.qApp = qApp
        super(CadnanoQt, self).__init__()
        from cadnano.gui.views.preferences import Preferences
        self.prefs = Preferences()
        icon = QIcon(ICON_PATH)
        self.qApp.setWindowIcon(icon)


        self.document_controllers = set()  # Open documents
        self.active_document = None
        self.vh = {}  # Newly created VirtualHelix register here by idnum.
        self.vhi = {}
        self.partItem = None


    def finishInit(self):
        global decode
        global Document
        global DocumentController
        from cadnano.document import Document
        from cadnano.fileio.nnodecode import decode
        from cadnano.gui.controllers.documentcontroller import DocumentController
        from cadnano.gui.views.pathview import pathstyles as styles
        doc = Document()
        self.d = self.newDocument(base_doc=doc)
        styles.setFontMetrics()
        
        os.environ['CADNANO_DISCARD_UNSAVED'] = 'True' ## added by Nick 
        if os.environ.get('CADNANO_DISCARD_UNSAVED', False) and not self.ignoreEnv():
            self.dontAskAndJustDiscardUnsavedChanges = True
        if os.environ.get('CADNANO_DEFAULT_DOCUMENT', False) and not self.ignoreEnv():
            self.shouldPerformBoilerplateStartupScript = True
        util.loadAllPlugins()
        if "-i" in self.argv:
            print("Welcome to cadnano's debug mode!")
            print("Some handy locals:")
            print("\ta\tcadnano.app() (the shared cadnano application object)")
            print("\td()\tthe last created Document")
            def d():
                return self.d

            print("\tw()\tshortcut for d().controller().window()")
            def w():
                return self.d.controller().window()

            print("\tp()\tshortcut for d().selectedPart()")
            def p():
                return self.d.selectedPart()

            print("\tpi()\tthe PartItem displaying p()")
            def pi():
                return w().pathroot.partItemForPart(p())

            print( "\tvh(i)\tshortcut for p().virtualHelix(i)")
            def vh(vhref):
                return p().virtualHelix(vhref)

            print( "\tvhi(i)\tvirtualHelixItem displaying vh(i)")
            def vhi(vhref):
                partitem = pi()
                vHelix = vh(vhref)
                return partitem.vhItemForVH(vHelix)
                
            print("\tquit()\tquit (for when the menu fails)")
            print("\tgraphicsItm.findChild()  see help(pi().findChild)")
            interact('', local={'a':self, 'd':d, 'w':w,\
                                'p':p, 'pi':pi, 'vh':vh, 'vhi':vhi,\
                                })
        # else:
        #     self.exec_()

    
    def exec_(self):
        if hasattr(self, 'qApp'):
            self.mainEventLoop = QEventLoop()
            self.mainEventLoop.exec_()
            #self.qApp.exec_()

    def ignoreEnv(self):
        return os.environ.get('CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME', False)

    def newDocument(self, base_doc=None):
        global DocumentController
        default_file = os.environ.get('CADNANO_DEFAULT_DOCUMENT', None)
        if default_file is not None and base_doc is not None:
            default_file = path.expanduser(default_file)
            default_file = path.expandvars(default_file)
            dc = DocumentController(doc)
            with open(default_file) as fd:
                file_contents = fd.read()
                decode(doc, file_contents)
                print("Loaded default document: %s" % (doc))
        else:
            doc_ctrlr_count = len(self.document_controllers)
            if doc_ctrlr_count == 0:  # first dc
                # dc adds itself to app.document_controllers
                dc = DocumentController(base_doc)
            elif doc_ctrlr_count == 1:  # dc already exists
                dc = list(self.document_controllers)[0]
                dc.newDocument()  # tell it to make a new doucment
        return dc.document()

    def prefsClicked(self):
        self.prefs.showDialog()
