# -*- coding: utf-8 -*-
import math
from heapq import heapify, heappush, nsmallest
from bisect import bisect_left

import numpy as np
import pandas as pd
from collections import deque, Iterable
from cadnano.strandset import StrandSet
from cadnano.enum import StrandType
from cadnano.cnobject import CNObject

"""
inner1d(a, a) is equivalent to np.einsum('ik,ij->i', a, a)
equivalent to np.sum(a*a, axis=1)
but faster
"""
from numpy.core.umath_tests import inner1d

DEFAULT_CACHE_SIZE = 20

def _defaultProperties(id_num):
    props = [
    ('name', "vh%d" % (id_num)),
    ('is_visible', True),
    ('color', '#00000000'),
    # ('eulerZ', 17.143*2),    # 0.5*360/10.5
    ('eulerZ', 0.),
    ('scamZ', 10.),
    ('neighbor_active_angle', 0.0),
    ('neighbors', '[]'),
    ('bases_per_repeat', 21),
    ('turns_per_repeat', 2),
    ('repeat_hint', 2), # used in path view for how many repeats to display PXIs
    ('helical_pitch', 1.),
    ('minor_groove_angle', 180.), #171.),
    ('length', -1),
    ('z', 0.0)
    ]
    return tuple(zip(*props))
# end def

Z_PROP_INDEX = -1 # index for Dataframe.iloc calls

def _defaultDataFrame(size):
    dummy_id_num = 999
    columns, row = _defaultProperties(dummy_id_num)
    df = pd.DataFrame([row for i in range(size)], columns=columns)
    return df
# end def
DEFAULT_SIZE = 256
DEFAULT_FULL_SIZE = DEFAULT_SIZE*48
DEFAULT_RADIUS = 1.125

