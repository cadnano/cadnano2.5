#!/usr/bin/env python
# encoding: utf-8

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

class Part(ProxyObject):
    """
    A Part is a group of VirtualHelix items that are on the same lattice.
    Parts are the model component that most directly corresponds to a
    DNA origami design.

    Parts are always parented to the document.
    Parts know about their oligos, and the internal geometry of a part
    Copying a part recursively copies all elements in a part:
        VirtualHelices, Strands, etc

    PartInstances are parented to either the document or an assembly
    PartInstances know global position of the part
    Copying a PartInstance only creates a new PartInstance with the same
    Part(), with a mutable parent and position field.
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

# end class
