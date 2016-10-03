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

    # 1. test strand creating
    assert fwd_ss.createStrand(0, 84) is None
    strand1_fwd = fwd_ss.createStrand(0, 21)
    assert strand1_fwd is not None
    strand1_rev = rev_ss.createStrand(3, 24)
    assert strand1_rev is not None
    strand1_get = fwd_ss.getStrand(1)
    assert strand1_fwd is strand1_get

    # 2. test overlapping strands
    overlapping = fwd_ss.getOverlappingStrands(0, 21)
    assert strand1_fwd == overlapping[0]

    # print('\n')
    # print(overlapping)

    # 3. test neighbor getting
    neighbors = fwd_ss.getNeighbors(strand1_fwd)
    assert neighbors == (None, None)

    # 4. test overlapping with existing strand
    strand2_fwd = fwd_ss.createStrand(19, 30)
    assert strand2_fwd is None

    strand2_fwd = fwd_ss.createStrand(23, 30)
    assert strand2_fwd is not None
    strand3_fwd = fwd_ss.createStrand(31, 40)
    assert strand3_fwd is not None

    # 5. more neighbor testing
    neighbors = fwd_ss.getNeighbors(strand1_fwd)
    assert neighbors == (None, strand2_fwd)
    neighbors = fwd_ss.getNeighbors(strand2_fwd)
    assert neighbors == (strand1_fwd, strand3_fwd)

    # 6 remove middle strand
    fwd_ss.removeStrand(strand2_fwd)
    neighbors = fwd_ss.getNeighbors(strand3_fwd)
    assert neighbors == (strand1_fwd, None)
# end def