from operator import itemgetter
from itertools import repeat
import array

izip = zip

from cadnano.enum import StrandType
import cadnano.preferences as prefs

import cadnano.util as util

from cadnano.cnproxy import UndoStack, UndoCommand
from cadnano.cnproxy import ProxyObject, ProxySignal

from cadnano.strand import Strand
from cadnano.oligo import Oligo

from .createstrandcmd import CreateStrandCommand
from .removestrandcmd import RemoveStrandCommand
from .splitcmd import SplitCommand
from .mergecmd import MergeCommand

class StrandSet(ProxyObject):
    """
    StrandSet is a container class for Strands, and provides the several
    publicly accessible methods for editing strands, including operations
    for creation, destruction, resizing, splitting, and merging strands.

    Views may also query StrandSet for information that is useful in
    determining if edits can be made, such as the bounds of empty space in
    which a strand can be created or resized.
    """
    def __init__(self, strand_type, virtual_helix):
        self._doc = virtual_helix.document()
        super(StrandSet, self).__init__(virtual_helix)
        self._virtual_helix = virtual_helix
        self._strand_list = []

        # self.strand_vector = array.array('L')
        self._undo_stack = None
        self._last_strandset_idx = None
        self._strand_type = strand_type
    # end def

    def __iter__(self):
        """Iterate over each strand in the strands list."""
        return self._strand_list.__iter__()
    # end def

    def __repr__(self):
        if self._strand_type == 0:
            type = 'scaf'
        else:
            type = 'stap'
        num = self._virtual_helix.number()
        return "<%s_StrandSet(%d)>" % (type, num)
    # end def

    ### SIGNALS ###
    strandsetStrandAddedSignal = ProxySignal(ProxyObject, ProxyObject,
                                    name='strandsetStrandAddedSignal')#pyqtSignal(QObject, QObject)  # strandset, strand

    ### SLOTS ###

    ### ACCESSORS ###
    def part(self):
        return self._virtual_helix.part()
    # end def

    def document(self):
        return self._doc
    # end def

    def generatorStrand(self):
        """Return a generator that yields the strands in self._strand_list."""
        return iter(self._strand_list)
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isDrawn5to3(self):
        return self._virtual_helix.isDrawn5to3(self)
    # end def

    def isStaple(self):
        return self._strand_type == StrandType.STAPLE
    # end def

    def isScaffold(self):
        return self._strand_type == StrandType.SCAFFOLD
    # end def

    # def getNeighbors(self, strand):
    #     is_in_set, overlap, strandset_idx = self._findIndexOfRangeFor(strand)
    #     s_list = self._strand_list
    #     if is_in_set:
    #         if strandset_idx > 0:
    #             lowStrand = s_list[strandset_idx - 1]
    #         else:
    #             lowStrand = None
    #         if strandset_idx < len(s_list) - 1:
    #             highStrand = s_list[strandset_idx + 1]
    #         else:
    #             highStrand = None
    #         return lowStrand, highStrand
    #     else:
    #         raise IndexError
    # # end def

    def getNeighbors(self, strand):
        sl = self._strand_list
        lsl = len(sl) 
        start, end = strand.idxs()
        if sl[start] != strand:
            raise IndexError("strand not in list")
        if start != 0:
            start -= 1
        if end != lsl - 1:
            end += 1
        low_strand = None
        high_strand = None
        while start > -1:
            if sl[start] != None:
                low_strand = sl[start]
                break
            else:
                start -= 1
        while end < lsl:
            if sl[i] != None:
                high_strand = sl[end]
                break
            else:
                end += 1
        return low_strand, high_strand
    # end def

    def complementStrandSet(self):
        """
        Returns the complementary strandset. Used for insertions and
        sequence application.
        """
        vh = self.virtualHelix()
        if self.isStaple():
            return vh.scaffoldStrandSet()
        else:
            return vh.stapleStrandSet()
    # end def

    # def getBoundsOfEmptyRegionContaining(self, base_idx):
    #     """
    #     Returns the (tight) bounds of the contiguous stretch of unpopulated
    #     bases that includes the base_idx.
    #     """
    #     low_idx, high_idx = 0, self.partMaxBaseIdx()  # init the return values
    #     len_strands = len(self._strand_list)

    #     # not sure how to set this up this to help in caching
    #     # lastIdx = self._last_strandset_idx

    #     if len_strands == 0:  # empty strandset, just return the part bounds
    #         return (low_idx, high_idx)

    #     low = 0              # index of the first (left-most) strand
    #     high = len_strands    # index of the last (right-most) strand
    #     while low < high:    # perform binary search to find empty region
    #         mid = (low + high) // 2
    #         midStrand = self._strand_list[mid]
    #         mLow, mHigh = midStrand.idxs()
    #         if base_idx < mLow:  # base_idx is to the left of crntStrand
    #             high = mid   # continue binary search to the left
    #             high_idx = mLow - 1  # set high_idx to left of crntStrand
    #         elif base_idx > mHigh:   # base_idx is to the right of crntStrand
    #             low = mid + 1    # continue binary search to the right
    #             low_idx = mHigh + 1  # set low_idx to the right of crntStrand
    #         else:
    #             return (None, None)  # base_idx was not empty
    #     self._last_strandset_idx = (low + high) // 2  # set cache
    #     return (low_idx, high_idx)
    # # end def

    def getBoundsOfEmptyRegionContaining(self, base_idx):
        """
        Returns the (tight) bounds of the contiguous stretch of unpopulated
        bases that includes the base_idx.
        """
        sl = self._strand_list

        low_idx, high_idx = 0, self.partMaxBaseIdx()  # init the return values
        # len_strands = len(sl)

        # if len_strands == 0:  # empty strandset, just return the part bounds
        #     return (low_idx, high_idx)

        if sl[base_idx] != None:
            return (None, None)

        low_idx = None
        high_idx= None
        i = base_idx
        while i > -1:
            if sl[i] == None:
                i -= 1
            else:
                low_idx = i + 1
                break
        i = base_idx
        while end < lsl:
            if sl[i] == None:
                i += 1
            else:
                high_idx = i - 1
        return (low_idx, high_idx)
    # end def


    # def indexOfRightmostNonemptyBase(self):
    #     """Returns the high base_idx of the last strand, or 0."""
    #     if len(self._strand_list) > 0:
    #         return self._strand_list[-1].highIdx()
    #     else:
    #         return 0

    def indexOfRightmostNonemptyBase(self):
        """Returns the high base_idx of the last strand, or 0."""
        sl = self._strand_list
        lsl = len(sl)-1
        for i in range(lsl, -1, -1):
            if sl[i] != None:
                return sl[i].highIdx()
    # end def

    def partMaxBaseIdx(self):
        """Return the bounds of the StrandSet as defined in the part."""
        return self._virtual_helix.part().maxBaseIdx()
    # end def

    def strandCount(self):
        return len(self._strand_list)
    # end def

    def strandType(self):
        return self._strand_type
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def createStrand(self, base_idx_low, base_idx_high, use_undostack=True):
        """
        Assumes a strand is being created at a valid set of indices.
        """
        bounds_low, bounds_high = \
                            self.getBoundsOfEmptyRegionContaining(base_idx_low)
    
        if bounds_low != None and bounds_low <= base_idx_low and
            bounds_high != None and bounds_high >= base_idx_high:
            c = CreateStrandCommand(self,
                                        base_idx_low, base_idx_high)
            row, col = self._virtual_helix.coord()
            d = "(%d,%d).%d" % (row, col, self._strand_type)
            util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
            return 0
        else:
            return -1
    # end def

    def createDeserializedStrand(self, base_idx_low, base_idx_high, use_undostack=False):
        """
        Passes a strand to AddStrandCommand that was read in from file input.
        Omits the step of checking _couldStrandInsertAtLastIndex, since
        we assume that deserialized strands will not cause collisions.
        """
        c = CreateStrandCommand(self,
                                    base_idx_low, base_idx_high)
        row, col = self._virtual_helix.coord()
        d = "(%d,%d).%d" % (row, col, self._strand_type)
        util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
        return 0
    # end def

    def isStrandInSet(self, strand):
        sl = self._strand_list
        if sl[strand.lowIdx()] == strand and sl[strand.highIdx()] == strand:
            return True
        else:
            return False
    # end def

    def removeStrand(self, strand, use_undostack=True, solo=True):
        """
        solo is an argument to enable limiting signals emiting from
        the command in the case the command is instantiated part of a larger
        command
        """
        cmds = []

        if not self.isStrandInSet(strand):
                raise IndexError("Strandset.removeStrand: strand not in set")
        if self.isScaffold() and strand.sequence() is not None:
            cmds.append(strand.oligo().applySequenceCMD(None))
        cmds += strand.clearDecoratorCommands()
        cmds.append(RemoveStrandCommand(self, strand, solo))
        util.execCommandList(self, cmds, desc="Remove strand", use_undostack=use_undostack)
        return strandset_idx
    # end def

    def removeAllStrands(self, use_undostack=True):
        # copy the list because we are going to shrink it and that's
        # a no no with iterators
        #temp = [x for x in self._strand_list]
        for strand in set(self._strand_list):
            self.removeStrand(strand, use_undostack=use_undostack, solo=False)
        # end def

    def mergeStrands(self, priority_strand, other_strand, use_undostack=True):
        """
        Merge the priority_strand and other_strand into a single new strand.
        The oligo of priority should be propagated to the other and all of
        its connections.
        """
        low_and_high_strands = self.strandsCanBeMerged(priority_strand, other_strand)
        if low_and_high_strands:
            strand_low, strand_high = low_and_high_strands
            if self.isStrandInSet(low_strand):
                c = MergeCommand(strand_low, strand_high, priority_strand)
                util.execCommandList(self, [c], desc="Merge", use_undostack=use_undostack)
    # end def

    def strandsCanBeMerged(self, strandA, strandB):
        """
        returns None if the strands can't be merged, otherwise
        if the strands can be merge it returns the strand with the lower index

        only checks that the strands are of the same StrandSet and that the
        end points differ by 1.  DOES NOT check if the Strands overlap, that
        should be handled by addStrand
        """
        if strandA.strandSet() != strandB.strandSet():
            return None
        if abs(strandA.lowIdx() - strandB.highIdx()) == 1 or \
            abs(strandB.lowIdx() - strandA.highIdx()) == 1:
            if strandA.lowIdx() < strandB.lowIdx():
                if not strandA.connectionHigh() and not strandB.connectionLow():
                    return strandA, strandB
            else:
                if not strandB.connectionHigh() and not strandA.connectionLow():
                    return strandB, strandA
        else:
            return None
    # end def

    def splitStrand(self, strand, base_idx, update_sequence=True, use_undostack=True):
        """
        Break strand into two strands. Reapply sequence by default (disabled
        during autostaple).
        """
        if self.strandCanBeSplit(strand, base_idx):
            if self.isStrandInSet(low_strand):
                c = SplitCommand(strand, base_idx, strandset_idx, update_sequence)
                util.execCommandList(self, [c], desc="Split", use_undostack=use_undostack)
                return True
            else:
                return False
        else:
            return False
    # end def

    def strandCanBeSplit(self, strand, base_idx):
        """
        Make sure the base index is within the strand
        Don't split right next to a 3Prime end
        Don't split on endpoint (AKA a crossover)
        """
        # no endpoints
        if base_idx == strand.lowIdx() or base_idx == strand.highIdx():
            return False
        # make sure the base index within the strand
        elif strand.lowIdx() > base_idx or base_idx > strand.highIdx():
            return False
        elif abs(base_idx - strand.idx3Prime()) > 1:
            return True
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject will emit a destroyed() Signal
    # end def

    def remove(self, use_undostack=True):
        """
        Removes a VirtualHelix from the model. Accepts a reference to the
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if use_undostack:
            self.undoStack().beginMacro("Delete StrandSet")
        self.removeAllStrands(use_undostack)
        if use_undostack:
            self.undoStack().endMacro()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def undoStack(self):
        if self._undo_stack == None:
            self._undo_stack = self._virtual_helix.undoStack()
        return self._undo_stack

    def virtualHelix(self):
        return self._virtual_helix

    def strandFilter(self):
        return "scaffold" if self._strand_type == StrandType.SCAFFOLD else "staple"

    def hasStrandAt(self, idx_low, idx_high):
        """
        """
        sl = self._strand_list
        if sl[idx_low] == None and sl[idx_high] == None:
            return False
        else:
            return True
    # end def

    def getOverlappingStrands(self, idx_low, idx_high):
        sl = self._strand_list
        strand_subset = set()
        out = []
        for i in range(idx_low, idx_high + 1]):
            strand = sl[i]
            if strand in strand_subset:
                continue
            else:
                strand_subset.add(strand)
                out.append(strand)
        return out
    # end def

    def hasStrandAtAndNoXover(self, idx):
        sl = self._strand_list
        strand = sl[idx]
        if strand == None:
            return False
        elif strand.hasXoverAt(idx):
            return False
        else:
            return True
    # end def

    def hasNoStrandAtOrNoXover(self, idx):
        sl = self._strand_list
        strand = sl[idx]
        if strand == None:
            return True
        elif strand.hasXoverAt(idx):
            return False
        else:
            return True
    # end def

    def getStrand(self, base_idx):
        """Returns the strand that overlaps with base_idx."""
        return self._strand_list[base_idx]
    # end def

    def getLegacyArray(self):
        """docstring for getLegacyArray"""
        num = self._virtual_helix.number()
        ret = [[-1, -1, -1, -1] for i in range(self.part().maxBaseIdx() + 1)]
        if self.isDrawn5to3():
            for strand in self._strand_list:
                lo, hi = strand.idxs()
                assert strand.idx5Prime() == lo and strand.idx3Prime() == hi
                # map the first base (5' xover if necessary)
                s5p = strand.connection5p()
                if s5p is not None:
                    ret[lo][0] = s5p.virtualHelix().number()
                    ret[lo][1] = s5p.idx3Prime()
                ret[lo][2] = num
                ret[lo][3] = lo + 1
                # map the internal bases
                for idx in range(lo + 1, hi):
                    ret[idx][0] = num
                    ret[idx][1] = idx - 1
                    ret[idx][2] = num
                    ret[idx][3] = idx + 1
                # map the last base (3' xover if necessary)
                ret[hi][0] = num
                ret[hi][1] = hi - 1
                s3p = strand.connection3p()
                if s3p is not None:
                    ret[hi][2] = s3p.virtualHelix().number()
                    ret[hi][3] = s3p.idx5Prime()
                # end if
            # end for
        # end if
        else:
            for strand in self._strand_list:
                lo, hi = strand.idxs()
                assert strand.idx3Prime() == lo and strand.idx5Prime() == hi
                # map the first base (3' xover if necessary)
                ret[lo][0] = num
                ret[lo][1] = lo + 1
                s3p = strand.connection3p()
                if s3p is not None:
                    ret[lo][2] = s3p.virtualHelix().number()
                    ret[lo][3] = s3p.idx5Prime()
                # map the internal bases
                for idx in range(lo + 1, hi):
                    ret[idx][0] = num
                    ret[idx][1] = idx + 1
                    ret[idx][2] = num
                    ret[idx][3] = idx - 1
                # map the last base (5' xover if necessary)
                ret[hi][2] = num
                ret[hi][3] = hi - 1
                s5p = strand.connection5p()
                if s5p is not None:
                    ret[hi][0] = s5p.virtualHelix().number()
                    ret[hi][1] = s5p.idx3Prime()
                # end if
            # end for
        return ret
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _addToStrandList(self, strand):
        """Inserts strand into the _strand_list at idx."""
        idx_low, idx_high = strand.idxs()
        self._strand_list[idx_low:idx_high+1] = strand

    def _removeFromStrandList(self, strand):
        """Remove strand from _strand_list."""
        self._doc.removeStrandFromSelection(strand)  # make sure the strand is no longer selected
        idx_low, idx_high = strand.idxs()
        self._strand_list[idx_low:idx_high+1] = None

    def getStrandIndex(self, strand):
        try:
            ind = self._strand_list.index(strand)
            return (True, ind)
        except ValueError:
            return (False, 0)
    # end def

    def _findIndexOfRangeFor(self, strand):
        """
        Performs a binary search for strand in self._strand_list.

        If the strand is found, we want to return its index and we don't care
        about whether it overlaps with anything.

        If the strand is not found, we want to return whether it would
        overlap with any existing strands, and if not, the index where it
        would go.

        Returns a tuple (found, overlap, idx)
            found is True if strand in self._strand_list
            overlap is True if strand is not found, and would overlap with
            existing strands in self._strand_list
            idx is the index where the strand was found if found is True
            idx is the index where the strand could be inserted if found
            is False and overlap is False.
        """
        # setup
        strand_list = self._strand_list
        lastIdx = self._last_strandset_idx
        len_strands = len(strand_list)
        # base case: empty list, can insert at 0
        if len_strands == 0:
            return (False, False, 0)
        # check cache
        if lastIdx:
            if lastIdx < len_strands and strand_list[lastIdx] == strand:
                return (True, False, lastIdx)
        # init search bounds
        low, high = 0, len_strands
        sLow, sHigh = strand.idxs()
        # perform binary search
        while low < high:
            mid = (low + high) // 2
            midStrand = strand_list[mid]
            mLow, mHigh = midStrand.idxs()
            if midStrand == strand:
                self._last_strandset_idx = mid
                return (True, False, mid)
            elif mHigh < sLow:
                #  strand                [sLow----)
                # mStrand  (----mHigh]
                low = mid + 1  # search higher
            elif mLow > sHigh:
                #  strand  (----sHigh]
                # mStrand                [mLow----)
                high = mid  # search lower
            else:
                if mLow <= sLow <= mHigh:
                    # overlap: right side of mStrand
                    #  strand         [sLow---------------)
                    # mStrand  [mLow----------mHigh]
                    self._last_strandset_idx = None
                    return (False, True, None)
                elif mLow <= sHigh <= mHigh:
                    # overlap: left side of mStrand
                    #  strand  (--------------sHigh]
                    # mStrand         [mLow-----------mHigh]
                    self._last_strandset_idx = None
                    return (False, True, None)
                elif sLow <= mLow and mHigh <= sHigh:
                    # overlap: strand encompases existing
                    #  strand  [sLow-------------------sHigh]
                    # mStrand         [mLow----mHigh]
                    # note: inverse case is already covered above
                    self._last_strandset_idx = None
                    return (False, True, None)
                else:
                    # strand not in set, here's where you'd insert it
                    self._last_strandset_idx = mid
                    return (False, False, mid)
            # end else
        self._last_strandset_idx = low
        return (False, False, low)
    # end def

    def _doesLastSetIndexMatch(self, qstrand, strand_list):
        """
        strand_list is passed to save a lookup
        """
        lSI = self._last_strandset_idx
        if lSI:
            qLow, qHigh = qstrand.idxs()
            temp_strand = strand_list[lSI]
            tLow, tHigh = temp_strand.idxs()
            if not (qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh):
                return False
            else:  # get a difference
                dif = abs(qLow - tLow)
                # check neighboring strand_list just in case
                difLow = dif + 1
                if lSI > 0:
                    tLow, tHigh = strand[lSI - 1].idxs()
                    if qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh:
                        difLow = abs(qLow - tLow)
                difHigh = dif + 1
                if lSI < len(strand) - 1:
                    tLow, tHigh = strand[lSI + 1].idxs()
                    if qLow <= tLow <= qHigh or qLow <= tHigh <= qHigh:
                        difHigh = abs(qLow - tLow)
                # check that the cached strand is in fact the right guy
                if dif < difLow and dif < difHigh:
                    return True
                else:
                    False
            # end else
        # end if
        else:
            return False
        # end else
    # end def

    def deepCopy(self, virtual_helix):
        """docstring for deepCopy"""
        pass
    # end def
# end class
