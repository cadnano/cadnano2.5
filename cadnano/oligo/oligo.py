# -*- coding: utf-8 -*-
import sys
import traceback

from cadnano import util
from cadnano.proxies.cnobject import CNObject
from cadnano.proxies.cnproxy import ProxySignal
from cadnano.proxies.cnenum import ModType
from cadnano.strand import Strand
from .applycolorcmd import ApplyColorCommand
from .applysequencecmd import ApplySequenceCommand
from .removeoligocmd import RemoveOligoCommand
from cadnano.setpropertycmd import SetPropertyCommand

OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 18
OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT = 60
MAX_HIGHLIGHT_LENGTH = 800

PROPERTY_KEYS = ['name', 'color', 'length', 'is_visible']
ALL_KEYS = ['id_num', 'idx5p', 'is_circular'] + PROPERTY_KEYS


class CircularOligoException(Exception):
    pass


class Oligo(CNObject):
    """
    Oligo is a group of Strands that are connected via 5' and/or 3'
    connections. It corresponds to the physical DNA strand, and is thus
    used tracking and storing properties that are common to a single strand,
    such as its color.

    Commands that affect Strands (e.g. create, remove, merge, split) are also
    responsible for updating the affected Oligos.

    Args:
        part (Part): the model :class:`Part`
        color (str): optional, color property of the :class:`Oligo`
    """
    editable_properties = ['name', 'color']

    def __init__(self, part, color=None, length=0):
        super(Oligo, self).__init__(part)
        self._part = part
        self._strand5p = None
        self._is_circular = False
        self._props = {'name': "oligo%s" % str(id(self))[-4:],
                       'color': "#cc0000" if color is None else color,
                       'length': length,
                       'is_visible': True
                       }
    # end def

    def __repr__(self):
        _name = self.__class__.__name__
        _id = str(id(self))[-4:]
        if self._strand5p is not None:
            vh_num = self._strand5p.idNum()
            idx = self._strand5p.idx5Prime()
            ss_type = self._strand5p.strandType()
        else:
            vh_num = -1
            idx = -1
            ss_type = -1
        oligo_identifier = '(%d.%d[%d])' % (vh_num, ss_type, idx)
        return '%s_%s_%s' % (_name, oligo_identifier, _id)
    # end def

    def __lt__(self, other):
        return self.length() < other.length()
    # end def

    def shallowCopy(self):
        olg = Oligo(self._part)
        olg._strand5p = self._strand5p
        olg._is_circular = self._is_circular
        olg._props = self._props.copy()
        # update the name
        olg._props['name'] = "oligo%s" % str(id(olg))[-4:]
        return olg
    # end def

    def dump(self):
        """ Return dictionary of this oligo and its properties.
        It's expected that caller will copy the properties
        if mutating

        Returns:
            dict:
        """
        s5p = self._strand5p
        key = {'id_num': s5p.idNum(),
               'idx5p': s5p.idx5Prime(),
               'is_5p_fwd': s5p.isForward(),
               'is_circular': self._is_circular,
               'sequence': self.sequence()}
        key.update(self._props)
        return key
    # end def

    ### SIGNALS ###
    oligoRemovedSignal = ProxySignal(CNObject, CNObject, name='oligoRemovedSignal')
    """part, self"""

    oligoSequenceAddedSignal = ProxySignal(CNObject, name='oligoSequenceAddedSignal')
    """self"""

    oligoSequenceClearedSignal = ProxySignal(CNObject, name='oligoSequenceClearedSignal')
    """self"""

    oligoPropertyChangedSignal = ProxySignal(CNObject, object, object, name='oligoPropertyChangedSignal')
    """self, property_name, new_value"""

    oligoSelectedChangedSignal = ProxySignal(CNObject, bool, name='oligoSelectedChangedSignal')
    """pyqtSignal(QObject, bool): (oligo, bool)"""
    ### SLOTS ###

    ### ACCESSORS ###
    def getProperty(self, key):
        return self._props[key]
    # end def

    def getOutlineProperties(self):
        """Convenience method for the outline view

        Returns:
            tuple: (<name>, <color>, <is_visible>)
        """
        props = self._props
        return props['name'], props['color'], props['is_visible']
    # end def

    def getModelProperties(self):
        """Return a reference to the property dictionary

        Returns:
            dict:
        """
        return self._props
    # end def

    def setProperty(self, key, value, use_undostack=True):
        if use_undostack:
            c = SetPropertyCommand([self], key, value)
            self.undoStack().push(c)
        else:
            self._setProperty(key, value)
    # end def

    def _setProperty(self, key, value, emit_signals=False):
        self._props[key] = value
        if emit_signals:
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
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
            traceback.print_stack()
            sys.exit(0)
        return color
    # end def

    def _setColor(self, color):
        """Set this oligo color.

        Args:
            color (str): format '#ffffff'
        """
        if color is None:
            raise ValueError("Whhat None???")
        self._props['color'] = color
    # end def

    def _setLength(self, length, emit_signals):
        before = self.shouldHighlight()
        key = 'length'
        self._props[key] = length
        if emit_signals and before != self.shouldHighlight():
            self.oligoSequenceClearedSignal.emit(self)
            self.oligoPropertyChangedSignal.emit(self, key, length)
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
        """The 5' strand is the first contiguous segment of the oligo,
        representing the region between the 5' base to the first crossover
        or 3' end.

        Returns:
            Strand: the 5'-most strand of the oligo.
        """
        return self._strand5p
    # end def

    def strand3p(self):
        """The 3' strand. The last strand in the oligo. See strand5p().

        Returns:
            Strand: the 3'-most strand of the oligo.
        """
        s5p = self._strand5p
        if self._is_circular:
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
    def isCircular(self):
        """Used for checking if an oligo is circular, or has a 5' and 3' end.
        Sequences cannot be exported of oligos for which isCircular returns True.
        See also: Oligo.sequenceExport().

        Returns:
            bool: True if the strand3p is connected to strand5p, else False.
        """
        return self._is_circular
    # end def

    def length(self):
        """
        The oligo length in bases.

        Returns:
            int: value from the oligo's property dict.
        """
        return self._props['length']
    # end def

    def sequence(self):
        """Get the sequence applied to this `Oligo`

        Returns:
            str or None
        """
        temp = self.strand5p()
        if not temp:
            return None
        if temp.sequence():
            return ''.join([Strand.sequence(strand)
                            for strand in self.strand5p().generator3pStrand()])
        else:
            return None
    # end def

    def sequenceExport(self, output):
        """ Iterative appending to argument `output` which is a dictionary of
        lists

        Args:
            output (dict): dictionary with keys given in `NucleicAcidPart.getSequences`

        Returns:
            dict: output with this oligo's values appended for each key
        """
        part = self.part()
        vh_num5p = self.strand5p().idNum()
        strand5p = self.strand5p()
        idx5p = strand5p.idx5Prime()
        seq = []
        a_seq = []
        if self.isCircular():
            # print("A loop exists")
            raise CircularOligoException("Cannot export circular oligo " + self.getName())
        for strand in strand5p.generator3pStrand():
            seq.append(Strand.sequence(strand, for_export=True))
            a_seq.append(Strand.abstractSeq(strand))
            if strand.connection3p() is None:  # last strand in the oligo
                vh_num3p = strand.idNum()
                idx3p = strand.idx3Prime()
        a_seq = ','.join(a_seq)
        a_seq = "(%s)" % (a_seq)
        modseq5p, modseq5p_name = part.getStrandModSequence(strand5p, idx5p,
                                                            ModType.END_5PRIME)
        modseq3p, modseq3p_name = part.getStrandModSequence(strand, idx3p,
                                                            ModType.END_3PRIME)
        seq = ''.join(seq)
        seq = modseq5p + seq + modseq3p
        # output = "%d[%d]\t%d[%d]\t%s\t%s\t%s\t%s\t(%s)\n" % \
        #          (vh_num5p, idx5p, vh_num3p, idx3p, self.getColor(),
        #           modseq5p_name, seq, modseq3p_name, a_seq)
        # these are the keys
        # keys = ['Start','End','Color', 'Mod5',
        #         'Sequence','Mod3','AbstractSequence']
        output['Start'].append("%d[%d]" % (vh_num5p, idx5p))
        output['End'].append("%d[%d]" % (vh_num3p, idx3p))
        output['Color'].append(self.getColor())
        output['Mod5'].append(modseq5p_name)
        output['Sequence'].append(seq)
        output['Mod3'].append(modseq3p_name)
        output['AbstractSequence'].append(a_seq)
        return output
    # end def

    def shouldHighlight(self):
        """
        Checks if oligo's length falls within the range specified by
        OLIGO_LEN_BELOW_WHICH_HIGHLIGHT and OLIGO_LEN_BELOW_WHICH_HIGHLIGHT.

        Returns:
            bool: True if circular or length outside acceptable range,
            otherwise False.
        """
        if not self._strand5p:
            return True
        if self.length() > MAX_HIGHLIGHT_LENGTH:
            return False
        if self.length() < OLIGO_LEN_BELOW_WHICH_HIGHLIGHT:
            return True
        if self.length() > OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT:
            return True
        return False
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def remove(self, use_undostack=True):
        c = RemoveOligoCommand(self)
        util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def applyAbstractSequences(self):
        temp = self.strand5p()
        if not temp:
            return
        for strand in temp.generator3pStrand():
            strand.applyAbstractSequence()
    # end def

    def clearAbstractSequences(self):
        temp = self.strand5p()
        if not temp:
            return
        for strand in temp.generator3pStrand():
            strand.clearAbstractSequence()
    # end def

    def displayAbstractSequences(self):
        temp = self.strand5p()
        if not temp:
            return
        for strand in temp.generator3pStrand():
            strand.copyAbstractSequenceToSequence()
    # end def

    def applyColor(self, color, use_undostack=True):
        if color == self.getColor():
            return  # oligo already has this color
        c = ApplyColorCommand(self, color)
        util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def applySequence(self, sequence, use_undostack=True):
        c = ApplySequenceCommand(self, sequence)
        util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def applySequenceCMD(self, sequence):
        return ApplySequenceCommand(self, sequence)
    # end def

    def _setLoop(self, bool):
        self._is_circular = bool
    # end def

    def getStrandLengths(self):
        """
        Traverses the oligo and builds up a list of each strand's total length,
        which also accounts for any insertions, deletions, or modifications.

        Returns:
            list: lengths of individual strands in the oligo
        """
        strand5p = self.strand5p()
        strand_lengths = []
        for strand in strand5p.generator3pStrand():
            strand_lengths.append(strand.totalLength())
        return strand_lengths

    def getNumberOfBasesToEachXover(self, use_3p_idx=False):
        """
        Convenience method to get a list of absolute distances from the 5' end
        of the oligo to each of the xovers in the oligo.

        Args:
            use_3p_idx: Adds a 1-base office to return 3' xover idx instead of
        """
        strand5p = self.strand5p()
        num_bases_to_xovers = []
        offset = 1 if use_3p_idx else 0  # 3p xover idx is always the next base
        i = 0
        for strand in strand5p.generator3pStrand():
            if strand.connection3p():
                i = i + strand.totalLength()
                num_bases_to_xovers.append(i+offset)
        return num_bases_to_xovers

    def splitAtAbsoluteLengths(self, len_list):
        self._part.splitOligoAtAbsoluteLengths(self, len_list)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def addToPart(self, part, emit_signals=False):
        self._part = part
        self.setParent(part)
        part._addOligoToSet(self, emit_signals)
    # end def

    def getAbsolutePositionAtLength(self, len_for_pos):
        """
        Convenience method convert the length in bases from the 5' end of the
        oligo to the absolute position (vh, strandset, baseidx).

        Args:
            len_for_pos: length in bases for position lookup
        """
        strand5p = self.strand5p()
        temp_len = 0
        for strand in strand5p.generator3pStrand():
            if (temp_len + strand.totalLength()) > len_for_pos:
                vh = strand.idNum()
                strandset = strand.strandType()
                baseidx = strand.idx5Prime() + len_for_pos - temp_len
                return (vh, strandset, baseidx)
            else:
                temp_len += strand.totalLength()
        return None
    # end def

    def setPart(self, part):
        self._part = part
        self.setParent(part)
    # end def

    def destroy(self):
        # QObject also emits a destroyed() Signal
        # self.setParent(None)
        # self.deleteLater()
        cmds = []
        s5p = self._strand5p
        for strand in s5p.generator3pStrand():
            cmds += strand.clearDecoratorCommands()
        # end for
        cmds.append(RemoveOligoCommand(self))
        return cmds
    # end def

    def _decrementLength(self, delta, emit_signals):
        self._setLength(self.length() - delta, emit_signals)
    # end def

    def _incrementLength(self, delta, emit_signals):
        self._setLength(self.length() + delta, emit_signals)
    # end def

    def refreshLength(self, emit_signals=False):
        temp = self.strand5p()
        if not temp:
            return
        length = 0
        for strand in temp.generator3pStrand():
            length += strand.totalLength()
        self._setLength(length, emit_signals)
    # end def

    def removeFromPart(self, emit_signals=False):
        """This method merely disconnects the object from the model.
        It still lives on in the undoStack until clobbered

        Note: don't set self._part = None because we need to continue passing
        the same reference around.
        """
        self._part._removeOligoFromSet(self, emit_signals)
        self.setParent(None)
    # end def

    def _strandMergeUpdate(self, old_strand_low, old_strand_high, new_strand):
        """This method sets the isCircular status of the oligo and the oligo's
        5' strand.
        """
        # check loop status
        if old_strand_low.oligo() == old_strand_high.oligo():
            self._is_circular = True
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

    def _strandSplitUpdate(self, new_strand5p, new_strand3p, oligo3p, old_merged_strand):
        """If the oligo is a loop, splitting the strand does nothing. If the
        oligo isn't a loop, a new oligo must be created and assigned to the
        new_strand and everything connected to it downstream.
        """
        # if you split it can't be a loop
        self._is_circular = False
        if old_merged_strand.oligo().isCircular():
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
