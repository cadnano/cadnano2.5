"""
modeltests.py

Created by Shawn Douglas on 2011-06-28.

Instructions: copypaste the following script into TextMate's
Bundles > Bundle Editor > Show Bundle Editor > Python > Run Project Unit Tests

cd "$TM_PROJECT_DIRECTORY"
find . -name "*tests.py" -exec "${TM_PYTHON:-python}" '{}' \;|pre

"""

import sys
sys.path.insert(0, '.')

from cadnano.tests.cadnanoguitestcase import CadnanoGuiTestCase

class ModelTests(CadnanoGuiTestCase):
    """
    Create new tests by adding methods to this class that begin with "test".
    See for more detail: http://docs.python.org/library/unittest.html

    Run model tests by calling "python -m tests.modeltests" from cadnano2 root
    directory.
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        """
        CadnanoGuiTestCase.setUp(self)
        # Add extra model-test-specific initialization here

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        CadnanoGuiTestCase.tearDown(self)
        # Add model-test-specific cleanup here

    def testModel1(self):
        """docstring for testModel1"""
        pass


if __name__ == '__main__':
    print("Running Model Tests")
    tests.cadnanoguitestcase.main()
