# -*- coding: utf-8 -*-
from bisect import bisect_left, insort_left
import cadnano.util as util
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnenum import StrandType
from .createstrandcmd import CreateStrandCommand
from .removestrandcmd import RemoveStrandCommand
from .mergecmd import MergeCommand
from .splitcmd import SplitCommand


class StrandSet(CNObject):
    """:class:`StrandSet` is a container class for :class:`Strands`, and provides
    the several publicly accessible methods for editing strands, including operations
    for creation, destruction, resizing, splitting, and merging strands.

    Views may also query :class:`StrandSet` for information that is useful in
    determining if edits can be made, such as the bounds of empty space in
    which a strand can be created or resized.

    Internally :class:`StrandSet` uses redundant heap and a list data structures
    to track :class:`Strands` objects, with the list of length of a virtual
    helix looking like::

        strand_array = [strandA, strandA, strandA, ..., None, strandB, strandB, ...]

    Where every index strandA spans has a reference to strandA and strand_heap::

        strand_heap = [strandA, strandB, strandC, ...]

    is merely a sorted list from low index to high index of strand objects

    Args:
        is_fwd (bool):  is this a forward or reverse StrandSet?
        id_num (int):   ID number of the virtual helix this is on
        part (Part):  Part object this is a child of
        initial_size (int): initial_size to allocate
    """
    def __init__(self, is_fwd, id_num, part, initial_size):
        self._document = part.document()
        super(StrandSet, self).__init__(part)
        self._is_fwd = is_fwd
        self._strand_type = StrandType.FWD if self._is_fwd else StrandType.REV
        self._id_num = id_num
        self._part = part

        self._reset(initial_size)

        self._undo_stack = None
    # end def

    def simpleCopy(self, part):
        """Create an empty copy (no strands) of this strandset with the only
        a new virtual_helix_group parent

        TODO: consider renaming this method

        Args:
            part (Part): part to copy this into
        """
        return StrandSet(self._is_fwd, self._id_num,
                         part, len(self.strand_array))
    # end def

    def __iter__(self):
        """Iterate over each strand in the strands list.

        Yields:
            Strand: :class:`Strand` in order from low to high index
        """
        return self.strands().__iter__()
    # end def

    def __repr__(self):
        if self._is_fwd:
            st = 'fwd'
        else:
            st = 'rev'
        num = self._id_num
        return "<%s_StrandSet(%d)>" % (st, num)
    # end def

    ### SIGNALS ###
    strandsetStrandAddedSignal = ProxySignal(CNObject, CNObject, name='strandsetStrandAddedSignal')
    """pyqtSignal(QObject, QObject): strandset, strand"""

    ### SLOTS ###

    ### ACCESSORS ###
    def part(self):
        """Get model :class:`Part`

        Returns:
            Part: the :class:`Part`
        """
        return self._part
    # end def

    def document(self):
        """Get model :class:`Document`

        Returns:
            Document: the :class:`Document`
        """
        return self._document
    # end def

    def strands(self):
        """Get raw reference to the strand_heap of this :class:`StrandSet`

        Returns:
            list: the list of strands
        """
        return self.strand_heap

    def _reset(self, initial_size):
        """Reset this object clearing out references to all :class:`Strand`
        objects.  Exceptional private method to be only used by Parts

        Args:
            initial_size (int): size to revert to
        """
        self.strand_array = [None]*(initial_size)
        self.strand_heap = []
    # end def

    def resize(self, delta_low, delta_high):
        """Resize this StrandSet.  Pad each end when growing otherwise
        don't do anything

        Args:
            delta_low (int):  amount to resize the low index end
            delta_high (int):  amount to resize the high index end
        """
        if delta_low < 0:
            self.strand_array = self.strand_array[delta_low:]
        if delta_high < 0:
            self.strand_array = self.strand_array[:delta_high]
        self.strand_array = [None]*delta_low + self.strand_array + [None]*delta_high
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def isForward(self):
        """Is the set 5' to 3' (forward) or is it 3' to 5' (reverse)

        Returns:
            bool: True if is forward, False otherwise
        """
        return self._is_fwd
    # end def

    def strandType(self):
        """Store the enum of strand type

        Returns:
            int: :class:`StrandType.FWD` if is forward, otherwise :class:`StrandType.REV`
        """
        return self._strand_type

    def isReverse(self):
        return not self._is_fwd
    # end def

    def length(self):
        """ length of the :class:`StrandSet` and therefore also the associated
        virtual helix in bases

        Returns:
            int: length of the set
        """
        return len(self.strand_array)

    def idNum(self):
        """Get the associated virtual helix ID number

        Returns:
            int: virtual helix ID number
        """
        return self._id_num
    # end def

    def getNeighbors(self, strand):
        """Given a :class:`Strand` in this :class:`StrandSet` find it's internal
        neighbors

        Args:
            strand (Strand):

        Returns:
            tuple: (low neighbor, high neighbor) of types :class:`Strand` or :obj:`None`
        """
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
        """Returns the complementary strandset. Used for insertions and
        sequence application.

        Returns:
            StrandSet: the complementary :class:`StrandSet`
        """
        fwd_ss, rev_ss = self._part.getStrandSets(self._id_num)
        return rev_ss if self._is_fwd else fwd_ss
    # end def

    def getBoundsOfEmptyRegionContaining(self, base_idx):
        """Return the bounds of the empty region containing base index <base_idx>.

        Args:
            base_idx (int): the index of interest

        Returns:
            tuple: of :obj:`int` of form::

                (low_idx, high_idx)
        """
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

    def strandCount(self):
        """Getter for the number of :class:`Strands` in the set

        Returns:
            int: the number of :class:`Strands` in the set
        """
        return len(self.strand_heap)
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def createStrand(self, base_idx_low, base_idx_high,
                     color=None, use_undostack=True):
        """Assumes a strand is being created at a valid set of indices.

        Args:
            base_idx_low (int):     low index of strand
            base_idx_high (int):    high index of strand
            color (:obj:`str`, optional): default=True
            use_undostack (:obj:`bool`, optional): default=True

        Returns:
            object: Strand if successful, None otherwise
        """
        # print("sss creating strand")
        part = self._part

        # NOTE: this color defaulting thing is problematic for tests
        if color is None:
            color = part.getProperty('color')
        bounds_low, bounds_high = self.getBoundsOfEmptyRegionContaining(base_idx_low)

        if bounds_low is not None and bounds_low <= base_idx_low and \
           bounds_high is not None and bounds_high >= base_idx_high:
            c = CreateStrandCommand(self, base_idx_low, base_idx_high,
                                    color,
                                    update_segments=use_undostack)
            x, y = part.getVirtualHelixOrigin(self._id_num)
            d = "%s:(%0.2f,%0.2f).%d^%d" % (self.part().getName(), x, y, self._is_fwd, base_idx_low)
            # print("strand", d)
            util.execCommandList(self, [c], desc=d, use_undostack=use_undostack)
            return c.strand()
        else:
            # print("could not create strand", bounds_low, bounds_high, base_idx_low, base_idx_high)
            return None
    # end def

    def createDeserializedStrand(self, base_idx_low, base_idx_high, color, use_undostack=False):
        """Passes a strand to AddStrandCommand that was read in from file input.
        Omits the step of checking _couldStrandInsertAtLastIndex, since
        we assume that deserialized strands will not cause collisions.

        """
        c = CreateStrandCommand(self, base_idx_low, base_idx_high,
                                color,
                                update_segments=use_undostack)
        x, y = self._part.getVirtualHelixOrigin(self._id_num)
        d = "(%0.2f,%0.2f).%d^%d" % (x, y, self._is_fwd, base_idx_low)
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
        """Remove a :class:`Strand` from the set

        Args:
            strand (Strand): the :class:`Strand` to remove
            use_undostack (:obj:`bool`, optional): default=True
            solo (:obj:`bool`, optional): solo is an argument to enable
            limiting signals emiting from the command in the case the command
            is instantiated part of a larger command, default=True
        """
        cmds = []

        if not self.isStrandInSet(strand):
            raise IndexError("Strandset.removeStrand: strand not in set")
        if strand.sequence() is not None:
            cmds.append(strand.oligo().applySequenceCMD(None))
        cmds += strand.clearDecoratorCommands()
        cmds.append(RemoveStrandCommand(self, strand, solo=solo))
        util.execCommandList(self, cmds, desc="Remove strand", use_undostack=use_undostack)
    # end def

    def oligoStrandRemover(self, strand, cmds, solo=True):
        """Used for removing all :class:`Strand`s from an :class:`Oligo`

        Args:
            strand (Strand): a strand to remove
            cmds (list): a list of :class:`UndoCommand` objects to append to
            solo (:obj:`bool`, optional): to pass on to RemoveStrandCommand,
            default=True
        """
        if not self.isStrandInSet(strand):
            raise IndexError("Strandset.oligoStrandRemover: strand not in set")
        cmds += strand.clearDecoratorCommands()
        cmds.append(RemoveStrandCommand(self, strand, solo=solo))
    # end def

    def removeAllStrands(self, use_undostack=True):
        """Remove all :class:`Strand` objects in the set

        Args:
         use_undostack (:obj:`bool`, optional): default=True
        """
        for strand in list(self.strand_heap):
            self.removeStrand(strand, use_undostack=use_undostack, solo=False)
        # end def

    def mergeStrands(self, priority_strand, other_strand, use_undostack=True):
        """Merge the priority_strand and other_strand into a single new strand.
        The oligo of priority should be propagated to the other and all of
        its connections.

        Args:
            priority_strand (Strand): priority strand
            other_strand (Strand): other strand
            use_undostack (:obj:`bool`, optional): default=True

        Returns:
            bool: True if strands were merged, False otherwise
        """
        low_and_high_strands = self.strandsCanBeMerged(priority_strand, other_strand)
        if low_and_high_strands:
            strand_low, strand_high = low_and_high_strands
            if self.isStrandInSet(strand_low):
                c = MergeCommand(strand_low, strand_high, priority_strand)
                util.doCmd(self, c, use_undostack=use_undostack)
                return True
        else:
            return False
    # end def

    def strandsCanBeMerged(self, strandA, strandB):
        """Only checks that the strands are of the same StrandSet and that the
        end points differ by 1.  DOES NOT check if the Strands overlap, that
        should be handled by addStrand

        Returns:
            tuple: empty :obj:`tuple` if the strands can't be
            merged if the strands can be merged it returns the strand with the
            lower index in the form::

                (strand_low, strand_high)
        """
        if strandA.strandSet() != strandB.strandSet():
            return ()
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
        """Break strand into two strands. Reapply sequence by default.

        Args:
            strand (Strand): the :class:`Strand`
            base_idx (int): the index
            update_sequence (:obj:`bool`, optional): whether to emit signal, default=True
            use_undostack (:obj:`bool`, optional): default=True

        Returns:
            bool: True if successful, False otherwise
            TODO consider return strands instead
        """
        if self.strandCanBeSplit(strand, base_idx):
            if self.isStrandInSet(strand):
                c = SplitCommand(strand, base_idx, update_sequence)
                util.doCmd(self, c, use_undostack=use_undostack)
                return True
            else:
                return False
        else:
            return False
    # end def

    def strandCanBeSplit(self, strand, base_idx):
        """Make sure the base index is within the strand
        Don't split right next to a 3Prime end
        Don't split on endpoint (AKA a crossover)

        Args:
            strand (Strand): the :class:`Strand`
            base_idx (int): the index to split at

        Returns:
            bool: True if can be split, False otherwise
        """
        # no endpoints
        lo, hi = strand.idxs()
        if base_idx == lo or base_idx == hi:
            return False
        # make sure the base index within the strand
        elif lo > base_idx or base_idx > hi:
            return False
        elif base_idx - lo > 1 and hi - base_idx > 1:
            return True
        else:
            return False
    # end def

    def destroy(self):
        """Destroy this object
        """
        self.setParent(None)
        self.deleteLater()  # QObject will emit a destroyed() Signal
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def strandFilter(self):
        """Get the filter type for this set

        Returns:
            str: 'forward' if is_fwd else 'reverse'
        """
        return "forward" if self._is_fwd else "reverse"
    # end def

    def hasStrandAt(self, idx_low, idx_high):
        """Check if set has a strand on the interval given

        Args:
            idx_low (int): low index
            idx_high (int): high index

        Returns:
            bool: True if strandset has a strand in the region between idx_low
            and idx_high (both included). False otherwise
        """
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
        """Gets :class:`Strand` list that overlap the given range.

        Args:
            idx_low (int): low index of overlap region
            idx_high (int): high index of overlap region

        Returns:
            :obj:`list` of :class:`Strand`: all :class:`Strand` objects in range
        """
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

    # def hasStrandAtAndNoXover(self, idx):
    #     """Name says it all

    #     Args:
    #         idx (int): index

    #     Returns:
    #         bool: True if hasStrandAtAndNoXover, False otherwise
    #     """
    #     sl = self.strand_array
    #     strand = sl[idx]
    #     if strand is None:
    #         return False
    #     elif strand.hasXoverAt(idx):
    #         return False
    #     else:
    #         return True
    # # end def

    # def hasNoStrandAtOrNoXover(self, idx):
    #     """Name says it all

    #     Args:
    #         idx (int): index

    #     Returns:
    #         bool: True if hasNoStrandAtOrNoXover, False otherwise
    #     """
    #     sl = self.strand_array
    #     strand = sl[idx]
    #     if strand is None:
    #         return True
    #     elif strand.hasXoverAt(idx):
    #         return False
    #     else:
    #         return True
    # # end def

    def getStrand(self, base_idx):
        """Returns the :class:`Strand` that overlaps with `base_idx`

        Args:
            base_idx (int):

        Returns:
            Strand: :class:`Strand` at `base_idx` if it exists
        """
        try:
            return self.strand_array[base_idx]
        except:
            print(self.strand_array)
            raise
    # end def

    def dump(self, xover_list):
        """ Serialize a StrandSet, and append to a xover_list of xovers
        adding a xover if the 3 prime end of it is founds
        TODO update this to support strand properties

        Args:
            xover_list (list): A list to append xovers to

        Returns:
            :obj:`list` of :obj:`tuple`: indices low and high of each strand in
            the :class:`StrandSet`
        """
        sh = self.strand_heap
        idxs = [strand.idxs() for strand in sh]
        colors = [strand.getColor() for strand in sh]
        is_fwd = self._is_fwd
        for strand in sh:
            s3p = strand.connection3p()
            if s3p is not None:
                xover = (strand.idNum(), is_fwd, strand.idx3Prime()) + s3p.dump5p()
                xover_list.append(xover)
        return idxs, colors
    # end def

    ### PRIVATE SUPPORT METHODS ###
    def _addToStrandList(self, strand, update_segments=True):
        """Inserts strand into the strand_array at idx

        Args:
            strand (Strand): the strand to add
            update_segments (:obj:`bool`, optional): whether to signal default=True
        """
        # print("Adding to strandlist")
        idx_low, idx_high = strand.idxs()
        for i in range(idx_low, idx_high+1):
            self.strand_array[i] = strand
        insort_left(self.strand_heap, strand)
        if update_segments:
            self._part.refreshSegments(self._id_num)

    def _updateStrandIdxs(self, strand, old_idxs, new_idxs):
        """update indices in the strand array/list of an existing strand

        Args:
            strand (Strand): the strand
            old_idxs (tuple): range (:obj:`int`) to clear
            new_idxs (tuple): range (:obj:`int`) to set to `strand`
        """
        for i in range(old_idxs[0], old_idxs[1] + 1):
            self.strand_array[i] = None
        for i in range(new_idxs[0], new_idxs[1] + 1):
            self.strand_array[i] = strand

    def _removeFromStrandList(self, strand, update_segments=True):
        """Remove strand from strand_array.

        Args:
            strand (Strand): the strand
            update_segments (:obj:`bool`, optional): whether to signal default=True
        """
        self._document.removeStrandFromSelection(strand)  # make sure the strand is no longer selected
        idx_low, idx_high = strand.idxs()
        for i in range(idx_low, idx_high + 1):
            self.strand_array[i] = None
        i = bisect_left(self.strand_heap, strand)
        self.strand_heap.pop(i)
        if update_segments:
            self._part.refreshSegments(self._id_num)

    def getStrandIndex(self, strand):
        """Get the 5' end index of strand if it exists for forward strands
        and the 3' end index of the strand for reverse strands

        Returns:
            tuple: (:obj:`bool`, :obj:`int`)
        """
        try:
            ind = self.strand_array.index(strand)
            return (True, ind)
        except ValueError:
            return (False, 0)
    # end def

    def _deepCopy(self, virtual_helix):
        """docstring for deepCopy"""
        raise NotImplementedError
    # end def
# end class
