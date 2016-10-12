# -*- coding: utf-8 -*-
import math
from ast import literal_eval
from bisect import bisect_left
from collections import defaultdict, deque
from heapq import heapify, heappush, nsmallest
from itertools import count as icount

import numpy as np
import pandas as pd

from cadnano import util
from cadnano.cnobject import CNObject
from .virtualhelix import VirtualHelix
from cadnano.cnproxy import ProxySignal
from cadnano.cnenum import GridType, PartType, PointType
from cadnano.oligo import RemoveOligoCommand
from cadnano.part.part import Part
from cadnano.strandset import StrandSet
from cadnano.strandset import SplitCommand
from .createvhelixcmd import CreateVirtualHelixCommand
from .removevhelixcmd import RemoveVirtualHelixCommand
from .resizevirtualhelixcmd import ResizeVirtualHelixCommand
from .translatevhelixcmd import TranslateVirtualHelicesCommand
from .xovercmds import CreateXoverCommand, RemoveXoverCommand
from cadnano.setpropertycmd import SetVHPropertyCommand
from cadnano.addinstancecmd import AddInstanceCommand
from cadnano.removeinstancecmd import RemoveInstanceCommand

"""
inner1d(a, a) is equivalent to np.einsum('ik,ij->i', a, a)
equivalent to np.sum(a*a, axis=1) but faster
"""
from numpy.core.umath_tests import inner1d

DEFAULT_CACHE_SIZE = 20


def _defaultProperties(id_num):
    props = [('name', "vh%d" % (id_num)),
             ('is_visible', True),
             ('color', '#00000000'),
             # ('eulerZ', 17.143*2),    # 0.5*360/10.5
             ('eulerZ', 0.),
             ('scamZ', 10.),
             ('neighbor_active_angle', 0.0),
             ('neighbors', '[]'),
             ('bases_per_repeat', 21),
             ('turns_per_repeat', 2),
             ('repeat_hint', 2),  # used in path view for how many repeats to display PXIs
             ('helical_pitch', 1.),
             ('minor_groove_angle', 180.),  # 171.),
             ('length', -1),
             ('z', 0.0)
             ]
    return tuple(zip(*props))
# end def
VH_PROPERTY_KEYS = set([x for x in _defaultProperties(0)[0]])


Z_PROP_INDEX = -1  # index for Dataframe.iloc calls


def _defaultDataFrame(size):
    dummy_id_num = 999
    columns, row = _defaultProperties(dummy_id_num)
    df = pd.DataFrame([row for i in range(size)], columns=columns)
    return df
# end def
DEFAULT_SIZE = 256
DEFAULT_FULL_SIZE = DEFAULT_SIZE * 48
DEFAULT_RADIUS = 1.125  # nm


