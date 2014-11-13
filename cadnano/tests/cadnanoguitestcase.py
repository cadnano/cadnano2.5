# The MIT License
#
# Copyright (c) 2011 Wyss Institute at Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# http://www.opensource.org/licenses/mit-license.php

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import cadnano
import tests.guitestcase

main = tests.guitestcase.main


class CadnanoGuiTestCase(tests.guitestcase.GUITestCase):
    """
    SEE: http://docs.python.org/library/unittest.html
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        For GUI Tests, you always have to call setWidget to tell the
        framework what you will be testing.
        """
        import sys
        
        self.app = cadnano.initAppWithGui() # kick off a Gui style app
        self.documentController = list(self.app.documentControllers)[0]
        self.mainWindow = self.documentController.win

        # Include this or the automatic build will hang
        self.app.dontAskAndJustDiscardUnsavedChanges = True

        # By setting the widget to the main window we can traverse and
        # interact with any part of it. Also, tearDown will close
        # the application so we don't need to worry about that.
        self.setWidget(self.mainWindow, False, None)

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        tests.guitestcase.GUITestCase.tearDown(self)

if __name__ == '__main__':
    tests.guitestcase.main()
