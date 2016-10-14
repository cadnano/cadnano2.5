# -*- coding: utf-8 -*-
import sys
import traceback

from cadnano import util
from cadnano.cnobject import CNObject
from cadnano.cnproxy import ProxySignal
from cadnano.cnenum import ModType
from cadnano.strand import Strand
from .applycolorcmd import ApplyColorCommand
from .applysequencecmd import ApplySequenceCommand
from .removeoligocmd import RemoveOligoCommand
from cadnano.setpropertycmd import SetPropertyCommand

OLIGO_LEN_BELOW_WHICH_HIGHLIGHT = 18
OLIGO_LEN_ABOVE_WHICH_HIGHLIGHT = 50

PROPERTY_KEYS = ['name', 'color', 'length', 'is_visible']
ALL_KEYS = ['id_num', 'idx5p', 'is_loop'] + PROPERTY_KEYS


class Oligo(CNObject):
    """Oligo is a group of Strands that are connected via 5' and/or 3'
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
        self._is_loop = False
        self._props = {'name': "oligo%s" % str(id(self))[-4:],
                       'color': "#cc0000" if color is None else color,
                       'length': 0,
                       'is_visible': True
                       }
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
               'is_loop': self._is_loop,
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
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback, limit=5, file=sys.stdout)
            traceback.print_stack()
            sys.exit(0)
        return color
    # end def

    def _setColor(self, color):
        """ Set this oligos color

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

    def length(self):
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
            dict:
        """
        part = self.part()
        vh_num5p = self.strand5p().idNum()
        strand5p = self.strand5p()
        idx5p = strand5p.idx5Prime()
        seq = []
        a_seq = []
        if self.isLoop():
            # print("A loop exists")
            raise Exception
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
        if not self._strand5p:
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
        self._is_loop = bool
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def addToPart(self, part, emit_signals=False):
        self._part = part
        self.setParent(part)
        part._addOligoToSet(self, emit_signals)
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
        self._setLength(self.length() - delta)
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
        """This method sets the isLoop status of the oligo and the oligo's
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

    def _strandSplitUpdate(self, new_strand5p, new_strand3p, oligo3p, old_merged_strand):
        """If the oligo is a loop, splitting the strand does nothing. If the
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
