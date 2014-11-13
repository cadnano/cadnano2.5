from operator import itemgetter
from itertools import repeat
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
        self._undoStack = None
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

    def getNeighbors(self, strand):
        is_in_set, overlap, strandset_idx = self._findIndexOfRangeFor(strand)
        s_list = self._strand_list
        if is_in_set:
            if strandset_idx > 0:
                lowStrand = s_list[strandset_idx - 1]
            else:
                lowStrand = None
            if strandset_idx < len(s_list) - 1:
                highStrand = s_list[strandset_idx + 1]
            else:
                highStrand = None
            return lowStrand, highStrand
        else:
            raise IndexError
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

    def getBoundsOfEmptyRegionContaining(self, base_idx):
        """
        Returns the (tight) bounds of the contiguous stretch of unpopulated
        bases that includes the base_idx.
        """
        low_idx, high_idx = 0, self.partMaxBaseIdx()  # init the return values
        len_strands = len(self._strand_list)

        # not sure how to set this up this to help in caching
        # lastIdx = self._last_strandset_idx

        if len_strands == 0:  # empty strandset, just return the part bounds
            return (low_idx, high_idx)

        low = 0              # index of the first (left-most) strand
        high = len_strands    # index of the last (right-most) strand
        while low < high:    # perform binary search to find empty region
            mid = (low + high) // 2
            midStrand = self._strand_list[mid]
            mLow, mHigh = midStrand.idxs()
            if base_idx < mLow:  # base_idx is to the left of crntStrand
                high = mid   # continue binary search to the left
                high_idx = mLow - 1  # set high_idx to left of crntStrand
            elif base_idx > mHigh:   # base_idx is to the right of crntStrand
                low = mid + 1    # continue binary search to the right
                low_idx = mHigh + 1  # set low_idx to the right of crntStrand
            else:
                return (None, None)  # base_idx was not empty
        self._last_strandset_idx = (low + high) // 2  # set cache
        return (low_idx, high_idx)
    # end def

    def indexOfRightmostNonemptyBase(self):
        """Returns the high base_idx of the last strand, or 0."""
        if len(self._strand_list) > 0:
            return self._strand_list[-1].highIdx()
        else:
            return 0

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
        boundsLow, boundsHigh = \
                            self.getBoundsOfEmptyRegionContaining(base_idx_low)
        can_insert, strandset_idx = \
                                self.getIndexToInsert(base_idx_low, base_idx_high)
        if can_insert:
            c = CreateStrandCommand(self,
                                        base_idx_low, base_idx_high, strandset_idx)
            row, col = self._virtual_helix.coord()
            # d = "(%d,%d).%d + [%d,%d]" % \
            #             (row, col, self._strand_type, base_idx_low, base_idx_high)
            d = "(%d,%d).%d^%d" % (row, col, self._strand_type, strandset_idx)
            util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
            return strandset_idx
        else:
            return -1
    # end def

    def createDeserializedStrand(self, base_idx_low, base_idx_high, use_undostack=False):
        """
        Passes a strand to AddStrandCommand that was read in from file input.
        Omits the step of checking _couldStrandInsertAtLastIndex, since
        we assume that deserialized strands will not cause collisions.
        """
        boundsLow, boundsHigh = self.getBoundsOfEmptyRegionContaining(base_idx_low)
        assert(base_idx_low < base_idx_high)
        assert(boundsLow <= base_idx_low)
        assert(base_idx_high <= boundsHigh)
        can_insert, strandset_idx = self.getIndexToInsert(base_idx_low, base_idx_high)
        if can_insert:
            c = CreateStrandCommand(self, base_idx_low, base_idx_high, strandset_idx)
            util.execCommandList(self, [c], desc=None, use_undostack=use_undostack)
            return strandset_idx
        else:
            return -1
    # end def

    def removeStrand(self, strand, strandset_idx=None, use_undostack=True, solo=True):
        """
        solo is an argument to enable limiting signals emiting from
        the command in the case the command is instantiated part of a larger
        command
        """
        cmds = []
        if strandset_idx == None:
            is_in_set, overlap, strandset_idx = self._findIndexOfRangeFor(strand)
            if not is_in_set:
                raise IndexError
        if self.isScaffold() and strand.sequence() is not None:
            cmds.append(strand.oligo().applySequenceCMD(None))
        cmds += strand.clearDecoratorCommands()
        cmds.append(RemoveStrandCommand(self, strand, strandset_idx, solo))
        util.execCommandList(self, cmds, desc="Remove strand", use_undostack=use_undostack)
        return strandset_idx
    # end def

    def removeAllStrands(self, use_undostack=True):
        # copy the list because we are going to shrink it and that's
        # a no no with iterators
        #temp = [x for x in self._strand_list]
        for strand in list(self._strand_list):#temp:
            self.removeStrand(strand, 0, use_undostack, solo=False)
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
            is_in_set, overlap, low_strandset_idx = self._findIndexOfRangeFor(strand_low)
            if is_in_set:
                c = MergeCommand(strand_low, strand_high, \
                                    low_strandset_idx, priority_strand)
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
            is_in_set, overlap, strandset_idx = self._findIndexOfRangeFor(strand)
            if is_in_set:
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
        if self._undoStack == None:
            self._undoStack = self._virtual_helix.undoStack()
        return self._undoStack

    def virtualHelix(self):
        return self._virtual_helix

    def strandFilter(self):
        return "scaffold" if self._strand_type == StrandType.SCAFFOLD else "staple"

    def hasStrandAt(self, idxLow, idxHigh):
        """
        """
        dummy_strand = Strand(self, idxLow, idxHigh)
        strand_list = [s for s in self._findOverlappingRanges(dummy_strand)]
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        return len(strand_list) > 0
    # end def

    def getOverlappingStrands(self, idxLow, idxHigh):
        dummy_strand = Strand(self, idxLow, idxHigh)
        strand_list = [s for s in self._findOverlappingRanges(dummy_strand)]
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        return strand_list
    # end def

    def hasStrandAtAndNoXover(self, idx):
        dummy_strand = Strand(self, idx, idx)
        strand_list = [s for s in self._findOverlappingRanges(dummy_strand)]
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        if len(strand_list) > 0:
            return False if strand_list[0].hasXoverAt(idx) else True
        else:
            return False
    # end def

    def hasNoStrandAtOrNoXover(self, idx):
        dummy_strand = Strand(self, idx, idx)
        strand_list = [s for s in self._findOverlappingRanges(dummy_strand)]
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        if len(strand_list) > 0:
            return False if strand_list[0].hasXoverAt(idx) else True
        else:
            return True
    # end def

    def getIndexToInsert(self, idxLow, idxHigh):
        """
        """
        can_insert = True
        dummy_strand = Strand(self, idxLow, idxHigh)
        if self._couldStrandInsertAtLastIndex(dummy_strand):
            return can_insert, self._last_strandset_idx
        is_in_set, overlap, idx = self._findIndexOfRangeFor(dummy_strand)
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        if overlap:
            can_insert = False
        return can_insert, idx
    # end def

    def getStrand(self, base_idx):
        """Returns the strand that overlaps with base_idx."""
        dummy_strand = Strand(self, base_idx, base_idx)
        strand_list = [s for s in self._findOverlappingRanges(dummy_strand)]
        dummy_strand._strandset = None
        dummy_strand.setParent(None)
        dummy_strand.deleteLater()
        dummy_strand = None
        return strand_list[0] if len(strand_list) > 0 else None
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
    def _addToStrandList(self, strand, idx):
        """Inserts strand into the _strand_list at idx."""
        self._strand_list.insert(idx, strand)

    def _removeFromStrandList(self, strand):
        """Remove strand from _strand_list."""
        self._doc.removeStrandFromSelection(strand)  # make sure the strand is no longer selected
        self._strand_list.remove(strand)

    def _couldStrandInsertAtLastIndex(self, strand):
        """Verification of insertability based on cached last index."""
        last_idx = self._last_strandset_idx
        strand_list = self._strand_list
        if last_idx == None or last_idx > (len(strand_list) - 1):
            self._last_strandset_idx = None
            return False
        else:
            s_test_high = strand_list[last_idx].lowIdx() if last_idx < len(strand_list) else self.partMaxBaseIdx()
            s_test_low = strand_list[last_idx - 1].highIdx() if last_idx > 0 else - 1
            sLow, sHigh = strand.idxs()
            if s_test_low < sLow and sHigh < s_test_high:
                return True
            else:
                return False

    def _findOverlappingRanges(self, qstrand, use_cache=False):
        """
        a binary search for the strands in self._strand_list overlapping with
        a query strands, or qstrands, indices.

        Useful for operations on complementary strands such as applying a
        sequence

        This is an generator for now

        Strategy:
        1.
            search the _strand_list for a strand the first strand that has a
            highIndex >= lowIndex of the query strand.
            save that strandset index as s_set_idx_low.
            if No strand satisfies this condition, return an empty list

            Unless it matches the query strand's lowIndex exactly,
            Step 1 is O(log N) where N in length of self._strand_list to the max,
            that is it needs to exhaust the search

            conversely you could search for first strand that has a
            lowIndex LESS than or equal to the lowIndex of the query strand.

        2.
            starting at self._strand_list[s_set_idx_low] test each strand to see if
            it's indexLow is LESS than or equal to qstrand.indexHigh.  If it is
            yield/return that strand.  If it's GREATER than the indexHigh, or
            you run out of strands to check, the generator terminates
        """
        strand_list = self._strand_list
        len_strands = len(strand_list)
        if len_strands == 0:
            return
        # end if

        low = 0
        high = len_strands
        qLow, qHigh = qstrand.idxs()

        # Step 1: get rangeIndexLow with a binary search
        if use_cache:  # or self.doesLastSetIndexMatch(qstrand, strand_list):
            # cache match!
            s_set_idx_low = self._last_strandset_idx
        else:
            s_set_idx_low = -1
            while low < high:
                mid = (low + high) // 2
                midStrand = strand_list[mid]

                # pre get indices from the currently tested strand
                mLow, mHigh = midStrand.idxs()

                if mHigh == qLow:
                    # match, break out of while loop
                    s_set_idx_low = mid
                    break
                elif mHigh > qLow:
                    # store the candidate index
                    s_set_idx_low = mid
                    # adjust the high index to find a better candidate if
                    # it exists
                    high = mid
                # end elif
                else:  # mHigh < qLow
                    # If a strand exists it must be a higher rangeIndex
                    # leave the high the same
                    low = mid + 1
                #end elif
            # end while
        # end else

        # Step 2: create a generator on matches
        # match on whether the temp_strand's lowIndex is
        # within the range of the qStrand
        if s_set_idx_low > -1:
            temp_strands = iter(strand_list[s_set_idx_low:])
            temp_strand = next(temp_strands)
            qHigh += 1  # bump it up for a more efficient comparison
            i = 0   # use this to
            while temp_strand and temp_strand.lowIdx() < qHigh:
                yield temp_strand
                # use a next and a default to cause a break condition
                temp_strand = next(temp_strands, None)
                i += 1
            # end while

            # cache the last index we left of at
            i = s_set_idx_low + i
            """
            if
            1. we ran out of strands to test adjust
                OR
            2. the end condition temp_strands highIndex is still inside the
            qstrand but not equal to the end point
                adjust i down 1
            otherwise
            """
            if not temp_strand or temp_strand.highIdx() < qHigh - 1:
                i -= 1
            # assign cache but double check it's a valid index
            self._last_strandset_idx = i if -1 < i < len_strands else None
            return
        else:
            # no strand was found
            # go ahead and clear the cache
            self._last_strandset_idx = None if len(self._strand_list) > 0 else 0
            return
    # end def

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
