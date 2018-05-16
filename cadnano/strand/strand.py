# -*- coding: utf-8 -*-
from array import array
from operator import attrgetter
from typing import (
    Tuple,
    List,
    Iterable
)

from cadnano import util
from cadnano.proxies.cnproxy import UndoCommand
from cadnano.proxies.cnobject import CNObject
from cadnano.proxies.cnproxy import ProxySignal
from cadnano.proxies.cnenum import EnumType
from .insertioncmd import (
    AddInsertionCommand,
    RemoveInsertionCommand
)
from .insertioncmd import ChangeInsertionCommand
from .modscmd import (
    AddModsCommand,
    RemoveModsCommand
)
from .resizecmd import ResizeCommand
from cadnano.cntypes import (
    NucleicAcidPartT,
    OligoT,
    StrandSetT,
    StrandT,
    DocT,
    InsertionT,
    SegmentT
)

def sixb(x: str) -> bytes: return x.encode('utf-8')


ARRAY_TYPE = 'B'


def tostring(x: array) -> str: return x.tobytes().decode('utf-8')


class Strand(CNObject):
    """A Strand is a continuous stretch of bases that are all in the same
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

    Args:
        strandset (StrandSet):
        base_idx_low (int): low index
        base_idx_high (int): high index
        oligo (cadnano.oligo.Oligo): optional, defaults to None.

    """

    def __init__(self,  strandset: StrandSetT,
                        base_idx_low: int, base_idx_high: int,
                        oligo: OligoT = None):
        self._document = strandset.document()
        super(Strand, self).__init__(strandset)
        self._strandset = strandset
        self._id_num = strandset.idNum()

        """Keep track of its own segments.  Updated on creation and resizing
        """

        self._base_idx_low = base_idx_low  # base index of the strand's left bound
        self._base_idx_high = base_idx_high  # base index of the right bound
        self._oligo = oligo
        self._strand5p = None  # 5' connection to another strand
        self._strand3p = None  # 3' connection to another strand
        self._sequence = None

        self.segments = []
        self.abstract_sequence = []

        # dynamic methods for mapping high/low connection /indices
        # to corresponding 3Prime 5Prime
        is_forward = strandset.isForward()
        if is_forward:
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
        self._is_forward = is_forward
    # end def

    def __repr__(self) -> str:
        s = "%s.<%s(%s, %s)>" % (self._strandset.__repr__(),
                                 self.__class__.__name__,
                                 self._base_idx_low,
                                 self._base_idx_high)
        return s
    # end def

    def __lt__(self, other) -> bool:
        return self._base_idx_low < other._base_idx_low

    def generator5pStrand(self) -> StrandT:
        """Iterate from self to the final _strand5p is None
        3' to 5'

        Includes originalCount to check for circular linked list

        Yields:
            Strand: 5' connected :class:`Strand`
        """
        node0 = node = self
        f = attrgetter('_strand5p')
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break

    # end def

    def generator3pStrand(self) -> StrandT:
        """Iterate from self to the final _strand3p is None
        5prime to 3prime
        Includes originalCount to check for circular linked list

        Yields:
            Strand: 3' connected :class:`Strand`
        """
        node0 = node = self
        f = attrgetter('_strand3p')
        while node:
            yield node  # equivalent to: node = node._strand5p
            node = f(node)
            if node0 == node:
                break
    # end def

    def strandFilter(self) -> List[str]:
        return self._strandset.strandFilter()

    ### SIGNALS ###
    strandHasNewOligoSignal = ProxySignal(CNObject, name='strandHasNewOligoSignal')
    """pyqtSignal(QObject): strand"""

    strandRemovedSignal = ProxySignal(CNObject, name='strandRemovedSignal')
    """pyqtSignal(QObject): strand"""

    strandResizedSignal = ProxySignal(CNObject, tuple, name='strandResizedSignal')
    """pyqtSignal(QObject, tuple)"""

    strandXover5pRemovedSignal = ProxySignal(CNObject, CNObject, name='strandXover5pRemovedSignal')
    """pyqtSignal(QObject, QObject: (strand3p, strand5p)"""

    strandConnectionChangedSignal = ProxySignal(CNObject, name='strandConnectionChangedSignal')
    """pyqtSignal(QObjec): strand"""

    strandInsertionAddedSignal = ProxySignal(CNObject, object, name='strandInsertionAddedSignal')
    """pyqtSignal(QObject, object): (strand, insertion object)"""

    strandInsertionChangedSignal = ProxySignal(CNObject, object, name='strandInsertionChangedSignal')
    """#pyqtSignal(QObject, object): (strand, insertion object)"""

    strandInsertionRemovedSignal = ProxySignal(CNObject, int, name='strandInsertionRemovedSignal')
    """#pyqtSignal(QObject, int): # Parameters: (strand, insertion index)"""

    strandModsAddedSignal = ProxySignal(CNObject, CNObject, str, int, name='strandModsAddedSignal')
    """pyqtSignal(QObject, object, str, int): (strand, document, mod_id, idx)"""

    strandModsChangedSignal = ProxySignal(CNObject, CNObject, str, int, name='strandModsChangedSignal')
    """pyqtSignal(QObject, object, str, int): (strand, document, mod_id, idx)"""

    strandModsRemovedSignal = ProxySignal(CNObject, CNObject, str, int, name='strandModsRemovedSignal')
    """pyqtSignal(QObject, object, str, int): (strand, document, mod_id, idx)"""

    strandSelectedChangedSignal = ProxySignal(CNObject, tuple, name='strandSelectedChangedSignal')
    """pyqtSignal(QObject, tuple): (strand, value)"""

    ### SLOTS ###
    ### ACCESSORS ###
    def part(self) -> NucleicAcidPartT:
        return self._strandset.part()
    # end def

    def idNum(self) -> int:
        return self._id_num
    # end def

    def document(self) -> DocT:
        return self._document
    # end def

    def oligo(self) -> OligoT:
        return self._oligo
    # end def

    def getColor(self) -> str:
        return self._oligo.getColor()
    # end def

    def sequence(self, for_export: bool = False) -> str:
        seq = self._sequence
        if seq:
            return util.markwhite(seq) if for_export else seq
        elif for_export:
            return ''.join(['?' for x in range(self.totalLength())])
        return ''
    # end def

    def abstractSeq(self) -> str:
        return ','.join([str(i) for i in self.abstract_sequence])

    def strandSet(self) -> StrandSetT:
        return self._strandset
    # end def

    def strandType(self) -> EnumType:
        return self._strandset.strandType()

    def isForward(self) -> bool:
        return self._strandset.isForward()

    def setSequence(self, sequence: str) -> Tuple[str, str]:
        """Applies sequence string from 5' to 3'
        return the tuple (used, unused) portion of the sequence

        Args:
            sequence (str):

        Returns:
            tuple: of :obj:`str` of form::

                (used, unused)
        """
        if sequence is None:
            self._sequence = None
            return None, None
        length = self.totalLength()
        if len(sequence) < length:
            bonus = length - len(sequence)
            sequence += ''.join([' ' for x in range(bonus)])
        temp = sequence[0:length]
        self._sequence = temp
        return temp, sequence[length:]
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

        for comp_strand in comp_ss.getOverlappingStrands(self._base_idx_low,
                                                         self._base_idx_high):
            comp_seq = comp_strand.sequence()
            used_seq = util.comp(comp_seq) if comp_seq else None
            used_seq = self.setComplementSequence(used_seq, comp_strand)
        # end for
    # end def

    def getComplementStrands(self) -> List[StrandT]:
        """Return the list of complement strands that overlap with this strand.
        """
        comp_ss = self.strandSet().complementStrandSet()
        return [comp_strand for comp_strand in
                comp_ss.getOverlappingStrands(self._base_idx_low, self._base_idx_high)]
    # end def

    def setComplementSequence(self, sequence: str, strand: StrandT) -> str:
        """This version takes anothers strand and only sets the indices that
        align with the given complimentary strand.

        As it depends which direction this is going, and strings are stored in
        memory left to right, we need to test for is_forward to map the
        reverse compliment appropriately, as we traverse overlapping strands.

        We reverse the sequence ahead of time if we are applying it 5' to 3',
        otherwise we reverse the sequence post parsing if it's 3' to 5'

        Again, sequences are stored as strings in memory 5' to 3' so we need
        to jump through these hoops to iterate 5' to 3' through them correctly

        Perhaps it's wiser to merely store them left to right and reverse them
        at draw time, or export time

        Args:
            sequence (str):
            strand (Strand):

        Returns:
            str: the used portion of the sequence
        """
        s_low_idx, s_high_idx = self._base_idx_low, self._base_idx_high
        c_low_idx, c_high_idx = strand.idxs()
        is_forward = self._is_forward
        self_seq = self._sequence
        # get the ovelap
        low_idx, high_idx = util.overlap(s_low_idx, s_high_idx, c_low_idx, c_high_idx)

        # only get the characters we're using, while we're at it, make it the
        # reverse compliment

        total_length = self.totalLength()

        # see if we are applying
        if sequence is None:
            # clear out string for in case of not total overlap
            use_seq = ''.join([' ' for x in range(total_length)])
        else:  # use the string as is
            use_seq = sequence[::-1] if is_forward else sequence

        temp = array(ARRAY_TYPE, sixb(use_seq))
        if self_seq is None:
            temp_self = array(ARRAY_TYPE, sixb(''.join([' ' for x in range(total_length)])))
        else:
            temp_self = array(ARRAY_TYPE, sixb(self_seq) if is_forward else sixb(self_seq[::-1]))

        # generate the index into the compliment string
        a = self.insertionLengthBetweenIdxs(s_low_idx, low_idx - 1)
        b = self.insertionLengthBetweenIdxs(low_idx, high_idx)
        c = strand.insertionLengthBetweenIdxs(c_low_idx, low_idx - 1)
        start = low_idx - c_low_idx + c
        end = start + b + high_idx - low_idx + 1
        temp_self[low_idx - s_low_idx + a:high_idx - s_low_idx + 1 + a + b] = temp[start:end]
        # print("old sequence", self_seq)
        self._sequence = tostring(temp_self)

        # if we need to reverse it do it now
        if not is_forward:
            self._sequence = self._sequence[::-1]

        # test to see if the string is empty(), annoyingly expensive
        # if len(self._sequence.strip()) == 0:
        if not self._sequence:
            self._sequence = None

        # print("new sequence", self._sequence)
        return self._sequence
    # end def

    def clearAbstractSequence(self):
        self.abstract_sequence = []
    # end def

    def applyAbstractSequence(self):
        """Assigns virtual index from 5' to 3' on strand and its complement
        location.
        """
        abstract_seq = []
        part = self.part()
        segment_dict = part.segment_dict[self._id_num]

        # make sure we apply numbers from 5' to 3'
        strand_order = 1 if self._is_forward else -1

        for segment in self.segments[::strand_order]:
            if segment in segment_dict:
                seg_id, offset, length = segment_dict[segment]
            else:
                seg_id, offset, length = part.getNewAbstractSegmentId(segment)
                segment_dict[segment] = (seg_id, offset, length)

            for i in range(length)[::strand_order]:
                abstract_seq.append(offset + i)
        self.abstract_sequence = abstract_seq
    # end def

    def copyAbstractSequenceToSequence(self):
        abstract_seq = self.abstract_sequence
        # self._sequence = ''.join([ascii_letters[i % 52] for i in abstract_seq])
        self._sequence = ''.join(['|' for i in abstract_seq])
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def connection3p(self) -> StrandT:
        return self._strand3p
    # end def

    def connection5p(self) -> StrandT:
        return self._strand5p
    # end def

    def idxs(self) -> SegmentT:
        return (self._base_idx_low, self._base_idx_high)
    # end def

    def lowIdx(self) -> int:
        return self._base_idx_low
    # end def

    def highIdx(self) -> int:
        return self._base_idx_high
    # end def

    def idx3Prime(self):
        """Returns the absolute base_idx of the 3' end of the strand.
        overloaded in __init__
        """
        # return self.idx3Prime

    def idx5Prime(self):
        """Returns the absolute base_idx of the 5' end of the strand.
        overloaded in __init__
        """
        # return self.idx5Prime

    def dump5p(self) -> Tuple[int, bool, int]:
        return self._id_num, self._is_forward, self.idx5Prime()
    # def

    def getSequenceList(self) -> List[Tuple[int, Tuple[str, str]]]:
        """return the list of sequences strings comprising the sequence and the
        inserts as a tuple with the index of the insertion
        [(idx, (strandItemString, insertionItemString), ...]

        This takes advantage of the fact the python iterates a dictionary
        by keys in order so if keys are indices, the insertions will iterate
        out from low index to high index
        """
        seq_list = []
        is_forward = self._is_forward
        seq = self._sequence if is_forward else self._sequence[::-1]
        # assumes a sequence has been applied correctly and is up to date
        tL = self.totalLength()

        offset_last = 0
        length_so_far = 0
        i_length = 0
        lI, hI = self.idxs()

        for insertion in self.insertionsOnStrand():
            i_length = insertion.length()
            index = insertion.idx()
            offset = index + 1 - lI + length_so_far
            if i_length < 0:
                offset -= 1
            # end if
            length_so_far += i_length
            seq_item = seq[offset_last:offset]  # the stranditem seq

            # Because skips literally skip displaying a character at a base
            # position, this needs to be accounted for seperately
            if i_length < 0:
                seq_item += ' '
                offset_last = offset
            else:
                offset_last = offset + i_length
            seq_insertion = seq[offset:offset_last]  # the insertions sequence
            seq_list.append((index, (seq_item, seq_insertion)))
        # end for
        # append the last bit of the strand
        seq_list.append((lI + tL, (seq[offset_last:tL], '')))
        if not is_forward:
            # reverse it again so all sub sequences are from 5' to 3'
            for i in range(len(seq_list)):
                index, temp = seq_list[i]
                seq_list[i] = (index, (temp[0][::-1], temp[1][::-1]))
        return seq_list
    # end def

    def canResizeTo(self, new_low: int, new_high: int) -> bool:
        """Checks to see if a resize is allowed. Similar to getResizeBounds
        but works for two bounds at once.

        Args:
            new_low: index
            new_high: index

        Returns:
            ``True`` if can resize, ``False`` otherwise
        """
        part = self.part()
        id_num = self._id_num
        low_neighbor, high_neighbor = self._strandset.getNeighbors(self)
        low_bound = low_neighbor.highIdx() if low_neighbor else 0
        high_bound = high_neighbor.lowIdx() if high_neighbor else part.maxBaseIdx(id_num)

        if new_low > low_bound and new_high < high_bound:
            return True
        return False

    def getResizeBounds(self, idx: int) -> SegmentT:
        """Determines (inclusive) low and high drag boundaries resizing
        from an endpoint located at idx.

        When resizing from _base_idx_low::

            low bound is determined by checking for lower neighbor strands.
            high bound is the index of this strand's high cap, minus 1.

        When resizing from _base_idx_high::

            low bound is the index of this strand's low cap, plus 1.
            high bound is determined by checking for higher neighbor strands.

        When a neighbor is not present, just use the Part boundary.

        Args:
            idx: index

        Returns:
            index bounds
        """
        part = self.part()
        neighbors = self._strandset.getNeighbors(self)
        if idx == self._base_idx_low:
            if neighbors[0] is not None:
                low = neighbors[0].highIdx() + 1
            else:
                low = 0
            # print("A", low, self._base_idx_high - 1 )
            return low, self._base_idx_high - 1
        else:  # self._base_idx_high
            if neighbors[1] is not None:
                high = neighbors[1].lowIdx() - 1
            else:
                high = part.maxBaseIdx(self._id_num)
            # print("B", self._base_idx_low+1, high)
            return self._base_idx_low + 1, high
    # end def

    def hasXoverAt(self, idx: int) -> bool:
        """An xover is necessarily at an enpoint of a strand
        """
        if idx == self.highIdx():
            return True if self.connectionHigh() is not None else False
        elif idx == self.lowIdx():
            return True if self.connectionLow() is not None else False
        else:
            return False
    # end def

    def canInstallXoverAt(self, idx: int,
                                from_strand: StrandT,
                                from_idx: int) -> bool:
        """Assumes idx is:
        self.lowIdx() <= idx <= self.highIdx()
        """

        if self.hasXoverAt(idx):
            return False
        ss = self.strandSet()
        is_same_strand = from_strand == self

        is_forward = ss.isForward()
        index_diff_H = self.highIdx() - idx
        index_diff_L = idx - self.lowIdx()
        idx3p = self.idx3Prime()
        idx5p = self.idx5Prime()
        # ensure 2 bps from 3p end if not the 3p end
        index3_lim = idx3p - 1 if is_forward else idx3p + 1

        if is_same_strand:
            index_diff_strands = from_idx - idx
            if idx == idx5p or idx == index3_lim:
                return True
            elif index_diff_strands > -3 and index_diff_strands < 3:
                return False
        # end if for same Strand
        else:
            from_idx3p = from_strand.idx3Prime()
            from_idx5p = from_strand.idx5Prime()
            if idx == idx5p or idx == index3_lim:
                if from_idx3p == from_idx:
                    return True
                elif (abs(from_idx3p - from_idx) > 1 and
                      abs(from_idx5p - from_idx) > 1):
                    return True
                else:
                    # print("this:", idx, idx3p, idx5p)
                    # print("from:", from_idx, from_idx3p, from_idx5p)
                    return False
            elif index_diff_H > 2 and index_diff_L > 1:
                if from_idx3p == from_idx:
                    return True
                elif (abs(from_idx3p - from_idx) > 1 and
                      abs(from_idx5p - from_idx) > 1):
                    return True
                else:
                    return False
            else:
                # print("default", index_diff_H, index_diff_L)
                return False
    # end def

    def insertionLengthBetweenIdxs(self, idx_low: int, idx_high: int) -> int:
        """includes the length of insertions in addition to the bases

        Args:
            idx_low: low index
            idx_high: high index

        Returns:
            total length
        """
        tL = 0
        insertions = self.insertionsOnStrand(idx_low, idx_high)
        for insertion in insertions:
            tL += insertion.length()
        return tL
    # end def

    def insertionsOnStrand(self, idx_low: int = None,
                                idx_high: int = None) -> List[InsertionT]:
        """if passed indices it will use those as a bounds

        Args:
            idx_low: low index
            idx_high: high index

        Returns:
            list of :class:`Insertion`
        """
        insertions = []
        insertionsDict = self.part().insertions()[self._id_num]
        sortedIndices = sorted(insertionsDict.keys())
        if idx_low is None:
            idx_low, idx_high = self.idxs()
        for index in sortedIndices:
            insertion = insertionsDict[index]
            if idx_low <= insertion.idx() <= idx_high:
                insertions.append(insertion)
            # end if
        # end for
        return insertions
    # end def

    def modifersOnStrand(self) -> List[dict]:
        """
        """
        mods = []
        modsDict = self.part().modifications()['ext_instances']
        id_num = self._id_num
        is_staple = True  # self.isStaple()
        idxL, idxH = self.idxs()
        keyL = "{},{},{}".format(id_num, is_staple, idxL)
        keyH = "{},{},{}".format(id_num, is_staple, idxH)
        if keyL in modsDict:
            mods.append(modsDict[keyL])
        if keyH in modsDict:
            mods.append(modsDict[keyH])
        return mods
    # end def

    def length(self) -> int:
        return self._base_idx_high - self._base_idx_low + 1
    # end def

    def totalLength(self) -> int:
        """includes the length of insertions in addition to the bases
        """
        tL = 0
        insertions = self.insertionsOnStrand()

        for insertion in insertions:
            tL += insertion.length()
        return tL + self.length()
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def addMods(self, document: DocT, mod_id: str, idx: int, use_undostack: bool = True):
        """Used to add mods during a merge operation."""
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low == idx or idx == idx_high:
            check_mid1 = self.part().getModID(self, idx)
            check_mid2 = document.getMod(mod_id)
            print("strand.addMods:", check_mid1, check_mid2)
            if check_mid2 is not None:
                if check_mid1 != mod_id:
                    if check_mid1 is not None:
                        cmds.append(RemoveModsCommand(document, self, idx, check_mid1))
                    # print("adding a {} modification at {}".format(mod_id, idx))
                    cmds.append(AddModsCommand(document, self, idx, mod_id))
                    util.execCommandList(self, cmds, desc="Add Modification",
                                         use_undostack=use_undostack)
                else:
                    print(check_mid1, mod_id)
        # end if
    # end def

    def removeMods(self, document: DocT, mod_id: str, idx: int, use_undostack: bool = True):
        """Used to add mods during a merge operation."""
        idx_low, idx_high = self.idxs()
        print("attempting to remove")
        if idx_low == idx or idx == idx_high:
            print("removing a modification at {}".format(idx))
            c = RemoveModsCommand(document, self, idx, mod_id)
            util.doCmd(self, c, use_undostack=use_undostack)
        # end if
    # end def

    def addInsertion(self, idx: int, length: int, use_undostack: bool = True):
        """Adds an insertion or skip at idx.
        length should be::

            >0 for an insertion
            -1 for a skip

        Args:
            idx (int):
            length (int):
            use_undostack (bool): optional, default is True
        """
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low <= idx <= idx_high:
            if not self.hasInsertionAt(idx):
                # make sure length is -1 if a skip
                if length < 0:
                    length = -1
                if use_undostack:   # on import no need to blank sequences
                    cmds.append(self.oligo().applySequenceCMD(None))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None))
                cmds.append(AddInsertionCommand(self, idx, length))
                util.execCommandList(self, cmds, desc="Add Insertion",
                                     use_undostack=use_undostack)
            # end if
        # end if
    # end def

    def changeInsertion(self, idx: int, length: int, use_undostack: bool = True):
        """
        Args:
            idx (int):
            length (int):
            use_undostack (bool): optional, default is True
        """
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
                    cmds.append(self.oligo().applySequenceCMD(None))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None))
                    cmds.append(ChangeInsertionCommand(self, idx, length))
                    util.execCommandList(self, cmds, desc="Change Insertion",
                                         use_undostack=use_undostack)
            # end if
        # end if
    # end def

    def removeInsertion(self, idx: int, use_undostack: bool = True):
        """
        Args:
            idx (int):
            use_undostack (bool): optional, default is True
        """
        cmds = []
        idx_low, idx_high = self.idxs()
        if idx_low <= idx <= idx_high:
            if self.hasInsertionAt(idx):
                if use_undostack:
                    cmds.append(self.oligo().applySequenceCMD(None))
                    for strand in self.getComplementStrands():
                        cmds.append(strand.oligo().applySequenceCMD(None))
                cmds.append(RemoveInsertionCommand(self, idx))
                util.execCommandList(self, cmds, desc="Remove Insertion",
                                     use_undostack=use_undostack)
            # end if
        # end if
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def

    def merge(self, idx: int):
        """Check for neighbor, then merge if possible.

        Args:
            idx (int):

        Raises:
            IndexError:
        """
        low_neighbor, high_neighbor = self._strandset.getNeighbors(self)
        # determine where to check for neighboring endpoint
        if idx == self._base_idx_low:
            if low_neighbor:
                if low_neighbor.highIdx() == idx - 1:
                    self._strandset.mergeStrands(self, low_neighbor)
        elif idx == self._base_idx_high:
            if high_neighbor:
                if high_neighbor.lowIdx() == idx + 1:
                    self._strandset.mergeStrands(self, high_neighbor)
        else:
            raise IndexError
    # end def

    def resize(self, new_idxs: SegmentT,
                    use_undostack: bool = True,
                    update_segments: bool = True):
        cmds = []

        # Delete sequences and remove inserations upon resize
        cmds.append(self.oligo().applySequenceCMD(None))
        cmds += self.getRemoveInsertionCommands(new_idxs)

        cmds.append(ResizeCommand(self, new_idxs, update_segments=update_segments))
        util.execCommandList(self, cmds, desc="Resize strand",
                             use_undostack=use_undostack)
    # end def

    def setConnection3p(self, strand: StrandT):
        self._strand3p = strand
    # end def

    def setConnection5p(self, strand: StrandT):
        self._strand5p = strand
    # end def

    def setIdxs(self, idxs: SegmentT):
        self._base_idx_low = idxs[0]
        self._base_idx_high = idxs[1]
    # end def

    def setOligo(self, new_oligo: OligoT, emit_signals: bool = False):
        self._oligo = new_oligo
        if emit_signals:
            self.strandHasNewOligoSignal.emit(self)
    # end def

    def split(self, idx: int, update_sequence: bool = True):
        """Called by view items to split this strand at idx."""
        self._strandset.splitStrand(self, idx, update_sequence)

    ### PUBLIC SUPPORT METHODS ###
    def getRemoveInsertionCommands(self, new_idxs: SegmentT):
        """Removes Insertions, Decorators, and Modifiers that have fallen out of
        range of new_idxs.

        For insertions, it finds the ones that have neither Staple nor Scaffold
        strands at the insertion idx as a result of the change of this
        strand to new_idxs

        """
        cIdxL, cIdxH = self.idxs()
        nIdxL, nIdxH = new_idxs

        # low_out, high_out = False, False
        insertions = []
        if cIdxL < nIdxL < cIdxH:
            idxL, idxH = cIdxL, nIdxL - 1
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            pass
        if cIdxL < nIdxH < cIdxH:
            idxL, idxH = nIdxH + 1, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
        else:
            pass
        # this only called if both the above aren't true
        # if low_out and high_out:
        # if we move the whole strand, just clear the insertions out
        if nIdxL > cIdxH or nIdxH < cIdxL:
            idxL, idxH = cIdxL, cIdxH
            insertions += self.insertionsOnStrand(idxL, idxH)
            # we stretched in this direction
        return self.clearInsertionsCommands(insertions, cIdxL, cIdxH)
    # end def

    def clearInsertionsCommands(self, insertions: Iterable[InsertionT],
                                    idx_low: int, idx_high: int) -> List[UndoCommand]:
        """clear out insertions in this range
        """
        commands = []
        comp_ss = self.strandSet().complementStrandSet()

        overlappingStrandList = comp_ss.getOverlappingStrands(idx_low, idx_high)
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

        # TODO ADD CODE HERE TO HANDLE DECORATORS AND MODIFIERS
        return commands
    # end def

    def clearDecoratorCommands(self):
        insertions = self.insertionsOnStrand()
        return self.clearInsertionsCommands(insertions, *self.idxs())
    # end def

    def hasInsertionAt(self, idx: int) -> bool:
        insts = self.part().insertions()[self._id_num]
        return idx in insts
    # end def

    def shallowCopy(self):
        """
        """
        new_s = Strand(self._strandset, *self.idxs())
        new_s._oligo = self._oligo
        new_s._strand5p = self._strand5p
        new_s._strand3p = self._strand3p
        # required to shallow copy the dictionary
        new_s._sequence = None  # self._sequence
        return new_s
    # end def

    def _deepCopy(self, strandset: StrandSetT, oligo: OligoT):
        """
        """
        new_s = Strand(strandset, *self.idxs())
        new_s._oligo = oligo
        new_s._sequence = self._sequence
        return new_s
    # end def
# end class
