import random
from collections import defaultdict
from heapq import heapify, heappush, heappop
from itertools import product, islice
from uuid import uuid4
izip = zip

from cadnano import util
from cadnano import preferences as prefs
from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.cnproxy import UndoCommand
from cadnano.enum import PartType, StrandType
from cadnano.oligo import Oligo
from cadnano.oligo import RemoveOligoCommand
from cadnano.part.part import Part
from cadnano.strand import Strand
from cadnano.strandset import CreateStrandCommand, RemoveStrandCommand
from cadnano.strandset import SplitCommand
from cadnano.strandset import StrandSet
from cadnano.virtualhelix import RemoveVirtualHelixCommand
from cadnano.virtualhelix import VirtualHelix
from .createvhelixcmd import CreateVirtualHelixCommand
from .pmodscmd import AddModCommand, RemoveModCommand, ModifyModCommand
from .resizepartcmd import ResizePartCommand
from .refresholigoscmd import RefreshOligosCommand
from .removepartcmd import RemovePartCommand
from .renumbercmd import RenumberVirtualHelicesCommand
from .xovercmds import CreateXoverCommand, RemoveXoverCommand

class NucleicAcidPart(Part):
    """
    NucleicAcidPart is a group of VirtualHelix items that are on the same lattice.
    The NucleicAcidPart model component is different from the OrigamiPart:

    - it does not enforce distinction between scaffold and staple strands
    - specific crossover types are not enforced (i.e. antiparallel)
    - sequence output is more abstract ("virtual sequences" are used)
    """

    _STEP = 21  # this is the period (in bases) of the part lattice
    _RADIUS = 1.125  # nanometers
    _TURNS_PER_STEP = 2
    _HELICAL_PITCH = _STEP / _TURNS_PER_STEP
    _TWIST_PER_BASE = 360 / _HELICAL_PITCH  # degrees

    __count = 0

    @classmethod
    def _count(cls):
        NucleicAcidPart.__count += 1
        return NucleicAcidPart.__count

    def __init__(self, *args, **kwargs):
        """
        Sets the parent document, sets bounds for part dimensions, and sets up
        bookkeeping for partInstances, Oligos, VirtualHelix's, and helix ID
        number assignment.
        """
        # if self.__class__ == Part:
        #     e = "This class is abstract. Perhaps you want HoneycombPart."
        #     raise NotImplementedError(e)
        self._document = kwargs.get('document', None)
        super(NucleicAcidPart, self).__init__(*args, **kwargs)
        # Data structure
        self._insertions = defaultdict(dict)  # dict of insertions per virtualhelix
        self._mods = defaultdict(dict)
        self._oligos = set()
        self._coord_to_virtual_velix = {}
        self._number_to_virtual_helix = {}
        # Dimensions
        self._max_row = 50  # subclass overrides based on prefs
        self._max_col = 50
        self._min_base = 0
        self._max_base = 2 * self._STEP - 1
        # Properties (NucleicAcidPart-specific)
        # self._properties["name"] = "Origami%d" % len(self._document.children())
        self._properties["name"] = "Origami%d" % self._count()
        # ID assignment
        self.odd_recycle_bin, self.even_recycle_bin = [], []
        self.reserve_bin = set()
        self._highest_used_odd = -1  # Used in _reserveHelixIDNumber
        self._highest_used_even = -2  # same
        self._imported_vh_order = []
        # Runtime state
        self._active_base_index = self._STEP
        self._active_virtual_helix = None
        self._active_virtual_helix_idx = None

    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###
    partActiveSliceIndexSignal = ProxySignal(ProxyObject, int,
                        name='partActiveSliceIndexSignal')      #(self, index)
    partActiveSliceResizeSignal = ProxySignal(ProxyObject,
                        name='partActiveSliceResizeSignal')     # self
    partDimensionsChangedSignal = ProxySignal(ProxyObject,
                        name='partDimensionsChangedSignal')     # self
    partInstanceAddedSignal = ProxySignal(ProxyObject,
                        name='partInstanceAddedSignal')         # self
    partParentChangedSignal = ProxySignal(ProxyObject,
                        name='partParentChangedSignal')         # self
    partPreDecoratorSelectedSignal = ProxySignal(object, int, int, int,
                        name='partPreDecoratorSelectedSignal')  # self, row, col, idx
    partRemovedSignal = ProxySignal(ProxyObject,
                        name='partRemovedSignal')               # self
    partStrandChangedSignal = ProxySignal(object, ProxyObject,
                        name='partStrandChangedSignal')         # self, virtual_helix
    # partVirtualHelixAddedSignal = ProxySignal(object, ProxyObject,
    #                     name='partVirtualHelixAddedSignal')     # self, virtualhelix
    partVirtualHelixAddedSignal = ProxySignal(object, object,
                        name='partVirtualHelixAddedSignal')     # self, virtualhelix
    partVirtualHelixRenumberedSignal = ProxySignal(object, tuple,
                        name='partVirtualHelixRenumberedSignal')# self, coord
    partVirtualHelixResizedSignal = ProxySignal(object, tuple,
                        name='partVirtualHelixResizedSignal')   # self, coord
    partVirtualHelicesReorderedSignal = ProxySignal(object, list, bool,
                        name='partVirtualHelicesReorderedSignal') # self, list of coords
    partActiveVirtualHelixChangedSignal = ProxySignal(ProxyObject, ProxyObject,
                        name='partActiveVirtualHelixChangedSignal')
    partModAddedSignal = ProxySignal(object, object, object,
                        name='partModAddedSignal')
    partModRemovedSignal = ProxySignal(object, object,
                        name='partModRemovedSignal')
    partModChangedSignal = ProxySignal(object, object, object,
                        name='partModChangedSignal')

    ### SLOTS ###

    ### ACCESSORS ###
    def document(self):
        return self._document
    # end def

    def oligos(self):
        return self._oligos
    # end def

    def setDocument(self, document):
        self._document = document
    # end def

    def stepSize(self):
        return self._STEP
    # end def

    def subStepSize(self):
        """Note: _SUB_STEP_SIZE is defined in subclasses."""
        return self._SUB_STEP_SIZE
    # end def

    def undoStack(self):
        return self._document.undoStack()
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def partType(self):
        return PartType.NUCLEICACIDPART
    # end def

    def virtualHelix(self, vhref, returnNoneIfAbsent=True):
        # vhrefs are the shiny new way to talk to part about its constituent
        # virtualhelices. Wherever you see f(...,vhref,...) you can
        # f(...,27,...)         use the virtualhelix's id number
        # f(...,vh,...)         use an actual virtualhelix
        # f(...,(1,42),...)     use the coordinate representation of its position
        """A vhref is the number of a virtual helix, the (row, col) of a virtual helix,
        or the virtual helix itself. For conveniece, CRUD should now work with any of them."""
        vh = None
        if type(vhref) in (int,):
            vh = self._number_to_virtual_helix.get(vhref, None)
        elif type(vhref) in (tuple, list):
            vh = self._coord_to_virtual_velix.get(vhref, None)
        else:
            vh = vhref
        if not isinstance(vh, VirtualHelix):
            if returnNoneIfAbsent:
                return None
            else:
                err = "Couldn't find the virtual helix in part %s "+\
                      "referenced by index %s" % (self, vhref)
                raise IndexError(err)
        return vh
    # end def

    def iterVHs(self):
        dcvh = self._coord_to_virtual_velix
        for coord, vh in dcvh.items():
            yield coord, vh
    # end def

    def activeBaseIndex(self):
        return self._active_base_index
    # end def

    def activeVirtualHelix(self):
        return self._active_virtual_helix
     # end def

    def activeVirtualHelixIdx(self):
        return self._active_virtual_helix_idx
     # end def

    def dimensions(self, scale_factor=1.0):
        """Returns a tuple of the max X and maxY coordinates of the lattice."""
        return self.latticeCoordToPositionXY(self._max_row, self._max_col, scale_factor)
    # end def

    def getStapleSequences(self):
        """getStapleSequences"""
        s = "Start,End,Sequence,Length,Color\n"
        for oligo in self._oligos:
            if oligo.strand5p().strandSet().isStaple():
                s = s + oligo.sequenceExport()
        return s

    def getVirtualHelices(self):
        """yield an iterator to the virtual_helix references in the part"""
        return self._coord_to_virtual_velix.values()
    # end def

    def indexOfRightmostNonemptyBase(self):
        """
        During reduction of the number of bases in a part, the first click
        removes empty bases from the right hand side of the part (red
        left-facing arrow). This method returns the new numBases that will
        effect that reduction.
        """
        ret = self._STEP - 1
        for vh in self.getVirtualHelices():
            ret = max(ret, vh.indexOfRightmostNonemptyBase())
        return ret
    # end def

    def insertions(self):
        """Return dictionary of insertions."""
        return self._insertions
    # end def

    def isEvenParity(self, row, column):
        """Should be overridden when subclassing."""
        raise NotImplementedError
    # end def

    def getStapleLoopOligos(self):
        """
        Returns staple oligos with no 5'/3' ends. Used by
        actionExportSequencesSlot in documentcontroller to validate before
        exporting staple sequences.
        """
        stap_loop_olgs = []
        for o in list(self.oligos()):
            if o.isStaple() and o.isLoop():
                stap_loop_olgs.append(o)
        return stap_loop_olgs

    def hasVirtualHelixAtCoord(self, coord):
        return coord in self._coord_to_virtual_velix
    # end def

    def maxBaseIdx(self):
        return self._max_base
    # end def

    def minBaseIdx(self):
        return self._min_base
    # end def

    def numberOfVirtualHelices(self):
        return len(self._coord_to_virtual_velix)
    # end def

    def radius(self):
        return self._RADIUS
    # end def

    def helicalPitch(self):
        return self._HELICAL_PITCH
    # end def

    def twistPerBase(self):
        return self._TWIST_PER_BASE
    # end def

    def virtualHelixAtCoord(self, coord):
        """
        Looks for a virtual_helix at the coordinate, coord = (row, colum)
        if it exists it is returned, else None is returned
        """
        try:
            return self._coord_to_virtual_velix[coord]
        except:
            return None
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def autoStaple(part, is_slow=True):
        """Autostaple does the following:
        1. Clear existing staple strands by iterating over each strand
        and calling RemoveStrandCommand on each. The next strand to remove
        is always at index 0.
        2. Create temporary strands that span regions where scaffold is present.
        3. Determine where actual strands will go based on strand overlap with
        prexovers.
        4. Delete temporary strands and create new strands.

        is_slow: True --> undoable
                : False --> not undoable
        """
        ep_dict = {}  # keyed on StrandSet
        cmds = []

        # clear existing staple strands
        # part.verifyOligos()

        for o in list(part.oligos()):
            if not o.isStaple():
                continue
            c = RemoveOligoCommand(o)
            cmds.append(c)
        # end for
        util.execCommandList(part, cmds, desc="Clear staples",
                                            use_undostack=False)
        cmds = []

        # create strands that span all bases where scaffold is present
        for vh in part.getVirtualHelices():
            segments = []
            scaf_ss = vh.scaffoldStrandSet()
            for strand in scaf_ss:
                lo, hi = strand.idxs()
                if len(segments) == 0:
                    segments.append([lo, hi])  # insert 1st strand
                elif segments[-1][1] == lo - 1:
                    segments[-1][1] = hi  # extend
                else:
                    segments.append([lo, hi])  # insert another strand
            stap_ss = vh.stapleStrandSet()
            ep_dict[stap_ss] = []
            for i in range(len(segments)):
                lo, hi = segments[i]
                ep_dict[stap_ss].extend(segments[i])
                c = CreateStrandCommand(stap_ss, lo, hi)
                cmds.append(c)
        util.execCommandList(part, cmds, desc="Add tmp strands",
                                use_undostack=False)
        cmds = []

        # determine where xovers should be installed
        for vh in part.getVirtualHelices():
            stap_ss = vh.stapleStrandSet()
            scaf_ss = vh.scaffoldStrandSet()
            is5to3 = stap_ss.isDrawn5to3()
            potential_xovers = part.potentialCrossoverList(vh)
            for neighbor_vh, idx, strand_type, is_low_idx in potential_xovers:
                if strand_type != StrandType.STAPLE:
                    continue
                if is_low_idx and is5to3:
                    strand = stap_ss.getStrand(idx)
                    neighbor_ss = neighbor_vh.stapleStrandSet()
                    n_strand = neighbor_ss.getStrand(idx)
                    if strand is None or n_strand is None:
                        continue
                    # check for bases on both strands at [idx-1:idx+3]
                    if not (strand.lowIdx() < idx and strand.highIdx() > idx + 1):
                        continue
                    if not (n_strand.lowIdx() < idx and n_strand.highIdx() > idx + 1):
                        continue

                    # # check for nearby scaffold xovers
                    # scaf_strand_L = scaf_ss.getStrand(idx-4)
                    # scaf_strand_H = scaf_ss.getStrand(idx+5)
                    # if scaf_strand_L:
                    #     if scaf_strand_L.hasXoverAt(idx-4):
                    #         continue
                    # if scaf_strand_H:
                    #     if scaf_strand_H.hasXoverAt(idx+5):
                    #         continue

                    # Finally, add the xovers to install
                    ep_dict[stap_ss].extend([idx, idx+1])
                    ep_dict[neighbor_ss].extend([idx, idx+1])

        # clear temporary staple strands
        for vh in part.getVirtualHelices():
            stap_ss = vh.stapleStrandSet()
            for strand in stap_ss:
                c = RemoveStrandCommand(stap_ss, strand)
                cmds.append(c)
        util.execCommandList(part, cmds, desc="Rm tmp strands",
                                        use_undostack=False)
        cmds = []

        if is_slow:
            part.undoStack().beginMacro("Auto-Staple")

        for stap_ss, ep_list in ep_dict.items():
            assert (len(ep_list) % 2 == 0)
            ep_list = sorted(ep_list)
            for i in range(0, len(ep_list),2):
                lo, hi = ep_list[i:i+2]
                c = CreateStrandCommand(stap_ss, lo, hi)
                cmds.append(c)
        util.execCommandList(part, cmds, desc="Create strands",
                                use_undostack=is_slow)
        cmds = []

        # create crossovers wherever possible (from strand5p only)
        for vh in part.getVirtualHelices():
            stap_ss = vh.stapleStrandSet()
            is5to3 = stap_ss.isDrawn5to3()
            potential_xovers = part.potentialCrossoverList(vh)
            for neighbor_vh, idx, strand_type, is_low_idx in potential_xovers:
                if strand_type != StrandType.STAPLE:
                    continue
                if (is_low_idx and is5to3) or (not is_low_idx and not is5to3):
                    strand = stap_ss.getStrand(idx)
                    neighbor_ss = neighbor_vh.stapleStrandSet()
                    n_strand = neighbor_ss.getStrand(idx)
                    if strand is None or n_strand is None:
                        continue
                    if idx in strand.idxs() and idx in n_strand.idxs():
                        # only install xovers on pre-split strands
                        part.createXover(strand, idx, n_strand, idx,
                                            update_oligo=is_slow,
                                            use_undostack=is_slow)

        if not is_slow:
            c = RefreshOligosCommand(part)
            cmds.append(c)
            util.execCommandList(part, cmds, desc="Assign oligos",
                                            use_undostack=False)

        cmds = []
        if is_slow:
            part.undoStack().endMacro()
        else:
            part.undoStack().clear()
    # end def

    def verifyOligoStrandCounts(self):
        total_stap_strands = 0
        stapOligos = set()
        total_stap_oligos = 0

        for vh in self.getVirtualHelices():
            stap_ss = vh.stapleStrandSet()
            total_stap_strands += stap_ss.strandCount()
            for strand in stap_ss:
                stapOligos.add(strand.oligo())
        # print("# stap oligos:", len(stapOligos), "# stap strands:", total_stap_strands)
    # end def

    def verifyOligos(self):
        total_errors = 0
        total_passed = 0

        for o in list(self.oligos()):
            o_l = o.length()
            a = 0
            gen = o.strand5p().generator3pStrand()

            for s in gen:
                a += s.totalLength()
            # end for
            if o_l != a:
                total_errors += 1
                # print("wtf", total_errors, "oligo_l", o_l, "strandsL", a, "isStaple?", o.isStaple())
                o.applyColor('#ff0000')
            else:
                total_passed += 1
        # end for
        # print("Total Passed: ", total_passed, "/", total_passed+total_errors)
    # end def

    def removeVirtualHelices(self, use_undostack=True):
        vhs = [vh for vh in self._coord_to_virtual_velix.values()]
        for vh in vhs:
            vh.remove(use_undostack)
        # end for
    # end def

    def remove(self, use_undostack=True):
        """
        This method assumes all strands are and all VirtualHelices are
        going away, so it does not maintain a valid model state while
        the command is being executed.
        Everything just gets pushed onto the undostack more or less as is.
        Except that strandSets are actually cleared then restored, but this
        is neglible performance wise.  Also, decorators/insertions are assumed
        to be parented to strands in the view so their removal Signal is
        not emitted.  This causes problems with undo and redo down the road
        but works as of now.
        """
        self._active_virtual_helix = None
        if use_undostack:
            self.undoStack().beginMacro("Delete Part")
        # remove strands and oligos
        self.removeAllOligos(use_undostack)
        # remove VHs
        vhs = [v for v in self._coord_to_virtual_velix.values()]
        for vh in vhs:
            d = RemoveVirtualHelixCommand(self, vh)
            if use_undostack:
                self.undoStack().push(d)
            else:
                d.redo()
        # end for
        # remove the part
        e = RemovePartCommand(self)
        if use_undostack:
            self.undoStack().push(e)
            self.undoStack().endMacro()
        else:
            e.redo()
    # end def

    def removeAllOligos(self, use_undostack=True):
        # clear existing oligos
        cmds = []
        for o in list(self.oligos()):
            cmds.append(RemoveOligoCommand(o))
        # end for
        util.execCommandList(self, cmds, desc="Clear oligos", use_undostack=use_undostack)
    # end def

    def addOligo(self, oligo):
        # print("adding oligo", oligo)
        self._oligos.add(oligo)
    # end def

    def createVirtualHelix(self, row, col, use_undostack=True):
        c = CreateVirtualHelixCommand(self, row, col)
        util.execCommandList(self, [c], desc="Add VirtualHelix", \
                                                use_undostack=use_undostack)
    # end def

    def createXover(self, strand5p, idx5p, strand3p, idx3p, update_oligo=True, use_undostack=True):
        # prexoveritem needs to store left or right, and determine
        # locally whether it is from or to
        # pass that info in here in and then do the breaks
        if not strand3p.canInstallXoverAt(idx3p, strand5p, idx5p):
            print("createXover: no xover can be installed here")
            return

        ss5p = strand5p.strandSet()
        ss3p = strand3p.strandSet()

        # commenting out if statement below allows scaf-to-stap xovers
        # if ss5p.strandType() != ss3p.strandType():
        #     return

        if use_undostack:
            self.undoStack().beginMacro("Create Xover")
        if ss5p.isScaffold() and use_undostack:  # ignore on import
            strand5p.oligo().applySequence(None)
            strand3p.oligo().applySequence(None)
        if strand5p == strand3p:
            """
            This is a complicated case basically we need a truth table.
            1 strand becomes 1, 2 or 3 strands depending on where the xover is
            to.  1 and 2 strands happen when the xover is to 1 or more existing
            endpoints.  Since SplitCommand depends on a StrandSet index, we need
            to adjust this strandset index depending which direction the
            crossover is going in.

            Below describes the 3 strand process
            1) Lookup the strands strandset index (ss_idx)
            2) Split attempted on the 3 prime strand, AKA 5prime endpoint of
            one of the new strands.  We have now created 2 strands, and the
            ss_idx is either the same as the first lookup, or one more than it
            depending on which way the the strand is drawn (isDrawn5to3).  If a
            split occured the 5prime strand is definitely part of the 3prime
            strand created in this step
            3) Split is attempted on the resulting 2 strands.  There is now 3
            strands, and the final 3 prime strand may be one of the two new
            strands created in this step. Check it.
            4) Create the Xover
            """
            c = None
            # lookup the initial strandset index
            if strand3p.idx5Prime() == idx3p:  # yes, idx already matches
                temp5 = xo_strand3 = strand3p
            else:
                offset3p = -1 if ss3p.isDrawn5to3() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    c = SplitCommand(strand3p, idx3p + offset3p)
                    # cmds.append(c)
                    xo_strand3 = c._strand_high if ss3p.isDrawn5to3() else c._strand_low
                    # adjust the target 5prime strand, always necessary if a split happens here
                    if idx5p > idx3p and ss3p.isDrawn5to3():
                        temp5 = xo_strand3
                    elif idx5p < idx3p and not ss3p.isDrawn5to3():
                        temp5 = xo_strand3
                    else:
                        temp5 = c._strand_low if ss3p.isDrawn5to3() else c._strand_high
                    if use_undostack:
                        self.undoStack().push(c)
                    else:
                        c.redo()
                else:
                    if use_undostack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return
                # end if
            if xo_strand3.idx3Prime() == idx5p:
                xo_strand5 = temp5
            else:
                ss_idx5p = ss_idx3p
                """
                if the strand was split for the strand3p, then we need to
                adjust the strandset index
                """
                if c:
                    # the insertion index into the set is increases
                    if ss3p.isDrawn5to3():
                        ss_idx5p = ss_idx3p + 1 if idx5p > idx3p else ss_idx3p
                    else:
                        ss_idx5p = ss_idx3p + 1 if idx5p > idx3p else ss_idx3p
                if ss5p.strandCanBeSplit(temp5, idx5p):
                    d = SplitCommand(temp5, idx5p)
                    # cmds.append(d)
                    xo_strand5 = d._strand_low if ss5p.isDrawn5to3() else d._strand_high
                    if use_undostack:
                        self.undoStack().push(d)
                    else:
                        d.redo()
                    # adjust the target 3prime strand, IF necessary
                    if idx5p > idx3p and ss3p.isDrawn5to3():
                        xo_strand3 = xo_strand5
                    elif idx5p < idx3p and not ss3p.isDrawn5to3():
                        xo_strand3 = xo_strand5
                else:
                    if use_undostack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    return
        # end if
        else:  # Do the following if it is in fact a different strand
            # is the 5' end ready for xover installation?
            if strand3p.idx5Prime() == idx3p:  # yes, idx already matches
                xo_strand3 = strand3p
            else:  # no, let's try to split
                offset3p = -1 if ss3p.isDrawn5to3() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    if ss3p.getStrandIndex(strand3p)[0]:
                        c = SplitCommand(strand3p, idx3p + offset3p)
                        # cmds.append(c)
                        xo_strand3 = c._strand_high if ss3p.isDrawn5to3() else c._strand_low
                        if use_undostack:
                            self.undoStack().push(c)
                        else:
                            c.redo()
                else:  # can't split... abort
                    if use_undostack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    raise ValueError("createXover: invalid call can't split abort 2")
                    return

            # is the 3' end ready for xover installation?
            if strand5p.idx3Prime() == idx5p:  # yes, idx already matches
                xo_strand5 = strand5p
            else:
                if ss5p.strandCanBeSplit(strand5p, idx5p):
                    if ss5p.getStrandIndex(strand5p)[0]:
                        d = SplitCommand(strand5p, idx5p)
                        # cmds.append(d)
                        xo_strand5 = d._strand_low if ss5p.isDrawn5to3() else d._strand_high
                        if use_undostack:
                            self.undoStack().push(d)
                        else:
                            d.redo()
                else:  # can't split... abort
                    if use_undostack:
                        self.undoStack().endMacro()
                        # unclear the applied sequence
                        if self.undoStack().canUndo() and ss5p.isScaffold():
                            self.undoStack().undo()
                    raise ValueError("createXover: invalid call can't split abort 2")
                    return
        # end else
        e = CreateXoverCommand(self, xo_strand5, idx5p,
                xo_strand3, idx3p, update_oligo=update_oligo)
        if use_undostack:
            self.undoStack().push(e)
            self.undoStack().endMacro()
        else:
            e.redo()
    # end def

    def removeXover(self, strand5p, strand3p, use_undostack=True):
        cmds = []
        if strand5p.connection3p() == strand3p:
            c = RemoveXoverCommand(self, strand5p, strand3p)
            cmds.append(c)
            util.execCommandList(self, cmds, desc="Remove Xover", \
                                                    use_undostack=use_undostack)
    # end def

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
    # end def



    def generatorFullLattice(self):
        """
        Returns a generator that yields the row, column lattice points to draw
        relative to the part origin.
        """
        return product(range(self._max_row), range(self._max_col))
    # end def

    def generatorSpatialLattice(self, scale_factor=1.0):
        """
        Returns a generator that yields the XY spatial lattice points to draw
        relative to the part origin.
        """
        # nested for loop in one line
        latticeCoordToPositionXY = self.latticeCoordToPositionXY
        for latticeCoord in product(range(self._max_row), range(self._max_col)):
            row, col = latticeCoord
            x, y = latticeCoordToPositionXY(row, col, scale_factor)
            yield x, y, row, col
    # end def

    def getPreXoversHigh(self, strand_type, neighbor_type, min_idx=0, max_idx=None):
        """
        Returns all prexover positions for neighbor_type that are below
        max_idx. Used in emptyhelixitem.py.
        """
        pre_xo = self._SCAFH if strand_type == StrandType.SCAFFOLD else self._STAPH
        if max_idx is None:
            max_idx = self._max_base
        steps = (self._max_base // self._STEP) + 1
        ret = [i * self._STEP + j for i in range(steps) for j in pre_xo[neighbor_type]]
        return filter(lambda x: x >= min_idx and x <= max_idx, ret)

    def getPreXoversLow(self, strand_type, neighbor_type, min_idx=0, max_idx=None):
        """
        Returns all prexover positions for neighbor_type that are above
        min_idx. Used in emptyhelixitem.py.
        """
        pre_xo = self._SCAFL if strand_type == StrandType.SCAFFOLD \
                                else self._STAPL
        if max_idx is None:
            max_idx = self._max_base
        steps = (self._max_base // self._STEP) + 1
        ret = [i * self._STEP + j for i in range(steps) for j in pre_xo[neighbor_type]]
        return filter(lambda x: x >= min_idx and x <= max_idx, ret)

    def latticeCoordToPositionXY(self, row, col, scale_factor=1.0, normalize=False):
        """
        Returns a tuple of the (x,y) position for a given lattice row and
        column.

        Note: The x,y position is the upperLeftCorner for the given
        coordinate, and relative to the part instance.
        """
        raise NotImplementedError  # To be implemented by Part subclass
    # end def

    def xoverSnapTo(self, strand, idx, delta):
        """
        Returns the nearest xover position to allow snap-to behavior in
        resizing strands via dragging selected xovers.
        """
        strand_type = strand.strandType()
        if delta > 0:
            min_idx, max_idx = idx - delta, idx + delta
        else:
            min_idx, max_idx = idx + delta, idx - delta

        # determine neighbor strand and bind the appropriate prexover method
        lo, hi = strand.idxs()
        if idx == lo:
            connected_strand = strand.connectionLow()
            preXovers = self.getPreXoversHigh
        else:
            connected_strand = strand.connectionHigh()
            preXovers = self.getPreXoversLow
        connected_vh = connected_strand.virtualHelix()

        # determine neighbor position, if any
        neighbors = self.getVirtualHelixNeighbors(strand.virtualHelix())
        if connected_vh in neighbors:
            neighbor_idx = neighbors.index(connected_vh)
            try:
                new_idx = util.nearest(idx + delta,
                                    preXovers(strand_type,
                                                neighbor_idx,
                                                min_idx=min_idx,
                                                max_idx=max_idx)
                                    )
                return new_idx
            except ValueError:
                return None  # nearest not found in the expanded list
        else:  # no neighbor (forced xover?)... don't snap, just return
            return idx + delta
    # end def

    def positionToCoord(self, x, y, scale_factor=1.0):
        """
        Returns a tuple (row, column) lattice coordinate for a given
        x and y position that is within +/- 0.5 of a true valid lattice
        position.

        Note: mapping should account for int-to-float rounding errors.
        x,y is relative to the Part Instance Position.
        """
        raise NotImplementedError  # To be implemented by Part subclass
    # end def

    def newPart(self):
        return Part(self._document)
    # end def

    def removeOligo(self, oligo):
        # Not a designated method
        # (there exist methods that also directly
        # remove parts from self._oligos)
        try:
            self._oligos.remove(oligo)
            oligo.oligoRemovedSignal.emit(self, oligo)
        except KeyError:
            print(util.trace(5))
            print("error removing oligo", oligo)
    # end def

    def resizeVirtualHelices(self, min_delta, max_delta, use_undostack=True):
        """docstring for resizeVirtualHelices"""
        c = ResizePartCommand(self, min_delta, max_delta)
        util.execCommandList(self, [c], desc="Resize part", \
                                                    use_undostack=use_undostack)
    # end def

    def setActiveBaseIndex(self, idx):
        self._active_base_index = idx
        self.partActiveSliceIndexSignal.emit(self, idx)
    # end def

    def setActiveVirtualHelix(self, virtual_helix, idx=None):
        self._active_virtual_helix = virtual_helix
        self._active_virtual_helix_idx = idx
        self.partStrandChangedSignal.emit(self, virtual_helix)
    # end def

    def selectPreDecorator(self, selection_list):
        """
        Handles view notifications that a predecorator has been selected.
        """
        if (len(selection_list) == 0):
            return
            # print("all PreDecorators were unselected")
            # partPreDecoratorUnSelectedSignal.emit()
        sel = selection_list[0]
        (row, col, baseIdx) = (sel[0], sel[1], sel[2])
        self.partPreDecoratorSelectedSignal.emit(self, row, col, baseIdx)



    ### PRIVATE SUPPORT METHODS ###
    def _addVirtualHelix(self, virtual_helix):
        """
        private method for adding a virtual_helix to the Parts data structure
        of virtual_helix references
        """
        self._coord_to_virtual_velix[virtual_helix.coord()] = virtual_helix
    # end def

    def _removeVirtualHelix(self, virtual_helix):
        """
        private method for adding a virtual_helix to the Parts data structure
        of virtual_helix references
        """
        del self._coord_to_virtual_velix[virtual_helix.coord()]
    # end def

    def _reserveHelixIDNumber(self, is_parity_even=True, requested_id_num=None):
        """
        Reserves and returns a unique numerical label appropriate for a
        virtualhelix of a given parity. If a specific index is preferable
        (say, for undo/redo) it can be requested in num.
        """
        num = requested_id_num
        if num is not None:  # We are handling a request for a particular number
            assert num >= 0, int(num) == num
            # assert not num in self._number_to_virtual_helix
            if num in self.odd_recycle_bin:
                self.odd_recycle_bin.remove(num)
                # rebuild the heap since we removed a specific item
                heapify(self.odd_recycle_bin)
                return num
            if num in self.even_recycle_bin:
                self.even_recycle_bin.remove(num)
                # rebuild the heap since we removed a specific item
                heapify(self.even_recycle_bin)
                return num
            self.reserve_bin.add(num)
            return num
        # end if
        else:
            # Just find any valid index (subject to parity constraints)
            if is_parity_even:
                if len(self.even_recycle_bin):
                    return heappop(self.even_recycle_bin)
                else:
                    while self._highest_used_even + 2 in self.reserve_bin:
                        self._highest_used_even += 2
                    self._highest_used_even += 2
                    self.reserve_bin.add(self._highest_used_even)
                    return self._highest_used_even
            else:
                if len(self.odd_recycle_bin):
                    return heappop(self.odd_recycle_bin)
                else:
                    # use self._highest_used_odd iff the recycle bin is empty
                    # and highestUsedOdd+2 is not in the reserve bin
                    while self._highest_used_odd + 2 in self.reserve_bin:
                        self._highest_used_odd += 2
                    self._highest_used_odd += 2
                    self.reserve_bin.add(self._highest_used_odd)
                    return self._highest_used_odd
        # end else
    # end def

    def _recycleHelixIDNumber(self, n):
        """
        The caller's contract is to ensure that n is not used in *any* helix
        at the time of the calling of this function (or afterwards, unless
        reserveLabelForHelix returns the label again).
        """
        if n % 2 == 0:
            heappush(self.even_recycle_bin, n)
        else:
            heappush(self.odd_recycle_bin, n)
    # end def

    def _splitBeforeAutoXovers(self, vh5p, vh3p, idx, use_undostack=True):
        # prexoveritem needs to store left or right, and determine
        # locally whether it is from or to
        # pass that info in here in and then do the breaks
        ss5p = strand5p.strandSet()
        ss3p = strand3p.strandSet()
        cmds = []

        # is the 5' end ready for xover installation?
        if strand3p.idx5Prime() == idx5p:  # yes, idx already matches
            xo_strand3 = strand3p
        else:  # no, let's try to split
            offset3p = -1 if ss3p.isDrawn5to3() else 1
            if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                found, overlap, ss_idx = ss3p._findIndexOfRangeFor(strand3p)
                if found:
                    c = SplitCommand(strand3p, idx3p + offset3p, ss_idx)
                    cmds.append(c)
                    xo_strand3 = c._strand_high if ss3p.isDrawn5to3() else c._strand_low
            else:  # can't split... abort
                return

        # is the 3' end ready for xover installation?
        if strand5p.idx3Prime() == idx5p:  # yes, idx already matches
            xo_strand5 = strand5p
        else:
            if ss5p.strandCanBeSplit(strand5p, idx5p):
                found, overlap, ss_idx = ss5p._findIndexOfRangeFor(strand5p)
                if found:
                    d = SplitCommand(strand5p, idx5p, ss_idx)
                    cmds.append(d)
                    xo_strand5 = d._strand_low if ss5p.isDrawn5to3() \
                                                else d._strand_high
            else:  # can't split... abort
                return
        c = CreateXoverCommand(self, xo_strand5, idx5p, xo_strand3, idx3p)
        cmds.append(c)
        util.execCommandList(self, cmds, desc="Create Xover", \
                                                use_undostack=use_undostack)
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def shallowCopy(self):
        part = self.newPart()
        part._virtual_helices = dict(self._virtual_helices)
        part._oligos = set(self._oligos)
        part._max_base = self._max_base
        return part
    # end def

    def deepCopy(self):
        """
        1) Create a new part
        2) copy the VirtualHelices
        3) Now you need to map the ORIGINALs Oligos onto the COPY's Oligos
        To do this you can for each Oligo in the ORIGINAL
            a) get the strand5p() of the ORIGINAL
            b) get the corresponding strand5p() in the COPY based on
                i) lookup the hash id_num of the ORIGINAL strand5p() VirtualHelix
                ii) get the StrandSet() that you created in Step 2 for the
                StrandType of the original using the hash id_num
        """
        # 1) new part
        part = self.newPart()
        for key, vhelix in self._virtual_helices:
            # 2) Copy VirtualHelix
            part._virtual_helices[key] = vhelix.deepCopy(part)
        # end for
        # 3) Copy oligos
        for oligo, val in self._oligos:
            strandGenerator = oligo.strand5p().generator3pStrand()
            strand_type = oligo.strand5p().strandType()
            new_oligo = oligo.deepCopy(part)
            last_strand = None
            for strand in strandGenerator:
                id_num = strand.virtualHelix().number()
                newVHelix = part._virtual_helices[id_num]
                new_strandset = newVHelix().getStrandSetByType(strand_type)
                new_strand = strand.deepCopy(new_strandset, new_oligo)
                if last_strand:
                    last_strand.setConnection3p(new_strand)
                else:
                    # set the first condition
                    new_oligo.setStrand5p(new_strand)
                new_strand.setConnection5p(last_strand)
                new_strandset.addStrand(new_strand)
                last_strand = new_strand
            # end for
            # check loop condition
            if oligo.isLoop():
                s5p = new_oligo.strand5p()
                last_strand.set3pconnection(s5p)
                s5p.set5pconnection(last_strand)
            # add to part
            oligo.add()
        # end for
        return part
    # end def

    def areSameOrNeighbors(self, virtual_helixA, virtual_helixB):
        """
        returns True or False
        """
        return virtual_helixB in self.getVirtualHelixNeighbors(virtual_helixA) or \
            virtual_helixA == virtual_helixB
    # end def

    def potentialCrossoverList(self, virtual_helix, idx=None, xover_p=False):
        """
        Returns a list of tuples
            (neighborVirtualHelix, index, strand_type, is_low_idx)

        where:

        neighborVirtualHelix is a virtual_helix neighbor of the arg virtual_helix
        index is the index where a potential Xover might occur
        strand_type is from the enum (StrandType.SCAFFOLD, StrandType.STAPLE)
        is_low_idx is whether or not it's the at the low index (left in the Path
        view) of a potential Xover site
        """
        vh = virtual_helix
        ret = []  # LUT = Look Up Table
        part = self
        # these are the list of crossover points simplified
        # they depend on whether the strand_type is scaffold or staple
        # create a list of crossover points for each neighbor of the form
        # [(_SCAFL[i], _SCAFH[i], _STAPL[i], _STAPH[i]), ...]
        luts_neighbor = list(
                            izip(
                                part._SCAFL,
                                part._SCAFH,
                                part._STAPL,
                                part._STAPH
                                )
                            )

        stand_types = (StrandType.SCAFFOLD, StrandType.STAPLE)
        num_bases = part.maxBaseIdx()

        # create a range for the helical length dimension of the Part,
        # incrementing by the lattice step size.
        base_range_unit = list(range(0, num_bases, part._STEP))

        if idx is not None:
            base_range_full = list(filter(lambda x: x >= idx - 3 * part._STEP and \
                                        x <= idx + 2 * part._STEP, base_range_unit))
        else:
            base_range_full = base_range_unit

        from_strandsets = vh.getStrandSets()
        neighbors = self.getVirtualHelixNeighbors(vh)

        # print(neighbors, luts_neighbor)
        for neighbor, lut in izip(neighbors, luts_neighbor):
            if not neighbor:
                continue

            """
            now arrange again for iteration
            ( (_SCAFL[i], _SCAFH[i]), (_STAPL[i], _STAPH[i]) )
            so we can pair by StrandType
            """
            lut_scaf = lut[0:2]
            lut_stap = lut[2:4]
            lut = (lut_scaf, lut_stap)

            to_strandsets = neighbor.getStrandSets()
            for from_ss, to_ss, pts, st in izip(from_strandsets,
                                                to_strandsets, lut, stand_types):
                # test each period of each lattice for each StrandType
                for pt, is_low_idx in izip(pts, (True, False)):
                    for i, j in product(base_range_full, pt):
                        index = to_index = i + j
                        if xover_p: # selection flag passed in from nucleicacidpartitem
                            to_index = index+1 if is_low_idx else index-1
                        if index < num_bases:
                            if from_ss.hasNoStrandAtOrNoXover(index) and \
                                    to_ss.hasNoStrandAtOrNoXover(to_index):
                                ret.append((neighbor, index, st, is_low_idx))
                            # end if
                        # end if
                    # end for
                # end for
            # end for
        # end for
        return ret
    # end def

    def isPossibleXoverA(self, from_virtual_helix, to_virtual_helix, strand_type, idx):
        from_ss = from_virtual_helix.getStrandSetByType(strand_type)
        to_ss = to_virtual_helix.getStrandSetByType(strand_type)
        return from_ss.hasStrandAtAndNoXover(idx) and \
                to_ss.hasStrandAtAndNoXover(idx)
    # end def

    def isPossibleXoverP(self, from_virtual_helix, to_virtual_helix, strand_type, idx):
        fromSS = from_virtual_helix.getStrandSetByType(strand_type)
        toSS = to_virtual_helix.getStrandSetByType(strand_type)
        if fromSS.isDrawn5to3():
            return fromSS.hasStrandAtAndNoXover(idx) and \
                    toSS.hasStrandAtAndNoXover(idx + 1)
        else:
            return fromSS.hasStrandAtAndNoXover(idx) and \
                    toSS.hasStrandAtAndNoXover(idx - 1)
    # end def

    def setImportedVHelixOrder(self, orderedCoordList, check_batch=True):
        """Used on file import to store the order of the virtual helices."""
        self._imported_vh_order = orderedCoordList
        self.partVirtualHelicesReorderedSignal.emit(self, orderedCoordList, check_batch)
    # end def

# end class
