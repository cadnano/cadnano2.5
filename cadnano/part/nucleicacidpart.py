import random
from collections import defaultdict
from heapq import heapify, heappush, heappop
from itertools import product, islice
from uuid import uuid4
from ast import literal_eval
izip = zip

from cadnano import util
from cadnano import preferences as prefs
from cadnano.cnproxy import ProxySignal
from cadnano.cnobject import CNObject
from cadnano.cnproxy import UndoCommand
from cadnano.enum import PartType, StrandType
from cadnano.oligo import Oligo
from cadnano.oligo import RemoveOligoCommand
from cadnano.part.part import Part
from cadnano.strand import Strand
from cadnano.strandset import CreateStrandCommand
from cadnano.strandset import SplitCommand
from cadnano.strandset import StrandSet
from cadnano.virtualhelix import RemoveVirtualHelixCommand
from .translatevhelixcmd import TranslateVirtualHelicesCommand

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

    _SUB_STEP_SIZE = Part._STEP_SIZE / 3

    _MINOR_GROOVE_ANGLE = 171

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
        super(NucleicAcidPart, self).__init__(*args, **kwargs)

        # Properties (NucleicAcidPart-specific)
        self._group_properties["name"] = "NaPart%d" % self._count()
        self._group_properties['active_phos'] = None
        self._group_properties['crossover_span_angle'] = 20#45
        self._group_properties['max_vhelix_length'] = self._STEP_SIZE*2
        self._group_properties['neighbor_active_angle'] = ''
    # end def

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    ### SIGNALS ###

    ### SLOTS ###

    ### ACCESSORS ###
    def minorGrooveAngle(self):
        return self._MINOR_GROOVE_ANGLE
    # end def

    def subStepSize(self):
        return self._SUB_STEP_SIZE
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def partType(self):
        return PartType.NUCLEICACIDPART
    # end def

    def getVirtualHelicesInArea(self, rect):
        res = self.queryVirtualHelixOriginRect(rect)
        return set(res)
    # end def

    def getVirtualHelixAtPoint(self, point, id_num=None):
        """ Fix this to get the closest result
        """
        radius = self._RADIUS
        res = self.queryVirtualHelixOrigin(radius, point)
        # res = set(res)
        if len(res) > 0:
            if id_num is None:
                return res[0]
            else:
                for i in range(len(res)):
                    check_id_num = res[i]
                    if check_id_num != id_num:
                        return check_id_num
        return None
    # end def

    def isVirtualHelixNearPoint(self, point, id_num=None):
        """ Is a VirtualHelix near a point
        multiples of radius
        """
        radius = self._RADIUS
        res = self.queryVirtualHelixOrigin(2*radius, point)
        res = list(res)
        if len(res) > 0:
            # print(res)
            if id_num is None:
                return True
            else:
                for i in range(len(res)):
                    check_id_num = res[i]
                    if check_id_num != id_num:
                        existing_id_num = check_id_num
                        existing_pt = self.getVirtualHelixOrigin(existing_id_num)
                        print("vh{}\n{}\n{}\ndx: {}, dy: {}".format(existing_id_num,
                                                        existing_pt,
                                                        point,
                                                        existing_pt[0] - point[0],
                                                        existing_pt[1] - point[1]))
                        return True
        return False
    # end def

    def potentialCrossoverMap(self, id_num, idx=None):
        """
        Args:
            id_num (int):

        Returns:
            dictionary of tuples:

                neighbor_id_num: (fwd_hit_list, rev_hit_list)

                where each list has the form:

                    [(id_num_index, forward_neighbor_idxs, reverse_neighbor_idxs), ...]]


        """
        # neighbors = self.getVirtualHelixOriginNeighbors(id_num, 2.1*self._RADIUS)
        neighbors = literal_eval(self.vh_properties.loc[id_num, 'neighbors'])
        # hit_radius = self.radiusForAngle(60, self._RADIUS, self._BASE_WIDTH)
        alpha = self.getProperty('crossover_span_angle')
        per_neighbor_hits = self.queryIdNumRangeNeighbor(id_num, neighbors, alpha, index_slice=None)
        return per_neighbor_hits

    # end def
    def dimensions(self, scale_factor=1.0):
        """Returns a tuple of rectangle definining the XY limits of a part"""
        DMIN = 30
        xLL, yLL, xUR, yUR = self.getVirtualHelixOriginLimits()
        if xLL > -DMIN:
            xLL = -DMIN
        if yLL > -DMIN:
            yLL = -DMIN
        if xUR < DMIN:
            xUR = DMIN
        if yUR < DMIN:
            yUR = DMIN
        return xLL*scale_factor, yLL*scale_factor, xUR*scale_factor, yUR*scale_factor
    # end def

    def getStapleSequences(self):
        """getStapleSequences"""
        s = "Start,End,Sequence,Length,Color\n"
        for oligo in self._oligos:
            # if oligo.strand5p().strandSet().isStaple():
            s = s + oligo.sequenceExport()
        return s

    def getIdNums(self):
        """return the set of all ids used"""
        return self.reserved_ids
    # end def

    def getStapleLoopOligos(self):
        """
        Returns staple oligos with no 5'/3' ends. Used by
        actionExportSequencesSlot in documentcontroller to validate before
        exporting staple sequences.
        """
        stap_loop_olgs = []
        for o in list(self.oligos()):
            # if o.isStaple() and o.isLoop():
            if o.isLoop():
                stap_loop_olgs.append(o)
        return stap_loop_olgs

    def maxBaseIdx(self, id_num):
        o_and_s = self.getOffsetAndSize(id_num)
        size = 42 if o_and_s is None else o_and_s[1]
        return size
    # end def

    def numberOfVirtualHelices(self):
        return self.getSize()
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def verifyOligoStrandCounts(self):
        total_stap_strands = 0
        rev_oligos = set()
        total_stap_oligos = 0

        for id_num in self.getIdNums():
            fwd_ss, rev_ss = part.getStrandSets(id_num)
            total_stap_strands += rev_ss.strandCount()
            for strand in rev_ss:
                rev_oligos.add(strand.oligo())
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
        for id_num in list(self.getIdNums()):
            self.removeVirtualHelix(id_num, use_undostack=use_undostack)
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
        self._oligos.add(oligo)
        self.partOligoAddedSignal.emit(self, oligo)
    # end def

    def createVirtualHelix(self, x, y, use_undostack=True):
        c = CreateVirtualHelixCommand(self, x, y, 42)
        util.execCommandList(self, [c], desc="Add VirtualHelix", \
                                                use_undostack=use_undostack)
    # end def

    def removeVirtualHelix(self, id_num, use_undostack=True):
        """
        Removes a VirtualHelix from the model. Accepts a reference to the
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if use_undostack:
            self.undoStack().beginMacro("Delete VirtualHelix")
        fwd_ss, rev_ss = self.getStrandSets(id_num)
        fwd_ss.remove(use_undostack)
        rev_ss.remove(use_undostack)
        c = RemoveVirtualHelixCommand(self, id_num)
        if use_undostack:
            self.undoStack().push(c)
            self.undoStack().endMacro()
        else:
            c.redo()
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
        # if ss5p.isScaffold() and use_undostack:  # ignore on import
        #     strand5p.oligo().applySequence(None)
        #     strand3p.oligo().applySequence(None)
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
            depending on which way the the strand is drawn (isForward).  If a
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
                offset3p = -1 if ss3p.isForward() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    c = SplitCommand(strand3p, idx3p + offset3p)
                    # cmds.append(c)
                    xo_strand3 = c._strand_high if ss3p.isForward() else c._strand_low
                    # adjust the target 5prime strand, always necessary if a split happens here
                    if idx5p > idx3p and ss3p.isForward():
                        temp5 = xo_strand3
                    elif idx5p < idx3p and not ss3p.isForward():
                        temp5 = xo_strand3
                    else:
                        temp5 = c._strand_low if ss3p.isForward() else c._strand_high
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
                    if ss3p.isForward():
                        ss_idx5p = ss_idx3p + 1 if idx5p > idx3p else ss_idx3p
                    else:
                        ss_idx5p = ss_idx3p + 1 if idx5p > idx3p else ss_idx3p
                if ss5p.strandCanBeSplit(temp5, idx5p):
                    d = SplitCommand(temp5, idx5p)
                    # cmds.append(d)
                    xo_strand5 = d._strand_low if ss5p.isForward() else d._strand_high
                    if use_undostack:
                        self.undoStack().push(d)
                    else:
                        d.redo()
                    # adjust the target 3prime strand, IF necessary
                    if idx5p > idx3p and ss3p.isForward():
                        xo_strand3 = xo_strand5
                    elif idx5p < idx3p and not ss3p.isForward():
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
                offset3p = -1 if ss3p.isForward() else 1
                if ss3p.strandCanBeSplit(strand3p, idx3p + offset3p):
                    if ss3p.getStrandIndex(strand3p)[0]:
                        c = SplitCommand(strand3p, idx3p + offset3p)
                        # cmds.append(c)
                        xo_strand3 = c._strand_high if ss3p.isForward() else c._strand_low
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
                        xo_strand5 = d._strand_low if ss5p.isForward() else d._strand_high
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

    # def xoverSnapTo(self, strand, idx, delta):
    #     """
    #     Returns the nearest xover position to allow snap-to behavior in
    #     resizing strands via dragging selected xovers.
    #     """
    #     strand_type = strand.strandType()
    #     if delta > 0:
    #         min_idx, max_idx = idx - delta, idx + delta
    #     else:
    #         min_idx, max_idx = idx + delta, idx - delta

    #     # determine neighbor strand and bind the appropriate prexover method
    #     lo, hi = strand.idxs()
    #     if idx == lo:
    #         connected_strand = strand.connectionLow()
    #         preXovers = self.getPreXoversHigh
    #     else:
    #         connected_strand = strand.connectionHigh()
    #         preXovers = self.getPreXoversLow
    #     connected_vh = connected_strand.idNum()

    #     # determine neighbor position, if any
    #     neighbors = self.getVirtualHelixNeighbors(strand.idNum())
    #     if connected_vh in neighbors:
    #         neighbor_idx = neighbors.index(connected_vh)
    #         try:
    #             new_idx = util.nearest(idx + delta,
    #                                 preXovers(strand_type,
    #                                             neighbor_idx,
    #                                             min_idx=min_idx,
    #                                             max_idx=max_idx)
    #                                 )
    #             return new_idx
    #         except ValueError:
    #             return None  # nearest not found in the expanded list
    #     else:  # no neighbor (forced xover?)... don't snap, just return
    #         return idx + delta
    # # end def

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

    def translateVirtualHelices(self,   vh_set,
                                        dx, dy, dz,
                                        finalize,
                                        use_undostack=False):
        if use_undostack:
            c = TranslateVirtualHelicesCommand(self, vh_set, dx, dy, dz)
            if finalize:
                util.finalizeCommands(self, [c], desc="Translate VHs")
            else:
                util.execCommandList(self, [c], desc="Translate VHs", \
                                                            use_undostack=True)
        else:
            self._translateVirtualHelices(vh_set, dx, dy, dz, False)
    # end def

    def _translateVirtualHelices(self, vh_set, dx, dy, dz, do_deselect):
        """
        do_deselect tells a view to clear selections that might have
        undesirable Object parenting to make sure the translations are set
        correctly.  set to True when "undo-ing"
        """
        threshold = 2.1*self._RADIUS
        # 1. get old neighbor list
        old_neighbors = set()
        for id_num in vh_set:
            neighbors = self.getVirtualHelixOriginNeighbors(id_num, threshold)
            old_neighbors.update(neighbors)
        # 2. move in the virtual_helix_group
        self.translateCoordinates(vh_set, (dx, dy, dz))
        # 3. update neighbor calculations
        new_neighbors = set()
        for id_num in vh_set:
            neighbors = self.getVirtualHelixOriginNeighbors(id_num, threshold)
            try:
                self.setVirtualHelixProperties(id_num, 'neighbors', str(list(neighbors)))
            except:
                print("neighbors", list(neighbors))
                raise
            new_neighbors.update(neighbors)

        # now update the old and new neighbors that were not in the vh set
        left_overs = new_neighbors.union(old_neighbors).difference(vh_set)
        for id_num in left_overs:
            neighbors = self.getVirtualHelixOriginNeighbors(id_num, threshold)
            try:
                self.setVirtualHelixProperties(id_num, 'neighbors', str(list(neighbors)))
            except:
                print("neighbors", list(neighbors))
                raise
        self.partVirtualHelicesTranslatedSignal.emit(self, vh_set, left_overs, do_deselect)
    #end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def shallowCopy(self):
        raise NotImplementedError
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
        new_part = self.newPart()
        # 2) Copy VirtualHelix Group
        new_part = self.copy(self._document, new_object=new_part)
        # end for
        # 3) Copy oligos, populating the strandsets
        for oligo, val in self._oligos:
            strandGenerator = oligo.strand5p().generator3pStrand()
            new_oligo = oligo.deepCopy(new_part)
            last_strand = None
            for strand in strandGenerator:
                id_num = strand.idNum()
                new_strandset = self.getStrandSets(id_num)[strand.strandType()]
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
            # add to new_part
            oligo.addToPart(new_part)
        # end for
        return part
    # end def


    def setImportedVHelixOrder(self, ordered_coord_list, check_batch=True):
        """Used on file import to store the order of the virtual helices."""
        self.setViewProperty('path:virtual_helix_order', ordered_coord_list)
        self.partVirtualHelicesReorderedSignal.emit(self, ordered_coord_list, check_batch)
    # end def

# end class
