import pytest
import math

from cntestcase import cnapp

from nucleicacidparttest import create3Helix

def testStrandset(cnapp):
    doc = cnapp.document
    HELIX_LENGTH = 42
    part = create3Helix(doc, [0, 0, 1], HELIX_LENGTH)
    fwd_ss, rev_ss = part.getStrandSets(0)
    assert fwd_ss.isForward()
    assert not rev_ss.isForward()
    assert rev_ss.isReverse()
    assert fwd_ss.length() == HELIX_LENGTH
    assert fwd_ss.idNum() == 0

    assert fwd_ss.createStrand(0, 84) == -1
    assert fwd_ss.createStrand(0, 21) == 0
    assert rev_ss.createStrand(3, 24) == 0

    strand = fwd_ss.getStrand(1)
    overlapping = fwd_ss.getOverlappingStrands(0, 21)
# end def