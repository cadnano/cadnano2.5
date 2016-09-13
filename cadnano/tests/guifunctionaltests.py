"""
guifunctionaltests.py
"""
import sys
import unittest
import os.path
pjoin = os.path.join
import time
import io

from cadnanoguitestcase import CadnanoGuiTestCase, TEST_PATH
from cadnano.data.dnasequences import sequences

class FunctionalTests(CadnanoGuiTestCase):
    """
    Functional tests are end-to-end tests that simulate user interaction
    with the interface and verify that the final outputs (e.g. staple
    sequences) are correct.

    Run these tests by calling "python -m tests.functionaltests" from cadnano2
    root directory.
    """
    def setUp(self):
        """
        The setUp method is called before running any test. It is used
        to set the general conditions for the tests to run correctly.
        """
        CadnanoGuiTestCase.setUp(self)
        # Add extra initialization here

    def tearDown(self):
        """
        The tearDown method is called at the end of running each test,
        generally used to clean up any objects created in setUp
        """
        CadnanoGuiTestCase.tearDown(self)
        # Add functional-test-specific cleanup here

    def getTestSequences(self, designname, sequences_to_apply):
        """
        Called by a sequence-verification functional test to read in a file
        (designname), apply scaffold sequence(s) to that design, and return
        the set of staple sequences."""
        # set up the document
        from cadnano.fileio.nnodecode import decodeFile
        inputfile = pjoin(TEST_PATH,
                            "functionaltestinputs", designname)
        document = self.document_controller.document()
        decodeFile(inputfile, document=document)
        self.setWidget(self.document_controller.win, False, None)
        # part = document.selectedInstance()
        part = self.document_controller.activePart()
        # apply one or more sequences to the design
        for sequence_name, start_id_num, start_idx in sequences_to_apply:
            sequence = sequences.get(sequence_name, None)
            for id_num in part.getIdNums():
                fwd_ss, rev_ss = part.getStrandSets(id_num)
                if id_num == start_id_num:
                    strand = fwd_ss.getStrand(start_idx)
                    strand.oligo().applySequence(sequence)
        generated_sequences = part.getStapleSequences()
        return set(generated_sequences.splitlines())

    def getRefSequences(self, designname):
        """docstring for getRefSequences"""
        staple_file = pjoin(TEST_PATH,
                            "functionaltestinputs", designname)
        with io.open(staple_file, 'r', encoding='utf-8') as f:
            read_sequences = f.read()
        return set(read_sequences.splitlines())

    def writeRefSequences(self, designname, data):
        """docstring for getRefSequences"""
        staple_file = pjoin(TEST_PATH,
                            "functionaltestinputs", designname)
        with io.open(staple_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(data))

    ####################### Staple Comparison Tests ########################
    def testStapleOutput_simple42legacy(self):
        """p7308 applied to 42-base duplex (json source)"""
        designname = "simple42legacy.json"
        refname = "simple42legacy.csv"
        sequences = [("p7308", 0, 0)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_insert_size_1(self):
        """Test sequence output with a single insert of size 1"""
        designname = "loop_size_1.json"
        refname = "loop_size_1.csv"
        sequences = [("M13mp18", 0, 14)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_skip(self):
        """Simple design with a single skip"""
        designname = "skip.json"
        refname = "skip.csv"
        sequences = [("M13mp18", 0, 14)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_inserts_and_skips(self):
        """Insert and skip stress test"""
        designname = "loops_and_skips.json"
        refname = "loops_and_skips.csv"
        sequences = [("M13mp18", 0, 0)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_Nature09_monolith(self):
        """Staples match reference set for Nature09 monolith"""
        designname = "Nature09_monolith.json"
        refname = "Nature09_monolith.csv"
        sequences = [("p7560", 4, 73)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    # def testStapleOutput_Nature09_squarenut(self):
    #      """Staples match reference set for Nature09 squarenut"""
    #      designname = "Nature09_squarenut.json"
    #      refname = "Nature09_squarenut.csv"
    #      sequences = [("p7560", 15, 100)]
    #      test_set = self.getTestSequences(designname, sequences)
    #      # self.writeRefSequences("Nature09_squarenut2.csv", test_set)
    #      ref_set = self.getRefSequences(refname)
    #      self.assertEqual(test_set, ref_set)

    def testStapleOutput_Science09_prot120_98_v3(self):
        """Staples match reference set for Science09 protractor 120 v3"""
        designname = "Science09_prot120_98_v3.json"
        refname = "Science09_prot120_98_v3.csv"
        sequences = [("p7704", 0, 105)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_Science09_beachball_v1_json(self):
        """Staples match reference set for Science09 beachball (json source)"""
        designname = "Science09_beachball_v1.json"
        refname = "Science09_beachball_v1.csv"
        sequences = [("p7308", 10, 221)]
        test_set = self.getTestSequences(designname, sequences)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    def testStapleOutput_Gap_Vs_Skip(self):
        """Staple gap output as '?'; staple skip output as ''"""
        designname = "gap_vs_skip.json"
        refname = "gap_vs_skip.csv"
        sequences = [("M13mp18", 0, 11), ("M13mp18", 2, 11)]
        test_set = self.getTestSequences(designname, sequences)
        # self.writeRefSequences("gap_vs_skip.csv_2.csv", test_set)
        ref_set = self.getRefSequences(refname)
        self.assertEqual(test_set, ref_set)

    ####################### Standard Functional Tests ########################
    # def testActiveSliceHandleAltShiftClick(self):
    #     """Alt+Shift+Click on ActiveSliceHandle extends scaffold strands."""
    #     # Create a new Honeycomb part
    #     newHoneycombPartButton = self.mainWindow.selection_toolbar.widgetForAction(\
    #                                    self.mainWindow.actionNewHoneycombPart)
    #     self.click(newHoneycombPartButton)
    #     # Click each SliceHelix
    #     sliceGraphicsItem = self.document_controller.sliceGraphicsItem
    #     slicehelix1 = sliceGraphicsItem.getSliceHelixByCoord(0, 0)
    #     slicehelix2 = sliceGraphicsItem.getSliceHelixByCoord(0, 1)
    #     self.click(slicehelix1, qgraphicsscene=self.mainWindow.slicescene)
    #     self.click(slicehelix2, qgraphicsscene=self.mainWindow.slicescene)
    #     # Click the activeSliceHandle with ALT and SHIFT modifiers
    #     pathHelixGroup = self.document_controller.pathHelixGroup
    #     activeSliceHandle = pathHelixGroup.activeSliceHandle()
    #     self.mousePress(activeSliceHandle,\
    #                     modifiers=Qt.AltModifier|Qt.ShiftModifier,\
    #                     qgraphicsscene=self.mainWindow.pathscene)
    #     # Check the model for correctness
    #     vh0 = self.app.v[0]
    #     vh1 = self.app.v[1]
    #     str0 = "0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    #     str1 = "1 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    #     self.assertEqual(repr(vh0), str0)
    #     self.assertEqual(repr(vh1), str1)
    #
    # def testEndpointAltClick(self):
    #     """Alt+Click on a 5' or 3' endpoint extends it to its boundary."""
    #     # Create a new Honeycomb part
    #     newHoneycombPartButton = self.mainWindow.selection_toolbar.widgetForAction(\
    #                                    self.mainWindow.actionNewHoneycombPart)
    #     self.click(newHoneycombPartButton)
    #     # Click each SliceHelix
    #     sliceGraphicsItem = self.document_controller.sliceGraphicsItem
    #     slicehelix1 = sliceGraphicsItem.getSliceHelixByCoord(0, 0)
    #     slicehelix2 = sliceGraphicsItem.getSliceHelixByCoord(0, 1)
    #     self.mousePress(slicehelix1, qgraphicsscene=self.mainWindow.slicescene)
    #     self.mousePress(slicehelix2, qgraphicsscene=self.mainWindow.slicescene)
    #     # Click the path helices with the ALT modifier
    #     pathHelixGroup = self.document_controller.pathHelixGroup
    #     ph0 = pathHelixGroup.getPathHelix(0)
    #     ph1 = pathHelixGroup.getPathHelix(1)
    #     self.mousePress(ph0, position=QPoint(410, 10),\
    #                     modifiers=Qt.AltModifier,\
    #                     qgraphicsscene=self.mainWindow.pathscene)
    #     self.mousePress(ph0, position=QPoint(450, 10),\
    #                     modifiers=Qt.AltModifier,\
    #                     qgraphicsscene=self.mainWindow.pathscene)
    #     self.mousePress(ph1, position=QPoint(410, 30),\
    #                     modifiers=Qt.AltModifier,\
    #                     qgraphicsscene=self.mainWindow.pathscene)
    #     self.mousePress(ph1, position=QPoint(450, 30),\
    #                     modifiers=Qt.AltModifier,\
    #                     qgraphicsscene=self.mainWindow.pathscene)
    #     # Check the model for correctness
    #     vh0 = self.app.v[0]
    #     vh1 = self.app.v[1]
    #     str0 = "0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    #     str1 = "1 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    #     self.assertEqual(repr(vh0), str0)
    #     self.assertEqual(repr(vh1), str1)
    #     # self.debugHere()  # Stop simulation and give control to user


if __name__ == '__main__':
    print("Running Functional Tests")
    """Use a TestRunner to get rid of dumb PendingDepricationWarning in
    distutils.__init__.py when it call

        import imp

    Python 3.5 released without changing imp to importlib
    """
    tr = unittest.TextTestRunner(warnings=None)
    unittest.main(testRunner=tr, verbosity=2)
