import math
from heapq import heapify, heappush, nsmallest

import numpy as np
import pandas as pd
from collections import deque
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

def defaultProperties(id_num):
    props = [
    ('name', "vh%d" % (id_num)),
    ('color', '#ffffffff'),
    ('active_phos', None),
    ('eulerZ', 10.),
    ('scamZ', 10.),
    ('neighbor_active_angle', 0.0),
    ('neighbors', [])
    ('bases_per_repeat', 21)
    ('turns_per_repeat', 2)
    ('repeats', 2)
    ('helical_pitch', 1.)
    ('bases_per_turn', 10.5), # bases_per_repeat/turns_per_repeat
    ('twist_per_base', 360 / 10.5) # 360/_bases_per_turn
    ]
    return tuple(zip(*props))
# end def

def defaultDataFrame(size):
    dummy_id_num = 999
    columns, row = defaultProperties(dummy_id_num)
    df = pd.DataFrame([row for i in range(size)], columns=columns)
    return df
# end def
DEFAULT_SIZE = 256
DEFAULT_FULL_SIZE = DEFAULT_SIZE*48

class VirtualHelixGroup(CNObject):
    def __init__(self, part):
        """ this is composed of a group of arrays
        that
        1. contain the coordinates of every virtual base stored
            in their index order per id_num
        2. contains the id_num per coordinate
        """
        super(VirtualHelixGroup, self).__init__(part)

        self.radius = 2     # probably a property???

        # 1. per virtual base pair allocations
        self.total_points = 0
        self.axis_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.fwd_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.rev_pts = np.full((DEFAULT_FULL_SIZE, 3), np.inf, dtype=float))
        self.id_nums = np.full((DEFAULT_FULL_SIZE, 1), -1, dtype=int)
        self.indices = np.zeros((DEFAULT_FULL_SIZE, 1), dtype=int)

        # 2. per virtual helix allocations
        self.total_id_nums = 0
        """
        for doing 2D X,Y manipulation for now.  keep track of
        XY position of virtual helices
        """
        self.origin_pts = np.full((DEFAULT_SIZE, 2), np.inf, dtype=float)
        self.directions = np.zeros((DEFAULT_SIZE, 3), dtype=float))
        """
        book keeping for fast lookup of indices for insertions and deletions
        and coordinate points
        the length of this is the max id_num used
        """
        self.offset_and_size = []

        self.properties = defaultDataFrame(DEFAULT_SIZE)

        self.fwd_strandsets = []
        self.rev_strandsets = []

        # Cache Stuff
        self._point_cache = {}
        self._point_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)
        self._origin_cache = {}
        self._origin_cache_keys = deque([None]*DEFAULT_CACHE_SIZE)

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

    def getOffsetAndSize(self, id_num):
        offset_and_size = self.offset_and_size
        offset_and_size[id_num] if id_num < len(offset_and_size) else return None
    # end def

    def getNewIdNum(self):
        """  Query the lowest available id_num
        """
        if len(self.recycle_bin):
            return nsmallest(1, self.recycle_bin)[0]
        else:
            # use self._highest_id_num_used if the recycle bin is empty
            # and _highest_id_num_used + 1 is not in the reserve bin
            return self._highest_id_num_used + 1
    # end def

    def reserveIdNum(self, requested_id_num):
        """
        Reserves and returns a unique numerical id_num appropriate for a
        virtualhelix of a given parity. If a specific index is preferable
        (say, for undo/redo) it can be requested in num.
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
    # end def

    def recycleIdNum(self, id_num):
        """
        The caller's contract is to ensure that id_num is not used in *any* helix
        at the time of the calling of this function (or afterwards, unless
        reserveIdNumForHelix returns the id_num again).
        """
        heappush(self.recycle_bin, id_num)
    # end def

    def isIdNumUsed(self, id_num):
        return True if self.getOffsetAndSize(id_num) is not None else False
    # end def

    def getCoordinates(self, id_num):
        """ return a view onto the numpy array for a
        given id_num
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size
        lo, hi = offset, offset + size
        return (self.axis_pts[lo:hi],
                self.fwd_pts[lo:hi],
                self.rev_pts[lo:hi] )
    # end def

    def part(self):
        return self.parent()
    # end def

    def getCoordinate(self, id_num, idx):
        """
        given a id_num get the coordinate at a given index
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size
        if idx < size:
            return self.axis_pts[offset + idx]
        else:
            raise IndexError("idx {} greater than size {}".format(idx, size))
    # end def

    def getOrigin(self, id_num):
        """
        given a id_num get the coordinate at a given index
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        return self.origin_pts[id_num]
    # end def

    def getStrandSets(self, id_num):
        """
        given a id_num get the coordinate at a given index
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        return (self.fwd_strandsets[id_num], self.rev_strandsets[id_num])
    # end def

    def hasStrandAtIdx(self, id_num, idx):
        """Return a tuple for (Scaffold, Staple). True if
           a strand is present at idx, False otherwise."""
        return (self.fwd_strandsets[id_num].hasStrandAt(idx, idx),\
                self.rev_strandsets[id_num].hasStrandAt(idx, idx))
    # end def

    def getStrand(self, strand_type, id_num, idx):
        if strand_type == StrandType.FWD:
            return self.fwd_strandsets[self._id_num].getStrand(idx)
        else:
            return self.rev_strandsets[self._id_num].getStrand(idx)

    def translateCoordinates(self, id_nums, delta):
        """ delta is a sequence of floats of length 3
        for now support XY translation
        """
        self._origin_cache = {} # clear cache
        self._point_cache = {}
        origin_pts = self.origin_pts
        delta_origin = delta[:2] # x, y only
        for id_num in id_nums:
            coord_pts, fwd_pts, rev_pts = self.getCoordinates(id_num)
            coord_pts += delta # use += to modify the view
            fwd_pts += delta # use += to modify the view
            rev_pts += delta # use += to modify the view
            origin_pts[id_num] += delta_origin
    # end def

    def getIndices(self, id_num):
        """ return a view onto the numpy array for a
        given id_num
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size
        lo, hi = offset, offset + size
        return self.indices[lo:hi]
    # end def

    def getNeighbors(self, id_num, radius, idx=0):
        """ might use radius = 2.1*RADIUS
        return list of neighbor id_nums and the indices nearby
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        coord = self.getCoordinate(id_num, idx)
        neighbors, indices = self.queryPoint(radius, *coord)
        non_id_num_idxs, _ = np.where(neighbors != id_num)
        return list(zip(np.take(neighbors, non_id_num_idxs),
                        np.take(indices, non_id_num_idxs)    ))
    # end def

    def getOriginNeighbors(self, id_num, radius):
        """ might use radius = 2.1*RADIUS
        for now return a set of neighbor id_nums
        """
        origin = self.origin_pts[id_num]
        neighbors = self.queryOrigin(radius, *origin)
        neighbor_candidates = set(neighbors)
        neighbor_candidates.discard(id_num)
        return neighbor_candidates
    # end def

    def addCoordinates(self, id_num, points, is_right):
        """ Points will only be added on the ends of a virtual helix
        not internally.  NO GAPS!
        handles reindex the points in self.indices

        id_num (int): integer index id_num of the virtual helix
        points (ndarray): n x 3 shaped numpy ndarray of floats or
                        2D Python list

                        points are stored in order and by index
        is_right (bool): whether we are extending in the positive index direction
                        or prepending
        """
        offset_and_size = self.getOffsetAndSize(id_num)

        # 1. Find insert indices
        if offset_and_size is None:
            raise IndexError("IdNum {} does not exists".format(id_num))

        offset_and_size = self.offset_and_size
        len_axis_pts = len(self.axis_pts)

        coord_pts, fwd_pts, rev_pts = points
        num_points = len(coord_pts) # number of points being added

        self._point_cache = {} # clear cache

        # 1. existing id_num
        offset, size = offset_and_size
        lo_idx_limit, hi_idx_limit = offset, offset + size
        if is_right:
            insert_idx = hi_idx_limit
        else: # prepend
            insert_idx = offset

        new_lims = (hi_idx_limit, hi_idx_limit + num_points)
        old_offset, old_size = offset_and_size[id_num]
        offset_and_size[id_num] = (old_offset, old_size + num_points)

        # 2. Did exceed allocation???
        if self.total_points + num_points > len_axis_pts:
            diff = self.total_points + num_points - len_axis_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_FULL_SIZE)*DEFAULT_FULL_SIZE
            total_rows = len_axis_pts + number_of_new_elements
            # resize per virtual base allocations
            self.axis_pts.resize((total_rows, 3))
            self.axis_pts[len_axis_pts:, :] = np.inf

            self.fwd_pts.resize((total_rows, 3))
            self.fwd_pts[len_axis_pts:, :] = np.inf

            self.rev_pts.resize((total_rows, 3))
            self.rev_pts[len_axis_pts:, :] = np.inf

            self.id_nums.resize((total_rows, 3))
            self.id_nums[len_axis_pts:, :] = -1

            self.indices.resize((total_rows, 3))
            self.indices[len_axis_pts:, :] = 0
        # end if exceeded allocation
        axis_pts = self.axis_pts
        fwd_pts = self.fwd_pts
        rev_pts = self.rev_pts
        id_nums = self.id_nums
        indices = self.indices

        # 3. Move Existing data
        move_idx_start = insert_idx + num_points
        move_idx_end = move_idx_start + total_points - insert_idx

        axis_pts[move_idx_start:move_idx_end] = axis_pts[insert_idx:total_points]
        axis_pts[insert_idx:move_idx_start] = coord_pts

        fwd_pts[move_idx_start:move_idx_end] = fwd_pts[insert_idx:total_points]
        fwd_pts[insert_idx:move_idx_start] = fwd_pts
        rev_pts[move_idx_start:move_idx_end] = rev_pts[insert_idx:total_points]
        rev_pts[insert_idx:move_idx_start] = rev_pts

        # just overwrite everything for indices and id_nums no need to move
        id_nums[insert_idx:move_idx_start] = id_num
        indices[lo_idx_limit:move_idx_start] = list(range(num_points + size))

        self.total_points += num_points
    # end def

    def getDirections(self, id_nums):
        """
        id_nums: array_like list of indices or scalar index
        """
        return np.take(self.directions, id_nums, axis=0)
    # end def

    def normalize(self, v):
        norm = np.linalg.norm(v)
        if norm == 0:
           return v
        return v / norm
    # end def

    def lengthSq(self, v):
        return inner1d(v, v)

    def cross(self, a, b):
        ax, ay, az = a
        bx, by, bz = b
        c = [ay*bz - az*by,
             az*bx - ax*bz,
             ax*by - ay*bx]
        return c
    # end def

    def makeRotation(self, v1, v2):
        """ create a rotation matrix for an object pointing
        in the v1 direction to the v2 direction

        see http://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d/180436#180436
        """
        if v1 == v2:
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

    def createHelix(self, id_num, origin, direction, num_points):
        offset_and_size = self.getOffsetAndSize(id_num)

        if offset_and_size is not None:
            raise IndexError("IdNum {} already exists")

        self.reserveIdNum(id_num)

        offset_and_size = self.offset_and_size
        len_axis_pts = len(self.axis_pts)
        num_points = len(points)

        # 1. New id_num / virtual helix insert after all other points
        # expand offset and size as required
        self._origin_cache = {} # clear cache

        number_of_new_elements = id_num - len(offset_and_size) + 1
        offset_and_size += [None]*number_of_new_elements
        self.fwd_strandsets += [None]*number_of_new_elements
        self.rev_strandsets += [None]*number_of_new_elements

        lo_idx_limit = len_axis_pts
        new_lims = (len_axis_pts, len_axis_pts + num_points)
        offset_and_size[id_num] = (len_axis_pts, num_points)

        # 2. Assign origin on creation, resizing as needed
        len_origin_pts = len(self.origin_pts)
        if id_num >= len_origin_pts:
            diff = id_num - len_origin_pts
            number_of_new_elements = math.ceil(diff / DEFAULT_SIZE)*DEFAULT_SIZE
            total_rows = len_origin_pts + number_of_new_elements
            # resize adding zeros
            self.origin_pts.resize((total_rows, 2))
            self.origin_pts[len_origin_pts:, :] = np.inf

            self.directions.resize((total_rows, 3))
            self.directions[len_origin_pts:, :] = 0 # unnecessary as resize fills with zeros

            self.properties = self.properties.append(
                                        defaultDataFrame(number_of_new_elements),
                                        ignore_index=True)

        self.origin_pts[id_num] = origin[:2]
        self.directions[id_num] = direction
        self.properties.loc[id_num, 'name'] = "vh%d" % (id_num)
        self.fwd_strandsets[id_num] = StrandSet(StrandType.FWD, id_num, self, num_points)
        self.rev_strandsets[id_num] = StrandSet(StrandType.REV, id_num, self, num_points)

        self.total_id_nums += 1

        # 3. Create points
        points = self.pointsFromDirection(id_num, origin, direction, num_points, 0)
        self.addCoordinates(id_num, points, is_right=False)
    # end def

    def pointsFromDirection(self, id_num, origin, direction, num_points, index):
        """ Assumes always prepending or appending points.  no insertions.
        changes eulerZ of the id_num properties as required for prepending points

        origin: (1,3) ndarray or length 3 sequence.  The origin should be
                    referenced from an index of 0.
        direction: (1,3) ndarray or length 3 sequence

        index: the offset index into a helix to start the helix at.  Useful for
            appending points. if index less than zero

        returns:
            None
        """
        rad = self.radius
        hp, twist_per_base, eulerZ = self.properties.loc[id_num,
                                                            ['helical_pitch',
                                                            'twist_per_base',
                                                            'eulerZ']]
        twist_per_base *= math.pi/180.
        eulerZ_new = eulerZ + twist_per_base*index

        fwd_angles = [i*twist_per_base + eulerZ_new for i in range(num_points)]
        rev_angles = [a + math.pi for a in fwd_angles]
        z_pts = np.arange(index, num_points + index)

        fwd_pts = rad*np.column_stack(( np.cos(fwd_angles),
                                        np.sin(fwd_angles),
                                        np.zeros(num_points)))
        fwd_pts[:,2] = z_pts
        rev_pts = rad*np.column_stack(( np.cos(rev_angles),
                                        np.sin(rev_angles),
                                        np.zeros(num_points)))
        rev_pts[:,2] = z_pts

        coord_pts = np.zeros((num_points,3))
        coord_pts[:,2] = z_pts

        # create scratch array for stashing intermediate results
        scratch = np.zeros((3, num_points), dtype=float)
        # rotate about 0 index and then translate
        m = self.makeRotation((1, 0, 0), direction)

        np.add(np.dot(m, fwd_pts.T, out=scratch).T, origin, out=fwd_pts)
        np.add(np.dot(m, rev_pts.T, out=scratch).T, origin, out=rev_pts)
        np.add(np.dot(m, coord_pts.T, out=scratch).T, origin, out=coord_pts)

        if index < 0:
            self.properties.loc[id_num, 'eulerZ'] = eulerZ_new

        return (coord_pts, fwd_pts, rev_pts)
    # end def

    def getProperties(self, id_num, keys, safe=True):
        if safe:
            offset_and_size = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size is None:
                raise IndexError("IdNum {} does not exists".format(id_num))
        return self.properties.loc[id_num, keys]
    # end

    def setProperties(self, id_num, keys, values, safe=True):
        """ keys and values can be sequences of equal length or
        singular values
        """
        if safe:
            offset_and_size = self.getOffsetAndSize(id_num)
            # 1. Find insert indices
            if offset_and_size is None:
                raise IndexError("IdNum {} does not exists".format(id_num))
        self.properties.loc[id_num, keys] = values
    # end

    def locationQt(self, id_num, scale_factor=1.0):
        """ Y-axis is inverted in Qt +y === DOWN
        """
        x, y = self.getOrigin(id_num)
        return scale_factor*x, -scale_factor*y
    # end def

    def resizeHelix(self, id_num, is_right, delta):
        """ id_num (int): the id_num of the virtual helix
            is_right (bool): whether this is a left side (False) or
                    right side (True) operation
            delta (int): number of virtual base pairs to add to (+) or trim (-)
            from the virtual helix
            returns: None
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise IndexError("IdNum {} does not exist")

        offset, size = offset_and_size
        len_axis_pts = len(self.axis_pts)
        direction = self.directions[id_num]
        origin = self.origin_pts[id_num]
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
    # end def

    def removeHelix(self, id_num):
        """
        id_num (int):
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise IndexError("IdNum {} does not exist")
        offset, size = offset_and_size
        did_remove = self.removeCoordinates(id_num, size, is_right=False)
        self.recycleIdNum(id_num)
        assert did_remove
    # end def

    def resetCoordinates(self, id_num):
        """ call this after changing helix properties
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))
        offset, size = offset_and_size
        origin = self.origin_pts[id_num]
        direction = self.origin_pts[direction]
        points = self.pointsFromDirection(id_num, origin, direction, size)
        self.setCoordinates(id_num, points)
    # end def

    def setCoordinates(self, id_num, points, idx_start=0):
        """ change the coordinates stored, useful when adjusting
        helix properties

        id_num: the id_num to apply this to

        points: tuple containing axis, and forward and reverse phosphates
        points

        idx_start: index offset into the virtual helix to assign points to.
        """
        offset_and_size = self.getOffsetAndSize(id_num)
        if offset_and_size is None:
            raise KeyError("id_num {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size
        if idx_start + len(points) > size:
            err = ("Number of Points {} out of range for"
                    "start index {} given existing size {}")
            raise IndexError(err.format(len(points), idx_start, size))

        coord_pts, fwd_pts, rev_pts = points
        lo = offset + idx_start
        hi = lo + len(coord_pts)
        self.axis_pts[lo:hi] = coord_pts
        self.fwd_pts[lo:hi] = fwd_pts
        self.rev_pts[lo:hi] = rev_pts
    # end def

    def removeCoordinates(self, id_num, length, is_right):
        """ remove coordinates given a length, reindex as necessary
        id_num (int):
        length (int):
        is_right (bool): whether the removal occurs at the right or left
        end of a virtual helix since virtual helix arrays are always
        contiguous

        returns (bool): True if id_num is removed, False otherwise
        """

        offset_and_size = self.getOffsetAndSize(id_num)

        if offset_and_size is None:
            raise KeyError("IdNum {} not in VirtualHelixGroup".format(id_num))

        offset, size = offset_and_size

        if length > size:
            raise IndexError("length longer {} than indices existing".format(length))
        lo, hi = offset, offset + size
        if is_right:
            idx_start, idx_stop = hi - length, hi
        else:
            idx_start, idx_stop = lo, lo + length

        self._point_cache = {} # clear cache
        offset_and_size = self.offset_and_size[id_num]
        current_offset_and_size_length = len(offset_and_size)

        # 1. Move the good data

        relocate_idx_end = idx_start + total_points - length
        total_points = self.total_points

        axis_pts = self.axis_pts
        axis_pts[idx_start:relocate_idx_end] = axis_pts[idx_stop:total_points]
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
                offset, size = item
                offset_and_size[i + id_num] = (offset - length, size)

        # 3. Check if we need to remove Virtual Helix
        if offset_and_size[id_num][1] == length:
            self.total_id_nums -= 1
            self._origin_cache = {} # clear cache
            offset_and_size[id_num] = None
            self.origin_pts[id_num] = (np.inf, np.inf)  # set off to infinity
            # trim the unused id_nums at the end
            remove_count = 0
            for i in range(current_offset_and_size_length - 1, id_num - 1, -1):
                if offset_and_size[i] is None:
                    remove_count += 1
                else:
                    break
            self.offset_and_size = offset_and_size[:old_length - remove_count]
            did_remove = True
        else:
            did_remove = False
        self.total_points -= length
        return did_remove
    # end def

    def queryPoint(self, radius, x, y, z):
        """
        cached query
        """
        qc = self._point_cache
        query = (radius, x, y, z)
        if query in self._point_cache:
            return qc.get(query)
        else:
            res = self._queryPoint(radius, x, y, z)
            self._point_cache_keys.append(query)
            qc[query] =  res
            # limit the size of the cache
            old_key = self._point_cache_keys.popleft()
            del qc[old_key]
            return res
    # end def

    def _queryPoint(self, radius, x, y, z):
        """ return the indices of all virtual helices closer
        than radius
        """
        difference = self.axis_pts - (x, y, z)
        ldiff = len(difference)
        delta = self.delta3D_scratch
        if ldiff != len(delta):
            self.delta3D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        delta = inner1d(difference, difference, out=delta)
        close_points, _ = np.where(delta < radius*radius)
        # return list(zip(    np.take(self.id_nums, close_points),
        #                     np.take(self.indices, close_points) ))
        return (np.take(self.id_nums, close_points),
                            np.take(self.indices, close_points) )
    # end def

    def queryOrigin(self, radius, x, y):
        """ Hack for now to get 2D behavior
        """
        qc = self._origin_cache
        query = (radius, x, y)
        if query in self._origin_cache:
            return qc.get(query)
        else:
            res = self._queryOrigin(radius, x, y)
            self._origin_cache_keys.append(query)
            qc[query] =  res
            # limit the size of the cache
            old_key = self._origin_cache_keys.popleft()
            del qc[old_key]
            return res
    # end def

    def _queryOrigin(self, radius, x, y):
        """ return the indices of all id_nums closer
        than radius
        """
        difference = self.origin_pts - (x, y)
        ldiff = len(difference)
        delta = self.delta2D_scratch
        if ldiff != len(delta):
            self.delta2D_scratch = delta = np.empty((ldiff,), dtype=float)

        # compute square of distance to point
        inner1d(difference, difference, out=delta)
        close_points, _ = np.where(delta < radius*radius)
        return close_points
    # end def

# end class

def distanceToPoint(origin, direction, point):
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
    """ remap a slice to positive indices for a given
    length
    """
    new_start = length - start if start < 0 else start
    new_stop = length - stop if stop < 0 else stop

    if new_stop < new_start:
        raise IndexError("Stop {} must be greater than or equal to start {}".format(stop, start))
    return start, stop
# end def
