# To run:
# pytest -c cadnano/tests/pytestgui.ini cadnano/tests/

import pytest
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtTest import QTest

from cadnano.fileio.lattice import HoneycombDnaPart
from cadnano.views.sliceview import slicestyles
from cnguitestcase import GUITestApp


@pytest.fixture()
def cnapp():
    app = GUITestApp()
    yield app
    app.tearDown()


DELAY = 5  # milliseconds
RADIUS = slicestyles.SLICE_HELIX_RADIUS


####################### Standard Functional Tests ########################
def testCreateVirtualHelixGui(cnapp):
    """Create some VHs"""
    # Create a new Honeycomb part
    toolbar = cnapp.window.main_toolbar
    action_new_honeycomb = toolbar.widgetForAction(cnapp.window.action_new_dnapart_honeycomb)
    QTest.mouseClick(action_new_honeycomb, Qt.LeftButton, delay=DELAY)

    slicerootitem = cnapp.window.slice_root
    assert len(slicerootitem.instance_items) == 1
    slice_part_item = list(slicerootitem.instance_items.values())[0]
    QTest.keyClick(cnapp.window, Qt.Key_H, delay=DELAY)
    QTest.keyClick(cnapp.window, Qt.Key_C, delay=DELAY)
    cnapp.processEvents()

    cmd_count = 1  # already added the part
    for row in range(-2, 2):
        for col in range(-2, 2):
            # print(row, col)
            x, y = HoneycombDnaPart.latticeCoordToModelXY(RADIUS, row, col)
            pt = QPointF(x, y)
            cnapp.graphicsItemClick(slice_part_item, Qt.LeftButton, pos=pt, delay=DELAY)
            cmd_count += 1
    cnapp.processEvents()

    vh_count = len(cnapp.document.activePart().getidNums())

    # undo and redo all
    for i in range(cmd_count):
        cnapp.document.undoStack().undo()
    cnapp.processEvents()
    for i in range(cmd_count):
        cnapp.document.undoStack().redo()
    cnapp.processEvents()

    part = list(cnapp.document.children())[0]
    vh_count_after_redo = len(part.getidNums())

    assert vh_count == vh_count_after_redo
    # import time
    # time.sleep(3)

# end def
