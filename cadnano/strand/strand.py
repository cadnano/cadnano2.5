#!/usr/bin/env python
# encoding: utf-8

from operator import attrgetter
from array import array
import sys
IS_PY_3 = int(sys.version_info[0] > 2)
if IS_PY_3:
    sixb = lambda x: x.encode('utf-8')
    array_type = 'B'
    tostring = lambda x: x.tostring().decode('utf-8')
else:
    sixb = lambda x: x
    array_type = 'c'
    tostring = lambda x: x.tostring()

import cadnano.util as util
from cadnano.decorators.insertion import Insertion

from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoCommand, UndoStack

from .insertioncmd import AddInsertionCommand, RemoveInsertionCommand
from .insertioncmd import ChangeInsertionCommand
from .modscmd import AddModsCommand, RemoveModsCommand
from .resizecmd import ResizeCommand

class Strand(ProxyObject):
    """
    A Strand is a continuous stretch of bases that are all in the same
    StrandSet (recall: a VirtualHelix is made up of two StrandSets).

    Every Strand has two endpoints. The naming convention for keeping track
    of these endpoints is based on the relative numeric value of those
    endpoints (low and high). Thus, Strand has a '_base_idx_low', which is its
    index with the lower numeric value (typically positioned on the left),
    and a '_base_idx_high' which is the higher-value index (typically positioned
    on the right)

    Strands can be linked to other strands by "connections". References to
    connected strands are named "_strand5p" and "_strand3p", which correspond
    to the 5' and 3' phosphate linkages in the physical DNA strand,
    respectively. Since Strands can point 5'-to-3' in either the low-to-high
    or high-to-low directions, connection accessor methods (connectionLow and
    connectionHigh) are bound during the init for convenience.
    """

    def __init__(self, strandset, base_idx_low, base_idx_high, oligo=None):
        self._doc = strandset.document()
        super(Strand, self).__init__(strandset)
        self._strandset = strandset
        self._base_idx_low = base_idx_low  # base index of the strand's left bound
        self._base_idx_high = base_idx_high  # base index of the right bound
        self._oligo = oligo
        self._strand5p = None  # 5' connection to another strand
        self._strand3p = None  # 3' connection to another strand
        self._sequence = None

        self._decorators = {}
        self._modifiers = {}

        # dynamic methods for mapping high/low connection /indices
        # to corresponding 3Prime 5Prime
        is_drawn_5_to_3 = strandset.isDrawn5to3()
        if is_drawn_5_to_3:
            self.idx5Prime = self.lowIdx
            self.idx3Prime = self.highIdx
            self.connectionLow = self.connection5p
            self.connectionHigh = self.connection3p
            self.setConnectionLow = self.setConnection5p
            self.setConnectionHigh = self.setConnection3p
        else:
            self.idx5Prime = self.highIdx
            self.idx3Prime = self.lowIdx
            self.connectionLow = self.connection3p
            self.connectionHigh = self.connection5p
            self.setConnectionLow = self.setConnection3p
            self.setConnectionHigh = self.setConnection5p
        self._is_drawn_5_to_3 = is_drawn_5_to_3
    # end def

    def __repr__(self):
        clsName = self.__class__.__name__
        s = "%s.<%s(%s, %s)>" % (self._strandset.__repr__(),
                                clsName,
                                self._base_idx_low,
                                self._base_idx_high)
        return s

    def generator5pStrand(self):
        """
        Iterate from self to the final _strand5p == None
        3prime to 5prime
        Includes originalCount to check for circular linked list
        """
        originalCount = 0
        node0 = node = self
        f = attrgetter('_strand5p')
        # while node and originalCount == 0:
        #     yield node  # equivalent to: node = node._strand5p
        #     node = f(node)
        #     if node0 == self:
        #         originalCount += 1
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break

    # end def

    def generator3pStrand(self):
        """
        Iterate from self to the final _strand3p == None
        5prime to 3prime
        Includes originalCount to check for circular linked list
        """
        originalCount = 0
        node0 = node = self
        f = attrgetter('_strand3p')
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break
    # end def

    def strandFilter(self):
        return self._strandset.strandFilter()

    ### SIGNALS ###
    strandHasNewOligoSignal = ProxySignal(ProxyObject, name='strandHasNewOligoSignal') #pyqtSignal(QObject)  # strand
    strandRemovedSignal = ProxySignal(ProxyObject, name='strandRemovedSignal') #pyqtSignal(QObject)  # strand
    strandResizedSignal = ProxySignal(ProxyObject, tuple, name='strandResizedSignal') #pyqtSignal(QObject, tuple)

    # Parameters: (strand3p, strand5p)
    strandXover5pChangedSignal = ProxySignal(ProxyObject, ProxyObject, name='strandXover5pChangedSignal') #pyqtSignal(QObject, QObject)
    strandXover5pRemovedSignal = ProxySignal(ProxyObject, ProxyObject, name='strandXover5pRemovedSignal') #pyqtSignal(QObject, QObject)

    # Parameters: (strand)
    strandUpdateSignal = ProxySignal(ProxyObject, name='strandUpdateSignal') #pyqtSignal(QObject)

    # Parameters: (strand, insertion object)
    strandInsertionAddedSignal = ProxySignal(ProxyObject, object, name='strandInsertionAddedSignal') #pyqtSignal(QObject, object)
    strandInsertionChangedSignal = ProxySignal(ProxyObject, object, name='strandInsertionChangedSignal') #pyqtSignal(QObject, object)
    # Parameters: (strand, insertion index)
    strandInsertionRemovedSignal = ProxySignal(ProxyObject, int, name='strandInsertionRemovedSignal') #pyqtSignal(QObject, int)

    # Parameters: (strand, decorator object)
    strandModsAddedSignal = ProxySignal(ProxyObject, object, int, name='strandModsAddedSignal') #pyqtSignal(QObject, object)
    strandModsChangedSignal = ProxySignal(ProxyObject, object, int, name='strandModsChangedSignal') #pyqtSignal(QObject, object)
    # Parameters: (strand, decorator index)
    strandModsRemovedSignal = ProxySignal(ProxyObject, object, int, name='strandModsRemovedSignal') #pyqtSignal(QObject, int)

    # Parameters: (strand, modifier object)
    strandModifierAddedSignal = ProxySignal(ProxyObject, object, name='strandModifierAddedSignal') #pyqtSignal(QObject, object)
    strandModifierChangedSignal = ProxySignal(ProxyObject, object, name='strandModifierChangedSignal') #pyqtSignal(QObject, object)
    # Parameters: (strand, modifier index)
    strandModifierRemovedSignal = ProxySignal(ProxyObject, int, name='strandModifierRemovedSignal') #pyqtSignal(QObject, int)

    # Parameters: (strand, value)
    selectedChangedSignal = ProxySignal(ProxyObject, tuple, name='selectedChangedSignal') #pyqtSignal(QObject, tuple)

    ### SLOTS ###
    ### ACCESSORS ###
    def undoStack(self):
        return self._strandset.undoStack()

    def decorators(self):
        return self._decorators
    # end def

    def isStaple(self):
        return self._strandset.isStaple()

    def isScaffold(self):
        return self._strandset.isScaffold()

    def part(self):
        return self._strandset.part()
    # end def

    def document(self):
        return self._doc
    # end def

    def oligo(self):
        return self._oligo
    # end def

    def sequence(self, for_export=False):
        seq = self._sequence
        if seq:
            return util.markwhite(seq) if for_export else seq
        elif for_export:
            return ''.join(['?' for x in range(self.totalLength())])
        return ''
    # end def

    def strandSet(self):
        return self._strandset
    # end def

    def strandType(self):
        return self._strandset.strandType()

    def virtualHelix(self):
        return self._strandset.virtualHelix()
    # end def

    def setSequence(self, sequence_string):
        """
        Applies sequence string from 5' to 3'
        return the tuple (used, unused) portion of the sequence_string
        """
        if sequence_string == None:
            self._sequence = None
            return None, None
        length = self.totalLength()
        if len(sequence_string) < length:
            bonus = length - len(sequence_string)
            sequence_string += ''.join([' ' for x in range(bonus)])
        temp = sequence_string[0:length]
        self._sequence = temp
        return temp, sequence_string[length:]
    # end def

    def reapplySequence(self):
        """
        """
        comp_ss = self.strandSet().complementStrandSet()
        
        # the strand sequence will need to be regenerated from scratch
        # as there are no guarantees about the entirety of the strand moving
        # i.e. both endpoints thanks to multiple selections so just redo the 
        # whole thing
        self._sequence = None
        
        for comp_strand in comp_ss._findOverlappingRanges(self):
            compSeq = comp_strand.sequence()
            usedSeq = util.comp(compSeq) if compSeq else None
            usedSeq = self.setComplementSequence(
                                        usedSeq, comp_strand)
        # end for
    # end def
    
    def getComplementStrands(self):
        """
        return the list of complement strands that overlap with this strand
        """
        comp_ss = self.strandSet().complementStrandSet()
        return [comp_strand for comp_strand in comp_ss._findOverlappingRanges(self)]
    # end def 

    def getPreDecoratorIdxList(self):
        """
        Return positions where predecorators should be displayed. This is
        just a very simple check for the presence of xovers on the strand.

        Will refine later by checking for lattice neighbors in 3D.
        """
        return range(self._base_idx_low, self._base_idx_high + 1)
    # end def

    # def getPreDecoratorIdxList(self):
    #     """Return positions where predecorators should be displayed."""
    #     part = self._strandset.part()
    #     validIdxs = sorted([idx[0] for idx in part._stapL + part._stapH])
    #     lo, hi = self._base_idx_low, self._base_idx_high
    #     start = lo if self.connectionLow() == None else lo+1
    #     end = hi if self.connectionHigh() == None else hi-1
    #     ret = []
    #     for i in range(start, end+1):
    #         if i % part.stepSize() in validIdxs:
    #             ret.append(i)
    #     return ret
    # # end def

    def setComplementSequence(self, sequence_string, strand):
        """
        This version takes anothers strand and only sets the indices that
        align with the given complimentary strand

        return the used portion of the sequence_string

        As it depends which direction this is going, and strings are stored in
        memory left to right, we need to test for is_drawn_5_to_3 to map the
        reverse compliment appropriately, as we traverse overlapping strands.

        We reverse the sequence ahead of time if we are applying it 5' to 3',
        otherwise we reverse the sequence post parsing if it's 3' to 5'

        Again, sequences are stored as strings in memory 5' to 3' so we need
        to jump through these hoops to iterate 5' to 3' through them correctly

        Perhaps it's wiser to merely store them left to right and reverse them
        at draw time, or export time
        """
        s_low_idx, s_high_idx = self._base_idx_low, self._base_idx_high
        c_low_idx, c_high_idx = strand.idxs()

        # get the ovelap
        low_idx, high_idx = util.overlap(s_low_idx, s_high_idx, c_low_idx, c_high_idx)

        # only get the characters we're using, while we're at it, make it the
        # reverse compliment

        total_length = self.totalLength()

        # see if we are applying
        if sequence_string == None:
            # clear out string for in case of not total overlap
            use_seq = ''.join([' ' for x in range(total_length)])
        else:  # use the string as is
            use_seq = sequence_string[::-1] if self._is_drawn_5_to_3 \
                                            else sequence_string

        temp = array(array_type, sixb(use_seq))
        if self._sequence == None:
            temp_self = array(array_type, sixb(''.join([' ' for x in range(total_length)])))
        else:
            temp_self = array(array_type, sixb(self._sequence) if self._is_drawn_5_to_3 \
                                                    else sixb(self._sequence[::-1]))

        # generate the index into the compliment string
        a = self.insertionLengthBetweenIdxs(s_low_idx, low_idx - 1)
        b = self.insertionLengthBetweenIdxs(low_idx, high_idx)
        c = strand.insertionLengthBetweenIdxs(c_low_idx, low_idx - 1)
        start = low_idx - c_low_idx + c
        end = start + b + high_idx - low_idx + 1
        temp_self[low_idx - s_low_idx + a:high_idx - s_low_idx + 1 + a + b] = \
                                                                temp[start:end]
        # print "old sequence", self._sequence
        self._sequence = tostring(temp_self)
        
        # if we need to reverse it do it now
        if not self._is_drawn_5_to_3:
            self._sequence = self._sequence[::-1]

        # test to see if the string is empty(), annoyingly expensive
        if len(self._sequence.strip()) == 0:
            self._sequence = None
            
        # print "new sequence", self._sequence
        return self._sequence
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def connection3p(self):
        return self._strand3p
    # end def

    def connection5p(self):
        return self._strand5p
    # end def

    def idxs(self):
        return (self._base_idx_low, self._base_idx_high)
    # end def

    def lowIdx(self):
        return self._base_idx_low
    # end def

    def highIdx(self):
        return self._base_idx_high
    # end def

    def idx3Prime(self):
        """Returns the absolute base_idx of the 3' end of the strand.
        overloaded in __init__
        """
        pass
        # return self.idx3Prime

    def idx5Prime(self):
        """Returns the absolute base_idx of the 5' end of the strand.
        overloaded in __init__
        """
        pass
        # return self.idx5Prime

    def isDrawn5to3(self):
        return self._strandset.isDrawn5to3()
    # end def

    def getSequenceList(self):
        """
        return the list of sequences strings comprising the sequence and the
        inserts as a tuple with the index of the insertion
        [(idx, (strandItemString, insertionItemString), ...]

        This takes advantage of the fact the python iterates a dictionary
        by keys in order so if keys are indices, the insertions will iterate
        out from low index to high index
        """
        seqList = []
        is_drawn_5_to_3 = self._is_drawn_5_to_3
        seq = self._sequence if is_drawn_5_to_3 else self._sequence[::-1]
        # assumes a sequence has been applied correctly and is up to date
        tL = self.totalLength()

        offsetLast = 0
        lengthSoFar = 0
        iLength = 0
        lI, hI = self.idxs()

        for insertion in self.insertionsOnStrand():
            iLength = insertion.length()
            index = insertion.idx()
            offset = index + 1 - lI + lengthSoFar
            if iLength < 0:
                offset -= 1
            # end if
            lengthSoFar += iLength
            seqItem = seq[offsetLast:offset]  # the stranditem seq

            # Because skips literally skip displaying a character at a base
            # position, this needs to be accounted for seperately
            if iLength < 0:
                seqItem += ' '
                offsetLast = offset
            else:
                offsetLast = offset + iLength
            seqInsertion = seq[offset:offsetLast]  # the insertions sequence
            seqList.append((index, (seqItem, seqInsertion)))
        # end for
        # append the last bit of the strand
        seqList.append((lI + tL, (seq[offsetLast:tL], '')))
        if not is_drawn_5_to_3:
            # reverse it again so all sub sequences are from 5' to 3'
            for i in range(len(seqList)):
                index, temp = seqList[i]
                seqList[i] = (index, (temp[0][::-1], temp[1][::-1]))
        return seqList
    # end def

    def canResizeTo(self, newLow, newHigh):
        """
        Checks to see if a resize is allowed. Similar to getResizeBounds
        but works for two bounds at once.
        """
        lowNeighbor, highNeighbor = self._strandset.getNeighbors(self)
        lowBound = lowNeighbor.highIdx() if lowNeighbor \
                                            else self.part().minBaseIdx()
        highBound = highNeighbor.lowIdx() if highNeighbor \
                                            else self.part().maxBaseIdx()

        if newLow > lowBound and newHigh < highBound:
            return True
        return False

    def getResizeBounds(self, idx):
        """
        Determines (inclusive) low and high drag boundaries resizing
        from an endpoint located at idx.

        When resizing from _base_idx_low:
            low bound is determined by checking for lower neighbor strands.
            high bound is the index of this strand's high cap, minus 1.

        When resizing from _base_idx_high:
            low bound is the index of this strand's low cap, plus 1.
            high bound is determined by checking for higher neighbor strands.

        When a neighbor is not present, just use the Part boundary.
        """
        neighbors = self._strandset.getNeighbors(self)
        if idx == self._base_idx_low:
            if neighbors[0]:
                low = neighbors[0].highIdx() + 1
            else:
                low = self.part().minBaseIdx()
            return low, self._base_idx_high - 1
        else:  # self._base_idx_high
            if neighbors[1]:
                high = neighbors[1].lowIdx() - 1
            else:
                high = self.part().maxBaseIdx()
            return self._base_idx_low + 1, high
    # end def

    def hasXoverAt(self, idx):
        """
        An xover is necessarily at an enpoint of a strand
        """
        if idx == self.highIdx():
            return True if self.connectionHigh() is not None else False
        elif idx == self.lowIdx():
            return True if self.connectionLow() is not None else False
        else:
            return False
    # end def

    def canInstallXoverAt(self, idx, from_strand, from_idx):
        """
        Assumes idx is:
        self.lowIdx() <= idx <= self.highIdx()
        """

        if self.hasXoverAt(idx):
            return False
        sS = self.strandSet()
        is_same_strand = from_strand == self
        is_strand_type_match = \
                from_strand.strandSet().strandType() == sS.strandType() \
                                                if from_strand else True
        if not is_strand_type_match:
            return False
        is_drawn_5_to_3 = sS.isDrawn5to3()
        indexDiffH = self.highIdx() - idx
        indexDiffL = idx - self.lowIdx()
        index3Lim = self.idx3Prime() - 1 if is_drawn_5_to_3 \
                                            else self.idx3Prime() + 1
        if is_same_strand:
            indexDiffStrands = from_idx - idx
            if idx == self.idx5Prime() or idx == index3Lim:
                return True
            elif indexDiffStrands > -3 and indexDiffStrands < 3:
                return False
        # end if for same Strand
        if idx == self.idx5Prime() or idx == index3Lim:
            return True
        elif indexDiffH > 2 and indexDiffL > 1:
            return True
        else:
            return False
    #end def

    def insertionLengthBetweenIdxs(self, idxL, idxH):
        """
        includes the length of insertions in addition to the bases
        """
        tL = 0
        insertions = self.insertionsOnStrand(idxL, idxH)
        for insertion in insertions:
            tL += insertion.length()
        return tL
    # end def

    def insertionsOnStrand(self, idxL=None, idxH=None):
        """
        if passed indices it will use those as a bounds
        """
        insertions = []
        coord = self.virtualHelix().coord()
        insertionsDict = self.part().insertions()[coord]
        sortedIndices = sorted(insertionsDict.keys())
        if idxL == None:
            idxL, idxH = self.idxs()
        for index in sortedIndices:
            insertion = insertionsDict[index]
            if idxL <= insertion.idx() <= idxH:
                insertions.append(insertion)
            # end if
        # end for
        return insertions
    # end def

    def modifersOnStrand(self):
        """
        """
        mods = []
        modsDict = self.part().mods()['ext_instances']
        coord = self.virtualHelix().coord()
        isstaple = self.isStaple()
        idxL, idxH = self.idxs()
        keyL =  "{},{},{}".format(coord, isstaple, idxL)
        keyH =  "{},{},{}".format(coord, isstaple, idxH)
        if keyL in modsDict:
            mods.append(modsDict[keyL])
        if keyH in modsDict:
            mods.append(modsDict[keyH])
        return mods
    # end def

    def length(self):
        return self._base_idx_high - self._base_idx_low + 1
    # end def

    def totalLength(self):
        """
        includes the length of insertions in addition to the bases
        """
        tL = 0
        insertions = self.insertionsOnStrand()

        for insertion in insertions:
            tL += insertion.length()
        return tL + self.length()
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addDecorators(self, additionalDecorators):
        """Used to add decorators during a merge operation."""
        self._decorators.update(additionalDecorators)
    # end def

    def addMods(self, mod_id, idx, use_undostack=True):
        """Used to add mods during a merge operation."""
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low == idx or idx == idx_high:
            check_mid1 = self.part().getModID(self, idx)
            check_mid2 = self.part().getMod(mod_id)
            if check_mid2 is not None:
                if check_mid1 != mod_id:
                    if check_mid1 is not None:
                        cmds.append(RemoveModsCommand(self, idx, check_mid1))
                    # print("adding a {} modification at {}".format(mod_id, idx))
                    cmds.append(AddModsCommand(self, idx, mod_id))
                    util.execCommandList(
                                        self, cmds, desc="Add Modification",
                                            use_undostack=use_undostack)
                else:
                    print(check_mid, mod_id)
        # end if
    # end def

    def removeMods(self, mod_id, idx, use_undostack=True):
        """Used to add mods during a merge operation."""
        cmds = []
        idx_low, idx_high = self.idxs()
        print("attempting to remove")
        if idx_low == idx or idx == idx_high:
            print("removing a modification at {}".format(idx))
            cmds.append(RemoveModsCommand(self, idx, mod_id))
            util.execCommandList(
                                self, cmds, desc="Remove Modification",
                                    use_undostack=use_undostack)
        # end if
    # end def

    def addInsertion(self, idx, length, use_undostack=True):
        """
        Adds an insertion or skip at idx.
        length should be
            >0 for an insertion
            -1 for a skip
        """
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low <= idx <= idx_high:
            if not self.hasInsertionAt(idx):
                # make sure length is -1 if a skip
                if length < 0:
                    length = -1
                if use_undostack:   # on import no need to blank sequences
                    cmds.append(self.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                cmds.append(AddInsertionCommand(self, idx, length))
                util.execCommandList(
                                    self, cmds, desc="Add Insertion",
                                    use_undostack=use_undostack)
            # end if
        # end if
    # end def

    def changeInsertion(self, idx, length, use_undostack=True):
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low <= idx <= idx_high:
            if self.hasInsertionAt(idx):
                if length == 0:
                    self.removeInsertion(idx)
                else:
                    # make sure length is -1 if a skip
                    if length < 0:
                        length = -1
                    cmds.append(self.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                    cmds.append(
                            ChangeInsertionCommand(self, idx, length))
                    util.execCommandList(
                                        self, cmds, desc="Change Insertion",
                                        use_undostack=use_undostack)
            # end if
        # end if
    # end def
    
    def removeInsertion(self,  idx, use_undostack=True):
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low <= idx <= idx_high:
            if self.hasInsertionAt(idx):
                if use_undostack:
                    cmds.append(self.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None, use_undostack=use_undostack))
                cmds.append(RemoveInsertionCommand(self, idx))
                util.execCommandList(
                                    self, cmds, desc="Remove Insertion",
                                    use_undostack=use_undostack)
            # end if
        # end if
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def

    def merge(self, idx):
        """Check for neighbor, then merge if possible."""
        lowNeighbor, highNeighbor = self._strandset.getNeighbors(self)
        # determine where to check for neighboring endpoint
        if idx == self._base_idx_low:
            if lowNeighbor:
                if lowNeighbor.highIdx() == idx - 1:
                    self._strandset.mergeStrands(self, lowNeighbor)
        elif idx == self._base_idx_high:
            if highNeighbor:
                if highNeighbor.lowIdx() == idx + 1:
                    self._strandset.mergeStrands(self, highNeighbor)
        else:
            raise IndexError
    # end def

    def resize(self, new_idxs, use_undostack=True):
        cmds = []
        if self.strandSet().isScaffold():
            cmds.append(self.oligo().applySequenceCMD(None))
        cmds += self.getRemoveInsertionCommands(new_idxs)
        cmds.append(ResizeCommand(self, new_idxs))
        util.execCommandList(
                            self, cmds, desc="Resize strand",
                            use_undostack=use_undostack)
    # end def

    def setConnection3p(self, strand):
        self._strand3p = strand
    # end def

    def setConnection5p(self, strand):
        self._strand5p = strand
    # end def

    def setIdxs(self, idxs):
        self._base_idx_low = idxs[0]
        self._base_idx_high = idxs[1]
    # end def

    def setOligo(self, new_oligo, emit_signal=True):
        self._oligo = new_oligo
        if emit_signal:
            self.strandHasNewOligoSignal.emit(self)
    # end def

    def setStrandSet(self, strandset):
        self._strandset = strandset
    # end def

    def split(self, idx, update_sequence=True):
        """Called by view items to split this strand at idx."""
        self._strandset.splitStrand(self, idx, update_sequence)

    def updateIdxs(self, delta):
        self._base_idx_low += delta
        self._base_idx_high += delta
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def getRemoveInsertionCommands(self, new_idxs):
        """
        Removes Insertions, Decorators, and Modifiers that have fallen out of
        range of new_idxs.

        For insertions, it finds the ones that have neither Staple nor Scaffold
        strands at the insertion idx as a result of the change of this
        strand to new_idxs

        """
        decs = self._decorators
        mods = self._modifiers
        cIdxL, cIdxH = self.idxs()
        nIdxL, nIdxH = new_idxs

        low_out, high_out = False, False
        insertions = []
        if cIdxL < nIdxL < cIdxH:
            idxL, idxH = cIdxL, nIdxL - 1
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            low_out = True
        if cIdxL < nIdxH < cIdxH:
            idxL, idxH = nIdxH + 1, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            high_out = True
        # this only called if both the above aren't true
        # if low_out and high_out:
        # if we move the whole strand, just clear the insertions out
        if nIdxL > cIdxH or nIdxH < cIdxL:
            idxL, idxH = cIdxL, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
            # we stretched in this direction

        return self.clearInsertionsCommands(insertions, cIdxL, cIdxH)
    # end def

    def clearInsertionsCommands(self, insertions, idxL, idxH):
        """
        clear out insertions in this range
        """
        commands = []
        comp_ss = self.strandSet().complementStrandSet()

        overlappingStrandList = comp_ss.getOverlappingStrands(idxL, idxH)
        for insertion in insertions:
            idx = insertion.idx()
            removeMe = True
            for strand in overlappingStrandList:
                overLapIdxL, overLapIdxH = strand.idxs()
                if overLapIdxL <= idx <= overLapIdxH:
                    removeMe = False
                # end if
            # end for
            if removeMe:
                commands.append(RemoveInsertionCommand(self, idx))
            else:
                pass
                # print "keeping %s insertion at %d" % (self, key)
        # end for

        ### ADD CODE HERE TO HANDLE DECORATORS AND MODIFIERS
        return commands
    # end def

    def clearDecoratorCommands(self):
        insertions = self.insertionsOnStrand()
        return self.clearInsertionsCommands(insertions, *self.idxs())
    # end def

    def hasDecoratorAt(self, idx):
        return idx in self._decorators
    # end def

    def hasInsertion(self):
        """
        Iterate through dict of insertions for this strand's virtualhelix
        and return True of any of the indices overlap with the strand.
        """
        coord = self.virtualHelix().coord()
        insts = self.part().insertions()[coord]
        for i in range(self._base_idx_low, self._base_idx_high+1):
            if i in insts:
                return True
        return False
    # end def

    def hasInsertionAt(self, idx):
        coord = self.virtualHelix().coord()
        insts = self.part().insertions()[coord]
        return idx in insts
    # end def

    def hasModifierAt(self, idx):
        return idx in self._modifiers
    # end def

    def shallowCopy(self):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(self._strandset, *self.idxs())
        nS._oligo = self._oligo
        nS._strand5p = self._strand5p
        nS._strand3p = self._strand3p
        # required to shallow copy the dictionary
        nS._decorators = dict(self._decorators.items())
        nS._sequence = None  # self._sequence
        return nS
    # end def

    def deepCopy(self, strandset, oligo):
        """
        can't use python module 'copy' as the dictionary _decorators
        needs to be shallow copied as well, but wouldn't be if copy.copy()
        is used, and copy.deepcopy is undesired
        """
        nS = Strand(strandset, *self.idxs())
        nS._oligo = oligo
        decs = nS._decorators
        for key, decOrig in self._decorators:
            decs[key] = decOrig.deepCopy()
        # end fo
        nS._sequence = self._sequence
        return nS
    # end def
# end class
