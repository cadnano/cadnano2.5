#!/usr/bin/env python
# encoding: utf-8
import sys, traceback
OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 18
OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT = 50

import copy

from cadnano import util
from cadnano.cnproxy import ProxySignal, UndoCommand
from cadnano.cnobject import CNObject
from cadnano.strand import Strand
from .applycolorcmd import ApplyColorCommand
from .applysequencecmd import ApplySequenceCommand
from .removeoligocmd import RemoveOligoCommand

PROPERTY_KEYS = ['name', 'color', 'length']
ALL_KEYS = ['id_num', 'idx5p', 'is_loop'] + PROPERTY_KEYS

class Oligo(CNObject):
    """
    Oligo is a group of Strands that are connected via 5' and/or 3'
    connections. It corresponds to the physical DNA strand, and is thus
    used tracking and storing properties that are common to a single strand,
    such as its color.

    Commands that affect Strands (e.g. create, remove, merge, split) are also
    responsible for updating the affected Oligos.
    """
    editable_properties = ['name', 'color']

    def __init__(self, part, color=None):
        super(Oligo, self).__init__(part)
        self._part = part
        self._strand5p = None
        # self._length = 0
        self._is_loop = False
        self._props = {}
        self._props['name'] = "oligo%s" % str(id(self))[-4:]
        self._props['color'] =  "#cc0000" if color is None else color
        self._props['length'] = 0
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        olg_id = str(id(self))[-4:]
        if self._strand5p is not None:
            vh_num = self._strand5p.idNum()
            idx = self._strand5p.idx5Prime()
        else:
            vh_num = -1
            idx = -1
        return "<%s %s>(%d[%d])" % (cls_name, olg_id, vh_num, idx)

    def shallowCopy(self):
        olg = Oligo(self._part)
        olg._strand5p = self._strand5p
        olg._is_loop = self._is_loop
        olg._props = self._props.copy()
        # print(">>>>checking color")
        # self.getColor()
        # olg.getColor()
        return olg
    # end def

    def dump(self):
        """ Return tuple of this oligo and its properties.
        It's expected that caller will copy the properties
        if mutating
        """
        s5p = self._strand5p
        # key = [s5p.idNum(), s5p.idx5Prime(), self._is_loop]
        # props = self._props
        # return key + [props[k] for k in PROPERTY_KEYS]
        key = { 'id_num': s5p.idNum(),
                'idx5p':s5p.idx5Prime(),
                'is_loop': self._is_loop}
        key.update(self._props)
        return key
    # end def

    # def copyProperties(self):
    #     return self._props()
    # # end

    # def deepCopy(self, part):
    #     """ not sure this actually gets called anywhere
    #     """
    #     olg = Oligo(part)
    #     olg._strand5p = None
    #     olg._is_loop = self._is_loop
    #     # do we copy length?
    #     olg._props = self._props.copy()
    #     return olg
    # # end def

    ### SIGNALS ###
    oligoIdentityChangedSignal = ProxySignal(CNObject,
                                        name='oligoIdentityChangedSignal')  # new oligo
    oligoAppearanceChangedSignal = ProxySignal(CNObject,
                                        name='oligoAppearanceChangedSignalpyqtSignal')  # self
    oligoRemovedSignal = ProxySignal(CNObject, CNObject,
                                        name='oligoRemovedSignal')  # part, self
    oligoSequenceAddedSignal = ProxySignal(CNObject,
                                        name='oligoSequenceAddedSignal')  # self
    oligoSequenceClearedSignal = ProxySignal(CNObject,
                                        name='oligoSequenceClearedSignal')  # self
    oligoPropertyChangedSignal = ProxySignal(CNObject, object, object,
                                        name='oligoPropertyChangedSignal')  # self, property_name, new_value

    ### SLOTS ###

    ### ACCESSORS ###
    def getProperty(self, key):
        return self._props[key]
    # end def

    def getPropertyDict(self):
        return self._props
    # end def

    def setProperty(self, key, value):
        # use ModifyPropertyCommand here
        self._props[key] = value
        if key == 'color':
            self.oligoAppearanceChangedSignal.emit(self)
        self.oligoPropertyChangedSignal.emit(self, key, value)
    # end def

    def getName(self):
        return self._props['name']
    # end def

    def getColor(self):
        color = self._props['color']
        try:
            if color is None:
                print(self._props)
                raise ValueError("Whhat Got None???")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
            traceback.print_stack()
            sys.exit(0)
        return color
    # end def

    def setColor(self, color):
        if color is None:
            raise ValueError("Whhat None???")
        self._props['color'] = color
    # end def

    def setLength(self, length):
        before = self.shouldHighlight()
        # self._length = length
        self.setProperty('length', length)
        if before != self.shouldHighlight():
            self.oligoSequenceClearedSignal.emit(self)
            self.oligoAppearanceChangedSignal.emit(self)
    # end def

    def locString(self):
        vh_num = self._strand5p.idNum()
        idx = self._strand5p.idx5Prime()
        return "%d[%d]" % (vh_num, idx)
    # end def

    def part(self):
        return self._part
    # end def

    def strand5p(self):
        return self._strand5p
    # end def

    def strand3p(self):
        s5p = self._strand5p
        if self._is_loop:
            return s5p._strand5p
        for strand in s5p.generator3pStrand():
            pass
        return strand
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
    # end def

    # def isStaple(self):
    #     if self._strand5p is not None:
    #         return self._strand5p.isStaple()
    #     else:
    #         return False
    # # end def

    def length(self):
        # return self._length
        return self._props['length']
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
        vh_num5p = self.strand5p().idNum()
        strand5p = self.strand5p()
        idx5p = strand5p.idx5Prime()
        seq = ''
        if self.isLoop():
            # print("A loop exists")
            raise Exception
        for strand in strand5p.generator3pStrand():
            seq = seq + Strand.sequence(strand, for_export=True)
            if strand.connection3p() is None:  # last strand in the oligo
                vh_num3p = strand.idNum()
                idx3p = strand.idx3Prime()
        modseq5p, modseq5p_name = part.getModSequence(strand5p, idx5p, 0)
        modseq3p, modseq3p_name = part.getModSequence(strand, idx3p, 1)
        seq = modseq5p + seq + modseq3p
        output = "%d[%d],%d[%d],%s,%s,%s,%s,%s\n" % \
                (vh_num5p, idx5p, vh_num3p, idx3p, seq, len(seq),
                    self.getColor(), modseq5p_name, modseq3p_name)
        return output
    # end def

    def shouldHighlight(self):
        if not self._strand5p:
            return False
        # if self._strand5p.isScaffold():
        #     return False
        if self.length() < OLIGO_LEN_BELOW_WHICH_HIGHLIGHT:
            return True
        if self.length() > OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT:
            return True
        return False
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def remove(self, use_undostack=True):
        c = RemoveOligoCommand(self)
        util.execCommandList(self, [c], desc="Remove Oligo", use_undostack=use_undostack)
        self.oligoRemovedSignal.emit(self._part, self)
    # end def

    def applyColor(self, color, use_undostack=True):
        if color == self.getColor():
            return  # oligo already has this color
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
    # end def

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
        self.setLength(self.length() - delta)
    # end def

    def incrementLength(self, delta):
        self.setLength(self.length() + delta)
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
        if old_strand_low.isForward():
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
            if old_merged_strand.connection5p() is None:
                self._strand5p = new_strand5p
            else:
                self._strand5p = old_merged_strand.oligo()._strand5p
            oligo3p._strand5p = new_strand3p
        # end else
    # end def

# end class
