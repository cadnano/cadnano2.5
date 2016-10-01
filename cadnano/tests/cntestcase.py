# -*- coding: utf-8 -*-
import os, io
pjoin = os.path.join

import pytest

from pathsetup import TEST_PATH
from cadnano.data.dnasequences import sequences

@pytest.fixture()
def cnapp():
    app = CNTestApp()
    yield app
    app.tearDown()

class CNTestApp(object):

    def __init__(self):
        # Document import must be here so as to allow for GUI tests to be run
        from cadnano.document import Document
        self.document = Document()

    def tearDown(self):
        pass

    def getTestSequences(self, designname, sequences_to_apply):
        """
        Called by a sequence-verification functional test to read in a file
        (designname), apply scaffold sequence(s) to that design, and return
        the set of staple sequences."""
        # set up the document
        inputfile = pjoin(TEST_PATH,
                            "data", designname)
        document = self.document
        document.readFile(inputfile)

        part = document.activePart()
        # apply one or more sequences to the design
        for sequence_name, start_id_num, start_idx in sequences_to_apply:
            sequence = sequences.get(sequence_name, None)
            for id_num in part.getIdNums():
                fwd_ss, rev_ss = part.getStrandSets(id_num)
                if id_num == start_id_num:
                    strand = fwd_ss.getStrand(start_idx)
                    strand.oligo().applySequence(sequence)
        generated_sequences = part.getSequences()
        return set(generated_sequences.splitlines())
    # end def

    @staticmethod
    def getRefSequences(designname):
        """docstring for getRefSequences"""
        staple_file = pjoin(TEST_PATH,
                            "data", designname)
        with io.open(staple_file, 'r', encoding='utf-8') as f:
            read_sequences = f.read()
        return set(read_sequences.splitlines())

    @staticmethod
    def writeRefSequences(designname, data):
        """docstring for getRefSequences"""
        staple_file = pjoin(TEST_PATH,
                            "data", designname)
        with io.open(staple_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(data))
# end class