# -*- coding: utf-8 -*-
import pytest
import math

from .cntestcase import CNTestApp

@pytest.fixture()
def cnapp():
    app = CNTestApp()
    yield app
    app.tearDown()

from cadnano.part.nucleicacidpart import NucleicAcidPart

def create3Helix(doc, direction, length):
    part = NucleicAcidPart(document=doc)
    assert len(part.getidNums()) == 0
    radius = part.radius()
    origin_pt00 = (0, 0, 0)
    origin_pt90 = (0, 2*radius, 0)
    theta = math.radians(30)
    origin_pt60 = (2*radius*math.cos(-theta), 2*radius*math.sin(-theta), 0)
    color = part.getColor()
    part.createHelix(0, origin_pt00, direction, length, color)
    part.createHelix(1, origin_pt60, direction, length, color)
    part.createHelix(2, origin_pt90, direction, length, color)
    return part

@pytest.mark.parametrize('direction', [(0, 0, 1), (0, 1, 0)])
def testVirtualHelixCreate(cnapp, direction):
    doc = cnapp.document
    part = create3Helix(doc, direction, 42)
    id_nums = part.getidNums()
    assert len(id_nums) == 3

def testVirtualHelixResize(cnapp):
    doc = cnapp.document
    start_length = 42
    end_length = 84
    part = create3Helix(doc, (0, 0, 1), start_length)
    assert part.getVirtualHelixProperties(1, 'length') == start_length
    part.setVirtualHelixSize(1, end_length)
    assert part.getVirtualHelixProperties(1, 'length') == end_length
    with pytest.raises(NotImplementedError):
        part.setVirtualHelixSize(1, start_length)

def testRemove(cnapp):
    doc = cnapp.document
    start_length = 42
    end_length = 84
    part = create3Helix(doc, (0, 0, 1), start_length)
    # us = part.undoStack()
    # part.remove()
    # assert len(doc.children()) == 0
    # us.undo()





