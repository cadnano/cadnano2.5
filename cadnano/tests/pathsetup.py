# -*- coding: utf-8 -*-
import sys, os, io
pjoin, opd, opr = os.path.join, os.path.dirname, os.path.realpath
TEST_PATH = os.path.abspath(opd(__file__))
CN_PATH = opd(TEST_PATH)
PROJECT_PATH = opd(CN_PATH)
sys.path.insert(0, PROJECT_PATH)
sys.path.insert(0, TEST_PATH)