class VirtualHelixGroup(CNObject):
    """This is composed of a group of arrays
    that:

    1. contain the coordinates of every virtual base stored in their index
       order per id_num
    2. contains the id_num per coordinate

    Uses *args and **kwargs to make subclassing easier

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(self, *args, **kwargs):
        """
        """
        self._document = document = kwargs.get('document', None)
        super(VirtualHelixGroup, self).__init__(document)
        do_copy = kwargs.get('do_copy', False)
        if do_copy:
            return

        self._radius = DEFAULT_RADIUS     # probably a property???

        # 1. per virtual base pair allocations
        self.total_points = 0
        self.axis_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        # self.axis_pts[:, 2] = 0.0
        self.fwd_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        self.rev_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float)
        self.id_nums = np.full((DEFAULT_FULL_SIZE,), -1, dtype=int)
        self.indices = np.zeros((DEFAULT_FULL_SIZE,), dtype=int)

        # 2. per virtual helix allocations
        self.total_id_nums = 0 # should be equal to len(self.reserved_ids)

        self._origin_pts = np.full((DEFAULT_SIZE, 2), np.inf, dtype=float)
        """For doing 2D X,Y manipulation for now.  keep track of
        XY position of virtual helices
        """

        self.origin_limits = (0., 0., 0., 0.)

        self.directions = np.zeros((DEFAULT_SIZE, 3), dtype=float)

        self._offset_and_size = [None]*DEFAULT_SIZE
        '''book keeping for fast lookup of indices for insertions and deletions
        and coordinate points
        the length of this is the max id_num used
        '''

        self.reserved_ids = set()

        self.vh_properties = _defaultDataFrame(DEFAULT_SIZE)
        self._group_properties = {}

        self.fwd_strandsets = [None]*DEFAULT_SIZE
        self.rev_strandsets = [None]*DEFAULT_SIZE
        self.segment_dict = {}  # for tracking strand segments

        # Cache Stuff
        self._point_cache = None
        self._point_cache_keys = None
        self.resetPointCache()
        self._origin_cache = None
        self._origin_cache_keys = None
        self._resetOriginCache()

        # scratch allocations for vector calculations
        self.m3_scratch0 = np.zeros((3,3), dtype=float)
        self.m3_scratch1 = np.zeros((3,3), dtype=float)
        self.m3_scratch2 = np.zeros((3,3), dtype=float)
        self.eye3_scratch = np.eye(3, 3, dtype=float)    # don't change this
        self.delta2D_scratch = np.empty((1,), dtype=float)
        self.delta3D_scratch = np.empty((1,), dtype=float)

        # ID assignment
        self.recycle_bin = []
        self._highest_id_num_used = -1  # Used in _reserveHelixIDNumber
    # end def

    def _resetOriginCache(self):
        self._origin_cache = {}
        self._origin_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
    # end def

    def resetPointCache(self):
        self._point_cache = {}
        self._point_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
    # end def

    def getSize(self):
        """ Getter for the number of virtual helices in use

        Returns:
            int
        """
        return len(self.reserved_ids)
    # end def

    def document(self):
        """Document attribute getter

        Returns:
            Document: the :class:`Document` object
        """
        return self._document
    # end def

    def copy(self, document, new_object=None):
        """Copy all arrays and counters and create new StrandSets

        TODO: consider renaming this method

        Args:
            document (Document): :class:`Document` object
            new_object (:class:`VirtualHelixGroup`, optional): whether to copy
            into new_object or to allocate a new one internal to this method
            an allocated :class:`VirtualHelixGroup`
        """
        new_vhg = new_object
        if new_vhg is None:
            constructor = type(self)
            new_vhg = constructor(document=document, do_copy=True)
        if not isinstance(new_vhg, VirtualHelixGroup):
            raise ValueError("new_vhg {} is not an instance of a VirtualHelixGroup".format(new_vhg))
        new_vhg.total_points = self.total_points
        new_vhg.axis_pts = self.axis_pts.copy()
        new_vhg.fwd_pts = self.fwd_pts.copy()
        new_vhg.rev_pts = self.rev_pts.copy()
        new_vhg.id_nums = self.id_nums.copy()
        new_vhg.indices = self.indices.copy()

        new_vhg.total_id_nums = self.total_id_nums
        new_vhg.origin_pts = self.origin_pts
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

    def getOffsetAndSize(self, id_num):
        """Get the index offset of this ID into the point buffers

        Args:
            id_num (int): virtual helix ID number

        Returns:
            tuple: (:obj:`int`, :obj:`int`) or :obj:`None` of the form::

                (offset, size)

            into the coordinate arrays for a given ID number
        """
        offset_and_size = self._offset_and_size
        return offset_and_size[id_num] if id_num < len(offset_and_size) else None
    # end def

    def getNewIdNum(self):
        """Query the lowest available id_num. Internally id numbers are
        recycled when virtual helices are deleted

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

    def getVirtualHelixName(self, id_num):
        """getter for the name of a virtual helix

        Args:
            id_num (int): the ID number

        Returns:
            str: name of the virtual helix at `id_num`
        """
        return self.getVirtualHelixProperties(id_num, 'name')
    # end def

    def reserveIdNum(self, requested_id_num):
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

    def recycleIdNum(self, id_num):
        """The caller's contract is to ensure that id_num is not used in *any*
        helix at the time of the calling of this function (or afterwards, unless
        `reserveIdNumForHelix` returns the id_num again).

        Args:
            id_num (int): virtual helix ID number
        """
        heappush(self.recycle_bin, id_num)
        self.reserved_ids.remove(id_num)
    # end def

    def isIdNumUsed(self, id_num):
        """Test if an `id_num` is used by :class:`Part`

        Args:
            id_num (int): virtual helix ID number

        Returns:
            bool:   True if used False otherwise
        """
        return True if self.getOffsetAndSize(id_num) is not None else False
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
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size_tuple
        lo, hi = offset, offset + size
        return (self.axis_pts[lo:hi],
                self.fwd_pts[lo:hi],
                self.rev_pts[lo:hi] )
    # end def

    def getCoordinate(self, id_num, idx):
        """Given a id_num get the coordinate at a given index

        Args:
            id_num (int): virtual helix ID number
            idx (int): index

        Returns:
            ndarray: shape (3, 1) of :obj:`float`

        Raises:
            KeyError, IndexError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

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
            KeyError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        return self.origin_pts[id_num]
    # end def

    def getidNums(self):
        """Return a list of used id_nums

        Returns:
            list: of :obj:`int` of virtual helix ID numbers used
        """
        return [i for i, x in filter(lambda i, x: x is not None, enumerate(self._offset_and_size))]
    # end def

    def setVirtualHelixOriginLimits(self):
        """Set origin limits
        """
        valid_pts = np.where(self._origin_pts != np.inf)
        vps = self.origin_pts[valid_pts]
        vps = vps.reshape((len(vps)//2, 2))
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
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        return (self.fwd_strandsets[id_num], self.rev_strandsets[id_num])
    # end def

    def refreshSegments(self, id_num):
        """ Partition strandsets into overlapping segments

        Returns:
            Tuple(List(List(Tuple))):  segments for the forward and reverse
            strand

                `( [ [(start, end),...], ...], [ [(start, end),...], ...])`
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))
        fwd_ss = self.fwd_strandsets[id_num]
        rev_ss = self.rev_strandsets[id_num]

        self.segment_dict[id_num] = {}
        return self._refreshSegments(fwd_ss, rev_ss)
    # end def

    def _refreshSegments(self, fwd_ss, rev_ss):
        """ Testable private version

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
        lim_hi_endpoints = len(hi_endpoints) - 1
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
        return (self.fwd_strandsets[id_num].hasStrandAt(idx, idx),\
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
            ret = max(ret, fwd_strandsets[id_num].indexOfRightmostNonemptyBase(),
                            rev_strandsets[id_num].indexOfRightmostNonemptyBase())
        return ret
    # end def

    def translateCoordinates(self, id_nums, delta):
        """ delta is a sequence of floats of length 3
        for now support XY translation

        Args:
            id_nums (:obj:`sequence` of :obj:`int`): virtual helix ID numbers
            delta (:obj:`sequence` of :obj:`float`): 1x3 vector
        """
        self._resetOriginCache()
        self.resetPointCache()
        origin_pts = self.origin_pts
        delta_origin = delta[:2] # x, y only
        for id_num in id_nums:
            coord_pts, fwd_pts, rev_pts = self.getCoordinates(id_num)
            coord_pts += delta # use += to modify the view
            fwd_pts += delta # use += to modify the view
            rev_pts += delta # use += to modify the view
            # print("old origin", self.locationQt(id_num, 15./self.radius()))
            origin_pts[id_num, :] += delta_origin
            # print("new origin", self.locationQt(id_num, 15./self.radius()))
        try:
            self.vh_properties.iloc[list(id_nums), Z_PROP_INDEX] += delta[2]
        except:
            print(list(id_nums), Z_PROP_INDEX)
            raise
        self.setVirtualHelixOriginLimits()
    # end def

    def getIndices(self, id_num):
        """ return a view onto the numpy array for a
        given id_num

        Args:
            id_num (int): virtual helix ID number

        Returns:
            ndarray[int]: array of indices corresponding to points
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

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
            idx (:obj:`int`, optional): index to center the neighbor search at

        Returns:
            list: of :obj:`tuple` of form::

                (neighbor ID, index)

            of type (:obj:`int`, :obj:`int`)
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        coord = self.getCoordinate(id_num, idx)
        neighbors, indices = self.queryBasePoint(radius, *coord)
        non_id_num_idxs, _ = np.where(neighbors != id_num)
        return list(zip(np.take(neighbors, non_id_num_idxs),
                        np.take(indices, non_id_num_idxs)    ))
    # end def

    def getVirtualHelixOriginNeighbors(self, id_num, radius):
        """ might use radius = 2.1*RADIUS
        for now return a set of neighbor id_nums

        Args:
            id_num (int): virtual helix ID number
            radius (float): radial distance within which a neighbors origin exists

        Returns:
            set: set of neighbor candidate ID numbers
        """
        origin = self.origin_pts[id_num]
        neighbors = self.queryVirtualHelixOrigin(radius, tuple(origin))
        neighbor_candidates = set(neighbors)
        neighbor_candidates.discard(id_num)
        return neighbor_candidates
    # end def

    def addCoordinates(self, id_num, points, is_right):
        """Points will only be added on the ends of a virtual helix
        not internally.  NO GAPS!
        handles reindex the points in self.indices

        Args:
            id_num (int): virtual helix ID number
            points (ndarray): n x 3 shaped numpy ndarray of floats or
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
        num_points = len(new_axis_pts) # number of points being added

        self.resetPointCache()

        # 1. existing id_num
        offset, size = offset_and_size_tuple
        lo_idx_limit, hi_idx_limit = offset, offset + size
        if is_right:
            insert_idx = hi_idx_limit
        else: # prepend
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
            number_of_new_elements = math.ceil(diff / DEFAULT_FULL_SIZE)*DEFAULT_FULL_SIZE
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
        """ Get directions for a sequence of ID numbers

        Args:
            id_nums (:obj:`sequence` of :obj:`int`): array_like list of indices
            or scalar index

        Returns:
            ndarray: shape (x, 3) array
        """
        return np.take(self.directions, id_nums, axis=0)
    # end def

    def normalize(self, v):
        """Normlize a vector

        Args:
            v (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence

        Returns:
            ndarray: of :obj:`float`, norm of `v`
        """
        norm = np.linalg.norm(v)
        if norm == 0:
           return v
        return v / norm
    # end def

    def lengthSq(self, v):
        """Compute the length of a sequence

        Args:
            v (:obj:`sequence` of :obj:`float`): shape (1,3) ndarray or length 3 sequence

        Returns:
            float
        """
        return inner1d(v, v)

    def cross(self, a, b):
        """Compute the cross product of two vectors of length 3

        Args:
            a (:obj:`sequence` of :obj:`float`): shape (1, 3) :obj:`ndarray` or length 3 :obj:`sequence`
            b (:obj:`sequence` of :obj:`float`): shape (1, 3) :obj:`ndarray` or length 3 :obj:`sequence`

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

        see: http://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d/180436#180436

        Args:
            v1 (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence
            v2 (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence

        Returns:
            ndarray: shape (3, 3) m0
        """
        if np.all(v1 == v2):
            return self.eye3_scratch.copy()

        v1 = self.normalize(v1)
        v2 = self.normalize(v2)

        v = np.cross(v1, v2)
        sin_squared = inner1d(v, v)
        cos_ = inner1d(v1, v2) # fast dot product

        m1 = self.m3_scratch1
        m2 = self.m3_scratch2
        m0 = self.m3_scratch0
        m0[:] = 0.

        m0[1, 0] =  v[2]
        m0[0, 1] =  -v[2]
        m0[2, 0] =  -v[1]
        m0[0, 2] =  v[1]
        m0[2, 1] =  v[0]
        m0[1, 2] =  -v[0]

        # do the following efficiently
        # self.eye3_scratch + m0 + np.dot(m0, m0)*((1 - cos_)/sin_squared)
        np.dot(m0, m0, out=m1)
        np.add(self.eye3_scratch, m0, out=m2)
        np.add(m2, m1*((1 - cos_)/sin_squared), out=m0)
        return m0
    # end def

    def createHelix(self, id_num, origin, direction, num_points, color):
        """Create a virtual helix in the group that has a Z_ONLY direction

        Args:
            id_num (int): virtual helix ID number
            origin (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence.
                The origin should be referenced from an index of 0.
            direction (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence
            num_points (int): number of bases in Virtual Helix
            color (str):
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is not None:
            raise IndexError("id_num {} already exists".format(id_num))

        self.reserveIdNum(id_num)

        offset_and_size = self._offset_and_size

        # 1. New id_num / virtual helix insert after all other points
        # expand offset and size as required
        self._resetOriginCache()

        number_of_new_elements = id_num - len(offset_and_size) + 1
        offset_and_size += [None]*number_of_new_elements
        self.fwd_strandsets += [None]*number_of_new_elements
        self.rev_strandsets += [None]*number_of_new_elements

        total_points = self.total_points
        lo_idx_limit = total_points
        # new_lims = (total_points, total_points + num_points)
        offset_and_size[id_num] = (total_points, 0) # initialize with size 0

        # 2. Assign origin on creation, resizing as needed
        len_origin_pts = len(self.origin_pts)
        if id_num >= len_origin_pts:
            diff = id_num - len_origin_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_SIZE)*DEFAULT_SIZE
            total_rows = len_origin_pts + number_of_new_elements
            # resize adding zeros
            self.origin_pts.resize((total_rows, 2))
            self.origin_pts[len_origin_pts:] = np.inf

            self.directions.resize((total_rows, 3))
            self.directions[len_origin_pts:] = 0 # unnecessary as resize fills with zeros

            self.vh_properties = self.vh_properties.append(
                                        _defaultDataFrame(number_of_new_elements),
                                        ignore_index=True)

        self.origin_pts[id_num] = origin[:2]
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
            self.fwd_strandsets[id_num].reset(num_points)
            self.rev_strandsets[id_num].reset(num_points)

        self.total_id_nums += 1

        # 3. Create points
        points = self.pointsFromDirection(id_num, origin, direction, num_points, 0)
        self.addCoordinates(id_num, points, is_right=False)
        self._group_properties['virtual_helix_order'].append(id_num)
    # end def

    def pointsFromDirection(self, id_num, origin, direction, num_points, index):
        """Assumes always prepending or appending points.  no insertions.
        changes eulerZ of the id_num vh_properties as required for prepending
        points

        Args:
            id_num (int): virtual helix ID number
            origin (:obj:`sequence` of :obj:`float`): (1, 3) ndarray or length 3 sequence.  The origin should be
                        referenced from an index of 0.
            direction (:obj:`sequence` of :obj:`float`): (1,3) ndarray or length 3 sequence
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

        fwd_angles = [i*twist_per_base + eulerZ_new for i in range(num_points)]
        rev_angles = [a + mgroove for a in fwd_angles]
        z_pts = BW*np.arange(index, num_points + index)

        # invert the X coordinate for Right handed DNA
        fwd_pts = rad*np.column_stack(( np.cos(fwd_angles),
                                        np.sin(fwd_angles),
                                        np.zeros(num_points)))
        fwd_pts[:,2] = z_pts

        # invert the X coordinate for Right handed DNA
        rev_pts = rad*np.column_stack(( np.cos(rev_angles),
                                        np.sin(rev_angles),
                                        np.zeros(num_points)))
        rev_pts[:,2] = z_pts

        coord_pts = np.zeros((num_points, 3))
        coord_pts[:, 2] = z_pts

        # create scratch array for stashing intermediate results
        scratch = np.zeros((3, num_points), dtype=float)

        # rotate about 0 index and then translate
        m = self.makeRotation( (0, 0, 1), direction)
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
            keys (:obj:`str` or :obj:`list`/:obj:`tuple`):
            safe (:obj:`bool`, optional):

        Returns:
            object or list: depending on type of arg `keys`
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
            id_num_list (:obj:`list` of :obj:`int`, optional): list of virtual
                helix id numbers to get the origins and properties of

        Returns:
            tuple: of (:obj:`dict`, :obj:`ndarray`) (properties dictionary
            where each key has a list of values correspoding to the id_number
            and, (n, 2) array of origins

        Raises:
            ValueError
        """
        if id_num_list is None:
            lim = self._highest_id_num_used + 1
            props = self.vh_properties.iloc[:lim]
            props = props.to_dict(orient='list')
            origins = self.origin_pts[:lim]
            return props, origins
        elif isinstance(id_num_list, list):
            # select by list of indices
            props = self.vh_properties.iloc[id_num_list].reset_index(drop=True)
            props = props.to_dict(orient='list')
            origins = self.origin_pts[id_num_list]
            return props, origins
        else:
            raise ValueError("id_num_list bad type: {}".format(type(id_num_list)))
    # end def

    def getAllVirtualHelixProperties(self, id_num, inject_extras=True, safe=True):
        """NOT to be used for a list of Virtual Helix property keys unless
        `inject_extras` is False

        Args:
            id_num (int): virtual helix ID number
            inject_extras (:obj:`bool`, optional): Adds in 'bases_per_turn' and
            'twist_per_base'  Default True
            safe (bool): check if id_num exists. Default True

        Returns:
            dict: properties of a given ids

        Raises:
            IndexError
        """
        if safe:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        series = self.vh_properties.loc[id_num]
        # to_dict doesn't promote to python native types needed by QVariant
        # leaves as numpy integers and floats
        out = dict((k, v.item()) if isinstance(v, (np.float64, np.int64, np.bool_)) else (k, v) for k, v in zip(series.index, series.tolist()))
        if inject_extras:
            bpr = out['bases_per_repeat']
            tpr = out['turns_per_repeat']
            out['bases_per_turn'] = bpr / tpr
            out['twist_per_base'] = tpr*360. / bpr
        return out
    # end

    def setVirtualHelixProperties(self, id_num, keys, values, safe=True):
        """ keys and values can be sequences of equal length or
        singular values

        emits `partVirtualHelixPropertyChangedSignal`

        Args:
            id_num (int): virtual helix ID number
            keys (:obj:`str` or :obj:`list`/:obj:`tuple`):
            value (:obj:`object` or :obj:`list`/:obj:`tuple`)
            safe (:obj:`bool`, optional): optionally echew signalling
        """
        if safe:
            offset_and_size_tuple = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size_tuple is None:
                raise IndexError("id_num {} does not exists".format(id_num))
        self.vh_properties.loc[id_num, keys] = values

        if not isinstance(values, (tuple, list)):
            keys, values = (keys,) , (values,)
        if safe:
            self.partVirtualHelixPropertyChangedSignal.emit(self, id_num, keys, values)
    # end

    def locationQt(self, id_num, scale_factor=1.0):
        """ Y-axis is inverted in Qt +y === DOWN

        Args:
            id_num (int):
            scale_factor (:obj:`float`, optional): default 1.0

        Returns:
            tuple: of :obj:`float`, x, y coordinates
        """
        x, y = self.getVirtualHelixOrigin(id_num)
        return scale_factor*x, -scale_factor*y
    # end def

    def resizeHelix(self, id_num, is_right, delta):
        """Resize vritual helix given by ID number

        Args:
            id_num (int): virtual helix ID number
            is_right (bool): whether this is a left side (False) or
                right side (True) operation
            delta (int): number of virtual base pairs to add to (+) or trim (-)
                from the virtual helix

        Returns:
            int: the ID number of the longest Virtual Helix in the
            VirtualHelixGroup

        Raises:
            IndexError, ValueError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise IndexError("id_num {} does not exist")

        offset, size = offset_and_size_tuple
        len_axis_pts = len(self.axis_pts)
        direction = self.directions[id_num]

        # make origin 3D
        origin = self.origin_pts[id_num]
        origin = (origin[0], origin[1], 0.)

        if delta > 0:   # adding points
            if is_right:
                index = size
            else:
                index = -delta
            # 3. Create points
            points = self.pointsFromDirection(id_num, origin, direction, delta, index)
            self.addCoordinates(id_num, points, is_right=is_right)
            # TODO add checks for resizing strandsets here
            if is_right:
                self.fwd_strandsets[id_num].resize(0, delta)
                self.rev_strandsets[id_num].resize(0, delta)
            else:
                self.fwd_strandsets[id_num].resize(delta, 0)
                self.rev_strandsets[id_num].resize(delta, 0)
        elif delta < 0: # trimming points
            if abs(delta) >= size:
                raise ValueError("can't delete virtual helix this way")
            # TODO add checks for strandsets etc here:

            self.removeCoordinates(id_num, abs(delta), is_right)
            if is_right:
                self.fwd_strandsets[id_num].resize(0, delta)
                self.rev_strandsets[id_num].resize(0, delta)
            else:
                self.fwd_strandsets[id_num].resize(delta, 0)
                self.rev_strandsets[id_num].resize(delta, 0)
        else: # delta == 0
            return
        _, final_size = self.getOffsetAndSize(id_num)
        self.vh_properties.loc[id_num, 'length'] =  final_size
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
        id_z_max = self.id_nums[np.argmax(  np.ma.array(test,
                                                        mask=np.isinf(test)))]
        return id_z_min, id_z_max
    # end def

    def removeHelix(self, id_num):
        """Remove a helix and recycle it's `id_num`

        Args:
            id_num (int): virtual helix ID number

        Raises:
            IndexError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise IndexError("id_num {} does not exist")
        offset, size = offset_and_size_tuple
        # print("the offset and size", offset_and_size_tuple)
        did_remove = self.removeCoordinates(id_num, size, is_right=False)
        self.recycleIdNum(id_num)
        assert did_remove
        self._group_properties['virtual_helix_order'].remove(id_num)
    # end def

    def resetCoordinates(self, id_num):
        """Call this after changing helix vh_properties to update the points
        controlled by the properties

        Args:
            id_num (int): virtual helix ID number

        Raises:
            KeyError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))
        offset, size = offset_and_size_tuple
        origin = self.axis_pts[offset] # zero point of axis
        direction = self.directions[id_num]
        points = self.pointsFromDirection(id_num, origin, direction, size, 0)
        self.setCoordinates(id_num, points)
    # end def

    def setCoordinates(self, id_num, points, idx_start=0):
        """Change the coordinates stored, useful when adjusting
        helix vh_properties

        Args:
            id_num (int): virtual helix ID number
            points (tuple): tuple containing :obj:`sequence`s of axis, and forward
            and reverse phosphates points
            idx_start (:obj:`int`, optional): index offset into the virtual helix to
            assign points to.

        Raises:
            KeyError, IndexError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)
        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

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

    def removeCoordinates(self, id_num, length, is_right):
        """Remove coordinates given a length, reindex as necessary

        Args:
            id_num (int): virtual helix ID number
            length (int):
            is_right (bool): whether the removal occurs at the right or left
            end of a virtual helix since virtual helix arrays are always
            contiguous

        Returns:
            bool: True if id_num is removed, False otherwise

        Raises:
            KeyError, IndexError
        """
        offset_and_size_tuple = self.getOffsetAndSize(id_num)

        if offset_and_size_tuple is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size_tuple
        if length > size:
            raise IndexError("length longer {} than indices existing".format(length))
        lo, hi = offset, offset + size
        if is_right:
            idx_start, idx_stop = hi - length, hi
        else:
            idx_start, idx_stop = lo, lo + length

        self.resetPointCache()
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
        for i, item in enumerate(offset_and_size[id_num:]):
            if item is not None:
                offset_other, size_other = item
                offset_and_size[i + id_num] = (offset_other - length, size_other)

        # 3. Check if we need to remove Virtual Helix
        if size == length:
            self.total_id_nums -= 1
            self._resetOriginCache()
            offset_and_size[id_num] = None
            self.origin_pts[id_num, :] = (np.inf, np.inf)  # set off to infinity
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
            did_remove = False
        self.total_points -= length
        return did_remove
    # end def

    def queryBasePoint(self, radius, point):
        """Cached query

        Args:
            radius (float): distance to consider
            point (:obj:`sequence` of :obj:`float`): is an array_like of length 3

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
            qc[query] =  res
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
            point (:obj:`sequence` of :obj:`float`): is an array_like of length 3

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
                            np.take(self.indices, close_points) )
    # end def

    def queryVirtualHelixOrigin(self, radius, point):
        """ Hack for now to get 2D behavior
        point is an array_like of length 2

        Args:
            radius (float): distance to consider
            point (:obj:`sequence` of :obj:`float`): is an array_like of length 3

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
            qc[query] =  res
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
            point (:obj:`sequence` of :obj:`float`): is an array_like of length 3

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

    def queryVirtualHelixOriginRect(self, rect):
        """Query based on a Rectangle

        Args:
            rect (:obj:`sequence` of :obj:`float`): rectangle defined by x1, y1, x2, y2
                definining the lower left and upper right corner of the
                rectangle respetively

        Returns:
            ndarray: list of ID numbers satisfying the query
        """
        # search children
        x1, y1, x2, y2 = rect
        origin_pts = self.origin_pts
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

    def queryIdNumRange(self, id_num, radius, index_slice=None):
        """Return the indices of all virtual helices phosphates closer
        than `radius` to `id_num`'s helical axis

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
            close_points, = np.where(   (close_points < offset) |
                                        (close_points > (offset + size)))
            if len(close_points) > 0:
                fwd_hits = (np.take(self.id_nums, close_points).tolist(),
                                    np.take(self.indices, close_points).tolist() )
                fwd_hit_list.append((start + i, fwd_hits))

            difference = rev_pts - point
            delta = inner1d(difference, difference, out=delta)
            close_points, = np.where(delta < rsquared)
            close_points, = np.where(   (close_points < offset) |
                                        (close_points > (offset + size)))
            if len(close_points) > 0:
                rev_hits = (np.take(self.id_nums, close_points).tolist(),
                                    np.take(self.indices, close_points).tolist() )
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

    def queryIdNumRangeNeighbor(self, id_num, neighbors, alpha, index=None):
        """Get indices of all virtual helices phosphates closer within an
        `alpha` angle's radius to `id_num`'s helical axis

        Args:
            id_num (int): virtual helix ID number
            neighbors (sequence): neighbors of id_num
            alpha (float): angle (degrees) commensurate with radius
            index (:obj:`tuple` of :obj:`int`, optional): (start_index, length)
            into a virtual helix

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
        norm = np.linalg.norm
        cross = np.cross
        dot = np.dot
        normalize = self.normalize
        PI = math.pi
        TWOPI = 2*PI
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
        key_prop_list = [   'eulerZ', 'bases_per_repeat',
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

                    all_fwd_angles = [(j, angleNormalize(eulerZ + tpb*j)) for j in range( max(neighbor_min_delta_idx - half_period, 0),
                                                                                    min(neighbor_min_delta_idx + half_period, size)) ]
                    passing_fwd_angles_idxs = [j for j, x in all_fwd_angles if angleRangeCheck(x, native_angle, theta)]
                    all_rev_angles = [(j, angleNormalize(x + mgroove)) for j, x in all_fwd_angles]
                    passing_rev_angles_idxs = [j for j, x in all_rev_angles if angleRangeCheck(x, native_angle, theta) ]
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

                    all_fwd_angles = [(j, angleNormalize(eulerZ + tpb*j)) for j in range( max(neighbor_min_delta_idx - half_period, 0),
                                                                                    min(neighbor_min_delta_idx + half_period, size)) ]
                    passing_fwd_angles_idxs = [j for j, x in all_fwd_angles if angleRangeCheck(x, native_angle, theta)]
                    all_rev_angles = [(j, angleNormalize(x + mgroove)) for j, x in all_fwd_angles]
                    passing_rev_angles_idxs = [j for j, x in all_rev_angles if angleRangeCheck(x, native_angle, theta) ]
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
            neighbors (sequence): neighbors of id_num
            index_slice (:obj:`tuple` of :obj:`int`, optional): (start_index, length) into a virtual
                helix

        Returns:
            dict: of :obj:`tuple` of form::

                neighbor_id_num: (fwd_hit_list, rev_hit_list)

            where each list has the form:

                [(id_num_index, forward_neighbor_idxs, reverse_neighbor_idxs), ...]]

        Raises:
            ValueError
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
        norm = np.linalg.norm
        cross = np.cross
        dot = np.dot
        normalize = self.normalize
        PI = math.pi
        TWOPI = 2*PI
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
        r2_radial = (RADIUS*((1. - math.cos(half_twist_per_base) ) +
                            (1. - math.cos(1.55*half_twist_per_base) ) ) )**2
        r2_tangent = (RADIUS*(  math.sin(half_twist_per_base) +
                                math.sin(1.55*half_twist_per_base) ) )**2
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
            nmin_idx = 999999
            nmax_idx = -1
            offset, size = self.getOffsetAndSize(neighbor_id)

            # 1. Finds points that point at neighbors axis point
            nfwd_pts = fwd_pts[offset:offset + size]
            nrev_pts = rev_pts[offset:offset + size]

            direction = self.directions[neighbor_id]
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
                f_idxs = np.where(  (delta > rsquared_p_min) &
                                    (delta < rsquared_p_max) &
                                    (zdelta > 0.3*r2_axial) &
                                    (zdelta < 1.1*r2_axial)
                                    )[0].tolist()
                difference = nrev_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                r_idxs = np.where(  (delta > rsquared_ap_min) &
                                    (delta < rsquared_ap_max) &
                                    (zdelta < 0.3*r2_axial))[0].tolist()
                if f_idxs or r_idxs:
                    # nmin_idx = min(nmin_idx, *f_idxs, *r_idxs)
                    # nmax_idx = max(nmax_idx, *f_idxs, *r_idxs)
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
                        fwd_axis_pairs[idx_last] = (True, neighbor_id) # 5 prime  most strand
                        fwd_axis_pairs[i] = (False, neighbor_id)       # 3 prime most strand
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
                f_idxs = np.where(  (delta > rsquared_ap_min) &
                                    (delta < rsquared_ap_max) &
                                    (zdelta < 0.3*r2_axial))[0].tolist()

                difference = nrev_pts - point
                inner1d(difference, difference, out=delta)
                zdelta = np.square(difference[:, 2])
                # assume there is only one possible index of intersection with the neighbor
                r_idxs = np.where(  (delta > rsquared_p_min) &
                                    (delta < rsquared_p_max) &
                                    (zdelta > 0.3*r2_axial) &
                                    (zdelta < 1.1*r2_axial)
                                    )[0].tolist()
                if f_idxs or r_idxs:
                    # nmin_idx = min(nmin_idx, *f_idxs, *r_idxs)
                    # nmax_idx = max(nmax_idx, *f_idxs, *r_idxs)
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

            per_neighbor_hits[neighbor_id] = ( fwd_axis_hits, rev_axis_hits)
        # end for
        return per_neighbor_hits, (fwd_axis_pairs, rev_axis_pairs)
    # end def

    def getAngleAtIdx(self, id_num, idx):
        """Account for Z translation ??????????

        Args:
            id_num (int): ID number of virtual helix
            idx (int): index of interest

        Returns:
            float: angle at the index
        """
        bpr, tpr, eulerZ = self.getVirtualHelixProperties(id_num,
                        ['bases_per_repeat', 'turns_per_repeat', 'eulerZ'])
        return eulerZ + idx*tpr*360./bpr
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

    def projectionPointOnPlane(self, id_num, point):
        """VirtualHelices are straight for now so only one direction for the axis
        assume directions are alway normalized, so no need to divide by the
        magnitude of the direction vector squared

        Args:
            id_num (int): virtual helix ID number
            point (sequence): length 3

        Returns:
            sequence: length 3
        """
        direction = self.directions[id_num]
        return point - np.dot(point, direction)*direction
    # end
# end class

def distanceToPoint(origin, direction, point):
    """ See:
    http://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html

    Args:
        direction (sequence):
        point (sequence):

    Returns:
        float: R squared distance
    """
    direction_distance = np.dot(point - origin,  direction)
    # point behind the ray
    if direction_distance < 0:
        diff = origin - point
        return diff*diff

    v = (direction * direction_distance ) + origin
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
        IndexError
    """
    new_start = length - start if start < 0 else start
    new_stop = length - stop if stop < 0 else stop

    if new_stop < new_start:
        raise IndexError("Stop {} must be greater than or equal to start {}".format(stop, start))
    return start, stop
# end def