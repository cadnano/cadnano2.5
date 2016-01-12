import array
from bisect import bisect_left, insort_left
from itertools import repeat
from operator import itemgetter
izip = zip

import cadnano.util as util

from cadnano import preferences as prefs
from cadnano.enum import StrandType
from cadnano.enum import StrandType
from cadnano.cnproxy import UndoStack, UndoCommand
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.oligo import Oligo
from cadnano.strand import Strand

from .createstrandcmd import CreateStrandCommand
from .removestrandcmd import RemoveStrandCommand
from .splitcmd import SplitCommand
from .mergecmd import MergeCommand

class StrandSet(CNObject):
    """
    StrandSet is a container class for Strands, and provides the several
    publicly accessible methods for editing strands, including operations
    for creation, destruction, resizing, splitting, and merging strands.

    Views may also query StrandSet for information that is useful in
    determining if edits can be made, such as the bounds of empty space in
    which a strand can be created or resized.
    """
    def __init__(self, strand_type, id_num, virtual_helix_group, initial_size):
        self._document = virtual_helix.document()
        super(StrandSet, self).__init__(virtual_helix_group)
        self._strand_type = strand_type
        self._id_num = id_num
        self._virtual_helix_group = virtual_helix_group

        self.strand_array = [None]*(initial_size)
        self.strand_heap = []

        self._undo_stack = None
        self._last_strandset_idx = None
    # end def

    def __iter__(self):
        """Iterate over each strand in the strands list."""
        return self.strands().__iter__()
    # end def

    def __repr__(self):
        if self._strand_type == 0:
            st = 'scaf'
        else:
            st = 'stap'
        num = self._virtual_helix.number()
        return "<%s_StrandSet(%d)>" % (st, num)
    # end def

    ### SIGNALS ###
    strandsetStrandAddedSignal = ProxySignal(CNObject, CNObject,
                                    name='strandsetStrandAddedSignal')#pyqtSignal(QObject, QObject)  # strandset, strand

    ### SLOTS ###

    ### ACCESSORS ###
    def part(self):
        return self._virtual_helix_group.part()
    # end def

    def document(self):
        return self._document
    # end def

    def strands(self):
        return self.strand_heap

    def resize(self, delta_low, delta_high):
        if delta_low < 0:
            self.strand_array = self.strand_array[delta_low:]
        if delta_high < 0:
            self.strand_array = self.strand_array[:delta_high]
        self.strand_array = [None]*delta_low + \
                self.strand_array + \
                    [None]*delta_high
    # end def

    def generatorStrand(self):
        """Return a generator that yields the strands in self.strand_array."""
        return iter(self.strand_heap)
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isDrawn5to3(self):
        return self._virtual_helix.isDrawn5to3(self)
    # end def

    def isForward(self):
        return self._strand_type is StrandType.FWD
    # end def

    def isReverse(self):
        return self._strand_type is StrandType.REV
    # end def

    def length(self):
        return len(self.strand_array)

    def idNum(self):
        return self._id_num

    # def getNeighbors(self, strand):
    #     sl = self.strand_array
    #     lsl = len(sl)
    #     start, end = strand.idxs()
    #     if sl[start] != strand:
    #         raise IndexError("strand not in list")
    #     if start != 0:
    #         start -= 1
    #     if end != lsl - 1:
    #         end += 1
    #     low_strand = None
    #     high_strand = None
    #     while start > -1:
    #         if sl[start] is not None:
    #             low_strand = sl[start]
    #             break
    #         else:
    #             start -= 1
    #     while end < lsl:
    #         if sl[end] is not None:
    #             high_strand = sl[end]
    #             break
    #         else:
    #             end += 1
    #     return low_strand, high_strand
    # # end def

    def getNeighbors(self, strand):
        sh = self.strand_heap
        i = bisect_left(sh, strand)
        if sh[i] != strand:
            raise ValueError("getNeighbors: strand not in set")
        if i == 0:
            low_strand = None
        else:
            low_strand = sh[i-1]
        if i == len(sh) - 1:
            high_strand = None
        else:
            high_strand = sh[i+1]
        return low_strand, high_strand
    # end def

    def complementStrandSet(self):
        """
        Returns the complementary strandset. Used for insertions and
        sequence application.
        """
        vhg = self._virtual_helix_group
        fwd_ss, rev_ss = vhg.getStrandSet(self.id_num)
        return rev_ss if self._strand_type == StrandType.FWD else fwd_ss
    # end def

    # def getBoundsOfEmptyRegionContaining(self, base_idx):
    #     """
    #     Returns the (tight) bounds of the contiguous stretch of unpopulated
    #     bases that includes the base_idx.
    #     """
    #     sl = self.strand_array
    #     lsl = len(sl)
    #     low_idx, high_idx = 0, self.partMaxBaseIdx()  # init the return values
    #     # len_strands = len(sl)

    #     # if len_strands == 0:  # empty strandset, just return the part bounds
    #     #     return (low_idx, high_idx)

    #     if sl[base_idx] is not None:
    #         # print("base already there", base_idx)
    #         return (None, None)

    #     i = base_idx
    #     while i > -1:
    #         if sl[i] is None:
    #             i -= 1
    #         else:
    #             low_idx = i + 1
    #             break

    #     i = base_idx
    #     while i < lsl:
    #         if sl[i] is None:
    #             i += 1
    #         else:
    #             high_idx = i - 1
    #     return (low_idx, high_idx)
    # # end def

    def getBoundsOfEmptyRegionContaining(self, base_idx):
        """ Return the bounds of the empty region containing base index <base_idx>. """
        class DummyStrand(object):
            _base_idx_low = base_idx
            def __lt__(self, other):
                return self._base_idx_low < other._base_idx_low

        ds = DummyStrand()
        sh = self.strand_heap
        lsh = len(sh)
        if lsh == 0:
            return 0, len(self.strand_array) - 1

        # the i-th index is the high-side strand and the i-1 index
        # is the low-side strand since bisect_left gives the index
        # to insert the dummy strand at
        i = bisect_left(sh, ds)
        if i == 0:
            low_idx = 0
        else:
            low_idx = sh[i - 1].highIdx() + 1

        # would be an append to the list effectively if inserting the dummy strand
        if i == lsh:
            high_idx = len(self.strand_array) - 1
        else:
            high_idx = sh[i].lowIdx() - 1
        return (low_idx, high_idx)
    # end def

    def indexOfRightmostNonemptyBase(self):
        """Returns the high base_idx of the last strand, or 0."""
        sh = self.strand_heap
        if len(sh) > 0:
            return sh[-1].highIdx()
        else:
            return 0
    # end def

    def partMaxBaseIdx(self):
        """Return the bounds of the StrandSet as defined in the part."""
        return self.length() - 1    # end def

    def strandCount(self):
        return len(self.strands())


    def strandType(self):
        return self._strand_type


    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def createStrand(self, base_idx_low, base_idx_high, use_undostack=True):
        """
        Assumes a strand is being created at a valid set of indices.
        """
        # print("sss creating strand")
        bounds_low, bounds_high = \
                            self.getBoundsOfEmptyRegionContaining(base_idx_low)

        if bounds_low is not None and bounds_low <= base_idx_low and \
            bounds_high is not None and bounds_high >= base_idx_high:
            c = CreateStrandCommand(self, base_idx_low, base_idx_high)
            x, y = self._virtual_helix_group.getOrigin(self._id_num)
            d = "%s:(%0.2f,%0.2f).%d^%d" % (self.part().getName(), x, y, self._strand_type, base_idx_low)
            # print("strand", d)
            util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
            return 0
        else:
            # print("could not create strand", bounds_low, bounds_high, base_idx_low, base_idx_high)
            return -1
    # end def

    def createDeserializedStrand(self, base_idx_low, base_idx_high, use_undostack=False):
        """
        Passes a strand to AddStrandCommand that was read in from file input.
        Omits the step of checking _couldStrandInsertAtLastIndex, since
        we assume that deserialized strands will not cause collisions.
        """
        c = CreateStrandCommand(self, base_idx_low, base_idx_high)
        x, y = self._virtual_helix_group.getOrigin(self._id_num)
        d = "(%0.2f,%0.2f).%d^%d" % (x, y, self._strand_type, base_idx_low)
        # print("strand", d)
        util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
        return 0
    # end def

    def isStrandInSet(self, strand):
        sl = self.strand_array
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
        cmds.append(RemoveStrandCommand(self, strand, solo=solo))
        util.execCommandList(self, cmds, desc="Remove strand", use_undostack=use_undostack)
    # end def

    def removeAllStrands(self, use_undostack=True):
        # copy the list because we are going to shrink it and that's
        # a no no with iterators
        #temp = [x for x in self.strand_array]
        for strand in list(self.strand_heap):
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
            if self.isStrandInSet(strand_low):
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
            if self.isStrandInSet(strand):
                c = SplitCommand(strand, base_idx, update_sequence)
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
    def strandFilter(self):
        return "forward" if self._strand_type is StrandType.FWD else "reverse"


    def hasStrandAt(self, idx_low, idx_high):
        """ Return True if strandset has a strand in the region between idx_low and idx_high (both included)."""
        sa = self.strand_array
        sh = self.strand_heap
        lsh = len(sh)

        strand = sa[idx_low]

        if strand is None:
            class DummyStrand(object):
                _base_idx_low = idx_low
                def __lt__(self, other):
                    return self._base_idx_low < other._base_idx_low

            ds = DummyStrand()
            i = bisect_left(sh, ds)

            while i < lsh:
                strand = sh[i]
                if strand.lowIdx() > idx_high:
                    return False
                elif idx_low <= strand.highIdx():
                    return True
                else:
                    i += 1
            return False
        else:
            return True
    # end def

    def getOverlappingStrands(self, idx_low, idx_high):
        sa = self.strand_array
        sh = self.strand_heap
        lsh = len(sh)

        strand = sa[idx_low]
        out = []
        if strand is None:
            class DummyStrand(object):
                _base_idx_low = idx_low
                def __lt__(self, other):
                    return self._base_idx_low < other._base_idx_low

            ds = DummyStrand()
            i = bisect_left(sh, ds)
        else:
            out.append(strand)
            i = bisect_left(sh, strand) + 1

        while i < lsh:
            strand = sh[i]
            if strand.lowIdx() > idx_high:
                break
            elif idx_low <= strand.highIdx():
                out.append(strand)
                i += 1
            else:
                i += 1
        return out
    # end def

    def hasStrandAtAndNoXover(self, idx):
        sl = self.strand_array
        strand = sl[idx]
        if strand is None:
            return False
        elif strand.hasXoverAt(idx):
            return False
        else:
            return True
    # end def

    def hasNoStrandAtOrNoXover(self, idx):
        sl = self.strand_array
        strand = sl[idx]
        if strand is None:
            return True
        elif strand.hasXoverAt(idx):
            return False
        else:
            return True
    # end def

    def getStrand(self, base_idx):
        """Returns the strand that overlaps with base_idx."""
        return self.strand_array[base_idx]
    # end def

    def getLegacyArray(self):
        """docstring for getLegacyArray"""
        num = self._id_num
        ret = [[-1, -1, -1, -1] for i in range(self.part().maxBaseIdx() + 1)]
        if self.isDrawn5to3():
            for strand in self.strand_heap:
                lo, hi = strand.idxs()
                assert strand.idx5Prime() == lo and strand.idx3Prime() == hi
                # map the first base (5' xover if necessary)
                s5p = strand.connection5p()
                if s5p is not None:
                    ret[lo][0] = s5p.idNum()
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
                    ret[hi][2] = s3p.idNum()
                    ret[hi][3] = s3p.idx5Prime()
                # end if
            # end for
        # end if
        else:
            for strand in self.strand_heap:
                lo, hi = strand.idxs()
                assert strand.idx3Prime() == lo and strand.idx5Prime() == hi
                # map the first base (3' xover if necessary)
                ret[lo][0] = num
                ret[lo][1] = lo + 1
                s3p = strand.connection3p()
                if s3p is not None:
                    ret[lo][2] = s3p.idNum()
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
                    ret[hi][0] = s5p.idNum()
                    ret[hi][1] = s5p.idx3Prime()
                # end if
            # end for
        return ret
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _addToStrandList(self, strand):
        """Inserts strand into the strand_array at idx."""
        # print("Adding to strandlist")
        idx_low, idx_high = strand.idxs()
        for i in range(idx_low, idx_high+1):
            self.strand_array[i] = strand
        insort_left(self.strand_heap, strand)

    def updateStrandIdxs(self, strand, old_idxs, new_idxs):
        """update indices in the strand array/list of an existing strand"""
        for i in range(old_idxs[0], old_idxs[1]+1):
            self.strand_array[i] = None
        for i in range(new_idxs[0], new_idxs[1]+1):
            self.strand_array[i] = strand

    def _removeFromStrandList(self, strand):
        """Remove strand from strand_array."""
        self._document.removeStrandFromSelection(strand)  # make sure the strand is no longer selected
        idx_low, idx_high = strand.idxs()
        for i in range(idx_low, idx_high+1):
            self.strand_array[i] = None
        i = bisect_left(self.strand_heap, strand)
        self.strand_heap.pop(i)

    def getStrandIndex(self, strand):
        try:
            ind = self.strand_array.index(strand)
            return (True, ind)
        except ValueError:
            return (False, 0)
    # end def

    def deepCopy(self, virtual_helix):
        """docstring for deepCopy"""
        pass
    # end def
# end class
