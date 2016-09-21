# -*- coding: utf-8 -*-
import sys, os, io, time

import pytest

from cntestcase import CNTestApp

@pytest.fixture()
def cnapp():
    app = CNTestApp()
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

def testStapleOutput_insert_size_1(cnapp):
    """Test sequence output with a single insert of size 1"""
    designname = "loop_size_1.json"
    refname = "loop_size_1.csv"
    sequences = [("M13mp18", 0, 14)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set

def testStapleOutput_Science09_prot120_98_v3(cnapp):
    """Staples match reference set for Science09 protractor 120 v3"""
    designname = "Science09_prot120_98_v3.json"
    refname = "Science09_prot120_98_v3.csv"
    sequences = [("p7704", 0, 105)]
    test_set = cnapp.getTestSequences(designname, sequences)
    ref_set = cnapp.getRefSequences(refname)
    assert test_set == ref_set


# def testStapleOutput_Nature09_monolith(cnapp):
#     """Staples match reference set for Nature09 monolith"""
#     designname = "Nature09_monolith.json"
#     refname = "Nature09_monolith.csv"
#     sequences = [("p7560", 4, 73)]
#     test_set = cnapp.getTestSequences(designname, sequences)
#     ref_set = cnapp.getRefSequences(refname)
#     assert test_set == ref_set

# def testStapleOutput_Nature09_squarenut(cnapp):
#      """Staples match reference set for Nature09 squarenut"""
#      designname = "Nature09_squarenut.json"
#      refname = "Nature09_squarenut2.csv"
#      sequences = [("p7560", 15, 100)]
#      test_set = cnapp.getTestSequences(designname, sequences)
#      # cnapp.writeRefSequences("Nature09_squarenut2.csv", test_set)
#      ref_set = cnapp.getRefSequences(refname)
#      assert test_set == ref_set

# def testStapleOutput_Science09_beachball_v1_json(cnapp):
#     """Staples match reference set for Science09 beachball (json source)"""
#     designname = "Science09_beachball_v1.json"
#     refname = "Science09_beachball_v1.csv"
#     sequences = [("p7308", 10, 221)]
#     test_set = cnapp.getTestSequences(designname, sequences)
#     ref_set = cnapp.getRefSequences(refname)
#     assert test_set == ref_set

# def testStapleOutput_Gap_Vs_Skip(cnapp):
#     """Staple gap output as '?'; staple skip output as ''"""
#     designname = "gap_vs_skip.json"
#     refname = "gap_vs_skip.csv"
#     sequences = [("M13mp18", 0, 11), ("M13mp18", 2, 11)]
#     test_set = cnapp.getTestSequences(designname, sequences)
#     # cnapp.writeRefSequences("gap_vs_skip.csv_2.csv", test_set)
#     ref_set = cnapp.getRefSequences(refname)
#     assert test_set == ref_set
