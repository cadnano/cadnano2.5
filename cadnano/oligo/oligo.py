#!/usr/bin/env python
# encoding: utf-8

import copy

import cadnano.util as util
from cadnano.strand import Strand
from cadnano.cnproxy import ProxyObject, ProxySignal, UndoCommand

from .applycolorcmd import ApplyColorCommand
from .applysequencecmd import ApplySequenceCommand
from .removeoligocmd import RemoveOligoCommand

class Oligo(ProxyObject):
    """
    Oligo is a group of Strands that are connected via 5' and/or 3'
    connections. It corresponds to the physical DNA strand, and is thus
    used tracking and storing properties that are common to a single strand,
    such as its color.

    Commands that affect Strands (e.g. create, remove, merge, split) are also
    responsible for updating the affected Oligos.
    """
    def __init__(self, part, color=None):
        # self.__class__.__base__.__init__(self, part)
        super(Oligo, self).__init__(part)
        self._part = part
        self._strand5p = None
        self._length = 0
        self._is_loop = False
        self._color = color if color else "#0066cc"
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        olg_id = str(id(self))[-4:]
        if self._strand5p is not None:
            strand_type = "Stap" if self.isStaple() else "Scaf"
            vh_num = self._strand5p.strandSet().virtualHelix().number()
            idx = self._strand5p.idx5Prime()
        else:
            strand_type = "None"
            vh_num = -1
            idx = -1
        return "<%s %s>(%s %d[%d])" % (cls_name, olg_id, strand_type, vh_num, idx)

    def shallowCopy(self):
        olg = Oligo(self._part)
        olg._strand5p = self._strand5p
        olg._length = self._length
        olg._is_loop = self._is_loop
        olg._color = self._color
        return olg
    # end def

    def deepCopy(self, part):
        olg = Oligo(part)
        olg._strand5p = None
        olg._length = self._length
        olg._is_loop = self._is_loop
        olg._color = self._color
        return olg
    # end def

    ### SIGNALS ###
    oligoIdentityChangedSignal = ProxySignal(ProxyObject, name='oligoIdentityChangedSignal') # new oligo
    oligoAppearanceChangedSignal = ProxySignal(ProxyObject, name='oligoAppearanceChangedSignalpyqtSignal')  # self
    oligoSequenceAddedSignal = ProxySignal(ProxyObject, name='oligoSequenceAddedSignal') # self
    oligoSequenceClearedSignal = ProxySignal(ProxyObject, name='oligoSequenceClearedSignal')  # self

    ### SLOTS ###

    ### ACCESSORS ###
    def color(self):
        return self._color
    # end def

    def locString(self):
        vh_num = self._strand5p.strandSet().virtualHelix().number()
        idx = self._strand5p.idx5Prime()
        return "%d[%d]" % (vh_num, idx)
    # end def

    def part(self):
        return self._part
    # end def

    def strand5p(self):
        return self._strand5p
    # end def

    def setStrand5p(self, strand):
        self._strand5p = strand
    # end def

    def undoStack(self):
        return self._part.undoStack()
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isLoop(self):
        return self._is_loop

    def isStaple(self):
        if self._strand5p is not None:
            return self._strand5p.isStaple()
        else:
            return False

    def length(self):
        return self._length
    # end def

    def sequence(self):
        temp = self.strand5p()
        if not temp:
            return None
        if temp.sequence():
            return ''.join([Strand.sequence(strand) \
                        for strand in self.strand5p().generator3pStrand()])
        else:
            return None
    # end def

    def sequenceExport(self):
        part = self.part()
        vh_num5p = self.strand5p().virtualHelix().number()
        strand5p = self.strand5p()
        idx5p = strand5p.idx5Prime()
        seq = ''
        if self.isLoop():
            # print("A loop exists")
            raise Exception
        for strand in strand5p.generator3pStrand():
            seq = seq + Strand.sequence(strand, for_export=True)
            if strand.connection3p() == None:  # last strand in the oligo
                vh_num3p = strand.virtualHelix().number()
                idx3p = strand.idx3Prime()
        modseq5p, modseq5p_name = part.getModSequence(strand5p, idx5p, 0)
        modseq3p, modseq3p_name = part.getModSequence(strand, idx3p, 1)
        seq = modseq5p + seq + modseq3p
        output = "%d[%d],%d[%d],%s,%s,%s,%s,%s\n" % \
                (vh_num5p, idx5p, vh_num3p, idx3p, seq, len(seq),
                    self._color, modseq5p_name, modseq3p_name)
        return output
    # end def

    def shouldHighlight(self):
        if not self._strand5p:
            return False
        if self._strand5p.isScaffold():
            return False
        if self.length() < 18:
            return True
        if self.length() > 50:
            return True
        return False
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def remove(self, use_undostack=True):
        c = RemoveOligoCommand(self)
        util.execCommandList(self, [c], desc="Color Oligo", use_undostack=use_undostack)
    # end def

    def applyColor(self, color, use_undostack=True):
        if color == self._color:
            return  # oligo already has color
        c = ApplyColorCommand(self, color)
        util.execCommandList(self, [c], desc="Color Oligo", use_undostack=use_undostack)
    # end def

    def applySequence(self, sequence, use_undostack=True):
        c = ApplySequenceCommand(self, sequence)
        util.execCommandList(self, [c], desc="Apply Sequence", use_undostack=use_undostack)
    # end def

    def applySequenceCMD(self, sequence, use_undostack=True):
        return ApplySequenceCommand(self, sequence)
    # end def

    def setLoop(self, bool):
        self._is_loop = bool

    ### PUBLIC SUPPORT METHODS ###
    def addToPart(self, part):
        self._part = part
        self.setParent(part)
        part.addOligo(self)
    # end def

    def destroy(self):
        # QObject also emits a destroyed() Signal
        self.setParent(None)
        self.deleteLater()
    # end def

    def decrementLength(self, delta):
        self.setLength(self._length-delta)
    # end def

    def incrementLength(self, delta):
        self.setLength(self._length+delta)
    # end def

    def refreshLength(self):
        temp = self.strand5p()
        if not temp:
            return
        length = 0
        for strand in temp.generator3pStrand():
            length += strand.totalLength()
        self.setLength(length)
    # end def

    def removeFromPart(self):
        """
        This method merely disconnects the object from the model.
        It still lives on in the undoStack until clobbered

        Note: don't set self._part = None because we need to continue passing
        the same reference around.
        """
        self._part.removeOligo(self)
        self.setParent(None)
    # end def

    def setColor(self, color):
        self._color = color
    # end def

    def setLength(self, length):
        before = self.shouldHighlight()
        self._length = length
        if before != self.shouldHighlight():
            self.oligoSequenceClearedSignal.emit(self)
            self.oligoAppearanceChangedSignal.emit(self)
    # end def

    def strandMergeUpdate(self, old_strand_low, old_strand_high, new_strand):
        """
        This method sets the isLoop status of the oligo and the oligo's
        5' strand.
        """
        # check loop status
        if old_strand_low.oligo() == old_strand_high.oligo():
            self._is_loop = True
            self._strand5p = new_strand
            return 
            # leave the _strand5p as is?
        # end if

        # Now get correct 5p end to oligo
        if old_strand_low.isDrawn5to3():
            if old_strand_low.connection5p() is not None:
                self._strand5p = old_strand_low.oligo()._strand5p
            else:
                self._strand5p = new_strand
        else:
            if old_strand_high.connection5p() is not None:
                self._strand5p = old_strand_high.oligo()._strand5p
            else:
                self._strand5p = new_strand
        # end if
    # end def

    def strandResized(self, delta):
        """
        Called by a strand after resize. Delta is used to update the length,
        which may case an appearance change.
        """
        pass
    # end def

    def strandSplitUpdate(self, new_strand5p, new_strand3p, oligo3p, old_merged_strand):
        """
        If the oligo is a loop, splitting the strand does nothing. If the
        oligo isn't a loop, a new oligo must be created and assigned to the
        new_strand and everything connected to it downstream.
        """
        # if you split it can't be a loop
        self._is_loop = False
        if old_merged_strand.oligo().isLoop():
            self._strand5p = new_strand3p
            return
        else:
            if old_merged_strand.connection5p() == None:
                self._strand5p = new_strand5p
            else:
                self._strand5p = old_merged_strand.oligo()._strand5p
            oligo3p._strand5p = new_strand3p
        # end else
    # end def

# end class
    