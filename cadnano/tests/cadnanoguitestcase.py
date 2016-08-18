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

import sys
import unittest
import os
opj, opd, opr = os.path.join, os.path.dirname, os.path.realpath
TEST_PATH = os.path.abspath(opd(__file__))
CN_PATH = opd(TEST_PATH)
PROJECT_PATH = opd(CN_PATH)
sys.path.insert(0, PROJECT_PATH)


from cadnano import initAppWithGui
import cadnano.tests.guitestcase as guitestcase

main = guitestcase.main


class CadnanoGuiTestCase(guitestcase.GUITestCase):
    """SEE: http://docs.python.org/library/unittest.html
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        For GUI Tests, you always have to call setWidget to tell the
        framework what you will be testing.
        """
        argv = None
        self.app = initAppWithGui(argv, do_exec=False)  # kick off a Gui style app
        self.document_controller = list(self.app.document_controllers)[0]
        self.mainWindow = self.document_controller.win

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
        print("new doc begin")
        self.document_controller.newDocument()
        print("new doc end")
        guitestcase.GUITestCase.tearDown(self)

if __name__ == '__main__':
    unittest.main(verbosity=2)
