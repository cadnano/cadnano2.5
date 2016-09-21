# -*- coding: utf-8 -*-
import sys, os, io, time

import pytest

from cnguitestcase import GUITestApp
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtTest import QTest

@pytest.fixture()
def cnapp():
    app = GUITestApp()
    yield app
    app.tearDown()

DELAY = 20 # milliseconds

####################### Standard Functional Tests ########################
def testCreateVirtualHelix(cnapp):
    """Alt+Click on a 5' or 3' endpoint extends it to its boundary."""
    # Create a new Honeycomb part
    main_toolbar = cnapp.window.main_toolbar
    new_dna_part_button = main_toolbar.widgetForAction(
                                            cnapp.window.action_new_dnapart)
    QTest.mouseClick(new_dna_part_button, Qt.LeftButton, delay=DELAY)
    # Click each SliceHelix
    slicerootitem = cnapp.window.sliceroot
    assert len(slicerootitem.instance_items) == 1
    slice_part_item = list(slicerootitem.instance_items.values())[0]
    QTest.keyClick(cnapp.window, Qt.Key_H, delay=DELAY)
    QTest.keyClick(cnapp.window, Qt.Key_N, delay=DELAY)
    # could try different positions
    cnapp.graphicsItemClick(slice_part_item, Qt.LeftButton, delay=DELAY)
    cnapp.processEvents()
    # time.sleep(3)

    # sliceGraphicsItem = self.document_controller.sliceGraphicsItem
    # slicehelix1 = sliceGraphicsItem.getSliceHelixByCoord(0, 0)
    # slicehelix2 = sliceGraphicsItem.getSliceHelixByCoord(0, 1)
    # self.mousePress(slicehelix1, qgraphicsscene=self.mainWindow.slicescene)
    # self.mousePress(slicehelix2, qgraphicsscene=self.mainWindow.slicescene)
    # # Click the path helices with the ALT modifier
    # pathHelixGroup = self.document_controller.pathHelixGroup
    # ph0 = pathHelixGroup.getPathHelix(0)
    # ph1 = pathHelixGroup.getPathHelix(1)
    # self.mousePress(ph0, position=QPoint(410, 10),\
    #                 modifiers=Qt.AltModifier,\
    #                 qgraphicsscene=self.mainWindow.pathscene)
    # self.mousePress(ph0, position=QPoint(450, 10),\
    #                 modifiers=Qt.AltModifier,\
    #                 qgraphicsscene=self.mainWindow.pathscene)
    # self.mousePress(ph1, position=QPoint(410, 30),\
    #                 modifiers=Qt.AltModifier,\
    #                 qgraphicsscene=self.mainWindow.pathscene)
    # self.mousePress(ph1, position=QPoint(450, 30),\
    #                 modifiers=Qt.AltModifier,\
    #                 qgraphicsscene=self.mainWindow.pathscene)
    # # Check the model for correctness
    # vh0 = self.app.v[0]
    # vh1 = self.app.v[1]
    # str0 = "0 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n0 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    # str1 = "1 Scaffold: _,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,> <,_\n1 Staple:   _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_ _,_"
    # self.assertEqual(repr(vh0), str0)
    # self.assertEqual(repr(vh1), str1)
    # self.debugHere()  # Stop simulation and give control to user