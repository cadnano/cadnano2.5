"""
runtests.py
Helper file to run tests with 1 command and output the results to an XML file.
Usage: From the main cadnano folder: python -m tests.runtests
Created by Flo Mazzoldi on 2011-06-15.

My TextMate Script:

cd "$TM_PROJECT_DIRECTORY"
CADNANO_RUN_PLAINTEXT_TESTS=YES CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME=YES python tests/runall.py | pre
"""

import glob
import os
import unittest
from cadnano.tests.xmlrunner import XMLTestRunner
# from unittests import UnitTests
# from modeltests import ModelTests
from cadnano.tests.functionaltests import FunctionalTests
# from recordedtests.template import RecordedTests

def main(useXMLRunner=True):
    # load hard-coded tests
    # unitsuite = unittest.makeSuite(UnitTests)
    # modelsuite = unittest.makeSuite(ModelTests)
    funcsuite = unittest.makeSuite(FunctionalTests)

    # combine and run tests
    # alltests = unittest.TestSuite([unitsuite, modelsuite, funcsuite])
    alltests = unittest.TestSuite([funcsuite])
    if useXMLRunner:
        stream = open("testresults.xml", "w")
        runner = XMLTestRunner(stream)
        result = runner.run(alltests)
        stream.close()
    else:
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(alltests)
    return result


if __name__ == "__main__":
    textRunner = os.environ.get('CADNANO_RUN_PLAINTEXT_TESTS', None) == "YES"
    main(not textRunner)