class NucleicAcidPart(Part):
    """NucleicAcidPart is a group of VirtualHelix items that are on the same
    lattice.
    - it does not enforce distinction between scaffold and staple strands
    - specific crossover types are not enforced (i.e. antiparallel)
    - sequence output is more abstract ("virtual sequences" are used)

    This is composed of a group of arrays that:

    1. Contain the coordinates of every virtual base stored in their index
       order per id_num
    2. Contains the id_num per coordinate.

    Uses `*args` and `**kwargs` to make subclassing easier

    Args:
        `*args`: Variable length argument list.
        `**kwargs`: Arbitrary keyword arguments.
    """
    _STEP_SIZE = 21  # this is the period (in bases) of the part lattice
    _TURNS_PER_STEP = 2
    _HELICAL_PITCH = _STEP_SIZE / _TURNS_PER_STEP
    _TWIST_PER_BASE = 360 / _HELICAL_PITCH  # degrees
    _BASE_WIDTH = 0.34  # nanometers, distance between bases, pith
    _SUB_STEP_SIZE = _STEP_SIZE / 3
    __count = 0
    vh_editable_properties = VH_PROPERTY_KEYS.difference(set(['neighbors']))

    @classmethod
    def _count(cls):
        NucleicAcidPart.__count += 1
        return NucleicAcidPart.__count

    def __init__(self, *args, **kwargs):
        """
        """
        super(NucleicAcidPart, self).__init__(*args, **kwargs)
        do_copy = kwargs.get('do_copy', False)
        if do_copy:
            return

        self._radius = DEFAULT_RADIUS     # probably a property???
        self._insertions = defaultdict(dict)  # dict of insertions per virtualhelix
        self._mods = {'int_instances': {},
                      'ext_instances': {}}
        self._oligos = set()

        # Runtime state
        self._active_base_index = self._STEP_SIZE
        self._active_id_num = None
        self.active_base_info = ()
        self._selected = False
        self.is_active = False

        self._abstract_segment_id = None
        self._current_base_count = None

        # Properties (NucleicAcidPart-specific)
        gps = self._group_properties
        gps["name"] = "NaPart%d" % self._count()
        gps['active_phos'] = None
        gps['crossover_span_angle'] = 45
        gps['max_vhelix_length'] = self._STEP_SIZE * 2
        gps['neighbor_active_angle'] = ''
        gps['grid_type'] = GridType.HONEYCOMB
        gps['virtual_helix_order'] = []
        gps['point_type'] = kwargs.get('point_type', PointType.Z_ONLY)

        ############################
        # Begin low level attributes
        ############################

        # 1. per virtual base pair allocations
        self.total_points = 0
        self.axis_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        # self.axis_pts[:, 2] = 0.0
        self.fwd_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        self.rev_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        self.id_nums = np.full((DEFAULT_FULL_SIZE,), -1, dtype=int)
        self.indices = np.zeros((DEFAULT_FULL_SIZE,), dtype=int)

        # 2. per virtual helix allocations
        self.total_id_nums = 0  # should be equal to len(self.reserved_ids)

        self._origin_pts = np.full((DEFAULT_SIZE, 2), np.inf, dtype=float)
        """For doing 2D X,Y manipulation for now.  keep track of
        XY position of virtual helices
        """

        self.origin_limits = (0., 0., 0., 0.)

        self.directions = np.zeros((DEFAULT_SIZE, 3), dtype=float)

        self._offset_and_size = [None] * DEFAULT_SIZE
        """Bookkeeping for fast lookup of indices for insertions and deletions
        and coordinate points. The length of this is the max id_num used.
        """
        self._virtual_helices_set = {}

        self.reserved_ids = set()

        self.vh_properties = _defaultDataFrame(DEFAULT_SIZE)

        self.fwd_strandsets = [None] * DEFAULT_SIZE
        self.rev_strandsets = [None] * DEFAULT_SIZE
        self.segment_dict = {}  # for tracking strand segments

        # Cache Stuff
        self._point_cache = None
        self._point_cache_keys = None
        self._resetPointCache()
        self._origin_cache = None
        self._origin_cache_keys = None
        self._resetOriginCache()

        # scratch allocations for vector calculations
        self.m3_scratch0 = np.zeros((3, 3), dtype=float)
        self.m3_scratch1 = np.zeros((3, 3), dtype=float)
        self.m3_scratch2 = np.zeros((3, 3), dtype=float)
        self.eye3_scratch = np.eye(3, 3, dtype=float)    # don't change this
        self.delta2D_scratch = np.empty((1,), dtype=float)
        self.delta3D_scratch = np.empty((1,), dtype=float)

        # ID assignment
        self.recycle_bin = []
        self._highest_id_num_used = -1  # Used in _reserveHelixIDNumber
    # end def

    # B. Virtual Helix
    partActiveVirtualHelixChangedSignal = ProxySignal(CNObject, int, name='partActiveVirtualHelixChangedSignal')
    """id_num"""

    partActiveBaseInfoSignal = ProxySignal(CNObject, object, name='partActiveBaseInfoSignal')
    """self.active_base_info (tuple or None)"""

    partVirtualHelixAddedSignal = ProxySignal(object, int, object, object, name='partVirtualHelixAddedSignal')
    """self, virtual_helix id_num, virtual_helix, neighbor list"""

    partVirtualHelixRemovingSignal = ProxySignal(object, int, object, object, name='partVirtualHelixRemovingSignal')
    """self, virtual_helix id_num, virtual_helix, neighbor list"""

    partVirtualHelixRemovedSignal = ProxySignal(object, int, name='partVirtualHelixRemovedSignal')
    """self, virtual_helix id_num"""

    partVirtualHelixResizedSignal = ProxySignal(CNObject, int, object, name='partVirtualHelixResizedSignal')
    """self, virtual_helix id_num, virtual_helix"""

    partVirtualHelicesTranslatedSignal = ProxySignal(CNObject, object, object, bool,
                                                     name='partVirtualHelicesTranslatedSignal')
    """self, list of id_nums, transform"""

    partVirtualHelicesSelectedSignal = ProxySignal(CNObject, object, bool, name='partVirtualHelicesSelectedSignal')
    """self, iterable of id_nums to select, transform"""

    partVirtualHelixPropertyChangedSignal = ProxySignal(CNObject, int, object, object, object,
                                                        name='partVirtualHelixPropertyChangedSignal')
    """self, id_num, virtual_helix, key, value"""

    # C. Oligo
    partOligoAddedSignal = ProxySignal(CNObject, object, name='partOligoAddedSignal')
    """self, oligo"""
    # D. Strand
    partStrandChangedSignal = ProxySignal(object, int, name='partStrandChangedSignal')
    """self, virtual_helix"""

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<%s %s>" % (cls_name, str(id(self))[-4:])

    def _resetOriginCache(self):
        self._origin_cache = {}
        self._origin_cache_keys = deque([None] * DEFAULT_CACHE_SIZE)
    # end def

    def _resetPointCache(self):
        self._point_cache = {}
        self._point_cache_keys = deque([None] * DEFAULT_CACHE_SIZE)
    # end def

    def copy(self, document, new_object=None):
        """Copy all arrays and counters and create new StrandSets

        TODO: consider renaming this method

        Args:
            document (Document): :class:`Document` object
            new_object (NucleicAcidPart): optional, whether to copy
                into new_object or to allocate a new one internal to this method
                an allocated :class:`NucleicAcidPart`
        """
        new_vhg = new_object
        if new_vhg is None:
            constructor = type(self)
            new_vhg = constructor(document=document, do_copy=True)
        if not isinstance(new_vhg, NucleicAcidPart):
            raise ValueError("new_vhg {} is not an instance of a NucleicAcidPart".format(new_vhg))
        new_vhg.total_points = self.total_points
        new_vhg.axis_pts = self.axis_pts.copy()
        new_vhg.fwd_pts = self.fwd_pts.copy()
        new_vhg.rev_pts = self.rev_pts.copy()
        new_vhg.id_nums = self.id_nums.copy()
        new_vhg.indices = self.indices.copy()

        new_vhg.total_id_nums = self.total_id_nums
        new_vhg._origin_pts = self._origin_pts
        new_vhg.origin_limits = self.origin_limits
        new_vhg.directions = self.directions

        new_vhg.offset_and_size = self._offset_and_size.copy()
        new_vhg.reserved_ids = self.reserved_ids.copy()

        new_vhg.vh_properties = _defaultDataFrame(DEFAULT_SIZE)

        new_vhg.fwd_strandsets = [x.simpleCopy(new_vhg) for x in self.fwd_strandsets]
        new_vhg.rev_strandsets = [x.simpleCopy(new_vhg) for x in self.rev_strandsets]

        new_vhg.recycle_bin = self.recycle_bin
        new_vhg._highest_id_num_used = self._highest_id_num_used
        return new_vhg
    # end def

    def stepSize(self):
        return self._STEP_SIZE
    # end def

    def baseWidth(self):
        return self._BASE_WIDTH
    # end def

    def radius(self):
        return self._radius
    # end def

    def helicalPitch(self):
        return self._HELICAL_PITCH
    # end def

    def twistPerBase(self):
        return self._TWIST_PER_BASE
    # end def

    def getOffsetAndSize(self, id_num):
        """Get the index offset of this ID into the point buffers

        Args:
            id_num (int): virtual helix ID number

        Returns:
            tuple: (:obj:`int`, :obj:`int`) of the form::

                (offset, size)

            into the coordinate arrays for a given ID number or or :obj:`None`
            if `id_num` if out of range
        """
        offset_and_size = self._offset_and_size
        return offset_and_size[id_num] if id_num < len(offset_and_size) else None
    # end def

    def getVirtualHelix(self, id_num):
        """Get a VirtualHelix object to allow for convenience manipulation

        Args:
            id_num (int):
        Returns:
            int: VirtualHelix
        """
        return self._virtual_helices_set[id_num]
    # end def

    def _getNewIdNum(self):
        """Query the lowest available (unused) id_num. Internally id numbers are
        recycled when virtual helices are deleted.

        Returns:
            int: ID number
        """
        if len(self.recycle_bin):
            return nsmallest(1, self.recycle_bin)[0]
        else:
            # use self._highest_id_num_used if the recycle bin is empty
            # and _highest_id_num_used + 1 is not in the reserve bin
            return self._highest_id_num_used + 1
    # end def

    def getIdNumMax(self):
        """The max id number

        Returns:
            int: max virtual helix ID number used
        """
        return self._highest_id_num_used
    # end def

    def _reserveIdNum(self, requested_id_num):
        """Reserves and returns a unique numerical id_num appropriate for a
        virtualhelix of a given parity. If a specific index is preferable
        (say, for undo/redo) it can be requested in num.

        Args:
            requested_id_num (int): virtual helix ID number
        """
        num = requested_id_num
        assert num >= 0, int(num) == num
        # assert not num in self._number_to_virtual_helix
        if num in self.recycle_bin:
            self.recycle_bin.remove(num)
            # rebuild the heap since we removed a specific item
            heapify(self.recycle_bin)
        if self._highest_id_num_used < num:
            self._highest_id_num_used = num
        self.reserved_ids.add(num)
    # end def

    def _recycleIdNum(self, id_num):
        """The caller's contract is to ensure that id_num is not used in *any*
        helix at the time of the calling of this function (or afterwards, unless
        `reserveIdNumForHelix` returns the id_num again).

        Args:
            id_num (int): virtual helix ID number
        """
        heappush(self.recycle_bin, id_num)
        self.reserved_ids.remove(id_num)
    # end def

    def getCoordinates(self, id_num):
        """Return a view onto the numpy array for a given id_num

        Args:
            id_num (int): virtual helix ID number

        Returns:
            tuple: of :obj:'ndarray' of the form::

                (axis_pts, fwd_pts, rev_pts)

            for a given virtual helix ID number
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        offset, size = offset_and_size_tuple
        lo, hi = offset, offset + size
        return (self.axis_pts[lo:hi],
                self.fwd_pts[lo:hi],
                self.rev_pts[lo:hi])
    # end def

    def getCoordinate(self, id_num, idx):
        """Given a id_num get the coordinate at a given index

        Args:
            id_num (int): virtual helix ID number
            idx (int): index

        Returns:
            ndarray: of :obj:`float` shape (1, 3)

        Raises:
            KeyError: id_num not in NucleicAcidPart
            IndexError: idx is greater than size
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        offset, size = offset_and_size_tuple
        if idx < size:
            return self.axis_pts[offset + idx]
        else:
            raise IndexError("idx {} greater than size {}".format(idx, size))
    # end def

    def isAGreaterThanB_Z(self, id_numA, idxA, id_numB, idxB):
        """Compare z values at each index of virtual helix A and B

        Args:
            id_numA (int):  ID number of A
            idxA (int):     index into A
            id_numB (int):  ID number of B
            idxB (int):     index into B

        Returns:
            bool: True if A > B
        """
        a = self.getCoordinate(id_numA, idxA)
        b = self.getCoordinate(id_numB, idxB)
        return a[2] > b[2]
    # end def

    def getVirtualHelixOrigin(self, id_num):
        """given a id_num get the origin coordinate

        Args:
            id_num (int): virtual helix ID number

        Returns:
            ndarray: (1, 3) origin of the Virtual Helix (0 index)

        Raises:
            KeyError: id_num not in NucleicAcidPart
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        return self._origin_pts[id_num]
    # end def

    def getidNums(self):
        """Return a list of used id_nums

        Returns:
            list: of :obj:`int` of virtual helix ID numbers used
        """
        return [i for i, j in filter(lambda x: x[1] is not None, enumerate(self._offset_and_size))]
    # end def

    def _setVirtualHelixOriginLimits(self):
        """Set origin limits by grabbing the max `x` and `y` values of the
        origins of all virtual helices
        """
        valid_pts = np.where(self._origin_pts != np.inf)
        vps = self._origin_pts[valid_pts]
        vps = vps.reshape((len(vps) // 2, 2))
        xs = vps[:, 0]
        ys = vps[:, 1]
        xLL = np.amin(xs)
        xUR = np.amax(xs)
        yLL = np.amin(ys)
        yUR = np.amax(ys)
        self.origin_limits = (xLL, yLL, xUR, yUR)
    # end def

    def getVirtualHelixOriginLimits(self):
        """Given a id_num get the coordinate at a given index

        Returns:
            tuple: of :obj:`int` of the form::

                (xLL, yLL, xUR, yUR)
        """
        return self.origin_limits
    # end def

    def getStrandSets(self, id_num):
        """Given a id_num get the coordinate at a given index

        Args:
            id_num (int): virtual helix ID number

        Returns:
            tuple: (forward :class:`StrandSet`, reverse :class:`StrandSet`)
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        return (self.fwd_strandsets[id_num], self.rev_strandsets[id_num])
    # end def

    def refreshSegments(self, id_num):
        """Partition strandsets into overlapping segments

        Returns:
            tuple: of segments for the forward and reverse strand of form::

                ( [ [(start, end),...], ...], [ [(start, end),...], ...])
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))
        fwd_ss = self.fwd_strandsets[id_num]
        rev_ss = self.rev_strandsets[id_num]

        self.segment_dict[id_num] = {}
        return self._refreshSegments(fwd_ss, rev_ss)
    # end def

    def _refreshSegments(self, fwd_ss, rev_ss):
        """Testable private version

        Returns:
            list: of :obj:`tuple`: of segments of form::

                (start, end)

            of type (:obj:`int`, :obj:`int`)
        """

        """ 1. Grab all endpoints separated by low and
        high indices of the strands
        """
        fwd_idxs = [x.idxs() for x in fwd_ss.strand_heap]
        if fwd_idxs:
            f_endpts_lo, f_endpts_hi = zip(*fwd_idxs)
        else:
            f_endpts_lo = []
            f_endpts_hi = []

        rev_idxs = [x.idxs() for x in rev_ss.strand_heap]
        if rev_idxs:
            r_endpts_lo, r_endpts_hi = zip(*rev_idxs)
        else:
            r_endpts_lo = []
            r_endpts_hi = []

        """ 2. create virtual high endpoints below the low endpoints
        and include them in a set and convert to a sorted list
        """
        hi_endpoints = set([x - 1 for x in f_endpts_lo])
        hi_endpoints.update([x - 1 for x in r_endpts_lo])
        hi_endpoints.update(f_endpts_hi)
        hi_endpoints.update(r_endpts_hi)
        hi_endpoints = list(hi_endpoints)
        hi_endpoints.sort()

        """ 3. now iterate through the strands and
        convert to
        """
        fwd_segments = []
        rev_segments = []

        i = 0
        for f_strand, f_idxs in zip(fwd_ss.strand_heap, fwd_idxs):
            start, idx_hi = f_idxs
            end = start
            segments = []
            while start <= idx_hi:
                i = bisect_left(hi_endpoints, start, lo=i)
                end = hi_endpoints[i]
                segments.append((start, end))
                start = end + 1
            f_strand.segments = segments
            fwd_segments.append(segments)
        i = 0
        for r_strand, r_idxs in zip(rev_ss.strand_heap, rev_idxs):
            start, idx_hi = r_idxs
            end = start
            segments = []
            while start <= idx_hi:
                i = bisect_left(hi_endpoints, start, lo=i)
                end = hi_endpoints[i]
                segments.append((start, end))
                start = end + 1
            r_strand.segments = segments
            rev_segments.append(segments)
        return fwd_segments, rev_segments
    # end def

    def hasStrandAtIdx(self, id_num, idx):
        """Check if `Strand` exists at an index

        Args:
            id_num (int): virtual helix ID number
            idx (int): index that the strand is at

        Returns:
            tuple[bool, bool]: True if a strand is present at idx,
            False otherwise.
        """
        return (self.fwd_strandsets[id_num].hasStrandAt(idx, idx),
                self.rev_strandsets[id_num].hasStrandAt(idx, idx))
    # end def

    def getStrand(self, is_fwd, id_num, idx):
        """Get a `Strand` object

        Args:
            is_fwd (bool): is the StrandType Forward
            id_num (int): virtual helix ID number
            idx (int): index that the strand is at

        Returns:
            Strand: if it exists
        """

        if is_fwd:
            return self.fwd_strandsets[id_num].getStrand(idx)
        else:
            return self.rev_strandsets[id_num].getStrand(idx)
    # end def

    def indexOfRightmostNonemptyBase(self):
        """During reduction of the number of bases in a part, the first click
        removes empty bases from the right hand side of the part (red
        left-facing arrow). This method returns the new numBases that will
        effect that reduction.

        Returns:
            int: index of right most base in all :class:`StrandSets`
        """
        ret = self._STEP - 1
        fwd_strandsets = self.fwd_strandsets
        rev_strandsets = self.rev_strandsets
        for id_num in self.reserved_ids:
            ret = max(ret,
                      fwd_strandsets[id_num].indexOfRightmostNonemptyBase(),
                      rev_strandsets[id_num].indexOfRightmostNonemptyBase())
        return ret
    # end def

    def _translateCoordinates(self, id_nums, delta):
        """delta is a :obj:`array-like` of floats of length 3
        for now support XY translation

        Args:
            id_nums (array-like): of :obj:`int` virtual helix ID numbers
            delta (array-like):  of :obj:`float` of length 3
        """
        self._resetOriginCache()
        self._resetPointCache()
        origin_pts = self._origin_pts
        delta_origin = delta[:2]  # x, y only
        for id_num in id_nums:
            coord_pts, fwd_pts, rev_pts = self.getCoordinates(id_num)
            coord_pts += delta  # use += to modify the view
            fwd_pts += delta  # use += to modify the view
            rev_pts += delta  # use += to modify the view
            # print("old origin", self.locationQt(id_num, 15./self.radius()))
            origin_pts[id_num, :] += delta_origin
            # print("new origin", self.locationQt(id_num, 15./self.radius()))
        try:
            self.vh_properties.iloc[list(id_nums), Z_PROP_INDEX] += delta[2]
        except:
            print(list(id_nums), Z_PROP_INDEX)
            raise
        self._setVirtualHelixOriginLimits()
    # end def

    def getIndices(self, id_num):
        """return a view onto the numpy array for a given id_num

        Args:
            id_num (int): virtual helix ID number

        Returns:
            ndarray: of :obj:`int` array of indices corresponding to points
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        offset, size = offset_and_size_tuple
        lo, hi = offset, offset + size
        return self.indices[lo:hi]
    # end def

    def getNeighbors(self, id_num, radius, idx=0):
        """ might use radius = 2.1*RADIUS
        return list of neighbor id_nums and the indices nearby

        Args:
            id_num (int): virtual helix ID number
            radius (float): radial distance within which a neighbors origin exists
            idx (int): optional, index to center the neighbor search at. default to 0

        Returns:
            list: of :obj:`tuple` of form::

                (neighbor ID, index)

            of type (:obj:`int`, :obj:`int`)
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        coord = self.getCoordinate(id_num, idx)
        neighbors, indices = self.queryBasePoint(radius, *coord)
        non_id_num_idxs, _ = np.where(neighbors != id_num)
        return list(zip(np.take(neighbors, non_id_num_idxs),
                        np.take(indices, non_id_num_idxs)
                        )
                    )
    # end def

    def _getVirtualHelixOriginNeighbors(self, id_num, radius):
        """ might use radius = 2.1*RADIUS
        for now return a set of neighbor id_nums

        Args:
            id_num (int): virtual helix ID number
            radius (float): radial distance within which a neighbors origin exists

        Returns:
            set: set of neighbor candidate ID numbers
        """
        origin = self._origin_pts[id_num]
        neighbors = self.queryVirtualHelixOrigin(radius, tuple(origin))
        neighbor_candidates = set(neighbors)
        neighbor_candidates.discard(id_num)
        return neighbor_candidates
    # end def

    def _addCoordinates(self, id_num, points, is_right):
        """Points will only be added on the ends of a virtual helix
        not internally.  NO GAPS!
        handles reindex the points in self.indices

        Args:
            id_num (int): virtual helix ID number
            points (array-like): n x 3 shaped numpy ndarray of floats or
                2D Python list. points are stored in order and by index
            is_right (bool): whether we are extending in the positive index
                direction or prepending
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)

        # 1. Find insert indices
        if offset_and_size_tuple is None:
            raise IndexError("id_num {} does not exists".format(id_num))

        offset_and_size = self._offset_and_size
        len_axis_pts = len(self.axis_pts)

        new_axis_pts, new_fwd_pts, new_rev_pts = points
        num_points = len(new_axis_pts)  # number of points being added

        self._resetPointCache()

        # 1. existing id_num
        offset, size = offset_and_size_tuple
        lo_idx_limit, hi_idx_limit = offset, offset + size
        if is_right:
            insert_idx = hi_idx_limit
        else:  # prepend
            insert_idx = offset

        # new_lims = (hi_idx_limit, hi_idx_limit + num_points)
        # print("{} settting offset {} and size {}".format(id_num, offset, size + num_points))
        # print("length before {}".format(len_axis_pts))
        offset_and_size[id_num] = (offset, size + num_points)
        # increment the offset for every higher index
        for i, o_and_s in enumerate(offset_and_size[id_num + 1:], start=id_num + 1):
            if o_and_s is not None:
                offset_and_size[i] = (o_and_s[0] + num_points, o_and_s[1])

        # 2. Did exceed allocation???
        total_points = self.total_points
        if total_points + num_points > len_axis_pts:
            diff = self.total_points + num_points - len_axis_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_FULL_SIZE) * DEFAULT_FULL_SIZE
            total_rows = len_axis_pts + number_of_new_elements
            # resize per virtual base allocations
            self.axis_pts.resize((total_rows, 3))
            self.axis_pts[len_axis_pts:] = [np.inf, np.inf, np.inf]

            self.fwd_pts.resize((total_rows, 3))
            self.fwd_pts[len_axis_pts:] = np.inf

            self.rev_pts.resize((total_rows, 3))
            self.rev_pts[len_axis_pts:] = np.inf

            self.id_nums.resize((total_rows,))
            self.id_nums[len_axis_pts:] = -1

            self.indices.resize((total_rows,))
            self.indices[len_axis_pts:] = 0
        # end if exceeded allocation
        axis_pts = self.axis_pts
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        id_nums = self.id_nums
        indices = self.indices

        # 3. Move Existing data
        move_idx_start = insert_idx + num_points
        move_idx_end = total_points + num_points

        axis_pts[move_idx_start:move_idx_end] = axis_pts[insert_idx:total_points]
        axis_pts[insert_idx:move_idx_start] = new_axis_pts
        fwd_pts[move_idx_start:move_idx_end] = fwd_pts[insert_idx:total_points]
        fwd_pts[insert_idx:move_idx_start] = new_fwd_pts
        rev_pts[move_idx_start:move_idx_end] = rev_pts[insert_idx:total_points]
        rev_pts[insert_idx:move_idx_start] = new_rev_pts

        # just overwrite everything for indices and id_nums no need to move
        id_nums[move_idx_start:move_idx_end] = id_nums[insert_idx:total_points]
        id_nums[insert_idx:move_idx_start] = id_num
        indices[move_idx_start:move_idx_end] = indices[insert_idx:total_points]
        indices[lo_idx_limit:lo_idx_limit + num_points + size] = list(range(num_points + size))

        self.total_points += num_points
    # end def

    def getDirections(self, id_nums):
        """ Get directions for a :obj:`array-like` of ID numbers

        Args:
            id_nums (array-like): of :obj:`int` array_like list of indices
            or scalar index

        Returns:
            ndarray: shape (x, 3) array
        """
        return np.take(self.directions, id_nums, axis=0)
    # end def

    @staticmethod
    def normalize(self, v):
        """Normlize a vector

        Args:
            v (array-like): of :obj:`float` of length 3

        Returns:
            ndarray: of :obj:`float`, norm of `v`
        """
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm
    # end def

    @staticmethod
    def lengthSq(self, v):
        """Compute the length of a :obj:`array-like`

        Args:
            v (array-like):  of :obj:`float` length 3

        Returns:
            float
        """
        return inner1d(v, v)

    @staticmethod
    def cross(self, a, b):
        """Compute the cross product of two vectors of length 3

        Args:
            a (array-like):  of :obj:`float` of length 3
            b (array-like):  of :obj:`float` of length 3

        Returns:
            list: of :obj:`float` of length 3
        """
        ax, ay, az = a
        bx, by, bz = b
        c = [ay*bz - az*by,
             az*bx - ax*bz,
             ax*by - ay*bx]
        return c
    # end def

    def makeRotation(self, v1, v2):
        """Create a rotation matrix for an object pointing in the `v1`
        direction to the `v2` direction.  Uses a class allocated scratch `ndarrays`

        see: http://math.stackexchange.com/questions/180418/180436#180436

        Args:
            v1 (array-like):  of :obj:`float` of length 3
            v2 (array-like):  of :obj:`float` of length 3

        Returns:
            ndarray: shape (3, 3) m0
        """
        if np.all(v1 == v2):
            return self.eye3_scratch.copy()

        v1 = self.normalize(v1)
        v2 = self.normalize(v2)

        v = np.cross(v1, v2)
        sin_squared = inner1d(v, v)
        cos_ = inner1d(v1, v2)  # fast dot product

        m1 = self.m3_scratch1
        m2 = self.m3_scratch2
        m0 = self.m3_scratch0
        m0[:] = 0.

        m0[1, 0] = v[2]
        m0[0, 1] = -v[2]
        m0[2, 0] = -v[1]
        m0[0, 2] = v[1]
        m0[2, 1] = v[0]
        m0[1, 2] = -v[0]

        # do the following efficiently
        # self.eye3_scratch + m0 + np.dot(m0, m0)*((1 - cos_)/sin_squared)
        np.dot(m0, m0, out=m1)
        np.add(self.eye3_scratch, m0, out=m2)
        np.add(m2, m1*((1 - cos_)/sin_squared), out=m0)
        return m0
    # end def

    def _createHelix(self, id_num, origin, direction, num_points, color):
        """Create a virtual helix in the group that has a Z_ONLY direction

        Args:
            id_num (int): virtual helix ID number
            origin (array-like):  of :obj:`float` of length 3
                The origin should be referenced from an index of 0.
            direction (array-like):  of :obj:`float` of length 3
            num_points (int): number of bases in Virtual Helix
            color (str): hexadecimal color code in the form: `#RRGGBB`
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is not None:
            raise IndexError("id_num {} already exists".format(id_num))

        self._reserveIdNum(id_num)

        offset_and_size = self._offset_and_size

        # 1. New id_num / virtual helix insert after all other points
        # expand offset and size as required
        self._resetOriginCache()

        len_offset_and_size = len(offset_and_size)
        number_of_new_elements = id_num - len_offset_and_size + 1
        if number_of_new_elements > 0:
            offset_and_size += [None]*number_of_new_elements
            self.fwd_strandsets += [None]*number_of_new_elements
            self.rev_strandsets += [None]*number_of_new_elements
        # find the next highest insertion offset
        next_o = self.total_points
        for next_o_and_s in offset_and_size[id_num + 1:]:
            if next_o_and_s:
                next_o, next_s = next_o_and_s
                break
        # this_offset = num_points
        # print("total points", self.total_points, next_o, id_num)
        offset_and_size[id_num] = (next_o, 0)
        # the other offsets will be adjusted later

        # 2. Assign origin on creation, resizing as needed
        len_origin_pts = len(self._origin_pts)
        if id_num >= len_origin_pts:
            diff = id_num - len_origin_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_SIZE)*DEFAULT_SIZE
            total_rows = len_origin_pts + number_of_new_elements
            # resize adding zeros
            self._origin_pts.resize((total_rows, 2))
            self._origin_pts[len_origin_pts:] = np.inf

            self.directions.resize((total_rows, 3))
            self.directions[len_origin_pts:] = 0  # unnecessary as resize fills with zeros

            self.vh_properties = self.vh_properties.append(_defaultDataFrame(number_of_new_elements),
                                                           ignore_index=True)

        self._origin_pts[id_num] = origin[:2]
        new_x, new_y = origin[:2]
        xLL, yLL, xUR, yUR = self.origin_limits
        if new_x < xLL:
            xLL = new_x
        if new_x > xUR:
            xUR = new_x
        if new_y < yLL:
            yLL = new_y
        if new_y > yUR:
            yUR = new_y
        self.origin_limits = (xLL, yLL, xUR, yUR)
        self.directions[id_num] = direction
        self.vh_properties.loc[id_num, ['name', 'color', 'length']] = "vh%d" % (id_num), color, num_points

        if self.fwd_strandsets[id_num] is None:
            self.fwd_strandsets[id_num] = StrandSet(True, id_num, self, num_points)
            self.rev_strandsets[id_num] = StrandSet(False, id_num, self, num_points)
        else:
            self.fwd_strandsets[id_num]._reset(num_points)
            self.rev_strandsets[id_num]._reset(num_points)

        self.total_id_nums += 1

        # 3. Create points
        points = self._pointsFromDirection(id_num, origin, direction, num_points, 0)
        self._addCoordinates(id_num, points, is_right=False)
        self._group_properties['virtual_helix_order'].append(id_num)
        self._virtual_helices_set[id_num] = vh = VirtualHelix(id_num, self)
        return vh
    # end def

    def _pointsFromDirection(self, id_num, origin, direction, num_points, index):
        """Assumes always prepending or appending points.  no insertions.
        changes eulerZ of the id_num vh_properties as required for prepending
        points

        Args:
            id_num (int): virtual helix ID number
            origin (array-like):  of :obj:`float` of length 3
                The origin should be referenced from an index of 0.
            direction (array-like): of :obj:`float` of length 3
            index (int): the offset index into a helix to start the helix at.
                Useful for appending points. if index less than zero

        Returns:
            tuple: (coord_pts, fwd_pts, rev_pts)
        """
        rad = self._radius
        BW = self._BASE_WIDTH
        hp, bpr, tpr, eulerZ, mgroove = self.vh_properties.loc[id_num,
                                                               ['helical_pitch',
                                                                'bases_per_repeat',
                                                                'turns_per_repeat',
                                                                'eulerZ',
                                                                'minor_groove_angle']]
        twist_per_base = tpr*360./bpr
        """
        + angle is CCW
        - angle is CW
        Right handed DNA rotates clockwise from 5' to 3'
        we use the convention the 5' end starts at 0 degrees
        and it's pair is minor_groove_angle degrees away
        direction, hence the minus signs.  eulerZ
        """
        twist_per_base = math.radians(twist_per_base)
        eulerZ_new = math.radians(eulerZ) + twist_per_base*index
        mgroove = math.radians(mgroove)

        # right handed rotates clockwise with increasing index / z
        fwd_angles = [-i*twist_per_base + eulerZ_new for i in range(num_points)]
        rev_angles = [a + mgroove for a in fwd_angles]
        z_pts = BW*np.arange(index, num_points + index)

        # invert the X coordinate for Right handed DNA
        fwd_pts = rad*np.column_stack((np.cos(fwd_angles),
                                       np.sin(fwd_angles),
                                       np.zeros(num_points)))
        fwd_pts[:, 2] = z_pts

        # invert the X coordinate for Right handed DNA
        rev_pts = rad*np.column_stack((np.cos(rev_angles),
                                       np.sin(rev_angles),
                                       np.zeros(num_points)))
        rev_pts[:, 2] = z_pts

        coord_pts = np.zeros((num_points, 3))
        coord_pts[:, 2] = z_pts

        # create scratch array for stashing intermediate results
        scratch = np.zeros((3, num_points), dtype=float)

        # rotate about 0 index and then translate
        m = self.makeRotation((0, 0, 1), direction)
        # print(m)

        np.add(np.dot(m, fwd_pts.T, out=scratch).T, origin, out=fwd_pts)
        np.add(np.dot(m, rev_pts.T, out=scratch).T, origin, out=rev_pts)
        np.add(np.dot(m, coord_pts.T, out=scratch).T, origin, out=coord_pts)

        if index < 0:
            self.vh_properties.loc[id_num, 'eulerZ'] = math.degrees(eulerZ_new)

        return (coord_pts, fwd_pts, rev_pts)
    # end def

    def getVirtualHelixProperties(self, id_num, keys, safe=True):
        """Getter of the properties of a virtual helix

        Args:
            id_num (int): virtual helix ID number
            keys (object): :obj:`str` or :obj:`list`/:obj:`tuple`
            safe (:obj:`bool`): optional, default to True

        Returns:
            object: object or list depending on type of arg `keys`
        """
        if safe:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        props = self.vh_properties.loc[id_num, keys]
        if isinstance(props, pd.Series):
            return [v.item() if isinstance(v, (np.float64, np.int64, np.bool_)) else v for v in props]
        else:
            return props.item() if isinstance(props, (np.float64, np.int64, np.bool_)) else props
    # end

    def helixPropertiesAndOrigins(self, id_num_list=None):
        """
        Args:
            id_num_list (list): optional, of :obj:`int` list of virtual
                helix ID numbers to get the origins and properties of. defaults to
                all IDs

        Returns:
            tuple: of (:obj:`dict`, :obj:`ndarray`) (properties dictionary
            where each key has a list of values correspoding to the id_number
            and, (n, 2) array of origins

        Raises:
            ValueError:
        """
        if id_num_list is None:
            lim = self._highest_id_num_used + 1
            props = self.vh_properties.iloc[:lim]
            props = props.to_dict(orient='list')
            origins = self._origin_pts[:lim]
            return props, origins
        elif isinstance(id_num_list, list):
            # select by list of indices
            props = self.vh_properties.iloc[id_num_list].reset_index(drop=True)
            props = props.to_dict(orient='list')
            origins = self._origin_pts[id_num_list]
            return props, origins
        else:
            raise ValueError("id_num_list bad type: {}".format(type(id_num_list)))
    # end def

    def getAllVirtualHelixProperties(self, id_num, inject_extras=True, safe=True):
        """NOT to be used for a list of Virtual Helix property keys unless
        `inject_extras` is False

        Args:
            id_num (int): virtual helix ID number
            inject_extras (bool): optional, adds in 'bases_per_turn' and
            'twist_per_base'.  default to True
            safe (bool): check if id_num exists. Default True

        Returns:
            dict: properties of a given ids

        Raises:
            IndexError:
        """
        if safe:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        series = self.vh_properties.loc[id_num]
        # to_dict doesn't promote to python native types needed by QVariant
        # leaves as numpy integers and floats
        out = dict((k, v.item()) if isinstance(v, (np.float64, np.int64, np.bool_))
                   else (k, v) for k, v in zip(series.index, series.tolist()))
        if inject_extras:
            bpr = out['bases_per_repeat']
            tpr = out['turns_per_repeat']
            out['bases_per_turn'] = bpr / tpr
            out['twist_per_base'] = tpr*360. / bpr
        return out
    # end

    def setVirtualHelixProperties(self, id_num, keys, values, safe=True, use_undostack=True):
        """Keys and values can be :obj:`array-like` of equal length or
        singular values. Public handles undostack

        This could be expanded to take a list of id numbers

        emits `partVirtualHelixPropertyChangedSignal`

        Args:
            id_num (int): virtual helix ID number
            keys (object): :obj:`str` or :obj:`list`/:obj:`tuple`, the key or keys
            value (object): :obj:`object` or :obj:`list`/:obj:`tuple`,
                the value or values matching the key order
            safe (bool): optionally echew signalling
        """
        if safe:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        if use_undostack:
            c = SetVHPropertyCommand(self, [id_num], keys, values, safe)
            self.undoStack().push(c)
        else:
            self._setVirtualHelixProperties(id_num, keys, values, emit_signals=safe)
    # end

    def _setVirtualHelixProperties(self, id_num, keys, values, emit_signals=True):
        """Private Version: Keys and values can be :obj:`array-like` of equal
        length or singular values.

        emits `partVirtualHelixPropertyChangedSignal`

        Args:
            id_num (int): virtual helix ID number
            keys (object): :obj:`str` or :obj:`list`/:obj:`tuple`, the key or keys
            value (object): :obj:`object` or :obj:`list`/:obj:`tuple`,
                the value or values matching the key order
            emit_signals (bool): optionally echew signaling
        """
        if emit_signals:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        self.vh_properties.loc[id_num, keys] = values

        if not isinstance(values, (tuple, list)):
            keys, values = (keys,), (values,)
        if emit_signals:
            self.partVirtualHelixPropertyChangedSignal.emit(
                self, id_num, self.getVirtualHelix(id_num), keys, values)
    # end

    def locationQt(self, id_num, scale_factor=1.0):
        """ Y-axis is inverted in Qt +y === DOWN

        Args:
            id_num (int):
            scale_factor (float): optional, default 1.0

        Returns:
            tuple: of :obj:`float`, x, y coordinates
        """
        x, y = self.getVirtualHelixOrigin(id_num)
        return scale_factor*x, -scale_factor*y
    # end def

    def _resizeHelix(self, id_num, is_right, delta):
        """Resize vritual helix given by ID number

        Args:
            id_num (int): virtual helix ID number
            is_right (bool): whether this is a left side (False) or
                right side (True) operation
            delta (int): number of virtual base pairs to add to (+) or trim (-)
                from the virtual helix

        Returns:
            int: the ID number of the longest Virtual Helix in the
            NucleicAcidPart

        Raises:
            IndexError:
            ValueError:
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise IndexError("id_num {} does not exist")

        offset, size = offset_and_size_tuple
        # len_axis_pts = len(self.axis_pts)
        direction = self.directions[id_num]

        # make origin 3D
        origin = self._origin_pts[id_num]
        origin = (origin[0], origin[1], 0.)

        if delta > 0:   # adding points
            if is_right:
                index = size
            else:
                index = -delta
            # 3. Create points
            points = self._pointsFromDirection(id_num, origin, direction, delta, index)
            self._addCoordinates(id_num, points, is_right=is_right)
            # TODO add checks for resizing strandsets here
            if is_right:
                self.fwd_strandsets[id_num].resize(0, delta)
                self.rev_strandsets[id_num].resize(0, delta)
            else:
                self.fwd_strandsets[id_num].resize(delta, 0)
                self.rev_strandsets[id_num].resize(delta, 0)
        elif delta < 0:  # trimming points
            if abs(delta) >= size:
                raise ValueError("can't delete virtual helix this way")
            # TODO add checks for strandsets etc here:

            self._removeCoordinates(id_num, abs(delta), is_right)
            if is_right:
                self.fwd_strandsets[id_num].resize(0, delta)
                self.rev_strandsets[id_num].resize(0, delta)
            else:
                self.fwd_strandsets[id_num].resize(delta, 0)
                self.rev_strandsets[id_num].resize(delta, 0)
        else:  # delta == 0
            return
        _, final_size = self.getOffsetAndSize(id_num)
        # print("final_size", final_size)
        self.vh_properties.loc[id_num, 'length'] = final_size
        # print("New max:", self.vh_properties['length'].idxmax(),
        #         self.vh_properties['length'].max())
        # return 0, self.vh_properties['length'].idxmax()
        return self.zBoundsIds()
    # end def

    def zBoundsIds(self):
        """Get the ID numbers of the Z bounds accounting for infinity for
        unitialized virtual helices

        Returns:
            tuple: of :obj:`int`, of form (ID_z_min, ID_z_max)
        """
        test = self.axis_pts[:, 2]
        id_z_min = self.id_nums[np.argmin(test)]
        # use numpy masked arrays to mask out infinites
        id_z_max = self.id_nums[np.argmax(np.ma.array(test,
                                                      mask=np.isinf(test)))]
        return id_z_min, id_z_max
    # end def

    def _removeHelix(self, id_num):
        """Remove a helix and recycle it's `id_num`

        Args:
            id_num (int): virtual helix ID number

        Raises:
            IndexError:
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise IndexError("id_num {} does not exist")
        offset, size = offset_and_size_tuple
        # print("the offset and size", offset_and_size_tuple)
        did_remove = self._removeCoordinates(id_num, size, is_right=False)
        self._recycleIdNum(id_num)
        assert did_remove
        # TODO if making 'virtual_helix_order' an instance property,
        # this needs to be changed
        self._group_properties['virtual_helix_order'].remove(id_num)
        del self._virtual_helices_set[id_num]
    # end def

    def resetCoordinates(self, id_num):
        """Call this after changing helix `vh_properties` to update the points
        controlled by the properties.  Basically clears things back to a simple
        version of a virtual helix

        Args:
            id_num (int): virtual helix ID number

        Raises:
            KeyError:
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))
        offset, size = offset_and_size_tuple
        origin = self.axis_pts[offset]  # zero point of axis
        direction = self.directions[id_num]
        points = self._pointsFromDirection(id_num, origin, direction, size, 0)
        self._setCoordinates(id_num, points)
    # end def

    def _setCoordinates(self, id_num, points, idx_start=0):
        """Change the stored coordinates.
        Useful when adjusting helix vh_properties.

        Args:
            id_num (int): virtual helix ID number
            points (tuple): tuple containing :obj:`array-like` of axis, and forward
            and reverse phosphates points
            idx_start (int): optional index offset into the virtual helix to
            assign points to. default to 0

        Raises:
            KeyError:
            IndexError:
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        offset, size = offset_and_size_tuple
        if idx_start + len(points) > size:
            err = ("Number of Points {} out of range for"
                   "start index {} given existing size {}")
            raise IndexError(err.format(len(points), idx_start, size))

        new_axis_pts, new_fwd_pts, new_rev_pts = points
        lo = offset + idx_start
        hi = lo + len(new_axis_pts)
        self.axis_pts[lo:hi] = new_axis_pts
        self.fwd_pts[lo:hi] = new_fwd_pts
        self.rev_pts[lo:hi] = new_rev_pts
    # end def

    def _removeCoordinates(self, id_num, length, is_right):
        """Remove coordinates given a length, reindex as necessary

        Args:
            id_num (int): virtual helix ID number
            length (int): number of coordinates to remove
            is_right (bool): whether the removal occurs at the right or left
                end of a virtual helix since virtual helix arrays are always contiguous

        Returns:
            bool: True if id_num is removed, False otherwise

        Raises:
            KeyError:
            IndexError:
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)

        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in NucleicAcidPart".format(id_num))

        offset, size = offset_and_size_tuple
        if length > size:
            raise IndexError("length longer {} than indices existing".format(length))
        lo, hi = offset, offset + size
        if is_right:
            idx_start, idx_stop = hi - length, hi
        else:
            idx_start, idx_stop = lo, lo + length

        self._resetPointCache()
        offset_and_size = self._offset_and_size
        current_offset_and_size_length = len(offset_and_size)

        # 1. Move the good data
        total_points = self.total_points
        relocate_idx_end = total_points - length

        axis_pts = self.axis_pts
        try:
            axis_pts[idx_start:relocate_idx_end] = axis_pts[idx_stop:total_points]
        except:
            err = "idx_start {}, relocate_idx_end {}, idx_stop {}, total_points {}, length {}"
            print(err.format(idx_start, relocate_idx_end, idx_stop, total_points, length))
            raise
        axis_pts[relocate_idx_end:total_points] = np.inf

        fwd_pts = self.fwd_pts
        fwd_pts[idx_start:relocate_idx_end] = fwd_pts[idx_stop:total_points]
        fwd_pts[relocate_idx_end:total_points] = np.inf

        rev_pts = self.rev_pts
        rev_pts[idx_start:relocate_idx_end] = rev_pts[idx_stop:total_points]
        rev_pts[relocate_idx_end:total_points] = np.inf

        id_nums = self.id_nums
        id_nums[idx_start:relocate_idx_end] = id_nums[idx_stop:total_points]
        id_nums[relocate_idx_end:total_points] = -1

        indices = self.indices
        indices[idx_start:relocate_idx_end] = indices[idx_stop:total_points]
        indices[relocate_idx_end:total_points] = 0
        if not is_right:
            # We need to adjust the base index
            # lo offset index should not change for a given id_num
            indices[lo:lo + length] -= length

        # 2. Adjust the offsets of id_nums greater than id_num
        for i, item in enumerate(offset_and_size[id_num + 1:], start=1):
            if item is not None:
                offset_other, size_other = item
                offset_and_size[i + id_num] = (offset_other - length, size_other)

        # 3. Check if we need to remove Virtual Helix
        if size == length:
            self.total_id_nums -= 1
            self._resetOriginCache()
            offset_and_size[id_num] = None
            self._origin_pts[id_num, :] = (np.inf, np.inf)  # set off to infinity
            # trim the unused id_nums at the end
            remove_count = 0
            for i in range(current_offset_and_size_length - 1, id_num - 1, -1):
                if offset_and_size[i] is None:
                    remove_count += 1
                else:
                    break
            self._offset_and_size = offset_and_size[:current_offset_and_size_length - remove_count]
            did_remove = True
        else:
            # print("Did remove", size, length)
            offset_and_size[id_num] = (offset, size - length)
            did_remove = False
        self.total_points -= length
        return did_remove
    # end def

    def queryBasePoint(self, radius, point):
        """Cached query

        Args:
            radius (float): distance to consider
            point (array-like): :obj:`float` of length 3

        Returns:
            tuple: of :obj:`ndarray`
        """
        qc = self._point_cache
        query = (radius, point)
        if query in qc:
            return qc.get(query)
        else:
            res = self._queryBasePoint(radius, point)
            self._point_cache_keys.append(query)
            qc[query] = res
            # limit the size of the cache
            old_key = self._point_cache_keys.popleft()
            if old_key is not None:
                del qc[old_key]
            return res
    # end def

    def _queryBasePoint(self, radius, point):
        """ return the indices of all virtual helices closer than radius

        Args:
            radius (float): distance to consider
            point (array-like): of :obj:`float` of length 3

        Returns:
            tuple: of :obj:`ndarray`
        """
        difference = self.axis_pts - point
        ldiff = len(difference)
        delta = self.delta3D_scratch
        if ldiff != len(delta):
            self.delta3D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        delta = inner1d(difference, difference, out=delta)
        close_points, = np.where(delta < radius*radius)
        # return list(zip(    np.take(self.id_nums, close_points),
        #                     np.take(self.indices, close_points) ))
        return (np.take(self.id_nums, close_points),
                np.take(self.indices, close_points))
    # end def

    def queryVirtualHelixOrigin(self, radius, point):
        """ Hack for now to get 2D behavior
        point is an array_like of length 2

        Args:
            radius (float): distance to consider
            point (array-like): of :obj:`float` of length 3

        Returns:
            ndarray: close origin points to `point`
        """
        qc = self._origin_cache
        query = (radius, point)
        if query in qc:
            return qc.get(query)
        else:
            # print('miss')
            res = self._queryVirtualHelixOrigin(radius, point)
            res = res.tolist()
            self._origin_cache_keys.append(query)
            qc[query] = res
            # print("size", len(qc))
            # limit the size of the cache
            old_key = self._origin_cache_keys.popleft()
            if old_key is not None:
                # try:
                del qc[old_key]
                # except:
                #     print(old_key, list(qc.keys()))
                #     raise
            return res
    # end def

    def _queryVirtualHelixOrigin(self, radius, point):
        """Return the indices of all id_nums closer
        than radius, sorted by distance

        Args:
            radius (float): distance to consider
            point (array-like): of :obj:`float` of length 3

        Returns:
            ndarray: close origin points to `point`
        """
        difference = self._origin_pts - point
        ldiff = len(difference)
        delta = self.delta2D_scratch
        if ldiff != len(delta):
            self.delta2D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        inner1d(difference, difference, out=delta)
        close_points, = np.where(delta <= radius*radius)
        # take then sort the indices of the points in range
        sorted_idxs = np.argsort(np.take(delta, close_points))

        return close_points[sorted_idxs]
    # end def

    def _queryVirtualHelixOriginRect(self, rect):
        """Query based on a Rectangle

        Args:
            rect (array-like): of :obj:`float` rectangle defined by::

                    ( x1, y1, x2, y2)

                definining the lower left and upper right corner of the
                rectangle respetively

        Returns:
            ndarray: list of ID numbers satisfying the query
        """
        # search children
        x1, y1, x2, y2 = rect
        origin_pts = self._origin_pts
        xs = origin_pts[:, 0]
        ys = origin_pts[:, 1]
        x_lo_mask = xs > x1
        x_hi_mask = xs < x2
        combo_x = np.logical_and(x_lo_mask, x_hi_mask)
        np.logical_and(ys > y1, ys < y2, out=x_lo_mask)
        np.logical_and(x_lo_mask, combo_x, out=x_hi_mask)
        id_nums, = np.where(x_hi_mask)
        return id_nums
    # end def

    def _queryIdNumRange(self, id_num, radius, index_slice=None):
        """Return the indices of all virtual helices phosphates closer
        than `radius` to `id_num`'s helical axis

        Currently UNUSED code, but keeping it around to show how to search
        ranges

        Args:
            id_num (int): virtual helix ID number
            radius (float): distance to consider
            index_slice (Tuple): a tuple of the start index and length into
            a virtual helix

        Returns:
            tuple: of :obj:`list`, fwd_axis_hits, rev_axis_hits
            where each element in the list is::

                :obj:`tuple` of :obj:`int`, :obj:`tuple`

            corresponding to an index into id_num and a tuple of hits on a neighbors
            looking like::

                :obj:`tuple` of :obj:`list`:

            with the item in the first element the neighbors ID and the item in second
            element the index into that neighbor
        """
        offset, size = self.getOffsetAndSize(id_num)
        start, length = 0, size if index_slice is None else index_slice

        # convert to a list since we can't speed this loop up without cython or something
        this_axis_pts = self.axis_pts[offset + start:offset + start + length].tolist()
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        # for now just looks against everything
        fwd_hit_list = []
        rev_hit_list = []
        rsquared = radius*radius
        for i, point in enumerate(this_axis_pts):
            difference = fwd_pts - point
            ldiff = len(difference)
            delta = self.delta3D_scratch
            if ldiff != len(delta):
                self.delta3D_scratch = delta = np.empty((ldiff,), dtype=float)

            # compute square of distance to point
            delta = inner1d(difference, difference, out=delta)
            close_points, = np.where(delta < rsquared)
            close_points, = np.where((close_points < offset) |
                                     (close_points > (offset + size)))
            if len(close_points) > 0:
                fwd_hits = (np.take(self.id_nums, close_points).tolist(),
                            np.take(self.indices, close_points).tolist())
                fwd_hit_list.append((start + i, fwd_hits))

            difference = rev_pts - point
            delta = inner1d(difference, difference, out=delta)
            close_points, = np.where(delta < rsquared)
            close_points, = np.where((close_points < offset) |
                                     (close_points > (offset + size)))
            if len(close_points) > 0:
                rev_hits = (np.take(self.id_nums, close_points).tolist(),
                            np.take(self.indices, close_points).tolist())
                rev_hit_list.append((start + i, rev_hits))
        return fwd_hit_list, rev_hit_list
    # end def

    def normalizedRange(self, id_num, index):
        """Given an `index` within the bounds `[0, size]`
        return an range of length `bases_per_repeat` if pro

        Args:
            id_num (int): virtual helix ID number
            index (int): index

        Returns:
            tuple: of :obj:`int` of form::

                (start index, bases per repeat)
        """
        offset, size = self.getOffsetAndSize(id_num)
        bpr = self.vh_properties.loc[id_num, 'bases_per_repeat']
        half_period = bpr // 2
        if size - index < bpr:
            start = size - bpr
        else:
            start = max(index - half_period, 0)
        return start, bpr
    # end def

    def _queryIdNumRangeNeighbor(self, id_num, neighbors, alpha, index=None):
        """Get indices of all virtual helices phosphates closer within an
        `alpha` angle's radius to `id_num`'s helical axis

        Args:
            id_num (int): virtual helix ID number
            neighbors (array-like): neighbors of id_num
            alpha (float): angle (degrees) commensurate with radius
            index (tuple): optional, of :obj:`int` (start_index, length) into
                a virtual helix, default to `(0, size)`

        Returns:
            dict: of :obj:`tuple` of form::

                neighbor_id_num: (fwd_hit_list, rev_hit_list)

            where each list has the form::

                [(id_num_index, forward_neighbor_idxs, reverse_neighbor_idxs), ...]]

        """
        offset, size = self.getOffsetAndSize(id_num)
        bpr, tpr = self.vh_properties.loc[id_num,
                                          ['bases_per_repeat', 'turns_per_repeat']]
        bases_per_turn = bpr / tpr
        if index is None:
            start, length = 0, size
        else:
            half_period = bpr // 2
            if size - index < bpr:
                start, length = size - bpr, bpr
            else:
                start, length = max(index - half_period, 0), bpr
        # norm = np.linalg.norm
        cross = np.cross
        dot = np.dot
        normalize = self.normalize
        # PI = math.pi
        # TWOPI = 2*PI
        RADIUS = self._radius
        BW = self._BASE_WIDTH

        theta, radius = self.radiusForAngle(alpha, RADIUS, bases_per_turn, BW)
        # convert to a list since we can't speed this loop up without cython or something
        axis_pts = self.axis_pts
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        this_axis_pts = axis_pts[offset + start:offset + start + length].tolist()
        this_fwd_pts = fwd_pts[offset + start:offset + start + length].tolist()
        this_rev_pts = rev_pts[offset + start:offset + start + length].tolist()
        # for now just looks against everything
        # rsquared1 = RADIUS*RADIUS + BASE_WIDTH*BASE_WIDTH/4
        # print("THE search radius", radius, RADIUS)
        rsquared2 = radius*radius
        per_neighbor_hits = {}
        key_prop_list = ['eulerZ', 'bases_per_repeat',
                         'turns_per_repeat', 'minor_groove_angle']
        for neighbor_id in neighbors:
            eulerZ, bpr, tpr, mgroove = self.vh_properties.loc[neighbor_id, key_prop_list]
            twist_per_base = tpr*360./bpr
            half_period = math.floor(bpr / 2)
            tpb = math.radians(twist_per_base)
            eulerZ = math.radians(eulerZ)
            mgroove = math.radians(mgroove)

            offset, size = self.getOffsetAndSize(neighbor_id)

            # 1. Finds points that point at neighbors axis point
            naxis_pts = axis_pts[offset:offset + size]
            nfwd_pts = fwd_pts[offset:offset + size]

            direction = self.directions[neighbor_id]
            len_neighbor_pts = len(naxis_pts)
            delta = self.delta3D_scratch
            if len_neighbor_pts != len(delta):
                self.delta3D_scratch = delta = np.empty((len_neighbor_pts,), dtype=float)

            fwd_axis_hits = []
            angleRangeCheck = self.angleRangeCheck
            angleNormalize = self.angleNormalize
            for i, point in enumerate(this_fwd_pts):
                difference = naxis_pts - point
                inner1d(difference, difference, out=delta)
                # assume there is only one possible index of intersection with the neighbor
                neighbor_min_delta_idx = np.argmin(delta)
                if delta[neighbor_min_delta_idx] < rsquared2:
                    neighbor_axis_pt = naxis_pts[neighbor_min_delta_idx]
                    # a. angle between vector from neighbor axis at minimum delta to this axis_pt
                    #   and the vector from the neighbor axis at minimum delta to neighbor_fwds_pts
                    v1 = normalize(this_axis_pts[i] - neighbor_axis_pt)
                    # project point onto plane normal to axis
                    v1 = normalize(v1 - dot(v1, direction)*direction)

                    v2 = normalize(nfwd_pts[neighbor_min_delta_idx] - neighbor_axis_pt)
                    # relative_angle = math.acos(np.dot(v1, v2))  # angle
                    # get signed angle between
                    relative_angle = math.atan2(dot(cross(v1, v2), direction), dot(v1, v2))
                    # relative_angle = math.atan2(dot(cross(v2, v1), direction), dot(v2, v1))
                    # print(id_num, 'f', relative_angle)
                    # b. fwd pt angle relative to first base in virtual helix
                    native_angle = angleNormalize(eulerZ + tpb*neighbor_min_delta_idx - relative_angle)

                    # print("FWD %d around %d relative_angle %0.2f, base_angle: %0.2f" %
                    #     (   id_num, neighbor_id,
                    #         math.degrees(relative_angle),
                    #         math.degrees(angleNormalize(tpb*neighbor_min_delta_idx))
                    #         ))
                    # print(math.degrees(native_angle), math.degrees(angleNormalize(tpb*neighbor_min_delta_idx + relative_angle)))

                    all_fwd_angles = [(j, angleNormalize(eulerZ - tpb*j)) for j in range(max(neighbor_min_delta_idx - half_period, 0),
                                                                                         min(neighbor_min_delta_idx + half_period, size))]
                    passing_fwd_angles_idxs = [j for j, x in all_fwd_angles if angleRangeCheck(x, native_angle, theta)]
                    all_rev_angles = [(j, angleNormalize(x + mgroove)) for j, x in all_fwd_angles]
                    passing_rev_angles_idxs = [j for j, x in all_rev_angles if angleRangeCheck(x, native_angle, theta)]
                    fwd_axis_hits.append((start + i, passing_fwd_angles_idxs, passing_rev_angles_idxs))
            # end for

            rev_axis_hits = []
            for i, point in enumerate(this_rev_pts):
                difference = naxis_pts - point
                inner1d(difference, difference, out=delta)
                neighbor_min_delta_idx = np.argmin(delta)
                if delta[neighbor_min_delta_idx] < rsquared2:
                    neighbor_axis_pt = naxis_pts[neighbor_min_delta_idx]
                    # a. angle between vector from neighbor axis at minimum delta to this axis_pt
                    #   and the vector from the neighbor axis at minimum delta to neighbor_fwds_pts
                    v1 = normalize(this_axis_pts[i] - neighbor_axis_pt)
                    # project point onto plane normal to axis
                    v1 = normalize(v1 - dot(v1, direction)*direction)

                    v2 = normalize(nfwd_pts[neighbor_min_delta_idx] - neighbor_axis_pt)
                    # relative_angle = math.acos(np.dot(v1, v2))  # angle
                    # get signed angle between
                    relative_angle = math.atan2(dot(cross(v1, v2), direction), dot(v1, v2))
                    # print(id_num, 'r', relative_angle, v1, v2)
                    # b. fwd pt angle relative to first base in virtual helix
                    native_angle = angleNormalize(eulerZ + tpb*neighbor_min_delta_idx - relative_angle)

                    # print("REV %d around %d relative_angle %0.2f, base_angle: %0.2f" %
                    #     (   id_num, neighbor_id,
                    #         math.degrees(relative_angle),
                    #         math.degrees(angleNormalize(tpb*neighbor_min_delta_idx))
                    #         ))
                    # print(math.degrees(native_angle), math.degrees(angleNormalize(tpb*neighbor_min_delta_idx + relative_angle)))

                    all_fwd_angles = [(j, angleNormalize(eulerZ - tpb*j)) for j in range(max(neighbor_min_delta_idx - half_period, 0),
                                                                                         min(neighbor_min_delta_idx + half_period, size))]
                    passing_fwd_angles_idxs = [j for j, x in all_fwd_angles if angleRangeCheck(x, native_angle, theta)]
                    all_rev_angles = [(j, angleNormalize(x + mgroove)) for j, x in all_fwd_angles]
                    passing_rev_angles_idxs = [j for j, x in all_rev_angles if angleRangeCheck(x, native_angle, theta)]
                    # print(math.degrees(native_angle), 'r', [math.degrees(x) for j, x in all_rev_angles if angleRangeCheck(x, native_angle, theta) ])
                    rev_axis_hits.append((start + i, passing_fwd_angles_idxs, passing_rev_angles_idxs))
            # end for
            per_neighbor_hits[neighbor_id] = (fwd_axis_hits, rev_axis_hits)
        # end for
        return per_neighbor_hits
    # end def

    def queryIdNumNeighbor(self, id_num, neighbors, index=None):
        """Get indices of all virtual helices phosphates within a bond
        length of each phosphate for the id_num Virtual Helix.

        Args:
            id_num (int): virtual helix ID number
            neighbors (array-like): neighbors of id_num
            index_slice (tuple):  optional, of :obj:`int` (start_index, length) into a virtual
                helix

        Returns:
            dict: of :obj:`tuple` of form::

                neighbor_id_num: (fwd_hit_list, rev_hit_list)

            where each list has the form:

                [(id_num_index, forward_neighbor_idxs, reverse_neighbor_idxs), ...]]

        Raises:
            ValueError:
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise ValueError("offset_and_size is None for {}".format(id_num))
        else:
            offset, size = offset_and_size
        bpr, tpr = self.vh_properties.loc[id_num,
                                          ['bases_per_repeat', 'turns_per_repeat']]
        bases_per_turn = bpr / tpr
        if index is None:
            start, length = 0, size
        else:
            half_period = bpr // 2
            if size - index < bpr:
                start, length = size - bpr, bpr
            else:
                start, length = max(index - half_period, 0), bpr
        # norm = np.linalg.norm
        # cross = np.cross
        # dot = np.dot
        # normalize = self.normalize
        PI = math.pi
        # TWOPI = 2*PI
        RADIUS = self._radius
        BW = self._BASE_WIDTH

        # theta, radius = self.radiusForAngle(alpha, RADIUS, bases_per_turn, BW)
        # convert to a list since we can't speed this loop up without cython or something
        # axis_pts = self.axis_pts
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        # this_axis_pts = axis_pts[offset + start:offset + start + length].tolist()
        this_fwd_pts = fwd_pts[offset + start:offset + start + length].tolist()
        this_rev_pts = rev_pts[offset + start:offset + start + length].tolist()

        """TODO: decide how we want to handle maintaining bond length
        ideal adjacent ANTI-PARALLEL xover strands project to a plane normal
        to the helical axis and point in the SAME direction

        ideal adjacent PARALLEL xover strands  project to a plane normal
        to the helical axis and point in the OPPOSITE directions

        NOTE:
        For now we use zdelta to get the right results for this 2.5 release
        for PARALLEL and ANTI-PARALLEL.
        """
        # 1. compute generallized r squared values for an ideal crossover of
        # both types
        half_twist_per_base = PI/bases_per_turn
        # r2_radial = (2.*RADIUS*(1. - math.cos(half_twist_per_base)))**2
        # r2_tangent = (2.*RADIUS*math.sin(half_twist_per_base))**2
        # r2_axial = BW*BW

        # MISALIGNED by 27.5% twist per base so that's 1.55*half_twist_per_base
        # ma_f = 1.55 # NC should be this if we wanted to be strict
        ma_f = 2.55  # NC changed to this to show all xovers in legacy Honeycomb
        r2_radial = (RADIUS*((1. - math.cos(half_twist_per_base)) +
                             (1. - math.cos(ma_f*half_twist_per_base))))**2
        r2_tangent = (RADIUS*(math.sin(half_twist_per_base) +
                              math.sin(ma_f*half_twist_per_base)))**2
        r2_axial = BW*BW

        # print("r2:", r2_radial, r2_tangent, r2_axial)
        # 2. ANTI-PARALLEL
        rsquared_ap = r2_tangent + r2_radial
        rsquared_ap_min = 0
        rsquared_ap_max = rsquared_ap

        # 3. PARALLEL
        rsquared_p = r2_tangent + r2_radial + r2_axial
        rsquared_p_min = r2_axial
        rsquared_p_max = rsquared_p + 0.25*r2_axial
        per_neighbor_hits = {}

        fwd_axis_pairs = {}
        rev_axis_pairs = {}

        for neighbor_id in neighbors:
            offset, size = self.getOffsetAndSize(neighbor_id)

            # 1. Finds points that point at neighbors axis point
            nfwd_pts = fwd_pts[offset:offset + size]
            nrev_pts = rev_pts[offset:offset + size]

            # direction = self.directions[neighbor_id]
            len_neighbor_pts = len(nfwd_pts)
            delta = self.delta3D_scratch
            if len_neighbor_pts != len(delta):
                self.delta3D_scratch = delta = np.empty((len_neighbor_pts,), dtype=float)

            fwd_axis_hits = []
            for i, point in enumerate(this_fwd_pts):
                difference = nfwd_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                f_idxs = np.where((delta > rsquared_p_min) &
                                  (delta < rsquared_p_max) &
                                  (zdelta > 0.3*r2_axial) &
                                  (zdelta < 1.1*r2_axial)
                                  )[0].tolist()
                difference = nrev_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                r_idxs = np.where((delta > rsquared_ap_min) &
                                  (delta < rsquared_ap_max) &
                                  (zdelta < 0.3*r2_axial))[0].tolist()
                if f_idxs or r_idxs:
                    fwd_axis_hits.append((start + i, f_idxs, r_idxs))
            # end for

            # Scan for pairs of bases in AP xovers
            idx_last = -2
            fwd_axis_pairs = {}
            isAGreaterThanB_Z = self.isAGreaterThanB_Z
            for i, f_idxs, r_idxs in fwd_axis_hits:
                if r_idxs:
                    if idx_last + 1 == i:
                        # print("pair", idx_last, i)
                        fwd_axis_pairs[idx_last] = (True, neighbor_id)  # 5 prime  most strand
                        fwd_axis_pairs[i] = (False, neighbor_id)        # 3 prime most strand
                    idx_last = i
                if f_idxs:
                    for idxB in f_idxs:
                        if isAGreaterThanB_Z(id_num, i, neighbor_id, idxB):
                            fwd_axis_pairs[i] = (False, neighbor_id)
                        else:
                            fwd_axis_pairs[i] = (True, neighbor_id)

            rev_axis_hits = []
            for i, point in enumerate(this_rev_pts):
                difference = nfwd_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                f_idxs = np.where((delta > rsquared_ap_min) &
                                  (delta < rsquared_ap_max) &
                                  (zdelta < 0.3*r2_axial))[0].tolist()

                difference = nrev_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                r_idxs = np.where((delta > rsquared_p_min) &
                                  (delta < rsquared_p_max) &
                                  (zdelta > 0.3*r2_axial) &
                                  (zdelta < 1.1*r2_axial)
                                  )[0].tolist()
                if f_idxs or r_idxs:
                    rev_axis_hits.append((start + i, f_idxs, r_idxs))
            # end for

            # Scan for pairs of bases in AP xovers
            idx_last = -2
            for i, f_idxs, r_idxs in rev_axis_hits:
                if f_idxs:
                    if idx_last + 1 == i:
                        # print("pair", idx_last, i)
                        rev_axis_pairs[idx_last] = (False, neighbor_id)    # 3 prime  most strand
                        rev_axis_pairs[i] = (True, neighbor_id)            # 5 prime most strand
                    idx_last = i
                if r_idxs:
                    for idxB in r_idxs:
                        if isAGreaterThanB_Z(id_num, i, neighbor_id, idxB):
                            rev_axis_pairs[i] = (True, neighbor_id)
                        else:
                            rev_axis_pairs[i] = (False, neighbor_id)

            per_neighbor_hits[neighbor_id] = (fwd_axis_hits, rev_axis_hits)
        # end for
        return per_neighbor_hits, (fwd_axis_pairs, rev_axis_pairs)
    # end def

    @staticmethod
    def angleNormalize(angle):
        """Ensure angle is normalized to [0, 2*PI]

        Args:
            angle (float): radians

        Returns:
            float:
        """
        TWOPI = 2*3.141592653589793
        return ((angle % TWOPI) + TWOPI) % TWOPI

    @staticmethod
    def angleRangeCheck(angle, target_angle, theta):
        """See if `angle` falls in range
        `[target_angle - theta`, target_angle + theta]`
        Accounting for wrap around

        Args:
            angle (float): radians
            target_angle (float): radians
            theta (float): radians

        Returns:
            bool: True if in range, False otherwise
        """
        PI = 3.141592653589793
        TWOPI = 2*PI
        diff = (angle - target_angle + PI) % TWOPI - PI
        return -theta <= diff and diff <= theta

    @staticmethod
    def radiusForAngle(angle, radius_in, bases_per_turn, base_width):
        """Calculate the distance from the center axis of
        a virtual helix with radius_in radius to a bounds of
        an arc on tangent virtual helix with the same radius
        the arc center is on the line connecting the two
        virtual helices.  Using trig identities and Pythagorean theorem
        additionally we need to account the axial distance between bases
        (the BASE_WIDTH)

        Args:
            angle (float):
            radius_in (float):
            bases_per_turn (float):
            base_width (float):

        Returns:
            tuple: of :obj:`float`, angle and radius
        """
        theta = math.radians(angle) / 2
        R = radius_in*math.sqrt(5 - 4*math.cos(theta))
        x = base_width*(angle/2/360*bases_per_turn)
        x = 0
        return theta, math.sqrt(R*R + x*x)
    # end def

    def _projectionPointOnPlane(self, id_num, point):
        """VirtualHelices are straight for now so only one direction for the axis
        assume directions are alway normalized, so no need to divide by the
        magnitude of the direction vector squared

        Args:
            id_num (int): virtual helix ID number
            point (array-like): length 3

        Returns:
            array-like: length 3
        """
        direction = self.directions[id_num]
        return point - np.dot(point, direction)*direction
    # end

    def subStepSize(self):
        """Get the substep size

        Returns:
            int:
        """
        return self._SUB_STEP_SIZE
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def partType(self):
        """Get this type of Part

        Returns:
            cnenum.PartType.NUCLEICACIDPART
        """
        return PartType.NUCLEICACIDPART
    # end def

    def isZEditable(self):
        """Return whether we move a Virtual Helix in the Z direction

        Returns:
            bool:
        """
        return self._group_properties['point_type'] == PointType.Z_ONLY
    # end def

    def getVirtualHelicesInArea(self, rect):
        """
        Args:
            rect (array-like): of :obj:`float` rectangle defined by::

                    ( x1, y1, x2, y2)

                definining the lower left and upper right corner of the
                rectangle respetively


        Returns:
            set: set of ID numbers in the Rectangle
        """
        res = self._queryVirtualHelixOriginRect(rect)
        return set(res)
    # end def

    def getVirtualHelixAtPoint(self, point, id_num=None):
        """ Fix this to get the closest result
        """
        radius = self._radius
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
        radius = self._radius
        # add a margin of 0.001 to account for floating point errors
        res = self.queryVirtualHelixOrigin(2 * radius - 0.001, point)
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
        neighbors = literal_eval(self.vh_properties.loc[id_num, 'neighbors'])
        # alpha = self.getProperty('crossover_span_angle')

        # idx = None # FORCE this for now to prevent animation GC crashes

        # per_neighbor_hits = self._queryIdNumRangeNeighbor(id_num, neighbors,
        #                                                 alpha, index=idx)
        per_neighbor_hits = self.queryIdNumNeighbor(id_num, neighbors, index=idx)
        return per_neighbor_hits

    # end def
    def boundDimensions(self, scale_factor=1.0):
        """Returns a tuple of rectangle definining the XY limits of a part"""
        DMIN = 10  # 30
        xLL, yLL, xUR, yUR = self.getVirtualHelixOriginLimits()
        if xLL > -DMIN:
            xLL = -DMIN
        if yLL > -DMIN:
            yLL = -DMIN
        if xUR < DMIN:
            xUR = DMIN
        if yUR < DMIN:
            yUR = DMIN
        return xLL * scale_factor, yLL * scale_factor, xUR * scale_factor, yUR * scale_factor
    # end def

    def getSequences(self):
        """getSequences"""
        # s = "Start\tEnd\tColor\tMod5\tSequence\tMod3\tAbstractSequence\n"
        keys = ['Start','End','Color', 'Mod5',
                'Sequence','Mod3','AbstractSequence']
        out = {key: [] for key in keys}
        for oligo in self._oligos:
            oligo.sequenceExport(out)
        df = pd.DataFrame(out, columns=keys)
        s = df.to_csv(index=False)
        return s

    def getIdNums(self):
        """return the set of all ids used"""
        return self.reserved_ids
    # end def

    def getLoopOligos(self):
        """
        Returns oligos with no 5'/3' ends. Used by
        actionExportSequencesSlot in documentcontroller to validate before
        exporting staple sequences.
        """
        loop_olgs = []
        for o in list(self.oligos()):
            if o.isLoop():
                loop_olgs.append(o)
        return loop_olgs

    def maxBaseIdx(self, id_num):
        o_and_s = self.getOffsetAndSize(id_num)
        size = 42 if o_and_s is None else o_and_s[1]
        return size
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
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
                o.applyColor('#ff0000')
            else:
                total_passed += 1
        # end for
    # end def

    def remove(self, use_undostack=True):
        """This method assumes all strands are and all VirtualHelices are
        going away, so it does not maintain a valid model state while
        the command is being executed.
        Everything just gets pushed onto the undostack more or less as is.
        Except that strandSets are actually cleared then restored, but this
        is neglible performance wise.  Also, decorators/insertions are assumed
        to be parented to strands in the view so their removal Signal is
        not emitted.  This causes problems with undo and redo down the road
        but works as of now.

        TODO: figure out how to decrement NucleicAcidPart._count as appropriate
        or to change that altogether
        """
        if use_undostack:
            us = self.undoStack()
            us.beginMacro("Delete Part")
        # remove strands and oligos
        self.removeAllOligos(use_undostack)
        # remove VHs
        for id_num in list(self.getIdNums()):
            self.removeVirtualHelix(id_num, use_undostack=use_undostack)
        # end for
        # remove the part
        cmdlist = [RemoveInstanceCommand(self, inst) for inst in self._instances]
        if use_undostack:
            for e in cmdlist:
                us.push(e)
            us.endMacro()
        else:
            for e in cmdlist:
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

    def _addOligoToSet(self, oligo, emit_signals=False):
        """This is an exceptional private method not part of the API as this
        is to be called only by an Oligo.

        Args:
            oligo (Oligo): Oligo to add to the Part
        """
        self._oligos.add(oligo)
        if emit_signals:
            self.partOligoAddedSignal.emit(self, oligo)
    # end def

    def _removeOligoFromSet(self, oligo, emit_signals=False):
        """ Not a designated method
        (there exist methods that also directly
        remove parts from self._oligos)
        """
        try:
            self._oligos.remove(oligo)
            if emit_signals:
                oligo.oligoRemovedSignal.emit(self, oligo)
        except KeyError:
            print(util.trace(5))
            print("error removing oligo", oligo)
    # end def

    def createVirtualHelix(self, x, y, z=0.0, length=42, id_num=None,
                           properties=None, safe=True, use_undostack=True):
        """Create new VirtualHelix by calling CreateVirtualHelixCommand.

        Args:
            x (float): x coordinate
            y (float): y coordinate
            z (float): z coordinate
            length (int): Size of VirtualHelix.
            properties (tuple): Tuple of two lists: `keys` and `values`, which
                contain full set of properties for the VirualHelix.
            safe (bool): Update neighbors otherwise,
                neighbors need to be explicitly updated

            use_undostack (bool): Set to False to disable undostack for bulk
                operations such as file import.
        """
        c = CreateVirtualHelixCommand(self, x, y, z, length, id_num=id_num, properties=properties, safe=safe)
        util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def removeVirtualHelix(self, id_num, use_undostack=True):
        """Removes a VirtualHelix from the model. Accepts a reference to the
        VirtualHelix, or a (row,col) lattice coordinate to perform a lookup.
        """
        if use_undostack:
            self.undoStack().beginMacro("Delete VirtualHelix")
        fwd_ss, rev_ss = self.getStrandSets(id_num)
        fwd_ss.removeAllStrands(use_undostack)
        rev_ss.removeAllStrands(use_undostack)
        c = RemoveVirtualHelixCommand(self, id_num)
        if use_undostack:
            self.undoStack().push(c)
            self.undoStack().endMacro()
        else:
            c.redo()
    # end def

    def createXover(self, strand5p, idx5p, strand3p, idx3p, update_oligo=True, use_undostack=True):
        """Xovers are ALWAYS installed FROM the 3' end of the 5' most
        strand (strand5p) TO the 5' end of the 3' most strand (strand3p)

        Args:
            strand5p (Strand):
            idx5p (int): index of the 3 prime end of the xover in strand5p
            strand3p (Strand):
            idx3p (int): index of the 5 prime end of the xover in strand3p
        """
        # test for reordering malformed input
        # if (strand5p.idx5Prime() == idx5p and
        #     strand3p.idx3Prime() == idx3p):
        #     strand5p, strand3p = strand3p, strand5p
        #     idx5p, idx3p = idx3p, idx5p

        if not strand3p.canInstallXoverAt(idx3p, strand5p, idx5p):
            print("createXover: no xover can be installed here")
            print("strand 5p", strand5p)
            print("\tidx: %d\tidx5p: %d\tidx3p: %d" %
                  (idx5p, strand5p.idx5Prime(), strand5p.idx3Prime())
                  )
            print("strand 3p", strand3p)
            print("\tidx: %d\tidx5p: %d\tidx3p: %d" %
                  (idx3p, strand3p.idx5Prime(), strand3p.idx3Prime())
                  )
            # raise ValueError("Part.createXover:")
            return

        ss5p = strand5p.strandSet()
        ss3p = strand3p.strandSet()

        if use_undostack:
            self.undoStack().beginMacro("Create Xover")

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
                    xo_strand3 = c.strand_high if ss3p.isForward() else c.strand_low
                    # adjust the target 5prime strand, always necessary if a split happens here
                    if idx5p > idx3p and ss3p.isForward():
                        temp5 = xo_strand3
                    elif idx5p < idx3p and not ss3p.isForward():
                        temp5 = xo_strand3
                    else:
                        temp5 = c.strand_low if ss3p.isForward() else c.strand_high
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
                idx5p = idx3p
                """
                if the strand was split for the strand3p, then we need to
                adjust the strandset index
                """
                if c:
                    # the insertion index into the set is increases
                    if ss3p.isForward():
                        idx5p = idx3p + 1 if idx5p > idx3p else idx3p
                    else:
                        idx5p = idx3p + 1 if idx5p > idx3p else idx3p
                if ss5p.strandCanBeSplit(temp5, idx5p):
                    d = SplitCommand(temp5, idx5p)
                    # cmds.append(d)
                    xo_strand5 = d.strand_low if ss5p.isForward() else d.strand_high
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
                        xo_strand3 = c.strand_high if ss3p.isForward() else c.strand_low
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
                        xo_strand5 = d.strand_low if ss5p.isForward() else d.strand_high
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
        if strand5p.connection3p() == strand3p:
            c = RemoveXoverCommand(self, strand5p, strand3p)
            util.doCmd(self, c, use_undostack=use_undostack)
    # end def

    def xoverSnapTo(self, strand, idx, delta):
        """
        Returns the nearest xover position to allow snap-to behavior in
        resizing strands via dragging selected xovers.
        """
        # strand_type = strand.strandType()
        # if delta > 0:
        #     min_idx, max_idx = idx - delta, idx + delta
        # else:
        #     min_idx, max_idx = idx + delta, idx - delta

        # # determine neighbor strand and bind the appropriate prexover method
        # lo, hi = strand.idxs()
        # if idx == lo:
        #     connected_strand = strand.connectionLow()
        #     preXovers = self.getPreXoversHigh
        # else:
        #     connected_strand = strand.connectionHigh()
        #     preXovers = self.getPreXoversLow
        # connected_vh = connected_strand.idNum()

        # # determine neighbor position, if any
        # neighbors = self.getVirtualHelixNeighbors(strand.idNum())
        # if connected_vh in neighbors:
        #     neighbor_idx = neighbors.index(connected_vh)
        #     try:
        #         new_idx = util.nearest(idx + delta,
        #                             preXovers(strand_type,
        #                                         neighbor_idx,
        #                                         min_idx=min_idx,
        #                                         max_idx=max_idx)
        #                             )
        #         return new_idx
        #     except ValueError:
        #         return None  # nearest not found in the expanded list
        # else:  # no neighbor (forced xover?)... don't snap, just return
        return idx + delta
    # end def

    def newPart(self):
        return Part(self._document)
    # end def

    def setVirtualHelixSize(self, id_num, new_size, use_undostack=True):
        old_size = self.vh_properties.loc[id_num, 'length']
        delta = new_size - old_size
        if delta > 0:
            c = ResizeVirtualHelixCommand(self, id_num, True, delta)
            util.doCmd(self, c, use_undostack=use_undostack)
        else:
            err = "shrinking VirtualHelices not supported yet: %d --> %d" % (old_size, new_size)
            raise NotImplementedError(err)
    # end def

    def translateVirtualHelices(self, vh_set, dx, dy, dz, finalize,
                                use_undostack=False):
        if use_undostack:
            c = TranslateVirtualHelicesCommand(self, vh_set, dx, dy, dz)
            if finalize:
                util.finalizeCommands(self, [c], desc="Translate VHs")
                # only emit this on finalize due to cost.
            else:
                util.doCmd(self, c, use_undostack=True)
        else:
            self._translateVirtualHelices(vh_set, dx, dy, dz, False)
    # end def

    def _translateVirtualHelices(self, vh_set, dx, dy, dz, do_deselect):
        """
        do_deselect tells a view to clear selections that might have
        undesirable Object parenting to make sure the translations are set
        correctly.  set to True when "undo-ing"
        """
        threshold = 2.1*self._radius
        # 1. get old neighbor list
        old_neighbors = set()
        for id_num in vh_set:
            neighbors = self._getVirtualHelixOriginNeighbors(id_num, threshold)
            old_neighbors.update(neighbors)
        # 2. move in the virtual_helix_group
        self._translateCoordinates(vh_set, (dx, dy, dz))
        # 3. update neighbor calculations
        new_neighbors = set()
        for id_num in vh_set:
            neighbors = self._getVirtualHelixOriginNeighbors(id_num, threshold)
            try:
                self.setVirtualHelixProperties(id_num, 'neighbors', str(list(neighbors)))
            except:
                print("neighbors", list(neighbors))
                raise
            new_neighbors.update(neighbors)

        # now update the old and new neighbors that were not in the vh set
        left_overs = new_neighbors.union(old_neighbors).difference(vh_set)
        for id_num in left_overs:
            neighbors = self._getVirtualHelixOriginNeighbors(id_num, threshold)
            try:
                self.setVirtualHelixProperties(id_num, 'neighbors', str(list(neighbors)))
            except:
                print("neighbors", list(neighbors))
                raise
        self.partVirtualHelicesTranslatedSignal.emit(self, vh_set, left_overs, do_deselect)
    # end def

    ### PRIVATE SUPPORT METHODS ###

    ### PUBLIC SUPPORT METHODS ###
    def shallowCopy(self):
        raise NotImplementedError
    # end def

    def _deepCopy(self):
        """Deep copy is used to create an entirely new copy of a Part in
        memory, rather than an instance pointer to an existing part.

        It works as follows:

        1. Create a new part (the "copy").
        2. _deepCopy the VirtualHelices from the "original" part.
        3. Map the original part's Oligos onto the copy's Oligos, using lookups
            of the hash id_num and the StrandSet from step 2.

        """
        # 1) new part
        new_part = self.newPart()
        # 2) Copy VirtualHelix Group
        new_part = self.copy(self._document, new_object=new_part)
        # 3) Copy oligos, populating the strandsets
        for oligo, val in self._oligos:
            strandGenerator = oligo.strand5p().generator3pStrand()
            new_oligo = oligo._deepCopy(new_part)
            last_strand = None
            for strand in strandGenerator:
                id_num = strand.idNum()
                new_strandset = self.getStrandSets(id_num)[strand.strandType()]
                new_strand = strand._deepCopy(new_strandset, new_oligo)
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
        return new_part
    # end def

    def getImportVirtualHelixOrder(self):
        """ the order of VirtualHelix items in the path view
        each element is the coord of the virtual helix
        """
        return self.getProperty('virtual_helix_order')
    # end def

    def setImportedVHelixOrder(self, ordered_id_list, check_batch=True):
        """Used on file import to store the order of the virtual helices.
        TODO: do something with check_batch or remove it
        """
        self.setProperty('virtual_helix_order', ordered_id_list)
    # end def

    def oligos(self):
        return self._oligos
    # end def

    def getNewAbstractSegmentId(self, segment):
        low_idx, high_idx = segment
        seg_id = next(self._abstract_segment_id)
        offset = self._current_base_count
        segment_length = (high_idx - low_idx + 1)
        self._current_base_count = offset + segment_length
        return seg_id, offset, segment_length
    # end def

    def initializeAbstractSegmentId(self):
        self._abstract_segment_id = icount(0)
        self._current_base_count = 0
    # end def

    def setAbstractSequences(self, emit_signals=False):
        """Reset, assign, and display abstract sequence numbers."""
        # reset all sequence numbers
        print("setting abstract sequence")
        for oligo in self._oligos:
            oligo.clearAbstractSequences()

        self.initializeAbstractSegmentId()

        for oligo in self._oligos:
            oligo.applyAbstractSequences()

        # display new sequence numbers
        for oligo in self._oligos:
            oligo.displayAbstractSequences()
            if emit_signals:
                oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def

    ### PUBLIC METHODS FOR QUERYING THE MODEL ###
    def activeIdNum(self):
        return self._active_id_num
    # end def

    def setActive(self, is_active):
        doc = self._document
        current_active_part = doc.activePart()
        if is_active:
            if current_active_part == self:
                # print("Part already active", current_active_part)
                return
            doc.setActivePart(self)
            if current_active_part is not None:
                # print("Part deactivating by proxy", current_active_part)
                current_active_part.setActive(False)
        # print("Part maybe activating", self, is_active)
        self.is_active = is_active
        self.partActiveChangedSignal.emit(self, is_active)
    # end def

    def activeBaseIndex(self):
        return self._active_base_index
    # end def

    def clearActiveVirtualHelix(self):
        self.active_base_info = active_base_info = ()
        self._active_id_num = id_num = -1
        self.partActiveVirtualHelixChangedSignal.emit(self, id_num)
        self.partActiveBaseInfoSignal.emit(self, active_base_info)
    # end def

    def setActiveVirtualHelix(self, id_num, is_fwd, idx=None):
        abi = (id_num, is_fwd, idx, -1)
        if self.active_base_info == abi:
            return
        else:
            self._active_id_num = id_num
            self.active_base_info = abi
        self.partActiveVirtualHelixChangedSignal.emit(self, id_num)
        self.partActiveBaseInfoSignal.emit(self, abi)
    # end def

    def setActiveBaseInfo(self, info):
        """ to_vh_num is not use as of now and may change
        Args:
            info (Tuple): id_num, is_fwd, idx, to_vh_num

        """
        if info != self.active_base_info:
            # keep the info the same but let views know it's not fresh
            if info is not None:
                self.active_base_info = info
            self.partActiveBaseInfoSignal.emit(self, info)
    # end def

    def isVirtualHelixActive(self, id_num):
        """Is the argument id_num the active virtual_helix?

        Args:
            id_num (int): ID number

        Returns:
            bool
        """
        return id_num == self._active_id_num
    # end def

    def insertions(self):
        """Return dictionary of insertions."""
        return self._insertions
    # end def

    def dumpInsertions(self):
        """ Serialize insertions

        Yields:
            tuple: (id_num, idx, length)
        """
        for id_num, id_dict in self._insertions.items():
            for idx, insertion in id_dict.items():
                yield (id_num, idx, insertion.length())
    # end def

    def isSelected(self):
        """Is this Part selected

        Returns:
            bool
        """
        return self.is_selected
    # end def

    ### PUBLIC METHODS FOR EDITING THE MODEL ###
    def setSelected(self, is_selected):
        """Set the selectiveness of the Part

        Args:
            is_selected (bool):
        """
        if is_selected != self._selected:
            self._selected = is_selected
            self.partSelectedChangedSignal.emit(self, is_selected)
    # end def

    def getModID(self, strand, idx):
        """Get the ID of a Mod

        Args:
            strand (Strand):
            idx (int):

        Returns:
            str: ID of the Mod
        """
        id_num = strand.idNum()
        strandtype = strand.strandType()
        key = "{},{},{}".format(id_num, strandtype, idx)
        mods_strand = self._mods['ext_instances']
        if key in mods_strand:
            return mods_strand[key]
    # end def

    def getStrandModSequence(self, strand, idx, mod_type):
        """Geet sequence of a Mod

        Args:
            strand (Strand):
            idx (int):
            mod_type (int): 0, 1, or 2

        Returns:
            str
        """
        mid = self.getModID(strand, idx)
        return self._document.getModSequence(mid, mod_type)

    def _getModKeyTokens(self, key):
        """ Get tokens from key
        Args:
            key (str):

        Returns:
            tuple: id_num, is_fwd, idx
        """
        keylist = key.split(',')
        id_num = int(keylist[0])
        is_fwd = int(keylist[1])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[2])
        return id_num, is_fwd, idx
    # end def

    def getModStrandIdx(self, key):
        """ Convert a key of a mod instance relative to a part
        to a strand and an index

        Args:
            key (str):

        Returns:
            tuple: Strand, int
        """
        keylist = key.split(',')
        id_num = int(keylist[0])
        is_fwd = int(keylist[1])    # enumeration of StrandType.FWD or StrandType.REV
        idx = int(keylist[2])
        strand = self.getStrand(is_fwd, id_num, idx)
        return strand, idx
    # end def

    def addModInstance(self, id_num, idx, is_rev, is_internal, mid):
        """Add an instance of a Mod given the Mod ID

        Args:
            id_num (int):
            idx (int):
            is_rev (bool):
            is_internal (bool):
            mid (str): Mod ID
        """
        key = "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        if key in mods_strands:
            self.removeModInstance(id_num, idx, is_rev, is_internal, mid)
        self._document.addModInstance(mid, is_internal, self, key)
        self._addModInstanceKey(key, mods_strands, mid)
    # end def

    def _addModInstanceKey(self, key, mods_strands, mid):
        """
        """
        mods_strands[key] = mid  # add to strand lookup
    # end def

    def addModStrandInstance(self, strand, idx, mid, is_internal=False):
        id_num = strand.idNum()
        strandtype = strand.strandType()
        if mid is not None:
            self.addModInstance(id_num, idx, strandtype, False, mid)
    # end def

    def removeModInstance(self, id_num, idx, is_rev, is_internal, mid):
        key = "{},{},{}".format(id_num, is_rev, idx)
        mods_strands = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        self._document.removeModInstance(mid, is_internal, self, key)
        if key in mods_strands:
            del mods_strands[key]
    # end def

    def removeModStrandInstance(self, strand, idx, mid, is_internal=False):
        """
        Args:
            strand (Strand):
            idx (int):
            mid (str): Mod ID
            is_internal (bool, optional): Default is False
        """
        id_num = strand.idNum()
        strandtype = strand.strandType()
        if mid is not None:
            self.removeModInstance(id_num, idx, strandtype, is_internal, mid)
    # end def

    def dumpModInstances(self, is_internal):
        """Serialize a Mod Instance

        Args:
            is_internal (bool):

        Yields:
            tuple: (id_num, is_fwd, idx, mid)
        """
        mods = self._mods['int_instances'] if is_internal else self._mods['ext_instances']
        for key, mid in mods:
            id_num, is_fwd, idx = self._getModKeyTokens(key)
            yield (id_num, is_fwd, idx, mid)
    # end def
# end class


def distanceToPoint(origin, direction, point):
    """Distance of a line to a point

    See:
    http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html

    Args:
        origin (array_like): of :obj:`float`, length 3, a starting point for the line
        direction (array-like): of :obj:`float`, length 3, the direction of the line
        point (array-like): of :obj:`float`, length 3, the point of interest

    Returns:
        float: R squared distance
    """
    direction_distance = np.dot(point - origin, direction)
    # point behind the ray
    if direction_distance < 0:
        diff = origin - point
        return diff*diff

    v = (direction * direction_distance) + origin
    diff = v - point
    return diff*diff
# end def


def remapSlice(start, stop, length):
    """Remap a slice to positive indices for a given
    length

    Args:
        start (int): index
        stop (int): index
        length (int): span

    Returns
        tuple: of :obj:`int`, positive start and stop index

    Raises:
        IndexError:
    """
    new_start = length - start if start < 0 else start
    new_stop = length - stop if stop < 0 else stop

    if new_stop < new_start:
        raise IndexError("Stop {} must be greater than or equal to start {}".format(stop, start))
    return start, stop
# end def
