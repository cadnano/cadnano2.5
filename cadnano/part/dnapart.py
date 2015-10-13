
from cadnano.part.part import Part

from heapq import heapify, heappush, heappop
from itertools import product, islice

izip = zip

from collections import defaultdict
import random
from uuid import uuid4

from cadnano.cnproxy import ProxyObject, ProxySignal
from cadnano.enum import StrandType

import cadnano.util as util
import cadnano.preferences as prefs

from cadnano.cnproxy import UndoCommand

from cadnano.strand import Strand

from cadnano.oligo import Oligo
from cadnano.oligo import RemoveOligoCommand

from cadnano.strandset import StrandSet
from cadnano.strandset import SplitCommand

from cadnano.virtualhelix import VirtualHelix
from cadnano.virtualhelix import RemoveVirtualHelixCommand
from cadnano.strandset import CreateStrandCommand, RemoveStrandCommand

from .createvhelixcmd import CreateVirtualHelixCommand
from .xovercmds import CreateXoverCommand, RemoveXoverCommand
from .resizepartcmd import ResizePartCommand

from .pmodscmd import AddModCommand, RemoveModCommand, ModifyModCommand
from .refresholigoscmd import RefreshOligosCommand
from .removepartcmd import RemovePartCommand
from .renumbercmd import RenumberVirtualHelicesCommand

class DnaPart(Part):
    """
    DNAPart.
    """

    _STEP = 21  # this is the period (in bases) of the part lattice
    _RADIUS = 1.125  # nanometers
    _TURNS_PER_STEP = 2
    _HELICAL_PITCH = _STEP / _TURNS_PER_STEP
    _TWIST_PER_BASE = 360 / _HELICAL_PITCH  # degrees

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
        super(Part, self).__init__(self._document)
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
        # ID assignment
        self.odd_recycle_bin, self.even_recycle_bin = [], []
        self.reserve_bin = set()
        self._highest_used_odd = -1  # Used in _reserveHelixIDNumber
        self._highest_used_even = -2  # same
        self._imported_vh_order = None
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
    partVirtualHelicesReorderedSignal = ProxySignal(object, list,
                        name='partVirtualHelicesReorderedSignal') # self, list of coords
    partHideSignal = ProxySignal(ProxyObject, name='partHideSignal')
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

    def dimensions(self):
        """Returns a tuple of the max X and maxY coordinates of the lattice."""
        return self.latticeCoordToPositionXY(self._max_row, self._max_col)
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
        self.partHideSignal.emit(self)
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
        doc = self.document()
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

    def destroy(self):
        self.setParent(None)
        self.deleteLater()  # QObject also emits a destroyed() Signal
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
        except KeyError:
            print(util.trace(5))
            print("error removing oligo", oligo)
    # end def

    def resizeLattice(self):
        pass
    # end def

    def resizeVirtualHelices(self, min_delta, max_delta, use_undostack=True):
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
                heapify(self.odd_recycle_bin)
                return num
            if num in self.even_recycle_bin:
                self.even_recycle_bin.remove(num)
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


# end class
