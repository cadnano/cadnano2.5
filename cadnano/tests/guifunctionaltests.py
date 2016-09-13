import sys, os, io, time

import pytest

from .cnguitestcase import GUITestApp

@pytest.fixture()
def cnapp():
    app = GUITestApp()
    yield app
    app.tearDown()

####################### Staple Comparison Tests ########################
def testStapleOutput_simple42legacy(cnapp):
    """p7308 applied to 42-base duplex (json source)"""
    designname = "simple42legacy.json"
    refname = "simple42legacy.csv"
    sequences = [("p7308", 0, 0)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_skip(cnapp):
    """Simple design with a single skip"""
    designname = "skip.json"
    refname = "skip.csv"
    sequences = [("M13mp18", 0, 14)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_inserts_and_skips(cnapp):
    """Insert and skip stress test"""
    designname = "loops_and_skips.json"
    refname = "loops_and_skips.csv"
    sequences = [("M13mp18", 0, 0)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_Nature09_monolith(cnapp):
    """Staples match reference set for Nature09 monolith"""
    designname = "Nature09_monolith.json"
    refname = "Nature09_monolith.csv"
    sequences = [("p7560", 4, 73)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_insert_size_1(cnapp):
    """Test sequence output with a single insert of size 1"""
    designname = "loop_size_1.json"
    refname = "loop_size_1.csv"
    sequences = [("M13mp18", 0, 14)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

# def testStapleOutput_Nature09_squarenut(cnapp):
#      """Staples match reference set for Nature09 squarenut"""
#      designname = "Nature09_squarenut.json"
#      refname = "Nature09_squarenut.csv"
#      sequences = [("p7560", 15, 100)]
#      test_set = cnapp.getTestSequences(designname, sequences)
#      # cnapp.writeRefSequences("Nature09_squarenut2.csv", test_set)
#      ref_set = cnapp.getRefSequences(refname)
#      assert test_set == ref_set

def testStapleOutput_Science09_prot120_98_v3(cnapp):
    """Staples match reference set for Science09 protractor 120 v3"""
    designname = "Science09_prot120_98_v3.json"
    refname = "Science09_prot120_98_v3.csv"
    sequences = [("p7704", 0, 105)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_Science09_beachball_v1_json(cnapp):
    """Staples match reference set for Science09 beachball (json source)"""
    designname = "Science09_beachball_v1.json"
    refname = "Science09_beachball_v1.csv"
    sequences = [("p7308", 10, 221)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_Gap_Vs_Skip(cnapp):
    """Staple gap output as '?'; staple skip output as ''"""
    designname = "gap_vs_skip.json"
    refname = "gap_vs_skip.csv"
    sequences = [("M13mp18", 0, 11), ("M13mp18", 2, 11)]
    test_set = cnapp.getTestSequences(designname, sequences)
    # cnapp.writeRefSequences("gap_vs_skip.csv_2.csv", test_set)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

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