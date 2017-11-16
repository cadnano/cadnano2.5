# Added NC to add the Library path

import os.path
from .QtCore import QCoreApplication
LOCAL_QT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Qt')
QCoreApplication.addLibraryPath(os.path.join(LOCAL_QT, 'plugins'))
