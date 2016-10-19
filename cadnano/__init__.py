import sys
from .cnproxy import tapp

__version__ = '2.5.1.1'

global shared_app
shared_app = tapp

global batch
batch = False
global reopen
reopen = False


def getBatch():
    global batch
    return batch


def setBatch(is_batch):
    global batch
    batch = is_batch


def getReopen():
    global reopen
    return reopen


def setReopen(is_reopen):
    global reopen
    reopen = is_reopen


def app():
    global shared_app
    return shared_app


def initAppWithGui(app_args=None, do_exec=True):
    global shared_app
    from cadnano.cadnanoqt import CadnanoQt
    # 1. Create the application object
    shared_app = CadnanoQt(app_args)
    # 2. Use the object to finish importing and creating
    # application wide objects
    shared_app.finishInit()
    if do_exec:
        sys.exit(shared_app.exec_())
    return shared_app
