# -*- coding: utf-8 -*-
import random

from cadnano import getBatch
from cadnano import preferences as prefs
from cadnano.cnproxy import UndoCommand
from cadnano.strand import Strand

class CreateXoverCommand(UndoCommand):
    """
    Creates a Xover from the 3' end of strand5p to the 5' end of strand3p
    this needs to
    1. preserve the old oligo of strand3p
    2. install the crossover
    3. apply the strand5p oligo to the strand3p
    """
    def __init__(self, part, strand5p, strand5p_idx, strand3p, strand3p_idx, update_oligo=True):
        super(CreateXoverCommand, self).__init__("create xover")
        self._part = part
        self._strand5p = strand5p
        self._strand5p_idx = strand5p_idx
        self._strand3p = strand3p
        self._strand3p_idx = strand3p_idx
        self._old_oligo3p = strand3p.oligo()
        self._update_oligo = update_oligo
    # end def

    def redo(self):
        part = self._part
        strand5p = self._strand5p
        strand5p_idx = self._strand5p_idx
        strand3p = self._strand3p
        strand3p_idx = self._strand3p_idx
        olg5p = strand5p.oligo()
        old_olg3p = self._old_oligo3p

        # 0. Deselect the involved strands
        doc = strand5p.document()
        doc.removeStrandFromSelection(strand5p)
        doc.removeStrandFromSelection(strand3p)

        fSetOligo = Strand.setOligo
        if self._update_oligo:
            # Test for Loopiness
            if olg5p == strand3p.oligo():
                olg5p._setLoop(True)
            else:
                # 1. update preserved oligo length
                olg5p._incrementLength(old_olg3p.length(), emit_signals=True)
                # 2. Remove the old oligo and apply the 5' oligo to the 3' strand
                old_olg3p.removeFromPart(emit_signals=True)
                for strand in strand3p.generator3pStrand():
                    # emits strandHasNewOligoSignal
                    fSetOligo(strand, olg5p, emit_signals=True)

        # 3. install the Xover
        strand5p.setConnection3p(strand3p)
        strand3p.setConnection5p(strand5p)

        # ss5 = strand5p.strandSet()
        # id_5p = ss5.idNum()
        # st5p = ss5.strandType()
        # ss3 = strand3p.strandSet()
        # id_3p = ss3.idNum()
        # st3p = ss3.strandType()

        if self._update_oligo:
            strand5p.strandUpdateSignal.emit(strand5p)
            strand3p.strandUpdateSignal.emit(strand3p)
    # end def

    def undo(self):
        part = self._part
        strand5p = self._strand5p
        strand5p_idx = self._strand5p_idx
        strand3p = self._strand3p
        strand3p_idx = self._strand3p_idx
        old_olg3p = self._old_oligo3p
        olg5p = strand5p.oligo()

        # 0. Deselect the involved strands
        doc = strand5p.document()
        doc.removeStrandFromSelection(strand5p)
        doc.removeStrandFromSelection(strand3p)

        # 1. uninstall the Xover
        strand5p.setConnection3p(None)
        strand3p.setConnection5p(None)

        if self._update_oligo:
            # Test Loopiness
            if old_olg3p.isLoop():
                old_olg3p._setLoop(False)
            else:
                # 2. restore the modified oligo length
                olg5p._decrementLength(old_olg3p.length(), emit_signals=True)
                # 3. apply the old oligo to strand3p
                old_olg3p.addToPart(part, emit_signals=True)
                for strand in strand3p.generator3pStrand():
                    # emits strandHasNewOligoSignal
                    fSetOligo(strand, old_olg3p, emit_signals=True)

        if self._update_oligo:
            strand5p.strandUpdateSignal.emit(strand5p)
            strand3p.strandUpdateSignal.emit(strand3p)
    # end def
# end class

class RemoveXoverCommand(UndoCommand):
    """
    Removes a Xover from the 3' end of strand5p to the 5' end of strand3p
    this needs to
    1. preserve the old oligo of strand3p
    2. install the crossover
    3. update the oligo length
    4. apply the new strand3p oligo to the strand3p
    """
    def __init__(self, part, strand5p, strand3p):
        super(RemoveXoverCommand, self).__init__("remove xover")
        self._part = part
        self._strand5p = strand5p
        self._strand5p_idx = strand5p.idx3Prime()
        self._strand3p = strand3p
        self._strand3p_idx = strand3p.idx5Prime()
        n_o3p = self._new_oligo3p = strand3p.oligo().shallowCopy()

        color_list = prefs.STAP_COLORS
        n_o3p._setColor(random.choice(color_list))
        n_o3p._setLength(0, emit_signals=True)
        for strand in strand3p.generator3pStrand():
            n_o3p._incrementLength(strand.totalLength(), emit_signals=True)
        # end def
        n_o3p.setStrand5p(strand3p)

        self._isLoop = strand3p.oligo().isLoop()
    # end def

    def redo(self):
        part = self._part
        strand5p = self._strand5p
        strand5p_idx = self._strand5p_idx
        strand3p = self._strand3p
        strand3p_idx = self._strand3p_idx
        new_olg3p = self._new_oligo3p
        olg5p = self._strand5p.oligo()

        fSetOligo = Strand.setOligo

        # 0. Deselect the involved strands
        doc = strand5p.document()
        doc.removeStrandFromSelection(strand5p)
        doc.removeStrandFromSelection(strand3p)

        # 1. uninstall the Xover
        strand5p.setConnection3p(None)
        strand3p.setConnection5p(None)

        if self._isLoop:
            olg5p._setLoop(False)
            olg5p.setStrand5p(strand3p)
        else:
            # 2. restore the modified oligo length
            olg5p._decrementLength(new_olg3p.length(), emit_signals=True)
            # 3. apply the old oligo to strand3p
            new_olg3p.addToPart(part, emit_signals=True)
            for strand in strand3p.generator3pStrand():
                # emits strandHasNewOligoSignal
                fSetOligo(strand, new_olg3p, emit_signals=True)

        strand5p.strandUpdateSignal.emit(strand5p)
        strand3p.strandUpdateSignal.emit(strand3p)
    # end def

    def undo(self):
        part = self._part
        strand5p = self._strand5p
        strand5p_idx = self._strand5p_idx
        strand3p = self._strand3p
        strand3p_idx = self._strand3p_idx
        olg5p = strand5p.oligo()
        new_olg3p = self._new_oligo3p

        fSetOligo = Strand.setOligo

        # 0. Deselect the involved strands
        doc = strand5p.document()
        doc.removeStrandFromSelection(strand5p)
        doc.removeStrandFromSelection(strand3p)

        if self._isLoop:
            olg5p._setLoop(True)
            # No need to restore whatever the old Oligo._strand5p was
        else:
            # 1. update preserved oligo length
            olg5p._incrementLength(new_olg3p.length(), emit_signals=True)
            # 2. Remove the old oligo and apply the 5' oligo to the 3' strand
            new_olg3p.removeFromPart(emit_signals=True)
            for strand in strand3p.generator3pStrand():
                # emits strandHasNewOligoSignal
                fSetOligo(strand, olg5p, emit_signals=True)
        # end else

        # 3. install the Xover
        strand5p.setConnection3p(strand3p)
        strand3p.setConnection5p(strand5p)

        strand5p.strandUpdateSignal.emit(strand5p)
        strand3p.strandUpdateSignal.emit(strand3p)
    # end def
# end class
